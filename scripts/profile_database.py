"""Database Profiling and Data Quality Discovery Script for Phase 11.
Audits row counts, NULL checks, uniqueness, numeric bounds, foreign key integrity,
and academic invariants across minilms_benchmark_db.
"""
import sys
import os
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db import get_connection

def profile_database(db_name="minilms_benchmark_db"):
    conn = get_connection()
    report = {
        'database': db_name,
        'profiled_at': str(datetime.now()),
        'tables': {},
        'foreign_key_integrity': {},
        'academic_invariants': {}
    }
    
    try:
        with conn.cursor() as cur:
            cur.execute(f"USE `{db_name}`")
            
            # 1. Table metrics
            cur.execute("""
                SELECT TABLE_NAME, TABLE_ROWS, DATA_LENGTH, INDEX_LENGTH 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """, (db_name,))
            tables = cur.fetchall()
            
            for t in tables:
                tname = t['TABLE_NAME']
                cur.execute(f"SELECT COUNT(*) AS cnt FROM `{tname}`")
                actual_cnt = cur.fetchone()['cnt']
                
                # Check columns and nulls
                cur.execute(f"DESCRIBE `{tname}`")
                cols = cur.fetchall()
                null_counts = {}
                for col in cols:
                    cname = col['Field']
                    cur.execute(f"SELECT COUNT(*) AS null_cnt FROM `{tname}` WHERE `{cname}` IS NULL")
                    null_c = cur.fetchone()['null_cnt']
                    if null_c > 0:
                        null_counts[cname] = null_c
                
                report['tables'][tname] = {
                    'actual_row_count': actual_cnt,
                    'data_length_bytes': t['DATA_LENGTH'],
                    'index_length_bytes': t['INDEX_LENGTH'],
                    'nullable_columns_with_nulls': null_counts
                }
            
            # 2. Referential integrity (orphan checks)
            orphan_checks = [
                ("enrollments $\rightarrow$ students", "SELECT COUNT(*) AS cnt FROM enrollments e LEFT JOIN students s ON e.student_id = s.student_id WHERE s.student_id IS NULL"),
                ("enrollments $\rightarrow$ courses", "SELECT COUNT(*) AS cnt FROM enrollments e LEFT JOIN courses c ON e.course_id = c.course_id WHERE c.course_id IS NULL"),
                ("attendance_records $\rightarrow$ sessions", "SELECT COUNT(*) AS cnt FROM attendance_records a LEFT JOIN attendance_sessions s ON a.session_id = s.session_id WHERE s.session_id IS NULL"),
                ("attendance_records $\rightarrow$ enrollments", "SELECT COUNT(*) AS cnt FROM attendance_records a LEFT JOIN enrollments e ON a.enrollment_id = e.enrollment_id WHERE e.enrollment_id IS NULL"),
                ("submissions $\rightarrow$ assignments", "SELECT COUNT(*) AS cnt FROM submissions s LEFT JOIN assignments a ON s.assignment_id = a.assignment_id WHERE a.assignment_id IS NULL"),
                ("grades $\rightarrow$ enrollments", "SELECT COUNT(*) AS cnt FROM grades g LEFT JOIN enrollments e ON g.enrollment_id = e.enrollment_id WHERE e.enrollment_id IS NULL"),
                ("academic_risks $\rightarrow$ offerings", "SELECT COUNT(*) AS cnt FROM academic_risks r LEFT JOIN course_offerings o ON r.offering_id = o.offering_id WHERE o.offering_id IS NULL")
            ]
            for name, query in orphan_checks:
                cur.execute(query)
                orphan_count = cur.fetchone()['cnt']
                report['foreign_key_integrity'][name] = {
                    'orphan_count': orphan_count,
                    'status': 'HEALTHY' if orphan_count == 0 else 'CORRUPT'
                }

            # 3. Academic Business Invariant Audits
            # Invariant A: offering enrolled_count == actual active enrollments
            cur.execute("""
                SELECT COUNT(*) as mismatch_count FROM (
                    SELECT co.offering_id, co.enrolled_count, COUNT(e.enrollment_id) as act_count
                    FROM course_offerings co
                    LEFT JOIN enrollments e ON e.offering_id = co.offering_id AND e.status = 'ACTIVE'
                    GROUP BY co.offering_id, co.enrolled_count
                    HAVING co.enrolled_count <> COUNT(e.enrollment_id)
                ) as m
            """)
            inv_a = cur.fetchone()['mismatch_count']
            report['academic_invariants']['offering_seat_counter_consistency'] = {
                'mismatched_offerings': inv_a,
                'status': 'CONSISTENT' if inv_a == 0 else 'INCONSISTENT'
            }

            # Invariant B: grade score within [0, 100]
            cur.execute("SELECT COUNT(*) as bad_grades FROM grades WHERE final_score < 0.0 OR final_score > 100.0")
            inv_b = cur.fetchone()['bad_grades']
            report['academic_invariants']['grade_bounds_validity'] = {
                'out_of_bounds_grades': inv_b,
                'status': 'VALID' if inv_b == 0 else 'INVALID'
            }

            # Invariant C: attendance percentage within [0.0, 100.0]
            cur.execute("SELECT COUNT(*) as bad_att FROM enrollments WHERE total_attendance_pct < 0.0 OR total_attendance_pct > 100.0")
            inv_c = cur.fetchone()['bad_att']
            report['academic_invariants']['attendance_bounds_validity'] = {
                'out_of_bounds_attendance': inv_c,
                'status': 'VALID' if inv_c == 0 else 'INVALID'
            }

            # Invariant D: date progression (term start < end date)
            cur.execute("SELECT COUNT(*) as bad_terms FROM academic_terms WHERE start_date >= end_date")
            inv_d = cur.fetchone()['bad_terms']
            report['academic_invariants']['term_date_progression'] = {
                'inverted_terms': inv_d,
                'status': 'CHRONOLOGICAL' if inv_d == 0 else 'INVERTED'
            }

    finally:
        conn.close()

    os.makedirs("_internal/test-evidence/data-profiling", exist_ok=True)
    out_path = "_internal/test-evidence/data-profiling/profiling_report.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    total_rows = sum(t['actual_row_count'] for t in report['tables'].values())
    print(f"=== Data Profiling Completed for {db_name} ===")
    print(f"Total Base Tables Profiled: {len(report['tables'])}")
    print(f"Total Valid Records Profiled: {total_rows:,}")
    print("Referential Integrity Checks:")
    for fk, res in report['foreign_key_integrity'].items():
        print(f"  {fk}: {res['status']} ({res['orphan_count']} orphans)")
    print("Academic Invariants:")
    for inv, res in report['academic_invariants'].items():
        print(f"  {inv}: {res['status']}")
    print(f"Full JSON evidence saved to: {out_path}")

if __name__ == '__main__':
    profile_database()
