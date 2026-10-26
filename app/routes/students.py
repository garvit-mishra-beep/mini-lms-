"""Student management routes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.auth.decorators import role_required, admin_required, teacher_required
from app.services import user_service

students_bp = Blueprint('students', __name__)

@students_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', 'ALL')
    students_list = user_service.get_all_students(search=search, status=status)
    return render_template('students/index.html', active='students', students=students_list, search=search, current_status=status)

@students_bp.route('/<int:student_id>')
@login_required
def profile(student_id):
    # Enforce student privacy: students can only view their own profile; admins & teachers can view all
    if current_user.is_student and current_user.student_id != student_id:
        flash("You are only permitted to view your own student profile.", "warning")
        return redirect(url_for('students.profile', student_id=current_user.student_id))

    student = user_service.get_student_profile(student_id)
    if not student:
        flash("Student not found.", "error")
        return redirect(url_for('students.index'))

    return render_template('students/profile.html', active='students', student=student)

@students_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        roll_no = request.form.get('roll_no', '').strip()
        enrollment_no = request.form.get('enrollment_no', '').strip()
        phone = request.form.get('phone', '').strip()
        dob = request.form.get('dob') or None

        if not full_name or not email or not roll_no or not enrollment_no:
            flash("Full name, email, roll number, and enrollment number are required.", "error")
            return render_template('students/form.html', active='students')

        res = user_service.add_student(full_name, email, roll_no, enrollment_no, phone, dob, current_user.id)
        if res['success']:
            flash(res['message'], "success")
            return redirect(url_for('students.profile', student_id=res['student_id']))
        else:
            flash(res['message'], "error")

    return render_template('students/form.html', active='students')

@students_bp.route('/<int:student_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_status(student_id):
    student = user_service.get_student_profile(student_id)
    if not student:
        flash("Student not found.", "error")
        return redirect(url_for('students.index'))

    res = user_service.toggle_user_status(student['user_id'], current_user.id)
    flash(res['message'], "success" if res['success'] else "error")
    return redirect(url_for('students.profile', student_id=student_id))
