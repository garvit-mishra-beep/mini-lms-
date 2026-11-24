-- Relational View: v_audit_summary_masked
-- MiniLMS Database Engineering
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_audit_summary_masked` AS select `al`.`audit_id` AS `audit_id`,`al`.`action_time` AS `action_time`,`al`.`action_type` AS `action_type`,`al`.`entity_name` AS `entity_name`,`al`.`entity_id` AS `entity_id`,`u`.`role` AS `actor_role`,'***.***.***.***' AS `masked_client_ip`,`al`.`details` AS `details` from (`audit_logs` `al` left join `users` `u` on((`al`.`performed_by` = `u`.`user_id`)));
