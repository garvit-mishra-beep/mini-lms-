"""TX-01: Student Course Enrollment Transaction Demonstration.
Demonstrates:
  1. Atomic execution with START TRANSACTION and COMMIT/ROLLBACK
  2. Row-level locking on course_offerings using SELECT ... FOR UPDATE
  3. Pre-condition checks: offering status, seat capacity, active enrollment conflict
  4. Enrollment creation and automatic seat count maintenance via triggers
  5. Audit log generation
"""
import sys
import pymysql
from app.db import get_connection

def demonstrate_tx_enrollment(student_id=1, offering_id=1):
    print("=== TX-01: Student Course Enrollment Demonstration ===")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Inspect offering before transaction
            cur.execute("SELECT offering_id, course_id, enrolled_count, max_capacity, status FROM course_offerings WHERE offering_id = %s", (offering_id,))
            offering = cur.fetchone()
            print(f"[PRE-CHECK] Offering ID {offering_id}: Capacity={offering['max_capacity']}, Enrolled={offering['enrolled_count']}, Status={offering['status']}")

            # 2. Call sp_enroll_student_in_offering
            print(f"[TRANSACTION] Calling sp_enroll_student_in_offering(student_id={student_id}, offering_id={offering_id})...")
            cur.execute("CALL sp_enroll_student_in_offering(%s, %s, @out_enrollment_id, @out_status_msg)", (student_id, offering_id))
            cur.execute("SELECT @out_enrollment_id AS enrollment_id, @out_status_msg AS status_msg")
            result = cur.fetchone()
            print(f"[RESULT] Enrollment ID: {result['enrollment_id']}, Message: {result['status_msg']}")

            # 3. Inspect post-condition
            cur.execute("SELECT offering_id, enrolled_count FROM course_offerings WHERE offering_id = %s", (offering_id,))
            post_offering = cur.fetchone()
            print(f"[POST-CHECK] Offering ID {offering_id}: New Enrolled Count = {post_offering['enrolled_count']}")
            return result
    finally:
        conn.close()

if __name__ == '__main__':
    # Test with student 1, offering 1 (or 2)
    s_id = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    o_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    demonstrate_tx_enrollment(s_id, o_id)
