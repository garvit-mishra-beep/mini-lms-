-- Database Trigger: trg_course_publish
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_course_publish` BEFORE UPDATE ON `courses` FOR EACH ROW BEGIN
 IF NEW.status='PUBLISHED' AND (OLD.status <> 'PUBLISHED')
 AND NOT EXISTS(SELECT 1 FROM course_instructors WHERE course_id=OLD.course_id AND is_authorized=1) THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='A published course needs an authorized instructor'; END IF;
END;
DELIMITER ;
