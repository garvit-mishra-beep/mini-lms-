"""Enrollment routes managing course enrollments, status transitions, and conflict handling."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.auth.decorators import role_required, admin_required, teacher_required
from app.services import enrollment_service
from app.db import fetch_all, fetch_one

enrollments_bp = Blueprint('enrollments', __name__)

@enrollments_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    # If POST request, process new enrollment
    if request.method == 'POST':
        # If logged in as student, self-enroll; otherwise take from form
        if current_user.is_student:
            student_id = current_user.student_id
        else:
            student_id = request.form.get('student_id')
            student_id = int(student_id) if student_id else None

        course_id = request.form.get('course_id')
        course_id = int(course_id) if course_id else None

        if not student_id or not course_id:
            flash("Please select both a student and a course.", "error")
        else:
            res = enrollment_service.enroll_student(student_id, course_id, current_user.id)
            if res['success']:
                flash(res['message'], "success")
                return redirect(url_for('enrollments.detail', enrollment_id=res['enrollment_id']))
            else:
                if res.get('conflict') and res.get('existing_enrollment_id'):
                    flash(f"{res['message']} (Existing Enrollment #{res['existing_enrollment_id']})", "warning")
                    return redirect(url_for('enrollments.detail', enrollment_id=res['existing_enrollment_id']))
                else:
                    flash(res['message'], "error")

    # Filters
    course_filter = request.args.get('course_id', '')
    status_filter = request.args.get('status', 'ALL')
    search = request.args.get('search', '').strip()

    sql = """
        SELECT e.enrollment_id, e.student_id, e.course_id, e.status, e.enrolled_at,
               c.course_code, c.title as course_title,
               s.roll_no, u.full_name as student_name, u.email as student_email,
               co.completion_status, co.completed_at,
               g.final_score, g.letter_grade
        FROM enrollments e
        JOIN courses c ON c.course_id = e.course_id
        JOIN students s ON s.student_id = e.student_id
        JOIN users u ON u.user_id = s.user_id
        LEFT JOIN completions co ON co.enrollment_id = e.enrollment_id
        LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
        WHERE 1=1
    """
    params = []

    # If student, show only their own enrollments
    if current_user.is_student:
        sql += " AND e.student_id = %s"
        params.append(current_user.student_id)

    if course_filter:
        sql += " AND e.course_id = %s"
        params.append(int(course_filter))
    if status_filter and status_filter != 'ALL':
        sql += " AND e.status = %s"
        params.append(status_filter)
    if search:
        sql += " AND (u.full_name LIKE %s OR s.roll_no LIKE %s OR c.course_code LIKE %s OR c.title LIKE %s)"
        pat = f"%{search}%"
        params.extend([pat, pat, pat, pat])

    sql += " ORDER BY e.enrolled_at DESC, e.enrollment_id DESC"
    enrollments_list = fetch_all(sql, tuple(params))

    # Form dropdown datasets
    students_dropdown = fetch_all("""
        SELECT s.student_id, u.full_name, u.status, s.roll_no
        FROM students s
        JOIN users u ON u.user_id = s.user_id
        ORDER BY u.full_name
    """)
    courses_dropdown = fetch_all("""
        SELECT course_id, course_code, title
        FROM courses
        WHERE status = 'PUBLISHED'
        ORDER BY course_code
    """)

    return render_template(
        'enrollments/index.html',
        active='enrollments',
        enrollments=enrollments_list,
        students=students_dropdown,
        courses=courses_dropdown,
        course_filter=course_filter,
        status_filter=status_filter,
        search=search
    )

@enrollments_bp.route('/<int:enrollment_id>')
@login_required
def detail(enrollment_id):
    enrollment = enrollment_service.get_enrollment_by_id(enrollment_id)
    if not enrollment:
        flash("Enrollment record not found.", "error")
        return redirect(url_for('enrollments.index'))

    # If student, verify this enrollment belongs to them
    if current_user.is_student and current_user.student_id != enrollment['student_id']:
        flash("You are only authorized to view your own enrollment details.", "error")
        return redirect(url_for('enrollments.index'))

    # Lessons progress in this course
    progress = fetch_all("""
        SELECT l.lesson_id, l.title, l.sequence_no, lp.completed_at
        FROM lessons l
        JOIN modules m ON m.module_id = l.module_id
        LEFT JOIN lesson_progress lp ON lp.lesson_id = l.lesson_id AND lp.enrollment_id = %s
        WHERE m.course_id = %s
        ORDER BY m.sequence_no, l.sequence_no
    """, (enrollment_id, enrollment['course_id']))

    # Quiz attempts in this enrollment
    attempts = fetch_all("""
        SELECT a.attempt_id, a.attempt_no, a.started_at, a.submitted_at, a.score, a.status,
               q.quiz_id, q.title as quiz_title, q.max_score
        FROM attempts a
        JOIN quizzes q ON q.quiz_id = a.quiz_id
        WHERE a.enrollment_id = %s
        ORDER BY a.started_at DESC
    """, (enrollment_id,))

    return render_template(
        'enrollments/detail.html',
        active='enrollments',
        enrollment=enrollment,
        progress=progress,
        attempts=attempts
    )

@enrollments_bp.route('/<int:enrollment_id>/cancel', methods=['POST'])
@login_required
def cancel(enrollment_id):
    enrollment = enrollment_service.get_enrollment_by_id(enrollment_id)
    if not enrollment:
        flash("Enrollment not found.", "error")
        return redirect(url_for('enrollments.index'))

    # Check permission
    if current_user.is_student and current_user.student_id != enrollment['student_id']:
        flash("Unauthorized action.", "error")
        return redirect(url_for('enrollments.index'))

    res = enrollment_service.cancel_enrollment(enrollment_id, current_user.id)
    flash(res['message'], "success" if res['success'] else "error")
    return redirect(url_for('enrollments.detail', enrollment_id=enrollment_id))

@enrollments_bp.route('/<int:enrollment_id>/evaluate', methods=['POST'])
@login_required
@teacher_required
def evaluate(enrollment_id):
    res = enrollment_service.complete_enrollment(enrollment_id, current_user.id)
    flash(res['message'], "info" if res['success'] else "error")
    return redirect(url_for('enrollments.detail', enrollment_id=enrollment_id))
