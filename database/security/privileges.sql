-- MiniLMS User Identities & Least-Privilege Role Bindings
-- Creates dedicated MySQL database accounts and binds them to their respective roles.

-- 1. User: minilms_app (Application Runtime Service Account)
CREATE USER IF NOT EXISTS 'minilms_app'@'localhost' IDENTIFIED BY 'MiniLMS_App_Pass#2026';
GRANT 'app_runtime_role' TO 'minilms_app'@'localhost';
SET DEFAULT ROLE 'app_runtime_role' TO 'minilms_app'@'localhost';

-- 2. User: minilms_reporter (Reporting & BI Analytic Identity)
CREATE USER IF NOT EXISTS 'minilms_reporter'@'localhost' IDENTIFIED BY 'MiniLMS_Report_Pass#2026';
GRANT 'reporting_role' TO 'minilms_reporter'@'localhost';
SET DEFAULT ROLE 'reporting_role' TO 'minilms_reporter'@'localhost';

-- 3. User: minilms_audit (Compliance & Security Auditor Identity)
CREATE USER IF NOT EXISTS 'minilms_audit'@'localhost' IDENTIFIED BY 'MiniLMS_Audit_Pass#2026';
GRANT 'audit_role' TO 'minilms_audit'@'localhost';
SET DEFAULT ROLE 'audit_role' TO 'minilms_audit'@'localhost';

FLUSH PRIVILEGES;
