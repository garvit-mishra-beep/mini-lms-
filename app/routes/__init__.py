"""Route blueprints package."""
from app.routes.dashboard import dashboard_bp
from app.routes.courses import courses_bp
from app.routes.students import students_bp
from app.routes.teachers import teachers_bp
from app.routes.enrollments import enrollments_bp
from app.routes.modules import modules_bp
from app.routes.quizzes import quizzes_bp
from app.routes.grades import grades_bp
from app.routes.certificates import certificates_bp
from app.routes.analytics import analytics_bp
from app.routes.audit import audit_bp
from app.routes.explorer import explorer_bp
from app.routes.settings import settings_bp

__all__ = [
    'dashboard_bp',
    'courses_bp',
    'students_bp',
    'teachers_bp',
    'enrollments_bp',
    'modules_bp',
    'quizzes_bp',
    'grades_bp',
    'certificates_bp',
    'analytics_bp',
    'audit_bp',
    'explorer_bp',
    'settings_bp'
]
