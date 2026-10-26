"""Database Explorer Route — Academic showcase for DBMS viva."""
from flask import Blueprint, render_template, request, abort, flash
from flask_login import login_required, current_user
from app.auth.decorators import admin_required
from app.db import fetch_all, scalar

explorer_bp = Blueprint('explorer', __name__)

BASE_TABLES = [
    'users', 'teachers', 'students', 'courses', 'course_instructors',
    'modules', 'lessons', 'lesson_prerequisites', 'enrollments', 'lesson_progress',
    'quizzes', 'quiz_questions', 'quiz_options', 'attempts', 'attempt_answers',
    'grades', 'grade_change_history', 'completions', 'certificates', 'audit_logs', 'schema_versions'
]

VIEWS = [
    'v_student_courses', 'v_course_enrollments', 'v_student_grades',
    'v_quiz_performance', 'v_course_completion'
]

CURATED_QUERIES = [
    {
        'id': 'join_multi',
        'title': 'Relational Multi-Table Join',
        'category': 'JOIN Demonstration',
        'description': 'Demonstrates joining 5 relational tables (Students, Users, Enrollments, Courses, Grades) to display student academic standing.',
        'sql': """SELECT u.full_name, s.roll_no, c.course_code, c.title as course_title,
       e.status as enrollment_status, g.final_score, g.letter_grade
FROM students s
JOIN users u ON u.user_id = s.user_id
JOIN enrollments e ON e.student_id = s.student_id
JOIN courses c ON c.course_id = e.course_id
LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
ORDER BY c.course_code, u.full_name;"""
    },
    {
        'id': 'window_fn',
        'title': 'Window Functions (DENSE_RANK & OVER)',
        'category': 'Window Functions',
        'description': 'Uses MySQL 8.0 DENSE_RANK() OVER (PARTITION BY course_code ORDER BY final_score DESC) to rank student performers within each course.',
        'sql': """SELECT c.course_code, u.full_name, g.final_score, g.letter_grade,
       DENSE_RANK() OVER (PARTITION BY c.course_code ORDER BY g.final_score DESC) as class_rank
FROM grades g
JOIN enrollments e ON e.enrollment_id = g.enrollment_id
JOIN courses c ON c.course_id = e.course_id
JOIN students s ON s.student_id = e.student_id
JOIN users u ON u.user_id = s.user_id
WHERE g.published = 1
ORDER BY c.course_code, class_rank;"""
    },
    {
        'id': 'group_having',
        'title': 'Aggregation with GROUP BY & HAVING',
        'category': 'Grouping & Filtering',
        'description': 'Aggregates enrollment counts per course and filters only popular courses with total enrollments >= 1.',
        'sql': """SELECT c.course_code, c.title,
       COUNT(e.enrollment_id) as total_enrolled,
       SUM(e.status = 'ACTIVE') as active_count,
       SUM(e.status = 'COMPLETED') as completed_count
FROM courses c
LEFT JOIN enrollments e ON e.course_id = c.course_id
GROUP BY c.course_id, c.course_code, c.title
HAVING total_enrolled >= 1
ORDER BY total_enrolled DESC;"""
    },
    {
        'id': 'subquery_correlated',
        'title': 'Correlated Subquery & NOT EXISTS',
        'category': 'Subqueries & Set Operations',
        'description': 'Finds all published courses that currently have active enrollments that have not completed mandatory lesson requirements.',
        'sql': """SELECT c.course_code, c.title, u.full_name as student_name, l.title as incomplete_lesson
FROM enrollments e
JOIN courses c ON c.course_id = e.course_id
JOIN students s ON s.student_id = e.student_id
JOIN users u ON u.user_id = s.user_id
JOIN modules m ON m.course_id = c.course_id
JOIN lessons l ON l.module_id = m.module_id
WHERE e.status = 'ACTIVE' AND l.required_for_completion = 1
  AND NOT EXISTS (
      SELECT 1 FROM lesson_progress lp
      WHERE lp.enrollment_id = e.enrollment_id AND lp.lesson_id = l.lesson_id
  )
LIMIT 20;"""
    },
    {
        'id': 'cte_recursive',
        'title': 'Common Table Expression (CTE)',
        'category': 'CTEs',
        'description': 'Demonstrates WITH clause summarizing average score benchmarks by course and comparing individual students against course averages.',
        'sql': """WITH CourseBenchmarks AS (
    SELECT c.course_id, c.course_code, ROUND(AVG(g.final_score), 2) as course_avg
    FROM courses c
    JOIN enrollments e ON e.course_id = c.course_id
    JOIN grades g ON g.enrollment_id = e.enrollment_id
    WHERE g.published = 1
    GROUP BY c.course_id, c.course_code
)
SELECT u.full_name, cb.course_code, g.final_score, cb.course_avg,
       ROUND(g.final_score - cb.course_avg, 2) as delta_from_avg
FROM grades g
JOIN enrollments e ON e.enrollment_id = g.enrollment_id
JOIN CourseBenchmarks cb ON cb.course_id = e.course_id
JOIN students s ON s.student_id = e.student_id
JOIN users u ON u.user_id = s.user_id
ORDER BY cb.course_code, g.final_score DESC;"""
    }
]

@explorer_bp.route('/')
@explorer_bp.route('/<name>')
@admin_required
def index(name='users'):
    valid_names = BASE_TABLES + VIEWS
    if name not in valid_names:
        name = 'users'

    # Pagination & Search
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page
    search = request.args.get('search', '').strip()

    # Total row count
    total_rows = scalar(f"SELECT COUNT(*) FROM `{name}`")

    # Column definitions with keys and data types from information_schema
    columns_info = fetch_all("""
        SELECT COLUMN_NAME as column_name, DATA_TYPE as data_type, IS_NULLABLE as is_nullable,
               COLUMN_KEY as column_key, COLUMN_DEFAULT as column_default, EXTRA as extra
        FROM information_schema.columns
        WHERE table_schema = DATABASE() AND table_name = %s
        ORDER BY ordinal_position
    """, (name,))

    # Table Indexes
    indexes = fetch_all(f"SHOW INDEX FROM `{name}`")

    # Foreign keys
    foreign_keys = fetch_all("""
        SELECT COLUMN_NAME as column_name, REFERENCED_TABLE_NAME as referenced_table_name,
               REFERENCED_COLUMN_NAME as referenced_column_name, CONSTRAINT_NAME as constraint_name
        FROM information_schema.key_column_usage
        WHERE table_schema = DATABASE() AND table_name = %s AND referenced_table_name IS NOT NULL
    """, (name,))

    # Data rows (safe parameterized limit)
    rows = fetch_all(f"SELECT * FROM `{name}` LIMIT %s OFFSET %s", (per_page, offset))
    cols = [c['column_name'] for c in columns_info] if columns_info else (list(rows[0].keys()) if rows else [])

    # Schema overview (list all tables with count)
    table_stats = []
    for t in BASE_TABLES:
        table_stats.append({
            'name': t,
            'is_view': False,
            'count': scalar(f"SELECT COUNT(*) FROM `{t}`")
        })
    for v in VIEWS:
        table_stats.append({
            'name': v,
            'is_view': True,
            'count': scalar(f"SELECT COUNT(*) FROM `{v}`")
        })

    # Procedures and triggers in minilms_db
    procedures = fetch_all("SHOW PROCEDURE STATUS WHERE Db = DATABASE()")
    triggers = fetch_all("SHOW TRIGGERS")

    # Curated demo query execution if requested
    query_id = request.args.get('query_id')
    curated_result = None
    selected_query = None
    if query_id:
        selected_query = next((q for q in CURATED_QUERIES if q['id'] == query_id), None)
        if selected_query:
            curated_rows = fetch_all(selected_query['sql'])
            curated_cols = list(curated_rows[0].keys()) if curated_rows else []
            curated_result = {'rows': curated_rows, 'cols': curated_cols}

    return render_template(
        'explorer/index.html',
        active='explorer',
        current_name=name,
        is_view=name in VIEWS,
        base_tables=BASE_TABLES,
        views=VIEWS,
        table_stats=table_stats,
        columns_info=columns_info,
        indexes=indexes,
        foreign_keys=foreign_keys,
        rows=rows,
        cols=cols,
        total_rows=total_rows,
        page=page,
        per_page=per_page,
        procedures=procedures,
        triggers=triggers,
        curated_queries=CURATED_QUERIES,
        selected_query=selected_query,
        curated_result=curated_result
    )
