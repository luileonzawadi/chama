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
import requests
import base64
import json

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

class Investment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # stocks, bonds, real_estate, business
    amount_invested = db.Column(db.Float, nullable=False)
    current_value = db.Column(db.Float, default=0)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='Active')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    receipt_url = db.Column(db.String(200))
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='Pending')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0)
    target_date = db.Column(db.DateTime, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Active')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    agenda = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    meeting_link = db.Column(db.String(300))
    minutes = db.Column(db.Text)
    attendees = db.Column(db.Text)  # JSON string of attendee IDs
    status = db.Column(db.String(20), default='Scheduled')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # financial, member, activity
    content = db.Column(db.Text)
    file_path = db.Column(db.String(300))
    generated_date = db.Column(db.DateTime, default=datetime.utcnow)
    period_start = db.Column(db.DateTime)
    period_end = db.Column(db.DateTime)
    generated_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class Blockchain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    block_hash = db.Column(db.String(64), unique=True, nullable=False)
    previous_hash = db.Column(db.String(64))
    transaction_data = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    nonce = db.Column(db.Integer, default=0)
    transaction_type = db.Column(db.String(50))  # contribution, loan, expense
    amount = db.Column(db.Float)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'))

class AIInsight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    insight_type = db.Column(db.String(50), nullable=False)  # prediction, recommendation, alert
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    confidence_score = db.Column(db.Float)  # 0-1
    data_points = db.Column(db.Text)  # JSON
    generated_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Active')
    priority = db.Column(db.String(20), default='Medium')

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Context processor for unread notifications and discussion count
@app.context_processor
def inject_counts():
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        discussion_count = Discussion.query.count()
        return dict(unread_notifications_count=unread_count, discussion_count=discussion_count)
    return dict(unread_notifications_count=0, discussion_count=0)

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return render_template('access_denied.html'), 403
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
    return render_template('user_dashboard.html', member=member)

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

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        
        if user:
            user.password = generate_password_hash('0000')
            db.session.commit()
            flash('Password has been reset to 0000. Please login and change it immediately.', 'success')
        else:
            flash('Username not found', 'danger')
        
        return redirect(url_for('login'))
    
    return render_template('auth/reset_password.html')

@app.route('/discussions')
@login_required
def discussions():
    discussions = Discussion.query.order_by(Discussion.date.desc()).all()
    return render_template('discussions/list.html', discussions=discussions)

@app.route('/expenses')
@login_required
def expenses():
    if current_user.is_admin:
        expenses = Expense.query.order_by(Expense.date.desc()).all()
    else:
        expenses = Expense.query.filter_by(created_by=current_user.id).order_by(Expense.date.desc()).all()
    return render_template('expenses/list.html', expenses=expenses)

@app.route('/goals')
@login_required
def goals():
    goals = Goal.query.order_by(Goal.target_date).all()
    return render_template('goals/list.html', goals=goals)

@app.route('/investments')
@login_required
def investments():
    investments = Investment.query.order_by(Investment.purchase_date.desc()).all()
    return render_template('investments/list.html', investments=investments)

@app.route('/meetings')
@login_required
def meetings():
    meetings = Meeting.query.order_by(Meeting.date.desc()).all()
    return render_template('meetings/list.html', meetings=meetings)

@app.route('/activities')
@login_required
def activities():
    upcoming = Activity.query.filter(Activity.date >= datetime.utcnow()).order_by(Activity.date).all()
    past = Activity.query.filter(Activity.date < datetime.utcnow()).order_by(Activity.date.desc()).limit(10).all()
    return render_template('activities.html', upcoming=upcoming, past=past)

@app.route('/loans')
@login_required
def loans():
    if current_user.is_admin:
        loans = Loan.query.all()
    else:
        member_ids = [m.id for m in Member.query.filter_by(user_id=current_user.id).all()]
        loans = Loan.query.filter(Loan.member_id.in_(member_ids)).all()
    return render_template('loans/list.html', loans=loans)

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

@app.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.date.desc()).all()
    discussions = Discussion.query.order_by(Discussion.date.desc()).limit(5).all()
    
    # Mark all notifications as read
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return render_template('notifications/list.html', notifications=notifications, discussions=discussions)

@app.route('/notifications/clear')
@login_required
def clear_notifications():
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('All notifications cleared successfully!', 'success')
    return redirect(url_for('notifications'))

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

@app.route('/reports')
@login_required
@admin_required
def reports():
    reports = Report.query.order_by(Report.generated_date.desc()).all()
    return render_template('reports/list.html', reports=reports)

@app.route('/ai-insights')
@login_required
def ai_insights():
    all_insights = AIInsight.query.filter_by(status='Active').order_by(AIInsight.generated_date.desc()).all()
    return render_template('ai/insights.html', insights=all_insights, is_admin=current_user.is_admin)

# Create database tables and add sample data
with app.app_context():
    db.create_all()
    
    if not User.query.filter_by(is_admin=True).first():
        admin_user = User(username='admin', password=generate_password_hash('admin'), is_admin=True)
        db.session.add(admin_user)
        db.session.commit()

# Error handlers
@app.errorhandler(403)
def forbidden_error(error):
    return render_template('access_denied.html'), 403

if __name__ == '__main__':
    app.run(debug=True)