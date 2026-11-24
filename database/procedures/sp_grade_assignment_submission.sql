-- Stored Procedure: sp_grade_assignment_submission
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_grade_assignment_submission`(
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

    
    UPDATE `submissions`
    SET `status` = 'EVALUATED',
        `marks_obtained` = p_marks,
        `feedback` = p_feedback,
        `graded_at` = NOW()
    WHERE `submission_id` = p_submission_id;

    
    UPDATE `grades`
    SET `submission_id` = p_submission_id,
        `feedback` = p_feedback
    WHERE `enrollment_id` = v_enrollment_id;

    COMMIT;
    SET p_status_msg = 'SUCCESS: Submission evaluated and grade recorded.';
END;
DELIMITER ;
