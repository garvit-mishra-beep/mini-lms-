-- Stored Procedure: sp_calculate_student_gpa
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_calculate_student_gpa`(
    IN p_student_id INT,
    OUT p_new_cgpa DECIMAL(4,2)
)
BEGIN
    DECLARE v_avg_cgpa DECIMAL(4,2);

    
    SELECT ROUND(AVG(g.final_score) / 10.0, 2) INTO v_avg_cgpa
    FROM `enrollments` e
    JOIN `grades` g ON e.enrollment_id = g.enrollment_id
    WHERE e.student_id = p_student_id AND e.status IN ('ACTIVE', 'COMPLETED');

    IF v_avg_cgpa IS NOT NULL THEN
        UPDATE `students`
        SET `cgpa` = LEAST(10.00, GREATEST(0.00, v_avg_cgpa))
        WHERE `student_id` = p_student_id;
        SET p_new_cgpa = v_avg_cgpa;
    ELSE
        SET p_new_cgpa = 0.00;
    END IF;
END;
DELIMITER ;
