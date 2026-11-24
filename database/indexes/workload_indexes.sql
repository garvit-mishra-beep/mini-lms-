-- ==============================================================================
-- MiniLMS Stage 4: Five Meaningful Workload Optimization Indexes
-- Database: MySQL 8.0 (InnoDB Storage Engine)
-- Target: High-throughput academic querying across 25,000+ row benchmark dataset
-- ==============================================================================

-- Index 1 (Study 01): Composite covering index for attendance percentage calculation
-- Accelerates GROUP BY and status aggregation on attendance_records
CREATE INDEX idx_att_rec_perf_covering 
ON attendance_records (enrollment_id, status, session_id);

-- Index 2 (Study 02): Composite index on enrollments for section capacity aggregation
-- Enables fast index-only scanning for active offering enrollments
CREATE INDEX idx_enr_offering_status_perf 
ON enrollments (offering_id, status, student_id);

-- Index 3 (Study 03): Composite index for window function academic ranking
-- Accelerates final_score sorting and enrollment joining in DENSE_RANK()
CREATE INDEX idx_grades_ranking_perf 
ON grades (enrollment_id, final_score DESC);

-- Index 4 (Study 04): Composite index for anti-join pending submission detection
-- Accelerates NOT EXISTS / LEFT JOIN checks for assignment submissions
CREATE INDEX idx_sub_assign_enr_status 
ON submissions (assignment_id, enrollment_id, status);

-- Index 5 (Study 05): Filtered index for academic risk alert scanning & executive dashboard
-- Accelerates filtering on risk_classification and sorting by risk_score
CREATE INDEX idx_academic_risk_perf 
ON academic_risks (risk_classification, risk_score DESC, student_id, offering_id);
