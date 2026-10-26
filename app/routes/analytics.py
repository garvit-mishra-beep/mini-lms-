"""Analytics routes providing live chart data directly from SQL aggregations."""
import json
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from app.db import fetch_all, scalar

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
