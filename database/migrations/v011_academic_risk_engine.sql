-- MiniLMS Migration v011: Intelligent Academic Early Warning & Risk Detection Engine
-- Adds academic_risks table, scoring stored function, evaluation stored procedure, and analytical view.

SET FOREIGN_KEY_CHECKS = 0;

-- 1. Create Academic Risks Table
CREATE TABLE IF NOT EXISTS `academic_risks` (
  `risk_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `student_id` INT NOT NULL,
  `offering_id` INT UNSIGNED NOT NULL,
  `attendance_pct` DECIMAL(5,2) NOT NULL DEFAULT 100.00,
  `assessment_pct` DECIMAL(5,2) NOT NULL DEFAULT 100.00,
  `overdue_count` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  `risk_score` DECIMAL(5,2) NOT NULL DEFAULT 0.00,
  `risk_classification` ENUM('LOW','MODERATE','HIGH','INSUFFICIENT_DATA') NOT NULL DEFAULT 'LOW',
  `data_sufficiency` ENUM('SUFFICIENT','INSUFFICIENT_DATA') NOT NULL DEFAULT 'SUFFICIENT',
  `explanation` TEXT NOT NULL,
  `review_status` ENUM('PENDING','CONFIRMED','DISMISSED','INTERVENTION_PLANNED') NOT NULL DEFAULT 'PENDING',
  `reviewer_id` INT DEFAULT NULL,
  `review_notes` TEXT DEFAULT NULL,
  `reviewed_at` TIMESTAMP NULL DEFAULT NULL,
  `rule_version` VARCHAR(20) NOT NULL DEFAULT 'v1.0',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`risk_id`),
  UNIQUE KEY `UK_student_offering_risk` (`student_id`, `offering_id`),
  KEY `idx_risk_class` (`risk_classification`),
  KEY `idx_risk_review` (`review_status`),
  CONSTRAINT `FK_risk_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`) ON DELETE CASCADE,
  CONSTRAINT `FK_risk_offering` FOREIGN KEY (`offering_id`) REFERENCES `course_offerings` (`offering_id`) ON DELETE CASCADE,
  CONSTRAINT `FK_risk_reviewer` FOREIGN KEY (`reviewer_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Stored Function: Calculate Composite Academic Risk Score
DROP FUNCTION IF EXISTS `fn_calculate_risk_score`;
DELIMITER //
CREATE FUNCTION `fn_calculate_risk_score`(
    p_att_pct DECIMAL(5,2),
    p_grade_pct DECIMAL(5,2),
    p_overdue_count INT
) RETURNS DECIMAL(5,2)
DETERMINISTIC
BEGIN
    DECLARE v_att_deficit DECIMAL(7,2);
    DECLARE v_grade_deficit DECIMAL(7,2);
    DECLARE v_overdue_factor DECIMAL(7,2);
    DECLARE v_composite DECIMAL(7,2);

    -- Attendance Deficit: max(0, (75.0 - att_pct) / 75.0 * 100)
    IF p_att_pct < 75.00 THEN
        SET v_att_deficit = ((75.00 - p_att_pct) / 75.00) * 100.00;
    ELSE
        SET v_att_deficit = 0.00;
    END IF;

    -- Grade Deficit: max(0, (50.0 - grade_pct) / 50.0 * 100)
    IF p_grade_pct < 50.00 THEN
        SET v_grade_deficit = ((50.00 - p_grade_pct) / 50.00) * 100.00;
    ELSE
        SET v_grade_deficit = 0.00;
    END IF;

    -- Overdue Factor: min(100, overdue_count * 25.0)
    SET v_overdue_factor = LEAST(100.00, p_overdue_count * 25.00);

    -- Composite Weighted Score: 40% Attendance + 40% Grade + 20% Overdue
    SET v_composite = (0.40 * v_att_deficit) + (0.40 * v_grade_deficit) + (0.20 * v_overdue_factor);

    RETURN LEAST(100.00, GREATEST(0.00, v_composite));
END //
DELIMITER ;

-- 3. Stored Procedure: Assess and Persist Student Academic Risk
DROP PROCEDURE IF EXISTS `sp_assess_student_academic_risk`;
DELIMITER //
CREATE PROCEDURE `sp_assess_student_academic_risk`(
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

    -- 1. Fetch attendance metrics
    SELECT COALESCE(e.total_attendance_pct, 100.00)
    INTO v_att_pct
    FROM `enrollments` e
    WHERE e.student_id = p_student_id AND e.offering_id = p_offering_id AND e.status = 'ACTIVE'
    LIMIT 1;

    -- Count total lecture sessions held in this offering
    SELECT COUNT(*) INTO v_total_sessions
    FROM `attendance_sessions`
    WHERE `offering_id` = p_offering_id;

    -- 2. Fetch assessment metrics (from evaluated submissions)
    SELECT 
        COALESCE(AVG((s.marks_obtained / NULLIF(a.max_marks, 0)) * 100), 100.00)
    INTO v_grade_pct
    FROM `submissions` s
    JOIN `assignments` a ON s.assignment_id = a.assignment_id
    JOIN `enrollments` e ON s.enrollment_id = e.enrollment_id
    WHERE e.student_id = p_student_id AND a.offering_id = p_offering_id AND s.status = 'EVALUATED';

    -- Count overdue/unsubmitted assignments past due date
    SELECT COUNT(*) INTO v_overdue_count
    FROM `assignments` a
    JOIN `enrollments` e ON a.offering_id = e.offering_id
    LEFT JOIN `submissions` s ON a.assignment_id = s.assignment_id AND s.enrollment_id = e.enrollment_id
    WHERE e.student_id = p_student_id 
      AND a.offering_id = p_offering_id
      AND a.due_date < NOW()
      AND (s.submission_id IS NULL OR s.status IN ('SUBMITTED', 'RESUBMITTED'));

    -- 3. Cold-Start Check: Insufficient data if fewer than 3 sessions held
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

    -- Upsert into academic_risks table
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
END //
DELIMITER ;

-- 4. Analytical View: Academic Risk Summary
CREATE OR REPLACE VIEW `v_academic_risk_summary` AS
SELECT 
    ar.risk_id,
    ar.student_id,
    s.roll_no,
    u.full_name AS student_name,
    u.email AS student_email,
    d.department_code,
    c.course_code,
    c.title AS course_title,
    co.section_name,
    ar.attendance_pct,
    ar.assessment_pct,
    ar.overdue_count,
    ar.risk_score,
    ar.risk_classification,
    ar.data_sufficiency,
    ar.explanation,
    ar.review_status,
    rev.full_name AS reviewer_name,
    ar.review_notes,
    ar.reviewed_at,
    ar.created_at AS assessed_at
FROM `academic_risks` ar
JOIN `students` s ON ar.student_id = s.student_id
JOIN `users` u ON s.user_id = u.user_id
JOIN `course_offerings` co ON ar.offering_id = co.offering_id
JOIN `courses` c ON co.course_id = c.course_id
LEFT JOIN `departments` d ON u.department_id = d.department_id
LEFT JOIN `users` rev ON ar.reviewer_id = rev.user_id;

-- 5. Record Migration in schema_versions
INSERT INTO `schema_versions` (`version_no`, `description`)
VALUES (11, 'Intelligent Academic Early Warning & Risk Detection Engine')
ON DUPLICATE KEY UPDATE `applied_at` = NOW();

SET FOREIGN_KEY_CHECKS = 1;
