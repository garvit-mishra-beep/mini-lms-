"""TX-03: Assignment Grading and Publication Transaction Demonstration.
Demonstrates:
  1. Atomic grading transaction with row-level lock (SELECT ... FOR UPDATE on submissions)
  2. Range validation: ensuring marks_obtained <= max_marks
  3. Status progression from SUBMITTED to EVALUATED
  4. Updating course-level grades table with letter grade derivation
  5. Audit log and grade change history recording
"""
import sys
import pymysql
from app.db import get_connection

def demonstrate_tx_grading(submission_id=1, marks=88.50, feedback="Excellent SQL query optimization and indexing explanation.", grader_user_id=2):
    print("=== TX-03: Assignment Grading & Publication Transaction Demonstration ===")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Inspect submission before grading
            cur.execute("""
                SELECT s.submission_id, s.assignment_id, a.title, a.max_marks, s.status, s.marks_obtained
                FROM submissions s
                JOIN assignments a ON s.assignment_id = a.assignment_id
                WHERE s.submission_id = %s
            """, (submission_id,))
            sub = cur.fetchone()
            if not sub:
                print(f"[ERROR] Submission {submission_id} not found.")
                return
            print(f"[PRE-CHECK] Submission {submission_id} ('{sub['title']}'): Max Marks={sub['max_marks']}, Status={sub['status']}, Prior Marks={sub['marks_obtained']}")

            # 2. Call sp_grade_assignment_submission
            print(f"[TRANSACTION] Calling sp_grade_assignment_submission(sub_id={submission_id}, marks={marks})...")
            cur.execute("CALL sp_grade_assignment_submission(%s, %s, %s, %s, @out_status_msg)", 
                        (submission_id, marks, feedback, grader_user_id))
            cur.execute("SELECT @out_status_msg AS status_msg")
            msg = cur.fetchone()['status_msg']
            print(f"[RESULT] Stored Procedure Message: {msg}")

            # 3. Verify post-condition
            cur.execute("SELECT submission_id, status, marks_obtained, feedback, graded_at FROM submissions WHERE submission_id = %s", (submission_id,))
            post_sub = cur.fetchone()
            print(f"[POST-CHECK] Evaluated Submission {submission_id}: Status={post_sub['status']}, Marks={post_sub['marks_obtained']}, Feedback='{post_sub['feedback']}'")
            return msg
    finally:
        conn.close()

if __name__ == '__main__':
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT submission_id FROM submissions LIMIT 1")
            r = cur.fetchone()
            sub_id = r['submission_id'] if r else 2
    finally:
        conn.close()
    if len(sys.argv) > 1:
        sub_id = int(sys.argv[1])
    marks = float(sys.argv[2]) if len(sys.argv) > 2 else 92.00
    demonstrate_tx_grading(sub_id, marks)
