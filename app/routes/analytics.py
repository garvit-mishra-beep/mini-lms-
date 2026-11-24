"""Analytics routes providing live chart data directly from SQL aggregations."""
import json
from datetime import datetime
from flask import Blueprint, render_template, jsonify, Response, redirect, url_for, flash, request
from flask_login import login_required
from app.db import fetch_all, scalar
from app.services import reporting_service

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/')
@login_required
def index():
    # 1. Enrollments by course (from v_course_enrollments)
    course_enrollments = fetch_all("""
        SELECT course_code, title, total_enrollments
        FROM v_course_enrollments
        ORDER BY total_enrollments DESC
    """)

    # 2. Grade distribution (A, B, C, D, F counts)
    grade_distribution = fetch_all("""
        SELECT letter_grade, COUNT(*) as count
        FROM grades
        GROUP BY letter_grade
        ORDER BY FIELD(letter_grade, 'A', 'B', 'C', 'D', 'F')
    """)

    # 3. Course completion statistics (from v_course_completion)
    completion_rates = fetch_all("""
        SELECT course_code, enrollments_with_completion_record, completed_count,
               ROUND(completed_count / NULLIF(enrollments_with_completion_record, 0) * 100, 1) as completion_pct
        FROM v_course_completion
        ORDER BY course_code
    """)

    # 4. Quiz performance (from v_quiz_performance)
    quiz_perf = fetch_all("""
        SELECT title, submissions, average_score, max_score,
               ROUND(average_score / NULLIF(max_score, 0) * 100, 1) as avg_pct
        FROM v_quiz_performance
        ORDER BY quiz_id
    """)

    # 5. Monthly enrollment trend
    enrollment_trends = fetch_all("""
        SELECT DATE_FORMAT(enrolled_at, '%Y-%m') as month, COUNT(*) as total
        FROM enrollments
        GROUP BY DATE_FORMAT(enrolled_at, '%Y-%m')
        ORDER BY month ASC
    """)

    # 6. Overall high-level KPIs
    kpis = {
        'total_students': scalar("SELECT COUNT(*) FROM students"),
        'active_students': scalar("SELECT COUNT(*) FROM students s JOIN users u ON u.user_id = s.user_id WHERE u.status = 'ACTIVE'"),
        'total_teachers': scalar("SELECT COUNT(*) FROM teachers"),
        'published_courses': scalar("SELECT COUNT(*) FROM courses WHERE status = 'PUBLISHED'"),
        'active_enrollments': scalar("SELECT COUNT(*) FROM enrollments WHERE status = 'ACTIVE'"),
        'completed_enrollments': scalar("SELECT COUNT(*) FROM completions WHERE completion_status = 'COMPLETED'"),
        'total_quizzes': scalar("SELECT COUNT(*) FROM quizzes"),
        'quiz_attempts': scalar("SELECT COUNT(*) FROM attempts WHERE status = 'SUBMITTED'"),
        'avg_grade': scalar("SELECT ROUND(AVG(final_score), 1) FROM grades WHERE published = 1"),
        'certificates_issued': scalar("SELECT COUNT(*) FROM certificates")
    }

    chart_payload = {
        'course_labels': [r['course_code'] for r in course_enrollments],
        'course_data': [int(r['total_enrollments']) for r in course_enrollments],
        'grade_labels': [r['letter_grade'] for r in grade_distribution],
        'grade_data': [int(r['count']) for r in grade_distribution],
        'comp_labels': [r['course_code'] for r in completion_rates],
        'comp_data': [float(r['completion_pct'] or 0) for r in completion_rates],
        'quiz_labels': [r['title'] for r in quiz_perf],
        'quiz_data': [float(r['avg_pct'] or 0) for r in quiz_perf],
        'trend_labels': [r['month'] for r in enrollment_trends],
        'trend_data': [int(r['total']) for r in enrollment_trends]
    }

    return render_template(
        'analytics/index.html',
        active='analytics',
        kpis=kpis,
        chart_payload=chart_payload,
        chart_json=json.dumps(chart_payload)
    )

@analytics_bp.route('/reports')
@login_required
def reports_catalog():
    """Browse catalog of all 16 institutional reports."""
    catalog = reporting_service.get_report_catalog()
    return render_template('analytics/reports_index.html', active='reports', catalog=catalog)

@analytics_bp.route('/report/<report_id>')
@login_required
def view_report(report_id):
    """View executed institutional report in tabular format."""
    report_data = reporting_service.execute_report(report_id)
    if not report_data['headers']:
        flash(f"Report {report_id} not found or has no columns.", "warning")
        return redirect(url_for('analytics.reports_catalog'))
    return render_template('analytics/report_view.html', active='reports', report=report_data)

@analytics_bp.route('/report/<report_id>/export')
@login_required
def export_report(report_id):
    """Export report as RFC 4180 CSV document."""
    csv_content = reporting_service.generate_report_csv(report_id)
    filename = f"MiniLMS_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@analytics_bp.route('/executive')
@login_required
def executive_dashboard():
    """Master Executive Leadership Dashboard with multi-dimensional Chart.js visualizations."""
    dept_stats = fetch_all("SELECT * FROM v_department_performance")
    capacity_stats = fetch_all("SELECT * FROM v_course_offering_summary ORDER BY capacity_utilization_pct DESC")
    workload_stats = fetch_all("SELECT * FROM v_faculty_workload")
    
    # Executive KPIs
    exec_kpis = {
        'total_students': scalar("SELECT COUNT(*) FROM students"),
        'avg_cgpa': scalar("SELECT ROUND(AVG(cgpa), 2) FROM students"),
        'capacity_utilization': scalar("SELECT ROUND(AVG((enrolled_count * 100.0) / NULLIF(max_capacity, 0)), 1) FROM course_offerings"),
        'retention_pct': scalar("SELECT ROUND((SUM(CASE WHEN status='ACTIVE' THEN 1 ELSE 0 END)*100.0)/COUNT(*), 1) FROM enrollments"),
        'avg_attendance': scalar("SELECT ROUND(AVG(total_attendance_pct), 1) FROM enrollments WHERE status='ACTIVE'"),
        'published_grades': scalar("SELECT COUNT(*) FROM grades WHERE published = 1")
    }

    # Chart payload for executive visualizations
    exec_charts = {
        'dept_labels': [r['department_code'] for r in dept_stats],
        'dept_cgpa': [float(r['dept_avg_cgpa'] or 0) for r in dept_stats],
        'dept_students': [int(r['total_students'] or 0) for r in dept_stats],
        'cap_labels': [f"{r['course_code']} ({r['section_name']})" for r in capacity_stats],
        'cap_util': [float(r['capacity_utilization_pct'] or 0) for r in capacity_stats],
        'work_labels': [r['full_name'] for r in workload_stats],
        'work_credits': [float(r['total_teaching_credits'] or 0) for r in workload_stats]
    }

    return render_template(
        'analytics/executive_dashboard.html',
        active='executive',
        kpis=exec_kpis,
        charts_json=json.dumps(exec_charts),
        capacity_stats=capacity_stats
    )
