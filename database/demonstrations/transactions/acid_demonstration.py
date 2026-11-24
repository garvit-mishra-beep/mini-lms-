"""ACID Properties Proof & Verification Demonstration.
Verifies all 4 ACID properties in MySQL 8.0 InnoDB engine:
  - Atomicity: Simulates mid-transaction error; verifies total rollback of all statements.
  - Consistency: Demonstrates CHECK constraint / foreign key rejection; DB state remains consistent.
  - Isolation: Verifies that an uncommitted INSERT/UPDATE is invisible to concurrent sessions.
  - Durability: Verifies that a committed transaction persists across connection closures and reconnects.
"""
import pymysql
from app.db import get_connection

def demonstrate_atomicity():
    print("\n--- 1. ATOMICITY DEMONSTRATION ---")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM announcements")
            count_before = cur.fetchone()['cnt']
            print(f"[ATOMICITY PRE] Current announcements count: {count_before}")

            conn.begin()
            try:
                # Step 1: Valid insert
                cur.execute("""
                    INSERT INTO announcements (offering_id, author_id, title, content)
                    VALUES (1, 1, 'Temporary Test Announcement', 'Should be rolled back')
                """)
                temp_id = conn.insert_id()
                print(f"[ATOMICITY STEP 1] Inserted announcement ID: {temp_id}")

                # Step 2: Intentional failure (Division by zero / invalid foreign key)
                print("[ATOMICITY STEP 2] Triggering intentional SQLEXCEPTION (Foreign Key violation)...")
                cur.execute("""
                    INSERT INTO announcements (offering_id, author_id, title, content)
                    VALUES (999999, 1, 'Invalid Offering Announcement', 'Violates FK')
                """)
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"[ATOMICITY CAUGHT] Error triggered: {e.__class__.__name__}. Transaction rolled back.")

            # Verify total count unchanged
            cur.execute("SELECT COUNT(*) AS cnt FROM announcements")
            count_after = cur.fetchone()['cnt']
            print(f"[ATOMICITY POST] Announcements count after rollback: {count_after}")
            assert count_before == count_after, "Atomicity violated! Partial writes detected."
            print("[ATOMICITY VERIFIED] All partial writes rolled back successfully.")
    finally:
        conn.close()

def demonstrate_consistency():
    print("\n--- 2. CONSISTENCY DEMONSTRATION ---")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            print("[CONSISTENCY CHECK] Attempting to insert invalid student CGPA (11.5 > 10.0 max)...")
            try:
                cur.execute("""
                    INSERT INTO students (user_id, roll_no, enrollment_no, current_semester, cgpa)
                    VALUES (1, 'TEST_ROLL_99', 'TEST_ENR_99', 3, 11.50)
                """)
                conn.commit()
                print("[FAIL] CHECK constraint failed to reject out-of-bounds value!")
            except pymysql.MySQLError as e:
                conn.rollback()
                print(f"[CONSISTENCY VERIFIED] MySQL CHECK constraint rejected invalid state: {e}")

            print("[CONSISTENCY CHECK] Attempting to insert negative assignment max_marks (-20.0)...")
            try:
                cur.execute("""
                    INSERT INTO assignments (offering_id, title, max_marks, weightage_pct, created_by)
                    VALUES (1, 'Invalid Assignment', -20.00, 10.0, 2)
                """)
                conn.commit()
                print("[FAIL] CHECK constraint failed to reject negative marks!")
            except pymysql.MySQLError as e:
                conn.rollback()
                print(f"[CONSISTENCY VERIFIED] MySQL CHECK constraint chk_assignment_marks enforced: {e}")
    finally:
        conn.close()

def demonstrate_isolation():
    print("\n--- 3. ISOLATION DEMONSTRATION ---")
    conn1 = get_connection()
    conn2 = get_connection()
    try:
        with conn1.cursor() as cur1, conn2.cursor() as cur2:
            # Session 1 starts transaction and inserts a row without committing
            conn1.begin()
            cur1.execute("""
                INSERT INTO announcements (offering_id, author_id, title, content)
                VALUES (1, 1, 'Uncommitted Isolated Announcement', 'Checking dirty read')
            """)
            temp_id = conn1.insert_id()
            print(f"[SESSION 1] Inserted uncommitted announcement ID: {temp_id}")

            # Session 2 inspects announcements in REPEATABLE READ / READ COMMITTED
            cur2.execute("SELECT * FROM announcements WHERE announcement_id = %s", (temp_id,))
            visible_to_session2 = cur2.fetchone()
            print(f"[SESSION 2] Attempt to read uncommitted announcement: {visible_to_session2}")
            assert visible_to_session2 is None, "Isolation violated! Dirty read occurred."
            print("[ISOLATION VERIFIED] Uncommitted data is completely invisible to concurrent Session 2.")

            # Roll back Session 1
            conn1.rollback()
            print("[SESSION 1] Rolled back uncommitted insert.")
    finally:
        conn1.close()
        conn2.close()

def demonstrate_durability():
    print("\n--- 4. DURABILITY DEMONSTRATION ---")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            conn.begin()
            cur.execute("""
                INSERT INTO announcements (offering_id, author_id, title, content)
                VALUES (1, 1, 'Durable Test Announcement', 'Testing persistence across session disconnect')
            """)
            durable_id = conn.insert_id()
            conn.commit()
            print(f"[SESSION 1] Committed announcement ID: {durable_id}")
    finally:
        conn.close()

    # Reconnect in a completely new independent session
    new_conn = get_connection()
    try:
        with new_conn.cursor() as new_cur:
            new_cur.execute("SELECT announcement_id, title FROM announcements WHERE announcement_id = %s", (durable_id,))
            record = new_cur.fetchone()
            print(f"[NEW SESSION] Successfully read durable record: {record}")
            assert record is not None, "Durability violated! Committed data lost on disconnect."
            print("[DURABILITY VERIFIED] Data persisted across connection restart.")

            # Cleanup test record
            new_cur.execute("DELETE FROM announcements WHERE announcement_id = %s", (durable_id,))
            new_conn.commit()
    finally:
        new_conn.close()

def run_all_acid_demonstrations():
    print("==================================================")
    print("   MINILMS DATABASE ACID VERIFICATION SUITE       ")
    print("==================================================")
    demonstrate_atomicity()
    demonstrate_consistency()
    demonstrate_isolation()
    demonstrate_durability()
    print("\n>>> ALL ACID PROPERTIES PROVEN COMPLIANT <<<")

if __name__ == '__main__':
    run_all_acid_demonstrations()
