-- Database Trigger: trg_progress_validate
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_progress_validate` BEFORE INSERT ON `lesson_progress` FOR EACH ROW BEGIN
 DECLARE v_course INT; DECLARE v_lesson_course INT;
 SELECT course_id INTO v_course FROM enrollments WHERE enrollment_id=NEW.enrollment_id;
 SELECT m.course_id INTO v_lesson_course FROM lessons l JOIN modules m ON l.module_id=m.module_id
 WHERE l.lesson_id=NEW.lesson_id;
 IF v_course <> v_lesson_course THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Lesson is not in enrollment course'; END IF;
END;
DELIMITER ;
