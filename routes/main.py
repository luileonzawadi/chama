from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime

def create_main_blueprint(db, User, Member, Contribution):
    main_bp = Blueprint('main', __name__)
    
    @main_bp.route('/')
    @login_required
    def index():
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        
        # Regular users see only their members
        members = Member.query.filter_by(user_id=current_user.id).all()
        return render_template('member.html', members=members)
    
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
    
    @main_bp.route('/contributions/add', methods=['GET', 'POST'])
    @login_required
    def add_contribution():
        members = Member.query.filter_by(user_id=current_user.id).all()
        
        if request.method == 'POST':
            member_id = request.form.get('member_id')
            amount = request.form.get('amount')
            
            if not member_id or not amount:
                flash('Please fill all required fields', 'danger')
                return render_template('add_contribution.html', members=members)
            
            # Validate member belongs to current user
            member = Member.query.filter_by(id=member_id, user_id=current_user.id).first()
            if not member:
                flash('Invalid member selected', 'danger')
                return render_template('add_contribution.html', members=members)
            
            # Create contribution
            contribution = Contribution(
                amount=float(amount),
                date=datetime.utcnow(),
                member_id=member_id
            )
            
            db.session.add(contribution)
            db.session.commit()
            
            flash('Contribution added successfully!', 'success')
            return redirect(url_for('main.contributions'))
        
        return render_template('add_contribution.html', members=members)
    
    @main_bp.route('/contributions')
    @login_required
    def contributions():
        # Get all contributions for user's members
        contributions = Contribution.query.join(Member).filter(Member.user_id == current_user.id).order_by(Contribution.date.desc()).all()
        return render_template('contributions.html', contributions=contributions)
    
    return main_bp