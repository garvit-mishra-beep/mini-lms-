"""Quiz routes supporting quiz listing, taking questions, server-side grading, and score review."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services import quiz_service
from app.db import fetch_all, fetch_one

quizzes_bp = Blueprint('quizzes', __name__)

@quizzes_bp.route('/')
@login_required
def index():
    # Use v_quiz_performance view joined with lesson and course context
    quizzes = fetch_all("""
        SELECT q.quiz_id, q.title, q.max_score, q.allowed_attempts, q.available_from, q.available_until,
               q.required_for_completion,
               l.title as lesson_title, c.course_id, c.course_code, c.title as course_title,
               COUNT(a.attempt_id) as total_attempts,
               ROUND(AVG(a.score), 2) as average_score
        FROM quizzes q
        JOIN lessons l ON l.lesson_id = q.lesson_id
        JOIN modules m ON m.module_id = l.module_id
        JOIN courses c ON c.course_id = m.course_id
        LEFT JOIN attempts a ON a.quiz_id = q.quiz_id AND a.status = 'SUBMITTED'
        GROUP BY q.quiz_id, q.title, q.max_score, q.allowed_attempts, q.available_from, q.available_until,
                 q.required_for_completion, l.title, c.course_id, c.course_code, c.title
        ORDER BY q.quiz_id
    """)
    return render_template('quizzes/index.html', active='quizzes', quizzes=quizzes)

@quizzes_bp.route('/<int:quiz_id>')
@login_required
def view_quiz(quiz_id):
    quiz = quiz_service.get_quiz_by_id(quiz_id)
    if not quiz:
        flash("Quiz not found.", "error")
        return redirect(url_for('quizzes.index'))

    # Check student enrollment & existing attempts
    enrollment = None
    attempts = []
    can_attempt = True
    reason_blocked = None

    if current_user.is_student and current_user.student_id:
        enrollment = fetch_one("""
            SELECT enrollment_id FROM enrollments
            WHERE student_id = %s AND course_id = %s AND status = 'ACTIVE'
        """, (current_user.student_id, quiz['course_id']))

        if not enrollment:
            can_attempt = False
            reason_blocked = "You must be actively enrolled in this course to take this quiz."
        else:
            attempts = quiz_service.get_attempts_for_enrollment(quiz_id, enrollment['enrollment_id'])
            if len(attempts) >= quiz['allowed_attempts']:
                can_attempt = False
                reason_blocked = f"You have reached the maximum attempt limit ({quiz['allowed_attempts']}/{quiz['allowed_attempts']})."

    questions = quiz_service.get_quiz_questions(quiz_id, include_correct=False)

    return render_template(
        'quizzes/detail.html',
        active='quizzes',
        quiz=quiz,
        enrollment=enrollment,
        attempts=attempts,
        can_attempt=can_attempt,
        reason_blocked=reason_blocked,
        question_count=len(questions)
    )

@quizzes_bp.route('/<int:quiz_id>/start', methods=['POST'])
@login_required
def start_quiz(quiz_id):
    if not current_user.is_student or not current_user.student_id:
        flash("Only enrolled students can start quiz attempts.", "error")
        return redirect(url_for('quizzes.view_quiz', quiz_id=quiz_id))

    quiz = quiz_service.get_quiz_by_id(quiz_id)
    if not quiz:
        flash("Quiz not found.", "error")
        return redirect(url_for('quizzes.index'))

    enrollment = fetch_one("""
        SELECT enrollment_id FROM enrollments
        WHERE student_id = %s AND course_id = %s AND status = 'ACTIVE'
    """, (current_user.student_id, quiz['course_id']))

    if not enrollment:
        flash("Active course enrollment required.", "error")
        return redirect(url_for('quizzes.view_quiz', quiz_id=quiz_id))

    res = quiz_service.start_attempt(enrollment['enrollment_id'], quiz_id)
    if not res['success']:
        flash(res['message'], "error")
        return redirect(url_for('quizzes.view_quiz', quiz_id=quiz_id))

    return redirect(url_for('quizzes.take_quiz', attempt_id=res['attempt']['attempt_id']))

@quizzes_bp.route('/attempt/<int:attempt_id>')
@login_required
def take_quiz(attempt_id):
    attempt = fetch_one("""
        SELECT a.*, q.title as quiz_title, q.max_score, q.allowed_attempts,
               c.course_id, c.course_code, c.title as course_title,
               e.student_id
        FROM attempts a
        JOIN quizzes q ON q.quiz_id = a.quiz_id
        JOIN enrollments e ON e.enrollment_id = a.enrollment_id
        JOIN courses c ON c.course_id = e.course_id
        WHERE a.attempt_id = %s
    """, (attempt_id,))

    if not attempt:
        flash("Attempt not found.", "error")
        return redirect(url_for('quizzes.index'))

    # If student, verify this attempt belongs to them
    if current_user.is_student and current_user.student_id != attempt['student_id']:
        flash("Unauthorized access to this attempt.", "error")
        return redirect(url_for('quizzes.index'))

    # If already submitted, redirect to results
    if attempt['status'] == 'SUBMITTED':
        return redirect(url_for('quizzes.attempt_results', attempt_id=attempt_id))

    questions = quiz_service.get_quiz_questions(attempt['quiz_id'], include_correct=False)

    return render_template(
        'quizzes/take.html',
        active='quizzes',
        attempt=attempt,
        questions=questions
    )

@quizzes_bp.route('/attempt/<int:attempt_id>/submit', methods=['POST'])
@login_required
def submit_quiz(attempt_id):
    # Form data maps question_id to selected option_id
    answers = {}
    for key, val in request.form.items():
        if key.startswith('q_'):
            qid = key.replace('q_', '')
            answers[qid] = int(val)

    res = quiz_service.submit_attempt(attempt_id, answers, current_user.id)
    if not res['success']:
        flash(res['message'], "error")
        return redirect(url_for('quizzes.take_quiz', attempt_id=attempt_id))

    flash(f"Quiz submitted successfully! You scored {res['final_score']} out of {res['max_score']} ({res['percentage']}%).", "success")
    return redirect(url_for('quizzes.attempt_results', attempt_id=attempt_id))

@quizzes_bp.route('/attempt/<int:attempt_id>/results')
@login_required
def attempt_results(attempt_id):
    attempt = fetch_one("""
        SELECT a.*, q.title as quiz_title, q.max_score, q.allowed_attempts,
               c.course_id, c.course_code, c.title as course_title,
               s.student_id, u.full_name as student_name
        FROM attempts a
        JOIN quizzes q ON q.quiz_id = a.quiz_id
        JOIN enrollments e ON e.enrollment_id = a.enrollment_id
        JOIN courses c ON c.course_id = e.course_id
        JOIN students s ON s.student_id = e.student_id
        JOIN users u ON u.user_id = s.user_id
        WHERE a.attempt_id = %s
    """, (attempt_id,))

    if not attempt:
        flash("Attempt record not found.", "error")
        return redirect(url_for('quizzes.index'))

    # Retrieve question answers breakdown
    answers = fetch_all("""
        SELECT aa.*, qq.question_text, qq.points as max_points,
               qo.option_text as chosen_option_text,
               correct_opt.option_text as correct_option_text
        FROM attempt_answers aa
        JOIN quiz_questions qq ON qq.question_id = aa.question_id
        JOIN quiz_options qo ON qo.option_id = aa.selected_option_id
        JOIN quiz_options correct_opt ON correct_opt.question_id = qq.question_id AND correct_opt.is_correct = 1
        WHERE aa.attempt_id = %s
        ORDER BY qq.sequence_no
    """, (attempt_id,))

    # Previous / other attempts count
    attempts_history = quiz_service.get_attempts_for_enrollment(attempt['quiz_id'], attempt['enrollment_id'])

    return render_template(
        'quizzes/results.html',
        active='quizzes',
        attempt=attempt,
        answers=answers,
        attempts_history=attempts_history
    )
