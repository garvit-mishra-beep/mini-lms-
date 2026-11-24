-- Relational View: v_quiz_performance
-- MiniLMS Database Engineering
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_quiz_performance` AS select `q`.`quiz_id` AS `quiz_id`,`q`.`title` AS `title`,count(`a`.`attempt_id`) AS `submissions`,round(avg(`a`.`score`),2) AS `average_score`,`q`.`max_score` AS `max_score` from (`quizzes` `q` left join `attempts` `a` on(((`a`.`quiz_id` = `q`.`quiz_id`) and (`a`.`status` = 'SUBMITTED')))) group by `q`.`quiz_id`,`q`.`title`,`q`.`max_score`;
