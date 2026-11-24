"""TCL (Transaction Control Language) Demonstration.
Demonstrates:
  1. START TRANSACTION / BEGIN
  2. COMMIT
  3. ROLLBACK
  4. SAVEPOINT <name>
  5. ROLLBACK TO SAVEPOINT <name>
  6. RELEASE SAVEPOINT <name>
"""
import pymysql
from app.db import get_connection

def demonstrate_tcl():
    print("=== TRANSACTION CONTROL LANGUAGE (TCL) DEMONSTRATION ===")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Step 1: START TRANSACTION
            print("[TCL 1] Starting explicit transaction...")
            conn.begin()

            cur.execute("""
                INSERT INTO announcements (offering_id, author_id, title, content)
                VALUES (1, 1, 'TCL Step 1: Baseline Announcement', 'Created before savepoint')
            """)
            id1 = conn.insert_id()
            print(f"  Inserted record 1 (ID: {id1})")

            # Step 2: SAVEPOINT sp_alpha
            print("[TCL 2] Creating SAVEPOINT `sp_alpha`...")
            cur.execute("SAVEPOINT sp_alpha")

            # Step 3: Insert second record after savepoint
            cur.execute("""
                INSERT INTO announcements (offering_id, author_id, title, content)
                VALUES (1, 1, 'TCL Step 2: Sub-operation Announcement', 'Created after savepoint')
            """)
            id2 = conn.insert_id()
            print(f"  Inserted record 2 (ID: {id2}) after SAVEPOINT")

            # Step 4: ROLLBACK TO SAVEPOINT sp_alpha
            print("[TCL 3] Executing ROLLBACK TO SAVEPOINT `sp_alpha` (reverting record 2)...")
            cur.execute("ROLLBACK TO SAVEPOINT sp_alpha")

            # Verify record 2 is gone, but record 1 remains in transaction
            cur.execute("SELECT announcement_id FROM announcements WHERE announcement_id = %s", (id2,))
            res2 = cur.fetchone()
            cur.execute("SELECT announcement_id FROM announcements WHERE announcement_id = %s", (id1,))
            res1 = cur.fetchone()
            print(f"  Check Record 2 (should be None): {res2}")
            print(f"  Check Record 1 (should exist in tx): {res1}")
            assert res2 is None, "ROLLBACK TO SAVEPOINT failed to discard record 2!"
            assert res1 is not None, "ROLLBACK TO SAVEPOINT erroneously discarded record 1!"

            # Step 5: RELEASE SAVEPOINT
            print("[TCL 4] Releasing savepoint `sp_alpha`...")
            # Note: in MySQL, rolling back to a savepoint keeps it active until released or committed
            cur.execute("RELEASE SAVEPOINT sp_alpha")

            # Step 6: COMMIT the remaining changes
            print("[TCL 5] Executing COMMIT to persist record 1...")
            conn.commit()

            # Verify final state
            cur.execute("SELECT announcement_id, title FROM announcements WHERE announcement_id = %s", (id1,))
            final_res = cur.fetchone()
            print(f"[TCL POST-COMMIT] Successfully committed: {final_res}")

            # Cleanup
            cur.execute("DELETE FROM announcements WHERE announcement_id = %s", (id1,))
            conn.commit()
            print("[TCL CLEANUP] Test record removed.")
            print(">>> TCL COMMANDS DEMONSTRATED SUCCESSFULLY <<<")
    finally:
        conn.close()

if __name__ == '__main__':
    demonstrate_tcl()
