-- MiniLMS Database Security Roles Definition
-- Defines role-based privileges adhering strictly to the Principle of Least Privilege.

-- 1. Create Roles
CREATE ROLE IF NOT EXISTS 'app_runtime_role';
CREATE ROLE IF NOT EXISTS 'reporting_role';
CREATE ROLE IF NOT EXISTS 'audit_role';

-- 2. Grant Privileges to 'app_runtime_role' (Web Application Backend)
-- Needs full CRUD on operational tables and EXECUTE on stored routines.
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`academic_terms` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`announcements` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`assignments` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`attempt_answers` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`attempts` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`attendance_records` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`attendance_sessions` TO 'app_runtime_role';
GRANT SELECT, INSERT ON `minilms_db`.`audit_logs` TO 'app_runtime_role'; -- NOTE: Never grant UPDATE/DELETE on audit_logs!
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`certificates` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`completions` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`course_instructors` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`course_offerings` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`courses` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`departments` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`enrollments` TO 'app_runtime_role';
GRANT SELECT, INSERT ON `minilms_db`.`grade_change_history` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`grades` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`lesson_prerequisites` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`lesson_progress` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`lessons` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`modules` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`quiz_options` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`quiz_questions` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`quizzes` TO 'app_runtime_role';
GRANT SELECT, INSERT ON `minilms_db`.`schema_versions` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`students` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`submissions` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`teachers` TO 'app_runtime_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON `minilms_db`.`users` TO 'app_runtime_role';
GRANT EXECUTE ON `minilms_db`.* TO 'app_runtime_role';

-- 3. Grant Privileges to 'reporting_role' (Data Analyst & Reporting Service)
-- Strictly Read-Only access across views and non-sensitive operational tables.
GRANT SELECT ON `minilms_db`.`v_student_academic_summary` TO 'reporting_role';
GRANT SELECT ON `minilms_db`.`v_course_offering_summary` TO 'reporting_role';
GRANT SELECT ON `minilms_db`.`v_department_performance` TO 'reporting_role';
GRANT SELECT ON `minilms_db`.`v_faculty_workload` TO 'reporting_role';
GRANT SELECT ON `minilms_db`.`v_course_completion` TO 'reporting_role';
GRANT SELECT ON `minilms_db`.`v_course_enrollments` TO 'reporting_role';
GRANT SELECT ON `minilms_db`.`v_quiz_performance` TO 'reporting_role';
GRANT SELECT ON `minilms_db`.`v_student_courses` TO 'reporting_role';
GRANT SELECT ON `minilms_db`.`v_student_grades` TO 'reporting_role';
GRANT SELECT ON `minilms_db`.`faculty` TO 'reporting_role';
GRANT SELECT ON `minilms_db`.`faculty_allocations` TO 'reporting_role';
GRANT SELECT ON `minilms_db`.`courses` TO 'reporting_role';
GRANT SELECT ON `minilms_db`.`departments` TO 'reporting_role';
GRANT SELECT ON `minilms_db`.`academic_terms` TO 'reporting_role';
GRANT SELECT ON `minilms_db`.`course_offerings` TO 'reporting_role';

-- 4. Grant Privileges to 'audit_role' (Independent Compliance Auditor)
-- Read-Only access strictly to audit and security verification tables.
GRANT SELECT ON `minilms_db`.`audit_logs` TO 'audit_role';
GRANT SELECT ON `minilms_db`.`grade_change_history` TO 'audit_role';
GRANT SELECT ON `minilms_db`.`schema_versions` TO 'audit_role';
