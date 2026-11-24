-- Database Trigger: trg_audit_logs_immutable
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_audit_logs_immutable` BEFORE UPDATE ON `audit_logs` FOR EACH ROW BEGIN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Security Violation: Audit log records are immutable and cannot be updated';
END;
DELIMITER ;
