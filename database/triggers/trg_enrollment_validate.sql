-- Database Trigger: trg_enrollment_validate
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_enrollment_validate` BEFORE INSERT ON `enrollments` FOR EACH ROW BEGIN
 IF NOT EXISTS(SELECT 1 FROM students s JOIN users u ON u.user_id=s.user_id
               WHERE s.student_id=NEW.student_id AND u.status='ACTIVE') THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Only active students may enroll'; END IF;
 IF NOT EXISTS(SELECT 1 FROM courses WHERE course_id=NEW.course_id AND status='PUBLISHED') THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Course is not published'; END IF;
END;
DELIMITER ;
