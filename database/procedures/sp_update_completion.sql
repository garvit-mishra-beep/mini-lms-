-- Stored Procedure: sp_update_completion
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_update_completion`(IN p_enrollment INT)
BEGIN
 DECLARE missing_lessons INT; DECLARE missing_quizzes INT; DECLARE pct DECIMAL(6,2);
 SELECT COUNT(*) INTO missing_lessons FROM lessons l JOIN modules m ON m.module_id=l.module_id
 JOIN enrollments e ON e.course_id=m.course_id
 WHERE e.enrollment_id=p_enrollment AND l.required_for_completion=1 AND NOT EXISTS
 (SELECT 1 FROM lesson_progress lp WHERE lp.enrollment_id=p_enrollment AND lp.lesson_id=l.lesson_id);
 SELECT COUNT(*) INTO missing_quizzes FROM quizzes q JOIN lessons l ON l.lesson_id=q.lesson_id
 JOIN modules m ON m.module_id=l.module_id JOIN enrollments e ON e.course_id=m.course_id
 WHERE e.enrollment_id=p_enrollment AND q.required_for_completion=1 AND NOT EXISTS
 (SELECT 1 FROM attempts a WHERE a.enrollment_id=p_enrollment AND a.quiz_id=q.quiz_id
 AND a.status='SUBMITTED' AND a.score/q.max_score>=0.60);
 SELECT final_score INTO pct FROM grades WHERE enrollment_id=p_enrollment AND published=1;
 IF missing_lessons=0 AND missing_quizzes=0 AND COALESCE(pct,0)>=60 THEN
  UPDATE completions SET completion_status='COMPLETED',completed_at=NOW() WHERE enrollment_id=p_enrollment;
  UPDATE enrollments SET status='COMPLETED' WHERE enrollment_id=p_enrollment;
 ELSE
  UPDATE completions SET completion_status='IN_PROGRESS',completed_at=NULL WHERE enrollment_id=p_enrollment;
 END IF;
END;
DELIMITER ;
