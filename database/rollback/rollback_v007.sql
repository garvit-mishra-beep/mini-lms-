-- Rollback for Migration v007

DROP TABLE IF EXISTS `attempt_answers`;
DROP TABLE IF EXISTS `quiz_options`;
DROP TABLE IF EXISTS `quiz_questions`;

DELETE FROM schema_versions WHERE version_no = 7;
