-- Database Trigger: trg_attempt_audit
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_attempt_audit` AFTER UPDATE ON `attempts` FOR EACH ROW BEGIN
 IF OLD.status <> NEW.status AND NEW.status='SUBMITTED' THEN
  INSERT INTO audit_logs(entity_name,entity_id,action_type,performed_by,details)
  SELECT 'attempts',NEW.attempt_id,'SUBMITTED',s.user_id,CONCAT('score=',NEW.score)
  FROM enrollments e JOIN students s ON s.student_id=e.student_id WHERE e.enrollment_id=NEW.enrollment_id;
 END IF;
END;
DELIMITER ;
