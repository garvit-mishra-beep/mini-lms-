"""MiniLMS Migration Rollback Runner
Reverts schema versions cleanly and updates the schema_versions table.
"""
import os
import sys
import pymysql
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'minilms_db'),
        charset='utf8mb4',
        autocommit=False
    )

def rollback_v007(conn):
    print("[*] Rolling back v007 (Quiz Questions and Options)...")
    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cur.execute("DROP TABLE IF EXISTS quiz_options;")
        cur.execute("DROP TABLE IF EXISTS quiz_questions;")
        cur.execute("DELETE FROM schema_versions WHERE version_no = 7;")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
    conn.commit()
    print("[OK] v007 rolled back successfully.")

def rollback_v006(conn):
    print("[*] Rolling back v006 (sp_enroll upgrade)...")
    with conn.cursor() as cur:
        cur.execute("DROP PROCEDURE IF EXISTS sp_enroll;")
        # Restore basic baseline sp_enroll
        cur.execute("""
        CREATE PROCEDURE sp_enroll(IN p_student INT, IN p_course INT)
        BEGIN
            START TRANSACTION;
            INSERT INTO enrollments(student_id, course_id, status)
            VALUES(p_student, p_course, 'ACTIVE');
            INSERT INTO completions(enrollment_id, completion_status)
            VALUES(LAST_INSERT_ID(), 'IN_PROGRESS');
            COMMIT;
        END;
        """)
        cur.execute("DELETE FROM schema_versions WHERE version_no = 6;")
    conn.commit()
    print("[OK] v006 rolled back successfully.")

def rollback_v010(conn):
    print("[*] Rolling back v010 (Views & Stored Programs)...")
    with conn.cursor() as cur:
        cur.execute("DROP VIEW IF EXISTS `v_faculty_workload`;")
        cur.execute("DROP VIEW IF EXISTS `v_department_performance`;")
        cur.execute("DROP VIEW IF EXISTS `v_course_offering_summary`;")
        cur.execute("DROP VIEW IF EXISTS `v_student_academic_summary`;")
        cur.execute("DROP VIEW IF EXISTS `faculty_allocations`;")
        cur.execute("DROP VIEW IF EXISTS `faculty`;")
        cur.execute("DROP PROCEDURE IF EXISTS `sp_calculate_student_gpa`;")
        cur.execute("DROP PROCEDURE IF EXISTS `sp_grade_assignment_submission`;")
        cur.execute("DROP PROCEDURE IF EXISTS `sp_record_attendance_session`;")
        cur.execute("DROP PROCEDURE IF EXISTS `sp_enroll_student_in_offering`;")
        cur.execute("DELETE FROM schema_versions WHERE version_no = 10;")
    conn.commit()
    print("[OK] v010 rolled back successfully.")

def rollback_v009(conn):
    print("[*] Rolling back v009 (Integrity Constraints & Triggers)...")
    with conn.cursor() as cur:
        cur.execute("DROP TRIGGER IF EXISTS `trg_audit_logs_no_delete`;")
        cur.execute("DROP TRIGGER IF EXISTS `trg_audit_logs_immutable`;")
        cur.execute("DROP TRIGGER IF EXISTS `trg_update_attendance_pct_after_update`;")
        cur.execute("DROP TRIGGER IF EXISTS `trg_update_attendance_pct_after_insert`;")
        cur.execute("DROP TRIGGER IF EXISTS `trg_enrollment_seat_decrement`;")
        cur.execute("DROP TRIGGER IF EXISTS `trg_enrollment_seat_increment`;")
        cur.execute("DROP TRIGGER IF EXISTS `trg_submission_offering_validate`;")
        cur.execute("DROP TRIGGER IF EXISTS `trg_att_offering_validate`;")
        cur.execute("DROP TRIGGER IF EXISTS `trg_grade_bounds_check`;")
        # Drop CHECK constraints
        for tbl, chk in [
            ('students', 'chk_student_cgpa'), ('students', 'chk_student_semester'),
            ('courses', 'chk_course_credits'), ('course_offerings', 'chk_offering_capacity'),
            ('course_offerings', 'chk_offering_enrolled'), ('academic_terms', 'chk_term_dates'),
            ('assignments', 'chk_assignment_marks'), ('assignments', 'chk_assignment_weightage'),
            ('grades', 'chk_grade_final_score'), ('enrollments', 'chk_enrollment_att_pct')
        ]:
            try:
                cur.execute(f"ALTER TABLE `{tbl}` DROP CHECK `{chk}`;")
            except Exception:
                pass
        cur.execute("DELETE FROM schema_versions WHERE version_no = 9;")
    conn.commit()
    print("[OK] v009 rolled back successfully.")

def rollback_v008(conn):
    print("[*] Rolling back v008 (Core Academic Enhancements)...")
    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cur.execute("DROP TABLE IF EXISTS `announcements`;")
        cur.execute("DROP TABLE IF EXISTS `submissions`;")
        cur.execute("DROP TABLE IF EXISTS `assignments`;")
        cur.execute("DROP TABLE IF EXISTS `attendance_records`;")
        cur.execute("DROP TABLE IF EXISTS `attendance_sessions`;")
        cur.execute("DROP TABLE IF EXISTS `course_offerings`;")
        cur.execute("DROP TABLE IF EXISTS `academic_terms`;")
        cur.execute("DROP TABLE IF EXISTS `departments`;")
        cur.execute("DELETE FROM schema_versions WHERE version_no = 8;")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
    conn.commit()
    print("[OK] v008 rolled back successfully.")

ROLLBACK_HANDLERS = {
    10: rollback_v010,
    9: rollback_v009,
    8: rollback_v008,
    7: rollback_v007,
    6: rollback_v006
}

def rollback_latest():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT version_no FROM schema_versions ORDER BY version_no DESC LIMIT 1;")
            row = cur.fetchone()
            if not row:
                print("[!] No schema migrations recorded in schema_versions.")
                return
            latest_version = row[0]

        handler = ROLLBACK_HANDLERS.get(latest_version)
        if not handler:
            print(f"[!] No rollback handler defined for schema version {latest_version}.")
            return

        print(f"[?] Rolling back schema version {latest_version}...")
        handler(conn)
    finally:
        conn.close()

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if target:
        try:
            t_num = int(target.lstrip('v'))
            conn = get_connection()
            if t_num in ROLLBACK_HANDLERS:
                ROLLBACK_HANDLERS[t_num](conn)
            else:
                print(f"[!] No rollback handler for version {t_num}")
            conn.close()
        except ValueError:
            print(f"[!] Invalid version format: {target}. Use e.g. 7 or v007")
    else:
        rollback_latest()
