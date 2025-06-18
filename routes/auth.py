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
                login_user(user)
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                if user.is_admin:
                    return redirect(url_for('admin.dashboard'))
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
    
    return auth_bp