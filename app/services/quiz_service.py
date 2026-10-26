"""Quiz Service
Manages quiz fetching, question presentation, attempt management, server-side grading,
and atomic score submission.
"""
from decimal import Decimal
import pymysql
from app.db import fetch_one, fetch_all, execute_query, call_proc, record_audit_log, transaction

def get_quiz_by_id(quiz_id):
    """Fetch quiz with lesson, module, and course context."""
    return fetch_one("""
        SELECT q.quiz_id, q.title, q.max_score, q.allowed_attempts,
               q.available_from, q.available_until, q.required_for_completion,
               l.lesson_id, l.title as lesson_title, l.is_restricted, l.release_date,
               m.module_id, m.title as module_title,
               c.course_id, c.course_code, c.title as course_title
        FROM quizzes q
        JOIN lessons l ON l.lesson_id = q.lesson_id
        JOIN modules m ON m.module_id = l.module_id
        JOIN courses c ON c.course_id = m.course_id
        WHERE q.quiz_id = %s
    """, (quiz_id,))

def get_quiz_questions(quiz_id, include_correct=False):
    """Fetch all questions and answer options for a quiz."""
    questions = fetch_all("""
        SELECT question_id, quiz_id, question_text, points, sequence_no
        FROM quiz_questions
        WHERE quiz_id = %s
        ORDER BY sequence_no, question_id
    """, (quiz_id,))

    for q in questions:
        if include_correct:
            options = fetch_all("""
                SELECT option_id, question_id, option_text, is_correct, sequence_no
                FROM quiz_options
                WHERE question_id = %s
                ORDER BY sequence_no, option_id
            """, (q['question_id'],))
        else:
            options = fetch_all("""
                SELECT option_id, question_id, option_text, sequence_no
                FROM quiz_options
                WHERE question_id = %s
                ORDER BY sequence_no, option_id
            """, (q['question_id'],))
        q['options'] = options
    return questions

def get_attempts_for_enrollment(quiz_id, enrollment_id):
    """List student attempts for this quiz."""
    return fetch_all("""
        SELECT attempt_id, quiz_id, enrollment_id, attempt_no, started_at, submitted_at,
               score, status
        FROM attempts
        WHERE quiz_id = %s AND enrollment_id = %s
        ORDER BY attempt_no DESC
    """, (quiz_id, enrollment_id))

def start_attempt(enrollment_id, quiz_id):
    """
    Start a new quiz attempt using database stored procedure sp_start_attempt.
    Enforces concurrency lock, availability window, attempt limits, and prerequisites via trigger.
    """
    try:
        call_proc('sp_start_attempt', (enrollment_id, quiz_id))
        
        # Fetch the newly initiated in-progress attempt
        attempt = fetch_one("""
            SELECT attempt_id, quiz_id, enrollment_id, attempt_no, started_at, status
            FROM attempts
            WHERE enrollment_id = %s AND quiz_id = %s AND status = 'IN_PROGRESS'
            ORDER BY attempt_id DESC LIMIT 1
        """, (enrollment_id, quiz_id))
        
        return {'success': True, 'attempt': attempt}
    except pymysql.MySQLError as e:
        msg = e.args[1] if len(e.args) > 1 else str(e)
        return {'success': False, 'message': f"Cannot start attempt: {msg}"}

def submit_attempt(attempt_id, answers_dict, student_user_id=None):
    """
    Grade and submit attempt server-side.
    answers_dict: {str(question_id): int(selected_option_id)}
    """
    attempt = fetch_one("""
        SELECT a.attempt_id, a.quiz_id, a.enrollment_id, a.attempt_no, a.status,
               q.max_score, q.title as quiz_title
        FROM attempts a
        JOIN quizzes q ON q.quiz_id = a.quiz_id
        WHERE a.attempt_id = %s
    """, (attempt_id,))

    if not attempt:
        return {'success': False, 'message': 'Attempt record not found.'}
    if attempt['status'] != 'IN_PROGRESS':
        return {'success': False, 'message': 'This attempt has already been submitted and is immutable.'}

    quiz_id = attempt['quiz_id']
    questions = get_quiz_questions(quiz_id, include_correct=True)

    total_points = Decimal('0.00')
    awarded_points = Decimal('0.00')
    graded_breakdown = []

    # Server-side answer scoring and recording
    with transaction() as con:
        with con.cursor() as cur:
            for q in questions:
                qid = q['question_id']
                q_points = Decimal(str(q['points']))
                total_points += q_points
                
                selected_opt_id = answers_dict.get(str(qid)) or answers_dict.get(qid)
                selected_opt_id = int(selected_opt_id) if selected_opt_id else None

                is_correct = 0
                pts_for_q = Decimal('0.00')

                if selected_opt_id:
                    # Check if selected option is indeed correct
                    opt_match = next((opt for opt in q['options'] if opt['option_id'] == selected_opt_id), None)
                    if opt_match and opt_match['is_correct'] == 1:
                        is_correct = 1
                        pts_for_q = q_points
                        awarded_points += q_points

                    # Insert or update attempt_answers record
                    cur.execute("""
                        INSERT INTO attempt_answers (attempt_id, question_id, selected_option_id, is_correct, points_awarded)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            selected_option_id = VALUES(selected_option_id),
                            is_correct = VALUES(is_correct),
                            points_awarded = VALUES(points_awarded)
                    """, (attempt_id, qid, selected_opt_id, is_correct, pts_for_q))

                graded_breakdown.append({
                    'question_id': qid,
                    'question_text': q['question_text'],
                    'points_possible': float(q_points),
                    'points_awarded': float(pts_for_q),
                    'is_correct': bool(is_correct),
                    'selected_option_id': selected_opt_id
                })

            # Scale to quiz max_score if needed, or cap at max_score
            final_score = min(awarded_points, Decimal(str(attempt['max_score'])))

            # Execute sp_submit_attempt
            cur.callproc('sp_submit_attempt', (attempt_id, final_score))
            while cur.nextset(): pass

            # Recalculate enrollment completion status automatically
            try:
                cur.callproc('sp_update_completion', (attempt['enrollment_id'],))
                while cur.nextset(): pass
            except Exception:
                pass

    if student_user_id:
        record_audit_log('attempts', attempt_id, 'SUBMIT_QUIZ', student_user_id,
                         f"Scored {final_score}/{attempt['max_score']} on Quiz '{attempt['quiz_title']}'")

    return {
        'success': True,
        'attempt_id': attempt_id,
        'final_score': float(final_score),
        'max_score': float(attempt['max_score']),
        'percentage': round(float(final_score) / float(attempt['max_score']) * 100, 1) if attempt['max_score'] > 0 else 0,
        'breakdown': graded_breakdown
    }
