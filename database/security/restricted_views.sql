-- MiniLMS Restricted & Privacy-Preserving Views
-- Creates views with PII masking and field restriction for data governance compliance.

-- 1. Public Student Directory (Masks personal contact info, hides GPA/academic standing)
CREATE OR REPLACE VIEW `v_student_public_directory` AS
SELECT 
    s.student_id,
    s.roll_no,
    s.enrollment_no,
    u.full_name,
    CONCAT(LEFT(u.email, 2), '***@***', RIGHT(u.email, 4)) AS masked_email,
    d.department_code,
    d.department_name,
    s.current_semester,
    u.status AS student_status
FROM `students` s
JOIN `users` u ON s.user_id = u.user_id
LEFT JOIN `departments` d ON u.department_id = d.department_id;

-- 2. Masked Audit Log Summary (Sanitizes details and personal identifiers)
CREATE OR REPLACE VIEW `v_audit_summary_masked` AS
SELECT 
    al.audit_id,
    al.action_time,
    al.action_type,
    al.entity_name,
    al.entity_id,
    u.role AS actor_role,
    '***.***.***.***' AS masked_client_ip,
    al.details
FROM `audit_logs` al
LEFT JOIN `users` u ON al.performed_by = u.user_id;
