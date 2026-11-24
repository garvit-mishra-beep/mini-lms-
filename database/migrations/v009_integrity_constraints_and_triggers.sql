-- MiniLMS Migration v009: Business Integrity Constraints and Automated Triggers
-- Adds MySQL 8.0 CHECK constraints, cross-table integrity triggers,
-- single-ownership counter sync, and audit immutability guards.

SET FOREIGN_KEY_CHECKS = 0;

-- 1. Add CHECK constraints (safely checking if not already present)
ALTER TABLE `students`
  ADD CONSTRAINT `chk_student_cgpa` CHECK (`cgpa` >= 0.00 AND `cgpa` <= 10.00),
  ADD CONSTRAINT `chk_student_semester` CHECK (`current_semester` BETWEEN 1 AND 8);

ALTER TABLE `courses`
  ADD CONSTRAINT `chk_course_credits` CHECK (`credits` >= 1.0 AND `credits` <= 10.0);

ALTER TABLE `course_offerings`
  ADD CONSTRAINT `chk_offering_capacity` CHECK (`max_capacity` >= 5 AND `max_capacity` <= 300),
  ADD CONSTRAINT `chk_offering_enrolled` CHECK (`enrolled_count` <= `max_capacity`);

ALTER TABLE `academic_terms`
  ADD CONSTRAINT `chk_term_dates` CHECK (`end_date` >= `start_date`);

ALTER TABLE `assignments`
  ADD CONSTRAINT `chk_assignment_marks` CHECK (`max_marks` > 0.00 AND `max_marks` <= 500.00),
  ADD CONSTRAINT `chk_assignment_weightage` CHECK (`weightage_pct` >= 0.00 AND `weightage_pct` <= 100.00);

ALTER TABLE `grades`
  ADD CONSTRAINT `chk_grade_final_score` CHECK (`final_score` >= 0.00);

ALTER TABLE `enrollments`
  ADD CONSTRAINT `chk_enrollment_att_pct` CHECK (`total_attendance_pct` >= 0.00 AND `total_attendance_pct` <= 100.00);

-- 2. Drop existing triggers if re-running
DROP TRIGGER IF EXISTS `trg_grade_bounds_check`;
DROP TRIGGER IF EXISTS `trg_att_offering_validate`;
DROP TRIGGER IF EXISTS `trg_submission_offering_validate`;
DROP TRIGGER IF EXISTS `trg_enrollment_seat_increment`;
DROP TRIGGER IF EXISTS `trg_enrollment_seat_decrement`;
DROP TRIGGER IF EXISTS `trg_update_attendance_pct_after_insert`;
DROP TRIGGER IF EXISTS `trg_update_attendance_pct_after_update`;
DROP TRIGGER IF EXISTS `trg_audit_logs_immutable`;
DROP TRIGGER IF EXISTS `trg_audit_logs_no_delete`;

-- 3. Trigger: Grade Bounds Check against Assignment Max Marks
DELIMITER //
CREATE TRIGGER `trg_grade_bounds_check`
BEFORE INSERT ON `grades`
FOR EACH ROW
BEGIN
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
END //

-- 4. Trigger: Prevent Cross-Course Attendance Contamination
CREATE TRIGGER `trg_att_offering_validate`
BEFORE INSERT ON `attendance_records`
FOR EACH ROW
BEGIN
    DECLARE v_sess_offering INT UNSIGNED;
    DECLARE v_enroll_offering INT UNSIGNED;
    
    SELECT offering_id INTO v_sess_offering FROM `attendance_sessions` WHERE session_id = NEW.session_id;
    SELECT offering_id INTO v_enroll_offering FROM `enrollments` WHERE enrollment_id = NEW.enrollment_id;
    
    IF v_sess_offering IS NOT NULL AND v_enroll_offering IS NOT NULL AND v_sess_offering <> v_enroll_offering THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cross-course data contamination: Attendance session and enrollment offerings do not match';
    END IF;
END //

-- 5. Trigger: Prevent Cross-Course Submission Contamination
CREATE TRIGGER `trg_submission_offering_validate`
BEFORE INSERT ON `submissions`
FOR EACH ROW
BEGIN
    DECLARE v_assign_offering INT UNSIGNED;
    DECLARE v_enroll_offering INT UNSIGNED;
    
    SELECT offering_id INTO v_assign_offering FROM `assignments` WHERE assignment_id = NEW.assignment_id;
    SELECT offering_id INTO v_enroll_offering FROM `enrollments` WHERE enrollment_id = NEW.enrollment_id;
    
    IF v_assign_offering IS NOT NULL AND v_enroll_offering IS NOT NULL AND v_assign_offering <> v_enroll_offering THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cross-course data contamination: Assignment and enrollment offerings do not match';
    END IF;
END //

-- 6. Trigger: Single Counter Ownership - Seat Increment on Enrollment
CREATE TRIGGER `trg_enrollment_seat_increment`
AFTER INSERT ON `enrollments`
FOR EACH ROW
BEGIN
    IF NEW.offering_id IS NOT NULL AND NEW.status = 'ACTIVE' THEN
        UPDATE `course_offerings`
        SET `enrolled_count` = `enrolled_count` + 1
        WHERE `offering_id` = NEW.offering_id;
    END IF;
END //

-- 7. Trigger: Single Counter Ownership - Seat Decrement on Cancellation
CREATE TRIGGER `trg_enrollment_seat_decrement`
AFTER UPDATE ON `enrollments`
FOR EACH ROW
BEGIN
    IF NEW.offering_id IS NOT NULL THEN
        IF OLD.status = 'ACTIVE' AND NEW.status IN ('CANCELLED', 'DROPPED') THEN
            UPDATE `course_offerings`
            SET `enrolled_count` = GREATEST(0, CAST(`enrolled_count` AS SIGNED) - 1)
            WHERE `offering_id` = NEW.offering_id;
        ELSEIF OLD.status IN ('CANCELLED', 'DROPPED') AND NEW.status = 'ACTIVE' THEN
            UPDATE `course_offerings`
            SET `enrolled_count` = `enrolled_count` + 1
            WHERE `offering_id` = NEW.offering_id;
        END IF;
    END IF;
END //

-- 8. Triggers: Real-time Attendance Percentage Auto-Recalculation
CREATE TRIGGER `trg_update_attendance_pct_after_insert`
AFTER INSERT ON `attendance_records`
FOR EACH ROW
BEGIN
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
END //

CREATE TRIGGER `trg_update_attendance_pct_after_update`
AFTER UPDATE ON `attendance_records`
FOR EACH ROW
BEGIN
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
END //

-- 9. Triggers: Audit Logs Immutability Guards
CREATE TRIGGER `trg_audit_logs_immutable`
BEFORE UPDATE ON `audit_logs`
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Security Violation: Audit log records are immutable and cannot be updated';
END //

CREATE TRIGGER `trg_audit_logs_no_delete`
BEFORE DELETE ON `audit_logs`
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Security Violation: Audit log records cannot be deleted';
END //

DELIMITER ;

-- Record Migration v009 in schema_versions
INSERT INTO `schema_versions` (`version_no`, `description`, `applied_at`)
VALUES (9, 'Integrity constraints: 9 CHECKs, grade bounds, cross-course guards, seat counter triggers, audit immutability', NOW())
ON DUPLICATE KEY UPDATE `applied_at` = NOW();

SET FOREIGN_KEY_CHECKS = 1;
