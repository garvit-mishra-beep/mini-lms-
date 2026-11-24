-- Database Trigger: trg_course_instructor_remove
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_course_instructor_remove` BEFORE DELETE ON `course_instructors` FOR EACH ROW BEGIN
 IF (SELECT status FROM courses WHERE course_id=OLD.course_id)='PUBLISHED'
 AND OLD.is_authorized=1
 AND (SELECT COUNT(*) FROM course_instructors WHERE course_id=OLD.course_id AND is_authorized=1) <= 1 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Cannot remove final authorized instructor'; END IF;
END;
DELIMITER ;
