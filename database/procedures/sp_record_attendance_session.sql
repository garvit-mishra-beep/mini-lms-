-- Stored Procedure: sp_record_attendance_session
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_record_attendance_session`(
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
END;
DELIMITER ;
