-- Database Trigger: trg_prerequisite_validate
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_prerequisite_validate` BEFORE INSERT ON `lesson_prerequisites` FOR EACH ROW BEGIN
 DECLARE c1 INT; DECLARE c2 INT;
 SELECT m.course_id INTO c1 FROM lessons l JOIN modules m ON m.module_id=l.module_id WHERE l.lesson_id=NEW.lesson_id;
 SELECT m.course_id INTO c2 FROM lessons l JOIN modules m ON m.module_id=l.module_id WHERE l.lesson_id=NEW.prerequisite_lesson_id;
 IF c1<>c2 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Prerequisites must be in the same course'; END IF;
 
 IF EXISTS (
  WITH RECURSIVE chain(id) AS (
    SELECT prerequisite_lesson_id FROM lesson_prerequisites WHERE lesson_id=NEW.prerequisite_lesson_id
    UNION DISTINCT
    SELECT lp.prerequisite_lesson_id FROM lesson_prerequisites lp JOIN chain c ON lp.lesson_id=c.id
  ) SELECT 1 FROM chain WHERE id=NEW.lesson_id
 ) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Cyclic lesson prerequisite'; END IF;
END;
DELIMITER ;
