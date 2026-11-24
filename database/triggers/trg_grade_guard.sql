-- Database Trigger: trg_grade_guard
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_grade_guard` BEFORE UPDATE ON `grades` FOR EACH ROW BEGIN
 IF OLD.published=1 AND (OLD.final_score<>NEW.final_score OR OLD.letter_grade<>NEW.letter_grade)
 AND COALESCE(@grade_change_approved,0)<>1 THEN
   SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Use authorized correction procedure for published grades';
 END IF;
END;
DELIMITER ;
