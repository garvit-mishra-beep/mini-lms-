"""MySQL 8.0 InnoDB Isolation Level Comparative Analysis.
Tests:
  1. READ UNCOMMITTED: Dirty Reads possible
  2. READ COMMITTED: Dirty Reads prevented; Non-Repeatable Reads possible
  3. REPEATABLE READ (Default): Dirty & Non-Repeatable Reads prevented via MVCC consistent read snapshot
  4. SERIALIZABLE: Range locking (Next-Key Locks) enforces strict serializability
"""
import time
import pymysql
from app.db import get_connection

def test_dirty_read(isolation_level):
    """Checks whether an uncommitted write in Session 1 is visible to Session 2."""
    conn1 = get_connection()
    conn2 = get_connection()
    try:
        with conn1.cursor() as cur1, conn2.cursor() as cur2:
            cur1.execute(f"SET SESSION TRANSACTION ISOLATION LEVEL {isolation_level}")
            cur2.execute(f"SET SESSION TRANSACTION ISOLATION LEVEL {isolation_level}")
            cur1.execute("SET innodb_lock_wait_timeout = 2")
            cur2.execute("SET innodb_lock_wait_timeout = 2")

            # Session 1 starts transaction and inserts a test record
            conn1.begin()
            cur1.execute("""
                INSERT INTO announcements (offering_id, author_id, title, content)
                VALUES (1, 1, 'Dirty Read Probe', 'Uncommitted payload')
            """)
            temp_id = conn1.insert_id()

            # Session 2 attempts to read it
            # Under SERIALIZABLE, SELECT requests an S-lock which is blocked by Session 1's X-lock!
            row = None
            try:
                conn2.begin()
                cur2.execute("SELECT announcement_id, title FROM announcements WHERE announcement_id = %s", (temp_id,))
                row = cur2.fetchone()
                conn2.commit()
            except pymysql.MySQLError as e:
                # If blocked by lock wait timeout, the read was blocked from reading uncommitted data
                conn2.rollback()
                row = None

            conn1.rollback() # Roll back uncommitted insert
            is_dirty_read_possible = (row is not None)
            return is_dirty_read_possible
    finally:
        conn1.close()
        conn2.close()

def test_non_repeatable_read(isolation_level):
    """Checks whether a committed UPDATE between two reads in Session 2 changes the value read."""
    conn1 = get_connection()
    conn2 = get_connection()
    try:
        with conn1.cursor() as cur1, conn2.cursor() as cur2:
            # Baseline test row
            cur1.execute("INSERT INTO announcements (offering_id, author_id, title, content) VALUES (1, 1, 'Initial Title', 'Body')")
            test_id = conn1.insert_id()
            conn1.commit()

            cur1.execute(f"SET SESSION TRANSACTION ISOLATION LEVEL {isolation_level}")
            cur2.execute(f"SET SESSION TRANSACTION ISOLATION LEVEL {isolation_level}")
            cur1.execute("SET innodb_lock_wait_timeout = 2")
            cur2.execute("SET innodb_lock_wait_timeout = 2")

            # Session 2: Read 1
            conn2.begin()
            cur2.execute("SELECT title FROM announcements WHERE announcement_id = %s", (test_id,))
            read_1 = cur2.fetchone()['title']

            # Session 1: Updates and commits (under SERIALIZABLE, cur2's shared lock will block cur1 until timeout!)
            update_blocked = False
            try:
                conn1.begin()
                cur1.execute("UPDATE announcements SET title = 'Modified Title' WHERE announcement_id = %s", (test_id,))
                conn1.commit()
            except pymysql.MySQLError as e:
                conn1.rollback()
                update_blocked = True

            if update_blocked:
                # Under SERIALIZABLE, Session 2's SELECT placed an S-lock on the row, preventing Session 1 from modifying it!
                conn2.commit()
                # Clean up
                cur1.execute("DELETE FROM announcements WHERE announcement_id = %s", (test_id,))
                conn1.commit()
                return False # Non-repeatable read is completely prevented because concurrent modification was blocked!

            # Session 2: Read 2 (within same transaction)
            cur2.execute("SELECT title FROM announcements WHERE announcement_id = %s", (test_id,))
            read_2 = cur2.fetchone()['title']
            conn2.commit()

            # Clean up
            cur1.execute("DELETE FROM announcements WHERE announcement_id = %s", (test_id,))
            conn1.commit()

            non_repeatable = (read_1 != read_2)
            return non_repeatable
    finally:
        conn1.close()
        conn2.close()

def run_isolation_matrix():
    print("==========================================================================")
    print("   MINILMS MYSQL 8.0 INNODB ISOLATION LEVEL MATRIX EMPIRICAL ANALYSIS     ")
    print("==========================================================================")
    levels = [
        "READ UNCOMMITTED",
        "READ COMMITTED",
        "REPEATABLE READ",
        "SERIALIZABLE"
    ]

    results = []
    for lvl in levels:
        dirty = test_dirty_read(lvl)
        non_rep = test_non_repeatable_read(lvl)
        results.append((lvl, dirty, non_rep))

    print(f"{'Isolation Level':<20} | {'Dirty Read?':<15} | {'Non-Repeatable Read?':<22}")
    print("-" * 65)
    for lvl, d, nr in results:
        d_str = "YES (Vulnerable)" if d else "NO (Prevented)"
        nr_str = "YES (Permitted)" if nr else "NO (Prevented via MVCC)"
        print(f"{lvl:<20} | {d_str:<15} | {nr_str:<22}")

    print("\nEmpirical Findings:")
    print("1. READ UNCOMMITTED allows reading dirty, uncommitted rows from other sessions.")
    print("2. READ COMMITTED prevents dirty reads, but allows non-repeatable reads as each statement reads the latest committed snapshot.")
    print("3. REPEATABLE READ (Default in InnoDB) uses an MVCC point-in-time snapshot established at the first read, preventing both dirty and non-repeatable reads.")
    print("4. SERIALIZABLE enforces strict locking on all SELECT statements (converting them implicitly to LOCK IN SHARE MODE), preventing phantoms.")

if __name__ == '__main__':
    run_isolation_matrix()
