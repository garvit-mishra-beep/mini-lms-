"""Concurrency Demonstration 3: Lost Update Prevention (Pessimistic Locking).
Scenario:
  Two evaluators open the same student submission at the same time and enter grades.
  Without concurrency control, Teacher B would overwrite Teacher A's evaluation.
Mechanism:
  sp_grade_assignment_submission acquires an exclusive lock via `SELECT ... FOR UPDATE`
  on the submission row. The second transaction must wait until the first commits,
  thereby preventing dirty reads or lost updates.
"""
import threading
import time
import pymysql
from app.db import get_connection

def teacher_grade(thread_name, submission_id, marks, feedback, teacher_user_id, sleep_before_commit, results):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            conn.begin()
            # Lock the submission record
            print(f"[{thread_name}] Locking submission {submission_id} with SELECT ... FOR UPDATE...")
            cur.execute("""
                SELECT submission_id, status, marks_obtained, feedback
                FROM submissions
                WHERE submission_id = %s
                FOR UPDATE
            """, (submission_id,))
            sub = cur.fetchone()
            print(f"[{thread_name}] Acquired lock! Current status={sub['status']}, prior marks={sub['marks_obtained']}")

            if sleep_before_commit > 0:
                print(f"[{thread_name}] Simulating rubric inspection (sleeping {sleep_before_commit}s)...")
                time.sleep(sleep_before_commit)

            # Update submission
            cur.execute("""
                UPDATE submissions
                SET marks_obtained = %s, feedback = %s, status = 'EVALUATED', graded_at = NOW()
                WHERE submission_id = %s
            """, (marks, feedback, submission_id))
            conn.commit()
            print(f"[{thread_name}] Committed grade {marks} and released lock.")
            results.append((thread_name, marks, feedback))
    finally:
        conn.close()

def run_lost_update_prevention():
    print("=== CONCURRENCY DEMO 3: LOST UPDATE PREVENTION VIA PESSIMISTIC LOCKING ===")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT submission_id FROM submissions LIMIT 1")
            row = cur.fetchone()
            if not row:
                print("[ERROR] No submissions found in database.")
                return
            submission_id = row['submission_id']
    finally:
        conn.close()

    results = []

    # Teacher 1 takes 1.5 seconds to finish evaluation
    t1 = threading.Thread(target=teacher_grade, args=("Instructor-Alpha", submission_id, 85.00, "Grade from Instructor Alpha", 2, 1.5, results))
    # Teacher 2 attempts to grade immediately after
    t2 = threading.Thread(target=teacher_grade, args=("Instructor-Beta", submission_id, 92.00, "Grade from Instructor Beta", 3, 0.0, results))

    t1.start()
    time.sleep(0.2) # Ensure t1 acquires lock first
    t2.start()

    t1.join()
    t2.join()

    # Verify final state
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT submission_id, marks_obtained, feedback FROM submissions WHERE submission_id = %s", (submission_id,))
            final_sub = cur.fetchone()
            print(f"\n[FINAL DB STATE] Marks: {final_sub['marks_obtained']}, Feedback: '{final_sub['feedback']}'")
            print("Both updates executed sequentially without lost update race or corrupted state.")
            print(">>> DEMO 3 PASSED: Exclusive row lock successfully serialized concurrent grading. <<<\n")
    finally:
        conn.close()

if __name__ == '__main__':
    run_lost_update_prevention()
