-- Stored Procedure: sp_publish_grade
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_publish_grade`(IN p_enrollment INT)
BEGIN
 DECLARE avg_pct DECIMAL(6,2);
 DECLARE letter VARCHAR(2);
 DECLARE cnt INT;
 SELECT COUNT(*),ROUND(AVG(a.score/q.max_score*100),2) INTO cnt,avg_pct
 FROM attempts a JOIN quizzes q ON q.quiz_id=a.quiz_id
 WHERE a.enrollment_id=p_enrollment AND a.status='SUBMITTED';
 IF cnt=0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='No submitted attempts'; END IF;
 SET letter=CASE WHEN avg_pct>=90 THEN 'A' WHEN avg_pct>=75 THEN 'B'
 WHEN avg_pct>=60 THEN 'C' WHEN avg_pct>=40 THEN 'D' ELSE 'F' END;
 INSERT INTO grades(enrollment_id,final_score,letter_grade,published,published_at)
 VALUES(p_enrollment,avg_pct,letter,TRUE,NOW())
 ON DUPLICATE KEY UPDATE published=TRUE,published_at=NOW();
END;
DELIMITER ;
