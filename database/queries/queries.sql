-- ==============================================================================
-- MINILMS ADVANCED SQL QUERY PORTFOLIO (25 EXECUTABLE QUERIES)
-- Course: CSL0311 DBMS PBL | ITM University, Gwalior
-- Categories: Operational, Subqueries, CTEs, Window Functions, Rollups, Strategic
-- Engine: MySQL 8.0.36 Community Server
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- OPERATIONAL & ACADEMIC QUERIES (Q01 - Q20)
-- ------------------------------------------------------------------------------

-- Q01: Active Student Enrollment Roster with Department & Offering Details (5-Table JOIN)
SELECT 
    e.enrollment_id,
    s.roll_no,
    u.full_name AS student_name,
    d.department_code,
    c.course_code,
    c.title AS course_title,
    t.term_code,
    co.section_name,
    e.status AS enrollment_status,
    e.total_attendance_pct
FROM enrollments e
JOIN students s ON e.student_id = s.student_id
JOIN users u ON s.user_id = u.user_id
JOIN course_offerings co ON e.offering_id = co.offering_id
JOIN courses c ON co.course_id = c.course_id
JOIN academic_terms t ON co.term_id = t.term_id
LEFT JOIN departments d ON u.department_id = d.department_id
ORDER BY c.course_code, co.section_name, s.roll_no;

-- Q02: Course Offerings with Primary Faculty Allocation & Utilization
SELECT 
    co.offering_id,
    c.course_code,
    c.title AS course_title,
    t.term_code,
    co.section_name,
    co.max_capacity,
    co.enrolled_count,
    ROUND((co.enrolled_count * 100.0) / NULLIF(co.max_capacity, 0), 1) AS utilization_pct,
    COALESCE(u.full_name, 'Unassigned') AS instructor_name,
    COALESCE(fac.employee_code, 'N/A') AS instructor_code
FROM course_offerings co
JOIN courses c ON co.course_id = c.course_id
JOIN academic_terms t ON co.term_id = t.term_id
LEFT JOIN course_instructors ci ON co.offering_id = ci.offering_id AND ci.role_in_course = 'PRIMARY'
LEFT JOIN teachers fac ON ci.teacher_id = fac.teacher_id
LEFT JOIN users u ON fac.user_id = u.user_id
ORDER BY utilization_pct DESC;

-- Q03: Faculty Teaching Workload and Department Allocation
SELECT 
    t.teacher_id,
    t.employee_code,
    u.full_name AS teacher_name,
    d.department_name,
    COUNT(DISTINCT ci.course_id) AS total_courses_assigned,
    COUNT(DISTINCT ci.offering_id) AS total_sections_instructed,
    COALESCE(SUM(c.credits), 0) AS total_credit_load
FROM teachers t
JOIN users u ON t.user_id = u.user_id
LEFT JOIN departments d ON u.department_id = d.department_id
LEFT JOIN course_instructors ci ON t.teacher_id = ci.teacher_id AND ci.is_authorized = 1
LEFT JOIN courses c ON ci.course_id = c.course_id
GROUP BY t.teacher_id, t.employee_code, u.full_name, d.department_name
ORDER BY total_sections_instructed DESC;

-- Q04: Correlated Subquery: Students with Above-Average Attendance in Their Section
SELECT 
    e.enrollment_id,
    s.roll_no,
    u.full_name,
    e.offering_id,
    e.total_attendance_pct
FROM enrollments e
JOIN students s ON e.student_id = s.student_id
JOIN users u ON s.user_id = u.user_id
WHERE e.status = 'ACTIVE'
  AND e.total_attendance_pct > (
      SELECT AVG(sub_e.total_attendance_pct)
      FROM enrollments sub_e
      WHERE sub_e.offering_id = e.offering_id
        AND sub_e.status = 'ACTIVE'
  )
ORDER BY e.offering_id, e.total_attendance_pct DESC;

-- Q05: Scalar Subquery: Offerings with Enrollment Exceeding Overall System Average
SELECT 
    co.offering_id,
    c.course_code,
    c.title,
    co.enrolled_count,
    (SELECT ROUND(AVG(enrolled_count), 2) FROM course_offerings) AS system_average_enrollment
FROM course_offerings co
JOIN courses c ON co.course_id = c.course_id
WHERE co.enrolled_count >= (
    SELECT AVG(enrolled_count) FROM course_offerings
)
ORDER BY co.enrolled_count DESC;

-- Q06: Subquery with NOT EXISTS: Published Courses with No Offerings in Current Term
SELECT 
    c.course_id,
    c.course_code,
    c.title,
    c.credits,
    d.department_code
FROM courses c
LEFT JOIN departments d ON c.department_id = d.department_id
WHERE c.status = 'PUBLISHED'
  AND NOT EXISTS (
      SELECT 1 
      FROM course_offerings co
      JOIN academic_terms t ON co.term_id = t.term_id
      WHERE co.course_id = c.course_id AND t.is_current = 1
  );

-- Q07: Subquery with IN: High-Performing Students (CGPA >= 8.5) and Enrolled Courses
SELECT 
    s.student_id,
    s.roll_no,
    u.full_name,
    s.cgpa,
    c.course_code,
    c.title AS course_title
FROM students s
JOIN users u ON s.user_id = u.user_id
JOIN enrollments e ON s.student_id = e.student_id
JOIN courses c ON e.course_id = c.course_id
WHERE s.student_id IN (
    SELECT student_id FROM students WHERE cgpa >= 8.50
)
ORDER BY s.cgpa DESC, s.roll_no;

-- Q08: Common Table Expression (CTE): Academic Standing Classification
WITH student_academic_standing AS (
    SELECT 
        s.student_id,
        s.roll_no,
        u.full_name,
        s.cgpa,
        CASE 
            WHEN s.cgpa >= 9.00 THEN 'First Class with Distinction'
            WHEN s.cgpa >= 7.50 THEN 'First Class'
            WHEN s.cgpa >= 6.00 THEN 'Second Class'
            ELSE 'Pass / Academic Support Needed'
        END AS standing_tier
    FROM students s
    JOIN users u ON s.user_id = u.user_id
)
SELECT 
    standing_tier,
    COUNT(*) AS student_count,
    ROUND(AVG(cgpa), 2) AS tier_avg_cgpa
FROM student_academic_standing
GROUP BY standing_tier
ORDER BY tier_avg_cgpa DESC;

-- Q09: Multi-Step CTE: Coursework Submission Performance & Evaluation Metrics
WITH submission_metrics AS (
    SELECT 
        a.assignment_id,
        a.title AS assignment_title,
        c.course_code,
        a.max_marks,
        COUNT(s.submission_id) AS total_submissions,
        SUM(CASE WHEN s.status = 'EVALUATED' THEN 1 ELSE 0 END) AS evaluated_submissions,
        AVG(s.marks_obtained) AS avg_raw_marks
    FROM assignments a
    JOIN course_offerings co ON a.offering_id = co.offering_id
    JOIN courses c ON co.course_id = c.course_id
    LEFT JOIN submissions s ON a.assignment_id = s.assignment_id
    GROUP BY a.assignment_id, a.title, c.course_code, a.max_marks
),
calculated_rates AS (
    SELECT 
        assignment_id,
        assignment_title,
        course_code,
        total_submissions,
        evaluated_submissions,
        ROUND((avg_raw_marks / NULLIF(max_marks, 0)) * 100, 2) AS average_score_pct
    FROM submission_metrics
)
SELECT * FROM calculated_rates;

-- Q10: Recursive CTE: Hierarchical Course Lesson Prerequisites Dependency Tree
WITH RECURSIVE lesson_prereq_hierarchy AS (
    -- Anchor: Lessons that have direct prerequisites
    SELECT 
        lp.lesson_id,
        lp.prerequisite_lesson_id,
        1 AS depth_level,
        CAST(CONCAT(lp.prerequisite_lesson_id, ' -> ', lp.lesson_id) AS CHAR(200)) AS prerequisite_chain
    FROM lesson_prerequisites lp
    
    UNION ALL
    
    -- Recursive step: Follow chaining prerequisites
    SELECT 
        child.lesson_id,
        parent.prerequisite_lesson_id,
        parent.depth_level + 1,
        CONCAT(parent.prerequisite_chain, ' -> ', child.lesson_id)
    FROM lesson_prerequisites child
    JOIN lesson_prereq_hierarchy parent ON child.prerequisite_lesson_id = parent.lesson_id
    WHERE parent.depth_level < 5
)
SELECT 
    h.lesson_id,
    l.title AS lesson_title,
    h.prerequisite_lesson_id,
    pl.title AS prerequisite_title,
    h.depth_level,
    h.prerequisite_chain
FROM lesson_prereq_hierarchy h
JOIN lessons l ON h.lesson_id = l.lesson_id
JOIN lessons pl ON h.prerequisite_lesson_id = pl.lesson_id;

-- Q11: Window Function ROW_NUMBER(): Rank Students by Attendance within Offering
SELECT 
    e.offering_id,
    s.roll_no,
    u.full_name,
    e.total_attendance_pct,
    ROW_NUMBER() OVER (
        PARTITION BY e.offering_id 
        ORDER BY e.total_attendance_pct DESC, s.roll_no ASC
    ) AS attendance_rank_in_section
FROM enrollments e
JOIN students s ON e.student_id = s.student_id
JOIN users u ON s.user_id = u.user_id
WHERE e.status = 'ACTIVE';

-- Q12: Window Function DENSE_RANK(): Top Departmental Students by CGPA
SELECT 
    COALESCE(d.department_code, 'UNASSIGNED') AS department,
    s.roll_no,
    u.full_name,
    s.cgpa,
    DENSE_RANK() OVER (
        PARTITION BY u.department_id 
        ORDER BY s.cgpa DESC
    ) AS dept_academic_rank
FROM students s
JOIN users u ON s.user_id = u.user_id
LEFT JOIN departments d ON u.department_id = d.department_id
ORDER BY department, dept_academic_rank;

-- Q13: Window Function LAG(): Comparative CGPA Analysis Across Semester Peers
SELECT 
    s.student_id,
    s.roll_no,
    s.current_semester,
    s.cgpa,
    LAG(s.cgpa, 1) OVER (
        PARTITION BY s.current_semester 
        ORDER BY s.cgpa DESC
    ) AS prior_peer_cgpa,
    ROUND(s.cgpa - LAG(s.cgpa, 1) OVER (
        PARTITION BY s.current_semester 
        ORDER BY s.cgpa DESC
    ), 2) AS cgpa_gap_to_next_peer
FROM students s
ORDER BY s.current_semester, s.cgpa DESC;

-- Q14: Window Function LEAD(): Lesson Navigation Sequencing within Modules
SELECT 
    l.module_id,
    m.title AS module_title,
    l.lesson_id,
    l.sequence_no,
    l.title AS lesson_title,
    LEAD(l.lesson_id, 1) OVER (
        PARTITION BY l.module_id 
        ORDER BY l.sequence_no ASC
    ) AS next_lesson_id,
    LEAD(l.title, 1) OVER (
        PARTITION BY l.module_id 
        ORDER BY l.sequence_no ASC
    ) AS next_lesson_title
FROM lessons l
JOIN modules m ON l.module_id = m.module_id
ORDER BY l.module_id, l.sequence_no;

-- Q15: Window Running Aggregation: Cumulative Enrollment Growth Over Time
SELECT 
    DATE(enrolled_at) AS enrollment_date,
    COUNT(*) AS daily_enrollments,
    SUM(COUNT(*)) OVER (ORDER BY DATE(enrolled_at)) AS cumulative_total_enrollments
FROM enrollments
GROUP BY DATE(enrolled_at)
ORDER BY enrollment_date;

-- Q16: Window Moving Average: Course Average Attendance Distribution Benchmark
SELECT 
    e.enrollment_id,
    c.course_code,
    s.roll_no,
    e.total_attendance_pct,
    ROUND(AVG(e.total_attendance_pct) OVER (
        PARTITION BY e.course_id
    ), 2) AS course_cohort_avg_attendance,
    ROUND(e.total_attendance_pct - AVG(e.total_attendance_pct) OVER (
        PARTITION BY e.course_id
    ), 2) AS attendance_variance_from_cohort
FROM enrollments e
JOIN courses c ON e.course_id = c.course_id
JOIN students s ON e.student_id = s.student_id
WHERE e.status = 'ACTIVE';

-- Q17: GROUP BY WITH ROLLUP: Multi-Level Enrollment Breakdown (Dept -> Course -> Offering)
SELECT 
    COALESCE(d.department_code, 'ALL DEPARTMENTS') AS department,
    COALESCE(c.course_code, 'ALL COURSES') AS course,
    COALESCE(co.section_name, 'ALL SECTIONS') AS section,
    COUNT(e.enrollment_id) AS enrolled_students,
    ROUND(AVG(e.total_attendance_pct), 2) AS avg_attendance
FROM enrollments e
JOIN course_offerings co ON e.offering_id = co.offering_id
JOIN courses c ON co.course_id = c.course_id
LEFT JOIN departments d ON c.department_id = d.department_id
GROUP BY d.department_code, c.course_code, co.section_name WITH ROLLUP;

-- Q18: GROUP BY WITH ROLLUP: Student Attendance Session Status Distribution
SELECT 
    COALESCE(c.course_code, 'ALL COURSES') AS course_code,
    COALESCE(ar.status, 'TOTAL ATTENDANCE RECORDS') AS attendance_state,
    COUNT(ar.enrollment_id) AS total_records
FROM attendance_records ar
JOIN attendance_sessions s ON ar.session_id = s.session_id
JOIN course_offerings co ON s.offering_id = co.offering_id
JOIN courses c ON co.course_id = c.course_id
GROUP BY c.course_code, ar.status WITH ROLLUP;

-- Q19: Complex Multi-Entity Scorecard: Course Enrollment, Quiz Score & Attendance
SELECT 
    s.student_id,
    s.roll_no,
    u.full_name,
    c.course_code,
    e.total_attendance_pct,
    COUNT(DISTINCT att.attempt_id) AS quizzes_attempted,
    ROUND(COALESCE(AVG(att.score), 0), 2) AS avg_quiz_score,
    COUNT(DISTINCT sub.submission_id) AS assignments_submitted
FROM enrollments e
JOIN students s ON e.student_id = s.student_id
JOIN users u ON s.user_id = u.user_id
JOIN courses c ON e.course_id = c.course_id
LEFT JOIN attempts att ON e.enrollment_id = att.enrollment_id AND att.status = 'COMPLETED'
LEFT JOIN submissions sub ON e.enrollment_id = sub.enrollment_id
GROUP BY s.student_id, s.roll_no, u.full_name, c.course_code, e.total_attendance_pct;

-- Q20: Academic Standing & Graduation Eligibility Matrix
SELECT 
    s.student_id,
    s.roll_no,
    u.full_name,
    s.current_semester,
    s.cgpa,
    COUNT(e.enrollment_id) AS enrolled_courses,
    SUM(CASE WHEN e.status = 'COMPLETED' THEN c.credits ELSE 0 END) AS credits_earned,
    ROUND(AVG(e.total_attendance_pct), 2) AS cumulative_attendance_pct,
    CASE 
        WHEN s.cgpa >= 5.00 AND AVG(e.total_attendance_pct) >= 75.00 THEN 'ELIGIBLE FOR PROMOTION'
        WHEN AVG(e.total_attendance_pct) < 75.00 THEN 'CONDITIONAL / ATTENDANCE DEBARRED'
        ELSE 'ACADEMIC PROBATION'
    END AS academic_clearance_status
FROM students s
JOIN users u ON s.user_id = u.user_id
LEFT JOIN enrollments e ON s.student_id = e.student_id
LEFT JOIN courses c ON e.course_id = c.course_id
GROUP BY s.student_id, s.roll_no, u.full_name, s.current_semester, s.cgpa;


-- ------------------------------------------------------------------------------
-- STRATEGIC MANAGEMENT QUERIES (SM01 - SM05)
-- ------------------------------------------------------------------------------

-- SM01: Institutional Department Performance & Resource Utilization Benchmark
SELECT 
    d.department_id,
    d.department_code,
    d.department_name,
    COUNT(DISTINCT s.student_id) AS total_enrolled_students,
    ROUND(AVG(s.cgpa), 2) AS department_mean_cgpa,
    COUNT(DISTINCT c.course_id) AS active_curriculum_courses,
    COUNT(DISTINCT t.teacher_id) AS faculty_strength,
    ROUND(COUNT(DISTINCT s.student_id) / NULLIF(COUNT(DISTINCT t.teacher_id), 0), 1) AS student_faculty_ratio
FROM departments d
LEFT JOIN courses c ON d.department_id = c.department_id AND c.status = 'PUBLISHED'
LEFT JOIN users u_fac ON d.department_id = u_fac.department_id AND u_fac.role = 'TEACHER' AND u_fac.status = 'ACTIVE'
LEFT JOIN teachers t ON u_fac.user_id = t.user_id
LEFT JOIN users u_stu ON d.department_id = u_stu.department_id AND u_stu.role = 'STUDENT' AND u_stu.status = 'ACTIVE'
LEFT JOIN students s ON u_stu.user_id = s.user_id
GROUP BY d.department_id, d.department_code, d.department_name
ORDER BY department_mean_cgpa DESC;

-- SM02: Course Offering Capacity Shortage & Demand Heatmap
SELECT 
    co.offering_id,
    c.course_code,
    c.title AS course_title,
    t.term_code,
    co.section_name,
    co.max_capacity,
    co.enrolled_count,
    (co.max_capacity - co.enrolled_count) AS seats_remaining,
    ROUND((co.enrolled_count * 100.0) / NULLIF(co.max_capacity, 0), 1) AS utilization_rate_pct,
    CASE 
        WHEN (co.enrolled_count * 100.0) / co.max_capacity >= 90.0 THEN 'CRITICAL CAPACITY / EXPANSION REQUIRED'
        WHEN (co.enrolled_count * 100.0) / co.max_capacity >= 75.0 THEN 'HIGH DEMAND'
        ELSE 'NORMAL CAPACITY'
    END AS operational_recommendation
FROM course_offerings co
JOIN courses c ON co.course_id = c.course_id
JOIN academic_terms t ON co.term_id = t.term_id
ORDER BY utilization_rate_pct DESC;

-- SM03: Faculty Teaching Workload Distribution & Balance Analysis
SELECT 
    t.teacher_id,
    t.employee_code,
    u.full_name AS faculty_name,
    d.department_code,
    COUNT(DISTINCT ci.offering_id) AS assigned_teaching_sections,
    COUNT(DISTINCT e.enrollment_id) AS total_students_mentored,
    CASE 
        WHEN COUNT(DISTINCT ci.offering_id) >= 3 THEN 'HIGH WORKLOAD'
        WHEN COUNT(DISTINCT ci.offering_id) BETWEEN 1 AND 2 THEN 'OPTIMAL'
        ELSE 'UNDER-ALLOCATED'
    END AS workload_status
FROM teachers t
JOIN users u ON t.user_id = u.user_id
LEFT JOIN departments d ON u.department_id = d.department_id
LEFT JOIN course_instructors ci ON t.teacher_id = ci.teacher_id AND ci.is_authorized = 1
LEFT JOIN enrollments e ON ci.offering_id = e.offering_id AND e.status = 'ACTIVE'
GROUP BY t.teacher_id, t.employee_code, u.full_name, d.department_code
ORDER BY assigned_teaching_sections DESC;

-- SM04: Institutional Academic Support & At-Risk Early Warning Matrix
SELECT 
    s.student_id,
    s.roll_no,
    u.full_name AS student_name,
    u.email,
    c.course_code,
    e.total_attendance_pct,
    COALESCE(sub.avg_score_pct, 0.00) AS assignment_score_pct,
    CASE 
        WHEN e.total_attendance_pct < 75.00 AND COALESCE(sub.avg_score_pct, 0.00) < 50.00 THEN 'HIGH RISK: SEVERE DEFICIT'
        WHEN e.total_attendance_pct < 75.00 THEN 'ATTENDANCE RISK (< 75%)'
        WHEN COALESCE(sub.avg_score_pct, 0.00) < 50.00 THEN 'ACADEMIC PERFORMANCE RISK (< 50%)'
        ELSE 'ON TRACK'
    END AS early_warning_classification
FROM enrollments e
JOIN students s ON e.student_id = s.student_id
JOIN users u ON s.user_id = u.user_id
JOIN courses c ON e.course_id = c.course_id
LEFT JOIN (
    SELECT 
        s2.enrollment_id,
        ROUND(AVG((s2.marks_obtained / NULLIF(a.max_marks, 0)) * 100), 2) AS avg_score_pct
    FROM submissions s2
    JOIN assignments a ON s2.assignment_id = a.assignment_id
    WHERE s2.status = 'EVALUATED'
    GROUP BY s2.enrollment_id
) sub ON e.enrollment_id = sub.enrollment_id
WHERE e.status = 'ACTIVE'
ORDER BY e.total_attendance_pct ASC;

-- SM05: Platform Engagement & Learning Velocity Analytics
SELECT 
    c.course_code,
    c.title AS course_title,
    COUNT(DISTINCT e.enrollment_id) AS total_active_enrollees,
    COUNT(DISTINCT sess.session_id) AS lecture_sessions_conducted,
    COUNT(DISTINCT sub.submission_id) AS total_assignments_turned_in,
    COUNT(DISTINCT att.attempt_id) AS total_quizzes_completed,
    ROUND(COUNT(DISTINCT att.attempt_id) / NULLIF(COUNT(DISTINCT e.enrollment_id), 0), 1) AS quiz_attempts_per_student
FROM courses c
JOIN course_offerings co ON c.course_id = co.course_id
LEFT JOIN enrollments e ON co.offering_id = e.offering_id AND e.status = 'ACTIVE'
LEFT JOIN attendance_sessions sess ON co.offering_id = sess.offering_id
LEFT JOIN assignments a ON co.offering_id = a.offering_id
LEFT JOIN submissions sub ON a.assignment_id = sub.assignment_id
LEFT JOIN attempts att ON e.enrollment_id = att.enrollment_id AND att.status = 'COMPLETED'
GROUP BY c.course_code, c.title
ORDER BY total_active_enrollees DESC;
