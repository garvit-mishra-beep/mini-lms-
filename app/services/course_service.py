"""Course Service
Manages course lifecycle, instructor assignments, publishing guards, and module/lesson associations.
"""
import pymysql
from app.db import fetch_one, fetch_all, execute_query, record_audit_log, transaction

def get_all_courses(search=None, status=None):
    """Query courses with instructor, module, and enrollment aggregations."""
    sql = """
        SELECT c.course_id, c.course_code, c.title, c.description, c.status, c.created_at,
               COUNT(DISTINCT e.enrollment_id) as enrollment_count,
               COUNT(DISTINCT m.module_id) as module_count,
               COUNT(DISTINCT ci.teacher_id) as instructor_count,
               GROUP_CONCAT(DISTINCT u.full_name SEPARATOR ', ') as instructors
        FROM courses c
        LEFT JOIN enrollments e ON e.course_id = c.course_id
        LEFT JOIN modules m ON m.course_id = c.course_id
        LEFT JOIN course_instructors ci ON ci.course_id = c.course_id AND ci.is_authorized = 1
        LEFT JOIN teachers t ON t.teacher_id = ci.teacher_id
        LEFT JOIN users u ON u.user_id = t.user_id
        WHERE 1=1
    """
    params = []
    if search:
        sql += " AND (c.course_code LIKE %s OR c.title LIKE %s OR c.description LIKE %s)"
        pat = f"%{search}%"
        params.extend([pat, pat, pat])
    if status and status != 'ALL':
        sql += " AND c.status = %s"
        params.append(status)

    sql += " GROUP BY c.course_id, c.course_code, c.title, c.description, c.status, c.created_at ORDER BY c.course_id"
    return fetch_all(sql, tuple(params))

def get_course_by_id(course_id):
    """Retrieve course by primary key."""
    return fetch_one("SELECT * FROM courses WHERE course_id = %s", (course_id,))

def get_course_instructors(course_id):
    """List instructors assigned to a course with role and status."""
    return fetch_all("""
        SELECT ci.course_id, ci.teacher_id, ci.instructor_role, ci.is_authorized, ci.assigned_at,
               t.employee_code, t.qualification, u.full_name, u.email
        FROM course_instructors ci
        JOIN teachers t ON t.teacher_id = ci.teacher_id
        JOIN users u ON u.user_id = t.user_id
        WHERE ci.course_id = %s
        ORDER BY (ci.instructor_role = 'OWNER') DESC, u.full_name
    """, (course_id,))

def create_course(course_code, title, description="", teacher_id=None, actor_user_id=None):
    """Create a new course in DRAFT status with optional primary owner."""
    course_code = course_code.strip().upper()
    title = title.strip()
    
    # Check duplicate code
    if fetch_one("SELECT course_id FROM courses WHERE course_code = %s", (course_code,)):
        return {'success': False, 'message': f"Course code '{course_code}' already exists."}

    try:
        with transaction() as con:
            with con.cursor() as cur:
                cur.execute("""
                    INSERT INTO courses (course_code, title, description, status)
                    VALUES (%s, %s, %s, 'DRAFT')
                """, (course_code, title, description))
                course_id = cur.lastrowid

                if teacher_id:
                    cur.execute("""
                        INSERT INTO course_instructors (course_id, teacher_id, instructor_role, is_authorized)
                        VALUES (%s, %s, 'OWNER', 1)
                    """, (course_id, int(teacher_id)))

        if actor_user_id:
            record_audit_log('courses', course_id, 'CREATE_COURSE', actor_user_id,
                             f"Created course {course_code} - {title}")
        return {'success': True, 'course_id': course_id, 'message': f"Course '{course_code}' created successfully."}
    except pymysql.MySQLError as e:
        return {'success': False, 'message': f"Failed to create course: {e.args[1] if len(e.args)>1 else str(e)}"}

def update_course(course_id, title, description, actor_user_id=None):
    """Update title and description of a course."""
    execute_query("UPDATE courses SET title = %s, description = %s WHERE course_id = %s",
                  (title.strip(), description.strip(), course_id))
    if actor_user_id:
        record_audit_log('courses', course_id, 'UPDATE_COURSE', actor_user_id, f"Updated course details")
    return {'success': True, 'message': 'Course details updated successfully.'}

def publish_course(course_id, actor_user_id=None):
    """
    Publish course. Enforces authorized instructor requirement both in code
    and through MySQL trigger trg_course_publish.
    """
    instructors = fetch_all("""
        SELECT teacher_id FROM course_instructors
        WHERE course_id = %s AND is_authorized = 1
    """, (course_id,))

    if not instructors:
        return {
            'success': False,
            'message': 'Cannot publish: A course requires at least one authorized instructor before publishing.'
        }

    try:
        execute_query("UPDATE courses SET status = 'PUBLISHED' WHERE course_id = %s", (course_id,))
        if actor_user_id:
            record_audit_log('courses', course_id, 'PUBLISH_COURSE', actor_user_id, "Published course")
        return {'success': True, 'message': 'Course has been published successfully.'}
    except pymysql.MySQLError as e:
        return {'success': False, 'message': f"Failed to publish: {e.args[1] if len(e.args)>1 else str(e)}"}

def archive_course(course_id, actor_user_id=None):
    """Archive course."""
    try:
        execute_query("UPDATE courses SET status = 'ARCHIVED' WHERE course_id = %s", (course_id,))
        if actor_user_id:
            record_audit_log('courses', course_id, 'ARCHIVE_COURSE', actor_user_id, "Archived course")
        return {'success': True, 'message': 'Course archived successfully.'}
    except pymysql.MySQLError as e:
        return {'success': False, 'message': f"Failed to archive: {e.args[1] if len(e.args)>1 else str(e)}"}

def assign_instructor(course_id, teacher_id, role='INSTRUCTOR', actor_user_id=None):
    """Assign an instructor to a course."""
    try:
        execute_query("""
            INSERT INTO course_instructors (course_id, teacher_id, instructor_role, is_authorized)
            VALUES (%s, %s, %s, 1)
            ON DUPLICATE KEY UPDATE instructor_role = VALUES(instructor_role), is_authorized = 1
        """, (course_id, teacher_id, role))
        if actor_user_id:
            record_audit_log('course_instructors', course_id, 'ASSIGN_INSTRUCTOR', actor_user_id,
                             f"Assigned teacher_id={teacher_id} as {role}")
        return {'success': True, 'message': 'Instructor assigned successfully.'}
    except pymysql.MySQLError as e:
        return {'success': False, 'message': f"Assignment failed: {e.args[1] if len(e.args)>1 else str(e)}"}
