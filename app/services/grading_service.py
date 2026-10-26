"""Grading and Certificate Service
Integrates with sp_publish_grade, sp_correct_published_grade, and certificate generation.
"""
import secrets
from decimal import Decimal
import pymysql
from app.db import fetch_one, fetch_all, execute_query, call_proc, record_audit_log, transaction

def get_grades_overview():
    """Retrieve grades view data joined with completion and quiz metadata."""
    grades = fetch_all("SELECT * FROM v_student_grades ORDER BY course_code, full_name")
    quiz_perf = fetch_all("SELECT * FROM v_quiz_performance ORDER BY quiz_id")
    completions = fetch_all("SELECT * FROM v_course_completion ORDER BY course_code")
    detailed_grades = fetch_all("""
        SELECT g.grade_id, g.enrollment_id, g.final_score, g.letter_grade, g.published, g.published_at,
               c.course_code, c.title as course_title, u.full_name as student_name, s.roll_no,
               co.completion_status
        FROM grades g
        JOIN enrollments e ON e.enrollment_id = g.enrollment_id
        JOIN courses c ON c.course_id = e.course_id
        JOIN students s ON s.student_id = e.student_id
        JOIN users u ON u.user_id = s.user_id
        LEFT JOIN completions co ON co.enrollment_id = e.enrollment_id
        ORDER BY c.course_code, u.full_name
    """)
    return {
        'grades': grades,
        'quiz_performance': quiz_perf,
        'completions': completions,
        'detailed_grades': detailed_grades
    }

def publish_course_grade(enrollment_id, actor_user_id=None):
    """Publish final grade for an enrollment using stored procedure sp_publish_grade."""
    try:
        call_proc('sp_publish_grade', (enrollment_id,))
        if actor_user_id:
            record_audit_log('grades', enrollment_id, 'PUBLISH_GRADE', actor_user_id,
                             f"Published final grade for enrollment #{enrollment_id}")
        return {'success': True, 'message': f"Grade published successfully for enrollment #{enrollment_id}."}
    except pymysql.MySQLError as e:
        msg = e.args[1] if len(e.args) > 1 else str(e)
        return {'success': False, 'message': f"Cannot publish grade: {msg}"}

def correct_grade(grade_id, new_score, reason, actor_user_id):
    """
    Correct an already published grade using sp_correct_published_grade.
    Enforces trigger trg_grade_guard and writes to grade_change_history via trigger trg_grade_history.
    """
    try:
        score_dec = Decimal(str(new_score))
        call_proc('sp_correct_published_grade', (grade_id, score_dec, actor_user_id, reason.strip()))
        return {'success': True, 'message': f"Grade #{grade_id} successfully updated to {score_dec}% with audit history recorded."}
    except pymysql.MySQLError as e:
        msg = e.args[1] if len(e.args) > 1 else str(e)
        return {'success': False, 'message': f"Grade correction failed: {msg}"}

def issue_certificate_for_enrollment(enrollment_id, actor_user_id=None):
    """Issue a unique completion certificate for eligible completed enrollments."""
    enrollment = fetch_one("""
        SELECT e.enrollment_id, e.status, co.completion_status, c.course_code, u.full_name
        FROM enrollments e
        JOIN completions co ON co.enrollment_id = e.enrollment_id
        JOIN courses c ON c.course_id = e.course_id
        JOIN students s ON s.student_id = e.student_id
        JOIN users u ON u.user_id = s.user_id
        WHERE e.enrollment_id = %s
    """, (enrollment_id,))

    if not enrollment:
        return {'success': False, 'message': 'Enrollment record not found.'}
    if enrollment['completion_status'] != 'COMPLETED':
        return {'success': False, 'message': f"Cannot issue certificate: Course completion status is '{enrollment['completion_status']}' (must be COMPLETED)."}

    # Check if certificate already exists
    existing = fetch_one("SELECT certificate_id, certificate_code FROM certificates WHERE enrollment_id = %s", (enrollment_id,))
    if existing:
        return {
            'success': True,
            'certificate_code': existing['certificate_code'],
            'message': f"Certificate already exists with code: {existing['certificate_code']}."
        }

    # Generate unique verifiable code
    cert_code = f"CERT-{enrollment['course_code']}-{secrets.token_hex(4).upper()}"
    try:
        execute_query("""
            INSERT INTO certificates (enrollment_id, certificate_code)
            VALUES (%s, %s)
        """, (enrollment_id, cert_code))
        if actor_user_id:
            record_audit_log('certificates', enrollment_id, 'ISSUE_CERTIFICATE', actor_user_id,
                             f"Issued certificate {cert_code} to {enrollment['full_name']}")
        return {'success': True, 'certificate_code': cert_code, 'message': f"Certificate issued successfully: {cert_code}"}
    except pymysql.MySQLError as e:
        return {'success': False, 'message': f"Failed to issue certificate: {e.args[1] if len(e.args)>1 else str(e)}"}
