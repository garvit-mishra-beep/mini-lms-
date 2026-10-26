"""Authentication routes."""
import secrets
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.auth.models import User
from app.db import record_audit_log
from app.config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    demo_mode_enabled = current_app.config.get('DEMO_MODE', False)
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template('auth/login.html', demo_mode=demo_mode_enabled)

        user = User.get_by_email(email)
        if not user or not user.check_password(password):
            flash("Invalid email or password. Please try again.", "error")
            return render_template('auth/login.html', demo_mode=demo_mode_enabled)

        if not user.is_active:
            flash("Your account is inactive. Please contact the administrator.", "error")
            return render_template('auth/login.html', demo_mode=demo_mode_enabled)

        login_user(user, remember=True)
        session['csrf_token'] = secrets.token_hex(32)
        record_audit_log('users', user.id, 'LOGIN', user.id, f"Logged in as {user.role}")
        flash(f"Welcome back, {user.full_name} ({user.role})!", "success")
        return redirect(url_for('dashboard.index'))

    # GET request - pass sample demo accounts to template ONLY if DEMO_MODE is enabled
    demo_accounts = []
    if demo_mode_enabled:
        demo_accounts = [
            {'role': 'ADMIN', 'name': 'Demo Admin', 'email': 'admin@example.test', 'badge': 'badge-primary'},
            {'role': 'TEACHER', 'name': 'Dr Anita Sharma', 'email': 'anita@example.test', 'badge': 'badge-info'},
            {'role': 'STUDENT', 'name': 'Aarav Singh', 'email': 'aarav@example.test', 'badge': 'badge-success'},
        ]
    return render_template('auth/login.html', demo_accounts=demo_accounts, demo_mode=demo_mode_enabled)

@auth_bp.route('/demo-login/<role>', methods=['GET', 'POST'])
def demo_login(role):
    """
    Convenience 1-click demo switcher for academic PBL viva evaluation.
    Strictly restricted to environments where DEMO_MODE=True and only accessible locally.
    """
    if not current_app.config.get('DEMO_MODE', False):
        abort(403)

    # Additional environment security: restrict to localhost loopback
    remote = request.remote_addr or ''
    if remote not in ('127.0.0.1', '::1', 'localhost', 'testclient'):
        record_audit_log('users', 0, 'UNAUTHORIZED_DEMO_LOGIN_ATTEMPT', None, f"Remote IP {remote} blocked from demo-login")
        abort(403)

    role_map = {
        'admin': 'admin@example.test',
        'teacher': 'anita@example.test',
        'student': 'aarav@example.test'
    }
    email = role_map.get(role.lower())
    if not email:
        flash("Invalid demo role specified.", "error")
        return redirect(url_for('auth.login'))

    user = User.get_by_email(email)
    if not user:
        flash(f"Demo user for role {role} not found in database.", "error")
        return redirect(url_for('auth.login'))

    login_user(user, remember=True)
    session['csrf_token'] = secrets.token_hex(32)
    record_audit_log('users', user.id, 'DEMO_LOGIN', user.id, f"Switched role to {user.role} (local viva demo mode)")
    flash(f"Logged in as {user.full_name} ({user.role}) via Quick Demo Switcher.", "success")
    return redirect(url_for('dashboard.index'))

@auth_bp.route('/logout')
@login_required
def logout():
    record_audit_log('users', current_user.id, 'LOGOUT', current_user.id, "Logged out")
    logout_user()
    session.pop('csrf_token', None)
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('auth.login'))
