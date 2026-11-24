-- Stored Procedure: sp_enroll_student_in_offering
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_enroll_student_in_offering`(
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

    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_enrollment_id = 0;
        SET p_status_message = 'DATABASE_ERROR: Transaction rolled back.';
    END;

    START TRANSACTION;

    
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

    
    INSERT INTO `enrollments` (`student_id`, `course_id`, `offering_id`, `status`, `total_attendance_pct`)
    VALUES (p_student_id, v_course_id, p_offering_id, 'ACTIVE', 100.00);

    SET p_enrollment_id = LAST_INSERT_ID();

    
    INSERT INTO `completions` (`enrollment_id`, `completion_status`)
    VALUES (p_enrollment_id, 'IN_PROGRESS');

    

    COMMIT;
    SET p_status_message = 'SUCCESS: Student enrolled successfully.';
END;
DELIMITER ;
