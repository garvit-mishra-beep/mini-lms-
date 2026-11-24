-- MiniLMS Privilege Validation & Security Policy Enforcement Tests
-- Executes verification tests ensuring least-privilege roles cannot execute forbidden operations.

-- Test 1: Verify 'minilms_reporter' cannot execute INSERT, UPDATE, or DELETE
-- Expected Result: ERROR 1142 (42000): INSERT/UPDATE/DELETE command denied to user 'minilms_reporter'@'localhost'
-- INSERT INTO `minilms_db`.`courses` (course_code, title) VALUES ('FAIL101', 'Illegal Course');

-- Test 2: Verify 'minilms_audit' cannot read student grades or modify audit logs
-- Expected Result: ERROR 1142 (42000): SELECT command denied to user 'minilms_audit'@'localhost' for table 'grades'
-- SELECT * FROM `minilms_db`.`grades`;
-- DELETE FROM `minilms_db`.`audit_logs`;

-- Test 3: Verify 'app_runtime_role' cannot delete from audit_logs (enforced by trigger & grant)
-- Expected Result: SQLSTATE 45000: Audit logs are immutable and cannot be deleted.
