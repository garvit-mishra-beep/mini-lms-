"""Academic Service
Handles coordination metrics, course offerings, attendance tracking,
coursework assignments, submissions, grading, and announcements.
"""
from decimal import Decimal
import pymysql
from app.db import fetch_one, fetch_all, execute_query, call_proc, record_audit_log, transaction

# ============================================================
# 1. COORDINATOR & DEPARTMENT METRICS
# ============================================================

def get_coordinator_overview():
    """Retrieve high-level institutional and departmental metrics."""
    dept_perf = fetch_all("SELECT * FROM v_department_performance ORDER BY department_code")
    offering_sum = fetch_all("SELECT * FROM v_course_offering_summary ORDER BY term_code DESC, course_code")
    faculty_load = fetch_all("SELECT * FROM v_faculty_workload ORDER BY full_name")
    student_sum = fetch_all("SELECT * FROM v_student_academic_summary ORDER BY avg_attendance_pct ASC, roll_no")
    
    # Calculate key summaries
    total_departments = len(dept_perf)
    total_offerings = len(offering_sum)
    total_faculty = len(faculty_load)
    total_students = len(student_sum)
    
    # Identify academic attendance warnings (< 75%)
    attendance_warnings = [s for s in student_sum if s.get('avg_attendance_pct') is not None and float(s['avg_attendance_pct']) < 75.0]

    return {
        'dept_performance': dept_perf,
        'offering_summary': offering_sum,
        'faculty_workload': faculty_load,
        'student_summary': student_sum,
        'total_departments': total_departments,
        'total_offerings': total_offerings,
        'total_faculty': total_faculty,
        'total_students': total_students,
        'attendance_warnings_count': len(attendance_warnings),
        'attendance_warnings': attendance_warnings
    }

def get_all_offerings(term_id=None, department_id=None):
    """Retrieve all course offerings with section, instructor, and capacity details."""
    sql = """
        SELECT co.offering_id, co.course_id, co.term_id, co.section_name,
               co.max_capacity, co.enrolled_count, co.status as offering_status,
               c.course_code, c.title as course_title, c.credits,
               t.term_code, t.term_name,
               d.department_code, d.department_name,
               fac.teacher_id, u.full_name as instructor_name, fac.employee_code
        FROM course_offerings co
        JOIN courses c ON co.course_id = c.course_id
        JOIN academic_terms t ON co.term_id = t.term_id
        LEFT JOIN departments d ON c.department_id = d.department_id
        LEFT JOIN course_instructors ci ON co.offering_id = ci.offering_id AND ci.role_in_course = 'PRIMARY'
        LEFT JOIN teachers fac ON ci.teacher_id = fac.teacher_id
        LEFT JOIN users u ON fac.user_id = u.user_id
        WHERE 1=1
    """
    params = []
    if term_id:
        sql += " AND co.term_id = %s"
        params.append(term_id)
    if department_id:
        sql += " AND c.department_id = %s"
        params.append(department_id)
    sql += " ORDER BY t.term_code DESC, c.course_code, co.section_name"
    return fetch_all(sql, params)

def create_course_offering(course_id, term_id, section_name, max_capacity, teacher_id=None, actor_user_id=None):
    """Create a new course offering section and optionally assign primary instructor."""
    try:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO course_offerings (course_id, term_id, section_name, max_capacity, status)
                    VALUES (%s, %s, %s, %s, 'OPEN');
                """, (course_id, term_id, section_name.strip().upper(), max_capacity))
                offering_id = cur.lastrowid

                if teacher_id:
                    cur.execute("""
                        INSERT INTO course_instructors (course_id, teacher_id, offering_id, role_in_course, is_authorized)
                        VALUES (%s, %s, %s, 'PRIMARY', 1)
                        ON DUPLICATE KEY UPDATE 
                            offering_id = VALUES(offering_id),
                            role_in_course = 'PRIMARY',
                            is_authorized = 1;
                    """, (course_id, teacher_id, offering_id))

        if actor_user_id:
            record_audit_log('course_offerings', offering_id, 'CREATE_OFFERING', actor_user_id,
                             f"Created section {section_name} for course #{course_id} in term #{term_id}")
        return {'success': True, 'offering_id': offering_id, 'message': 'Course offering created successfully.'}
    except pymysql.MySQLError as e:
        msg = e.args[1] if len(e.args) > 1 else str(e)
        return {'success': False, 'message': f"Database error creating offering: {msg}"}

def update_offering_status(offering_id, new_status, actor_user_id=None):
    """Update section lifecycle status ('PLANNED', 'OPEN', 'CLOSED', 'COMPLETED')."""
    if new_status not in ('PLANNED', 'OPEN', 'CLOSED', 'COMPLETED'):
        return {'success': False, 'message': f"Invalid status: {new_status}"}
    try:
        execute_query("UPDATE course_offerings SET status = %s WHERE offering_id = %s", (new_status, offering_id))
        if actor_user_id:
            record_audit_log('course_offerings', offering_id, 'UPDATE_STATUS', actor_user_id,
                             f"Changed offering #{offering_id} status to {new_status}")
        return {'success': True, 'message': f"Offering status updated to {new_status}."}
    except pymysql.MySQLError as e:
        msg = e.args[1] if len(e.args) > 1 else str(e)
        return {'success': False, 'message': f"Failed to update status: {msg}"}


# ============================================================
# 2. ATTENDANCE TRACKING
# ============================================================

def get_offerings_for_teacher(teacher_id):
    """Retrieve offering sections assigned to a teacher."""
    return fetch_all("""
        SELECT co.offering_id, co.section_name, co.enrolled_count, co.max_capacity, co.status as offering_status,
               c.course_id, c.course_code, c.title as course_title,
               t.term_code, t.term_name
        FROM course_offerings co
        JOIN courses c ON co.course_id = c.course_id
        JOIN academic_terms t ON co.term_id = t.term_id
        JOIN course_instructors ci ON co.offering_id = ci.offering_id
        WHERE ci.teacher_id = %s
        ORDER BY t.term_code DESC, c.course_code
    """, (teacher_id,))

def get_attendance_sessions_for_offering(offering_id):
    """Retrieve past attendance sessions for a given course offering."""
    return fetch_all("""
        SELECT att.session_id, att.offering_id, att.session_date, att.topic_covered, att.created_at,
               u.full_name as teacher_name,
               COUNT(ar.enrollment_id) as total_marked,
               SUM(CASE WHEN ar.status = 'PRESENT' THEN 1 ELSE 0 END) as present_count,
               SUM(CASE WHEN ar.status = 'ABSENT' THEN 1 ELSE 0 END) as absent_count,
               SUM(CASE WHEN ar.status = 'LATE' THEN 1 ELSE 0 END) as late_count
        FROM attendance_sessions att
        JOIN teachers t ON att.teacher_id = t.teacher_id
        JOIN users u ON t.user_id = u.user_id
        LEFT JOIN attendance_records ar ON att.session_id = ar.session_id
        WHERE att.offering_id = %s
        GROUP BY att.session_id, att.offering_id, att.session_date, att.topic_covered, att.created_at, u.full_name
        ORDER BY att.session_date DESC, att.session_id DESC
    """, (offering_id,))

def create_attendance_session(offering_id, teacher_id, session_date, topic_covered):
    """Atomically record lecture session using stored procedure."""
    try:
        conn = pymysql.connect(
            host=fetch_one("SELECT 1") and pymysql.connect.__defaults__ or '127.0.0.1' # connection fallback
        )
    except Exception:
        pass
    
    # Direct DB call
    conn = None
    try:
        from app.db import get_connection
        conn = get_connection()
        with conn.cursor() as cur:
            cur.callproc('sp_record_attendance_session', (
                offering_id, teacher_id, session_date, topic_covered.strip(), 0
            ))
            cur.execute("SELECT @_sp_record_attendance_session_4;")
            row = cur.fetchone()
            sess_id = list(row.values())[0] if isinstance(row, dict) else row[0]
        conn.commit()
        return {'success': True, 'session_id': sess_id, 'message': 'Attendance session created successfully.'}
    except pymysql.MySQLError as e:
        msg = e.args[1] if len(e.args) > 1 else str(e)
        return {'success': False, 'message': f"Failed to record attendance session: {msg}"}
    finally:
        if conn:
            conn.close()

def get_session_roll_call(session_id):
    """Retrieve all students in the offering with their marked status for this session."""
    sess = fetch_one("""
        SELECT att.session_id, att.offering_id, att.session_date, att.topic_covered,
               c.course_code, c.title as course_title, co.section_name,
               u.full_name as teacher_name
        FROM attendance_sessions att
        JOIN course_offerings co ON att.offering_id = co.offering_id
        JOIN courses c ON co.course_id = c.course_id
        JOIN teachers t ON att.teacher_id = t.teacher_id
        JOIN users u ON t.user_id = u.user_id
        WHERE att.session_id = %s
    """, (session_id,))
    if not sess:
        return None, []

    students = fetch_all("""
        SELECT e.enrollment_id, e.student_id, e.total_attendance_pct,
               s.roll_no, s.enrollment_no, u.full_name as student_name,
               COALESCE(ar.status, 'NOT_MARKED') as attendance_status,
               ar.remarks
        FROM enrollments e
        JOIN students s ON e.student_id = s.student_id
        JOIN users u ON s.user_id = u.user_id
        LEFT JOIN attendance_records ar ON ar.session_id = %s AND ar.enrollment_id = e.enrollment_id
        WHERE e.offering_id = %s AND e.status = 'ACTIVE'
        ORDER BY s.roll_no, u.full_name
    """, (session_id, sess['offering_id']))
    return sess, students

def save_roll_call(session_id, records):
    """
    Save attendance records for a session.
    records: list of dicts [{'enrollment_id': int, 'status': str, 'remarks': str}]
    Triggers automatically compute enrollments.total_attendance_pct!
    """
    try:
        with transaction() as conn:
            with conn.cursor() as cur:
                for rec in records:
                    enr_id = rec['enrollment_id']
                    st = rec.get('status', 'PRESENT')
                    rem = rec.get('remarks', '')
                    cur.execute("""
                        INSERT INTO attendance_records (session_id, enrollment_id, status, remarks)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                            status = VALUES(status),
                            remarks = VALUES(remarks);
                    """, (session_id, enr_id, st, rem))
        return {'success': True, 'message': f"Saved attendance for {len(records)} students."}
    except pymysql.MySQLError as e:
        msg = e.args[1] if len(e.args) > 1 else str(e)
        return {'success': False, 'message': f"Failed to save attendance: {msg}"}

def get_student_attendance(student_id):
    """Retrieve full attendance breakdown for a student across all active enrollments."""
    courses_att = fetch_all("""
        SELECT e.enrollment_id, e.offering_id, e.total_attendance_pct,
               c.course_code, c.title as course_title, co.section_name,
               COUNT(ar.session_id) as total_sessions,
               SUM(CASE WHEN ar.status = 'PRESENT' THEN 1 ELSE 0 END) as attended_sessions
        FROM enrollments e
        JOIN course_offerings co ON e.offering_id = co.offering_id
        JOIN courses c ON co.course_id = c.course_id
        LEFT JOIN attendance_records ar ON e.enrollment_id = ar.enrollment_id
        WHERE e.student_id = %s AND e.status IN ('ACTIVE', 'COMPLETED')
        GROUP BY e.enrollment_id, e.offering_id, e.total_attendance_pct, c.course_code, c.title, co.section_name
        ORDER BY c.course_code
    """, (student_id,))

    recent_records = fetch_all("""
        SELECT ar.status, ar.remarks, ar.marked_at,
               att.session_date, att.topic_covered,
               c.course_code, c.title as course_title
        FROM attendance_records ar
        JOIN attendance_sessions att ON ar.session_id = att.session_id
        JOIN enrollments e ON ar.enrollment_id = e.enrollment_id
        JOIN courses c ON e.course_id = c.course_id
        WHERE e.student_id = %s
        ORDER BY att.session_date DESC, ar.marked_at DESC
        LIMIT 20
    """, (student_id,))

    return {
        'courses_attendance': courses_att,
        'recent_records': recent_records
    }


# ============================================================
# 3. COURSEWORK ASSIGNMENTS & SUBMISSIONS
# ============================================================

def create_assignment(offering_id, title, description, max_marks, weightage_pct, due_date, teacher_id):
    """Create coursework assignment specification."""
    try:
        execute_query("""
            INSERT INTO assignments (offering_id, title, description, max_marks, weightage_pct, due_date, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (offering_id, title.strip(), description.strip(), max_marks, weightage_pct, due_date, teacher_id))
        return {'success': True, 'message': 'Assignment published successfully.'}
    except pymysql.MySQLError as e:
        msg = e.args[1] if len(e.args) > 1 else str(e)
        return {'success': False, 'message': f"Failed to publish assignment: {msg}"}

def get_assignment_by_id(assignment_id):
    """Retrieve assignment details with course and section metadata."""
    return fetch_one("""
        SELECT a.assignment_id, a.offering_id, a.title, a.description, a.max_marks,
               a.weightage_pct, a.due_date, a.created_by, a.created_at,
               c.course_id, c.course_code, c.title as course_title, co.section_name,
               u.full_name as teacher_name
        FROM assignments a
        JOIN course_offerings co ON a.offering_id = co.offering_id
        JOIN courses c ON co.course_id = c.course_id
        JOIN teachers t ON a.created_by = t.teacher_id
        JOIN users u ON t.user_id = u.user_id
        WHERE a.assignment_id = %s
    """, (assignment_id,))

def get_assignments_for_offering(offering_id):
    """Retrieve all assignments in an offering with submission statistics."""
    return fetch_all("""
        SELECT a.assignment_id, a.offering_id, a.title, a.description, a.max_marks,
               a.weightage_pct, a.due_date, a.created_at,
               COUNT(s.submission_id) as total_submissions,
               SUM(CASE WHEN s.status = 'EVALUATED' THEN 1 ELSE 0 END) as evaluated_count
        FROM assignments a
        LEFT JOIN submissions s ON a.assignment_id = s.assignment_id
        WHERE a.offering_id = %s
        GROUP BY a.assignment_id, a.offering_id, a.title, a.description, a.max_marks, a.weightage_pct, a.due_date, a.created_at
        ORDER BY a.due_date DESC
    """, (offering_id,))

def get_student_assignments(student_id):
    """Retrieve assignments and student submission status for all enrolled courses."""
    return fetch_all("""
        SELECT a.assignment_id, a.offering_id, a.title, a.description, a.max_marks,
               a.weightage_pct, a.due_date,
               c.course_code, c.title as course_title, co.section_name,
               e.enrollment_id,
               s.submission_id, s.status as submission_status, s.marks_obtained, s.feedback, s.submitted_at
        FROM assignments a
        JOIN course_offerings co ON a.offering_id = co.offering_id
        JOIN courses c ON co.course_id = c.course_id
        JOIN enrollments e ON e.offering_id = co.offering_id AND e.student_id = %s AND e.status = 'ACTIVE'
        LEFT JOIN submissions s ON s.assignment_id = a.assignment_id AND s.enrollment_id = e.enrollment_id
        ORDER BY a.due_date ASC
    """, (student_id,))

def submit_assignment(assignment_id, enrollment_id, submission_text, file_path=None):
    """Submit student coursework, triggering cross-course isolation check trg_submission_offering_validate."""
    try:
        execute_query("""
            INSERT INTO submissions (assignment_id, enrollment_id, submission_text, file_path, status, submitted_at)
            VALUES (%s, %s, %s, %s, 'SUBMITTED', NOW())
            ON DUPLICATE KEY UPDATE 
                submission_text = VALUES(submission_text),
                file_path = COALESCE(VALUES(file_path), file_path),
                status = 'RESUBMITTED',
                submitted_at = NOW();
        """, (assignment_id, enrollment_id, submission_text.strip(), file_path))
        return {'success': True, 'message': 'Coursework submitted successfully.'}
    except pymysql.MySQLError as e:
        msg = e.args[1] if len(e.args) > 1 else str(e)
        return {'success': False, 'message': f"Submission rejected: {msg}"}

def get_assignment_submissions(assignment_id):
    """Retrieve all student submissions for an assignment."""
    return fetch_all("""
        SELECT s.submission_id, s.assignment_id, s.enrollment_id, s.submission_text, s.file_path,
               s.submitted_at, s.status as submission_status, s.marks_obtained, s.feedback, s.graded_at,
               stu.roll_no, stu.enrollment_no, u.full_name as student_name, u.email as student_email,
               a.max_marks
        FROM submissions s
        JOIN assignments a ON s.assignment_id = a.assignment_id
        JOIN enrollments e ON s.enrollment_id = e.enrollment_id
        JOIN students stu ON e.student_id = stu.student_id
        JOIN users u ON stu.user_id = u.user_id
        WHERE s.assignment_id = %s
        ORDER BY s.submitted_at DESC
    """, (assignment_id,))

def grade_submission(submission_id, marks, feedback, teacher_id):
    """Grade submission using stored procedure sp_grade_assignment_submission."""
    conn = None
    try:
        from app.db import get_connection
        conn = get_connection()
        with conn.cursor() as cur:
            cur.callproc('sp_grade_assignment_submission', (
                submission_id, Decimal(str(marks)), feedback.strip(), teacher_id, ''
            ))
            cur.execute("SELECT @_sp_grade_assignment_submission_4;")
            row = cur.fetchone()
            status_msg = list(row.values())[0] if isinstance(row, dict) else row[0]
        conn.commit()

        if status_msg.startswith('SUCCESS'):
            return {'success': True, 'message': status_msg}
        else:
            return {'success': False, 'message': status_msg}
    except pymysql.MySQLError as e:
        msg = e.args[1] if len(e.args) > 1 else str(e)
        return {'success': False, 'message': f"Grading error: {msg}"}
    finally:
        if conn:
            conn.close()


# ============================================================
# 4. CAMPUS & COURSE ANNOUNCEMENTS
# ============================================================

def get_announcements_for_user(user):
    """Retrieve announcements relevant to current user role and course enrollments."""
    if user.is_admin or user.is_coordinator:
        # Coordinators and Admins see all announcements
        return fetch_all("""
            SELECT ann.announcement_id, ann.title, ann.content, ann.offering_id, ann.created_at,
                   u.full_name as author_name, u.role as author_role,
                   c.course_code, c.title as course_title, co.section_name
            FROM announcements ann
            JOIN users u ON ann.author_id = u.user_id
            LEFT JOIN course_offerings co ON ann.offering_id = co.offering_id
            LEFT JOIN courses c ON co.course_id = c.course_id
            ORDER BY ann.created_at DESC
        """)

    if user.is_student and user.student_id:
        return fetch_all("""
            SELECT ann.announcement_id, ann.title, ann.content, ann.offering_id, ann.created_at,
                   u.full_name as author_name, u.role as author_role,
                   c.course_code, c.title as course_title, co.section_name
            FROM announcements ann
            JOIN users u ON ann.author_id = u.user_id
            LEFT JOIN course_offerings co ON ann.offering_id = co.offering_id
            LEFT JOIN courses c ON co.course_id = c.course_id
            WHERE ann.offering_id IS NULL OR ann.offering_id IN (
                SELECT offering_id FROM enrollments WHERE student_id = %s AND status = 'ACTIVE'
            )
            ORDER BY ann.created_at DESC
        """, (user.student_id,))

    if user.is_teacher and user.teacher_id:
        return fetch_all("""
            SELECT ann.announcement_id, ann.title, ann.content, ann.offering_id, ann.created_at,
                   u.full_name as author_name, u.role as author_role,
                   c.course_code, c.title as course_title, co.section_name
            FROM announcements ann
            JOIN users u ON ann.author_id = u.user_id
            LEFT JOIN course_offerings co ON ann.offering_id = co.offering_id
            LEFT JOIN courses c ON co.course_id = c.course_id
            WHERE ann.offering_id IS NULL OR ann.offering_id IN (
                SELECT offering_id FROM course_instructors WHERE teacher_id = %s
            )
            ORDER BY ann.created_at DESC
        """, (user.teacher_id,))

    # Default fallback
    return fetch_all("""
        SELECT ann.announcement_id, ann.title, ann.content, ann.created_at,
               u.full_name as author_name, u.role as author_role, NULL as course_code, NULL as course_title, NULL as section_name
        FROM announcements ann
        JOIN users u ON ann.author_id = u.user_id
        WHERE ann.offering_id IS NULL
        ORDER BY ann.created_at DESC
    """)

def create_announcement(title, content, author_id, offering_id=None):
    """Publish a new announcement."""
    try:
        execute_query("""
            INSERT INTO announcements (title, content, offering_id, author_id)
            VALUES (%s, %s, %s, %s)
        """, (title.strip(), content.strip(), offering_id if offering_id else None, author_id))
        return {'success': True, 'message': 'Announcement posted successfully.'}
    except pymysql.MySQLError as e:
        msg = e.args[1] if len(e.args) > 1 else str(e)
        return {'success': False, 'message': f"Failed to post announcement: {msg}"}

def delete_announcement(announcement_id, user_id, is_admin=False):
    """Delete an announcement if author or administrator."""
    try:
        if is_admin:
            execute_query("DELETE FROM announcements WHERE announcement_id = %s", (announcement_id,))
        else:
            execute_query("DELETE FROM announcements WHERE announcement_id = %s AND author_id = %s", (announcement_id, user_id))
        return {'success': True, 'message': 'Announcement deleted successfully.'}
    except pymysql.MySQLError as e:
        msg = e.args[1] if len(e.args) > 1 else str(e)
        return {'success': False, 'message': f"Failed to delete announcement: {msg}"}
