"""Reporting service for MiniLMS.
Provides structured data retrieval, parametric filtering, and CSV export
for all 16 institutional operational, management, trend, and exception reports.
"""
import io
import csv
from datetime import datetime
from app.db import fetch_all, fetch_one

# Catalog of the 16 standard institutional reports
REPORT_CATALOG = {
    # Operational Reports (OR)
    'OR-01': {
        'code': 'OR-01',
        'title': 'Student Course Enrollment Roster',
        'category': 'OPERATIONAL',
        'description': 'Comprehensive active student enrollment list per course offering with attendance percentages.'
    },
    'OR-02': {
        'code': 'OR-02',
        'title': 'Lecture Attendance Register',
        'category': 'OPERATIONAL',
        'description': 'Session-by-session roll call logs and topic coverage tracking.'
    },
    'OR-03': {
        'code': 'OR-03',
        'title': 'Assignment Submissions & Evaluation Status',
        'category': 'OPERATIONAL',
        'description': 'Student coursework submission timestamps, evaluation status, and marks obtained.'
    },
    'OR-04': {
        'code': 'OR-04',
        'title': 'Official Published Grades & Score Distribution',
        'category': 'OPERATIONAL',
        'description': 'Course-level final grades, calculated letter grades, and publication standing.'
    },
    'OR-05': {
        'code': 'OR-05',
        'title': 'Course Module & Lesson Completion Progress',
        'category': 'OPERATIONAL',
        'description': 'Student progress through sequential instructional lessons and modules.'
    },

    # Management Reports (MR)
    'MR-01': {
        'code': 'MR-01',
        'title': 'Department Academic Performance Benchmark',
        'category': 'MANAGEMENT',
        'description': 'Departmental student enrollment counts, faculty count, and mean CGPA benchmark.'
    },
    'MR-02': {
        'code': 'MR-02',
        'title': 'Course Offering Demand & Capacity Utilization',
        'category': 'MANAGEMENT',
        'description': 'Section capacity limits vs enrolled student counts and expansion demand.'
    },
    'MR-03': {
        'code': 'MR-03',
        'title': 'Faculty Teaching Workload & Allocation Distribution',
        'category': 'MANAGEMENT',
        'description': 'Faculty course assignments, teaching load in credits, and student headcounts.'
    },
    'MR-04': {
        'code': 'MR-04',
        'title': 'Term-Over-Term Academic Activity Summary',
        'category': 'MANAGEMENT',
        'description': 'Comparison of enrollment and completion activity across academic terms.'
    },
    'MR-05': {
        'code': 'MR-05',
        'title': 'Student Academic Standing & Honors Classification',
        'category': 'MANAGEMENT',
        'description': 'Stratification of student population across first class, second class, and academic support.'
    },

    # Trend Reports (TR)
    'TR-01': {
        'code': 'TR-01',
        'title': 'Enrollment Growth & Registration Velocity',
        'category': 'TREND',
        'description': 'Cumulative enrollment trajectory and registration acceleration over time.'
    },
    'TR-02': {
        'code': 'TR-02',
        'title': 'Weekly Lecture Attendance Trends',
        'category': 'TREND',
        'description': 'Temporal analysis of student classroom attendance percentages across lecture sessions.'
    },
    'TR-03': {
        'code': 'TR-03',
        'title': 'Coursework Score Trends & Historical Grade Trajectory',
        'category': 'TREND',
        'description': 'Grade score distributions and assignment score progression.'
    },

    # Exception Reports (ER)
    'ER-01': {
        'code': 'ER-01',
        'title': 'Critical Low Attendance Exception Report (< 75%)',
        'category': 'EXCEPTION',
        'description': 'Identifies students failing the statutory 75% attendance threshold who risk exam debarment.'
    },
    'ER-02': {
        'code': 'ER-02',
        'title': 'Academic Workflow Processing Exceptions',
        'category': 'EXCEPTION',
        'description': 'Flags pending un-evaluated submissions, unverified grades, and missing sessions.'
    },

    # Audit & Compliance Reports (AR)
    'AR-01': {
        'code': 'AR-01',
        'title': 'System Security Audit Trail & Compliance Log',
        'category': 'MANAGEMENT',
        'description': 'Chronological audit log of administrative mutations, role updates, and transactional events.'
    }
}

def get_report_catalog():
    """Return catalog of all 16 reports categorized."""
    return REPORT_CATALOG

def execute_report(report_id: str, filters: dict = None):
    """Execute dynamic query corresponding to report_id with optional filters."""
    filters = filters or {}

    if report_id == 'OR-01':
        # Student Course Enrollment Roster
        sql = """
            SELECT e.enrollment_id, s.roll_no, u.full_name, c.course_code, c.title as course_title,
                   t.term_code, co.section_name, e.status, e.total_attendance_pct
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            JOIN users u ON s.user_id = u.user_id
            JOIN course_offerings co ON e.offering_id = co.offering_id
            JOIN courses c ON co.course_id = c.course_id
            JOIN academic_terms t ON co.term_id = t.term_id
            ORDER BY c.course_code, s.roll_no
        """
        rows = fetch_all(sql)
        headers = ['Enrollment ID', 'Roll No', 'Student Name', 'Course Code', 'Course Title', 'Term', 'Section', 'Status', 'Attendance %']

    elif report_id == 'OR-02':
        # Lecture Attendance Register
        sql = """
            SELECT s.session_id, c.course_code, co.section_name, s.session_date, s.topic_covered,
                   u.full_name as teacher_name,
                   COUNT(ar.enrollment_id) as total_marked,
                   SUM(CASE WHEN ar.status = 'PRESENT' THEN 1 ELSE 0 END) as present_count,
                   SUM(CASE WHEN ar.status = 'ABSENT' THEN 1 ELSE 0 END) as absent_count
            FROM attendance_sessions s
            JOIN course_offerings co ON s.offering_id = co.offering_id
            JOIN courses c ON co.course_id = c.course_id
            JOIN teachers t ON s.teacher_id = t.teacher_id
            JOIN users u ON t.user_id = u.user_id
            LEFT JOIN attendance_records ar ON s.session_id = ar.session_id
            GROUP BY s.session_id, c.course_code, co.section_name, s.session_date, s.topic_covered, u.full_name
            ORDER BY s.session_date DESC
        """
        rows = fetch_all(sql)
        headers = ['Session ID', 'Course Code', 'Section', 'Date', 'Topic Covered', 'Faculty', 'Marked Count', 'Present', 'Absent']

    elif report_id == 'OR-03':
        # Assignment Submissions & Evaluation Status
        sql = """
            SELECT sub.submission_id, a.title as assignment_title, c.course_code, s.roll_no, u.full_name as student_name,
                   sub.submitted_at, sub.status as evaluation_status, sub.marks_obtained, a.max_marks,
                   sub.graded_at
            FROM submissions sub
            JOIN assignments a ON sub.assignment_id = a.assignment_id
            JOIN course_offerings co ON a.offering_id = co.offering_id
            JOIN courses c ON co.course_id = c.course_id
            JOIN enrollments e ON sub.enrollment_id = e.enrollment_id
            JOIN students s ON e.student_id = s.student_id
            JOIN users u ON s.user_id = u.user_id
            ORDER BY sub.submitted_at DESC
        """
        rows = fetch_all(sql)
        headers = ['Submission ID', 'Assignment', 'Course', 'Roll No', 'Student Name', 'Submitted At', 'Status', 'Marks', 'Max Marks', 'Graded At']

    elif report_id == 'OR-04':
        # Official Published Grades
        sql = """
            SELECT g.grade_id, s.roll_no, u.full_name as student_name, c.course_code, c.title as course_title,
                   g.final_score, g.letter_grade, CASE WHEN g.published = 1 THEN 'PUBLISHED' ELSE 'DRAFT' END as publish_status,
                   g.published_at
            FROM grades g
            JOIN enrollments e ON g.enrollment_id = e.enrollment_id
            JOIN students s ON e.student_id = s.student_id
            JOIN users u ON s.user_id = u.user_id
            JOIN courses c ON e.course_id = c.course_id
            ORDER BY c.course_code, g.final_score DESC
        """
        rows = fetch_all(sql)
        headers = ['Grade ID', 'Roll No', 'Student Name', 'Course Code', 'Course Title', 'Final Score', 'Letter Grade', 'Status', 'Published Date']

    elif report_id == 'OR-05':
        # Course Module & Lesson Completion Progress
        sql = """
            SELECT comp.enrollment_id, s.roll_no, u.full_name as student_name, c.course_code,
                   comp.completion_status, comp.completed_at
            FROM completions comp
            JOIN enrollments e ON comp.enrollment_id = e.enrollment_id
            JOIN students s ON e.student_id = s.student_id
            JOIN users u ON s.user_id = u.user_id
            JOIN courses c ON e.course_id = c.course_id
            ORDER BY c.course_code, s.roll_no
        """
        rows = fetch_all(sql)
        headers = ['Enrollment ID', 'Roll No', 'Student Name', 'Course Code', 'Status', 'Completed Date']

    elif report_id == 'MR-01':
        # Department Academic Performance Benchmark
        sql = "SELECT * FROM v_department_performance"
        rows = fetch_all(sql)
        headers = ['Dept ID', 'Code', 'Department Name', 'Total Students', 'Mean CGPA', 'Courses Offered', 'Faculty Count']

    elif report_id == 'MR-02':
        # Course Offering Demand & Capacity Utilization
        sql = "SELECT * FROM v_course_offering_summary ORDER BY capacity_utilization_pct DESC"
        rows = fetch_all(sql)
        headers = ['Offering ID', 'Course Code', 'Title', 'Credits', 'Dept', 'Term', 'Term Name', 'Section', 'Max Cap', 'Enrolled', 'Utilization %', 'Status', 'Primary Faculty', 'Employee Code']

    elif report_id == 'MR-03':
        # Faculty Teaching Allocation & Workload Distribution
        sql = "SELECT * FROM v_faculty_workload"
        rows = fetch_all(sql)
        headers = ['Faculty ID', 'Employee Code', 'Faculty Name', 'Qualification', 'Assigned Courses', 'Sections Taught', 'Credit Load']

    elif report_id == 'MR-04':
        # Term-Over-Term Activity Summary
        sql = """
            SELECT t.term_code, t.term_name, COUNT(DISTINCT co.offering_id) as total_offerings,
                   COUNT(DISTINCT e.enrollment_id) as total_enrollments,
                   SUM(CASE WHEN e.status = 'COMPLETED' THEN 1 ELSE 0 END) as completions_count
            FROM academic_terms t
            LEFT JOIN course_offerings co ON t.term_id = co.term_id
            LEFT JOIN enrollments e ON co.offering_id = e.offering_id
            GROUP BY t.term_code, t.term_name
            ORDER BY t.term_code DESC
        """
        rows = fetch_all(sql)
        headers = ['Term Code', 'Term Name', 'Total Offerings', 'Total Enrollments', 'Completed Enrollments']

    elif report_id == 'MR-05':
        # Student Academic Standing
        sql = "SELECT * FROM v_student_academic_summary ORDER BY cgpa DESC"
        rows = fetch_all(sql)
        headers = ['Student ID', 'Roll No', 'Enrollment No', 'Full Name', 'Email', 'Dept Code', 'Dept Name', 'Semester', 'CGPA', 'Status', 'Enrolled Courses', 'Completed Courses', 'Avg Attendance %']

    elif report_id == 'TR-01':
        # Enrollment Growth & Registration Velocity
        sql = """
            SELECT DATE(enrolled_at) as registration_date,
                   COUNT(*) as daily_new_registrations,
                   SUM(COUNT(*)) OVER (ORDER BY DATE(enrolled_at)) as cumulative_total_students
            FROM enrollments
            GROUP BY DATE(enrolled_at)
            ORDER BY registration_date ASC
        """
        rows = fetch_all(sql)
        headers = ['Registration Date', 'Daily Registrations', 'Cumulative Enrolled Students']

    elif report_id == 'TR-02':
        # Weekly Lecture Attendance Trends
        sql = """
            SELECT s.session_date, c.course_code, co.section_name, s.topic_covered,
                   ROUND(SUM(CASE WHEN ar.status = 'PRESENT' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(ar.enrollment_id), 0), 1) as session_attendance_pct
            FROM attendance_sessions s
            JOIN course_offerings co ON s.offering_id = co.offering_id
            JOIN courses c ON co.course_id = c.course_id
            LEFT JOIN attendance_records ar ON s.session_id = ar.session_id
            GROUP BY s.session_id, s.session_date, c.course_code, co.section_name, s.topic_covered
            ORDER BY s.session_date ASC
        """
        rows = fetch_all(sql)
        headers = ['Session Date', 'Course Code', 'Section', 'Topic Covered', 'Session Attendance %']

    elif report_id == 'TR-03':
        # Coursework Score Trends
        sql = """
            SELECT a.title as assignment_title, c.course_code, a.max_marks,
                   COUNT(s.submission_id) as total_evaluated,
                   ROUND(AVG(s.marks_obtained), 2) as avg_marks,
                   ROUND(MIN(s.marks_obtained), 2) as min_marks,
                   ROUND(MAX(s.marks_obtained), 2) as max_marks_awarded
            FROM assignments a
            JOIN course_offerings co ON a.offering_id = co.offering_id
            JOIN courses c ON co.course_id = c.course_id
            LEFT JOIN submissions s ON a.assignment_id = s.assignment_id AND s.status = 'EVALUATED'
            GROUP BY a.assignment_id, a.title, c.course_code, a.max_marks
        """
        rows = fetch_all(sql)
        headers = ['Assignment', 'Course Code', 'Max Marks', 'Evaluated Submissions', 'Average Marks', 'Min Marks', 'Max Marks Awarded']

    elif report_id == 'ER-01':
        # Critical Low Attendance Exception (< 75%)
        sql = """
            SELECT s.roll_no, u.full_name, u.email, c.course_code, co.section_name,
                   e.total_attendance_pct,
                   'DEBARMENT RISK: Attendance below statutory 75%% threshold' as exception_cause
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            JOIN users u ON s.user_id = u.user_id
            JOIN course_offerings co ON e.offering_id = co.offering_id
            JOIN courses c ON co.course_id = c.course_id
            WHERE e.status = 'ACTIVE' AND e.total_attendance_pct < 75.00
            ORDER BY e.total_attendance_pct ASC
        """
        rows = fetch_all(sql)
        headers = ['Roll No', 'Student Name', 'Email', 'Course Code', 'Section', 'Attendance %', 'Exception Detail']

    elif report_id == 'ER-02':
        # Academic Workflow Exceptions (Ungraded Submissions or Zero Attendance Sessions)
        sql = """
            SELECT sub.submission_id, a.title as item_name, c.course_code, s.roll_no,
                   sub.submitted_at, sub.status as current_state,
                   'UNGRADED: Assignment awaiting instructor grading' as exception_type
            FROM submissions sub
            JOIN assignments a ON sub.assignment_id = a.assignment_id
            JOIN course_offerings co ON a.offering_id = co.offering_id
            JOIN courses c ON co.course_id = c.course_id
            JOIN enrollments e ON sub.enrollment_id = e.enrollment_id
            JOIN students s ON e.student_id = s.student_id
            WHERE sub.status IN ('SUBMITTED', 'RESUBMITTED')
        """
        rows = fetch_all(sql)
        headers = ['Submission ID', 'Assignment Item', 'Course Code', 'Roll No', 'Submitted At', 'Current State', 'Exception Type']

    elif report_id == 'AR-01':
        # Security Audit Trail & Compliance Log
        sql = """
            SELECT al.audit_id, al.action_time, al.action_type, al.entity_name, al.entity_id,
                   u.email as performed_by_email, u.role as actor_role, al.details
            FROM audit_logs al
            LEFT JOIN users u ON al.performed_by = u.user_id
            ORDER BY al.action_time DESC
            LIMIT 100
        """
        rows = fetch_all(sql)
        headers = ['Audit ID', 'Timestamp', 'Action Type', 'Entity', 'Entity ID', 'Actor Email', 'Role', 'Details']

    else:
        rows = []
        headers = []

    return {
        'meta': REPORT_CATALOG.get(report_id, {'code': report_id, 'title': 'Custom Report'}),
        'headers': headers,
        'rows': rows,
        'count': len(rows),
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def generate_report_csv(report_id: str, filters: dict = None) -> str:
    """Generate RFC 4180 compliant CSV string for the requested report."""
    data = execute_report(report_id, filters)
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Metadata headers
    writer.writerow([f"# MiniLMS Institutional Report: {data['meta']['title']} ({data['meta']['code']})"])
    writer.writerow([f"# Generated At: {data['generated_at']}"])
    writer.writerow([f"# Total Records: {data['count']}"])
    writer.writerow([])

    # Table columns
    writer.writerow(data['headers'])

    # Data rows
    for row in data['rows']:
        writer.writerow([row[k] for k in row])

    return output.getvalue()
