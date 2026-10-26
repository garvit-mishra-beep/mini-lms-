"""Teacher directory routes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.services import user_service
from app.db import fetch_all, fetch_one

teachers_bp = Blueprint('teachers', __name__)

@teachers_bp.route('/')
@login_required
def index():
    teachers = user_service.get_all_teachers()
    return render_template('teachers/index.html', active='teachers', teachers=teachers)

@teachers_bp.route('/<int:teacher_id>')
@login_required
def profile(teacher_id):
    teacher = fetch_one("""
        SELECT t.teacher_id, t.user_id, t.employee_code, t.qualification, t.bio, t.phone_no,
               u.full_name, u.email, u.status, u.created_at
        FROM teachers t
        JOIN users u ON u.user_id = t.user_id
        WHERE t.teacher_id = %s
    """, (teacher_id,))
    if not teacher:
        flash("Teacher not found.", "error")
        return redirect(url_for('teachers.index'))

    assigned_courses = fetch_all("""
        SELECT c.course_id, c.course_code, c.title, c.status, ci.instructor_role, ci.assigned_at,
               COUNT(DISTINCT e.enrollment_id) as student_count
        FROM course_instructors ci
        JOIN courses c ON c.course_id = ci.course_id
        LEFT JOIN enrollments e ON e.course_id = c.course_id
        WHERE ci.teacher_id = %s AND ci.is_authorized = 1
        GROUP BY c.course_id, c.course_code, c.title, c.status, ci.instructor_role, ci.assigned_at
        ORDER BY c.course_code
    """, (teacher_id,))

    teacher['courses'] = assigned_courses
    return render_template('teachers/profile.html', active='teachers', teacher=teacher)
