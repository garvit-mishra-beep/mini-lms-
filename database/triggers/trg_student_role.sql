-- Database Trigger: trg_student_role
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_student_role` BEFORE INSERT ON `students` FOR EACH ROW BEGIN
 IF NOT EXISTS(SELECT 1 FROM users WHERE user_id=NEW.user_id AND role='STUDENT') THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Student profile needs a STUDENT user'; END IF;
END;
DELIMITER ;
