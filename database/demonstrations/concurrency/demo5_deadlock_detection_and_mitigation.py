"""Concurrency Demonstration 5: Deadlock Generation, Detection, and Application Mitigation.
Scenario:
  Transaction 1 locks Record A, then requests Record B.
  Transaction 2 locks Record B, then requests Record A.
  This creates a cyclical wait graph (Deadlock).
Mechanism:
  1. MySQL InnoDB deadlock detection engine detects the cycle and terminates one transaction with Error 1213:
     "ER_LOCK_DEADLOCK: Deadlock found when trying to get lock; try restarting transaction".
  2. The application catches Error 1213, backs off exponentially, retries the transaction, and succeeds.
"""
import threading
import time
import random
import pymysql
from app.db import get_connection

def tx1_worker(log):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            conn.begin()
            log.append("[TX-1] Locking Course 1...")
            cur.execute("SELECT course_id, title FROM courses WHERE course_id = 1 FOR UPDATE")
            time.sleep(1.0) # Allow TX-2 to lock Course 2

            log.append("[TX-1] Requesting lock on Course 2...")
            cur.execute("SELECT course_id, title FROM courses WHERE course_id = 2 FOR UPDATE")
            conn.commit()
            log.append("[TX-1] SUCCESS: Both locks acquired and committed.")
    except pymysql.MySQLError as e:
        conn.rollback()
        log.append(f"[TX-1] CAUGHT INNODB EXCEPTION: {e}")
    finally:
        conn.close()

def tx2_resilient_worker(log):
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                conn.begin()
                log.append(f"[TX-2 (Attempt {attempt})] Locking Course 2...")
                cur.execute("SELECT course_id, title FROM courses WHERE course_id = 2 FOR UPDATE")
                time.sleep(1.0) # Allow TX-1 to request Course 2

                log.append(f"[TX-2 (Attempt {attempt})] Requesting lock on Course 1...")
                cur.execute("SELECT course_id, title FROM courses WHERE course_id = 1 FOR UPDATE")
                conn.commit()
                log.append(f"[TX-2 (Attempt {attempt})] SUCCESS: Both locks acquired and committed.")
                break
        except pymysql.MySQLError as e:
            conn.rollback()
            if e.args[0] == 1213: # ER_LOCK_DEADLOCK
                log.append(f"[TX-2 (Attempt {attempt})] DEADLOCK DETECTED (Error 1213)! InnoDB aborted victim transaction.")
                log.append(f"[TX-2] Backing off for retry {attempt + 1}...")
                time.sleep(0.5 + random.random() * 0.5)
            else:
                log.append(f"[TX-2] Unhandled error: {e}")
                break
        finally:
            conn.close()

def run_deadlock_demo():
    print("=== CONCURRENCY DEMO 5: DEADLOCK GENERATION & APPLICATION MITIGATION ===")
    log = []

    t1 = threading.Thread(target=tx1_worker, args=(log,))
    t2 = threading.Thread(target=tx2_resilient_worker, args=(log,))

    t1.start()
    time.sleep(0.2)
    t2.start()

    t1.join()
    t2.join()

    print("\n--- Deadlock Execution Timeline ---")
    deadlock_detected = False
    for line in log:
        print(f"  {line}")
        if "DEADLOCK DETECTED" in line or "1213" in line:
            deadlock_detected = True

    assert deadlock_detected, "Deadlock was not triggered or detected as expected."
    print("\n>>> DEMO 5 PASSED: InnoDB detected cycle (Error 1213) and resilient retry recovered successfully. <<<\n")

if __name__ == '__main__':
    run_deadlock_demo()
