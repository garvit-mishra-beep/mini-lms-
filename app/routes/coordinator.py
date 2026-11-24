"""Coordinator routes for institutional and departmental management."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.auth.decorators import coordinator_required
from app.services import academic_service
from app.db import fetch_all

coordinator_bp = Blueprint('coordinator', __name__)

@coordinator_bp.route('/')
@coordinator_bp.route('/dashboard')
@login_required
@coordinator_required
def index():
    overview = academic_service.get_coordinator_overview()
    return render_template('coordinator/dashboard.html', active='coordinator', **overview)

@coordinator_bp.route('/offerings')
@login_required
@coordinator_required
def offerings():
    all_offerings = academic_service.get_all_offerings()
    departments = fetch_all("SELECT * FROM departments WHERE is_active = 1 ORDER BY department_name")
    terms = fetch_all("SELECT * FROM academic_terms ORDER BY start_date DESC")
    courses = fetch_all("SELECT course_id, course_code, title FROM courses WHERE status = 'PUBLISHED' ORDER BY course_code")
    faculty = fetch_all("SELECT t.teacher_id, u.full_name, t.employee_code FROM teachers t JOIN users u ON t.user_id = u.user_id ORDER BY u.full_name")
    return render_template(
        'coordinator/offerings.html',
        active='coordinator_offerings',
        offerings=all_offerings,
        departments=departments,
        terms=terms,
        courses=courses,
        faculty=faculty
    )

@coordinator_bp.route('/offerings/new', methods=['POST'])
@login_required
@coordinator_required
def create_offering():
    course_id = request.form.get('course_id', type=int)
    term_id = request.form.get('term_id', type=int)
    section_name = request.form.get('section_name', 'A').strip().upper()
    max_capacity = request.form.get('max_capacity', 60, type=int)
    teacher_id = request.form.get('teacher_id', type=int) or None

    if not course_id or not term_id or not section_name:
        flash("Course, Term, and Section Name are required.", "error")
        return redirect(url_for('coordinator.offerings'))

    res = academic_service.create_course_offering(
        course_id=course_id,
        term_id=term_id,
        section_name=section_name,
        max_capacity=max_capacity,
        teacher_id=teacher_id,
        actor_user_id=current_user.id
    )
    flash(res['message'], "success" if res['success'] else "error")
    return redirect(url_for('coordinator.offerings'))

@coordinator_bp.route('/offerings/<int:offering_id>/status', methods=['POST'])
@login_required
@coordinator_required
def update_offering_status(offering_id):
    new_status = request.form.get('status', '').strip().upper()
    res = academic_service.update_offering_status(offering_id, new_status, actor_user_id=current_user.id)
    flash(res['message'], "success" if res['success'] else "error")
    return redirect(url_for('coordinator.offerings'))

@coordinator_bp.route('/faculty')
@login_required
@coordinator_required
def faculty_workload():
    workloads = fetch_all("SELECT * FROM v_faculty_workload ORDER BY full_name")
    return render_template('coordinator/faculty.html', active='coordinator_faculty', workloads=workloads)

@coordinator_bp.route('/students')
@login_required
@coordinator_required
def students_overview():
    students = fetch_all("SELECT * FROM v_student_academic_summary ORDER BY roll_no")
    return render_template('coordinator/students.html', active='coordinator_students', students=students)
