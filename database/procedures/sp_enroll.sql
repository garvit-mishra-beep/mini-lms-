-- Stored Procedure: sp_enroll
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_enroll`(IN p_student INT, IN p_course INT)
BEGIN
    DECLARE v_active_count INT DEFAULT 0;
    DECLARE v_student_status VARCHAR(20);
    DECLARE v_course_status VARCHAR(20);
    DECLARE v_new_enrollment_id INT;

    START TRANSACTION;

    
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

    
    SELECT COUNT(*) INTO v_active_count
    FROM enrollments
    WHERE student_id = p_student AND course_id = p_course AND status = 'ACTIVE'
    FOR UPDATE;

    IF v_active_count > 0 THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Student is already actively enrolled in this course';
    END IF;

    
    INSERT INTO enrollments(student_id, course_id, status)
    VALUES(p_student, p_course, 'ACTIVE');

    SET v_new_enrollment_id = LAST_INSERT_ID();

    INSERT INTO completions(enrollment_id, completion_status)
    VALUES(v_new_enrollment_id, 'IN_PROGRESS');

    COMMIT;
END;
DELIMITER ;
