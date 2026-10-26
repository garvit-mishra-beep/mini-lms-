"""Course routes for catalog browsing, course creation, updates, and instructor management."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.auth.decorators import role_required, teacher_required, admin_required
from app.services import course_service, user_service
from app.db import fetch_all, fetch_one

courses_bp = Blueprint('courses', __name__)

def is_teacher_assigned_to_course(teacher_id, course_id):
    """Verify that teacher is an authorized instructor for the specific course."""
    row = fetch_one("""
        SELECT 1 FROM course_instructors
        WHERE course_id = %s AND teacher_id = %s AND is_authorized = 1
    """, (course_id, teacher_id))
    return row is not None

@courses_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', 'ALL')
    courses_list = course_service.get_all_courses(search=search, status=status)
    return render_template('courses/index.html', active='courses', courses=courses_list, search=search, current_status=status)

@courses_bp.route('/<int:course_id>')
@login_required
def detail(course_id):
    course = course_service.get_course_by_id(course_id)
    if not course:
        flash("Course not found.", "error")
        return redirect(url_for('courses.index'))

    instructors = course_service.get_course_instructors(course_id)
    modules = fetch_all("SELECT * FROM modules WHERE course_id = %s ORDER BY sequence_no", (course_id,))
    lessons = fetch_all("""
        SELECT l.*, m.title as module_title, m.sequence_no as module_order
        FROM lessons l
        JOIN modules m ON m.module_id = l.module_id
        WHERE m.course_id = %s
        ORDER BY m.sequence_no, l.sequence_no
    """, (course_id,))
    quizzes = fetch_all("""
        SELECT q.quiz_id, q.title, q.max_score, q.allowed_attempts, q.available_from, q.available_until,
               l.title as lesson_title
        FROM quizzes q
        JOIN lessons l ON l.lesson_id = q.lesson_id
        JOIN modules m ON m.module_id = l.module_id
        WHERE m.course_id = %s
        ORDER BY m.sequence_no, l.sequence_no
    """, (course_id,))

    enrolled_students = fetch_all("""
        SELECT e.enrollment_id, e.status, e.enrolled_at,
               s.student_id, s.roll_no, u.full_name, u.email,
               co.completion_status, g.final_score, g.letter_grade
        FROM enrollments e
        JOIN students s ON s.student_id = e.student_id
        JOIN users u ON u.user_id = s.user_id
        LEFT JOIN completions co ON co.enrollment_id = e.enrollment_id
        LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
        WHERE e.course_id = %s
        ORDER BY e.enrolled_at DESC
    """, (course_id,))

    teachers_list = user_service.get_all_teachers() if current_user.is_admin or current_user.is_teacher else []

    # Check if student is actively enrolled
    student_enrollment = None
    if current_user.is_student and current_user.student_id:
        student_enrollment = fetch_one("""
            SELECT * FROM enrollments
            WHERE student_id = %s AND course_id = %s AND status = 'ACTIVE'
        """, (current_user.student_id, course_id))

    return render_template(
        'courses/detail.html',
        active='courses',
        course=course,
        instructors=instructors,
        modules=modules,
        lessons=lessons,
        quizzes=quizzes,
        enrolled_students=enrolled_students,
        teachers_list=teachers_list,
        student_enrollment=student_enrollment
    )

@courses_bp.route('/create', methods=['GET', 'POST'])
@login_required
@teacher_required
def create():
    if request.method == 'POST':
        code = request.form.get('course_code', '').strip()
        title = request.form.get('title', '').strip()
        desc = request.form.get('description', '').strip()
        teacher_id = request.form.get('teacher_id')
        
        # If teacher creates, assign themselves if teacher_id not provided
        if current_user.is_teacher and not teacher_id and current_user.teacher_id:
            teacher_id = current_user.teacher_id

        if not code or not title:
            flash("Course code and title are required.", "error")
            teachers = user_service.get_all_teachers()
            return render_template('courses/form.html', active='courses', action='Create', teachers=teachers)

        res = course_service.create_course(code, title, desc, teacher_id, current_user.id)
        if res['success']:
            flash(res['message'], "success")
            return redirect(url_for('courses.detail', course_id=res['course_id']))
        else:
            flash(res['message'], "error")

    teachers = user_service.get_all_teachers()
    return render_template('courses/form.html', active='courses', action='Create', teachers=teachers)

@courses_bp.route('/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit(course_id):
    if current_user.is_teacher and not current_user.is_admin:
        if not is_teacher_assigned_to_course(current_user.teacher_id, course_id):
            flash("Access denied: You are not an assigned instructor for this course.", "error")
            abort(403)

    course = course_service.get_course_by_id(course_id)
    if not course:
        flash("Course not found.", "error")
        return redirect(url_for('courses.index'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        desc = request.form.get('description', '').strip()
        if not title:
            flash("Title cannot be empty.", "error")
        else:
            res = course_service.update_course(course_id, title, desc, current_user.id)
            flash(res['message'], "success" if res['success'] else "error")
            return redirect(url_for('courses.detail', course_id=course_id))

    return render_template('courses/form.html', active='courses', action='Edit', course=course)

@courses_bp.route('/<int:course_id>/publish', methods=['POST'])
@login_required
@teacher_required
def publish(course_id):
    if current_user.is_teacher and not current_user.is_admin:
        if not is_teacher_assigned_to_course(current_user.teacher_id, course_id):
            flash("Access denied: You are not an assigned instructor for this course.", "error")
            abort(403)

    res = course_service.publish_course(course_id, current_user.id)
    flash(res['message'], "success" if res['success'] else "error")
    return redirect(url_for('courses.detail', course_id=course_id))

@courses_bp.route('/<int:course_id>/archive', methods=['POST'])
@login_required
@admin_required
def archive(course_id):
    res = course_service.archive_course(course_id, current_user.id)
    flash(res['message'], "success" if res['success'] else "error")
    return redirect(url_for('courses.detail', course_id=course_id))

@courses_bp.route('/<int:course_id>/assign-instructor', methods=['POST'])
@login_required
@admin_required
def assign_instructor(course_id):
    teacher_id = request.form.get('teacher_id')
    role = request.form.get('role', 'INSTRUCTOR')
    if not teacher_id:
        flash("Please select a teacher to assign.", "error")
    else:
        res = course_service.assign_instructor(course_id, int(teacher_id), role, current_user.id)
        flash(res['message'], "success" if res['success'] else "error")
    return redirect(url_for('courses.detail', course_id=course_id))
