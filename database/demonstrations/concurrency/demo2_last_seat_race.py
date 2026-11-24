"""Concurrency Demonstration 2: Last Available Seat Race Condition.
Scenario:
  A course offering has capacity = 10, and enrolled_count = 9 (exactly 1 seat remaining).
  Two distinct students attempt to enroll simultaneously.
Mechanism:
  sp_enroll_student_in_offering executes `SELECT enrolled_count, max_capacity FROM course_offerings ... FOR UPDATE`.
  This acquires an exclusive row lock on the offering, serializing the check and seat increment.
  Result: Exactly one student gets the seat; the second receives 'ERROR: Course offering section capacity exceeded.'
"""
import threading
import pymysql
from app.db import get_connection

def attempt_seat_grab(thread_name, student_id, offering_id, results):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("CALL sp_enroll_student_in_offering(%s, %s, @out_enrollment_id, @out_status_msg)", (student_id, offering_id))
            cur.execute("SELECT @out_enrollment_id AS enrollment_id, @out_status_msg AS status_msg")
            res = cur.fetchone()
            print(f"[{thread_name} (Student {student_id})] Result: ID={res['enrollment_id']}, Msg='{res['status_msg']}'")
            results.append((thread_name, student_id, res['enrollment_id'], res['status_msg']))
    finally:
        conn.close()

def run_last_seat_race():
    print("=== CONCURRENCY DEMO 2: LAST AVAILABLE SEAT RACE CONDITION ===")
    conn = get_connection()
    test_offering_id = 1 # Course 3 (PUBLISHED)
    student_a = 10
    student_b = 11

    try:
        with conn.cursor() as cur:
            # Clean up prior test enrollments
            cur.execute("""
                DELETE FROM completions 
                WHERE enrollment_id IN (
                    SELECT enrollment_id FROM enrollments 
                    WHERE student_id IN (%s, %s) AND offering_id = %s
                )
            """, (student_a, student_b, test_offering_id))
            cur.execute("DELETE FROM enrollments WHERE student_id IN (%s, %s) AND offering_id = %s", (student_a, student_b, test_offering_id))
            # Set max_capacity = 10 and enrolled_count = 9 (satisfies chk_offering_capacity >= 5 and leaves exactly 1 seat)
            cur.execute("UPDATE course_offerings SET max_capacity = 10, enrolled_count = 9 WHERE offering_id = %s", (test_offering_id,))
            conn.commit()
            print(f"[SETUP] Offering {test_offering_id}: Enrolled=9, Max Capacity=10 (Exactly 1 seat available)")
    finally:
        conn.close()

    results = []
    t1 = threading.Thread(target=attempt_seat_grab, args=("Thread-A", student_a, test_offering_id, results))
    t2 = threading.Thread(target=attempt_seat_grab, args=("Thread-B", student_b, test_offering_id, results))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("\n--- Summary of Last Seat Race ---")
    granted = [r for r in results if r[2] > 0 and 'SUCCESS' in r[3]]
    rejected = [r for r in results if r[2] == 0 or 'capacity' in r[3].lower()]

    print(f"Granted Enrollments: {len(granted)} (Expected: 1)")
    print(f"Rejected Enrollments: {len(rejected)} (Expected: 1)")
    assert len(granted) == 1 and len(rejected) == 1, "Last seat race check failed!"
    print(">>> DEMO 2 PASSED: Row-level lock serialized seat allocation, preventing over-enrollment. <<<\n")

if __name__ == '__main__':
    run_last_seat_race()
