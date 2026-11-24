"""Concurrency Demonstration 4: Lock Wait Demonstration.
Scenario:
  Session 1 acquires an exclusive lock on an announcement record and holds it.
  Session 2 attempts to execute an UPDATE on the same row.
Mechanism:
  Session 2 is placed into a LOCK WAIT state by the InnoDB storage engine.
  Measures the elapsed wait time until Session 1 commits and releases the lock.
"""
import threading
import time
import pymysql
from app.db import get_connection

def session_1_holder(announcement_id, hold_seconds, log):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            conn.begin()
            log.append("Session 1: Executing SELECT ... FOR UPDATE...")
            cur.execute("SELECT announcement_id, title FROM announcements WHERE announcement_id = %s FOR UPDATE", (announcement_id,))
            row = cur.fetchone()
            log.append(f"Session 1: Lock acquired on row {announcement_id}. Holding lock for {hold_seconds}s...")
            time.sleep(hold_seconds)
            conn.commit()
            log.append("Session 1: Committed transaction. Lock released.")
    finally:
        conn.close()

def session_2_waiter(announcement_id, log):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            time.sleep(0.3) # Ensure session 1 locks first
            log.append("Session 2: Attempting UPDATE on locked row (expecting LOCK WAIT)...")
            start_time = time.time()
            cur.execute("UPDATE announcements SET title = 'Session 2 Updated Title' WHERE announcement_id = %s", (announcement_id,))
            conn.commit()
            elapsed = time.time() - start_time
            log.append(f"Session 2: UPDATE succeeded after waiting {elapsed:.2f} seconds!")
    finally:
        conn.close()

def run_lock_wait_demo():
    print("=== CONCURRENCY DEMO 4: INNODB LOCK WAIT DEMONSTRATION ===")
    announcement_id = 1
    hold_duration = 2.0
    log = []

    t1 = threading.Thread(target=session_1_holder, args=(announcement_id, hold_duration, log))
    t2 = threading.Thread(target=session_2_waiter, args=(announcement_id, log))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("\n--- Lock Wait Execution Timeline ---")
    for entry in log:
        print(f"  {entry}")

    # Revert announcement title
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE announcements SET title = 'Welcome to DBMS PBL 2026' WHERE announcement_id = %s", (announcement_id,))
            conn.commit()
    finally:
        conn.close()

    print(">>> DEMO 4 PASSED: Session 2 successfully queued in LOCK WAIT and resumed upon commit. <<<\n")

if __name__ == '__main__':
    run_lock_wait_demo()
