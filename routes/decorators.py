from functools import wraps
from flask import abort, redirect, url_for, request
from flask_login import current_user

def admin_required(f):
    """
    Decorator to protect routes requiring Administrator privileges.
    Returns HTTP 403 Forbidden if current_user is authenticated but not an admin.
    Redirects unauthenticated visitors to login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
