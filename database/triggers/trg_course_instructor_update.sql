-- Database Trigger: trg_course_instructor_update
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_course_instructor_update` BEFORE UPDATE ON `course_instructors` FOR EACH ROW BEGIN
 IF OLD.is_authorized=1 AND NEW.is_authorized=0
 AND (SELECT status FROM courses WHERE course_id=OLD.course_id)='PUBLISHED'
 AND (SELECT COUNT(*) FROM course_instructors WHERE course_id=OLD.course_id AND is_authorized=1)<=1 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Cannot disable final authorized instructor'; END IF;
END;
DELIMITER ;
