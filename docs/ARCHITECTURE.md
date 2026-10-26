# MiniLMS Architecture & Schema Design

## Database Schema Highlights

MiniLMS is built on MySQL 8.0 with relational integrity, triggers, stored procedures, and views.

### Core Tables
- `users`: Stores user credentials, hashed passwords (`scrypt` / `pbkdf2`), and role (`ADMIN`, `TEACHER`, `STUDENT`).
- `students` & `teachers`: Specialized subtype entities referencing `users(user_id)`.
- `courses`: Master course information with publishing status (`DRAFT`, `PUBLISHED`, `ARCHIVED`).
- `course_instructors`: Associative table linking teachers to courses.
- `modules` & `lessons`: Hierarchical course syllabus organization with ordering and prerequisite checks.
- `enrollments`: Active student enrollments with unique constraint `(student_id, course_id)`.
- `quizzes`, `quiz_questions`, `quiz_options`: Normalized assessment engine.
- `attempts` & `attempt_answers`: Student assessment submissions evaluated server-side.
- `completions`: Student progress tracker.
- `audit_logs` & `grade_change_history`: Immutable logs for sensitive operations and grade modifications.

### Analytical SQL Views
- `v_course_enrollments`: Real-time active student enrollment counts per course.
- `v_student_grades`: Grade distributions, attempt numbers, and percentages.
- `v_course_completion`: Percentage completion rates partitioned by student and course.
- `v_quiz_performance`: Average scores, pass rates, and performance statistics across attempts.

### Stored Procedures & Triggers
- `sp_enroll`: Atomic enrollment procedure with `FOR UPDATE` lock, preventing duplicate and race-condition enrollments.
- `sp_correct_published_grade`: Authorized grade correction with mandatory reason and automated audit trail insertion.
- `trg_course_publish`: Prevents publishing any course without an assigned instructor.
- `trg_prerequisite_validate`: Prevents circular prerequisites and mismatched course dependencies using recursive CTE validation.
