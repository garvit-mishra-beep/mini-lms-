-- ==============================================================================
-- MiniLMS Migration v012: Performance Optimization Workload Indexes
-- Database: MySQL 8.0 (InnoDB Storage Engine)
-- Target: High-throughput academic querying across 25,000+ row benchmark dataset
-- ==============================================================================

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;

-- 1. Index 1 (Study 01): Composite covering index for attendance percentage calculation
-- Accelerates GROUP BY and status aggregation on attendance_records
DROP PROCEDURE IF EXISTS _create_perf_idx_1;
DELIMITER //
CREATE PROCEDURE _create_perf_idx_1()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.statistics 
        WHERE table_schema = DATABASE() 
          AND table_name = 'attendance_records' 
          AND index_name = 'idx_att_rec_perf_covering'
    ) THEN
        CREATE INDEX `idx_att_rec_perf_covering` ON `attendance_records` (`enrollment_id`, `status`, `session_id`);
    END IF;
END //
DELIMITER ;
CALL _create_perf_idx_1();
DROP PROCEDURE _create_perf_idx_1;

-- 2. Index 2 (Study 02): Composite index on enrollments for section capacity aggregation
-- Enables fast index-only scanning for active offering enrollments
DROP PROCEDURE IF EXISTS _create_perf_idx_2;
DELIMITER //
CREATE PROCEDURE _create_perf_idx_2()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.statistics 
        WHERE table_schema = DATABASE() 
          AND table_name = 'enrollments' 
          AND index_name = 'idx_enr_offering_status_perf'
    ) THEN
        CREATE INDEX `idx_enr_offering_status_perf` ON `enrollments` (`offering_id`, `status`, `student_id`);
    END IF;
END //
DELIMITER ;
CALL _create_perf_idx_2();
DROP PROCEDURE _create_perf_idx_2;

-- 3. Index 3 (Study 03): Composite index for window function academic ranking
-- Accelerates final_score sorting and enrollment joining in DENSE_RANK()
DROP PROCEDURE IF EXISTS _create_perf_idx_3;
DELIMITER //
CREATE PROCEDURE _create_perf_idx_3()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.statistics 
        WHERE table_schema = DATABASE() 
          AND table_name = 'grades' 
          AND index_name = 'idx_grades_ranking_perf'
    ) THEN
        CREATE INDEX `idx_grades_ranking_perf` ON `grades` (`enrollment_id`, `final_score` DESC);
    END IF;
END //
DELIMITER ;
CALL _create_perf_idx_3();
DROP PROCEDURE _create_perf_idx_3;

-- 4. Index 4 (Study 04): Composite index for anti-join pending submission detection
-- Accelerates NOT EXISTS / LEFT JOIN checks for assignment submissions
DROP PROCEDURE IF EXISTS _create_perf_idx_4;
DELIMITER //
CREATE PROCEDURE _create_perf_idx_4()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.statistics 
        WHERE table_schema = DATABASE() 
          AND table_name = 'submissions' 
          AND index_name = 'idx_sub_assign_enr_status'
    ) THEN
        CREATE INDEX `idx_sub_assign_enr_status` ON `submissions` (`assignment_id`, `enrollment_id`, `status`);
    END IF;
END //
DELIMITER ;
CALL _create_perf_idx_4();
DROP PROCEDURE _create_perf_idx_4;

-- 5. Index 5 (Study 05): Filtered index for academic risk alert scanning & executive dashboard
-- Accelerates filtering on risk_classification and sorting by risk_score
DROP PROCEDURE IF EXISTS _create_perf_idx_5;
DELIMITER //
CREATE PROCEDURE _create_perf_idx_5()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.statistics 
        WHERE table_schema = DATABASE() 
          AND table_name = 'academic_risks' 
          AND index_name = 'idx_academic_risk_perf'
    ) THEN
        CREATE INDEX `idx_academic_risk_perf` ON `academic_risks` (`risk_classification`, `risk_score` DESC, `student_id`, `offering_id`);
    END IF;
END //
DELIMITER ;
CALL _create_perf_idx_5();
DROP PROCEDURE _create_perf_idx_5;

-- 6. Record Migration in schema_versions
INSERT INTO `schema_versions` (`version_no`, `description`)
VALUES (12, 'Performance Optimization Workload Indexes')
ON DUPLICATE KEY UPDATE `applied_at` = NOW();

SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
