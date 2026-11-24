"""TX-02: Bulk Attendance Recording Transaction Demonstration.
Demonstrates:
  1. Atomic bulk attendance insertion across an entire course offering roster
  2. Roster validation (verifying all student enrollments belong to the offering)
  3. Dynamic attendance percentage recalculation triggered per student
  4. All-or-nothing rollback if any student ID or attendance state is invalid
"""
import sys
from datetime import date
import pymysql
from app.db import get_connection

def demonstrate_tx_bulk_attendance(offering_id=1, teacher_id=1, topic="Lecture: Transaction Processing & ACID"):
    print("=== TX-02: Bulk Attendance Recording Transaction Demonstration ===")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Fetch enrolled active students for this offering
            cur.execute("""
                SELECT enrollment_id, student_id, total_attendance_pct 
                FROM enrollments 
                WHERE offering_id = %s AND status = 'ACTIVE'
            """, (offering_id,))
            roster = cur.fetchall()
            print(f"[ROSTER] Found {len(roster)} actively enrolled students in Offering {offering_id}.")

            if not roster:
                print("[WARN] No active students in offering to record attendance for.")
                return

            # 2. Begin explicit transaction
            conn.begin()
            try:
                # Insert master attendance session
                cur.execute("""
                    INSERT INTO attendance_sessions (offering_id, teacher_id, session_date, topic_covered)
                    VALUES (%s, %s, %s, %s)
                """, (offering_id, teacher_id, date.today(), topic))
                session_id = conn.insert_id()
                print(f"[TX STEP 1] Created attendance session ID: {session_id}")

                # Insert attendance records in batch for all students
                for idx, student in enumerate(roster):
                    att_status = 'PRESENT' if idx % 4 != 0 else 'ABSENT'
                    cur.execute("""
                        INSERT INTO attendance_records (session_id, enrollment_id, status, remarks)
                        VALUES (%s, %s, %s, %s)
                    """, (session_id, student['enrollment_id'], att_status, f"Automated batch record ({att_status})"))
                    print(f"  -> Recorded Enrollment {student['enrollment_id']} as {att_status}")

                # Commit transaction
                conn.commit()
                print(f"[TX COMMIT] Successfully committed batch attendance session {session_id}.")
            except Exception as e:
                conn.rollback()
                print(f"[TX ROLLBACK] Transaction failed and rolled back cleanly: {e}")
                raise

            # 3. Verify updated attendance percentages via trigger recalculation
            cur.execute("""
                SELECT e.enrollment_id, s.roll_no, e.total_attendance_pct
                FROM enrollments e
                JOIN students s ON e.student_id = s.student_id
                WHERE e.offering_id = %s
                LIMIT 5
            """, (offering_id,))
            updated_roster = cur.fetchall()
            print("[POST-VERIFY] Updated Student Attendance Percentages (recalculated by triggers):")
            for ur in updated_roster:
                print(f"  Student Roll {ur['roll_no']}: Attendance = {ur['total_attendance_pct']}%")

    finally:
        conn.close()

if __name__ == '__main__':
    demonstrate_tx_bulk_attendance()
