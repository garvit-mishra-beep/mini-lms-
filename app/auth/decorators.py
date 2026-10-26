"""Role-based authorization decorators."""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def role_required(*allowed_roles):
    """Decorator ensuring current user is authenticated and possesses one of the allowed roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('auth.login'))
            if not current_user.is_active:
                flash("Your account is currently inactive. Contact your administrator.", "error")
                return redirect(url_for('auth.logout'))
            if current_user.role not in allowed_roles:
                flash(f"Access denied: {current_user.role} is not authorized for this action.", "error")
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return role_required('ADMIN')(f)

def teacher_required(f):
    return role_required('ADMIN', 'TEACHER')(f)

def student_required(f):
    return role_required('ADMIN', 'STUDENT')(f)
