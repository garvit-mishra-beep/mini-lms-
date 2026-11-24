-- ==============================================================================
-- MiniLMS Rollback v012: Performance Optimization Workload Indexes
-- ==============================================================================

SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;

ALTER TABLE `attendance_records` DROP INDEX IF EXISTS `idx_att_rec_perf_covering`;
ALTER TABLE `enrollments` DROP INDEX IF EXISTS `idx_enr_offering_status_perf`;
ALTER TABLE `grades` DROP INDEX IF EXISTS `idx_grades_ranking_perf`;
ALTER TABLE `submissions` DROP INDEX IF EXISTS `idx_sub_assign_enr_status`;
ALTER TABLE `academic_risks` DROP INDEX IF EXISTS `idx_academic_risk_perf`;

DELETE FROM `schema_versions` WHERE `version_no` = 12;

SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
