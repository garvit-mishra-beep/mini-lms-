-- Relational View: v_course_enrollments
-- MiniLMS Database Engineering
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_course_enrollments` AS select `c`.`course_id` AS `course_id`,`c`.`course_code` AS `course_code`,`c`.`title` AS `title`,count(`e`.`enrollment_id`) AS `total_enrollments` from (`courses` `c` left join `enrollments` `e` on((`e`.`course_id` = `c`.`course_id`))) group by `c`.`course_id`,`c`.`course_code`,`c`.`title`;
