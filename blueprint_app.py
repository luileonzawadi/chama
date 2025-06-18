from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps
from flask import Blueprint

# Load environment variables
load_dotenv()

# Delete existing database if it exists
db_path = 'instance/chama.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Old database removed.")

# Create Flask app
app = Flask(__name__, template_folder='template')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-for-testing')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chama.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# Define models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    members = db.relationship('Member', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    discussions = db.relationship('Discussion', backref='user', lazy=True)
    messages = db.relationship('Message', backref='user', lazy=True)
    
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
    contributions = db.relationship('Contribution', backref='member', lazy=True)
    loans = db.relationship('Loan', backref='member', lazy=True)
    
    def __repr__(self):
        return f'<Member {self.name}>'

class Contribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    
    def __repr__(self):
        return f'<Contribution {self.id}>'

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    purpose = db.Column(db.String(200))
    interest_rate = db.Column(db.Float, default=10.0)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected, Repaid
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    
    def __repr__(self):
        return f'<Loan {self.id}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return f'<Notification {self.id}>'

class Discussion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    messages = db.relationship('Message', backref='discussion', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Discussion {self.id}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    discussion_id = db.Column(db.Integer, db.ForeignKey('discussion.id'), nullable=False)
    
    def __repr__(self):
        return f'<Message {self.id}>'

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

# Create blueprints
auth_bp = Blueprint('auth', __name__)
main_bp = Blueprint('main', __name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Auth routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if user already exists
        user_exists = User.query.filter_by(username=username).first()
        
        if user_exists:
            flash('Username already exists', 'danger')
        else:
            # Create new user
            new_user = User(
                username=username,
                password=generate_password_hash(password),
                is_admin=False
            )
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

# Main routes
@main_bp.route('/')
@login_required
def index():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    # Get user's members
    members = Member.query.filter_by(user_id=current_user.id).all()
    
    # Get all active members
    active_members = Member.query.filter_by(status='Active').all()
    
    # Get user's notifications
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.date.desc()).limit(5).all()
    
    # Get recent discussions
    discussions = Discussion.query.order_by(Discussion.date.desc()).limit(5).all()
    
    # Get recent contributions
    contributions = Contribution.query.join(Member).filter(Member.user_id == current_user.id).order_by(Contribution.date.desc()).limit(5).all()
    
    # Get user's loans
    loans = Loan.query.join(Member).filter(Member.user_id == current_user.id).all()
    
    return render_template('dashboard.html', 
                          members=members,
                          active_members=active_members,
                          notifications=notifications,
                          discussions=discussions,
                          contributions=contributions,
                          loans=loans)

@main_bp.route('/members/add', methods=['GET', 'POST'])
@login_required
def add_member():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        
        # Check if phone already exists
        phone_exists = Member.query.filter_by(phone=phone).first()
        
        if phone_exists:
            flash('Phone number already exists', 'danger')
        else:
            # Create new member
            new_member = Member(
                name=name,
                phone=phone,
                email=email,
                user_id=current_user.id
            )
            db.session.add(new_member)
            db.session.commit()
            
            flash('Member added successfully!', 'success')
            return redirect(url_for('main.index'))
    
    return render_template('add_member.html')

@main_bp.route('/loans/apply', methods=['GET', 'POST'])
@login_required
def apply_loan():
    # Get user's members
    members = Member.query.filter_by(user_id=current_user.id).all()
    
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        amount = float(request.form.get('amount'))
        purpose = request.form.get('purpose')
        due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d')
        
        # Validate member belongs to current user
        member = Member.query.filter_by(id=member_id, user_id=current_user.id).first()
        
        if not member:
            flash('Invalid member selected', 'danger')
            return redirect(url_for('main.apply_loan'))
        
        # Create new loan application
        new_loan = Loan(
            amount=amount,
            purpose=purpose,
            due_date=due_date,
            status='Pending',
            member_id=member_id
        )
        db.session.add(new_loan)
        db.session.commit()
        
        flash('Loan application submitted successfully!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('apply_loan.html', members=members)

@main_bp.route('/contributions')
@login_required
def contributions():
    # Get all contributions for user's members
    contributions = Contribution.query.join(Member).filter(Member.user_id == current_user.id).order_by(Contribution.date.desc()).all()
    return render_template('contributions.html', contributions=contributions)

@main_bp.route('/discussions')
@login_required
def discussions():
    # Get all discussions
    discussions = Discussion.query.order_by(Discussion.date.desc()).all()
    return render_template('discussions.html', discussions=discussions)

@main_bp.route('/discussions/create', methods=['GET', 'POST'])
@login_required
def create_discussion():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        # Create new discussion
        new_discussion = Discussion(
            title=title,
            content=content,
            user_id=current_user.id
        )
        db.session.add(new_discussion)
        db.session.commit()
        
        flash('Discussion created successfully!', 'success')
        return redirect(url_for('main.view_discussion', discussion_id=new_discussion.id))
    
    return render_template('create_discussion.html')

@main_bp.route('/discussions/<int:discussion_id>')
@login_required
def view_discussion(discussion_id):
    discussion = Discussion.query.get_or_404(discussion_id)
    messages = Message.query.filter_by(discussion_id=discussion_id).order_by(Message.timestamp).all()
    return render_template('view_discussion.html', discussion=discussion, messages=messages)

@main_bp.route('/discussions/<int:discussion_id>/message', methods=['POST'])
@login_required
def add_message(discussion_id):
    discussion = Discussion.query.get_or_404(discussion_id)
    content = request.form.get('content')
    
    if content:
        message = Message(
            content=content,
            user_id=current_user.id,
            discussion_id=discussion_id
        )
        db.session.add(message)
        db.session.commit()
        flash('Message sent', 'success')
    
    return redirect(url_for('main.view_discussion', discussion_id=discussion_id))

@main_bp.route('/notifications')
@login_required
def notifications():
    # Get all notifications for current user
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.date.desc()).all()
    
    # Mark all as read
    for notification in notifications:
        notification.is_read = True
    db.session.commit()
    
    return render_template('notifications.html', notifications=notifications)

# Admin routes
@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    members_count = Member.query.count()
    users_count = User.query.count()
    contributions_count = Contribution.query.count()
    loans_count = Loan.query.count()
    
    return render_template('admin/dashboard.html', 
                          members_count=members_count,
                          users_count=users_count,
                          contributions_count=contributions_count,
                          loans_count=loans_count)

@admin_bp.route('/members')
@login_required
@admin_required
def members():
    members = Member.query.all()
    return render_template('admin/members.html', members=members)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/send-notification', methods=['GET', 'POST'])
@login_required
@admin_required
def send_notification():
    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        user_id = request.form.get('user_id')
        
        if user_id == 'all':
            # Send to all users
            users = User.query.filter_by(is_admin=False).all()
            for user in users:
                notification = Notification(
                    title=title,
                    message=message,
                    user_id=user.id
                )
                db.session.add(notification)
        else:
            # Send to specific user
            notification = Notification(
                title=title,
                message=message,
                user_id=int(user_id)
            )
            db.session.add(notification)
        
        db.session.commit()
        flash('Notification sent successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/send_notification.html', users=users)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')

# Create database tables and add sample data
with app.app_context():
    db.create_all()
    
    # Create a default admin user if none exists
    if not User.query.filter_by(is_admin=True).first():
        admin_user = User(
            username='admin',
            password=generate_password_hash('admin'),
            is_admin=True
        )
        db.session.add(admin_user)
        
        # Create a regular user if none exists
        if not User.query.filter_by(username='user').first():
            regular_user = User(
                username='user',
                password=generate_password_hash('user'),
                is_admin=False
            )
            db.session.add(regular_user)
        
        db.session.commit()
        
        # Add sample data if no members exist
        if not Member.query.first():
            # Add members for admin
            admin = User.query.filter_by(username='admin').first()
            user = User.query.filter_by(username='user').first()
            
            # Admin's members
            member1 = Member(
                name='John Doe',
                phone='0712345678',
                email='john@example.com',
                join_date=datetime.utcnow(),
                status='Active',
                user_id=admin.id
            )
            
            member2 = Member(
                name='Jane Smith',
                phone='0723456789',
                email='jane@example.com',
                join_date=datetime.utcnow(),
                status='Active',
                user_id=admin.id
            )
            
            # User's members
            member3 = Member(
                name='Michael Johnson',
                phone='0734567890',
                email='michael@example.com',
                join_date=datetime.utcnow(),
                status='Active',
                user_id=user.id
            )
            
            db.session.add_all([member1, member2, member3])
            db.session.commit()
            
            # Add sample contributions
            contribution1 = Contribution(
                amount=1000,
                date=datetime.utcnow() - timedelta(days=7),
                member_id=member1.id
            )
            
            contribution2 = Contribution(
                amount=1500,
                date=datetime.utcnow() - timedelta(days=5),
                member_id=member2.id
            )
            
            contribution3 = Contribution(
                amount=800,
                date=datetime.utcnow() - timedelta(days=3),
                member_id=member3.id
            )
            
            db.session.add_all([contribution1, contribution2, contribution3])
            db.session.commit()
            
            # Add sample loans
            loan1 = Loan(
                amount=5000,
                purpose="Business expansion",
                interest_rate=10.0,
                issue_date=datetime.utcnow() - timedelta(days=10),
                due_date=datetime.utcnow() + timedelta(days=20),
                status='Approved',
                member_id=member1.id
            )
            
            loan2 = Loan(
                amount=3000,
                purpose="Education fees",
                interest_rate=8.0,
                issue_date=datetime.utcnow() - timedelta(days=5),
                due_date=datetime.utcnow() + timedelta(days=25),
                status='Pending',
                member_id=member3.id
            )
            
            db.session.add_all([loan1, loan2])
            db.session.commit()
            
            # Add sample notifications
            notification1 = Notification(
                title="Welcome to Chama",
                message="Welcome to our Chama Management System. We're glad to have you on board!",
                date=datetime.utcnow() - timedelta(days=1),
                is_read=False,
                user_id=user.id
            )
            
            notification2 = Notification(
                title="Meeting Reminder",
                message="Don't forget our monthly meeting this Friday at 5 PM.",
                date=datetime.utcnow() - timedelta(hours=12),
                is_read=False,
                user_id=user.id
            )
            
            db.session.add_all([notification1, notification2])
            db.session.commit()
            
            # Add sample discussions
            discussion1 = Discussion(
                title="Investment Opportunities",
                content="Let's discuss potential investment opportunities for our group funds.",
                date=datetime.utcnow() - timedelta(days=2),
                user_id=admin.id
            )
            
            discussion2 = Discussion(
                title="Next Meeting Agenda",
                content="What topics should we cover in our next meeting?",
                date=datetime.utcnow() - timedelta(days=1),
                user_id=user.id
            )
            
            db.session.add_all([discussion1, discussion2])
            db.session.commit()
            
            # Add sample messages
            message1 = Message(
                content="I think we should consider investing in government bonds for stable returns.",
                timestamp=datetime.utcnow() - timedelta(hours=12),
                user_id=admin.id,
                discussion_id=discussion1.id
            )
            
            message2 = Message(
                content="Real estate might be a better option given the current market conditions.",
                timestamp=datetime.utcnow() - timedelta(hours=10),
                user_id=user.id,
                discussion_id=discussion1.id
            )
            
            message3 = Message(
                content="We should discuss the upcoming loan applications and review our lending criteria.",
                timestamp=datetime.utcnow() - timedelta(hours=8),
                user_id=admin.id,
                discussion_id=discussion2.id
            )
            
            db.session.add_all([message1, message2, message3])
            db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)