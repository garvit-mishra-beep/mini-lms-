"""Enrollment Service
Handles student course enrollments, atomic transactions, duplicate conflict detection,
and enrollment status transitions.
"""
import pymysql
from app.db import fetch_one, fetch_all, execute_query, call_proc, record_audit_log, transaction

def get_existing_active_enrollment(student_id, course_id):
    """Check if student already has an active enrollment in the course."""
    return fetch_one("""
        SELECT e.enrollment_id, e.student_id, e.course_id, e.status, e.enrolled_at,
               c.course_code, c.title as course_title, u.full_name as student_name
        FROM enrollments e
        JOIN courses c ON c.course_id = e.course_id
        JOIN students s ON s.student_id = e.student_id
        JOIN users u ON u.user_id = s.user_id
        WHERE e.student_id = %s AND e.course_id = %s AND e.status = 'ACTIVE'
    """, (student_id, course_id))

def get_enrollment_by_id(enrollment_id):
    """Fetch complete enrollment record with joined student, course, completion, and grade info."""
    return fetch_one("""
        SELECT e.enrollment_id, e.student_id, e.course_id, e.status, e.enrolled_at,
               c.course_code, c.title as course_title, c.status as course_status,
               s.roll_no, s.enrollment_no, u.full_name as student_name, u.email as student_email,
               co.completion_status, co.completed_at,
               g.final_score, g.letter_grade, g.published as grade_published,
               cert.certificate_code, cert.issued_at as cert_issued_at
        FROM enrollments e
        JOIN courses c ON c.course_id = e.course_id
        JOIN students s ON s.student_id = e.student_id
        JOIN users u ON u.user_id = s.user_id
        LEFT JOIN completions co ON co.enrollment_id = e.enrollment_id
        LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
        LEFT JOIN certificates cert ON cert.enrollment_id = e.enrollment_id
        WHERE e.enrollment_id = %s
    """, (enrollment_id,))

def enroll_student(student_id, course_id, actor_user_id=None):
    """
    Perform atomic enrollment of a student into a course.
    Returns:
        dict: {'success': bool, 'message': str, 'conflict': bool, 'enrollment_id': int, 'existing_enrollment_id': int}
    """
    # 1. Pre-flight verification: Check if student is active
    student = fetch_one("""
        SELECT s.student_id, u.full_name, u.status
        FROM students s JOIN users u ON u.user_id = s.user_id
        WHERE s.student_id = %s
    """, (student_id,))
    if not student:
        return {'success': False, 'conflict': False, 'message': 'Student record was not found.'}
    if student['status'] != 'ACTIVE':
        return {'success': False, 'conflict': False, 'message': f"Cannot enroll: Student '{student['full_name']}' account is inactive."}

    # 2. Pre-flight verification: Check if course is published
    course = fetch_one("SELECT course_id, course_code, title, status FROM courses WHERE course_id = %s", (course_id,))
    if not course:
        return {'success': False, 'conflict': False, 'message': 'Selected course was not found.'}
    if course['status'] != 'PUBLISHED':
        return {'success': False, 'conflict': False, 'message': f"Cannot enroll: Course '{course['course_code']}' is currently in {course['status']} status (must be PUBLISHED)."}

    # 3. Conflict Check: Detect existing active enrollment
    existing = get_existing_active_enrollment(student_id, course_id)
    if existing:
        return {
            'success': False,
            'conflict': True,
            'message': f"This student ({student['full_name']}) is already actively enrolled in course {course['course_code']} - {course['title']}.",
            'existing_enrollment_id': existing['enrollment_id']
        }

    # 4. Atomic Execution via Stored Procedure sp_enroll
    try:
        call_proc('sp_enroll', (student_id, course_id))
        
        # Retrieve the newly created enrollment
        new_enrollment = fetch_one("""
            SELECT enrollment_id FROM enrollments
            WHERE student_id = %s AND course_id = %s AND status = 'ACTIVE'
            ORDER BY enrollment_id DESC LIMIT 1
        """, (student_id, course_id))
        
        new_id = new_enrollment['enrollment_id'] if new_enrollment else None

        if actor_user_id:
            record_audit_log('enrollments', new_id, 'MANUAL_ENROLL', actor_user_id,
                             f"Enrolled student_id={student_id} into course_id={course_id}")

        return {
            'success': True,
            'conflict': False,
            'message': f"Successfully enrolled {student['full_name']} in {course['course_code']}.",
            'enrollment_id': new_id
        }

    except pymysql.MySQLError as err:
        err_code, err_msg = err.args[0], err.args[1] if len(err.args) > 1 else str(err)
        
        # MySQL error 1062: Duplicate entry conflict on unique key
        if err_code == 1062 or 'Duplicate entry' in str(err_msg):
            existing = get_existing_active_enrollment(student_id, course_id)
            existing_id = existing['enrollment_id'] if existing else None
            return {
                'success': False,
                'conflict': True,
                'message': f"Enrollment conflict: Student is already actively enrolled in this course.",
                'existing_enrollment_id': existing_id
            }
        
        # Custom signals from triggers / stored procedures (SQLSTATE 45000)
        if 'already actively enrolled' in str(err_msg):
            existing = get_existing_active_enrollment(student_id, course_id)
            return {
                'success': False,
                'conflict': True,
                'message': "This student is already actively enrolled in this course.",
                'existing_enrollment_id': existing['enrollment_id'] if existing else None
            }
        
        return {
            'success': False,
            'conflict': False,
            'message': f"Enrollment could not be completed: {err_msg}"
        }

def cancel_enrollment(enrollment_id, actor_user_id=None):
    """Cancel an active enrollment, allowing subsequent re-enrollment if required."""
    enrollment = get_enrollment_by_id(enrollment_id)
    if not enrollment:
        return {'success': False, 'message': 'Enrollment record not found.'}
    if enrollment['status'] != 'ACTIVE':
        return {'success': False, 'message': f"Cannot cancel enrollment with status '{enrollment['status']}'."}

    execute_query("UPDATE enrollments SET status = 'CANCELLED' WHERE enrollment_id = %s", (enrollment_id,))
    if actor_user_id:
        record_audit_log('enrollments', enrollment_id, 'STATUS_CANCELLED', actor_user_id,
                         f"Cancelled enrollment #{enrollment_id} for student {enrollment['student_name']}")
    return {'success': True, 'message': f"Enrollment #{enrollment_id} has been cancelled."}

def complete_enrollment(enrollment_id, actor_user_id=None):
    """Run completion procedure sp_update_completion for an enrollment."""
    enrollment = get_enrollment_by_id(enrollment_id)
    if not enrollment:
        return {'success': False, 'message': 'Enrollment record not found.'}
    
    try:
        call_proc('sp_update_completion', (enrollment_id,))
        updated = get_enrollment_by_id(enrollment_id)
        if actor_user_id:
            record_audit_log('completions', enrollment_id, 'EVALUATE_COMPLETION', actor_user_id,
                             f"Completion status: {updated['completion_status']}")
        return {
            'success': True,
            'message': f"Enrollment #{enrollment_id} evaluated: Status is {updated['completion_status']} (Enrollment {updated['status']})."
        }
    except pymysql.MySQLError as e:
        return {'success': False, 'message': f"Completion evaluation failed: {e.args[1] if len(e.args)>1 else str(e)}"}
