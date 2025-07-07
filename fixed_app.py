from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import secrets
import string
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-for-testing')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chama.db'
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
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_online = db.Column(db.Boolean, default=False)
    members = db.relationship('Member', backref='user', lazy=True)
    
    def update_last_seen(self):
        self.last_seen = datetime.utcnow()
        self.is_online = True

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(100))
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Active')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Contribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'))
    description = db.Column(db.String(200))
    member = db.relationship('Member', backref='contributions')

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    purpose = db.Column(db.String(200))
    date_applied = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Pending')
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'))
    member = db.relationship('Member', backref='loans')

class Discussion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='discussions')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    discussion_id = db.Column(db.Integer, db.ForeignKey('discussion.id'))
    user = db.relationship('User', backref='messages')
    discussion = db.relationship('Discussion', backref='messages')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='notifications')

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.String(50), default='meeting')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='activities')

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
@login_required
def index():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    current_user.update_last_seen()
    db.session.commit()
    
    member = Member.query.filter_by(user_id=current_user.id).first()
    all_members = Member.query.filter(Member.user_id != current_user.id).all()
    online_members = [m for m in all_members if m.user and m.user.is_online]
    
    member_ids = [member.id] if member else []
    contributions = Contribution.query.filter(Contribution.member_id.in_(member_ids)).order_by(Contribution.date.desc()).limit(5).all() if member_ids else []
    total_contributions = sum(c.amount for c in Contribution.query.filter(Contribution.member_id.in_(member_ids)).all()) if member_ids else 0
    loans = Loan.query.filter(Loan.member_id.in_(member_ids)).order_by(Loan.date_applied.desc()).limit(3).all() if member_ids else []
    upcoming_activities = Activity.query.filter(Activity.date >= datetime.utcnow()).order_by(Activity.date).limit(5).all()
    discussions = Discussion.query.order_by(Discussion.date.desc()).limit(3).all()
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).limit(3).all()
    
    return render_template('user_dashboard.html', 
                         member=member, online_members=online_members, contributions=contributions,
                         total_contributions=total_contributions, loans=loans, upcoming_activities=upcoming_activities,
                         discussions=discussions, notifications=notifications)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            user.update_last_seen()
            db.session.commit()
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    current_user.is_online = False
    db.session.commit()
    logout_user()
    return redirect(url_for('login'))

@app.route('/contribute', methods=['GET', 'POST'])
@login_required
def contribute():
    member = Member.query.filter_by(user_id=current_user.id).first()
    if not member:
        flash('No member profile found', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        amount = request.form.get('amount')
        description = request.form.get('description', '')
        
        contribution = Contribution(amount=float(amount), member_id=member.id, description=description)
        db.session.add(contribution)
        db.session.commit()
        flash('Contribution added successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('contribute.html', member=member)

@app.route('/request-loan', methods=['GET', 'POST'])
@login_required
def request_loan():
    member = Member.query.filter_by(user_id=current_user.id).first()
    if not member:
        flash('No member profile found', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        amount = request.form.get('amount')
        purpose = request.form.get('purpose')
        due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d')
        
        loan = Loan(amount=float(amount), purpose=purpose, member_id=member.id, due_date=due_date)
        db.session.add(loan)
        db.session.commit()
        flash('Loan request submitted successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('request_loan.html', member=member)

@app.route('/contributions')
@login_required
def contributions():
    if current_user.is_admin:
        contributions = Contribution.query.all()
    else:
        member_ids = [m.id for m in Member.query.filter_by(user_id=current_user.id).all()]
        contributions = Contribution.query.filter(Contribution.member_id.in_(member_ids)).all()
    return render_template('contributions.html', contributions=contributions)

@app.route('/my-contributions')
@login_required
def my_contributions():
    member = Member.query.filter_by(user_id=current_user.id).first()
    if not member:
        contributions, total = [], 0
    else:
        contributions = Contribution.query.filter_by(member_id=member.id).order_by(Contribution.date.desc()).all()
        total = sum(c.amount for c in contributions)
    
    return render_template('my_contributions.html', contributions=contributions, total=total, member=member)

@app.route('/loans')
@login_required
def loans():
    if current_user.is_admin:
        loans = Loan.query.all()
    else:
        member_ids = [m.id for m in Member.query.filter_by(user_id=current_user.id).all()]
        loans = Loan.query.filter(Loan.member_id.in_(member_ids)).all()
    return render_template('loans/list.html', loans=loans)

@app.route('/discussions')
@login_required
def discussions():
    discussions = Discussion.query.order_by(Discussion.date.desc()).all()
    return render_template('discussions/list.html', discussions=discussions)

@app.route('/discussions/create', methods=['GET', 'POST'])
@login_required
def create_discussion():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        discussion = Discussion(title=title, content=content, user_id=current_user.id)
        db.session.add(discussion)
        db.session.commit()
        flash('Discussion created successfully!', 'success')
        return redirect(url_for('discussions'))
    
    return render_template('discussions/create.html')

@app.route('/discussions/<int:discussion_id>')
@login_required
def view_discussion(discussion_id):
    discussion = Discussion.query.get_or_404(discussion_id)
    messages = Message.query.filter_by(discussion_id=discussion_id).order_by(Message.timestamp).all()
    return render_template('discussions/view.html', discussion=discussion, messages=messages)

@app.route('/discussions/<int:discussion_id>/message', methods=['POST'])
@login_required
def add_message(discussion_id):
    content = request.form.get('content')
    if content and content.strip():
        message = Message(content=content.strip(), user_id=current_user.id, discussion_id=discussion_id)
        db.session.add(message)
        db.session.commit()
    return redirect(url_for('view_discussion', discussion_id=discussion_id))

@app.route('/api/discussions/<int:discussion_id>/messages')
@login_required
def get_messages(discussion_id):
    messages = Message.query.filter_by(discussion_id=discussion_id).order_by(Message.timestamp).all()
    return {'messages': [{'content': m.content, 'user': m.user.username, 'timestamp': m.timestamp.isoformat()} for m in messages]}

@app.route('/activities')
@login_required
def activities():
    upcoming = Activity.query.filter(Activity.date >= datetime.utcnow()).order_by(Activity.date).all()
    past = Activity.query.filter(Activity.date < datetime.utcnow()).order_by(Activity.date.desc()).limit(10).all()
    return render_template('activities.html', upcoming=upcoming, past=past)

@app.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.date.desc()).all()
    return render_template('notifications/list.html', notifications=notifications)

@app.route('/account/profile')
@login_required
def account_profile():
    member = Member.query.filter_by(user_id=current_user.id).first()
    return render_template('account/profile.html', user=current_user, member=member)

@app.route('/account/settings')
@login_required
def account_settings():
    return render_template('account/settings.html', user=current_user)

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

@app.route('/admin/loan-requests')
@login_required
@admin_required
def admin_loan_requests():
    loans = Loan.query.order_by(Loan.date_applied.desc()).all()
    return render_template('admin/loans.html', loans=loans)

@app.route('/admin/loans/<int:loan_id>/approve')
@login_required
@admin_required
def approve_loan(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    loan.status = 'Approved'
    db.session.commit()
    flash('Loan approved successfully!', 'success')
    return redirect(url_for('admin_loan_requests'))

@app.route('/admin/loans/<int:loan_id>/reject')
@login_required
@admin_required
def reject_loan(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    loan.status = 'Rejected'
    db.session.commit()
    flash('Loan rejected!', 'info')
    return redirect(url_for('admin_loan_requests'))

@app.route('/admin/ai-insights')
@login_required
@admin_required
def admin_ai_insights():
    risk_analysis = {
        'summary': {
            'high_risk': 0,
            'medium_risk': 0,
            'low_risk': User.query.count(),
            'total_analyzed': User.query.count()
        },
        'predictions': []
    }
    recommendations = []
    return render_template('admin/ai_insights.html', 
                         risk_analysis=risk_analysis, 
                         recommendations=recommendations)

@app.route('/admin/risk-analysis')
@login_required
@admin_required
def admin_risk_analysis():
    risk_analysis = {
        'summary': {
            'high_risk': 0,
            'medium_risk': 0,
            'low_risk': User.query.count(),
            'total_analyzed': User.query.count()
        },
        'predictions': []
    }
    return render_template('admin/risk_analysis.html', risk_analysis=risk_analysis)

@app.route('/add-member', methods=['GET', 'POST'])
@login_required
@admin_required
def add_member():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        username = request.form.get('username')
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return render_template('add_member.html')
        
        # Create user account with default password
        user = User(username=username, password=generate_password_hash('0000'), is_admin=False)
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create member profile
        member = Member(name=name, phone=phone, email=email, user_id=user.id)
        db.session.add(member)
        db.session.commit()
        
        flash(f'Member added successfully! Username: {username}, Default password: 0000', 'success')
        return redirect(url_for('admin_members'))
    
    return render_template('add_member.html')

@app.route('/send-notification', methods=['GET', 'POST'])
@login_required
@admin_required
def send_notification():
    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        user_id = request.form.get('user_id')
        
        if user_id == 'all':
            users = User.query.filter_by(is_admin=False).all()
            for user in users:
                notification = Notification(title=title, message=message, user_id=user.id)
                db.session.add(notification)
        else:
            notification = Notification(title=title, message=message, user_id=int(user_id))
            db.session.add(notification)
        
        db.session.commit()
        flash('Notification sent successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/send_notification.html', users=users)

@app.route('/admin/reset-password/<int:user_id>')
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot reset admin password!', 'danger')
        return redirect(url_for('admin_users'))
    
    user.password = generate_password_hash('0000')
    db.session.commit()
    flash(f'Password reset for {user.username}. New password: 0000', 'success')
    return redirect(url_for('admin_users'))

@app.route('/account/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not check_password_hash(current_user.password, current_password):
            flash('Current password is incorrect', 'danger')
            return render_template('account/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return render_template('account/change_password.html')
        
        if len(new_password) < 4:
            flash('Password must be at least 4 characters long', 'danger')
            return render_template('account/change_password.html')
        
        current_user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Password changed successfully', 'success')
        return redirect(url_for('account_profile'))
    
    return render_template('account/change_password.html')

# Create database tables and add sample data
with app.app_context():
    db.drop_all()
    db.create_all()
    
    if not User.query.filter_by(is_admin=True).first():
        admin_user = User(username='admin', password=generate_password_hash('admin'), is_admin=True)
        regular_user = User(username='user', password=generate_password_hash('user'), is_admin=False)
        db.session.add_all([admin_user, regular_user])
        db.session.commit()
        
        admin = User.query.filter_by(username='admin').first()
        user = User.query.filter_by(username='user').first()
        
        member1 = Member(name='John Doe', phone='0712345678', email='john@example.com', user_id=admin.id)
        member2 = Member(name='Jane Smith', phone='0723456789', email='jane@example.com', user_id=admin.id)
        member3 = Member(name='Michael Johnson', phone='0734567890', email='michael@example.com', user_id=user.id)
        
        activity1 = Activity(title='Monthly Meeting', description='Regular monthly chama meeting', 
                           date=datetime.utcnow() + timedelta(days=7), type='meeting', created_by=admin.id)
        activity2 = Activity(title='Investment Review', description='Review of investment portfolio', 
                           date=datetime.utcnow() + timedelta(days=14), type='review', created_by=admin.id)
        
        db.session.add_all([member1, member2, member3, activity1, activity2])
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)