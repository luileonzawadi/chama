from flask import jsonify, request
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash
from app.api import bp
from app.models import User, Member, Contribution, Loan, Discussion, Activity, Notification
from app import db
import requests
import base64
from datetime import datetime

@bp.route('/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        user.update_last_seen()
        db.session.commit()
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'is_admin': user.is_admin
            }
        })
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@bp.route('/dashboard', methods=['GET'])
@login_required
def api_dashboard():
    member = Member.query.filter_by(user_id=current_user.id).first()
    if not member:
        return jsonify({'error': 'No member profile found'}), 404
    
    contributions = Contribution.query.filter_by(member_id=member.id).order_by(Contribution.date.desc()).limit(5).all()
    total_contributions = sum(c.amount for c in Contribution.query.filter_by(member_id=member.id).all())
    loans = Loan.query.filter_by(member_id=member.id).order_by(Loan.date_applied.desc()).limit(3).all()
    
    return jsonify({
        'member': {
            'name': member.name,
            'phone': member.phone,
            'email': member.email
        },
        'stats': {
            'total_contributions': total_contributions,
            'contribution_count': len(contributions),
            'loan_count': len(loans)
        },
        'recent_contributions': [{
            'amount': c.amount,
            'date': c.date.isoformat(),
            'description': c.description
        } for c in contributions],
        'recent_loans': [{
            'amount': l.amount,
            'purpose': l.purpose,
            'status': l.status,
            'date_applied': l.date_applied.isoformat() if l.date_applied else None
        } for l in loans]
    })

@bp.route('/contribute', methods=['POST'])
@login_required
def api_contribute():
    data = request.get_json()
    member = Member.query.filter_by(user_id=current_user.id).first()
    if not member:
        return jsonify({'error': 'No member profile found'}), 404
    
    amount = data.get('amount')
    phone = data.get('phone')
    description = data.get('description', '')
    
    # Initiate M-Pesa STK Push
    mpesa_response = initiate_stk_push(phone, amount, f'CONTRIB-{member.id}')
    
    if mpesa_response.get('ResponseCode') == '0':
        return jsonify({
            'success': True,
            'message': 'Payment request sent to your phone'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Payment request failed'
        }), 400

@bp.route('/loans', methods=['GET'])
@login_required
def api_loans():
    member = Member.query.filter_by(user_id=current_user.id).first()
    if not member:
        return jsonify({'error': 'No member profile found'}), 404
    
    loans = Loan.query.filter_by(member_id=member.id).order_by(Loan.date_applied.desc()).all()
    return jsonify({
        'loans': [{
            'id': l.id,
            'amount': l.amount,
            'purpose': l.purpose,
            'status': l.status,
            'date_applied': l.date_applied.isoformat() if l.date_applied else None,
            'due_date': l.due_date.isoformat() if l.due_date else None
        } for l in loans]
    })

@bp.route('/discussions', methods=['GET'])
@login_required
def api_discussions():
    discussions = Discussion.query.order_by(Discussion.date.desc()).all()
    return jsonify({
        'discussions': [{
            'id': d.id,
            'title': d.title,
            'content': d.content,
            'date': d.date.isoformat(),
            'author': d.user.username
        } for d in discussions]
    })

@bp.route('/activities', methods=['GET'])
@login_required
def api_activities():
    upcoming = Activity.query.filter(Activity.date >= datetime.utcnow()).order_by(Activity.date).all()
    return jsonify({
        'activities': [{
            'id': a.id,
            'title': a.title,
            'description': a.description,
            'date': a.date.isoformat(),
            'type': a.type
        } for a in upcoming]
    })

def initiate_stk_push(phone, amount, account_ref):
    try:
        consumer_key = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
        consumer_secret = 'b051e7d22f7e0fe81e71b1d1a0e8b9c2d5c0b1f8e6a9c8d7f4e3b2a1c9d8e7f6'
        
        api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        r = requests.get(api_url, auth=(consumer_key, consumer_secret))
        access_token = r.json()['access_token']
        
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