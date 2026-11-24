-- Database Trigger: trg_enrollment_seat_decrement
-- MiniLMS Database Engineering
DELIMITER $$
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
END;
DELIMITER ;
