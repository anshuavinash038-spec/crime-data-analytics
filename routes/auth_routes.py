from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app, Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models.user_model import User
from services.activity_service import ActivityService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash(f'You are currently signed in as {current_user.name} ({current_user.email}). To switch accounts, please log out.', 'info')
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('dashboard.index'))

    email = request.args.get('email', '').strip()

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = True if request.form.get('remember') else False

        user = User.get_by_email(email)
        if not user or not user.check_password(password):
            flash('Invalid email address or password. Please try again.', 'danger')
            return render_template('login.html', email=email)

        # Check if account is active / disabled
        if not user.is_active:
            flash('Your account has been deactivated. Please contact a system administrator.', 'danger')
            return render_template('login.html', email=email)

        login_user(user, remember=remember)
        ActivityService.log(
            "Admin Login" if user.is_admin else "User Login",
            f"User authenticated successfully with role {user.role}",
            user_id=user.id, user_name=user.name, user_email=user.email
        )
        flash(f'Welcome back, {user.name}!', 'success')

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            from urllib.parse import urlsplit
            parsed = urlsplit(next_page)
            # Block protocol-relative URLs like //attacker.com
            if not parsed.netloc and not parsed.scheme:
                return redirect(next_page)

        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('dashboard.index'))

    return render_template('login.html', email=email)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash(f'You are currently signed in as {current_user.name}. Please logout to register a new account.', 'info')
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html', name=name, email=email)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html', name=name, email=email)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', name=name, email=email)

        existing = User.get_by_email(email)
        if existing:
            flash('An account with this email already exists.', 'warning')
            return render_template('register.html', name=name)

        # Normal registration ALWAYS creates role="USER" with is_active=1 (Active)
        user = User.create_user(name=name, email=email, password=password, role="USER")
        ActivityService.log(
            "User Registration",
            f"New user registered: {name} ({email})",
            user_id=user.id, user_name=user.name, user_email=user.email
        )
        flash('Account registered and activated successfully! Please enter your password to login.', 'success')
        return redirect(url_for('auth.login', email=email))

    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    if current_user and current_user.is_authenticated:
        ActivityService.log(
            "User Logout",
            "User signed out safely",
            user_id=current_user.id, user_name=current_user.name, user_email=current_user.email
        )
    logout_user()
    session.clear()
    flash('You have been logged out safely.', 'info')
    resp = redirect(url_for('auth.login'))
    remember_cookie = current_app.config.get('REMEMBER_COOKIE_NAME', 'remember_token')
    resp.delete_cookie(remember_cookie)
    return resp

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Full name cannot be blank.', 'danger')
        return redirect(url_for('auth.profile'))

    User.update_profile(current_user.id, name)
    ActivityService.log("Update Profile", f"User updated profile name to '{name}'")
    flash('Profile details updated successfully!', 'success')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    current_pwd = request.form.get('current_password', '')
    new_pwd = request.form.get('new_password', '')
    confirm_pwd = request.form.get('confirm_password', '')

    if not current_user.check_password(current_pwd):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('auth.profile'))

    if len(new_pwd) < 6:
        flash('New password must be at least 6 characters long.', 'danger')
        return redirect(url_for('auth.profile'))

    if new_pwd != confirm_pwd:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('auth.profile'))

    User.update_password(current_user.id, new_pwd)
    ActivityService.log("Password Change", "User changed their password successfully")
    flash('Your password has been changed successfully!', 'success')
    return redirect(url_for('auth.profile'))

def get_reset_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.get_by_email(email)
        
        if user:
            s = get_reset_serializer()
            token = s.dumps(email, salt='password-reset-salt')
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            flash(f'Password reset link generated! <a href="{reset_url}" class="alert-link">Click here to reset your password</a>. (Simulated email delivery)', 'info')
        else:
            flash('If an account with that email exists, a password reset link has been dispatched.', 'info')
            
        return redirect(url_for('auth.login'))
        
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    s = get_reset_serializer()
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        flash('The password reset link has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    except BadSignature:
        flash('Invalid password reset link.', 'danger')
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or password != confirm_password:
            flash('Passwords must match and cannot be empty.', 'danger')
            return render_template('reset_password.html', token=token)
            
        user = User.get_by_email(email)
        if user:
            User.update_password(user.id, password)
            ActivityService.log("Password Reset", f"Password reset completed for email: {email}")
            flash('Your password has been updated! You are now able to log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Account not found.', 'danger')
            return redirect(url_for('auth.login'))
            
    return render_template('reset_password.html', token=token)
