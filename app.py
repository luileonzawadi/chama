from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
from decimal import Decimal

# Create Flask app
app = Flask(__name__, template_folder='template')
app.config['SECRET_KEY'] = 'dev-key-for-testing'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chama_new.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Define models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(100))
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Active')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return f'<Member {self.name}>'

class Contribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(200))
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Contribution {self.amount}>'

# Loan model
class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    purpose = db.Column(db.String(200))
    status = db.Column(db.String(20), default='Pending')
    date_applied = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Loan {self.amount} - {self.status}>'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Error handlers
@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

# Routes
@app.route('/')
@login_required
def index():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Regular users see only their members
    members = Member.query.filter_by(user_id=current_user.id).all()
    try:
        contributions = Contribution.query.filter_by(user_id=current_user.id).order_by(Contribution.date.desc()).limit(5).all()
    except:
        contributions = []
    return render_template('member.html', members=members, contributions=contributions)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists', 'danger')
        else:
            new_user = User(
                username=username,
                password=generate_password_hash(password),
                is_admin=False
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('auth/register.html')

@app.route('/members/add', methods=['GET', 'POST'])
@login_required
def add_member():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        phone_exists = Member.query.filter_by(phone=phone).first()
        if phone_exists:
            flash('Phone number already exists', 'danger')
        else:
            new_member = Member(
                name=name,
                phone=phone,
                email=email,
                user_id=current_user.id
            )
            db.session.add(new_member)
            db.session.commit()
            flash('Member added successfully!', 'success')
            return redirect(url_for('index'))
    return render_template('add_member.html')

@app.route('/contributions', methods=['GET', 'POST'])
@login_required
def contributions():
    if request.method == 'POST':
        amount = request.form.get('amount')
        description = request.form.get('description')
        member_id = request.form.get('member_id')
        if not amount or not member_id:
            flash('Amount and member are required', 'danger')
            return redirect(url_for('contributions'))
        new_contribution = Contribution(
            amount=Decimal(amount),
            description=description,
            member_id=member_id,
            user_id=current_user.id
        )
        db.session.add(new_contribution)
        db.session.commit()
        flash('Contribution added successfully!', 'success')
        return redirect(url_for('contributions'))
    contributions = Contribution.query.filter_by(user_id=current_user.id).order_by(Contribution.date.desc()).all()
    members = Member.query.filter_by(user_id=current_user.id).all()
    return render_template('contributions.html', contributions=contributions, members=members)

@app.route('/my-contributions')
@login_required
def my_contributions():
    contributions = Contribution.query.filter_by(user_id=current_user.id).order_by(Contribution.date.desc()).all()
    return render_template('my_contribution.html', contributions=contributions)

@app.route('/contribute', methods=['GET', 'POST'])
@login_required
def contribute():
    members = Member.query.filter_by(user_id=current_user.id).all()
    if request.method == 'POST':
        amount = request.form.get('amount')
        description = request.form.get('description')
        member_id = request.form.get('member_id')
        if not amount or not member_id:
            flash('Amount and member are required', 'danger')
            return redirect(url_for('contribute'))
        # Simulate Mpesa payment trigger
        flash(f'Mpesa payment of KES {amount} initiated for member ID {member_id}.', 'info')
        # Optionally, save a pending contribution record here
        return redirect(url_for('my_contributions'))
    return render_template('contribute.html', members=members)

# Loan application route
@app.route('/apply-loan', methods=['GET', 'POST'])
@login_required
def apply_loan():
    if request.method == 'POST':
        amount = request.form.get('amount')
        purpose = request.form.get('purpose')
        if not amount or not purpose:
            flash('Amount and purpose are required', 'danger')
            return redirect(url_for('apply_loan'))
        loan = Loan(
            amount=Decimal(amount),
            purpose=purpose,
            user_id=current_user.id
        )
        db.session.add(loan)
        db.session.commit()
        flash('Loan application submitted successfully!', 'success')
        return redirect(url_for('my_loans'))
    return render_template('apply_loan.html')

# User's loan applications
@app.route('/my-loans')
@login_required
def my_loans():
    loans = Loan.query.filter_by(user_id=current_user.id).order_by(Loan.date_applied.desc()).all()
    return render_template('my_loans.html', loans=loans)

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    members_count = Member.query.count()
    users_count = User.query.count()
    contributions_count = Contribution.query.count()
    loans_count = Loan.query.count()
    context = {
        'members_count': members_count,
        'users_count': users_count,
        'contributions_count': contributions_count,
        'loans_count': loans_count,
        'admin_users_url': url_for('admin_users'),
        'admin_members_url': url_for('admin_members'),
        'add_member_url': url_for('add_member'),
        'contributions_url': url_for('contributions')
    }
    return render_template('admin/dashboard.html', **context)

@app.route('/admin/members')
@login_required
@admin_required
def admin_members():
    members = Member.query.all()
    return render_template('admin/members.html', members=members)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

# Create database tables and add sample data
with app.app_context():
    db.create_all()
    if not User.query.filter_by(is_admin=True).first():
        admin_user = User(
            username='admin',
            password=generate_password_hash('admin'),
            is_admin=True
        )
        db.session.add(admin_user)
        if not User.query.filter_by(username='user').first():
            regular_user = User(
                username='user',
                password=generate_password_hash('user'),
                is_admin=False
            )
            db.session.add(regular_user)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)