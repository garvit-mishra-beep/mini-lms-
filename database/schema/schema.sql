-- =====================================================================
-- MiniLMS Complete Relational Database Schema
-- RDBMS: MySQL 8.0 InnoDB (BCNF Normalized)
-- Inventory: 30 Base Tables, 14 Views, 11 Procs, 2 Funcs, 23 Triggers
-- =====================================================================

SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = "STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION";

-- ---------------------------------------------------------------------
-- 1. BASE TABLES (30 TABLES)
-- ---------------------------------------------------------------------

DROP TABLE IF EXISTS `academic_risks`;
CREATE TABLE `academic_risks` (
  `risk_id` int unsigned NOT NULL AUTO_INCREMENT,
  `student_id` int NOT NULL,
  `offering_id` int unsigned NOT NULL,
  `attendance_pct` decimal(5,2) NOT NULL DEFAULT '100.00',
  `assessment_pct` decimal(5,2) NOT NULL DEFAULT '100.00',
  `overdue_count` smallint unsigned NOT NULL DEFAULT '0',
  `risk_score` decimal(5,2) NOT NULL DEFAULT '0.00',
  `risk_classification` enum('LOW','MODERATE','HIGH','INSUFFICIENT_DATA') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'LOW',
  `data_sufficiency` enum('SUFFICIENT','INSUFFICIENT_DATA') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'SUFFICIENT',
  `explanation` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `review_status` enum('PENDING','CONFIRMED','DISMISSED','INTERVENTION_PLANNED') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PENDING',
  `reviewer_id` int DEFAULT NULL,
  `review_notes` text COLLATE utf8mb4_unicode_ci,
  `reviewed_at` timestamp NULL DEFAULT NULL,
  `rule_version` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'v1.0',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`risk_id`),
  UNIQUE KEY `UK_student_offering_risk` (`student_id`,`offering_id`),
  KEY `idx_risk_class` (`risk_classification`),
  KEY `idx_risk_review` (`review_status`),
  KEY `FK_risk_offering` (`offering_id`),
  KEY `FK_risk_reviewer` (`reviewer_id`),
  KEY `idx_academic_risk_perf` (`risk_classification`,`risk_score` DESC,`student_id`,`offering_id`),
  CONSTRAINT `FK_risk_offering` FOREIGN KEY (`offering_id`) REFERENCES `course_offerings` (`offering_id`) ON DELETE CASCADE,
  CONSTRAINT `FK_risk_reviewer` FOREIGN KEY (`reviewer_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `FK_risk_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=39 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `academic_terms`;
CREATE TABLE `academic_terms` (
  `term_id` int unsigned NOT NULL AUTO_INCREMENT,
  `term_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `term_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `is_current` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`term_id`),
  UNIQUE KEY `UK_terms_code` (`term_code`),
  CONSTRAINT `chk_term_dates` CHECK ((`end_date` >= `start_date`))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `announcements`;
CREATE TABLE `announcements` (
  `announcement_id` int unsigned NOT NULL AUTO_INCREMENT,
  `title` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `offering_id` int unsigned DEFAULT NULL,
  `author_id` int NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`announcement_id`),
  KEY `idx_ann_offering` (`offering_id`),
  KEY `FK_ann_author` (`author_id`),
  CONSTRAINT `FK_ann_author` FOREIGN KEY (`author_id`) REFERENCES `users` (`user_id`) ON DELETE RESTRICT,
  CONSTRAINT `FK_ann_offering` FOREIGN KEY (`offering_id`) REFERENCES `course_offerings` (`offering_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=129 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `assignments`;
CREATE TABLE `assignments` (
  `assignment_id` int unsigned NOT NULL AUTO_INCREMENT,
  `offering_id` int unsigned NOT NULL,
  `title` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `max_marks` decimal(5,2) NOT NULL DEFAULT '100.00',
  `weightage_pct` decimal(4,2) NOT NULL DEFAULT '10.00',
  `due_date` datetime NOT NULL,
  `created_by` int NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`assignment_id`),
  KEY `idx_assign_offering_due` (`offering_id`,`due_date`),
  KEY `FK_assign_creator` (`created_by`),
  CONSTRAINT `FK_assign_creator` FOREIGN KEY (`created_by`) REFERENCES `teachers` (`teacher_id`) ON DELETE RESTRICT,
  CONSTRAINT `FK_assign_offering` FOREIGN KEY (`offering_id`) REFERENCES `course_offerings` (`offering_id`) ON DELETE CASCADE,
  CONSTRAINT `chk_assignment_marks` CHECK (((`max_marks` > 0.00) and (`max_marks` <= 500.00))),
  CONSTRAINT `chk_assignment_weightage` CHECK (((`weightage_pct` >= 0.00) and (`weightage_pct` <= 100.00)))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `attempt_answers`;
CREATE TABLE `attempt_answers` (
  `answer_id` int NOT NULL AUTO_INCREMENT,
  `attempt_id` int NOT NULL,
  `question_id` int NOT NULL,
  `selected_option_id` int NOT NULL,
  `is_correct` tinyint(1) NOT NULL DEFAULT '0',
  `points_awarded` decimal(6,2) NOT NULL DEFAULT '0.00',
  `answered_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`answer_id`),
  UNIQUE KEY `uq_attempt_question` (`attempt_id`,`question_id`),
  KEY `fk_aa_question` (`question_id`),
  KEY `fk_aa_option` (`selected_option_id`),
  CONSTRAINT `fk_aa_attempt` FOREIGN KEY (`attempt_id`) REFERENCES `attempts` (`attempt_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_aa_option` FOREIGN KEY (`selected_option_id`) REFERENCES `quiz_options` (`option_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_aa_question` FOREIGN KEY (`question_id`) REFERENCES `quiz_questions` (`question_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `attempts`;
CREATE TABLE `attempts` (
  `attempt_id` int NOT NULL AUTO_INCREMENT,
  `quiz_id` int NOT NULL,
  `enrollment_id` int NOT NULL,
  `attempt_no` int NOT NULL,
  `started_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `submitted_at` datetime DEFAULT NULL,
  `score` decimal(8,2) DEFAULT NULL,
  `status` enum('IN_PROGRESS','SUBMITTED') NOT NULL DEFAULT 'IN_PROGRESS',
  PRIMARY KEY (`attempt_id`),
  UNIQUE KEY `quiz_id` (`quiz_id`,`enrollment_id`,`attempt_no`),
  KEY `idx_attempt_enrollment` (`enrollment_id`,`quiz_id`),
  CONSTRAINT `attempts_ibfk_1` FOREIGN KEY (`quiz_id`) REFERENCES `quizzes` (`quiz_id`),
  CONSTRAINT `attempts_ibfk_2` FOREIGN KEY (`enrollment_id`) REFERENCES `enrollments` (`enrollment_id`),
  CONSTRAINT `attempts_chk_1` CHECK ((`attempt_no` > 0)),
  CONSTRAINT `attempts_chk_2` CHECK ((`score` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `attendance_records`;
CREATE TABLE `attendance_records` (
  `session_id` int unsigned NOT NULL,
  `enrollment_id` int NOT NULL,
  `status` enum('PRESENT','ABSENT','LATE','EXCUSED') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PRESENT',
  `remarks` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `marked_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`session_id`,`enrollment_id`),
  KEY `idx_att_rec_enrollment` (`enrollment_id`,`status`),
  KEY `idx_att_rec_perf_covering` (`enrollment_id`,`status`,`session_id`),
  CONSTRAINT `FK_att_rec_enrollment` FOREIGN KEY (`enrollment_id`) REFERENCES `enrollments` (`enrollment_id`) ON DELETE CASCADE,
  CONSTRAINT `FK_att_rec_session` FOREIGN KEY (`session_id`) REFERENCES `attendance_sessions` (`session_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `attendance_sessions`;
CREATE TABLE `attendance_sessions` (
  `session_id` int unsigned NOT NULL AUTO_INCREMENT,
  `offering_id` int unsigned NOT NULL,
  `teacher_id` int NOT NULL,
  `session_date` date NOT NULL,
  `topic_covered` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`session_id`),
  KEY `idx_att_sess_offering_date` (`offering_id`,`session_date`),
  KEY `FK_att_sess_teacher` (`teacher_id`),
  CONSTRAINT `FK_att_sess_offering` FOREIGN KEY (`offering_id`) REFERENCES `course_offerings` (`offering_id`) ON DELETE CASCADE,
  CONSTRAINT `FK_att_sess_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `teachers` (`teacher_id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=39 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `audit_logs`;
CREATE TABLE `audit_logs` (
  `audit_id` bigint NOT NULL AUTO_INCREMENT,
  `entity_name` varchar(70) NOT NULL,
  `entity_id` int NOT NULL,
  `action_type` varchar(60) NOT NULL,
  `performed_by` int DEFAULT NULL,
  `details` varchar(500) DEFAULT NULL,
  `action_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`audit_id`),
  KEY `performed_by` (`performed_by`),
  KEY `idx_audit_action` (`entity_name`,`action_time`),
  CONSTRAINT `audit_logs_ibfk_1` FOREIGN KEY (`performed_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=433 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `certificates`;
CREATE TABLE `certificates` (
  `certificate_id` int NOT NULL AUTO_INCREMENT,
  `enrollment_id` int NOT NULL,
  `certificate_code` varchar(60) NOT NULL,
  `issued_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`certificate_id`),
  UNIQUE KEY `enrollment_id` (`enrollment_id`),
  UNIQUE KEY `certificate_code` (`certificate_code`),
  CONSTRAINT `certificates_ibfk_1` FOREIGN KEY (`enrollment_id`) REFERENCES `completions` (`enrollment_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `completions`;
CREATE TABLE `completions` (
  `enrollment_id` int NOT NULL,
  `completion_status` enum('IN_PROGRESS','COMPLETED') NOT NULL DEFAULT 'IN_PROGRESS',
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`enrollment_id`),
  CONSTRAINT `completions_ibfk_1` FOREIGN KEY (`enrollment_id`) REFERENCES `enrollments` (`enrollment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `course_instructors`;
CREATE TABLE `course_instructors` (
  `course_id` int NOT NULL,
  `teacher_id` int NOT NULL,
  `instructor_role` enum('OWNER','INSTRUCTOR') NOT NULL DEFAULT 'INSTRUCTOR',
  `is_authorized` tinyint(1) NOT NULL DEFAULT '1',
  `assigned_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `offering_id` int unsigned DEFAULT NULL,
  `role_in_course` enum('PRIMARY','CO_INSTRUCTOR','TEACHING_ASSISTANT') NOT NULL DEFAULT 'PRIMARY',
  PRIMARY KEY (`course_id`,`teacher_id`),
  KEY `fk_ci_teacher` (`teacher_id`),
  CONSTRAINT `fk_ci_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`),
  CONSTRAINT `fk_ci_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `teachers` (`teacher_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `course_offerings`;
CREATE TABLE `course_offerings` (
  `offering_id` int unsigned NOT NULL AUTO_INCREMENT,
  `course_id` int NOT NULL,
  `term_id` int unsigned NOT NULL,
  `section_name` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'A',
  `max_capacity` smallint unsigned NOT NULL DEFAULT '60',
  `enrolled_count` smallint unsigned NOT NULL DEFAULT '0',
  `status` enum('PLANNED','OPEN','CLOSED','COMPLETED') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'OPEN',
  PRIMARY KEY (`offering_id`),
  UNIQUE KEY `UK_offering_course_term_sec` (`course_id`,`term_id`,`section_name`),
  KEY `idx_offerings_term_course` (`term_id`,`course_id`),
  CONSTRAINT `FK_offering_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`) ON DELETE CASCADE,
  CONSTRAINT `FK_offering_term` FOREIGN KEY (`term_id`) REFERENCES `academic_terms` (`term_id`) ON DELETE RESTRICT,
  CONSTRAINT `chk_offering_capacity` CHECK (((`max_capacity` >= 5) and (`max_capacity` <= 300))),
  CONSTRAINT `chk_offering_enrolled` CHECK ((`enrolled_count` <= `max_capacity`))
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `courses`;
CREATE TABLE `courses` (
  `course_id` int NOT NULL AUTO_INCREMENT,
  `course_code` varchar(30) NOT NULL,
  `title` varchar(150) NOT NULL,
  `description` text,
  `status` enum('DRAFT','PUBLISHED','ARCHIVED') NOT NULL DEFAULT 'DRAFT',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `department_id` int unsigned DEFAULT NULL,
  `credits` decimal(3,1) NOT NULL DEFAULT '4.0',
  PRIMARY KEY (`course_id`),
  UNIQUE KEY `course_code` (`course_code`),
  CONSTRAINT `chk_course_credits` CHECK (((`credits` >= 1.0) and (`credits` <= 10.0)))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `departments`;
CREATE TABLE `departments` (
  `department_id` int unsigned NOT NULL AUTO_INCREMENT,
  `department_code` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `department_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `building` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`department_id`),
  UNIQUE KEY `UK_dept_code` (`department_code`),
  UNIQUE KEY `UK_dept_name` (`department_name`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `enrollments`;
CREATE TABLE `enrollments` (
  `enrollment_id` int NOT NULL AUTO_INCREMENT,
  `student_id` int NOT NULL,
  `course_id` int NOT NULL,
  `enrolled_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` enum('ACTIVE','COMPLETED','CANCELLED') NOT NULL DEFAULT 'ACTIVE',
  `active_course_id` int GENERATED ALWAYS AS ((case when (`status` = _utf8mb4'ACTIVE') then `course_id` else NULL end)) STORED,
  `offering_id` int unsigned DEFAULT NULL,
  `total_attendance_pct` decimal(5,2) DEFAULT '100.00',
  PRIMARY KEY (`enrollment_id`),
  UNIQUE KEY `student_id` (`student_id`,`active_course_id`),
  KEY `idx_enrollment_course` (`course_id`,`status`),
  KEY `idx_enr_offering_status_perf` (`offering_id`,`status`,`student_id`),
  CONSTRAINT `enrollments_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`),
  CONSTRAINT `enrollments_ibfk_2` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`),
  CONSTRAINT `chk_enrollment_att_pct` CHECK (((`total_attendance_pct` >= 0.00) and (`total_attendance_pct` <= 100.00)))
) ENGINE=InnoDB AUTO_INCREMENT=97 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `grade_change_history`;
CREATE TABLE `grade_change_history` (
  `change_id` bigint NOT NULL AUTO_INCREMENT,
  `grade_id` int NOT NULL,
  `changed_by` int NOT NULL,
  `old_score` decimal(6,2) NOT NULL,
  `new_score` decimal(6,2) NOT NULL,
  `changed_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `reason` varchar(255) NOT NULL,
  PRIMARY KEY (`change_id`),
  KEY `grade_id` (`grade_id`),
  KEY `changed_by` (`changed_by`),
  CONSTRAINT `grade_change_history_ibfk_1` FOREIGN KEY (`grade_id`) REFERENCES `grades` (`grade_id`),
  CONSTRAINT `grade_change_history_ibfk_2` FOREIGN KEY (`changed_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `grades`;
CREATE TABLE `grades` (
  `grade_id` int NOT NULL AUTO_INCREMENT,
  `enrollment_id` int NOT NULL,
  `final_score` decimal(6,2) NOT NULL,
  `letter_grade` varchar(2) NOT NULL,
  `published` tinyint(1) NOT NULL DEFAULT '0',
  `published_at` datetime DEFAULT NULL,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `submission_id` int unsigned DEFAULT NULL,
  `feedback` text,
  PRIMARY KEY (`grade_id`),
  UNIQUE KEY `enrollment_id` (`enrollment_id`),
  KEY `idx_grades_ranking_perf` (`enrollment_id`,`final_score` DESC),
  CONSTRAINT `grades_ibfk_1` FOREIGN KEY (`enrollment_id`) REFERENCES `enrollments` (`enrollment_id`),
  CONSTRAINT `chk_grade_final_score` CHECK ((`final_score` >= 0.00)),
  CONSTRAINT `grades_chk_1` CHECK ((`final_score` between 0 and 100))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `lesson_prerequisites`;
CREATE TABLE `lesson_prerequisites` (
  `lesson_id` int NOT NULL,
  `prerequisite_lesson_id` int NOT NULL,
  PRIMARY KEY (`lesson_id`,`prerequisite_lesson_id`),
  KEY `prerequisite_lesson_id` (`prerequisite_lesson_id`),
  CONSTRAINT `lesson_prerequisites_ibfk_1` FOREIGN KEY (`lesson_id`) REFERENCES `lessons` (`lesson_id`),
  CONSTRAINT `lesson_prerequisites_ibfk_2` FOREIGN KEY (`prerequisite_lesson_id`) REFERENCES `lessons` (`lesson_id`),
  CONSTRAINT `lesson_prerequisites_chk_1` CHECK ((`lesson_id` <> `prerequisite_lesson_id`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `lesson_progress`;
CREATE TABLE `lesson_progress` (
  `enrollment_id` int NOT NULL,
  `lesson_id` int NOT NULL,
  `completed_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`enrollment_id`,`lesson_id`),
  KEY `lesson_id` (`lesson_id`),
  CONSTRAINT `lesson_progress_ibfk_1` FOREIGN KEY (`enrollment_id`) REFERENCES `enrollments` (`enrollment_id`),
  CONSTRAINT `lesson_progress_ibfk_2` FOREIGN KEY (`lesson_id`) REFERENCES `lessons` (`lesson_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `lessons`;
CREATE TABLE `lessons` (
  `lesson_id` int NOT NULL AUTO_INCREMENT,
  `module_id` int NOT NULL,
  `title` varchar(150) NOT NULL,
  `content_text` text,
  `sequence_no` int NOT NULL,
  `release_date` datetime DEFAULT NULL,
  `is_restricted` tinyint(1) NOT NULL DEFAULT '1',
  `required_for_completion` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`lesson_id`),
  UNIQUE KEY `module_id` (`module_id`,`sequence_no`),
  KEY `idx_lesson_module` (`module_id`),
  CONSTRAINT `fk_lesson_module` FOREIGN KEY (`module_id`) REFERENCES `modules` (`module_id`),
  CONSTRAINT `lessons_chk_1` CHECK ((`sequence_no` > 0))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `modules`;
CREATE TABLE `modules` (
  `module_id` int NOT NULL AUTO_INCREMENT,
  `course_id` int NOT NULL,
  `title` varchar(150) NOT NULL,
  `description` text,
  `sequence_no` int NOT NULL,
  PRIMARY KEY (`module_id`),
  UNIQUE KEY `course_id` (`course_id`,`sequence_no`),
  KEY `idx_module_course` (`course_id`),
  CONSTRAINT `fk_mod_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`),
  CONSTRAINT `modules_chk_1` CHECK ((`sequence_no` > 0))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `quiz_options`;
CREATE TABLE `quiz_options` (
  `option_id` int NOT NULL AUTO_INCREMENT,
  `question_id` int NOT NULL,
  `option_text` varchar(255) NOT NULL,
  `is_correct` tinyint(1) NOT NULL DEFAULT '0',
  `sequence_no` int NOT NULL DEFAULT '1',
  PRIMARY KEY (`option_id`),
  UNIQUE KEY `uq_question_opt_seq` (`question_id`,`sequence_no`),
  CONSTRAINT `fk_qo_question` FOREIGN KEY (`question_id`) REFERENCES `quiz_questions` (`question_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `quiz_questions`;
CREATE TABLE `quiz_questions` (
  `question_id` int NOT NULL AUTO_INCREMENT,
  `quiz_id` int NOT NULL,
  `question_text` text NOT NULL,
  `points` decimal(6,2) NOT NULL DEFAULT '1.00',
  `sequence_no` int NOT NULL DEFAULT '1',
  PRIMARY KEY (`question_id`),
  UNIQUE KEY `uq_quiz_seq` (`quiz_id`,`sequence_no`),
  CONSTRAINT `fk_qq_quiz` FOREIGN KEY (`quiz_id`) REFERENCES `quizzes` (`quiz_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `quizzes`;
CREATE TABLE `quizzes` (
  `quiz_id` int NOT NULL AUTO_INCREMENT,
  `lesson_id` int NOT NULL,
  `title` varchar(150) NOT NULL,
  `max_score` decimal(8,2) NOT NULL,
  `allowed_attempts` int NOT NULL,
  `available_from` datetime NOT NULL,
  `available_until` datetime NOT NULL,
  `required_for_completion` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`quiz_id`),
  KEY `idx_quiz_lesson` (`lesson_id`),
  CONSTRAINT `quizzes_ibfk_1` FOREIGN KEY (`lesson_id`) REFERENCES `lessons` (`lesson_id`),
  CONSTRAINT `quizzes_chk_1` CHECK ((`max_score` > 0)),
  CONSTRAINT `quizzes_chk_2` CHECK ((`allowed_attempts` > 0)),
  CONSTRAINT `quizzes_chk_3` CHECK ((`available_until` > `available_from`))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `schema_versions`;
CREATE TABLE `schema_versions` (
  `version_no` int NOT NULL,
  `description` varchar(200) NOT NULL,
  `applied_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`version_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `students`;
CREATE TABLE `students` (
  `student_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `roll_no` varchar(30) NOT NULL,
  `enrollment_no` varchar(30) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `dob` date DEFAULT NULL,
  `current_semester` tinyint unsigned NOT NULL DEFAULT '1',
  `cgpa` decimal(4,2) NOT NULL DEFAULT '0.00',
  PRIMARY KEY (`student_id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `roll_no` (`roll_no`),
  UNIQUE KEY `enrollment_no` (`enrollment_no`),
  CONSTRAINT `fk_student_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `chk_student_cgpa` CHECK (((`cgpa` >= 0.00) and (`cgpa` <= 10.00))),
  CONSTRAINT `chk_student_semester` CHECK ((`current_semester` between 1 and 8))
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `submissions`;
CREATE TABLE `submissions` (
  `submission_id` int unsigned NOT NULL AUTO_INCREMENT,
  `assignment_id` int unsigned NOT NULL,
  `enrollment_id` int NOT NULL,
  `submission_text` text COLLATE utf8mb4_unicode_ci,
  `file_path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `submitted_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` enum('SUBMITTED','LATE','EVALUATED','RESUBMITTED') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'SUBMITTED',
  `marks_obtained` decimal(5,2) DEFAULT NULL,
  `feedback` text COLLATE utf8mb4_unicode_ci,
  `graded_at` datetime DEFAULT NULL,
  PRIMARY KEY (`submission_id`),
  UNIQUE KEY `UK_sub_assignment_enrollment` (`assignment_id`,`enrollment_id`),
  KEY `idx_submissions_assign` (`assignment_id`,`status`),
  KEY `FK_sub_enrollment` (`enrollment_id`),
  KEY `idx_sub_assign_enr_status` (`assignment_id`,`enrollment_id`,`status`),
  CONSTRAINT `FK_sub_assignment` FOREIGN KEY (`assignment_id`) REFERENCES `assignments` (`assignment_id`) ON DELETE CASCADE,
  CONSTRAINT `FK_sub_enrollment` FOREIGN KEY (`enrollment_id`) REFERENCES `enrollments` (`enrollment_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `teachers`;
CREATE TABLE `teachers` (
  `teacher_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `employee_code` varchar(30) NOT NULL,
  `qualification` varchar(150) DEFAULT NULL,
  `bio` text,
  `phone_no` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`teacher_id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `employee_code` (`employee_code`),
  CONSTRAINT `fk_teacher_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `full_name` varchar(120) NOT NULL,
  `email` varchar(190) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('ADMIN','TEACHER','STUDENT','COORDINATOR') NOT NULL,
  `status` enum('ACTIVE','INACTIVE') NOT NULL DEFAULT 'ACTIVE',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `department_id` int unsigned DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------------------
-- 2. RELATIONAL VIEWS (14 VIEWS)
-- ---------------------------------------------------------------------

DROP VIEW IF EXISTS `faculty`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `faculty` AS select `teachers`.`teacher_id` AS `faculty_id`,`teachers`.`user_id` AS `user_id`,`teachers`.`employee_code` AS `employee_code`,`teachers`.`qualification` AS `qualification`,`teachers`.`bio` AS `bio`,`teachers`.`phone_no` AS `phone_no` from `teachers`;

DROP VIEW IF EXISTS `faculty_allocations`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `faculty_allocations` AS select concat(`course_instructors`.`course_id`,'_',`course_instructors`.`teacher_id`) AS `allocation_id`,`course_instructors`.`offering_id` AS `offering_id`,`course_instructors`.`course_id` AS `course_id`,`course_instructors`.`teacher_id` AS `faculty_id`,`course_instructors`.`role_in_course` AS `role_in_course`,`course_instructors`.`is_authorized` AS `is_authorized`,`course_instructors`.`assigned_at` AS `assigned_at` from `course_instructors`;

DROP VIEW IF EXISTS `v_academic_risk_summary`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_academic_risk_summary` AS select `ar`.`risk_id` AS `risk_id`,`ar`.`student_id` AS `student_id`,`s`.`roll_no` AS `roll_no`,`u`.`full_name` AS `student_name`,`u`.`email` AS `student_email`,`d`.`department_code` AS `department_code`,`c`.`course_code` AS `course_code`,`c`.`title` AS `course_title`,`co`.`section_name` AS `section_name`,`ar`.`attendance_pct` AS `attendance_pct`,`ar`.`assessment_pct` AS `assessment_pct`,`ar`.`overdue_count` AS `overdue_count`,`ar`.`risk_score` AS `risk_score`,`ar`.`risk_classification` AS `risk_classification`,`ar`.`data_sufficiency` AS `data_sufficiency`,`ar`.`explanation` AS `explanation`,`ar`.`review_status` AS `review_status`,`rev`.`full_name` AS `reviewer_name`,`ar`.`review_notes` AS `review_notes`,`ar`.`reviewed_at` AS `reviewed_at`,`ar`.`created_at` AS `assessed_at` from ((((((`academic_risks` `ar` join `students` `s` on((`ar`.`student_id` = `s`.`student_id`))) join `users` `u` on((`s`.`user_id` = `u`.`user_id`))) join `course_offerings` `co` on((`ar`.`offering_id` = `co`.`offering_id`))) join `courses` `c` on((`co`.`course_id` = `c`.`course_id`))) left join `departments` `d` on((`u`.`department_id` = `d`.`department_id`))) left join `users` `rev` on((`ar`.`reviewer_id` = `rev`.`user_id`)));

DROP VIEW IF EXISTS `v_audit_summary_masked`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_audit_summary_masked` AS select `al`.`audit_id` AS `audit_id`,`al`.`action_time` AS `action_time`,`al`.`action_type` AS `action_type`,`al`.`entity_name` AS `entity_name`,`al`.`entity_id` AS `entity_id`,`u`.`role` AS `actor_role`,'***.***.***.***' AS `masked_client_ip`,`al`.`details` AS `details` from (`audit_logs` `al` left join `users` `u` on((`al`.`performed_by` = `u`.`user_id`)));

DROP VIEW IF EXISTS `v_course_completion`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_course_completion` AS select `c`.`course_code` AS `course_code`,count(`co`.`enrollment_id`) AS `enrollments_with_completion_record`,sum((`co`.`completion_status` = 'COMPLETED')) AS `completed_count` from ((`courses` `c` left join `enrollments` `e` on((`e`.`course_id` = `c`.`course_id`))) left join `completions` `co` on((`co`.`enrollment_id` = `e`.`enrollment_id`))) group by `c`.`course_id`,`c`.`course_code`;

DROP VIEW IF EXISTS `v_course_enrollments`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_course_enrollments` AS select `c`.`course_id` AS `course_id`,`c`.`course_code` AS `course_code`,`c`.`title` AS `title`,count(`e`.`enrollment_id`) AS `total_enrollments` from (`courses` `c` left join `enrollments` `e` on((`e`.`course_id` = `c`.`course_id`))) group by `c`.`course_id`,`c`.`course_code`,`c`.`title`;

DROP VIEW IF EXISTS `v_course_offering_summary`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_course_offering_summary` AS select `co`.`offering_id` AS `offering_id`,`c`.`course_code` AS `course_code`,`c`.`title` AS `course_title`,`c`.`credits` AS `credits`,`d`.`department_code` AS `department_code`,`t`.`term_code` AS `term_code`,`t`.`term_name` AS `term_name`,`co`.`section_name` AS `section_name`,`co`.`max_capacity` AS `max_capacity`,`co`.`enrolled_count` AS `enrolled_count`,round(((`co`.`enrolled_count` * 100.0) / nullif(`co`.`max_capacity`,0)),1) AS `capacity_utilization_pct`,`co`.`status` AS `offering_status`,`u`.`full_name` AS `primary_instructor_name`,`fac`.`employee_code` AS `primary_instructor_code` from ((((((`course_offerings` `co` join `courses` `c` on((`co`.`course_id` = `c`.`course_id`))) join `academic_terms` `t` on((`co`.`term_id` = `t`.`term_id`))) left join `departments` `d` on((`c`.`department_id` = `d`.`department_id`))) left join `course_instructors` `ci` on(((`co`.`offering_id` = `ci`.`offering_id`) and (`ci`.`role_in_course` = 'PRIMARY')))) left join `teachers` `fac` on((`ci`.`teacher_id` = `fac`.`teacher_id`))) left join `users` `u` on((`fac`.`user_id` = `u`.`user_id`)));

DROP VIEW IF EXISTS `v_department_performance`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_department_performance` AS select `d`.`department_id` AS `department_id`,`d`.`department_code` AS `department_code`,`d`.`department_name` AS `department_name`,count(distinct `s`.`student_id`) AS `total_students`,round(avg(`s`.`cgpa`),2) AS `dept_avg_cgpa`,count(distinct `c`.`course_id`) AS `total_courses_offered`,count(distinct `t`.`teacher_id`) AS `total_faculty_count` from ((((`departments` `d` left join `users` `u` on(((`d`.`department_id` = `u`.`department_id`) and (`u`.`status` = 'ACTIVE')))) left join `students` `s` on((`u`.`user_id` = `s`.`user_id`))) left join `teachers` `t` on((`u`.`user_id` = `t`.`user_id`))) left join `courses` `c` on((`d`.`department_id` = `c`.`department_id`))) group by `d`.`department_id`,`d`.`department_code`,`d`.`department_name`;

DROP VIEW IF EXISTS `v_faculty_workload`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_faculty_workload` AS select `fac`.`teacher_id` AS `faculty_id`,`fac`.`employee_code` AS `employee_code`,`u`.`full_name` AS `full_name`,`fac`.`qualification` AS `qualification`,`d`.`department_code` AS `department_code`,count(distinct `ci`.`offering_id`) AS `total_assigned_sections`,sum(`c`.`credits`) AS `total_teaching_credits`,count(distinct `att`.`session_id`) AS `total_lectures_conducted` from ((((((`teachers` `fac` join `users` `u` on((`fac`.`user_id` = `u`.`user_id`))) left join `departments` `d` on((`u`.`department_id` = `d`.`department_id`))) left join `course_instructors` `ci` on((`fac`.`teacher_id` = `ci`.`teacher_id`))) left join `course_offerings` `co` on((`ci`.`offering_id` = `co`.`offering_id`))) left join `courses` `c` on((`co`.`course_id` = `c`.`course_id`))) left join `attendance_sessions` `att` on(((`co`.`offering_id` = `att`.`offering_id`) and (`att`.`teacher_id` = `fac`.`teacher_id`)))) group by `fac`.`teacher_id`,`fac`.`employee_code`,`u`.`full_name`,`fac`.`qualification`,`d`.`department_code`;

DROP VIEW IF EXISTS `v_quiz_performance`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_quiz_performance` AS select `q`.`quiz_id` AS `quiz_id`,`q`.`title` AS `title`,count(`a`.`attempt_id`) AS `submissions`,round(avg(`a`.`score`),2) AS `average_score`,`q`.`max_score` AS `max_score` from (`quizzes` `q` left join `attempts` `a` on(((`a`.`quiz_id` = `q`.`quiz_id`) and (`a`.`status` = 'SUBMITTED')))) group by `q`.`quiz_id`,`q`.`title`,`q`.`max_score`;

DROP VIEW IF EXISTS `v_student_academic_summary`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_student_academic_summary` AS select `s`.`student_id` AS `student_id`,`s`.`roll_no` AS `roll_no`,`s`.`enrollment_no` AS `enrollment_no`,`u`.`full_name` AS `full_name`,`u`.`email` AS `email`,`d`.`department_code` AS `department_code`,`d`.`department_name` AS `department_name`,`s`.`current_semester` AS `current_semester`,`s`.`cgpa` AS `cgpa`,`u`.`status` AS `student_status`,count(`e`.`enrollment_id`) AS `total_enrolled_courses`,sum((case when (`e`.`status` = 'COMPLETED') then 1 else 0 end)) AS `completed_courses`,round(avg(coalesce(`e`.`total_attendance_pct`,100.00)),2) AS `avg_attendance_pct` from (((`students` `s` join `users` `u` on((`s`.`user_id` = `u`.`user_id`))) left join `departments` `d` on((`u`.`department_id` = `d`.`department_id`))) left join `enrollments` `e` on((`s`.`student_id` = `e`.`student_id`))) group by `s`.`student_id`,`s`.`roll_no`,`s`.`enrollment_no`,`u`.`full_name`,`u`.`email`,`d`.`department_code`,`d`.`department_name`,`s`.`current_semester`,`s`.`cgpa`,`u`.`status`;

DROP VIEW IF EXISTS `v_student_courses`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_student_courses` AS select `s`.`student_id` AS `student_id`,`u`.`full_name` AS `full_name`,`c`.`course_code` AS `course_code`,`c`.`title` AS `title`,`e`.`enrollment_id` AS `enrollment_id`,`e`.`status` AS `status` from (((`enrollments` `e` join `students` `s` on((`s`.`student_id` = `e`.`student_id`))) join `users` `u` on((`u`.`user_id` = `s`.`user_id`))) join `courses` `c` on((`c`.`course_id` = `e`.`course_id`)));

DROP VIEW IF EXISTS `v_student_grades`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_student_grades` AS select `u`.`full_name` AS `full_name`,`c`.`course_code` AS `course_code`,`g`.`final_score` AS `final_score`,`g`.`letter_grade` AS `letter_grade`,`g`.`published` AS `published` from ((((`grades` `g` join `enrollments` `e` on((`e`.`enrollment_id` = `g`.`enrollment_id`))) join `students` `s` on((`s`.`student_id` = `e`.`student_id`))) join `users` `u` on((`u`.`user_id` = `s`.`user_id`))) join `courses` `c` on((`c`.`course_id` = `e`.`course_id`)));

DROP VIEW IF EXISTS `v_student_public_directory`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_student_public_directory` AS select `s`.`student_id` AS `student_id`,`s`.`roll_no` AS `roll_no`,`s`.`enrollment_no` AS `enrollment_no`,`u`.`full_name` AS `full_name`,concat(left(`u`.`email`,2),'***@***',right(`u`.`email`,4)) AS `masked_email`,`d`.`department_code` AS `department_code`,`d`.`department_name` AS `department_name`,`s`.`current_semester` AS `current_semester`,`u`.`status` AS `student_status` from ((`students` `s` join `users` `u` on((`s`.`user_id` = `u`.`user_id`))) left join `departments` `d` on((`u`.`department_id` = `d`.`department_id`)));

-- ---------------------------------------------------------------------
-- 3. STORED FUNCTIONS (2 FUNCTIONS)
-- ---------------------------------------------------------------------

DELIMITER $$
DROP FUNCTION IF EXISTS `fn_calculate_risk_score`$$
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
    END$$

DROP FUNCTION IF EXISTS `fn_letter_grade`$$
CREATE DEFINER=`root`@`localhost` FUNCTION `fn_letter_grade`(p_score DECIMAL(6,2)) RETURNS varchar(2) CHARSET utf8mb4
    NO SQL
    DETERMINISTIC
BEGIN
 RETURN CASE WHEN p_score>=90 THEN 'A' WHEN p_score>=75 THEN 'B'
 WHEN p_score>=60 THEN 'C' WHEN p_score>=40 THEN 'D' ELSE 'F' END;
END$$

DELIMITER ;

-- ---------------------------------------------------------------------
-- 4. STORED PROCEDURES (11 PROCEDURES)
-- ---------------------------------------------------------------------

DELIMITER $$
DROP PROCEDURE IF EXISTS `sp_assess_student_academic_risk`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_assess_student_academic_risk`(
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

        SELECT COALESCE(e.total_attendance_pct, 100.00)
        INTO v_att_pct
        FROM `enrollments` e
        WHERE e.student_id = p_student_id AND e.offering_id = p_offering_id AND e.status = 'ACTIVE'
        LIMIT 1;

        SELECT COUNT(*) INTO v_total_sessions
        FROM `attendance_sessions`
        WHERE `offering_id` = p_offering_id;

        SELECT 
            COALESCE(AVG((s.marks_obtained / NULLIF(a.max_marks, 0)) * 100), 100.00)
        INTO v_grade_pct
        FROM `submissions` s
        JOIN `assignments` a ON s.assignment_id = a.assignment_id
        JOIN `enrollments` e ON s.enrollment_id = e.enrollment_id
        WHERE e.student_id = p_student_id AND a.offering_id = p_offering_id AND s.status = 'EVALUATED';

        SELECT COUNT(*) INTO v_overdue_count
        FROM `assignments` a
        JOIN `enrollments` e ON a.offering_id = e.offering_id
        LEFT JOIN `submissions` s ON a.assignment_id = s.assignment_id AND s.enrollment_id = e.enrollment_id
        WHERE e.student_id = p_student_id 
          AND a.offering_id = p_offering_id
          AND a.due_date < NOW()
          AND (s.submission_id IS NULL OR s.status IN ('SUBMITTED', 'RESUBMITTED'));

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
    END$$

DROP PROCEDURE IF EXISTS `sp_calculate_student_gpa`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_calculate_student_gpa`(
    IN p_student_id INT,
    OUT p_new_cgpa DECIMAL(4,2)
)
BEGIN
    DECLARE v_avg_cgpa DECIMAL(4,2);

    
    SELECT ROUND(AVG(g.final_score) / 10.0, 2) INTO v_avg_cgpa
    FROM `enrollments` e
    JOIN `grades` g ON e.enrollment_id = g.enrollment_id
    WHERE e.student_id = p_student_id AND e.status IN ('ACTIVE', 'COMPLETED');

    IF v_avg_cgpa IS NOT NULL THEN
        UPDATE `students`
        SET `cgpa` = LEAST(10.00, GREATEST(0.00, v_avg_cgpa))
        WHERE `student_id` = p_student_id;
        SET p_new_cgpa = v_avg_cgpa;
    ELSE
        SET p_new_cgpa = 0.00;
    END IF;
END$$

DROP PROCEDURE IF EXISTS `sp_correct_published_grade`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_correct_published_grade`(IN p_grade INT,IN p_score DECIMAL(6,2),IN p_actor INT,IN p_reason VARCHAR(255))
BEGIN
 DECLARE actor_role VARCHAR(20); DECLARE actor_status VARCHAR(20);
 IF p_reason IS NULL OR LENGTH(TRIM(p_reason))=0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Reason is required'; END IF;
 SELECT role,status INTO actor_role,actor_status FROM users WHERE user_id=p_actor;
 IF actor_status<>'ACTIVE' OR actor_role NOT IN ('ADMIN','TEACHER') THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unauthorized grade correction'; END IF;
 IF p_score<0 OR p_score>100 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Invalid grade percentage'; END IF;
 SET @grade_actor=p_actor; SET @grade_reason=p_reason; SET @grade_change_approved=1;
 UPDATE grades SET final_score=p_score,
 letter_grade=CASE WHEN p_score>=90 THEN 'A' WHEN p_score>=75 THEN 'B'
 WHEN p_score>=60 THEN 'C' WHEN p_score>=40 THEN 'D' ELSE 'F' END
 WHERE grade_id=p_grade AND published=1;
 SET @grade_change_approved=NULL; SET @grade_actor=NULL; SET @grade_reason=NULL;
END$$

DROP PROCEDURE IF EXISTS `sp_enroll`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_enroll`(IN p_student INT, IN p_course INT)
BEGIN
    DECLARE v_active_count INT DEFAULT 0;
    DECLARE v_student_status VARCHAR(20);
    DECLARE v_course_status VARCHAR(20);
    DECLARE v_new_enrollment_id INT;

    START TRANSACTION;

    
    SELECT u.status INTO v_student_status
    FROM students s
    JOIN users u ON u.user_id = s.user_id
    WHERE s.student_id = p_student
    FOR SHARE;

    IF v_student_status IS NULL THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Student record does not exist';
    ELSEIF v_student_status <> 'ACTIVE' THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only active students may enroll';
    END IF;

    
    SELECT status INTO v_course_status
    FROM courses
    WHERE course_id = p_course
    FOR SHARE;

    IF v_course_status IS NULL THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Course does not exist';
    ELSEIF v_course_status <> 'PUBLISHED' THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Course is not published';
    END IF;

    
    SELECT COUNT(*) INTO v_active_count
    FROM enrollments
    WHERE student_id = p_student AND course_id = p_course AND status = 'ACTIVE'
    FOR UPDATE;

    IF v_active_count > 0 THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Student is already actively enrolled in this course';
    END IF;

    
    INSERT INTO enrollments(student_id, course_id, status)
    VALUES(p_student, p_course, 'ACTIVE');

    SET v_new_enrollment_id = LAST_INSERT_ID();

    INSERT INTO completions(enrollment_id, completion_status)
    VALUES(v_new_enrollment_id, 'IN_PROGRESS');

    COMMIT;
END$$

DROP PROCEDURE IF EXISTS `sp_enroll_student_in_offering`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_enroll_student_in_offering`(
    IN p_student_id INT,
    IN p_offering_id INT,
    OUT p_enrollment_id INT,
    OUT p_status_message VARCHAR(100)
)
sp_block: BEGIN
    DECLARE v_course_id INT;
    DECLARE v_max_cap INT;
    DECLARE v_curr_enrolled INT;
    DECLARE v_offering_status VARCHAR(20);
    DECLARE v_existing_active INT DEFAULT 0;

    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_enrollment_id = 0;
        SET p_status_message = 'DATABASE_ERROR: Transaction rolled back.';
    END;

    START TRANSACTION;

    
    SELECT course_id, max_capacity, enrolled_count, status
    INTO v_course_id, v_max_cap, v_curr_enrolled, v_offering_status
    FROM `course_offerings`
    WHERE `offering_id` = p_offering_id
    FOR UPDATE;

    IF v_course_id IS NULL THEN
        ROLLBACK;
        SET p_enrollment_id = 0;
        SET p_status_message = 'ERROR: Course offering section does not exist.';
        LEAVE sp_block;
    END IF;

    IF v_offering_status <> 'OPEN' THEN
        ROLLBACK;
        SET p_enrollment_id = 0;
        SET p_status_message = 'ERROR: Course offering is not open for registration.';
        LEAVE sp_block;
    END IF;

    IF v_curr_enrolled >= v_max_cap THEN
        ROLLBACK;
        SET p_enrollment_id = 0;
        SET p_status_message = 'ERROR: Course offering section capacity exceeded.';
        LEAVE sp_block;
    END IF;

    
    SELECT COUNT(*) INTO v_existing_active
    FROM `enrollments`
    WHERE `student_id` = p_student_id 
      AND `course_id` = v_course_id 
      AND `status` = 'ACTIVE';

    IF v_existing_active > 0 THEN
        ROLLBACK;
        SET p_enrollment_id = 0;
        SET p_status_message = 'CONFLICT: Student is already actively enrolled in this course.';
        LEAVE sp_block;
    END IF;

    
    INSERT INTO `enrollments` (`student_id`, `course_id`, `offering_id`, `status`, `total_attendance_pct`)
    VALUES (p_student_id, v_course_id, p_offering_id, 'ACTIVE', 100.00);

    SET p_enrollment_id = LAST_INSERT_ID();

    
    INSERT INTO `completions` (`enrollment_id`, `completion_status`)
    VALUES (p_enrollment_id, 'IN_PROGRESS');

    

    COMMIT;
    SET p_status_message = 'SUCCESS: Student enrolled successfully.';
END$$

DROP PROCEDURE IF EXISTS `sp_grade_assignment_submission`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_grade_assignment_submission`(
    IN p_submission_id INT,
    IN p_marks DECIMAL(5,2),
    IN p_feedback TEXT,
    IN p_graded_by INT,
    OUT p_status_msg VARCHAR(100)
)
sp_grade_block: BEGIN
    DECLARE v_enrollment_id INT;
    DECLARE v_max_marks DECIMAL(5,2);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status_msg = 'DATABASE_ERROR: Grading transaction aborted.';
    END;

    START TRANSACTION;

    SELECT s.enrollment_id, a.max_marks
    INTO v_enrollment_id, v_max_marks
    FROM `submissions` s
    JOIN `assignments` a ON s.assignment_id = a.assignment_id
    WHERE s.submission_id = p_submission_id
    FOR UPDATE;

    IF v_enrollment_id IS NULL THEN
        ROLLBACK;
        SET p_status_msg = 'ERROR: Submission record not found.';
        LEAVE sp_grade_block;
    END IF;

    IF p_marks < 0.00 OR p_marks > v_max_marks THEN
        ROLLBACK;
        SET p_status_msg = 'ERROR: Marks out of permissible assignment bounds.';
        LEAVE sp_grade_block;
    END IF;

    
    UPDATE `submissions`
    SET `status` = 'EVALUATED',
        `marks_obtained` = p_marks,
        `feedback` = p_feedback,
        `graded_at` = NOW()
    WHERE `submission_id` = p_submission_id;

    
    UPDATE `grades`
    SET `submission_id` = p_submission_id,
        `feedback` = p_feedback
    WHERE `enrollment_id` = v_enrollment_id;

    COMMIT;
    SET p_status_msg = 'SUCCESS: Submission evaluated and grade recorded.';
END$$

DROP PROCEDURE IF EXISTS `sp_publish_grade`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_publish_grade`(IN p_enrollment INT)
BEGIN
 DECLARE avg_pct DECIMAL(6,2);
 DECLARE letter VARCHAR(2);
 DECLARE cnt INT;
 SELECT COUNT(*),ROUND(AVG(a.score/q.max_score*100),2) INTO cnt,avg_pct
 FROM attempts a JOIN quizzes q ON q.quiz_id=a.quiz_id
 WHERE a.enrollment_id=p_enrollment AND a.status='SUBMITTED';
 IF cnt=0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='No submitted attempts'; END IF;
 SET letter=CASE WHEN avg_pct>=90 THEN 'A' WHEN avg_pct>=75 THEN 'B'
 WHEN avg_pct>=60 THEN 'C' WHEN avg_pct>=40 THEN 'D' ELSE 'F' END;
 INSERT INTO grades(enrollment_id,final_score,letter_grade,published,published_at)
 VALUES(p_enrollment,avg_pct,letter,TRUE,NOW())
 ON DUPLICATE KEY UPDATE published=TRUE,published_at=NOW();
END$$

DROP PROCEDURE IF EXISTS `sp_record_attendance_session`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_record_attendance_session`(
    IN p_offering_id INT,
    IN p_teacher_id INT,
    IN p_session_date DATE,
    IN p_topic VARCHAR(200),
    OUT p_session_id INT
)
BEGIN
    START TRANSACTION;
    INSERT INTO `attendance_sessions` (`offering_id`, `teacher_id`, `session_date`, `topic_covered`)
    VALUES (p_offering_id, p_teacher_id, p_session_date, p_topic);
    SET p_session_id = LAST_INSERT_ID();
    COMMIT;
END$$

DROP PROCEDURE IF EXISTS `sp_start_attempt`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_start_attempt`(IN p_enrollment INT,IN p_quiz INT)
BEGIN
 DECLARE next_no INT;
 START TRANSACTION;
 
 SELECT enrollment_id INTO @locked_enrollment FROM enrollments WHERE enrollment_id=p_enrollment FOR UPDATE;
 SELECT COUNT(*)+1 INTO next_no FROM attempts WHERE enrollment_id=p_enrollment AND quiz_id=p_quiz;
 INSERT INTO attempts(enrollment_id,quiz_id,attempt_no) VALUES(p_enrollment,p_quiz,next_no);
 COMMIT;
END$$

DROP PROCEDURE IF EXISTS `sp_submit_attempt`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_submit_attempt`(IN p_attempt INT, IN p_score DECIMAL(8,2))
BEGIN
 START TRANSACTION;
 UPDATE attempts SET score=p_score,submitted_at=NOW(),status='SUBMITTED'
 WHERE attempt_id=p_attempt AND status='IN_PROGRESS';
 IF ROW_COUNT()<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Attempt not found or already submitted'; END IF;
 COMMIT;
END$$

DROP PROCEDURE IF EXISTS `sp_update_completion`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_update_completion`(IN p_enrollment INT)
BEGIN
 DECLARE missing_lessons INT; DECLARE missing_quizzes INT; DECLARE pct DECIMAL(6,2);
 SELECT COUNT(*) INTO missing_lessons FROM lessons l JOIN modules m ON m.module_id=l.module_id
 JOIN enrollments e ON e.course_id=m.course_id
 WHERE e.enrollment_id=p_enrollment AND l.required_for_completion=1 AND NOT EXISTS
 (SELECT 1 FROM lesson_progress lp WHERE lp.enrollment_id=p_enrollment AND lp.lesson_id=l.lesson_id);
 SELECT COUNT(*) INTO missing_quizzes FROM quizzes q JOIN lessons l ON l.lesson_id=q.lesson_id
 JOIN modules m ON m.module_id=l.module_id JOIN enrollments e ON e.course_id=m.course_id
 WHERE e.enrollment_id=p_enrollment AND q.required_for_completion=1 AND NOT EXISTS
 (SELECT 1 FROM attempts a WHERE a.enrollment_id=p_enrollment AND a.quiz_id=q.quiz_id
 AND a.status='SUBMITTED' AND a.score/q.max_score>=0.60);
 SELECT final_score INTO pct FROM grades WHERE enrollment_id=p_enrollment AND published=1;
 IF missing_lessons=0 AND missing_quizzes=0 AND COALESCE(pct,0)>=60 THEN
  UPDATE completions SET completion_status='COMPLETED',completed_at=NOW() WHERE enrollment_id=p_enrollment;
  UPDATE enrollments SET status='COMPLETED' WHERE enrollment_id=p_enrollment;
 ELSE
  UPDATE completions SET completion_status='IN_PROGRESS',completed_at=NULL WHERE enrollment_id=p_enrollment;
 END IF;
END$$

DELIMITER ;

-- ---------------------------------------------------------------------
-- 5. DATABASE TRIGGERS (23 TRIGGERS)
-- ---------------------------------------------------------------------

DELIMITER $$
DROP TRIGGER IF EXISTS `trg_attempt_audit`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_attempt_audit` AFTER UPDATE ON `attempts` FOR EACH ROW BEGIN
 IF OLD.status <> NEW.status AND NEW.status='SUBMITTED' THEN
  INSERT INTO audit_logs(entity_name,entity_id,action_type,performed_by,details)
  SELECT 'attempts',NEW.attempt_id,'SUBMITTED',s.user_id,CONCAT('score=',NEW.score)
  FROM enrollments e JOIN students s ON s.student_id=e.student_id WHERE e.enrollment_id=NEW.enrollment_id;
 END IF;
END$$

DROP TRIGGER IF EXISTS `trg_attempt_score`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_attempt_score` BEFORE UPDATE ON `attempts` FOR EACH ROW BEGIN
 DECLARE max_allowed DECIMAL(8,2);
 SELECT max_score INTO max_allowed FROM quizzes WHERE quiz_id=NEW.quiz_id;
 IF NEW.score IS NOT NULL AND (NEW.score < 0 OR NEW.score > max_allowed) THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Score exceeds quiz maximum'; END IF;
 IF OLD.status='SUBMITTED' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Submitted attempt is immutable'; END IF;
 IF NEW.status='SUBMITTED' AND (NEW.score IS NULL OR NEW.submitted_at IS NULL) THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Submission needs score and timestamp'; END IF;
END$$

DROP TRIGGER IF EXISTS `trg_attempt_validate`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_attempt_validate` BEFORE INSERT ON `attempts` FOR EACH ROW BEGIN
 DECLARE mx INT; DECLARE t1 DATETIME; DECLARE t2 DATETIME; DECLARE cid INT; DECLARE course_enrolled INT;
 DECLARE lesson INT; DECLARE restricted_flag BOOLEAN; DECLARE released DATETIME;
 SELECT q.allowed_attempts,q.available_from,q.available_until,m.course_id,q.lesson_id,l.is_restricted,l.release_date
 INTO mx,t1,t2,cid,lesson,restricted_flag,released
 FROM quizzes q JOIN lessons l ON l.lesson_id=q.lesson_id JOIN modules m ON m.module_id=l.module_id
 WHERE q.quiz_id=NEW.quiz_id;
 SELECT course_id INTO course_enrolled FROM enrollments WHERE enrollment_id=NEW.enrollment_id AND status='ACTIVE';
 IF course_enrolled IS NULL OR cid<>course_enrolled THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Active course enrollment required'; END IF;
 IF NEW.attempt_no>mx OR NEW.attempt_no <> 1+(SELECT COUNT(*) FROM attempts a WHERE a.quiz_id=NEW.quiz_id AND a.enrollment_id=NEW.enrollment_id) THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Invalid attempt sequence or maximum exceeded'; END IF;
 IF NEW.started_at<t1 OR NEW.started_at>t2 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Quiz outside availability window'; END IF;
 IF released IS NOT NULL AND NEW.started_at<released THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Lesson not released'; END IF;
 IF restricted_flag=1 AND EXISTS (
  SELECT 1 FROM lesson_prerequisites p WHERE p.lesson_id=lesson AND NOT EXISTS (
   SELECT 1 FROM lesson_progress x WHERE x.enrollment_id=NEW.enrollment_id AND x.lesson_id=p.prerequisite_lesson_id
  )
 ) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Lesson prerequisites incomplete'; END IF;
END$$

DROP TRIGGER IF EXISTS `trg_att_offering_validate`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_att_offering_validate` BEFORE INSERT ON `attendance_records` FOR EACH ROW BEGIN
    DECLARE v_sess_offering INT UNSIGNED;
    DECLARE v_enroll_offering INT UNSIGNED;
    
    SELECT offering_id INTO v_sess_offering FROM `attendance_sessions` WHERE session_id = NEW.session_id;
    SELECT offering_id INTO v_enroll_offering FROM `enrollments` WHERE enrollment_id = NEW.enrollment_id;
    
    IF v_sess_offering IS NOT NULL AND v_enroll_offering IS NOT NULL AND v_sess_offering <> v_enroll_offering THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cross-course data contamination: Attendance session and enrollment offerings do not match';
    END IF;
END$$

DROP TRIGGER IF EXISTS `trg_audit_logs_immutable`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_audit_logs_immutable` BEFORE UPDATE ON `audit_logs` FOR EACH ROW BEGIN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Security Violation: Audit log records are immutable and cannot be updated';
END$$

DROP TRIGGER IF EXISTS `trg_audit_logs_no_delete`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_audit_logs_no_delete` BEFORE DELETE ON `audit_logs` FOR EACH ROW BEGIN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Security Violation: Audit log records cannot be deleted';
END$$

DROP TRIGGER IF EXISTS `trg_course_instructor_remove`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_course_instructor_remove` BEFORE DELETE ON `course_instructors` FOR EACH ROW BEGIN
 IF (SELECT status FROM courses WHERE course_id=OLD.course_id)='PUBLISHED'
 AND OLD.is_authorized=1
 AND (SELECT COUNT(*) FROM course_instructors WHERE course_id=OLD.course_id AND is_authorized=1) <= 1 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Cannot remove final authorized instructor'; END IF;
END$$

DROP TRIGGER IF EXISTS `trg_course_instructor_update`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_course_instructor_update` BEFORE UPDATE ON `course_instructors` FOR EACH ROW BEGIN
 IF OLD.is_authorized=1 AND NEW.is_authorized=0
 AND (SELECT status FROM courses WHERE course_id=OLD.course_id)='PUBLISHED'
 AND (SELECT COUNT(*) FROM course_instructors WHERE course_id=OLD.course_id AND is_authorized=1)<=1 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Cannot disable final authorized instructor'; END IF;
END$$

DROP TRIGGER IF EXISTS `trg_course_publish`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_course_publish` BEFORE UPDATE ON `courses` FOR EACH ROW BEGIN
 IF NEW.status='PUBLISHED' AND (OLD.status <> 'PUBLISHED')
 AND NOT EXISTS(SELECT 1 FROM course_instructors WHERE course_id=OLD.course_id AND is_authorized=1) THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='A published course needs an authorized instructor'; END IF;
END$$

DROP TRIGGER IF EXISTS `trg_enrollment_audit`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_enrollment_audit` AFTER INSERT ON `enrollments` FOR EACH ROW BEGIN
 INSERT INTO audit_logs(entity_name,entity_id,action_type,performed_by,details)
 SELECT 'enrollments', NEW.enrollment_id,'ENROLLED',s.user_id,CONCAT('course=',NEW.course_id)
 FROM students s WHERE s.student_id=NEW.student_id;
END$$

DROP TRIGGER IF EXISTS `trg_enrollment_seat_decrement`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_enrollment_seat_decrement` AFTER UPDATE ON `enrollments` FOR EACH ROW BEGIN
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
END$$

DROP TRIGGER IF EXISTS `trg_enrollment_seat_increment`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_enrollment_seat_increment` AFTER INSERT ON `enrollments` FOR EACH ROW BEGIN
    IF NEW.offering_id IS NOT NULL AND NEW.status = 'ACTIVE' THEN
        UPDATE `course_offerings`
        SET `enrolled_count` = `enrolled_count` + 1
        WHERE `offering_id` = NEW.offering_id;
    END IF;
END$$

DROP TRIGGER IF EXISTS `trg_enrollment_validate`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_enrollment_validate` BEFORE INSERT ON `enrollments` FOR EACH ROW BEGIN
 IF NOT EXISTS(SELECT 1 FROM students s JOIN users u ON u.user_id=s.user_id
               WHERE s.student_id=NEW.student_id AND u.status='ACTIVE') THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Only active students may enroll'; END IF;
 IF NOT EXISTS(SELECT 1 FROM courses WHERE course_id=NEW.course_id AND status='PUBLISHED') THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Course is not published'; END IF;
END$$

DROP TRIGGER IF EXISTS `trg_grade_bounds_check`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_grade_bounds_check` BEFORE INSERT ON `grades` FOR EACH ROW BEGIN
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
END$$

DROP TRIGGER IF EXISTS `trg_grade_guard`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_grade_guard` BEFORE UPDATE ON `grades` FOR EACH ROW BEGIN
 IF OLD.published=1 AND (OLD.final_score<>NEW.final_score OR OLD.letter_grade<>NEW.letter_grade)
 AND COALESCE(@grade_change_approved,0)<>1 THEN
   SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Use authorized correction procedure for published grades';
 END IF;
END$$

DROP TRIGGER IF EXISTS `trg_grade_history`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_grade_history` AFTER UPDATE ON `grades` FOR EACH ROW BEGIN
 IF OLD.published=1 AND (OLD.final_score<>NEW.final_score OR OLD.letter_grade<>NEW.letter_grade) THEN
  INSERT INTO grade_change_history(grade_id,changed_by,old_score,new_score,reason)
  VALUES(OLD.grade_id,@grade_actor,OLD.final_score,NEW.final_score,@grade_reason);
 END IF;
END$$

DROP TRIGGER IF EXISTS `trg_prerequisite_validate`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_prerequisite_validate` BEFORE INSERT ON `lesson_prerequisites` FOR EACH ROW BEGIN
 DECLARE c1 INT; DECLARE c2 INT;
 SELECT m.course_id INTO c1 FROM lessons l JOIN modules m ON m.module_id=l.module_id WHERE l.lesson_id=NEW.lesson_id;
 SELECT m.course_id INTO c2 FROM lessons l JOIN modules m ON m.module_id=l.module_id WHERE l.lesson_id=NEW.prerequisite_lesson_id;
 IF c1<>c2 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Prerequisites must be in the same course'; END IF;
 
 IF EXISTS (
  WITH RECURSIVE chain(id) AS (
    SELECT prerequisite_lesson_id FROM lesson_prerequisites WHERE lesson_id=NEW.prerequisite_lesson_id
    UNION DISTINCT
    SELECT lp.prerequisite_lesson_id FROM lesson_prerequisites lp JOIN chain c ON lp.lesson_id=c.id
  ) SELECT 1 FROM chain WHERE id=NEW.lesson_id
 ) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Cyclic lesson prerequisite'; END IF;
END$$

DROP TRIGGER IF EXISTS `trg_progress_validate`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_progress_validate` BEFORE INSERT ON `lesson_progress` FOR EACH ROW BEGIN
 DECLARE v_course INT; DECLARE v_lesson_course INT;
 SELECT course_id INTO v_course FROM enrollments WHERE enrollment_id=NEW.enrollment_id;
 SELECT m.course_id INTO v_lesson_course FROM lessons l JOIN modules m ON l.module_id=m.module_id
 WHERE l.lesson_id=NEW.lesson_id;
 IF v_course <> v_lesson_course THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Lesson is not in enrollment course'; END IF;
END$$

DROP TRIGGER IF EXISTS `trg_student_role`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_student_role` BEFORE INSERT ON `students` FOR EACH ROW BEGIN
 IF NOT EXISTS(SELECT 1 FROM users WHERE user_id=NEW.user_id AND role='STUDENT') THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Student profile needs a STUDENT user'; END IF;
END$$

DROP TRIGGER IF EXISTS `trg_submission_offering_validate`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_submission_offering_validate` BEFORE INSERT ON `submissions` FOR EACH ROW BEGIN
    DECLARE v_assign_offering INT UNSIGNED;
    DECLARE v_enroll_offering INT UNSIGNED;
    
    SELECT offering_id INTO v_assign_offering FROM `assignments` WHERE assignment_id = NEW.assignment_id;
    SELECT offering_id INTO v_enroll_offering FROM `enrollments` WHERE enrollment_id = NEW.enrollment_id;
    
    IF v_assign_offering IS NOT NULL AND v_enroll_offering IS NOT NULL AND v_assign_offering <> v_enroll_offering THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cross-course data contamination: Assignment and enrollment offerings do not match';
    END IF;
END$$

DROP TRIGGER IF EXISTS `trg_teacher_role`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_teacher_role` BEFORE INSERT ON `teachers` FOR EACH ROW BEGIN
 IF NOT EXISTS(SELECT 1 FROM users WHERE user_id=NEW.user_id AND role='TEACHER') THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Teacher profile needs a TEACHER user'; END IF;
END$$

DROP TRIGGER IF EXISTS `trg_update_attendance_pct_after_insert`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_update_attendance_pct_after_insert` AFTER INSERT ON `attendance_records` FOR EACH ROW BEGIN
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
END$$

DROP TRIGGER IF EXISTS `trg_update_attendance_pct_after_update`$$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_update_attendance_pct_after_update` AFTER UPDATE ON `attendance_records` FOR EACH ROW BEGIN
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
END$$

DELIMITER ;

SET FOREIGN_KEY_CHECKS = 1;
-- =====================================================================
-- END OF MINILMS SCHEMA DEFINITION
-- =====================================================================
