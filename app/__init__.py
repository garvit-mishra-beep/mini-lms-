"""MiniLMS Application Factory."""
import os
import secrets
from decimal import Decimal
from datetime import datetime
from flask import Flask, render_template, request, jsonify, abort, session, redirect, url_for, flash
from flask_login import LoginManager, current_user
import pymysql

from app.config import Config
from app.auth.models import User

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    login_manager.init_app(app)

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.routes import (
        dashboard_bp,
        courses_bp,
        students_bp,
        teachers_bp,
        enrollments_bp,
        modules_bp,
        quizzes_bp,
        grades_bp,
        certificates_bp,
        analytics_bp,
        audit_bp,
        explorer_bp,
        settings_bp
    )

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='')
    app.register_blueprint(courses_bp, url_prefix='/courses')
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(teachers_bp, url_prefix='/teachers')
    app.register_blueprint(enrollments_bp, url_prefix='/enrollments')
    app.register_blueprint(modules_bp, url_prefix='/modules')
    app.register_blueprint(quizzes_bp, url_prefix='/quizzes')
    app.register_blueprint(grades_bp, url_prefix='/grades')
    app.register_blueprint(certificates_bp, url_prefix='/certificates')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(audit_bp, url_prefix='/audit')
    app.register_blueprint(explorer_bp, url_prefix='/explorer')
    app.register_blueprint(settings_bp, url_prefix='/settings')

    # Backward compatibility redirect for old /enroll route
    @app.route('/enroll', methods=['GET', 'POST'])
    def legacy_enroll():
        return redirect(url_for('enrollments.index'), code=307 if request.method == 'POST' else 302)

    # CSRF Protection & Session Token Management
    @app.before_request
    def handle_csrf_and_session():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)

        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            # Allow explicit test bypass with testing config and special header if needed
            if app.config.get('TESTING') and request.headers.get('X-Skip-CSRF') == '1':
                return

            submitted_token = (
                request.form.get('csrf_token') or
                request.headers.get('X-CSRF-Token') or
                (request.get_json(silent=True) or {}).get('csrf_token')
            )
            session_token = session.get('csrf_token', '')

            if not submitted_token or not secrets.compare_digest(str(submitted_token), str(session_token)):
                abort(400, description="Security verification failed: invalid or missing CSRF token.")

    # Custom Jinja template filters
    @app.template_filter('human')
    def human_filter(v):
        if v is None:
            return '—'
        if isinstance(v, Decimal):
            return str(v)
        return str(v)

    @app.template_filter('date_fmt')
    def date_filter(v, fmt='%b %d, %Y'):
        if not v:
            return '—'
        if isinstance(v, (datetime,)):
            return v.strftime(fmt)
        return str(v)

    @app.template_filter('status_badge')
    def status_badge_filter(status):
        badges = {
            'ACTIVE': 'badge-success',
            'PUBLISHED': 'badge-success',
            'COMPLETED': 'badge-primary',
            'SUBMITTED': 'badge-primary',
            'DRAFT': 'badge-warning',
            'IN_PROGRESS': 'badge-warning',
            'INACTIVE': 'badge-secondary',
            'ARCHIVED': 'badge-secondary',
            'CANCELLED': 'badge-danger'
        }
        return badges.get(str(status).upper(), 'badge-secondary')

    # Context processors
    @app.context_processor
    def inject_context():
        # Ensure csrf_token is available to templates
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        return {
            'csrf_token': session.get('csrf_token', ''),
            'now': datetime.now()
        }

    # Health check endpoint
    @app.route('/health')
    def health():
        from app.db import scalar
        try:
            tbl_count = scalar("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_type='BASE TABLE'")
            return jsonify(
                status='connected',
                database=app.config['DB_NAME'],
                tables=tbl_count
            )
        except pymysql.MySQLError as exc:
            safe_err = str(exc) if app.config.get('DEBUG') else "Database connection unavailable."
            return jsonify(status='unavailable', error=safe_err), 503

    # Error Handlers
    @app.errorhandler(400)
    def bad_request_error(e):
        msg = getattr(e, 'description', 'Invalid request')
        return render_template('errors/400.html', description=msg), 400

    @app.errorhandler(403)
    def forbidden_error(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        err_detail = str(e) if app.config.get('DEBUG') else "An internal server error occurred. Application state has been securely preserved."
        return render_template('errors/500.html', error=err_detail), 500

    @app.errorhandler(503)
    def service_unavailable_error(e):
        err_detail = str(e) if app.config.get('DEBUG') else "Service is temporarily unavailable."
        return render_template('offline.html', error=err_detail), 503

    return app
