-- Migration v007: Normalized Quiz Questions, Options, and Student Attempt Answers
-- DBMS PBL MiniLMS Upgrade

CREATE TABLE IF NOT EXISTS `quiz_questions` (
  `question_id` INT NOT NULL AUTO_INCREMENT,
  `quiz_id` INT NOT NULL,
  `question_text` TEXT NOT NULL,
  `points` DECIMAL(6,2) NOT NULL DEFAULT 1.00,
  `sequence_no` INT NOT NULL DEFAULT 1,
  PRIMARY KEY (`question_id`),
  UNIQUE KEY `uq_quiz_seq` (`quiz_id`, `sequence_no`),
  CONSTRAINT `fk_qq_quiz` FOREIGN KEY (`quiz_id`) REFERENCES `quizzes` (`quiz_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `quiz_options` (
  `option_id` INT NOT NULL AUTO_INCREMENT,
  `question_id` INT NOT NULL,
  `option_text` VARCHAR(255) NOT NULL,
  `is_correct` TINYINT(1) NOT NULL DEFAULT 0,
  `sequence_no` INT NOT NULL DEFAULT 1,
  PRIMARY KEY (`option_id`),
  UNIQUE KEY `uq_question_opt_seq` (`question_id`, `sequence_no`),
  CONSTRAINT `fk_qo_question` FOREIGN KEY (`question_id`) REFERENCES `quiz_questions` (`question_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `attempt_answers` (
  `answer_id` INT NOT NULL AUTO_INCREMENT,
  `attempt_id` INT NOT NULL,
  `question_id` INT NOT NULL,
  `selected_option_id` INT NOT NULL,
  `is_correct` TINYINT(1) NOT NULL DEFAULT 0,
  `points_awarded` DECIMAL(6,2) NOT NULL DEFAULT 0.00,
  `answered_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`answer_id`),
  UNIQUE KEY `uq_attempt_question` (`attempt_id`, `question_id`),
  CONSTRAINT `fk_aa_attempt` FOREIGN KEY (`attempt_id`) REFERENCES `attempts` (`attempt_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_aa_question` FOREIGN KEY (`question_id`) REFERENCES `quiz_questions` (`question_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_aa_option` FOREIGN KEY (`selected_option_id`) REFERENCES `quiz_options` (`option_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Seed questions and options for existing Quiz 1 (Primary Key Quiz - 20 pts)
INSERT IGNORE INTO `quiz_questions` (`question_id`, `quiz_id`, `question_text`, `points`, `sequence_no`)
VALUES 
(1, 1, 'Which of the following properties is mandatory for a Primary Key in a relational table?', 10.00, 1),
(2, 1, 'Can a relational table contain more than one Primary Key constraint?', 10.00, 2);

INSERT IGNORE INTO `quiz_options` (`option_id`, `question_id`, `option_text`, `is_correct`, `sequence_no`)
VALUES
(1, 1, 'It must be UNIQUE and NOT NULL', 1, 1),
(2, 1, 'It can contain duplicate values but no NULLs', 0, 2),
(3, 1, 'It allows NULL values as long as they are distinct', 0, 3),
(4, 1, 'It must be an auto-incrementing integer only', 0, 4),
(5, 2, 'No, a table can only have at most one primary key (though it can be composite)', 1, 1),
(6, 2, 'Yes, up to 16 separate primary keys per table', 0, 2),
(7, 2, 'Yes, if each primary key belongs to a different column group', 0, 3),
(8, 2, 'Only if the table is created using MyISAM engine', 0, 4);

-- Seed questions and options for existing Quiz 2 (Python Foundations Quiz - 10 pts)
INSERT IGNORE INTO `quiz_questions` (`question_id`, `quiz_id`, `question_text`, `points`, `sequence_no`)
VALUES 
(3, 2, 'Which data type in Python is immutable?', 5.00, 1),
(4, 2, 'What keyword is used to define a function in Python?', 5.00, 2);

INSERT IGNORE INTO `quiz_options` (`option_id`, `question_id`, `option_text`, `is_correct`, `sequence_no`)
VALUES
(9, 3, 'Tuple', 1, 1),
(10, 3, 'List', 0, 2),
(11, 3, 'Dictionary', 0, 3),
(12, 3, 'Set', 0, 4),
(13, 4, 'def', 1, 1),
(14, 4, 'function', 0, 2),
(15, 4, 'func', 0, 3),
(16, 4, 'define', 0, 4);

INSERT INTO schema_versions (version_no, description, applied_at)
VALUES (7, 'Normalized quiz_questions, quiz_options, and attempt_answers tables', NOW())
ON DUPLICATE KEY UPDATE description = VALUES(description), applied_at = NOW();
