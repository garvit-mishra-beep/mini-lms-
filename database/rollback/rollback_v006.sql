-- Rollback for Migration v006: Revert sp_enroll to original definition

DROP PROCEDURE IF EXISTS sp_enroll;

DELIMITER //

CREATE PROCEDURE sp_enroll(IN p_student INT, IN p_course INT)
BEGIN
    START TRANSACTION;
    INSERT INTO enrollments(student_id,course_id) VALUES(p_student,p_course);
    INSERT INTO completions(enrollment_id) VALUES(LAST_INSERT_ID());
    COMMIT;
END //

DELIMITER ;

DELETE FROM schema_versions WHERE version_no = 6;
