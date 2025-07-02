from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
from decimal import Decimal
import os
import time

# Initialize Flask app
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'chama.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    members = db.relationship('Member', backref='user', lazy=True)
    contributions = db.relationship('Contribution', backref='user', lazy=True)
    loans = db.relationship('Loan', backref='user', lazy=True)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(100))
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Active')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    contributions = db.relationship('Contribution', backref='member', lazy=True)

class Contribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(200))
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    purpose = db.Column(db.String(200))
    status = db.Column(db.String(20), default='Pending')
    date_applied = db.Column(db.DateTime, default=datetime.utcnow)
    date_approved = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Initialize database
def initialize_database():
    with app.app_context():
        db.session.close()
        if not os.path.exists(app.instance_path):
            os.makedirs(app.instance_path)
        
        db.create_all()
        
        if not User.query.filter_by(is_admin=True).first():
            admin = User(
                username='admin',
                password=generate_password_hash('admin'),
                is_admin=True
            )
            db.session.add(admin)
            
            regular_user = User(
                username='user',
                password=generate_password_hash('user'),
                is_admin=False
            )
            db.session.add(regular_user)
            db.session.commit()

# User loader
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Decorators
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Error Handlers
@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Main Routes
@app.route('/')
@login_required
def index():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    members = Member.query.filter_by(user_id=current_user.id).all()
    contributions = Contribution.query.filter_by(user_id=current_user.id)\
                          .order_by(Contribution.date.desc()).limit(5).all()
    loans = Loan.query.filter_by(user_id=current_user.id, status='Pending').all()
    
    return render_template('index.html',
                         members=members,
                         contributions=contributions,
                         loans=loans)

# Auth Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if password != confirm:
            flash('Passwords do not match', 'danger')
        else:
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'danger')
            else:
                user = User(
                    username=username,
                    password=generate_password_hash(password),
                    is_admin=False
                )
                db.session.add(user)
                db.session.commit()
                flash('Account created! Please login', 'success')
                return redirect(url_for('login'))
    return render_template('register.html')

# Member Routes
@app.route('/members')
@login_required
def member_list():
    members = Member.query.filter_by(user_id=current_user.id).all()
    return render_template('members/list.html', members=members)

@app.route('/members/add', methods=['GET', 'POST'])
@login_required
def add_member():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        
        if Member.query.filter_by(phone=phone).first():
            flash('Phone number already registered', 'danger')
        else:
            member = Member(
                name=name,
                phone=phone,
                email=email,
                user_id=current_user.id
            )
            db.session.add(member)
            db.session.commit()
            flash('Member added successfully', 'success')
            return redirect(url_for('member_list'))
    return render_template('members/add.html')

@app.route('/members/<int:member_id>')
@login_required
def view_member(member_id):
    member = Member.query.get_or_404(member_id)
    if member.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    contributions = Contribution.query.filter_by(member_id=member_id).all()
    return render_template('members/view.html',
                         member=member,
                         contributions=contributions)

# Contribution Routes
@app.route('/contributions')
@login_required
def contribution_list():
    contributions = Contribution.query.filter_by(user_id=current_user.id)\
                           .order_by(Contribution.date.desc()).all()
    return render_template('contributions/list.html',
                         contributions=contributions)

@app.route('/contributions/add', methods=['GET', 'POST'])
@login_required
def add_contribution():
    members = Member.query.filter_by(user_id=current_user.id).all()
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        amount = request.form.get('amount')
        description = request.form.get('description')
        
        if not member_id or not amount:
            flash('Member and amount are required', 'danger')
        else:
            contribution = Contribution(
                amount=Decimal(amount),
                description=description,
                member_id=member_id,
                user_id=current_user.id
            )
            db.session.add(contribution)
            db.session.commit()
            flash('Contribution recorded', 'success')
            return redirect(url_for('contribution_list'))
    return render_template('contributions/add.html', members=members)

# Loan Routes
@app.route('/loans')
@login_required
def loan_list():
    loans = Loan.query.filter_by(user_id=current_user.id).all()
    return render_template('loans/list.html', loans=loans)

@app.route('/loans/apply', methods=['GET', 'POST'])
@login_required
def apply_loan():
    if request.method == 'POST':
        amount = request.form.get('amount')
        purpose = request.form.get('purpose')
        
        if not amount or not purpose:
            flash('Amount and purpose are required', 'danger')
        else:
            loan = Loan(
                amount=Decimal(amount),
                purpose=purpose,
                user_id=current_user.id
            )
            db.session.add(loan)
            db.session.commit()
            flash('Loan application submitted', 'success')
            return redirect(url_for('loan_list'))
    return render_template('loans/apply.html')

# Admin Routes
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    stats = {
        'users': User.query.count(),
        'members': Member.query.count(),
        'contributions': Contribution.query.count(),
        'loans': Loan.query.count()
    }
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/loans')
@login_required
@admin_required
def admin_loans():
    loans = Loan.query.all()
    return render_template('admin/loans.html', loans=loans)

@app.route('/admin/loans/<int:loan_id>/approve')
@login_required
@admin_required
def approve_loan(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    loan.status = 'Approved'
    loan.date_approved = datetime.utcnow()
    db.session.commit()
    flash('Loan approved', 'success')
    return redirect(url_for('admin_loans'))

# Initialize before first request
@app.before_first_request
def before_first_request():
    initialize_database()

if __name__ == '__main__':
    try:
        app.run(debug=True)
    finally:
        db.session.close()