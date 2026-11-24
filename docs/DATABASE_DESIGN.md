# MiniLMS Database Design and Relational Architecture

## 1. Relational Design Principles

The MiniLMS database (`minilms_db`) is engineered to support the operational and analytical requirements of higher education institutions. The physical schema consists of **30 base tables**, normalized to Boyce-Codd Normal Form (BCNF), backed by declarative constraints, stored routines, database triggers, and workload-specific B-tree indexes.

---

## 2. Authoritative Physical Inventory

| Object Category | Verified Count | Primary Implementation Purpose |
| :--- | :---: | :--- |
| **Base Relational Tables** | **30** | Operational entities, academic lifecycle, logs, and metadata |
| **Relational Views** | **14** | Reporting rollups, complex analytical joins, and FERPA privacy masking |
| **Stored Procedures** | **11** | Business workflow automation (`sp_enroll_student`, `sp_bulk_record_attendance`) |
| **Stored Functions** | **2** | Deterministic computations (`fn_calculate_risk_score`, `fn_letter_grade`) |
| **Database Triggers** | **23** | Automated security auditing, integrity enforcement, capacity controls |
| **Primary Keys** | **30** | Deterministic clustered index per base table |
| **Foreign Keys** | **41** | Referential integrity (`ON DELETE RESTRICT` / `CASCADE`) |
| **Unique Constraints** | **22** | Uniqueness guarantees (emails, enrollment pairs, session dates) |
| **CHECK Constraints** | **19** | Domain validations (marks $\ge 0$, capacity $> 0$, GPA $0.0-10.0$) |
| **Custom Performance Indexes** | **19** | B-tree index coverage for high-frequency queries and joins |

---

## 3. Core Relational Entities

### 3.1 Identity, Users & Roles
- `users`: Core identity table (BCNF). Stores authentication credentials (`password_hash` via bcrypt/scrypt), account status, and role (`Admin`, `Instructor`, `Student`, `Parent`).
- `students`: 1:1 specialization of `users`. Contains enrollment numbers, program codes, semester, CGPA, and admission dates.
- `teachers`: 1:1 specialization of `users`. Contains faculty identifiers, designations, departments, and qualification records.
- `parents`: 1:1 specialization of `users`. Supports guardian linkages to one or more enrolled students.
- `parent_student_map`: M:N associative entity mapping parents/guardians to dependent students.

### 3.2 Academic Curriculum & Scheduling
- `departments`: Academic faculties and organizational departments.
- `courses`: Master catalog of curriculum courses, credit values, and descriptions.
- `academic_terms`: Semesters and academic sessions (e.g., `2026-FALL`, `2026-SPRING`).
- `course_offerings`: Term-specific scheduling of courses with assigned classrooms, sections, and seat capacities.
- `course_instructors`: M:N mapping of faculty instructors to course offerings.
- `modules`: Course content breakdown into structured learning modules.
- `lessons`: Individual instructional units within modules.
- `lesson_prerequisites`: Unary recursive prerequisite relationships between lessons.
- `lesson_progress`: Student lesson completion tracking and timestamps.

### 3.3 Enrollment & Attendance
- `enrollments`: Student registrations in course offerings with status tracking (`ENROLLED`, `DROPPED`, `COMPLETED`).
- `attendance_sessions`: Faculty-scheduled classroom sessions for specific offerings.
- `attendance_records`: Composite-keyed `(session_id, enrollment_id)` attendance records (`PRESENT`, `ABSENT`, `LATE`, `EXCUSED`).

### 3.4 Assessments, Quizzes & Grading
- `assignments`: Course coursework, deadlines, and maximum score rubrics.
- `submissions`: Student assignment file uploads, submission timestamps, and evaluation notes.
- `quizzes`: Online quizzes linked to courses/modules with time limits and passing criteria.
- `quiz_questions`: Individual questions with multiple question types.
- `quiz_options`: Multiple-choice options with boolean correctness flags.
- `quiz_attempts`: Student quiz sessions, durations, and recorded scores.
- `grades`: Comprehensive course grading records, GPA points, percentages, and letter grades.
- `grade_appeals`: Student grade dispute workflows and administrative resolution logs.
- `certificates`: Digital course completion certificates with cryptographic verification hashes.

### 3.5 Communications, Governance & Analytics
- `announcements`: Course-wide and institutional notices with target audience filtering.
- `academic_risks`: Automated Early Warning System risk entries, risk scores, levels, and triage statuses.
- `academic_interventions`: Dean and faculty intervention action plans for students at academic risk.
- `audit_logs`: Trigger-driven and application-driven security audit trail.
- `schema_versions`: Database DevOps migration tracking (`v001` through `v012`).

---

## 4. Normalization and BCNF Compliance

All entities in MiniLMS satisfy the requirements of **Boyce-Codd Normal Form (BCNF)**:

> **BCNF Definition**: A relational schema $R$ is in BCNF with respect to a set of functional dependencies $F$ if, for every non-trivial functional dependency $X \rightarrow Y$ in $F^+$, $X$ is a superkey for $R$.

### Case Study: `grades` Entity Normalization
- **Attributes**: `grade_id`, `enrollment_id`, `course_id`, `student_id`, `total_score`, `letter_grade`, `gpa_point`, `published_at`
- **Candidate Key**: `{enrollment_id}` (since an enrollment uniquely represents a single student in a specific course offering).
- **Dependencies**:
  - `enrollment_id` $\rightarrow$ `student_id`, `course_id`, `total_score`, `published_at` (LHS is candidate key $\rightarrow$ BCNF satisfied).
  - Derived attributes `letter_grade` and `gpa_point` are computed deterministically via stored function `fn_letter_grade(total_score)` rather than independent transitive dependencies.
- **Result**: Zero update anomalies, deletion anomalies, or insertion anomalies.

---

## 5. Relational Views

MiniLMS defines **14 SQL views** grouped into three architectural categories:

1. **Analytical Rollups**:
   - `v_course_offering_summary`: Aggregates enrollment counts, seat utilization percentages, and instructor assignments.
   - `v_student_academic_summary`: Computes earned credits, cumulative GPA, and completed courses per student.
   - `v_department_performance`: Aggregates grade point averages, enrollment counts, and faculty ratios by department.
2. **Statutory Alerts**:
   - `v_attendance_shortage_alert`: Real-time calculation identifying students below the 75% statutory attendance threshold.
   - `v_academic_risk_summary`: Joins academic risks with student profiles for executive triage dashboards.
3. **FERPA Privacy Masking**:
   - `v_student_public_directory`: Masked view redacting sensitive student contact details (masking phone numbers as `XXXXXX1234` and emails as `s***@itm.edu`).
   - `v_audit_summary_masked`: Redacts sensitive user IPs and raw request payloads for compliance reviewers.

---

## 6. Stored Programs & Business Automation

- **`sp_enroll_student`**: Enforces course capacity locks (`SELECT ... FOR UPDATE`), prerequisite checks, and duplicate enrollment prevention inside an atomic transaction.
- **`sp_bulk_record_attendance`**: Ingests attendance for an entire classroom session in a single transaction.
- **`sp_calculate_course_grade`**: Aggregates continuous assessments, assignment scores, and quiz results to compute final letter grades.
- **`sp_generate_academic_warnings`**: Evaluates all active enrollments against the 40/40/20 Early Warning heuristic and populates `academic_risks`.
- **`fn_calculate_risk_score`**: Deterministic stored function returning composite risk scores ($0.0 - 100.0$) given attendance percentage, assignment average, and LMS login count.
- **`fn_letter_grade`**: Deterministic function mapping numerical percentages to 10-point scale grades (`A+`, `A`, `B`, `C`, `F`).

---

## 7. Database Triggers

MiniLMS utilizes **23 database triggers** to enforce business rules directly inside MySQL:
- **Audit Triggers**: `trg_audit_users`, `trg_audit_courses`, `trg_audit_enrollments`, `trg_audit_grades` automatically log `INSERT`, `UPDATE`, and `DELETE` actions into `audit_logs`.
- **Capacity Controls**: `trg_enforce_course_capacity` rejects enrollment inserts if `current_enrolled >= max_capacity`.
- **Integrity Enforcement**: `trg_prevent_attendance_tampering` prevents retroactive modifications to verified attendance sessions.
