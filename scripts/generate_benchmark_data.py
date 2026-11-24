"""Synthetic Benchmark Dataset Generator for MiniLMS Phase 11.
Generates 20,000+ referentially intact, pedagogically consistent academic records
specifically targeting minilms_benchmark_db for performance engineering.
"""
import sys
import os
import random
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db import get_connection

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
    "Shaurya", "Atharva", "Advik", "Pranav", "Advaith", "Aaryan", "Dhruv", "Kabir", "Ritvik", "Darsh",
    "Ananya", "Diya", "Gauri", "Isha", "Kavya", "Khushi", "Mira", "Myra", "Navya", "Pari",
    "Prisha", "Riya", "Saanvi", "Sara", "Siya", "Tanvi", "Veda", "Zara", "Aanya", "Aadhya"
]
LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Malhotra", "Bhatia", "Saxena", "Mehta", "Chopra", "Joshi", "Patel",
    "Reddy", "Nair", "Rao", "Iyer", "Kulkarni", "Deshmukh", "Chatterjee", "Banerjee", "Mukherjee", "Singh",
    "Kumar", "Yadav", "Mishra", "Pandey", "Trivedi", "Dubey", "Shukla", "Tiwari", "Chauhan", "Rathore"
]

DEPARTMENTS_DATA = [
    (1, 'CSE', 'Computer Science & Engineering', 'Block A, Turing Hall', 1),
    (2, 'IT', 'Information Technology', 'Block B, Shannon Hall', 1),
    (3, 'ECE', 'Electronics & Communication', 'Block C, Raman Hall', 1),
    (4, 'EE', 'Electrical Engineering', 'Block D, Faraday Hall', 1),
    (5, 'ME', 'Mechanical Engineering', 'Block E, Watt Hall', 1),
    (6, 'CE', 'Civil Engineering', 'Block F, Visvesvaraya Hall', 1),
    (7, 'MBA', 'Management Studies', 'Block G, Drucker Hall', 1),
    (8, 'MCA', 'Computer Applications', 'Block H, Knuth Hall', 1),
]

TERMS_DATA = [
    (1, 'FA24', 'Fall 2024', date(2024, 8, 1), date(2024, 12, 15), 0),
    (2, 'SP25', 'Spring 2025', date(2025, 1, 10), date(2025, 5, 25), 0),
    (3, 'FA25', 'Fall 2025', date(2025, 8, 1), date(2025, 12, 15), 0),
    (4, 'SP26', 'Spring 2026', date(2026, 1, 10), date(2026, 5, 25), 1),
    (5, 'FA26', 'Fall 2026', date(2026, 8, 1), date(2026, 12, 15), 0),
    (6, 'SP27', 'Spring 2027', date(2027, 1, 10), date(2027, 5, 25), 0),
]

def generate_benchmark_data(target_db="minilms_benchmark_db", seed=42):
    random.seed(seed)
    conn = get_connection()
    
    if "benchmark" not in target_db and "test" not in target_db:
        raise ValueError(f"Safety Guard Activated: target_db must contain 'benchmark' or 'test'. Got: {target_db}")

    print(f"=== Starting Synthetic Benchmark Data Generation ===")
    print(f"Target Database: {target_db}")
    print(f"Random Seed: {seed}")
    
    counts = {}
    try:
        with conn.cursor() as cur:
            cur.execute(f"USE `{target_db}`")
            cur.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            tables = [
                'academic_risks', 'audit_logs', 'announcements', 'certificates', 'completions',
                'attempt_answers', 'attempts', 'quiz_options', 'quiz_questions', 'quizzes',
                'grades', 'grade_change_history', 'submissions', 'assignments',
                'attendance_records', 'attendance_sessions', 'lesson_progress', 'lesson_prerequisites',
                'lessons', 'modules', 'enrollments', 'course_instructors', 'course_offerings',
                'courses', 'academic_terms', 'departments', 'teachers', 'students', 'users'
            ]
            for t in tables:
                cur.execute(f"TRUNCATE TABLE `{t}`")
            print("Cleared existing benchmark tables.")

            # 1. Departments (8)
            print("1. Inserting Departments (8)...")
            cur.executemany("""
                INSERT INTO departments (department_id, department_code, department_name, building, is_active)
                VALUES (%s, %s, %s, %s, %s)
            """, DEPARTMENTS_DATA)
            counts['departments'] = len(DEPARTMENTS_DATA)

            # 2. Academic Terms (6)
            print("2. Inserting Academic Terms (6)...")
            cur.executemany("""
                INSERT INTO academic_terms (term_id, term_code, term_name, start_date, end_date, is_current)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, TERMS_DATA)
            counts['academic_terms'] = len(TERMS_DATA)

            # 3. Users (650: 15 Admin, 15 Coord, 120 Teacher, 500 Student)
            print("3. Generating 650 User Accounts...")
            user_records = []
            uid = 1
            # 15 Admins
            for i in range(15):
                fn, ln = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
                dep = (i % 8) + 1
                user_records.append((uid, f"{fn} {ln}", f"admin_{i+1}@itm.test", "pbkdf2:sha256:600000$dummy$hash", "ADMIN", "ACTIVE", dep, f"98765{uid:05d}"))
                uid += 1
            # 15 Coordinators
            for i in range(15):
                fn, ln = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
                dep = (i % 8) + 1
                user_records.append((uid, f"{fn} {ln}", f"coord_{i+1}@itm.test", "pbkdf2:sha256:600000$dummy$hash", "COORDINATOR", "ACTIVE", dep, f"98765{uid:05d}"))
                uid += 1
            # 120 Teachers
            for i in range(120):
                fn, ln = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
                dep = (i % 8) + 1
                user_records.append((uid, f"Dr. {fn} {ln}", f"prof_{i+1}@itm.test", "pbkdf2:sha256:600000$dummy$hash", "TEACHER", "ACTIVE", dep, f"98765{uid:05d}"))
                uid += 1
            # 500 Students
            for i in range(500):
                fn, ln = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
                dep = (i % 8) + 1
                user_records.append((uid, f"{fn} {ln}", f"student_{i+1}@itm.test", "pbkdf2:sha256:600000$dummy$hash", "STUDENT", "ACTIVE", dep, f"98765{uid:05d}"))
                uid += 1

            cur.executemany("""
                INSERT INTO users (user_id, full_name, email, password_hash, role, status, department_id, phone)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, user_records)
            counts['users'] = len(user_records)

            # 4. Teachers (120: user_id 31 to 150)
            print("4. Inserting Teachers (120)...")
            teacher_records = []
            for tid in range(1, 121):
                u_id = 30 + tid
                qual = random.choice(["Ph.D. in Computer Science", "Ph.D. in Data Engineering", "M.Tech in CSE", "Ph.D. in Artificial Intelligence"])
                bio = f"Experienced academician and researcher in department {(tid%8)+1}."
                teacher_records.append((tid, u_id, f"EMP{tid:04d}", qual, bio, f"98234{tid:05d}"))
            cur.executemany("""
                INSERT INTO teachers (teacher_id, user_id, employee_code, qualification, bio, phone_no)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, teacher_records)
            counts['teachers'] = len(teacher_records)

            # 5. Students (500: user_id 151 to 650)
            print("5. Inserting Students (500)...")
            student_records = []
            for sid in range(1, 501):
                u_id = 150 + sid
                dep_id = (sid % 8) + 1
                roll = f"23BT{dep_id}{sid:04d}"
                enr_no = f"ITM2023CS{sid:04d}"
                sem = random.choice([3, 4, 5, 6])
                cgpa = round(random.uniform(5.5, 9.8), 2)
                dob = date(2003, (sid % 12) + 1, (sid % 28) + 1)
                student_records.append((sid, u_id, roll, enr_no, f"97123{sid:05d}", dob, sem, cgpa))
            cur.executemany("""
                INSERT INTO students (student_id, user_id, roll_no, enrollment_no, phone, dob, current_semester, cgpa)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, student_records)
            counts['students'] = len(student_records)

            # 6. Courses (100)
            print("6. Inserting Courses (100)...")
            COURSE_TITLES = [
                "Data Structures", "Database Management Systems", "Operating Systems", "Computer Networks",
                "Algorithms Design", "Software Engineering", "Artificial Intelligence", "Machine Learning",
                "Cloud Computing", "Cyber Security", "Web Technologies", "Discrete Mathematics",
                "Compiler Design", "Computer Architecture", "Object Oriented Programming", "Big Data Analytics",
                "Mobile App Development", "Deep Learning", "Internet of Things", "Blockchain Technology"
            ]
            course_records = []
            for cid in range(1, 101):
                dep_id = (cid % 8) + 1
                c_title = f"{COURSE_TITLES[(cid - 1) % len(COURSE_TITLES)]} {cid}"
                c_code = f"CS{cid:03d}"
                credits = random.choice([3, 4])
                course_records.append((cid, c_code, c_title, f"Comprehensive syllabus for {c_title}", 'PUBLISHED', dep_id, credits))
            cur.executemany("""
                INSERT INTO courses (course_id, course_code, title, description, status, department_id, credits)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, course_records)
            counts['courses'] = len(course_records)

            # 7. Course Offerings (150)
            print("7. Inserting Course Offerings (150)...")
            offering_records = []
            for off_id in range(1, 151):
                c_id = ((off_id - 1) % 100) + 1
                term_id = ((off_id - 1) % 6) + 1
                sec = chr(65 + ((off_id - 1) % 3)) # A, B, C
                offering_records.append((off_id, c_id, term_id, sec, 60, 0, 'OPEN'))
            cur.executemany("""
                INSERT INTO course_offerings (offering_id, course_id, term_id, section_name, max_capacity, enrolled_count, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, offering_records)
            counts['course_offerings'] = len(offering_records)

            # 8. Course Instructors (250)
            print("8. Inserting Course Instructors (250)...")
            ci_records = []
            assigned_pairs = set()
            for off_id in range(1, 151):
                c_id = ((off_id - 1) % 100) + 1
                t1 = ((off_id * 3) % 120) + 1
                if (c_id, t1) not in assigned_pairs:
                    ci_records.append((c_id, t1, 'OWNER', 1, off_id, 'PRIMARY'))
                    assigned_pairs.add((c_id, t1))
                if off_id <= 100:
                    t2 = ((off_id * 7) % 120) + 1
                    if t2 != t1 and (c_id, t2) not in assigned_pairs:
                        ci_records.append((c_id, t2, 'INSTRUCTOR', 1, off_id, 'TEACHING_ASSISTANT'))
                        assigned_pairs.add((c_id, t2))
            cur.executemany("""
                INSERT INTO course_instructors (course_id, teacher_id, instructor_role, is_authorized, offering_id, role_in_course)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ci_records)
            counts['course_instructors'] = len(ci_records)

            # 9. Modules (300) & Lessons (600)
            print("9. Inserting Modules (300) & Lessons (600)...")
            module_records = []
            for mid in range(1, 301):
                c_id = ((mid - 1) % 100) + 1
                seq = ((mid - 1) // 100) + 1
                module_records.append((mid, c_id, f"Module {seq}: Foundations", f"Overview of module {mid}", seq))
            cur.executemany("""
                INSERT INTO modules (module_id, course_id, title, description, sequence_no)
                VALUES (%s, %s, %s, %s, %s)
            """, module_records)
            counts['modules'] = len(module_records)

            lesson_records = []
            for lid in range(1, 601):
                mid = ((lid - 1) % 300) + 1
                seq = ((lid - 1) // 300) + 1
                lesson_records.append((lid, mid, f"Lesson {lid}: Theory & Practice", f"In-depth instructional text for lesson {lid}", seq, None, 0, 1))
            cur.executemany("""
                INSERT INTO lessons (lesson_id, module_id, title, content_text, sequence_no, release_date, is_restricted, required_for_completion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, lesson_records)
            counts['lessons'] = len(lesson_records)

            # 10. Enrollments (1,800: exactly 12 students per offering)
            print("10. Inserting Enrollments (1,800)...")
            enrollment_records = []
            enr_id = 1
            offering_students = {}
            course_active_enrollments = {cid: [] for cid in range(1, 101)}
            for off_id in range(1, 151):
                offering_students[off_id] = []
                c_id = ((off_id - 1) % 100) + 1
                base_s = ((off_id * 7) % 450) + 1
                for s_idx in range(12):
                    sid = base_s + s_idx
                    status = 'ACTIVE' if off_id > 50 else 'COMPLETED'
                    att_p = round(random.uniform(62.0, 98.0), 2)
                    enrollment_records.append((enr_id, sid, c_id, status, off_id, att_p))
                    offering_students[off_id].append((enr_id, sid))
                    if status == 'ACTIVE':
                        course_active_enrollments[c_id].append(enr_id)
                    enr_id += 1
            cur.executemany("""
                INSERT INTO enrollments (enrollment_id, student_id, course_id, status, offering_id, total_attendance_pct)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, enrollment_records)
            counts['enrollments'] = len(enrollment_records)

            cur.execute("""
                UPDATE course_offerings co 
                SET enrolled_count = (SELECT COUNT(*) FROM enrollments e WHERE e.offering_id = co.offering_id AND e.status = 'ACTIVE')
            """)

            # 11. Attendance Sessions (450: 3 per offering)
            print("11. Inserting Attendance Sessions (450)...")
            session_records = []
            sess_id = 1
            offering_sessions = {}
            for off_id in range(1, 151):
                offering_sessions[off_id] = []
                term_id = ((off_id - 1) % 6) + 1
                t_start = TERMS_DATA[term_id - 1][3]
                t_id = ((off_id * 3) % 120) + 1
                for s_num in range(1, 4):
                    s_date = t_start + timedelta(days=7 * s_num)
                    session_records.append((sess_id, off_id, t_id, s_date, f"Lecture Session #{s_num}: Practical Architecture"))
                    offering_sessions[off_id].append(sess_id)
                    sess_id += 1
            cur.executemany("""
                INSERT INTO attendance_sessions (session_id, offering_id, teacher_id, session_date, topic_covered)
                VALUES (%s, %s, %s, %s, %s)
            """, session_records)
            counts['attendance_sessions'] = len(session_records)

            # 12. Attendance Records (450 sessions * 12 students = 5,400 records)
            print("12. Inserting Attendance Records (5,400) [Main Transaction Table]...")
            att_records = []
            for off_id, s_ids in offering_sessions.items():
                enr_list = offering_students[off_id]
                for s_id in s_ids:
                    for (e_id, _) in enr_list:
                        st = random.choices(['PRESENT', 'ABSENT', 'LATE', 'EXCUSED'], weights=[0.82, 0.10, 0.05, 0.03])[0]
                        att_records.append((s_id, e_id, st, "Recorded attendance"))
            
            batch_size = 1000
            for i in range(0, len(att_records), batch_size):
                cur.executemany("""
                    INSERT INTO attendance_records (session_id, enrollment_id, status, remarks)
                    VALUES (%s, %s, %s, %s)
                """, att_records[i:i+batch_size])
            counts['attendance_records'] = len(att_records)

            # 13. Assignments (300: 2 per offering)
            print("13. Inserting Assignments (300)...")
            assign_records = []
            assign_id = 1
            offering_assignments = {}
            for off_id in range(1, 151):
                offering_assignments[off_id] = []
                term_id = ((off_id - 1) % 6) + 1
                t_start = TERMS_DATA[term_id - 1][3]
                for a_num in range(1, 3):
                    due = t_start + timedelta(days=14 * a_num)
                    assign_records.append((assign_id, off_id, f"Assignment #{a_num}: Problem Solving", f"Complete problem set {a_num}", 100.0, 20.0, due, 1))
                    offering_assignments[off_id].append(assign_id)
                    assign_id += 1
            cur.executemany("""
                INSERT INTO assignments (assignment_id, offering_id, title, description, max_marks, weightage_pct, due_date, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, assign_records)
            counts['assignments'] = len(assign_records)

            # 14. Submissions (1,800)
            print("14. Inserting Submissions (1,800) [Main Transaction Table]...")
            sub_records = []
            sub_id = 1
            for off_id, a_ids in offering_assignments.items():
                enr_list = offering_students[off_id]
                for a_id in a_ids:
                    for (e_id, _) in enr_list[:6]: # 6 students submit each assignment
                        status = random.choices(['EVALUATED', 'SUBMITTED'], weights=[0.80, 0.20])[0]
                        marks = round(random.uniform(50.0, 95.0), 2) if status == 'EVALUATED' else None
                        sub_records.append((sub_id, a_id, e_id, f"Solution text for assignment {a_id}", f"/uploads/sub_{sub_id}.pdf", status, marks, "Evaluated feedback" if marks else None, datetime.now() if marks else None))
                        sub_id += 1
            for i in range(0, len(sub_records), batch_size):
                cur.executemany("""
                    INSERT INTO submissions (submission_id, assignment_id, enrollment_id, submission_text, file_path, status, marks_obtained, feedback, graded_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, sub_records[i:i+batch_size])
            counts['submissions'] = len(sub_records)

            # 15. Grades (matching evaluated submissions, unique per enrollment)
            print("15. Inserting Grades [Main Transaction Table]...")
            grade_records = []
            gid = 1
            graded_enrollments = set()
            for sub in sub_records:
                enr_id = sub[2]
                if sub[5] == 'EVALUATED' and enr_id not in graded_enrollments:
                    graded_enrollments.add(enr_id)
                    score = sub[6]
                    let = 'A' if score >= 85 else ('B' if score >= 70 else ('C' if score >= 50 else 'F'))
                    grade_records.append((gid, enr_id, score, let, 1, sub[0], "Official final grade publication"))
                    gid += 1
            cur.executemany("""
                INSERT INTO grades (grade_id, enrollment_id, final_score, letter_grade, published, submission_id, feedback)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, grade_records)
            counts['grades'] = len(grade_records)

            # 16. Quizzes (100: 1 per course attached to lesson_id)
            print("16. Inserting Quizzes (100), Questions (400), Options (1,600)...")
            quiz_records = []
            now_dt = datetime.now()
            for qid in range(1, 101):
                lesson_id = qid # attach to lesson
                quiz_records.append((qid, lesson_id, f"Review Quiz #{qid}", 20.0, 3, now_dt - timedelta(days=30), now_dt + timedelta(days=60), 1))
            cur.executemany("""
                INSERT INTO quizzes (quiz_id, lesson_id, title, max_score, allowed_attempts, available_from, available_until, required_for_completion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, quiz_records)
            counts['quizzes'] = len(quiz_records)

            question_records = []
            quest_id = 1
            for qid in range(1, 101):
                for q_num in range(1, 5):
                    question_records.append((quest_id, qid, f"Question {q_num}: Analyze the relational schema property.", 5.0, q_num))
                    quest_id += 1
            cur.executemany("""
                INSERT INTO quiz_questions (question_id, quiz_id, question_text, points, sequence_no)
                VALUES (%s, %s, %s, %s, %s)
            """, question_records)
            counts['quiz_questions'] = len(question_records)

            option_records = []
            opt_id = 1
            for q_entry in question_records:
                for o_idx in range(4):
                    is_c = 1 if o_idx == 0 else 0
                    option_records.append((opt_id, q_entry[0], f"Answer option choice {chr(65+o_idx)}", is_c, o_idx + 1))
                    opt_id += 1
            for i in range(0, len(option_records), batch_size):
                cur.executemany("""
                    INSERT INTO quiz_options (option_id, question_id, option_text, is_correct, sequence_no)
                    VALUES (%s, %s, %s, %s, %s)
                """, option_records[i:i+batch_size])
            counts['quiz_options'] = len(option_records)

            # 17. Attempts & Attempt Answers
            print("17. Inserting Attempts & Answers...")
            attempt_records = []
            ans_records = []
            att_id = 1
            ans_id = 1
            now_dt = datetime.now()
            for qid in range(1, 101):
                c_id = ((qid - 1) % 100) + 1
                active_enrs = course_active_enrollments.get(c_id, [])
                used_enrs = set()
                for enr_id in active_enrs[:8]:
                    if enr_id in used_enrs:
                        continue
                    used_enrs.add(enr_id)
                    score = random.choice([10.0, 15.0, 20.0])
                    attempt_records.append((att_id, qid, enr_id, 1, now_dt, now_dt, score, 'SUBMITTED'))
                    # 4 answers per attempt
                    start_q = (qid - 1) * 4 + 1
                    for q_off in range(4):
                        opt_id_sel = (start_q + q_off - 1) * 4 + 1
                        ans_records.append((ans_id, att_id, start_q + q_off, opt_id_sel, 1, 5.0))
                        ans_id += 1
                    att_id += 1
            cur.executemany("""
                INSERT INTO attempts (attempt_id, quiz_id, enrollment_id, attempt_no, started_at, submitted_at, score, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, attempt_records)
            counts['attempts'] = len(attempt_records)

            for i in range(0, len(ans_records), batch_size):
                cur.executemany("""
                    INSERT INTO attempt_answers (answer_id, attempt_id, question_id, selected_option_id, is_correct, points_awarded)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, ans_records[i:i+batch_size])
            counts['attempt_answers'] = len(ans_records)

            # 18. Completions (1,800) & Certificates (400)
            print("18. Inserting Completions (1,800) & Certificates (400)...")
            comp_records = []
            cert_records = []
            cert_id = 1
            for enr in enrollment_records:
                eid = enr[0]
                status = 'COMPLETED' if enr[3] == 'COMPLETED' else 'IN_PROGRESS'
                comp_records.append((eid, status, datetime.now() if status == 'COMPLETED' else None))
                if status == 'COMPLETED' and cert_id <= 400:
                    cert_records.append((cert_id, eid, f"CERT-2026-ITM-{cert_id:05d}", datetime.now()))
                    cert_id += 1
            cur.executemany("""
                INSERT INTO completions (enrollment_id, completion_status, completed_at)
                VALUES (%s, %s, %s)
            """, comp_records)
            counts['completions'] = len(comp_records)

            cur.executemany("""
                INSERT INTO certificates (certificate_id, enrollment_id, certificate_code, issued_at)
                VALUES (%s, %s, %s, %s)
            """, cert_records)
            counts['certificates'] = len(cert_records)

            # 19. Announcements (150) & Audit Logs (1,200)
            print("19. Inserting Announcements (150) & Audit Logs (1,200)...")
            ann_records = []
            for aid in range(1, 151):
                ann_records.append((aid, f"Notice #{aid}: Term Academic Updates", "Please check course schedule and assignment due dates.", aid, 1))
            cur.executemany("""
                INSERT INTO announcements (announcement_id, title, content, offering_id, author_id)
                VALUES (%s, %s, %s, %s, %s)
            """, ann_records)
            counts['announcements'] = len(ann_records)

            audit_records = []
            for au_id in range(1, 1201):
                audit_records.append(('enrollments', (au_id % 1800) + 1, 'STUDENT_ENROLLMENT', 1, 'Automated enrollment record', datetime.now()))
            for i in range(0, len(audit_records), batch_size):
                cur.executemany("""
                    INSERT INTO audit_logs (entity_name, entity_id, action_type, performed_by, details, action_time)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, audit_records[i:i+batch_size])
            counts['audit_logs'] = len(audit_records)

            # 20. Academic Risks (400)
            print("20. Inserting Academic Risks (400)...")
            risk_records = []
            for rid in range(1, 401):
                enr = enrollment_records[rid - 1]
                sid = enr[1]
                off_id = enr[4]
                att_p = enr[5]
                grade_p = round(random.uniform(40.0, 90.0), 2)
                overdue = random.choice([0, 1, 2, 3])
                score = round(0.40 * max(0.0, (75.0 - att_p)/75.0*100) + 0.40 * max(0.0, (50.0 - grade_p)/50.0*100) + 0.20 * min(100.0, overdue*25.0), 2)
                cls = 'HIGH' if score >= 60 else ('MODERATE' if score >= 30 else 'LOW')
                status = 'PENDING' if rid <= 200 else 'CONFIRMED'
                risk_records.append((rid, sid, off_id, att_p, grade_p, overdue, score, cls, 'SUFFICIENT', f"Risk score: {score:.2f}", status, 1 if rid > 200 else None, "Automated assessment", datetime.now(), 'v1.0'))
            cur.executemany("""
                INSERT INTO academic_risks (risk_id, student_id, offering_id, attendance_pct, assessment_pct, overdue_count, risk_score, risk_classification, data_sufficiency, explanation, review_status, reviewer_id, review_notes, reviewed_at, rule_version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, risk_records)
            counts['academic_risks'] = len(risk_records)

            cur.execute("SET FOREIGN_KEY_CHECKS = 1")
            conn.commit()

            total_rows = sum(counts.values())
            print("\n=======================================================")
            print(f"BENCHMARK DATASET GENERATION COMPLETE: {total_rows:,} ROWS")
            print("=======================================================")
            for t, c in counts.items():
                print(f"  {t:25s}: {c:,} rows")

    finally:
        conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='minilms_benchmark_db')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    generate_benchmark_data(target_db=args.db, seed=args.seed)
