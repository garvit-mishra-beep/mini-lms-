"""Module and Lesson management routes."""
import pymysql
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.auth.decorators import role_required, teacher_required
from app.db import fetch_all, fetch_one, execute_query, record_audit_log

modules_bp = Blueprint('modules', __name__)

@modules_bp.route('/')
@login_required
def index():
    courses = fetch_all("""
        SELECT c.course_id, c.course_code, c.title, c.status,
               COUNT(DISTINCT m.module_id) as module_count,
               COUNT(DISTINCT l.lesson_id) as lesson_count
        FROM courses c
        LEFT JOIN modules m ON m.course_id = c.course_id
        LEFT JOIN lessons l ON l.module_id = m.module_id
        GROUP BY c.course_id, c.course_code, c.title, c.status
        ORDER BY c.course_code
    """)
    return render_template('modules/index.html', active='modules', courses=courses)

@modules_bp.route('/course/<int:course_id>')
@login_required
def course_modules(course_id):
    course = fetch_one("SELECT * FROM courses WHERE course_id = %s", (course_id,))
    if not course:
        flash("Course not found.", "error")
        return redirect(url_for('modules.index'))

    modules = fetch_all("SELECT * FROM modules WHERE course_id = %s ORDER BY sequence_no", (course_id,))
    for m in modules:
        m['lessons'] = fetch_all("""
            SELECT l.*, q.quiz_id, q.title as quiz_title
            FROM lessons l
            LEFT JOIN quizzes q ON q.lesson_id = l.lesson_id
            WHERE l.module_id = %s
            ORDER BY l.sequence_no
        """, (m['module_id'],))

    return render_template('modules/course_modules.html', active='modules', course=course, modules=modules)

@modules_bp.route('/course/<int:course_id>/add-module', methods=['POST'])
@login_required
@teacher_required
def add_module(course_id):
    if current_user.is_teacher and not current_user.is_admin:
        from app.routes.courses import is_teacher_assigned_to_course
        if not is_teacher_assigned_to_course(current_user.teacher_id, course_id):
            flash("Access denied: You are not an assigned instructor for this course.", "error")
            from flask import abort
            abort(403)

    title = request.form.get('title', '').strip()
    desc = request.form.get('description', '').strip()
    seq = request.form.get('sequence_no')

    if not title:
        flash("Module title is required.", "error")
        return redirect(url_for('modules.course_modules', course_id=course_id))

    if not seq:
        # Determine next sequence_no
        current_max = fetch_one("SELECT COALESCE(MAX(sequence_no), 0) as max_seq FROM modules WHERE course_id = %s", (course_id,))
        seq = (current_max['max_seq'] if current_max else 0) + 1
    else:
        seq = int(seq)

    try:
        execute_query("""
            INSERT INTO modules (course_id, title, description, sequence_no)
            VALUES (%s, %s, %s, %s)
        """, (course_id, title, desc, seq))
        record_audit_log('modules', course_id, 'ADD_MODULE', current_user.id, f"Added module '{title}'")
        flash(f"Module '{title}' created successfully.", "success")
    except pymysql.MySQLError as e:
        flash(f"Failed to add module: {e.args[1] if len(e.args)>1 else str(e)}", "error")

    return redirect(url_for('modules.course_modules', course_id=course_id))

@modules_bp.route('/lesson/<int:lesson_id>')
@login_required
def view_lesson(lesson_id):
    lesson = fetch_one("""
        SELECT l.*, m.title as module_title, m.course_id, c.course_code, c.title as course_title,
               q.quiz_id, q.title as quiz_title
        FROM lessons l
        JOIN modules m ON m.module_id = l.module_id
        JOIN courses c ON c.course_id = m.course_id
        LEFT JOIN quizzes q ON q.lesson_id = l.lesson_id
        WHERE l.lesson_id = %s
    """, (lesson_id,))

    if not lesson:
        flash("Lesson not found.", "error")
        return redirect(url_for('modules.index'))

    # Check student active enrollment & progress
    enrollment = None
    is_completed = False
    prerequisites = fetch_all("""
        SELECT p.prerequisite_lesson_id, pl.title as prerequisite_title
        FROM lesson_prerequisites p
        JOIN lessons pl ON pl.lesson_id = p.prerequisite_lesson_id
        WHERE p.lesson_id = %s
    """, (lesson_id,))

    if current_user.is_student and current_user.student_id:
        enrollment = fetch_one("""
            SELECT enrollment_id FROM enrollments
            WHERE student_id = %s AND course_id = %s AND status = 'ACTIVE'
        """, (current_user.student_id, lesson['course_id']))

        if enrollment:
            prog = fetch_one("""
                SELECT completed_at FROM lesson_progress
                WHERE enrollment_id = %s AND lesson_id = %s
            """, (enrollment['enrollment_id'], lesson_id))
            is_completed = bool(prog)

    return render_template(
        'modules/lesson.html',
        active='modules',
        lesson=lesson,
        enrollment=enrollment,
        is_completed=is_completed,
        prerequisites=prerequisites
    )

@modules_bp.route('/lesson/<int:lesson_id>/complete', methods=['POST'])
@login_required
def mark_lesson_complete(lesson_id):
    if not current_user.is_student or not current_user.student_id:
        flash("Only enrolled students can mark lesson progress.", "error")
        return redirect(url_for('modules.view_lesson', lesson_id=lesson_id))

    lesson = fetch_one("""
        SELECT l.lesson_id, m.course_id
        FROM lessons l JOIN modules m ON m.module_id = l.module_id
        WHERE l.lesson_id = %s
    """, (lesson_id,))

    if not lesson:
        flash("Lesson not found.", "error")
        return redirect(url_for('modules.index'))

    enrollment = fetch_one("""
        SELECT enrollment_id FROM enrollments
        WHERE student_id = %s AND course_id = %s AND status = 'ACTIVE'
    """, (current_user.student_id, lesson['course_id']))

    if not enrollment:
        flash("Active course enrollment required to save progress.", "error")
        return redirect(url_for('modules.view_lesson', lesson_id=lesson_id))

    try:
        execute_query("""
            INSERT IGNORE INTO lesson_progress (enrollment_id, lesson_id, completed_at)
            VALUES (%s, %s, NOW())
        """, (enrollment['enrollment_id'], lesson_id))
        flash("Lesson marked as completed!", "success")
    except pymysql.MySQLError as e:
        flash(f"Progress error: {e.args[1] if len(e.args)>1 else str(e)}", "error")

    return redirect(url_for('modules.view_lesson', lesson_id=lesson_id))
