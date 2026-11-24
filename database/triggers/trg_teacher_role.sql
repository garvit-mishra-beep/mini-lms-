-- Database Trigger: trg_teacher_role
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_teacher_role` BEFORE INSERT ON `teachers` FOR EACH ROW BEGIN
 IF NOT EXISTS(SELECT 1 FROM users WHERE user_id=NEW.user_id AND role='TEACHER') THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Teacher profile needs a TEACHER user'; END IF;
END;
DELIMITER ;
