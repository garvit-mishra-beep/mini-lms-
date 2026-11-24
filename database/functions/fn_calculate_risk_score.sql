-- Stored Function: fn_calculate_risk_score
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` FUNCTION `fn_calculate_risk_score`(
        p_att_pct DECIMAL(5,2),
        p_grade_pct DECIMAL(5,2),
        p_overdue_count INT
    ) RETURNS decimal(5,2)
    DETERMINISTIC
BEGIN
        DECLARE v_att_deficit DECIMAL(7,2);
        DECLARE v_grade_deficit DECIMAL(7,2);
        DECLARE v_overdue_factor DECIMAL(7,2);
        DECLARE v_composite DECIMAL(7,2);

        IF p_att_pct < 75.00 THEN
            SET v_att_deficit = ((75.00 - p_att_pct) / 75.00) * 100.00;
        ELSE
            SET v_att_deficit = 0.00;
        END IF;

        IF p_grade_pct < 50.00 THEN
            SET v_grade_deficit = ((50.00 - p_grade_pct) / 50.00) * 100.00;
        ELSE
            SET v_grade_deficit = 0.00;
        END IF;

        SET v_overdue_factor = LEAST(100.00, p_overdue_count * 25.00);
        SET v_composite = (0.40 * v_att_deficit) + (0.40 * v_grade_deficit) + (0.20 * v_overdue_factor);

        RETURN LEAST(100.00, GREATEST(0.00, v_composite));
    END;
DELIMITER ;
