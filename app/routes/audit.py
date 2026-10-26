"""Audit and traceability logs route."""
from flask import Blueprint, render_template, request
from flask_login import login_required
from app.auth.decorators import role_required, admin_required, teacher_required
from app.db import fetch_all

audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/')
@login_required
@teacher_required
def index():
    entity_filter = request.args.get('entity', 'ALL')
    action_filter = request.args.get('action', 'ALL')
    search = request.args.get('search', '').strip()

    sql = """
        SELECT a.audit_id, a.entity_name, a.entity_id, a.action_type, a.details, a.action_time,
               u.full_name as actor_name, u.email as actor_email, u.role as actor_role
        FROM audit_logs a
        LEFT JOIN users u ON u.user_id = a.performed_by
        WHERE 1=1
    """
    params = []
    if entity_filter and entity_filter != 'ALL':
        sql += " AND a.entity_name = %s"
        params.append(entity_filter)
    if action_filter and action_filter != 'ALL':
        sql += " AND a.action_type = %s"
        params.append(action_filter)
    if search:
        sql += " AND (a.details LIKE %s OR u.full_name LIKE %s OR a.action_type LIKE %s)"
        pat = f"%{search}%"
        params.extend([pat, pat, pat])

    sql += " ORDER BY a.action_time DESC, a.audit_id DESC LIMIT 200"
    logs = fetch_all(sql, tuple(params))

    # Grade change history records with reason and actor
    history = fetch_all("""
        SELECT h.change_id, h.grade_id, h.old_score, h.new_score, h.reason, h.changed_at,
               u.full_name as actor_name, u.role as actor_role,
               c.course_code, stu_u.full_name as student_name
        FROM grade_change_history h
        JOIN users u ON u.user_id = h.changed_by
        JOIN grades g ON g.grade_id = h.grade_id
        JOIN enrollments e ON e.enrollment_id = g.enrollment_id
        JOIN courses c ON c.course_id = e.course_id
        JOIN students s ON s.student_id = e.student_id
        JOIN users stu_u ON stu_u.user_id = s.user_id
        ORDER BY h.changed_at DESC
        LIMIT 100
    """)

    entities = fetch_all("SELECT DISTINCT entity_name FROM audit_logs ORDER BY entity_name")
    actions = fetch_all("SELECT DISTINCT action_type FROM audit_logs ORDER BY action_type")

    return render_template(
        'audit/index.html',
        active='audit',
        logs=logs,
        history=history,
        entities=[r['entity_name'] for r in entities],
        actions=[r['action_type'] for r in actions],
        current_entity=entity_filter,
        current_action=action_filter,
        search=search
    )
