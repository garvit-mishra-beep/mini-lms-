"""MiniLMS Deterministic Development Data Seeder.
Seeds:
1. Academic Coordinator user account (coordinator@example.test / MiniLMS@2026).
2. Attendance sessions & records for Course Offerings.
3. Coursework assignments in assignments table.
4. Student coursework submissions in submissions table.
5. Campus & course-specific announcements in announcements table.
"""
import os
import pymysql
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

DEMO_PWD = os.getenv('DEMO_USER_PASSWORD', 'MiniLMS@2026')

def seed_dev_data():
    conn = pymysql.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'minilms_db'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )

    try:
        with conn.cursor() as cur:
            # 1. Academic Coordinator Account
            pwd_hash = generate_password_hash(DEMO_PWD)
            cur.execute("""
                INSERT INTO users (full_name, email, password_hash, role, status, department_id, phone)
                VALUES ('Dr S. K. Raman (Academic Coordinator)', 'coordinator@example.test', %s, 'COORDINATOR', 'ACTIVE', 1, '+91-9876543299')
                ON DUPLICATE KEY UPDATE 
                    full_name = VALUES(full_name),
                    password_hash = VALUES(password_hash),
                    role = 'COORDINATOR',
                    status = 'ACTIVE',
                    department_id = 1;
            """, (pwd_hash,))
            cur.execute("SELECT user_id FROM users WHERE email = 'coordinator@example.test';")
            coord_row = cur.fetchone()
            coord_user_id = coord_row['user_id']
            print(f"[+] Verified Academic Coordinator account: coordinator@example.test (user_id: {coord_user_id})")

            # 2. Identify Offering for DBMS101
            cur.execute("""
                SELECT co.offering_id, co.course_id, ci.teacher_id, t.user_id as teacher_user_id
                FROM course_offerings co
                JOIN course_instructors ci ON co.offering_id = ci.offering_id
                JOIN teachers t ON ci.teacher_id = t.teacher_id
                WHERE co.offering_id = 3
                LIMIT 1;
            """)
            offering = cur.fetchone()
            if not offering:
                # Fallback to first offering
                cur.execute("SELECT offering_id, course_id FROM course_offerings LIMIT 1;")
                offering = cur.fetchone()
                offering['teacher_id'] = 1
                offering['teacher_user_id'] = 2

            offering_id = offering['offering_id']
            teacher_id = offering['teacher_id']
            teacher_user_id = offering['teacher_user_id']
            print(f"[+] Using offering #{offering_id} with teacher #{teacher_id}")

            # 3. Attendance Sessions
            sessions_data = [
                ('2024-09-02', 'Introduction to Relational Algebra & Database Architectures'),
                ('2024-09-09', 'Entity-Relationship Modeling and Cardinality Ratios'),
                ('2024-09-16', 'Functional Dependencies and Normalization: 1NF through BCNF'),
                ('2024-09-23', 'Advanced SQL Joins, Subqueries and Aggregations')
            ]
            session_ids = []
            for s_date, topic in sessions_data:
                cur.execute("""
                    SELECT session_id FROM attendance_sessions 
                    WHERE offering_id = %s AND session_date = %s;
                """, (offering_id, s_date))
                existing_sess = cur.fetchone()
                if existing_sess:
                    session_ids.append(existing_sess['session_id'])
                else:
                    cur.execute("""
                        INSERT INTO attendance_sessions (offering_id, teacher_id, session_date, topic_covered)
                        VALUES (%s, %s, %s, %s);
                    """, (offering_id, teacher_id, s_date, topic))
                    session_ids.append(cur.lastrowid)

            print(f"[+] Seeded {len(session_ids)} attendance sessions for offering #{offering_id}")

            # 4. Attendance Records for Active Enrollments in this Offering
            cur.execute("""
                SELECT enrollment_id, student_id FROM enrollments
                WHERE offering_id = %s AND status = 'ACTIVE';
            """, (offering_id,))
            active_enrollments = cur.fetchall()

            status_cycle = ['PRESENT', 'PRESENT', 'PRESENT', 'ABSENT', 'LATE', 'PRESENT']
            records_count = 0
            for sess_idx, sess_id in enumerate(session_ids):
                for enr_idx, enr in enumerate(active_enrollments):
                    st = status_cycle[(sess_idx + enr_idx) % len(status_cycle)]
                    cur.execute("""
                        INSERT INTO attendance_records (session_id, enrollment_id, status, remarks)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE status = VALUES(status);
                    """, (sess_id, enr['enrollment_id'], st, f"Lecture #{sess_idx + 1} roll call"))
                    records_count += 1

            print(f"[+] Seeded {records_count} attendance records across active enrollments.")

            # 5. Coursework Assignments
            assignments_data = [
                ('Lab Assignment 1: Schema Design & 3NF Normalization',
                 'Design a normalized relational schema for university examination management and submit DDL statements with test datasets.',
                 100.00, 15.00, '2024-10-15 23:59:59'),
                ('Lab Assignment 2: Complex Multi-Table SQL Queries',
                 'Implement 10 complex multi-table SQL queries demonstrating INNER, LEFT, self joins and window aggregations.',
                 50.00, 10.00, '2024-11-20 23:59:59')
            ]
            assign_ids = []
            for title, desc, max_m, weight, due in assignments_data:
                cur.execute("""
                    SELECT assignment_id FROM assignments 
                    WHERE offering_id = %s AND title = %s;
                """, (offering_id, title))
                existing_assign = cur.fetchone()
                if existing_assign:
                    assign_ids.append(existing_assign['assignment_id'])
                else:
                    cur.execute("""
                        INSERT INTO assignments (offering_id, title, description, max_marks, weightage_pct, due_date, created_by)
                        VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """, (offering_id, title, desc, max_m, weight, due, teacher_id))
                    assign_ids.append(cur.lastrowid)

            print(f"[+] Seeded {len(assign_ids)} assignments for offering #{offering_id}")

            # 6. Student Submissions & Grading
            if active_enrollments and assign_ids:
                # Student 1 submission - Evaluated
                enr1 = active_enrollments[0]['enrollment_id']
                cur.execute("""
                    INSERT INTO submissions (assignment_id, enrollment_id, submission_text, file_path, status, marks_obtained, feedback, graded_at)
                    VALUES (%s, %s, %s, %s, 'EVALUATED', 94.50, 'Outstanding work on Boyce-Codd normal form decomposition and integrity constraints.', NOW())
                    ON DUPLICATE KEY UPDATE 
                        submission_text = VALUES(submission_text),
                        status = 'EVALUATED',
                        marks_obtained = VALUES(marks_obtained),
                        feedback = VALUES(feedback),
                        graded_at = VALUES(graded_at);
                """, (assign_ids[0], enr1,
                      'Submitted complete 3NF schema diagram, DDL script with foreign key actions, and synthetic test tuples.',
                      '/uploads/submissions/lab1_student1_solution.pdf'))
                cur.execute("SELECT submission_id FROM submissions WHERE assignment_id = %s AND enrollment_id = %s;", (assign_ids[0], enr1))
                sub1_id = cur.fetchone()['submission_id']

                # Update Grade for enrollment 1 with submission_id and feedback
                cur.execute("""
                    UPDATE grades 
                    SET submission_id = %s,
                        feedback = 'Outstanding work on Boyce-Codd normal form decomposition and integrity constraints.'
                    WHERE enrollment_id = %s;
                """, (sub1_id, enr1))

                # Student 2 submission - Submitted
                if len(active_enrollments) > 1:
                    enr2 = active_enrollments[1]['enrollment_id']
                    cur.execute("""
                        INSERT INTO submissions (assignment_id, enrollment_id, submission_text, file_path, status)
                        VALUES (%s, %s, %s, %s, 'SUBMITTED')
                        ON DUPLICATE KEY UPDATE 
                            submission_text = VALUES(submission_text),
                            status = 'SUBMITTED';
                    """, (assign_ids[0], enr2,
                          'Draft normalization tables and DDL script ready for review.',
                          '/uploads/submissions/lab1_student2_solution.pdf'))

                print(f"[+] Seeded student coursework submissions and grades.")

            # 7. Announcements
            announcements_data = [
                ('Welcome to Fall 2024 Database Management Systems',
                 'Welcome all students to DBMS (CSL0311 / DBMS101). Please review the syllabus, lab schedules, and grading policy. Lectures are held in Block A - Turing Hall.',
                 offering_id, teacher_user_id),
                ('Academic Circular: Mid-Semester Evaluation & Minimum Attendance Requirement',
                 'All undergraduate students are reminded that a minimum of 75% attendance across all registered courses is strictly required to appear for semester end examinations.',
                 None, coord_user_id),
                ('Upcoming Technical Seminar: Next-Gen Relational Databases',
                 'The Department of Computer Science & Engineering is organizing a guest lecture on Modern Query Optimization and Distributed Relational Storage on November 18, 2024.',
                 None, coord_user_id)
            ]
            ann_count = 0
            for title, content, off_id, author_id in announcements_data:
                cur.execute("""
                    SELECT announcement_id FROM announcements
                    WHERE title = %s AND author_id = %s;
                """, (title, author_id))
                existing_ann = cur.fetchone()
                if not existing_ann:
                    cur.execute("""
                        INSERT INTO announcements (title, content, offering_id, author_id)
                        VALUES (%s, %s, %s, %s);
                    """, (title, content, off_id, author_id))
                    ann_count += 1

            print(f"[+] Seeded {ann_count} announcements (course and campus-wide).")

        conn.commit()
        print("[*] Successfully completed development data seeding.")
    except Exception as e:
        conn.rollback()
        print(f"[!] Error seeding development data: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    seed_dev_data()
