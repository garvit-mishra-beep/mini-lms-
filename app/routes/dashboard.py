"""Dashboard routes displaying live KPIs, recent activity, and system overview."""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.db import scalar, fetch_all

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    # Fetch live KPI statistics from the actual MySQL database
    metrics = {
        'students': scalar("SELECT COUNT(*) FROM students"),
        'active_students': scalar("SELECT COUNT(*) FROM students s JOIN users u ON u.user_id = s.user_id WHERE u.status = 'ACTIVE'"),
        'teachers': scalar("SELECT COUNT(*) FROM teachers"),
        'courses': scalar("SELECT COUNT(*) FROM courses"),
        'published_courses': scalar("SELECT COUNT(*) FROM courses WHERE status = 'PUBLISHED'"),
        'enrollments': scalar("SELECT COUNT(*) FROM enrollments"),
        'active_enrollments': scalar("SELECT COUNT(*) FROM enrollments WHERE status = 'ACTIVE'"),
        'completions': scalar("SELECT COUNT(*) FROM completions WHERE completion_status = 'COMPLETED'"),
        'quizzes': scalar("SELECT COUNT(*) FROM quizzes"),
        'attempts': scalar("SELECT COUNT(*) FROM attempts"),
        'certificates': scalar("SELECT COUNT(*) FROM certificates")
    }

    # Recent enrollments
    recent_enrollments = fetch_all("""
        SELECT e.enrollment_id, e.status, e.enrolled_at,
               c.course_code, c.title as course_title,
               u.full_name as student_name, s.roll_no
        FROM enrollments e
        JOIN courses c ON c.course_id = e.course_id
        JOIN students s ON s.student_id = e.student_id
        JOIN users u ON u.user_id = s.user_id
        ORDER BY e.enrolled_at DESC, e.enrollment_id DESC
        LIMIT 6
    """)

    # Course enrollment summary view
    course_summary = fetch_all("SELECT * FROM v_course_enrollments ORDER BY total_enrollments DESC LIMIT 6")

    # Recent audit events
    recent_audits = fetch_all("""
        SELECT a.audit_id, a.entity_name, a.entity_id, a.action_type, a.details, a.action_time,
               u.full_name as actor_name
        FROM audit_logs a
        LEFT JOIN users u ON u.user_id = a.performed_by
        ORDER BY a.action_time DESC, a.audit_id DESC
        LIMIT 6
    """)

    # For students: get their personal enrolled courses
    personal_enrollments = []
    if current_user.is_student and current_user.student_id:
        personal_enrollments = fetch_all("""
            SELECT e.enrollment_id, e.status, e.enrolled_at,
                   c.course_id, c.course_code, c.title as course_title,
                   co.completion_status, g.final_score, g.letter_grade
            FROM enrollments e
            JOIN courses c ON c.course_id = e.course_id
            LEFT JOIN completions co ON co.enrollment_id = e.enrollment_id
            LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id AND g.published = 1
            WHERE e.student_id = %s
            ORDER BY e.enrolled_at DESC
        """, (current_user.student_id,))

    return render_template(
        'dashboard/index.html',
        active='dashboard',
        metrics=metrics,
        recent_enrollments=recent_enrollments,
        course_summary=course_summary,
        recent_audits=recent_audits,
        personal_enrollments=personal_enrollments
    )
