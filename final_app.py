from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import time
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-for-testing')
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
    notifications = db.relationship('Notification', backref='user', lazy=True)
    discussions = db.relationship('Discussion', backref='user', lazy=True)
    messages = db.relationship('Message', backref='user', lazy=True)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(100))
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Active')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    contributions = db.relationship('Contribution', backref='member', lazy=True)
    loans = db.relationship('Loan', backref='member', lazy=True)

class Contribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    purpose = db.Column(db.String(200))
    interest_rate = db.Column(db.Float, default=10.0)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Discussion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    messages = db.relationship('Message', backref='discussion', lazy=True, cascade='all, delete-orphan')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    discussion_id = db.Column(db.Integer, db.ForeignKey('discussion.id'), nullable=False)

def safely_remove_db_file(db_path):
    """Safely remove database file with multiple retries and connection cleanup"""
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            # Close all SQLite connections first
            try:
                conn = sqlite3.connect(db_path)
                conn.close()
            except:
                pass
            
            # Close SQLAlchemy connections
            db.session.close()
            db.engine.dispose()
            
            if os.path.exists(db_path):
                os.remove(db_path)
                print(f"Successfully removed database file (attempt {attempt + 1})")
                return True
        except PermissionError:
            print(f"Attempt {attempt + 1}: File still locked, waiting...")
            time.sleep(1.5)  # Increased wait time
        except Exception as e:
            print(f"Error during removal attempt {attempt + 1}: {str(e)}")
            break
    return False

def initialize_database():
    """Initialize the database with robust connection handling"""
    with app.app_context():
        # Create instance folder if needed
        if not os.path.exists(app.instance_path):
            os.makedirs(app.instance_path)
        
        db_path = os.path.join(app.instance_path, 'chama.db')
        
        # Try to remove old database file if it exists
        if os.path.exists(db_path):
            if not safely_remove_db_file(db_path):
                print("Warning: Could not remove old database file, attempting to continue anyway")
        
        # Create all tables
        db.create_all()
        
        # Create default admin user if none exists
        if not User.query.filter_by(is_admin=True).first():
            admin = User(
                username='admin',
                password=generate_password_hash('admin'),
                is_admin=True
            )
            db.session.add(admin)
            
            # Create regular user if none exists
            if not User.query.filter_by(username='user').first():
                user = User(
                    username='user',
                    password=generate_password_hash('user'),
                    is_admin=False
                )
                db.session.add(user)
            
            db.session.commit()
            print("Default users created")

# Initialize database when app starts
with app.app_context():
    initialize_database()

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

# Error handlers
@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Authentication Routes
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
    return render_template('auth/login.html')

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
    return render_template('auth/register.html')

# Main Application Routes
@app.route('/')
@login_required
def index():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Get all active members
    members = Member.query.filter_by(status='Active').all()
    
    # Get all contributions
    contributions = Contribution.query.join(Member)\
        .filter(Member.status == 'Active')\
        .order_by(Contribution.date.desc())\
        .limit(10).all()
    
    # Get user's own contributions for personal stats
    user_contributions = Contribution.query.join(Member)\
        .filter(Member.user_id == current_user.id)\
        .order_by(Contribution.date.desc())\
        .limit(5).all()
    
    # Calculate totals
    total_contributions = db.session.query(
        db.func.sum(Contribution.amount)
    ).scalar() or 0.0
    
    user_contributions_total = db.session.query(
        db.func.sum(Contribution.amount)
    ).join(Member)\
     .filter(Member.user_id == current_user.id)\
     .scalar() or 0.0
    
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.date.desc())\
        .limit(5).all()
    
    discussions = Discussion.query.order_by(Discussion.date.desc()).limit(5).all()
    loans = Loan.query.join(Member).filter(Member.user_id == current_user.id).all()
    
    return render_template('dashboard.html',
        members=members,
        contributions=contributions,
        user_contributions=user_contributions,
        total_contributions=total_contributions,
        user_contributions_total=user_contributions_total,
        notifications=notifications,
        discussions=discussions,
        loans=loans
    )

# Member Routes
@app.route('/members')
@login_required
def member_list():
    members = Member.query.filter_by(status='Active').all()
    return render_template('members/list_public.html', members=members)

@app.route('/members/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_member():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        username = request.form.get('username')
        temp_password = request.form.get('temp_password')
        
        if Member.query.filter_by(phone=phone).first():
            flash('Phone number already registered', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
        else:
            # Create user account first
            new_user = User(
                username=username,
                password=generate_password_hash(temp_password),
                is_admin=False
            )
            db.session.add(new_user)
            db.session.flush()  # Get user ID
            
            # Create member profile
            member = Member(
                name=name,
                phone=phone,
                email=email,
                user_id=new_user.id,
                status='Active'
            )
            db.session.add(member)
            db.session.commit()
            
            flash(f'Member added successfully. Username: {username}, Temporary Password: {temp_password}', 'success')
            return redirect(url_for('admin_members'))
    
    return render_template('members/add.html')

import secrets
import string

def generate_temp_password(length=8):
    """Generate a temporary password"""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

@app.route('/members/<int:member_id>')
@login_required
def view_member(member_id):
    member = Member.query.get_or_404(member_id)
    contributions = Contribution.query.filter_by(member_id=member_id).all()
    loans = Loan.query.filter_by(member_id=member_id).all()
    return render_template('members/view_public.html', 
                         member=member, 
                         contributions=contributions, 
                         loans=loans)

# Contribution Routes
@app.route('/contributions')
@login_required
def contributions():
    contributions = Contribution.query.join(Member)\
        .filter(Member.status == 'Active')\
        .order_by(Contribution.date.desc()).all()
    return render_template('contributions/list_public.html', contributions=contributions)

@app.route('/contributions/add', methods=['GET', 'POST'])
@login_required
def add_contribution():
    # Members can only contribute to their own account
    member = Member.query.filter_by(user_id=current_user.id).first()
    if not member:
        flash('No member profile found for your account', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        amount = request.form.get('amount')
        
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash('Invalid amount entered', 'danger')
            return redirect(url_for('add_contribution'))
            
        contribution = Contribution(
            amount=amount,
            member_id=member.id,
            date=datetime.utcnow()
        )
        db.session.add(contribution)
        db.session.commit()
        
        flash('Contribution recorded successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('contributions/add.html')

# Loan Routes
@app.route('/loans')
@login_required
def loans():
    loans = Loan.query.join(Member)\
        .filter(Member.user_id == current_user.id)\
        .all()
    return render_template('loans/list.html', loans=loans)

@app.route('/loans/apply', methods=['GET', 'POST'])
@login_required
def apply_loan():
    member = Member.query.filter_by(user_id=current_user.id).first()
    if not member:
        flash('No member profile found for your account', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        amount = request.form.get('amount')
        purpose = request.form.get('purpose')
        due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d')
        
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash('Invalid amount entered', 'danger')
            return redirect(url_for('apply_loan'))
            
        loan = Loan(
            amount=amount,
            purpose=purpose,
            due_date=due_date,
            member_id=member.id,
            status='Pending'
        )
        db.session.add(loan)
        db.session.commit()
        
        flash('Loan application submitted successfully!', 'success')
        return redirect(url_for('loans'))
    
    return render_template('loans/apply.html')

# Discussion Routes
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
        
        discussion = Discussion(
            title=title,
            content=content,
            user_id=current_user.id
        )
        db.session.add(discussion)
        db.session.commit()
        flash('Discussion created successfully!', 'success')
        return redirect(url_for('view_discussion', discussion_id=discussion.id))
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
        message = Message(
            content=content.strip(),
            user_id=current_user.id,
            discussion_id=discussion_id
        )
        db.session.add(message)
        db.session.commit()
        flash('Message sent', 'success')
    return redirect(url_for('view_discussion', discussion_id=discussion_id))

@app.route('/discussions/<int:discussion_id>/messages')
@login_required
def get_messages(discussion_id):
    """API endpoint to fetch messages for AJAX updates"""
    messages = Message.query.filter_by(discussion_id=discussion_id)\
        .order_by(Message.timestamp).all()
    
    messages_data = []
    for message in messages:
        messages_data.append({
            'id': message.id,
            'content': message.content,
            'username': message.user.username,
            'timestamp': message.timestamp.strftime('%I:%M %p'),
            'is_current_user': message.user_id == current_user.id
        })
    
    return {'messages': messages_data}

# User Account Routes
@app.route('/account/profile')
@login_required
def account_profile():
    member = Member.query.filter_by(user_id=current_user.id).first()
    return render_template('account/profile.html', user=current_user, member=member)

@app.route('/account/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        username = request.form.get('username')
        
        # Check if username is taken by another user
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != current_user.id:
            flash('Username already taken', 'danger')
            return render_template('account/edit.html', user=current_user)
        
        current_user.username = username
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('account_profile'))
    
    return render_template('account/edit.html', user=current_user)

@app.route('/account/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Verify current password
        if not check_password_hash(current_user.password, current_password):
            flash('Current password is incorrect', 'danger')
            return render_template('account/change_password.html')
        
        # Validate new password
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return render_template('account/change_password.html')
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long', 'danger')
            return render_template('account/change_password.html')
        
        # Update password
        current_user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Password changed successfully', 'success')
        return redirect(url_for('account_profile'))
    
    return render_template('account/change_password.html')

@app.route('/account/settings')
@login_required
def account_settings():
    return render_template('account/settings.html', user=current_user)

# Notification Routes
@app.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.date.desc()).all()
    for notification in notifications:
        notification.is_read = True
    db.session.commit()
    return render_template('notifications/list.html', notifications=notifications)

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
    
    # AI Default Risk Analysis
    risk_analysis = calculate_default_risk_analysis()
    
    return render_template('admin/dashboard.html', stats=stats, risk_analysis=risk_analysis)

def calculate_default_risk_analysis():
    """AI-based default risk prediction for members"""
    members = Member.query.all()
    risk_predictions = []
    
    for member in members:
        # Get member's financial data
        contributions = Contribution.query.filter_by(member_id=member.id).all()
        loans = Loan.query.filter_by(member_id=member.id).all()
        
        # Calculate risk factors
        total_contributions = sum(c.amount for c in contributions)
        total_loans = sum(l.amount for l in loans)
        active_loans = [l for l in loans if l.status in ['Approved', 'Pending']]
        overdue_loans = [l for l in loans if l.status == 'Overdue']
        
        # AI Risk Scoring Algorithm
        risk_score = 0
        risk_factors = []
        
        # Factor 1: Loan to Contribution Ratio
        if total_contributions > 0:
            loan_ratio = total_loans / total_contributions
            if loan_ratio > 2:
                risk_score += 40
                risk_factors.append('High loan-to-contribution ratio')
            elif loan_ratio > 1:
                risk_score += 20
                risk_factors.append('Moderate loan-to-contribution ratio')
        else:
            risk_score += 50
            risk_factors.append('No contributions made')
        
        # Factor 2: Active Loans Count
        if len(active_loans) > 2:
            risk_score += 30
            risk_factors.append('Multiple active loans')
        elif len(active_loans) > 1:
            risk_score += 15
        
        # Factor 3: Payment History
        if overdue_loans:
            risk_score += 35
            risk_factors.append('Previous overdue payments')
        
        # Factor 4: Contribution Consistency
        if len(contributions) < 3:
            risk_score += 25
            risk_factors.append('Irregular contribution pattern')
        
        # Factor 5: Member Activity
        if not contributions and not loans:
            risk_score += 60
            risk_factors.append('Inactive member')
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = 'High'
            risk_color = 'danger'
        elif risk_score >= 40:
            risk_level = 'Medium'
            risk_color = 'warning'
        else:
            risk_level = 'Low'
            risk_color = 'success'
        
        risk_predictions.append({
            'member': member,
            'risk_score': min(risk_score, 100),
            'risk_level': risk_level,
            'risk_color': risk_color,
            'risk_factors': risk_factors,
            'total_contributions': total_contributions,
            'total_loans': total_loans,
            'active_loans_count': len(active_loans)
        })
    
    # Sort by risk score (highest first)
    risk_predictions.sort(key=lambda x: x['risk_score'], reverse=True)
    
    # Calculate summary statistics
    high_risk_count = len([r for r in risk_predictions if r['risk_level'] == 'High'])
    medium_risk_count = len([r for r in risk_predictions if r['risk_level'] == 'Medium'])
    low_risk_count = len([r for r in risk_predictions if r['risk_level'] == 'Low'])
    
    return {
        'predictions': risk_predictions,
        'summary': {
            'high_risk': high_risk_count,
            'medium_risk': medium_risk_count,
            'low_risk': low_risk_count,
            'total_analyzed': len(risk_predictions)
        }
    }

@app.route('/admin/risk-analysis')
@login_required
@admin_required
def admin_risk_analysis():
    """Detailed risk analysis page"""
    risk_analysis = calculate_default_risk_analysis()
    return render_template('admin/risk_analysis.html', risk_analysis=risk_analysis)

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
    db.session.commit()
    flash('Loan approved', 'success')
    return redirect(url_for('admin_loans'))

@app.route('/admin/ai-insights')
@login_required
@admin_required
def admin_ai_insights():
    """AI insights and recommendations"""
    risk_analysis = calculate_default_risk_analysis()
    
    # Generate AI recommendations
    recommendations = []
    high_risk_members = [r for r in risk_analysis['predictions'] if r['risk_level'] == 'High']
    
    if high_risk_members:
        recommendations.append({
            'type': 'warning',
            'title': 'High Risk Members Detected',
            'message': f'{len(high_risk_members)} members have high default risk. Consider reviewing their loan applications carefully.',
            'action': 'Review high-risk members'
        })
    
    inactive_members = [r for r in risk_analysis['predictions'] if 'Inactive member' in r['risk_factors']]
    if inactive_members:
        recommendations.append({
            'type': 'info',
            'title': 'Member Engagement',
            'message': f'{len(inactive_members)} members show low activity. Consider engagement strategies.',
            'action': 'Send engagement notifications'
        })
    
    return render_template('admin/ai_insights.html', 
                         risk_analysis=risk_analysis, 
                         recommendations=recommendations)

@app.route('/admin/send-notification', methods=['GET', 'POST'])
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
                notification = Notification(
                    title=title,
                    message=message,
                    user_id=user.id
                )
                db.session.add(notification)
        else:
            notification = Notification(
                title=title,
                message=message,
                user_id=int(user_id)
            )
            db.session.add(notification)
        
        db.session.commit()
        flash('Notification sent successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/send_notification.html', users=users)

if __name__ == '__main__':
    try:
        app.run(debug=True)
    finally:
        # Ensure all connections are properly closed
        db.session.close()
        db.engine.dispose()
        print("Application shutdown complete")