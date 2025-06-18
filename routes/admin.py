from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def create_admin_blueprint(db, User, Member, Contribution):
    admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
    
    @admin_bp.route('/')
    @login_required
    @admin_required
    def dashboard():
        members_count = Member.query.count()
        users_count = User.query.count()
        
        contributions_count = Contribution.query.count()
        
        return render_template('admin/dashboard.html', 
                              members_count=members_count,
                              users_count=users_count,
                              contributions_count=contributions_count,
                              loans_count=0)
    
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
    
    return admin_bp