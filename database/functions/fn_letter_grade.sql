-- Stored Function: fn_letter_grade
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` FUNCTION `fn_letter_grade`(p_score DECIMAL(6,2)) RETURNS varchar(2) CHARSET utf8mb4
    NO SQL
    DETERMINISTIC
BEGIN
 RETURN CASE WHEN p_score>=90 THEN 'A' WHEN p_score>=75 THEN 'B'
 WHEN p_score>=60 THEN 'C' WHEN p_score>=40 THEN 'D' ELSE 'F' END;
END;
DELIMITER ;
