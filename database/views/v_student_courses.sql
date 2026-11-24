-- Relational View: v_student_courses
-- MiniLMS Database Engineering
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_student_courses` AS select `s`.`student_id` AS `student_id`,`u`.`full_name` AS `full_name`,`c`.`course_code` AS `course_code`,`c`.`title` AS `title`,`e`.`enrollment_id` AS `enrollment_id`,`e`.`status` AS `status` from (((`enrollments` `e` join `students` `s` on((`s`.`student_id` = `e`.`student_id`))) join `users` `u` on((`u`.`user_id` = `s`.`user_id`))) join `courses` `c` on((`c`.`course_id` = `e`.`course_id`)));
