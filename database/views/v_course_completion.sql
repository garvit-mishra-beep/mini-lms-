-- Relational View: v_course_completion
-- MiniLMS Database Engineering
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_course_completion` AS select `c`.`course_code` AS `course_code`,count(`co`.`enrollment_id`) AS `enrollments_with_completion_record`,sum((`co`.`completion_status` = 'COMPLETED')) AS `completed_count` from ((`courses` `c` left join `enrollments` `e` on((`e`.`course_id` = `c`.`course_id`))) left join `completions` `co` on((`co`.`enrollment_id` = `e`.`enrollment_id`))) group by `c`.`course_id`,`c`.`course_code`;
