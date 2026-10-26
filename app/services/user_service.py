"""User and Student/Teacher management service.
Handles student and teacher profile creation, updates, and status toggles.
"""
from werkzeug.security import generate_password_hash
import pymysql
from app.db import fetch_one, fetch_all, execute_query, record_audit_log, transaction
from app.config import Config

def get_all_students(search=None, status=None):
    """Retrieve students with user details and enrollment counts."""
    sql = """
        SELECT s.student_id, s.user_id, s.roll_no, s.enrollment_no, s.phone, s.dob,
               u.full_name, u.email, u.status, u.created_at,
               COUNT(e.enrollment_id) as total_enrollments,
               SUM(e.status = 'ACTIVE') as active_enrollments,
               SUM(co.completion_status = 'COMPLETED') as completed_enrollments
        FROM students s
        JOIN users u ON u.user_id = s.user_id
        LEFT JOIN enrollments e ON e.student_id = s.student_id
        LEFT JOIN completions co ON co.enrollment_id = e.enrollment_id
        WHERE 1=1
    """
    params = []
    if search:
        sql += " AND (u.full_name LIKE %s OR u.email LIKE %s OR s.roll_no LIKE %s OR s.enrollment_no LIKE %s)"
        pat = f"%{search}%"
        params.extend([pat, pat, pat, pat])
    if status and status != 'ALL':
        sql += " AND u.status = %s"
        params.append(status)

    sql += " GROUP BY s.student_id, s.user_id, s.roll_no, s.enrollment_no, s.phone, s.dob, u.full_name, u.email, u.status, u.created_at ORDER BY s.student_id"
    return fetch_all(sql, tuple(params))

def get_student_profile(student_id):
    """Detailed student profile with active courses, grades, quiz attempts, and certificates."""
    student = fetch_one("""
        SELECT s.student_id, s.user_id, s.roll_no, s.enrollment_no, s.phone, s.dob,
               u.full_name, u.email, u.status, u.created_at
        FROM students s
        JOIN users u ON u.user_id = s.user_id
        WHERE s.student_id = %s
    """, (student_id,))

    if not student:
        return None

    enrollments = fetch_all("""
        SELECT e.enrollment_id, e.course_id, e.status, e.enrolled_at,
               c.course_code, c.title as course_title,
               co.completion_status, co.completed_at,
               g.final_score, g.letter_grade, g.published as grade_published,
               cert.certificate_code, cert.issued_at as cert_issued_at
        FROM enrollments e
        JOIN courses c ON c.course_id = e.course_id
        LEFT JOIN completions co ON co.enrollment_id = e.enrollment_id
        LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
        LEFT JOIN certificates cert ON cert.enrollment_id = e.enrollment_id
        WHERE e.student_id = %s
        ORDER BY e.enrolled_at DESC
    """, (student_id,))

    student['enrollments'] = enrollments
    return student

def add_student(full_name, email, roll_no, enrollment_no, phone="", dob=None, actor_user_id=None):
    """
    Create a new student user and corresponding student record atomically.
    Triggers trg_student_role enforce that the referenced user has role='STUDENT'.
    """
    full_name = full_name.strip()
    email = email.strip().lower()
    roll_no = roll_no.strip()
    enrollment_no = enrollment_no.strip()

    # Check unique constraints
    if fetch_one("SELECT user_id FROM users WHERE LOWER(email) = %s", (email,)):
        return {'success': False, 'message': f"A user with email '{email}' already exists."}
    if fetch_one("SELECT student_id FROM students WHERE roll_no = %s", (roll_no,)):
        return {'success': False, 'message': f"Roll number '{roll_no}' is already assigned."}
    if fetch_one("SELECT student_id FROM students WHERE enrollment_no = %s", (enrollment_no,)):
        return {'success': False, 'message': f"Enrollment number '{enrollment_no}' is already assigned."}

    password_hash = generate_password_hash(Config.DEMO_USER_PASSWORD)

    try:
        with transaction() as con:
            with con.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (full_name, email, password_hash, role, status)
                    VALUES (%s, %s, %s, 'STUDENT', 'ACTIVE')
                """, (full_name, email, password_hash))
                user_id = cur.lastrowid

                cur.execute("""
                    INSERT INTO students (user_id, roll_no, enrollment_no, phone, dob)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, roll_no, enrollment_no, phone or None, dob or None))
                student_id = cur.lastrowid

        if actor_user_id:
            record_audit_log('students', student_id, 'CREATE_STUDENT', actor_user_id,
                             f"Created student {full_name} ({roll_no})")
        return {'success': True, 'student_id': student_id, 'message': f"Student '{full_name}' added successfully."}
    except pymysql.MySQLError as e:
        return {'success': False, 'message': f"Failed to add student: {e.args[1] if len(e.args)>1 else str(e)}"}

def toggle_user_status(user_id, actor_user_id=None):
    """Toggle between ACTIVE and INACTIVE user status."""
    user = fetch_one("SELECT user_id, full_name, status, role FROM users WHERE user_id = %s", (user_id,))
    if not user:
        return {'success': False, 'message': 'User not found.'}
    
    new_status = 'INACTIVE' if user['status'] == 'ACTIVE' else 'ACTIVE'
    execute_query("UPDATE users SET status = %s WHERE user_id = %s", (new_status, user_id))
    
    if actor_user_id:
        record_audit_log('users', user_id, 'STATUS_CHANGE', actor_user_id,
                         f"Changed status from {user['status']} to {new_status}")
    return {'success': True, 'new_status': new_status, 'message': f"User '{user['full_name']}' is now {new_status}."}

def get_all_teachers():
    """List teachers with assigned courses and contact details."""
    return fetch_all("""
        SELECT t.teacher_id, t.user_id, t.employee_code, t.qualification, t.bio, t.phone_no,
               u.full_name, u.email, u.status, u.created_at,
               COUNT(DISTINCT ci.course_id) as assigned_courses_count
        FROM teachers t
        JOIN users u ON u.user_id = t.user_id
        LEFT JOIN course_instructors ci ON ci.teacher_id = t.teacher_id AND ci.is_authorized = 1
        GROUP BY t.teacher_id, t.user_id, t.employee_code, t.qualification, t.bio, t.phone_no,
                 u.full_name, u.email, u.status, u.created_at
        ORDER BY t.teacher_id
    """)
