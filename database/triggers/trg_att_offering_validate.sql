-- Database Trigger: trg_att_offering_validate
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_att_offering_validate` BEFORE INSERT ON `attendance_records` FOR EACH ROW BEGIN
    DECLARE v_sess_offering INT UNSIGNED;
    DECLARE v_enroll_offering INT UNSIGNED;
    
    SELECT offering_id INTO v_sess_offering FROM `attendance_sessions` WHERE session_id = NEW.session_id;
    SELECT offering_id INTO v_enroll_offering FROM `enrollments` WHERE enrollment_id = NEW.enrollment_id;
    
    IF v_sess_offering IS NOT NULL AND v_enroll_offering IS NOT NULL AND v_sess_offering <> v_enroll_offering THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cross-course data contamination: Attendance session and enrollment offerings do not match';
    END IF;
END;
DELIMITER ;
