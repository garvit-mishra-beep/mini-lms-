"""Settings and System Health route."""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.db import fetch_all, fetch_one, scalar
from app.config import Config

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
@login_required
def index():
    # Database connection metadata
    server_info = fetch_one("""
        SELECT VERSION() as mysql_version,
               DATABASE() as current_db,
               USER() as db_user,
               NOW() as db_time,
               @@GLOBAL.time_zone as timezone
    """)

    # Schema versions
    schema_versions = fetch_all("SELECT * FROM schema_versions ORDER BY version_no ASC")

    # Table counts
    table_count = scalar("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE'")
    view_count = scalar("SELECT COUNT(*) FROM information_schema.views WHERE table_schema = DATABASE()")
    routine_count = scalar("SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema = DATABASE()")
    trigger_count = scalar("SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = DATABASE()")

    config_info = {
        'host': Config.DB_HOST,
        'port': Config.DB_PORT,
        'database': Config.DB_NAME,
        'user': Config.DB_USER,
        'secret_key_set': bool(Config.SECRET_KEY),
        'flask_port': Config.PORT
    }

    return render_template(
        'settings/index.html',
        active='settings',
        server_info=server_info,
        schema_versions=schema_versions,
        table_count=table_count,
        view_count=view_count,
        routine_count=routine_count,
        trigger_count=trigger_count,
        config_info=config_info
    )
