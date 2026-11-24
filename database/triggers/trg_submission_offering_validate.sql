-- Database Trigger: trg_submission_offering_validate
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_submission_offering_validate` BEFORE INSERT ON `submissions` FOR EACH ROW BEGIN
    DECLARE v_assign_offering INT UNSIGNED;
    DECLARE v_enroll_offering INT UNSIGNED;
    
    SELECT offering_id INTO v_assign_offering FROM `assignments` WHERE assignment_id = NEW.assignment_id;
    SELECT offering_id INTO v_enroll_offering FROM `enrollments` WHERE enrollment_id = NEW.enrollment_id;
    
    IF v_assign_offering IS NOT NULL AND v_enroll_offering IS NOT NULL AND v_assign_offering <> v_enroll_offering THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cross-course data contamination: Assignment and enrollment offerings do not match';
    END IF;
END;
DELIMITER ;
