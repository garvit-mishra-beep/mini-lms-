-- Stored Procedure: sp_submit_attempt
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_submit_attempt`(IN p_attempt INT, IN p_score DECIMAL(8,2))
BEGIN
 START TRANSACTION;
 UPDATE attempts SET score=p_score,submitted_at=NOW(),status='SUBMITTED'
 WHERE attempt_id=p_attempt AND status='IN_PROGRESS';
 IF ROW_COUNT()<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Attempt not found or already submitted'; END IF;
 COMMIT;
END;
DELIMITER ;
