-- Relational View: faculty
-- MiniLMS Database Engineering
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `faculty` AS select `teachers`.`teacher_id` AS `faculty_id`,`teachers`.`user_id` AS `user_id`,`teachers`.`employee_code` AS `employee_code`,`teachers`.`qualification` AS `qualification`,`teachers`.`bio` AS `bio`,`teachers`.`phone_no` AS `phone_no` from `teachers`;
