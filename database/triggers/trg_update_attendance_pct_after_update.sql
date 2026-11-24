-- Database Trigger: trg_update_attendance_pct_after_update
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_update_attendance_pct_after_update` AFTER UPDATE ON `attendance_records` FOR EACH ROW BEGIN
    DECLARE v_total_sessions INT UNSIGNED DEFAULT 0;
    DECLARE v_attended_sessions INT UNSIGNED DEFAULT 0;
    DECLARE v_new_pct DECIMAL(5,2) DEFAULT 100.00;

    SELECT 
        COUNT(*),
        COALESCE(SUM(CASE WHEN `status` IN ('PRESENT', 'EXCUSED') THEN 1 ELSE 0 END), 0)
    INTO v_total_sessions, v_attended_sessions
    FROM `attendance_records`
    WHERE `enrollment_id` = NEW.enrollment_id;

    IF v_total_sessions > 0 THEN
        SET v_new_pct = ROUND((v_attended_sessions * 100.0) / v_total_sessions, 2);
    ELSE
        SET v_new_pct = 100.00;
    END IF;

    UPDATE `enrollments`
    SET `total_attendance_pct` = v_new_pct
    WHERE `enrollment_id` = NEW.enrollment_id;
END;
DELIMITER ;
