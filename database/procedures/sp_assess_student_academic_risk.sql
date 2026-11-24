-- Stored Procedure: sp_assess_student_academic_risk
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_assess_student_academic_risk`(
        IN p_student_id INT,
        IN p_offering_id INT,
        OUT p_risk_score DECIMAL(5,2),
        OUT p_classification VARCHAR(20),
        OUT p_explanation TEXT
    )
sp_risk_block: BEGIN
        DECLARE v_att_pct DECIMAL(5,2);
        DECLARE v_total_sessions INT;
        DECLARE v_grade_pct DECIMAL(5,2);
        DECLARE v_overdue_count INT;
        DECLARE v_score DECIMAL(5,2);
        DECLARE v_class VARCHAR(20);
        DECLARE v_suff VARCHAR(20);
        DECLARE v_expl TEXT;

        SELECT COALESCE(e.total_attendance_pct, 100.00)
        INTO v_att_pct
        FROM `enrollments` e
        WHERE e.student_id = p_student_id AND e.offering_id = p_offering_id AND e.status = 'ACTIVE'
        LIMIT 1;

        SELECT COUNT(*) INTO v_total_sessions
        FROM `attendance_sessions`
        WHERE `offering_id` = p_offering_id;

        SELECT 
            COALESCE(AVG((s.marks_obtained / NULLIF(a.max_marks, 0)) * 100), 100.00)
        INTO v_grade_pct
        FROM `submissions` s
        JOIN `assignments` a ON s.assignment_id = a.assignment_id
        JOIN `enrollments` e ON s.enrollment_id = e.enrollment_id
        WHERE e.student_id = p_student_id AND a.offering_id = p_offering_id AND s.status = 'EVALUATED';

        SELECT COUNT(*) INTO v_overdue_count
        FROM `assignments` a
        JOIN `enrollments` e ON a.offering_id = e.offering_id
        LEFT JOIN `submissions` s ON a.assignment_id = s.assignment_id AND s.enrollment_id = e.enrollment_id
        WHERE e.student_id = p_student_id 
          AND a.offering_id = p_offering_id
          AND a.due_date < NOW()
          AND (s.submission_id IS NULL OR s.status IN ('SUBMITTED', 'RESUBMITTED'));

        IF v_total_sessions < 3 THEN
            SET v_suff = 'INSUFFICIENT_DATA';
            SET v_class = 'INSUFFICIENT_DATA';
            SET v_score = 0.00;
            SET v_expl = CONCAT('Course offering has conducted only ', v_total_sessions, ' session(s). Minimum 3 sessions required for reliable risk evaluation.');
        ELSE
            SET v_suff = 'SUFFICIENT';
            SET v_score = fn_calculate_risk_score(v_att_pct, v_grade_pct, v_overdue_count);

            IF v_score >= 60.00 OR v_att_pct < 60.00 THEN
                SET v_class = 'HIGH';
            ELSEIF v_score >= 30.00 THEN
                SET v_class = 'MODERATE';
            ELSE
                SET v_class = 'LOW';
            END IF;

            SET v_expl = CONCAT(
                'Risk Score: ', v_score, ' (Attendance: ', v_att_pct, '%, Avg Grade: ', v_grade_pct, 
                '%, Overdue Assignments: ', v_overdue_count, '). Classification: ', v_class, '.'
            );
        END IF;

        INSERT INTO `academic_risks` 
            (`student_id`, `offering_id`, `attendance_pct`, `assessment_pct`, `overdue_count`, 
             `risk_score`, `risk_classification`, `data_sufficiency`, `explanation`)
        VALUES 
            (p_student_id, p_offering_id, v_att_pct, v_grade_pct, v_overdue_count,
             v_score, v_class, v_suff, v_expl)
        ON DUPLICATE KEY UPDATE
            `attendance_pct` = VALUES(`attendance_pct`),
            `assessment_pct` = VALUES(`assessment_pct`),
            `overdue_count` = VALUES(`overdue_count`),
            `risk_score` = VALUES(`risk_score`),
            `risk_classification` = VALUES(`risk_classification`),
            `data_sufficiency` = VALUES(`data_sufficiency`),
            `explanation` = VALUES(`explanation`),
            `updated_at` = NOW();

        SET p_risk_score = v_score;
        SET p_classification = v_class;
        SET p_explanation = v_expl;
    END;
DELIMITER ;
