from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

def create_account_blueprint(db, User, Member):
    account_bp = Blueprint('account', __name__, url_prefix='/account')
    
    @account_bp.route('/profile')
    @login_required
    def profile():
        """Display user profile information"""
        member = Member.query.filter_by(user_id=current_user.id).first()
        return render_template('account/profile.html', user=current_user, member=member)
    
    @account_bp.route('/edit', methods=['GET', 'POST'])
    @login_required
    def edit_profile():
        """Edit user profile"""
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
            return redirect(url_for('account.profile'))
        
        return render_template('account/edit.html', user=current_user)
    
    @account_bp.route('/change-password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        """Change user password"""
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
            return redirect(url_for('account.profile'))
        
        return render_template('account/change_password.html')
    
    @account_bp.route('/settings')
    @login_required
    def settings():
        """User account settings"""
        return render_template('account/settings.html', user=current_user)
    
    return account_bp