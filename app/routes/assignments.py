"""Coursework Assignments and Student Submissions Routes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.auth.decorators import role_required, teacher_required, student_required
from app.services import academic_service
from app.db import fetch_one, fetch_all

assignments_bp = Blueprint('assignments', __name__)

@assignments_bp.route('/')
@login_required
def index():
    if current_user.is_student and current_user.student_id:
        # Student view: Coursework for enrolled courses
        assignments = academic_service.get_student_assignments(current_user.student_id)
        return render_template('assignments/student_list.html', active='assignments', assignments=assignments)

    if current_user.is_teacher and current_user.teacher_id:
        # Teacher view: Offerings and assignments
        offerings = academic_service.get_offerings_for_teacher(current_user.teacher_id)
        assignments = fetch_all("""
            SELECT a.assignment_id, a.offering_id, a.title, a.max_marks, a.weightage_pct, a.due_date,
                   c.course_code, c.title as course_title, co.section_name,
                   COUNT(s.submission_id) as submission_count,
                   SUM(CASE WHEN s.status = 'EVALUATED' THEN 1 ELSE 0 END) as evaluated_count
            FROM assignments a
            JOIN course_offerings co ON a.offering_id = co.offering_id
            JOIN courses c ON co.course_id = c.course_id
            JOIN course_instructors ci ON co.offering_id = ci.offering_id
            LEFT JOIN submissions s ON a.assignment_id = s.assignment_id
            WHERE ci.teacher_id = %s
            GROUP BY a.assignment_id, a.offering_id, a.title, a.max_marks, a.weightage_pct, a.due_date,
                     c.course_code, c.title, co.section_name
            ORDER BY a.due_date DESC
        """, (current_user.teacher_id,))
        return render_template(
            'assignments/teacher_list.html',
            active='assignments',
            offerings=offerings,
            assignments=assignments
        )

    # Coordinator and Admin view: All coursework across all offerings
    assignments = fetch_all("""
        SELECT a.assignment_id, a.offering_id, a.title, a.max_marks, a.weightage_pct, a.due_date,
               c.course_code, c.title as course_title, co.section_name,
               u.full_name as teacher_name,
               COUNT(s.submission_id) as submission_count,
               SUM(CASE WHEN s.status = 'EVALUATED' THEN 1 ELSE 0 END) as evaluated_count
        FROM assignments a
        JOIN course_offerings co ON a.offering_id = co.offering_id
        JOIN courses c ON co.course_id = c.course_id
        JOIN teachers t ON a.created_by = t.teacher_id
        JOIN users u ON t.user_id = u.user_id
        LEFT JOIN submissions s ON a.assignment_id = s.assignment_id
        GROUP BY a.assignment_id, a.offering_id, a.title, a.max_marks, a.weightage_pct, a.due_date,
                 c.course_code, c.title, co.section_name, u.full_name
        ORDER BY a.due_date DESC
    """)
    offerings = academic_service.get_all_offerings()
    return render_template(
        'assignments/admin_list.html',
        active='assignments',
        assignments=assignments,
        offerings=offerings
    )

@assignments_bp.route('/offering/<int:offering_id>/new', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_assignment(offering_id):
    offering = fetch_one("""
        SELECT co.offering_id, co.section_name, c.course_code, c.title as course_title
        FROM course_offerings co
        JOIN courses c ON co.course_id = c.course_id
        WHERE co.offering_id = %s
    """, (offering_id,))
    if not offering:
        flash("Offering not found.", "error")
        return redirect(url_for('assignments.index'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        max_marks = request.form.get('max_marks', 100.0, type=float)
        weightage_pct = request.form.get('weightage_pct', 10.0, type=float)
        due_date = request.form.get('due_date', '').strip()

        if not title or not due_date:
            flash("Title and Due Date are mandatory.", "error")
            return redirect(url_for('assignments.create_assignment', offering_id=offering_id))

        teacher_id = current_user.teacher_id or 1
        res = academic_service.create_assignment(
            offering_id=offering_id,
            title=title,
            description=description,
            max_marks=max_marks,
            weightage_pct=weightage_pct,
            due_date=due_date,
            teacher_id=teacher_id
        )
        flash(res['message'], "success" if res['success'] else "error")
        return redirect(url_for('assignments.index'))

    return render_template('assignments/create.html', active='assignments', offering=offering)

@assignments_bp.route('/<int:assignment_id>')
@login_required
def details(assignment_id):
    assign = academic_service.get_assignment_by_id(assignment_id)
    if not assign:
        flash("Assignment not found.", "error")
        return redirect(url_for('assignments.index'))

    submission = None
    enrollment = None
    if current_user.is_student and current_user.student_id:
        enrollment = fetch_one("""
            SELECT enrollment_id FROM enrollments
            WHERE student_id = %s AND offering_id = %s AND status = 'ACTIVE'
        """, (current_user.student_id, assign['offering_id']))
        if enrollment:
            submission = fetch_one("""
                SELECT * FROM submissions
                WHERE assignment_id = %s AND enrollment_id = %s
            """, (assignment_id, enrollment['enrollment_id']))

    return render_template(
        'assignments/details.html',
        active='assignments',
        assignment=assign,
        submission=submission,
        enrollment=enrollment
    )

@assignments_bp.route('/<int:assignment_id>/submit', methods=['POST'])
@login_required
def submit(assignment_id):
    if not current_user.is_student or not current_user.student_id:
        flash("Only enrolled students can submit coursework.", "error")
        return redirect(url_for('assignments.details', assignment_id=assignment_id))

    assign = academic_service.get_assignment_by_id(assignment_id)
    if not assign:
        flash("Assignment not found.", "error")
        return redirect(url_for('assignments.index'))

    enrollment = fetch_one("""
        SELECT enrollment_id FROM enrollments
        WHERE student_id = %s AND offering_id = %s AND status = 'ACTIVE'
    """, (current_user.student_id, assign['offering_id']))
    if not enrollment:
        flash("You are not actively enrolled in this course offering section.", "error")
        return redirect(url_for('assignments.details', assignment_id=assignment_id))

    submission_text = request.form.get('submission_text', '').strip()
    file_path = request.form.get('file_path', '').strip() or None

    if not submission_text and not file_path:
        flash("Please provide solution text or a file path.", "error")
        return redirect(url_for('assignments.details', assignment_id=assignment_id))

    res = academic_service.submit_assignment(
        assignment_id=assignment_id,
        enrollment_id=enrollment['enrollment_id'],
        submission_text=submission_text,
        file_path=file_path
    )
    flash(res['message'], "success" if res['success'] else "error")
    return redirect(url_for('assignments.details', assignment_id=assignment_id))

@assignments_bp.route('/<int:assignment_id>/submissions')
@login_required
@teacher_required
def submissions(assignment_id):
    assign = academic_service.get_assignment_by_id(assignment_id)
    if not assign:
        flash("Assignment not found.", "error")
        return redirect(url_for('assignments.index'))

    sub_list = academic_service.get_assignment_submissions(assignment_id)
    return render_template(
        'assignments/submissions.html',
        active='assignments',
        assignment=assign,
        submissions=sub_list
    )

@assignments_bp.route('/submissions/<int:submission_id>/grade', methods=['POST'])
@login_required
@teacher_required
def grade(submission_id):
    marks = request.form.get('marks', type=float)
    feedback = request.form.get('feedback', '').strip()
    assignment_id = request.form.get('assignment_id', type=int)

    if marks is None or marks < 0:
        flash("A valid positive mark is required.", "error")
        return redirect(url_for('assignments.submissions', assignment_id=assignment_id))

    teacher_id = current_user.teacher_id or 1
    res = academic_service.grade_submission(
        submission_id=submission_id,
        marks=marks,
        feedback=feedback,
        teacher_id=teacher_id
    )
    flash(res['message'], "success" if res['success'] else "error")
    return redirect(url_for('assignments.submissions', assignment_id=assignment_id))
