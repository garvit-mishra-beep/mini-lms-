-- Database Trigger: trg_attempt_validate
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_attempt_validate` BEFORE INSERT ON `attempts` FOR EACH ROW BEGIN
 DECLARE mx INT; DECLARE t1 DATETIME; DECLARE t2 DATETIME; DECLARE cid INT; DECLARE course_enrolled INT;
 DECLARE lesson INT; DECLARE restricted_flag BOOLEAN; DECLARE released DATETIME;
 SELECT q.allowed_attempts,q.available_from,q.available_until,m.course_id,q.lesson_id,l.is_restricted,l.release_date
 INTO mx,t1,t2,cid,lesson,restricted_flag,released
 FROM quizzes q JOIN lessons l ON l.lesson_id=q.lesson_id JOIN modules m ON m.module_id=l.module_id
 WHERE q.quiz_id=NEW.quiz_id;
 SELECT course_id INTO course_enrolled FROM enrollments WHERE enrollment_id=NEW.enrollment_id AND status='ACTIVE';
 IF course_enrolled IS NULL OR cid<>course_enrolled THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Active course enrollment required'; END IF;
 IF NEW.attempt_no>mx OR NEW.attempt_no <> 1+(SELECT COUNT(*) FROM attempts a WHERE a.quiz_id=NEW.quiz_id AND a.enrollment_id=NEW.enrollment_id) THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Invalid attempt sequence or maximum exceeded'; END IF;
 IF NEW.started_at<t1 OR NEW.started_at>t2 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Quiz outside availability window'; END IF;
 IF released IS NOT NULL AND NEW.started_at<released THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Lesson not released'; END IF;
 IF restricted_flag=1 AND EXISTS (
  SELECT 1 FROM lesson_prerequisites p WHERE p.lesson_id=lesson AND NOT EXISTS (
   SELECT 1 FROM lesson_progress x WHERE x.enrollment_id=NEW.enrollment_id AND x.lesson_id=p.prerequisite_lesson_id
  )
 ) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Lesson prerequisites incomplete'; END IF;
END;
DELIMITER ;
