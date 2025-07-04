from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

def create_auth_blueprint(db, User):
    auth_bp = Blueprint('auth', __name__)
    
    @auth_bp.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password, password):
                user.update_last_login()
                db.session.commit()
                login_user(user)
                
                # Check if this is first login (no previous login recorded)
                if not user.last_login and not user.is_admin:
                    flash('Please change your temporary password', 'warning')
                    return redirect(url_for('change_password'))
                
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                if user.is_admin:
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'danger')
        
        return render_template('auth/login.html')
    
    @auth_bp.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('auth.login'))
    
    @auth_bp.route('/register')
    def register():
        flash('Registration is restricted. Please contact an administrator to create your account.', 'info')
        return redirect(url_for('auth.login'))
    
    return auth_bp