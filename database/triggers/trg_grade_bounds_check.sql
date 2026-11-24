-- Database Trigger: trg_grade_bounds_check
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_grade_bounds_check` BEFORE INSERT ON `grades` FOR EACH ROW BEGIN
    DECLARE v_max_marks DECIMAL(5,2);
    IF NEW.submission_id IS NOT NULL THEN
        SELECT a.max_marks INTO v_max_marks
        FROM `submissions` s
        JOIN `assignments` a ON s.assignment_id = a.assignment_id
        WHERE s.submission_id = NEW.submission_id;
        
        IF v_max_marks IS NOT NULL AND NEW.final_score > v_max_marks THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Awarded marks cannot exceed assignment maximum marks ceiling';
        END IF;
    END IF;
END;
DELIMITER ;
