-- Database Trigger: trg_grade_history
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_grade_history` AFTER UPDATE ON `grades` FOR EACH ROW BEGIN
 IF OLD.published=1 AND (OLD.final_score<>NEW.final_score OR OLD.letter_grade<>NEW.letter_grade) THEN
  INSERT INTO grade_change_history(grade_id,changed_by,old_score,new_score,reason)
  VALUES(OLD.grade_id,@grade_actor,OLD.final_score,NEW.final_score,@grade_reason);
 END IF;
END;
DELIMITER ;
