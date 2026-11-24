"""Attendance Tracking Routes."""
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.auth.decorators import role_required, teacher_required
from app.services import academic_service
from app.db import fetch_one, fetch_all

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/')
@login_required
def index():
    if current_user.is_student and current_user.student_id:
        # Student Portal: Personal attendance dashboard
        data = academic_service.get_student_attendance(current_user.student_id)
        return render_template('attendance/student_view.html', active='attendance', **data)

    if current_user.is_teacher and current_user.teacher_id:
        # Teacher Portal: Assigned course offerings and sessions
        offerings = academic_service.get_offerings_for_teacher(current_user.teacher_id)
        return render_template('attendance/teacher_view.html', active='attendance', offerings=offerings)

    # Coordinator and Admin Portal: All offerings overview
    offerings = academic_service.get_all_offerings()
    return render_template('attendance/admin_view.html', active='attendance', offerings=offerings)

@attendance_bp.route('/offering/<int:offering_id>')
@login_required
def offering_sessions(offering_id):
    offering = fetch_one("""
        SELECT co.offering_id, co.section_name, co.enrolled_count,
               c.course_code, c.title as course_title,
               t.term_code, t.term_name
        FROM course_offerings co
        JOIN courses c ON co.course_id = c.course_id
        JOIN academic_terms t ON co.term_id = t.term_id
        WHERE co.offering_id = %s
    """, (offering_id,))
    if not offering:
        flash("Course offering section not found.", "error")
        return redirect(url_for('attendance.index'))

    sessions = academic_service.get_attendance_sessions_for_offering(offering_id)
    return render_template(
        'attendance/offering_sessions.html',
        active='attendance',
        offering=offering,
        sessions=sessions,
        today=date.today().isoformat()
    )

@attendance_bp.route('/sessions/new/<int:offering_id>', methods=['POST'])
@login_required
@teacher_required
def create_session(offering_id):
    session_date = request.form.get('session_date', date.today().isoformat())
    topic_covered = request.form.get('topic_covered', 'Regular Lecture').strip()

    # Determine teacher_id: if admin, use assigned primary instructor; if teacher, use current_user.teacher_id
    teacher_id = current_user.teacher_id
    if not teacher_id and current_user.is_admin:
        primary = fetch_one("SELECT teacher_id FROM course_instructors WHERE offering_id = %s AND role_in_course = 'PRIMARY'", (offering_id,))
        teacher_id = primary['teacher_id'] if primary else 1

    res = academic_service.create_attendance_session(
        offering_id=offering_id,
        teacher_id=teacher_id,
        session_date=session_date,
        topic_covered=topic_covered
    )
    if res['success']:
        flash("Lecture session created. Please record student roll call.", "success")
        return redirect(url_for('attendance.session_roll_call', session_id=res['session_id']))
    else:
        flash(res['message'], "error")
        return redirect(url_for('attendance.offering_sessions', offering_id=offering_id))

@attendance_bp.route('/sessions/<int:session_id>')
@login_required
def session_roll_call(session_id):
    sess, students = academic_service.get_session_roll_call(session_id)
    if not sess:
        flash("Attendance session not found.", "error")
        return redirect(url_for('attendance.index'))

    return render_template(
        'attendance/session_roll_call.html',
        active='attendance',
        session=sess,
        students=students
    )

@attendance_bp.route('/sessions/<int:session_id>/mark', methods=['POST'])
@login_required
@teacher_required
def mark_attendance(session_id):
    sess = fetch_one("SELECT offering_id FROM attendance_sessions WHERE session_id = %s", (session_id,))
    if not sess:
        flash("Session not found.", "error")
        return redirect(url_for('attendance.index'))

    # Gather submitted attendance statuses
    records = []
    for key, value in request.form.items():
        if key.startswith('status_'):
            enrollment_id = int(key.replace('status_', ''))
            remarks = request.form.get(f'remarks_{enrollment_id}', '')
            records.append({
                'enrollment_id': enrollment_id,
                'status': value,
                'remarks': remarks
            })

    res = academic_service.save_roll_call(session_id, records)
    flash(res['message'], "success" if res['success'] else "error")
    return redirect(url_for('attendance.session_roll_call', session_id=session_id))
