-- Database Trigger: trg_enrollment_audit
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_enrollment_audit` AFTER INSERT ON `enrollments` FOR EACH ROW BEGIN
 INSERT INTO audit_logs(entity_name,entity_id,action_type,performed_by,details)
 SELECT 'enrollments', NEW.enrollment_id,'ENROLLED',s.user_id,CONCAT('course=',NEW.course_id)
 FROM students s WHERE s.student_id=NEW.student_id;
END;
DELIMITER ;
