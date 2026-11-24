-- Stored Procedure: sp_correct_published_grade
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_correct_published_grade`(IN p_grade INT,IN p_score DECIMAL(6,2),IN p_actor INT,IN p_reason VARCHAR(255))
BEGIN
 DECLARE actor_role VARCHAR(20); DECLARE actor_status VARCHAR(20);
 IF p_reason IS NULL OR LENGTH(TRIM(p_reason))=0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Reason is required'; END IF;
 SELECT role,status INTO actor_role,actor_status FROM users WHERE user_id=p_actor;
 IF actor_status<>'ACTIVE' OR actor_role NOT IN ('ADMIN','TEACHER') THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unauthorized grade correction'; END IF;
 IF p_score<0 OR p_score>100 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Invalid grade percentage'; END IF;
 SET @grade_actor=p_actor; SET @grade_reason=p_reason; SET @grade_change_approved=1;
 UPDATE grades SET final_score=p_score,
 letter_grade=CASE WHEN p_score>=90 THEN 'A' WHEN p_score>=75 THEN 'B'
 WHEN p_score>=60 THEN 'C' WHEN p_score>=40 THEN 'D' ELSE 'F' END
 WHERE grade_id=p_grade AND published=1;
 SET @grade_change_approved=NULL; SET @grade_actor=NULL; SET @grade_reason=NULL;
END;
DELIMITER ;
