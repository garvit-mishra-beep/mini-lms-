-- MiniLMS Migration v008: Core Academic Enhancements
-- Adds Departments, Academic Terms, Course Offerings, Attendance Sessions & Weak Records,
-- Assignments, Submissions, and Announcements with seamless backward compatibility.

SET FOREIGN_KEY_CHECKS = 0;

-- Idempotent column addition helper for MySQL 8.0
DROP PROCEDURE IF EXISTS `_migrate_add_col`;
DELIMITER //
CREATE PROCEDURE `_migrate_add_col`(IN p_tbl VARCHAR(64), IN p_col VARCHAR(64), IN p_def TEXT)
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = p_tbl AND COLUMN_NAME = p_col
  ) THEN
    SET @sql = CONCAT('ALTER TABLE `', p_tbl, '` ADD COLUMN `', p_col, '` ', p_def);
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
END //
DELIMITER ;

-- 1. Departments Table
CREATE TABLE IF NOT EXISTS `departments` (
  `department_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `department_code` VARCHAR(10) NOT NULL,
  `department_name` VARCHAR(100) NOT NULL,
  `building` VARCHAR(100) DEFAULT NULL,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`department_id`),
  UNIQUE KEY `UK_dept_code` (`department_code`),
  UNIQUE KEY `UK_dept_name` (`department_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert baseline Computer Science Department if not exists
INSERT INTO `departments` (`department_code`, `department_name`, `building`)
VALUES ('CSE', 'Computer Science and Engineering', 'Block A - Turing Hall')
ON DUPLICATE KEY UPDATE `department_name` = VALUES(`department_name`);

SET @default_dept_id = (SELECT `department_id` FROM `departments` WHERE `department_code` = 'CSE' LIMIT 1);

-- 2. Alter Users to link with Department and add COORDINATOR role
CALL `_migrate_add_col`('users', 'department_id', 'INT UNSIGNED DEFAULT NULL');
CALL `_migrate_add_col`('users', 'phone', 'VARCHAR(20) DEFAULT NULL');
ALTER TABLE `users` MODIFY COLUMN `role` ENUM('ADMIN', 'TEACHER', 'STUDENT', 'COORDINATOR') NOT NULL;

-- Backfill department for existing users
UPDATE `users` SET `department_id` = @default_dept_id WHERE `department_id` IS NULL;

-- 3. Alter Students for academic semester and CGPA tracking
CALL `_migrate_add_col`('students', 'current_semester', 'TINYINT UNSIGNED NOT NULL DEFAULT 1');
CALL `_migrate_add_col`('students', 'cgpa', 'DECIMAL(4,2) NOT NULL DEFAULT 0.00');

-- 4. Alter Courses for department affiliation and credit hours
CALL `_migrate_add_col`('courses', 'department_id', 'INT UNSIGNED DEFAULT NULL');
CALL `_migrate_add_col`('courses', 'credits', 'DECIMAL(3,1) NOT NULL DEFAULT 4.0');

UPDATE `courses` SET `department_id` = @default_dept_id WHERE `department_id` IS NULL;

-- 5. Academic Terms Table
CREATE TABLE IF NOT EXISTS `academic_terms` (
  `term_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `term_code` VARCHAR(20) NOT NULL,
  `term_name` VARCHAR(50) NOT NULL,
  `start_date` DATE NOT NULL,
  `end_date` DATE NOT NULL,
  `is_current` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`term_id`),
  UNIQUE KEY `UK_terms_code` (`term_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert baseline current term
INSERT INTO `academic_terms` (`term_code`, `term_name`, `start_date`, `end_date`, `is_current`)
VALUES ('2024-ODD', 'Fall Semester 2024', '2024-08-01', '2024-12-15', 1)
ON DUPLICATE KEY UPDATE `is_current` = 1;

SET @default_term_id = (SELECT `term_id` FROM `academic_terms` WHERE `term_code` = '2024-ODD' LIMIT 1);

-- 6. Course Offerings Table
CREATE TABLE IF NOT EXISTS `course_offerings` (
  `offering_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `course_id` INT NOT NULL,
  `term_id` INT UNSIGNED NOT NULL,
  `section_name` VARCHAR(10) NOT NULL DEFAULT 'A',
  `max_capacity` SMALLINT UNSIGNED NOT NULL DEFAULT 60,
  `enrolled_count` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  `status` ENUM('PLANNED','OPEN','CLOSED','COMPLETED') NOT NULL DEFAULT 'OPEN',
  PRIMARY KEY (`offering_id`),
  UNIQUE KEY `UK_offering_course_term_sec` (`course_id`, `term_id`, `section_name`),
  KEY `idx_offerings_term_course` (`term_id`, `course_id`),
  CONSTRAINT `FK_offering_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`) ON DELETE CASCADE,
  CONSTRAINT `FK_offering_term` FOREIGN KEY (`term_id`) REFERENCES `academic_terms` (`term_id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Backfill Course Offerings for existing active courses in default term
INSERT INTO `course_offerings` (`course_id`, `term_id`, `section_name`, `max_capacity`, `status`)
SELECT `course_id`, @default_term_id, 'A', 60, 'OPEN'
FROM `courses`
WHERE `course_id` NOT IN (SELECT `course_id` FROM `course_offerings` WHERE `term_id` = @default_term_id);

-- 7. Alter Course Instructors to link with Course Offerings
CALL `_migrate_add_col`('course_instructors', 'offering_id', 'INT UNSIGNED DEFAULT NULL');
CALL `_migrate_add_col`('course_instructors', 'role_in_course', "ENUM('PRIMARY','CO_INSTRUCTOR','TEACHING_ASSISTANT') NOT NULL DEFAULT 'PRIMARY'");

-- Backfill offering_id in course_instructors from matching course in default term
UPDATE `course_instructors` ci
JOIN `course_offerings` co ON ci.course_id = co.course_id AND co.term_id = @default_term_id
SET ci.offering_id = co.offering_id
WHERE ci.offering_id IS NULL;

-- 8. Alter Enrollments to link with Course Offerings and store attendance %
CALL `_migrate_add_col`('enrollments', 'offering_id', 'INT UNSIGNED DEFAULT NULL');
CALL `_migrate_add_col`('enrollments', 'total_attendance_pct', 'DECIMAL(5,2) DEFAULT 100.00');

-- Backfill offering_id in enrollments from matching course in default term
UPDATE `enrollments` e
JOIN `course_offerings` co ON e.course_id = co.course_id AND co.term_id = @default_term_id
SET e.offering_id = co.offering_id
WHERE e.offering_id IS NULL;

-- Update enrolled_count on offerings
UPDATE `course_offerings` co
SET `enrolled_count` = (
  SELECT COUNT(*) FROM `enrollments` e 
  WHERE e.offering_id = co.offering_id AND e.status = 'ACTIVE'
);

-- 9. Attendance Sessions Table
CREATE TABLE IF NOT EXISTS `attendance_sessions` (
  `session_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `offering_id` INT UNSIGNED NOT NULL,
  `teacher_id` INT NOT NULL,
  `session_date` DATE NOT NULL,
  `topic_covered` VARCHAR(200) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`session_id`),
  KEY `idx_att_sess_offering_date` (`offering_id`, `session_date`),
  CONSTRAINT `FK_att_sess_offering` FOREIGN KEY (`offering_id`) REFERENCES `course_offerings` (`offering_id`) ON DELETE CASCADE,
  CONSTRAINT `FK_att_sess_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `teachers` (`teacher_id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Attendance Records Table (Weak Entity)
CREATE TABLE IF NOT EXISTS `attendance_records` (
  `session_id` INT UNSIGNED NOT NULL,
  `enrollment_id` INT NOT NULL,
  `status` ENUM('PRESENT','ABSENT','LATE','EXCUSED') NOT NULL DEFAULT 'PRESENT',
  `remarks` VARCHAR(100) DEFAULT NULL,
  `marked_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`session_id`, `enrollment_id`),
  KEY `idx_att_rec_enrollment` (`enrollment_id`, `status`),
  CONSTRAINT `FK_att_rec_session` FOREIGN KEY (`session_id`) REFERENCES `attendance_sessions` (`session_id`) ON DELETE CASCADE,
  CONSTRAINT `FK_att_rec_enrollment` FOREIGN KEY (`enrollment_id`) REFERENCES `enrollments` (`enrollment_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. Coursework Assignments Table
CREATE TABLE IF NOT EXISTS `assignments` (
  `assignment_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `offering_id` INT UNSIGNED NOT NULL,
  `title` VARCHAR(150) NOT NULL,
  `description` TEXT DEFAULT NULL,
  `max_marks` DECIMAL(5,2) NOT NULL DEFAULT 100.00,
  `weightage_pct` DECIMAL(4,2) NOT NULL DEFAULT 10.00,
  `due_date` DATETIME NOT NULL,
  `created_by` INT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`assignment_id`),
  KEY `idx_assign_offering_due` (`offering_id`, `due_date`),
  CONSTRAINT `FK_assign_offering` FOREIGN KEY (`offering_id`) REFERENCES `course_offerings` (`offering_id`) ON DELETE CASCADE,
  CONSTRAINT `FK_assign_creator` FOREIGN KEY (`created_by`) REFERENCES `teachers` (`teacher_id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. Student Coursework Submissions Table
CREATE TABLE IF NOT EXISTS `submissions` (
  `submission_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `assignment_id` INT UNSIGNED NOT NULL,
  `enrollment_id` INT NOT NULL,
  `submission_text` TEXT DEFAULT NULL,
  `file_path` VARCHAR(255) DEFAULT NULL,
  `submitted_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` ENUM('SUBMITTED','LATE','EVALUATED','RESUBMITTED') NOT NULL DEFAULT 'SUBMITTED',
  `marks_obtained` DECIMAL(5,2) DEFAULT NULL,
  `feedback` TEXT DEFAULT NULL,
  `graded_at` DATETIME DEFAULT NULL,
  PRIMARY KEY (`submission_id`),
  UNIQUE KEY `UK_sub_assignment_enrollment` (`assignment_id`, `enrollment_id`),
  KEY `idx_submissions_assign` (`assignment_id`, `status`),
  CONSTRAINT `FK_sub_assignment` FOREIGN KEY (`assignment_id`) REFERENCES `assignments` (`assignment_id`) ON DELETE CASCADE,
  CONSTRAINT `FK_sub_enrollment` FOREIGN KEY (`enrollment_id`) REFERENCES `enrollments` (`enrollment_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. Alter Grades to support optional linkage with Coursework Submission and feedback
CALL `_migrate_add_col`('grades', 'submission_id', 'INT UNSIGNED DEFAULT NULL');
CALL `_migrate_add_col`('grades', 'feedback', 'TEXT DEFAULT NULL');

-- 14. Course & Campus Announcements Table
CREATE TABLE IF NOT EXISTS `announcements` (
  `announcement_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(150) NOT NULL,
  `content` TEXT NOT NULL,
  `offering_id` INT UNSIGNED DEFAULT NULL,
  `author_id` INT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`announcement_id`),
  KEY `idx_ann_offering` (`offering_id`),
  CONSTRAINT `FK_ann_offering` FOREIGN KEY (`offering_id`) REFERENCES `course_offerings` (`offering_id`) ON DELETE CASCADE,
  CONSTRAINT `FK_ann_author` FOREIGN KEY (`author_id`) REFERENCES `users` (`user_id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Cleanup helper procedure
DROP PROCEDURE IF EXISTS `_migrate_add_col`;

-- Record Migration v008 in schema_versions
INSERT INTO `schema_versions` (`version_no`, `description`, `applied_at`)
VALUES (8, 'Core academic enhancements: departments, terms, offerings, attendance, assignments, submissions, announcements', NOW())
ON DUPLICATE KEY UPDATE `applied_at` = NOW();

SET FOREIGN_KEY_CHECKS = 1;
