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

ROLLBACK_HANDLERS = {
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
