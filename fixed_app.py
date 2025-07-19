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

class Biometric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    biometric_type = db.Column(db.String(20), nullable=False)  # fingerprint, face, voice
    biometric_hash = db.Column(db.String(256), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

class SmartContract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contract_name = db.Column(db.String(100), nullable=False)
    contract_type = db.Column(db.String(50), nullable=False)  # loan, investment, savings
    conditions = db.Column(db.Text, nullable=False)  # JSON
    parties = db.Column(db.Text)  # JSON of member IDs
    status = db.Column(db.String(20), default='Active')
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    executed_date = db.Column(db.DateTime)
    amount = db.Column(db.Float)
    auto_execute = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class IoTDevice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(100), nullable=False)
    device_type = db.Column(db.String(50), nullable=False)  # sensor, camera, beacon
    device_id = db.Column(db.String(100), unique=True, nullable=False)
    location = db.Column(db.String(200))
    status = db.Column(db.String(20), default='Active')
    last_ping = db.Column(db.DateTime)
    data = db.Column(db.Text)  # JSON sensor data
    battery_level = db.Column(db.Integer)

class VirtualReality(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_name = db.Column(db.String(100), nullable=False)
    session_type = db.Column(db.String(50), nullable=False)  # meeting, training, presentation
    vr_room_id = db.Column(db.String(100), unique=True)
    participants = db.Column(db.Text)  # JSON of member IDs
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    recording_url = db.Column(db.String(300))
    status = db.Column(db.String(20), default='Scheduled')

class CryptoWallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    wallet_address = db.Column(db.String(100), unique=True, nullable=False)
    private_key_hash = db.Column(db.String(256), nullable=False)
    balance_btc = db.Column(db.Float, default=0)
    balance_eth = db.Column(db.Float, default=0)
    balance_usdt = db.Column(db.Float, default=0)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return render_template('access_denied.html'), 403
        return f(*args, **kwargs)
    return decorated_function

# AI Risk Analysis Function
def calculate_risk_analysis():
    members = Member.query.all()
    predictions = []
    high_risk = medium_risk = low_risk = 0
    
    for member in members:
        # Calculate member metrics
        total_contributions = sum(c.amount for c in member.contributions)
        contribution_count = len(member.contributions)
        loan_count = len(member.loans)
        pending_loans = len([l for l in member.loans if l.status == 'Pending'])
        rejected_loans = len([l for l in member.loans if l.status == 'Rejected'])
        
        # Calculate risk score (0-100)
        risk_score = 0
        risk_factors = []
        
        # Contribution history analysis
        if total_contributions < 5000:
            risk_score += 30
            risk_factors.append('Low contribution history')
        elif total_contributions < 15000:
            risk_score += 15
            risk_factors.append('Moderate contributions')
        
        # Loan history analysis
        if rejected_loans > 0:
            risk_score += 25
            risk_factors.append('Previous loan rejections')
        
        if pending_loans > 1:
            risk_score += 20
            risk_factors.append('Multiple pending loans')
        
        # Activity analysis
        if contribution_count < 3:
            risk_score += 20
            risk_factors.append('Low activity')
        
        # Member tenure
        days_since_join = (datetime.utcnow() - member.join_date).days
        if days_since_join < 30:
            risk_score += 15
            risk_factors.append('New member')
        
        # Determine risk level and color
        if risk_score >= 60:
            risk_level = 'High Risk'
            risk_color = 'danger'
            high_risk += 1
        elif risk_score >= 30:
            risk_level = 'Medium Risk'
            risk_color = 'warning'
            medium_risk += 1
        else:
            risk_level = 'Low Risk'
            risk_color = 'success'
            low_risk += 1
        
        if not risk_factors:
            risk_factors = ['Good standing']
        
        predictions.append({
            'member': member,
            'risk_score': min(risk_score, 100),
            'risk_level': risk_level,
            'risk_color': risk_color,
            'risk_factors': risk_factors,
            'total_contributions': total_contributions,
            'loan_count': loan_count
        })
    
    # Sort by risk score (highest first)
    predictions.sort(key=lambda x: x['risk_score'], reverse=True)
    
    return {
        'summary': {
            'high_risk': high_risk,
            'medium_risk': medium_risk,
            'low_risk': low_risk,
            'total_analyzed': len(members)
        },
        'predictions': predictions
    }

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

# Investment tracking functions
def calculate_portfolio_performance():
    investments = Investment.query.filter_by(status='Active').all()
    total_invested = sum(inv.amount_invested for inv in investments)
    total_current = sum(inv.current_value for inv in investments)
    return {
        'total_invested': total_invested,
        'current_value': total_current,
        'profit_loss': total_current - total_invested,
        'roi_percentage': ((total_current - total_invested) / total_invested * 100) if total_invested > 0 else 0
    }

# Blockchain Functions
import hashlib
import json

def create_blockchain_transaction(transaction_type, amount, member_id, data):
    # Get the last block
    last_block = Blockchain.query.order_by(Blockchain.id.desc()).first()
    previous_hash = last_block.block_hash if last_block else '0' * 64
    
    # Create transaction data
    transaction_data = {
        'type': transaction_type,
        'amount': amount,
        'member_id': member_id,
        'timestamp': datetime.utcnow().isoformat(),
        'data': data
    }
    
    # Calculate hash
    block_string = json.dumps(transaction_data, sort_keys=True) + previous_hash
    block_hash = hashlib.sha256(block_string.encode()).hexdigest()
    
    # Create blockchain entry
    blockchain_entry = Blockchain(
        block_hash=block_hash,
        previous_hash=previous_hash,
        transaction_data=json.dumps(transaction_data),
        transaction_type=transaction_type,
        amount=amount,
        member_id=member_id
    )
    
    db.session.add(blockchain_entry)
    return blockchain_entry

# AI-Powered Analytics
def generate_ai_insights():
    insights = []
    
    # Analyze contribution patterns
    contributions = Contribution.query.all()
    if len(contributions) > 5:
        avg_contribution = sum(c.amount for c in contributions) / len(contributions)
        recent_avg = sum(c.amount for c in contributions[-5:]) / 5
        
        if recent_avg > avg_contribution * 1.2:
            insights.append({
                'type': 'prediction',
                'title': 'Increasing Contribution Trend',
                'description': f'Recent contributions are 20% higher than average. Projected monthly growth: {((recent_avg - avg_contribution) / avg_contribution * 100):.1f}%',
                'confidence': 0.85,
                'priority': 'High'
            })
    
    # Risk assessment
    high_risk_members = calculate_risk_analysis()['predictions']
    high_risk_count = len([m for m in high_risk_members if m['risk_level'] == 'High Risk'])
    
    if high_risk_count > 0:
        insights.append({
            'type': 'alert',
            'title': 'High Risk Members Alert',
            'description': f'{high_risk_count} members have high default risk. Recommend immediate review.',
            'confidence': 0.92,
            'priority': 'Critical'
        })
    
    # Investment recommendations
    portfolio = calculate_portfolio_performance()
    if portfolio['roi_percentage'] < 5:
        insights.append({
            'type': 'recommendation',
            'title': 'Investment Diversification Needed',
            'description': 'Current ROI is below 5%. Consider diversifying into high-yield bonds or real estate.',
            'confidence': 0.78,
            'priority': 'Medium'
        })
    
    return insights

# Smart Contract Execution
def execute_smart_contracts():
    active_contracts = SmartContract.query.filter_by(status='Active', auto_execute=True).all()
    
    for contract in active_contracts:
        conditions = json.loads(contract.conditions)
        
        # Example: Auto-approve loans under certain conditions
        if contract.contract_type == 'loan' and 'auto_approve_limit' in conditions:
            pending_loans = Loan.query.filter_by(status='Pending').all()
            
            for loan in pending_loans:
                if loan.amount <= conditions['auto_approve_limit']:
                    # Check member's contribution history
                    member_contributions = sum(c.amount for c in loan.member.contributions)
                    if member_contributions >= loan.amount * 2:  # 2x contribution requirement
                        loan.status = 'Approved'
                        contract.executed_date = datetime.utcnow()
                        
                        # Create blockchain record
                        create_blockchain_transaction('loan_approval', loan.amount, loan.member_id, {
                            'loan_id': loan.id,
                            'auto_approved': True,
                            'contract_id': contract.id
                        })

def generate_financial_report(start_date, end_date):
    contributions = Contribution.query.filter(
        Contribution.date.between(start_date, end_date)
    ).all()
    loans = Loan.query.filter(
        Loan.date_applied.between(start_date, end_date)
    ).all()
    expenses = Expense.query.filter(
        Expense.date.between(start_date, end_date),
        Expense.status == 'Approved'
    ).all()
    
    return {
        'total_contributions': sum(c.amount for c in contributions),
        'total_loans': sum(l.amount for l in loans),
        'total_expenses': sum(e.amount for e in expenses),
        'net_position': sum(c.amount for c in contributions) - sum(l.amount for l in loans) - sum(e.amount for e in expenses)
    }

# M-Pesa STK Push function
def initiate_stk_push(phone, amount, account_ref):
    try:
        # Get access token
        consumer_key = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
        consumer_secret = 'b051e7d22f7e0fe81e71b1d1a0e8b9c2d5c0b1f8e6a9c8d7f4e3b2a1c9d8e7f6'
        
        api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        r = requests.get(api_url, auth=(consumer_key, consumer_secret))
        access_token = r.json()['access_token']
        
        # STK Push request
        api_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        shortcode = '174379'
        passkey = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919b051e7d22f7e0fe81e71b1d1a0e8b9c2d5c0b1f8e6a9c8d7f4e3b2a1c9d8e7f6'
        
        password = base64.b64encode((shortcode + passkey + timestamp).encode()).decode('utf-8')
        
        payload = {
            'BusinessShortCode': shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(amount),
            'PartyA': phone,
            'PartyB': shortcode,
            'PhoneNumber': phone,
            'CallBackURL': 'https://mydomain.com/path',
            'AccountReference': account_ref,
            'TransactionDesc': 'Chama Contribution'
        }
        
        response = requests.post(api_url, json=payload, headers=headers)
        return response.json()
    except:
        return {'ResponseCode': '1', 'errorMessage': 'Service unavailable'}

@app.route('/contribute', methods=['GET', 'POST'])
@login_required
def contribute():
    member = Member.query.filter_by(user_id=current_user.id).first()
    if not member:
        flash('No member profile found', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        amount = request.form.get('amount')
        phone = request.form.get('phone')
        description = request.form.get('description', '')
        
        # Initiate M-Pesa STK Push
        mpesa_response = initiate_stk_push(phone, amount, f'CONTRIB-{member.id}')
        
        if mpesa_response.get('ResponseCode') == '0':
            flash('Payment request sent to your phone. Please complete the payment.', 'info')
        else:
            flash('Payment request failed. Please try again.', 'danger')
        
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
    
    # AI Risk Analysis
    risk_analysis = calculate_risk_analysis()
    
    return render_template('admin/dashboard.html', stats=stats, risk_analysis=risk_analysis)

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
    risk_analysis = calculate_risk_analysis()
    
    # Generate AI recommendations
    recommendations = []
    if risk_analysis['summary']['high_risk'] > 0:
        recommendations.append({
            'type': 'warning',
            'title': 'High Risk Members Detected',
            'message': f"{risk_analysis['summary']['high_risk']} members have high default risk. Review their loan applications carefully."
        })
    
    if risk_analysis['summary']['medium_risk'] > risk_analysis['summary']['low_risk']:
        recommendations.append({
            'type': 'info',
            'title': 'Encourage More Contributions',
            'message': 'Many members have medium risk due to low contribution history. Consider incentive programs.'
        })
    
    recommendations.append({
        'type': 'success',
        'title': 'Regular Monitoring',
        'message': 'Continue monitoring member activities and update risk assessments monthly.'
    })
    
    return render_template('admin/ai_insights.html', 
                         risk_analysis=risk_analysis, 
                         recommendations=recommendations)

@app.route('/admin/risk-analysis')
@login_required
@admin_required
def admin_risk_analysis():
    risk_analysis = calculate_risk_analysis()
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

@app.route('/add-activity', methods=['GET', 'POST'])
@login_required
@admin_required
def add_activity():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%dT%H:%M')
        activity_type = request.form.get('type')
        
        activity = Activity(
            title=title,
            description=description,
            date=date,
            type=activity_type,
            created_by=current_user.id
        )
        db.session.add(activity)
        db.session.commit()
        flash('Activity added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/add_activity.html')

@app.route('/admin/remove-member/<int:member_id>')
@login_required
@admin_required
def remove_member(member_id):
    member = Member.query.get_or_404(member_id)
    member_name = member.name
    
    # Only delete member profile, keep user account
    db.session.delete(member)
    db.session.commit()
    
    flash(f'Member {member_name} removed from chama (user account preserved)!', 'success')
    return redirect(url_for('admin_members'))

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

# Investment Management Routes
@app.route('/investments')
@login_required
def investments():
    investments = Investment.query.order_by(Investment.purchase_date.desc()).all()
    portfolio = calculate_portfolio_performance()
    return render_template('investments/list.html', investments=investments, portfolio=portfolio)

@app.route('/investments/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_investment():
    if request.method == 'POST':
        investment = Investment(
            name=request.form.get('name'),
            type=request.form.get('type'),
            amount_invested=float(request.form.get('amount')),
            current_value=float(request.form.get('amount')),
            description=request.form.get('description'),
            created_by=current_user.id
        )
        db.session.add(investment)
        db.session.commit()
        flash('Investment added successfully!', 'success')
        return redirect(url_for('investments'))
    return render_template('investments/add.html')

# Expense Management Routes
@app.route('/expenses')
@login_required
def expenses():
    if current_user.is_admin:
        expenses = Expense.query.order_by(Expense.date.desc()).all()
    else:
        expenses = Expense.query.filter_by(created_by=current_user.id).order_by(Expense.date.desc()).all()
    return render_template('expenses/list.html', expenses=expenses)

@app.route('/expenses/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        expense = Expense(
            category=request.form.get('category'),
            amount=float(request.form.get('amount')),
            description=request.form.get('description'),
            created_by=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense submitted for approval!', 'success')
        return redirect(url_for('expenses'))
    return render_template('expenses/add.html')

@app.route('/expenses/<int:expense_id>/approve')
@login_required
@admin_required
def approve_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    expense.status = 'Approved'
    expense.approved_by = current_user.id
    db.session.commit()
    flash('Expense approved!', 'success')
    return redirect(url_for('expenses'))

# Goals Management Routes
@app.route('/goals')
@login_required
def goals():
    goals = Goal.query.order_by(Goal.target_date).all()
    return render_template('goals/list.html', goals=goals)

@app.route('/goals/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_goal():
    if request.method == 'POST':
        goal = Goal(
            title=request.form.get('title'),
            description=request.form.get('description'),
            target_amount=float(request.form.get('target_amount')),
            target_date=datetime.strptime(request.form.get('target_date'), '%Y-%m-%d'),
            category=request.form.get('category'),
            created_by=current_user.id
        )
        db.session.add(goal)
        db.session.commit()
        flash('Goal created successfully!', 'success')
        return redirect(url_for('goals'))
    return render_template('goals/add.html')

# Meeting Management Routes
@app.route('/meetings')
@login_required
def meetings():
    meetings = Meeting.query.order_by(Meeting.date.desc()).all()
    return render_template('meetings/list.html', meetings=meetings)

@app.route('/meetings/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_meeting():
    if request.method == 'POST':
        meeting = Meeting(
            title=request.form.get('title'),
            agenda=request.form.get('agenda'),
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%dT%H:%M'),
            location=request.form.get('location'),
            meeting_link=request.form.get('meeting_link'),
            created_by=current_user.id
        )
        db.session.add(meeting)
        db.session.commit()
        flash('Meeting scheduled successfully!', 'success')
        return redirect(url_for('meetings'))
    return render_template('meetings/add.html')

# Reports Routes
@app.route('/reports')
@login_required
@admin_required
def reports():
    reports = Report.query.order_by(Report.generated_date.desc()).all()
    return render_template('reports/list.html', reports=reports)

@app.route('/reports/generate', methods=['GET', 'POST'])
@login_required
@admin_required
def generate_report():
    if request.method == 'POST':
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        report_type = request.form.get('type')
        
        financial_data = generate_financial_report(start_date, end_date)
        
        report = Report(
            title=f'{report_type.title()} Report - {start_date.strftime("%b %Y")}',
            type=report_type,
            content=str(financial_data),
            period_start=start_date,
            period_end=end_date,
            generated_by=current_user.id
        )
        db.session.add(report)
        db.session.commit()
        flash('Report generated successfully!', 'success')
        return redirect(url_for('reports'))
    return render_template('reports/generate.html')

# Blockchain & Crypto Routes
@app.route('/blockchain')
@login_required
@admin_required
def blockchain_explorer():
    blocks = Blockchain.query.order_by(Blockchain.id.desc()).limit(50).all()
    return render_template('blockchain/explorer.html', blocks=blocks)

@app.route('/crypto-wallet')
@login_required
def crypto_wallet():
    member = Member.query.filter_by(user_id=current_user.id).first()
    if not member:
        flash('No member profile found', 'danger')
        return redirect(url_for('index'))
    
    wallet = CryptoWallet.query.filter_by(member_id=member.id).first()
    if not wallet:
        # Create wallet
        import secrets
        wallet_address = 'CW' + secrets.token_hex(20)
        private_key = hashlib.sha256(secrets.token_bytes(32)).hexdigest()
        
        wallet = CryptoWallet(
            member_id=member.id,
            wallet_address=wallet_address,
            private_key_hash=private_key
        )
        db.session.add(wallet)
        db.session.commit()
    
    return render_template('crypto/wallet.html', wallet=wallet)

# AI Insights Routes
@app.route('/ai-insights')
@login_required
def ai_insights():
    # Only admins can generate new insights
    if current_user.is_admin:
        insights = generate_ai_insights()
        
        # Save insights to database
        for insight_data in insights:
            existing = AIInsight.query.filter_by(
                title=insight_data['title'],
                generated_date=datetime.utcnow().date()
            ).first()
            
            if not existing:
                insight = AIInsight(
                    insight_type=insight_data['type'],
                    title=insight_data['title'],
                    description=insight_data['description'],
                    confidence_score=insight_data['confidence'],
                    priority=insight_data['priority']
                )
                db.session.add(insight)
        
        db.session.commit()
    
    # Both admins and regular users can view insights
    all_insights = AIInsight.query.filter_by(status='Active').order_by(AIInsight.generated_date.desc()).all()
    return render_template('ai/insights.html', insights=all_insights, is_admin=current_user.is_admin)

# Smart Contracts Routes
@app.route('/smart-contracts')
@login_required
@admin_required
def smart_contracts():
    contracts = SmartContract.query.order_by(SmartContract.created_date.desc()).all()
    return render_template('smart_contracts/list.html', contracts=contracts)

@app.route('/smart-contracts/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_smart_contract():
    if request.method == 'POST':
        conditions = {
            'auto_approve_limit': float(request.form.get('auto_approve_limit', 0)),
            'contribution_multiplier': float(request.form.get('contribution_multiplier', 2)),
            'max_loan_term_days': int(request.form.get('max_loan_term', 90))
        }
        
        contract = SmartContract(
            contract_name=request.form.get('name'),
            contract_type=request.form.get('type'),
            conditions=json.dumps(conditions),
            amount=float(request.form.get('amount', 0))
        )
        db.session.add(contract)
        db.session.commit()
        flash('Smart contract created successfully!', 'success')
        return redirect(url_for('smart_contracts'))
    
    return render_template('smart_contracts/create.html')

# IoT Dashboard
@app.route('/iot-dashboard')
@login_required
@admin_required
def iot_dashboard():
    devices = IoTDevice.query.all()
    return render_template('iot/dashboard.html', devices=devices)

# VR Meeting Routes
@app.route('/vr-meetings')
@login_required
def vr_meetings():
    vr_sessions = VirtualReality.query.order_by(VirtualReality.start_time.desc()).all()
    return render_template('vr/meetings.html', sessions=vr_sessions, is_admin=current_user.is_admin)

@app.route('/vr-meetings/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_vr_meeting():
    if request.method == 'POST':
        import secrets
        vr_room_id = 'VR' + secrets.token_hex(8)
        
        vr_session = VirtualReality(
            session_name=request.form.get('name'),
            session_type=request.form.get('type'),
            vr_room_id=vr_room_id,
            start_time=datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
        )
        db.session.add(vr_session)
        db.session.commit()
        flash('VR meeting scheduled successfully!', 'success')
        return redirect(url_for('vr_meetings'))
    
    return render_template('vr/create.html')

# Biometric Authentication
@app.route('/biometric-setup')
@login_required
def biometric_setup():
    biometrics = Biometric.query.filter_by(user_id=current_user.id, is_active=True).all()
    return render_template('biometric/setup.html', biometrics=biometrics)

# API for modern features
@app.route('/api/blockchain/verify', methods=['POST'])
@login_required
def verify_blockchain():
    blocks = Blockchain.query.order_by(Blockchain.id).all()
    
    for i, block in enumerate(blocks):
        if i == 0:  # Genesis block
            continue
        
        previous_block = blocks[i-1]
        if block.previous_hash != previous_block.block_hash:
            return jsonify({'valid': False, 'error': f'Block {block.id} has invalid previous hash'})
    
    return jsonify({'valid': True, 'message': 'Blockchain is valid'})

@app.route('/api/ai/predict-default/<int:member_id>')
@login_required
@admin_required
def predict_member_default(member_id):
    member = Member.query.get_or_404(member_id)
    
    # Simple ML prediction based on contribution patterns
    contributions = member.contributions
    loans = member.loans
    
    if not contributions:
        return jsonify({'risk_score': 0.8, 'risk_level': 'High', 'reason': 'No contribution history'})
    
    avg_contribution = sum(c.amount for c in contributions) / len(contributions)
    total_loans = sum(l.amount for l in loans)
    
    risk_score = min(1.0, total_loans / (avg_contribution * len(contributions)) if contributions else 1.0)
    
    risk_level = 'High' if risk_score > 0.7 else 'Medium' if risk_score > 0.4 else 'Low'
    
    return jsonify({
        'risk_score': risk_score,
        'risk_level': risk_level,
        'avg_contribution': avg_contribution,
        'total_loans': total_loans
    })

# Create database tables and add sample data
with app.app_context():
    db.drop_all()
    db.create_all()
    
    if not User.query.filter_by(is_admin=True).first():
        admin_user = User(username='admin', password=generate_password_hash('admin'), is_admin=True)
        db.session.add(admin_user)
        db.session.commit()
        
        admin = User.query.filter_by(username='admin').first()
        
        member1 = Member(name='John Doe', phone='0712345678', email='john@example.com', user_id=admin.id)
        member2 = Member(name='Jane Smith', phone='0723456789', email='jane@example.com', user_id=admin.id)
        
        activity1 = Activity(title='Monthly Meeting', description='Regular monthly chama meeting', 
                           date=datetime.utcnow() + timedelta(days=7), type='meeting', created_by=admin.id)
        activity2 = Activity(title='Investment Review', description='Review of investment portfolio', 
                           date=datetime.utcnow() + timedelta(days=14), type='review', created_by=admin.id)
        
        # Sample investments
        investment1 = Investment(name='Treasury Bonds', type='bonds', amount_invested=50000, current_value=52000, created_by=admin.id)
        investment2 = Investment(name='Real Estate - Plot', type='real_estate', amount_invested=200000, current_value=220000, created_by=admin.id)
        
        # Sample goals
        goal1 = Goal(title='Emergency Fund', description='Build emergency fund', target_amount=100000, current_amount=25000, 
                    target_date=datetime.utcnow() + timedelta(days=365), category='savings', created_by=admin.id)
        goal2 = Goal(title='Investment Capital', description='Raise capital for new investments', target_amount=500000, current_amount=150000,
                    target_date=datetime.utcnow() + timedelta(days=180), category='investment', created_by=admin.id)
        
        # Sample smart contract
        smart_contract1 = SmartContract(
            contract_name='Auto Loan Approval',
            contract_type='loan',
            conditions=json.dumps({
                'auto_approve_limit': 10000,
                'contribution_multiplier': 2,
                'max_loan_term_days': 90
            }),
            created_by=admin.id
        )
        
        # Sample IoT device
        iot_device1 = IoTDevice(
            device_name='Office Security Camera',
            device_type='camera',
            device_id='CAM001',
            location='Main Office',
            battery_level=85
        )
        
        db.session.add_all([member1, member2, activity1, activity2, investment1, investment2, goal1, goal2, smart_contract1, iot_device1])
        db.session.commit()

# Error handlers
@app.errorhandler(403)
def forbidden_error(error):
    return render_template('access_denied.html'), 403

if __name__ == '__main__':
    app.run(debug=True)