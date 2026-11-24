-- MiniLMS Migration v010: Foundational Stored Procedures and Analytical Views
-- Creates compatibility views, analytical views, and stored procedures for enrollment, attendance, and grading.

SET FOREIGN_KEY_CHECKS = 0;

-- 1. Compatibility Views for Academic Terminology
CREATE OR REPLACE VIEW `faculty` AS
SELECT 
    `teacher_id` AS `faculty_id`,
    `user_id`,
    `employee_code`,
    `qualification`,
    `bio`,
    `phone_no`
FROM `teachers`;

CREATE OR REPLACE VIEW `faculty_allocations` AS
SELECT 
    CONCAT(`course_id`, '_', `teacher_id`) AS `allocation_id`,
    `offering_id`,
    `course_id`,
    `teacher_id` AS `faculty_id`,
    `role_in_course`,
    `is_authorized`,
    `assigned_at`
FROM `course_instructors`;

-- 2. Analytical Views

-- 2.1 Student Academic Summary View
CREATE OR REPLACE VIEW `v_student_academic_summary` AS
SELECT 
    s.student_id,
    s.roll_no,
    s.enrollment_no,
    u.full_name,
    u.email,
    d.department_code,
    d.department_name,
    s.current_semester,
    s.cgpa,
    u.status AS student_status,
    COUNT(e.enrollment_id) AS total_enrolled_courses,
    SUM(CASE WHEN e.status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_courses,
    ROUND(AVG(COALESCE(e.total_attendance_pct, 100.00)), 2) AS avg_attendance_pct
FROM `students` s
JOIN `users` u ON s.user_id = u.user_id
LEFT JOIN `departments` d ON u.department_id = d.department_id
LEFT JOIN `enrollments` e ON s.student_id = e.student_id
GROUP BY s.student_id, s.roll_no, s.enrollment_no, u.full_name, u.email, d.department_code, d.department_name, s.current_semester, s.cgpa, u.status;

-- 2.2 Course Offering Summary View
CREATE OR REPLACE VIEW `v_course_offering_summary` AS
SELECT 
    co.offering_id,
    c.course_code,
    c.title AS course_title,
    c.credits,
    d.department_code,
    t.term_code,
    t.term_name,
    co.section_name,
    co.max_capacity,
    co.enrolled_count,
    ROUND((co.enrolled_count * 100.0) / NULLIF(co.max_capacity, 0), 1) AS capacity_utilization_pct,
    co.status AS offering_status,
    u.full_name AS primary_instructor_name,
    fac.employee_code AS primary_instructor_code
FROM `course_offerings` co
JOIN `courses` c ON co.course_id = c.course_id
JOIN `academic_terms` t ON co.term_id = t.term_id
LEFT JOIN `departments` d ON c.department_id = d.department_id
LEFT JOIN `course_instructors` ci ON co.offering_id = ci.offering_id AND ci.role_in_course = 'PRIMARY'
LEFT JOIN `teachers` fac ON ci.teacher_id = fac.teacher_id
LEFT JOIN `users` u ON fac.user_id = u.user_id;

-- 2.3 Department Performance Benchmark View
CREATE OR REPLACE VIEW `v_department_performance` AS
SELECT 
    d.department_id,
    d.department_code,
    d.department_name,
    COUNT(DISTINCT s.student_id) AS total_students,
    ROUND(AVG(s.cgpa), 2) AS dept_avg_cgpa,
    COUNT(DISTINCT c.course_id) AS total_courses_offered,
    COUNT(DISTINCT t.teacher_id) AS total_faculty_count
FROM `departments` d
LEFT JOIN `users` u ON d.department_id = u.department_id AND u.status = 'ACTIVE'
LEFT JOIN `students` s ON u.user_id = s.user_id
LEFT JOIN `teachers` t ON u.user_id = t.user_id
LEFT JOIN `courses` c ON d.department_id = c.department_id
GROUP BY d.department_id, d.department_code, d.department_name;

-- 2.4 Faculty Workload View
CREATE OR REPLACE VIEW `v_faculty_workload` AS
SELECT 
    fac.teacher_id AS faculty_id,
    fac.employee_code,
    u.full_name,
    fac.qualification,
    d.department_code,
    COUNT(DISTINCT ci.offering_id) AS total_assigned_sections,
    SUM(c.credits) AS total_teaching_credits,
    COUNT(DISTINCT att.session_id) AS total_lectures_conducted
FROM `teachers` fac
JOIN `users` u ON fac.user_id = u.user_id
LEFT JOIN `departments` d ON u.department_id = d.department_id
LEFT JOIN `course_instructors` ci ON fac.teacher_id = ci.teacher_id
LEFT JOIN `course_offerings` co ON ci.offering_id = co.offering_id
LEFT JOIN `courses` c ON co.course_id = c.course_id
LEFT JOIN `attendance_sessions` att ON co.offering_id = att.offering_id AND att.teacher_id = fac.teacher_id
GROUP BY fac.teacher_id, fac.employee_code, u.full_name, fac.qualification, d.department_code;

-- 3. Stored Procedures

DROP PROCEDURE IF EXISTS `sp_enroll_student_in_offering`;
DROP PROCEDURE IF EXISTS `sp_record_attendance_session`;
DROP PROCEDURE IF EXISTS `sp_grade_assignment_submission`;
DROP PROCEDURE IF EXISTS `sp_calculate_student_gpa`;

DELIMITER //

-- 3.1 sp_enroll_student_in_offering (TX-01 with row lock and capacity check)
CREATE PROCEDURE `sp_enroll_student_in_offering`(
    IN p_student_id INT,
    IN p_offering_id INT,
    OUT p_enrollment_id INT,
    OUT p_status_message VARCHAR(100)
)
sp_block: BEGIN
    DECLARE v_course_id INT;
    DECLARE v_max_cap INT;
    DECLARE v_curr_enrolled INT;
    DECLARE v_offering_status VARCHAR(20);
    DECLARE v_existing_active INT DEFAULT 0;

    -- Exit handler for unhandled SQL errors
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_enrollment_id = 0;
        SET p_status_message = 'DATABASE_ERROR: Transaction rolled back.';
    END;

    START TRANSACTION;

    -- Lock the offering row to prevent seat race condition
    SELECT course_id, max_capacity, enrolled_count, status
    INTO v_course_id, v_max_cap, v_curr_enrolled, v_offering_status
    FROM `course_offerings`
    WHERE `offering_id` = p_offering_id
    FOR UPDATE;

    IF v_course_id IS NULL THEN
        ROLLBACK;
        SET p_enrollment_id = 0;
        SET p_status_message = 'ERROR: Course offering section does not exist.';
        LEAVE sp_block;
    END IF;

    IF v_offering_status <> 'OPEN' THEN
        ROLLBACK;
        SET p_enrollment_id = 0;
        SET p_status_message = 'ERROR: Course offering is not open for registration.';
        LEAVE sp_block;
    END IF;

    IF v_curr_enrolled >= v_max_cap THEN
        ROLLBACK;
        SET p_enrollment_id = 0;
        SET p_status_message = 'ERROR: Course offering section capacity exceeded.';
        LEAVE sp_block;
    END IF;

    -- Check for existing active enrollment in this course
    SELECT COUNT(*) INTO v_existing_active
    FROM `enrollments`
    WHERE `student_id` = p_student_id 
      AND `course_id` = v_course_id 
      AND `status` = 'ACTIVE';

    IF v_existing_active > 0 THEN
        ROLLBACK;
        SET p_enrollment_id = 0;
        SET p_status_message = 'CONFLICT: Student is already actively enrolled in this course.';
        LEAVE sp_block;
    END IF;

    -- Insert enrollment tuple
    INSERT INTO `enrollments` (`student_id`, `course_id`, `offering_id`, `status`, `total_attendance_pct`)
    VALUES (p_student_id, v_course_id, p_offering_id, 'ACTIVE', 100.00);

    SET p_enrollment_id = LAST_INSERT_ID();

    -- Also record baseline completion record
    INSERT INTO `completions` (`enrollment_id`, `completion_status`)
    VALUES (p_enrollment_id, 'IN_PROGRESS');

    -- NOTE: enrolled_count is maintained automatically by trigger trg_enrollment_seat_increment!

    COMMIT;
    SET p_status_message = 'SUCCESS: Student enrolled successfully.';
END //

-- 3.2 sp_record_attendance_session (TX-02 Master Lecture creation)
CREATE PROCEDURE `sp_record_attendance_session`(
    IN p_offering_id INT,
    IN p_teacher_id INT,
    IN p_session_date DATE,
    IN p_topic VARCHAR(200),
    OUT p_session_id INT
)
BEGIN
    START TRANSACTION;
    INSERT INTO `attendance_sessions` (`offering_id`, `teacher_id`, `session_date`, `topic_covered`)
    VALUES (p_offering_id, p_teacher_id, p_session_date, p_topic);
    SET p_session_id = LAST_INSERT_ID();
    COMMIT;
END //

-- 3.3 sp_grade_assignment_submission (TX-03 Evaluation and Feedback)
CREATE PROCEDURE `sp_grade_assignment_submission`(
    IN p_submission_id INT,
    IN p_marks DECIMAL(5,2),
    IN p_feedback TEXT,
    IN p_graded_by INT,
    OUT p_status_msg VARCHAR(100)
)
sp_grade_block: BEGIN
    DECLARE v_enrollment_id INT;
    DECLARE v_max_marks DECIMAL(5,2);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status_msg = 'DATABASE_ERROR: Grading transaction aborted.';
    END;

    START TRANSACTION;

    SELECT s.enrollment_id, a.max_marks
    INTO v_enrollment_id, v_max_marks
    FROM `submissions` s
    JOIN `assignments` a ON s.assignment_id = a.assignment_id
    WHERE s.submission_id = p_submission_id
    FOR UPDATE;

    IF v_enrollment_id IS NULL THEN
        ROLLBACK;
        SET p_status_msg = 'ERROR: Submission record not found.';
        LEAVE sp_grade_block;
    END IF;

    IF p_marks < 0.00 OR p_marks > v_max_marks THEN
        ROLLBACK;
        SET p_status_msg = 'ERROR: Marks out of permissible assignment bounds.';
        LEAVE sp_grade_block;
    END IF;

    -- Update submission status to EVALUATED with marks and feedback
    UPDATE `submissions`
    SET `status` = 'EVALUATED',
        `marks_obtained` = p_marks,
        `feedback` = p_feedback,
        `graded_at` = NOW()
    WHERE `submission_id` = p_submission_id;

    -- Update linked grade record if present
    UPDATE `grades`
    SET `submission_id` = p_submission_id,
        `feedback` = p_feedback
    WHERE `enrollment_id` = v_enrollment_id;

    COMMIT;
    SET p_status_msg = 'SUCCESS: Submission evaluated and grade recorded.';
END //

-- 3.4 sp_calculate_student_gpa
CREATE PROCEDURE `sp_calculate_student_gpa`(
    IN p_student_id INT,
    OUT p_new_cgpa DECIMAL(4,2)
)
BEGIN
    DECLARE v_avg_cgpa DECIMAL(4,2);

    -- Calculate average score normalized to 10-point scale across all completed enrollments
    SELECT ROUND(AVG(g.final_score) / 10.0, 2) INTO v_avg_cgpa
    FROM `enrollments` e
    JOIN `grades` g ON e.enrollment_id = g.enrollment_id
    WHERE e.student_id = p_student_id AND e.status IN ('ACTIVE', 'COMPLETED');

    IF v_avg_cgpa IS NOT NULL THEN
        UPDATE `students`
        SET `cgpa` = LEAST(10.00, GREATEST(0.00, v_avg_cgpa))
        WHERE `student_id` = p_student_id;
        SET p_new_cgpa = v_avg_cgpa;
    ELSE
        SET p_new_cgpa = 0.00;
    END IF;
END //

DELIMITER ;

-- Record Migration v010 in schema_versions
INSERT INTO `schema_versions` (`version_no`, `description`, `applied_at`)
VALUES (10, 'Analytical views: v_student_academic_summary, v_course_offering_summary, v_department_performance, v_faculty_workload, and stored programs', NOW())
ON DUPLICATE KEY UPDATE `applied_at` = NOW();

SET FOREIGN_KEY_CHECKS = 1;
