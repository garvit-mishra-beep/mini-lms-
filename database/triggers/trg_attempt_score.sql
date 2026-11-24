-- Database Trigger: trg_attempt_score
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_attempt_score` BEFORE UPDATE ON `attempts` FOR EACH ROW BEGIN
 DECLARE max_allowed DECIMAL(8,2);
 SELECT max_score INTO max_allowed FROM quizzes WHERE quiz_id=NEW.quiz_id;
 IF NEW.score IS NOT NULL AND (NEW.score < 0 OR NEW.score > max_allowed) THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Score exceeds quiz maximum'; END IF;
 IF OLD.status='SUBMITTED' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Submitted attempt is immutable'; END IF;
 IF NEW.status='SUBMITTED' AND (NEW.score IS NULL OR NEW.submitted_at IS NULL) THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Submission needs score and timestamp'; END IF;
END;
DELIMITER ;
