-- Migration v006: Upgrade sp_enroll with robust duplicate checks and business validations
-- DBMS PBL MiniLMS Upgrade

DROP PROCEDURE IF EXISTS sp_enroll;

DELIMITER //

CREATE PROCEDURE sp_enroll(IN p_student INT, IN p_course INT)
BEGIN
    DECLARE v_active_count INT DEFAULT 0;
    DECLARE v_student_status VARCHAR(20);
    DECLARE v_course_status VARCHAR(20);
    DECLARE v_new_enrollment_id INT;

    START TRANSACTION;

    -- 1. Check student existence and status
    SELECT u.status INTO v_student_status
    FROM students s
    JOIN users u ON u.user_id = s.user_id
    WHERE s.student_id = p_student
    FOR SHARE;

    IF v_student_status IS NULL THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Student record does not exist';
    ELSEIF v_student_status <> 'ACTIVE' THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only active students may enroll';
    END IF;

    -- 2. Check course existence and status
    SELECT status INTO v_course_status
    FROM courses
    WHERE course_id = p_course
    FOR SHARE;

    IF v_course_status IS NULL THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Course does not exist';
    ELSEIF v_course_status <> 'PUBLISHED' THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Course is not published';
    END IF;

    -- 3. Row-level lock check for existing active enrollment
    SELECT COUNT(*) INTO v_active_count
    FROM enrollments
    WHERE student_id = p_student AND course_id = p_course AND status = 'ACTIVE'
    FOR UPDATE;

    IF v_active_count > 0 THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Student is already actively enrolled in this course';
    END IF;

    -- 4. Perform atomic insert
    INSERT INTO enrollments(student_id, course_id, status)
    VALUES(p_student, p_course, 'ACTIVE');

    SET v_new_enrollment_id = LAST_INSERT_ID();

    INSERT INTO completions(enrollment_id, completion_status)
    VALUES(v_new_enrollment_id, 'IN_PROGRESS');

    COMMIT;
END //

DELIMITER ;

INSERT INTO schema_versions (version_no, description, applied_at)
VALUES (6, 'Enhanced sp_enroll with active duplicate lock, status validations, and atomic completion', NOW())
ON DUPLICATE KEY UPDATE description = VALUES(description), applied_at = NOW();
