-- Stored Procedure: sp_start_attempt
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_start_attempt`(IN p_enrollment INT,IN p_quiz INT)
BEGIN
 DECLARE next_no INT;
 START TRANSACTION;
 
 SELECT enrollment_id INTO @locked_enrollment FROM enrollments WHERE enrollment_id=p_enrollment FOR UPDATE;
 SELECT COUNT(*)+1 INTO next_no FROM attempts WHERE enrollment_id=p_enrollment AND quiz_id=p_quiz;
 INSERT INTO attempts(enrollment_id,quiz_id,attempt_no) VALUES(p_enrollment,p_quiz,next_no);
 COMMIT;
END;
DELIMITER ;
