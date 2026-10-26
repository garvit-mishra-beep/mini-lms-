"""Grades and Gradebook routes with strict course-level instructor authorization."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.auth.decorators import role_required, teacher_required
from app.services import grading_service
from app.db import fetch_all, fetch_one

grades_bp = Blueprint('grades', __name__)

def is_teacher_authorized_for_enrollment(teacher_id, enrollment_id):
    """Check if teacher is an authorized instructor for this enrollment's course."""
    row = fetch_one("""
        SELECT 1 FROM course_instructors ci
        JOIN enrollments e ON e.course_id = ci.course_id
        WHERE e.enrollment_id = %s AND ci.teacher_id = %s AND ci.is_authorized = 1
    """, (enrollment_id, teacher_id))
    return row is not None

def is_teacher_authorized_for_grade(teacher_id, grade_id):
    """Check if teacher is an authorized instructor for this grade's course."""
    row = fetch_one("""
        SELECT 1 FROM course_instructors ci
        JOIN enrollments e ON e.course_id = ci.course_id
        JOIN grades g ON g.enrollment_id = e.enrollment_id
        WHERE g.grade_id = %s AND ci.teacher_id = %s AND ci.is_authorized = 1
    """, (grade_id, teacher_id))
    return row is not None

@grades_bp.route('/')
@login_required
def index():
    overview = grading_service.get_grades_overview()
    
    # If student, filter student grades for current student only
    if current_user.is_student and current_user.student_id:
        student_grades = fetch_all("""
            SELECT g.grade_id, g.enrollment_id, g.final_score, g.letter_grade, g.published, g.published_at,
                   c.course_code, c.title as course_title, co.completion_status
            FROM grades g
            JOIN enrollments e ON e.enrollment_id = g.enrollment_id
            JOIN courses c ON c.course_id = e.course_id
            LEFT JOIN completions co ON co.enrollment_id = e.enrollment_id
            WHERE e.student_id = %s
            ORDER BY c.course_code
        """, (current_user.student_id,))
        overview['my_grades'] = student_grades

    return render_template('grades/index.html', active='grades', **overview)

@grades_bp.route('/publish/<int:enrollment_id>', methods=['POST'])
@login_required
@teacher_required
def publish(enrollment_id):
    # Verify course-level teacher authorization
    if current_user.is_teacher and not current_user.is_admin:
        if not is_teacher_authorized_for_enrollment(current_user.teacher_id, enrollment_id):
            flash("Access denied: You are not an authorized instructor for this course.", "error")
            abort(403)

    res = grading_service.publish_course_grade(enrollment_id, current_user.id)
    flash(res['message'], "success" if res['success'] else "error")
    return redirect(url_for('grades.index'))

@grades_bp.route('/correct/<int:grade_id>', methods=['POST'])
@login_required
@teacher_required
def correct(grade_id):
    # Verify course-level teacher authorization
    if current_user.is_teacher and not current_user.is_admin:
        if not is_teacher_authorized_for_grade(current_user.teacher_id, grade_id):
            flash("Access denied: You are not an authorized instructor for this course.", "error")
            abort(403)

    score = request.form.get('final_score')
    reason = request.form.get('reason', '').strip()
    
    if not score or not reason:
        flash("Score and change reason are required for authorized grade corrections.", "error")
        return redirect(url_for('grades.index'))

    res = grading_service.correct_grade(grade_id, score, reason, current_user.id)
    flash(res['message'], "success" if res['success'] else "error")
    return redirect(url_for('grades.index'))
