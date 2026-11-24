-- Database Trigger: trg_audit_logs_no_delete
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_audit_logs_no_delete` BEFORE DELETE ON `audit_logs` FOR EACH ROW BEGIN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Security Violation: Audit log records cannot be deleted';
END;
DELIMITER ;
