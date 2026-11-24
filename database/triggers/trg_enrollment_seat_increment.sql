-- Database Trigger: trg_enrollment_seat_increment
-- MiniLMS Database Engineering
DELIMITER $$
CREATE DEFINER=`root`@`localhost` TRIGGER `trg_enrollment_seat_increment` AFTER INSERT ON `enrollments` FOR EACH ROW BEGIN
    IF NEW.offering_id IS NOT NULL AND NEW.status = 'ACTIVE' THEN
        UPDATE `course_offerings`
        SET `enrolled_count` = `enrolled_count` + 1
        WHERE `offering_id` = NEW.offering_id;
    END IF;
END;
DELIMITER ;
