"""Concurrency Demonstration 1: Duplicate Enrollment Race Condition.
Scenario:
  Two concurrent threads attempt to enroll the exact same student into the same
  course offering at the exact same millisecond.
Mechanism:
  MySQL stored procedure sp_enroll_student_in_offering executes within an atomic transaction.
  Unique index on enrollments (student_id, active_course_id) and SELECT FOR UPDATE
  guarantees that exactly one thread succeeds and the other receives a conflict rejection.
"""
import threading
import time
import pymysql
from app.db import get_connection

def attempt_enroll(thread_name, student_id, offering_id, results):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("CALL sp_enroll_student_in_offering(%s, %s, @out_enrollment_id, @out_status_msg)", (student_id, offering_id))
            cur.execute("SELECT @out_enrollment_id AS enrollment_id, @out_status_msg AS status_msg")
            res = cur.fetchone()
            print(f"[{thread_name}] Enrollment Result: ID={res['enrollment_id']}, Msg='{res['status_msg']}'")
            results.append((thread_name, res['enrollment_id'], res['status_msg']))
    except Exception as e:
        print(f"[{thread_name}] Exception caught: {e}")
        results.append((thread_name, 0, str(e)))
    finally:
        conn.close()

def run_duplicate_enrollment_race():
    print("=== CONCURRENCY DEMO 1: DUPLICATE ENROLLMENT RACE CONDITION ===")
    # Student 12 into offering 4 (if available) or create a fresh test scenario
    student_id = 12
    offering_id = 3
    results = []

    # Clean up prior test enrollment if any
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM completions 
                WHERE enrollment_id IN (
                    SELECT enrollment_id FROM enrollments 
                    WHERE student_id = %s AND offering_id = %s
                )
            """, (student_id, offering_id))
            cur.execute("DELETE FROM enrollments WHERE student_id = %s AND offering_id = %s", (student_id, offering_id))
            conn.commit()
    finally:
        conn.close()

    t1 = threading.Thread(target=attempt_enroll, args=("Thread-1", student_id, offering_id, results))
    t2 = threading.Thread(target=attempt_enroll, args=("Thread-2", student_id, offering_id, results))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("\n--- Summary of Concurrent Execution ---")
    successes = [r for r in results if r[1] > 0 and 'SUCCESS' in r[2]]
    conflicts = [r for r in results if r[1] == 0 or 'CONFLICT' in r[2] or 'Duplicate' in r[2]]

    print(f"Total Successful Enrollments: {len(successes)} (Expected: exactly 1)")
    print(f"Total Rejected Conflicts: {len(conflicts)} (Expected: exactly 1)")
    assert len(successes) == 1 and len(conflicts) == 1, "Race condition check failed!"
    print(">>> DEMO 1 PASSED: Duplicate enrollment race successfully prevented by relational lock & unique constraint. <<<\n")

if __name__ == '__main__':
    run_duplicate_enrollment_race()
