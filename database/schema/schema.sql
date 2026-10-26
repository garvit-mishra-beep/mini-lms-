-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: minilms_db
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `attempts`
--

DROP TABLE IF EXISTS `attempts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `attempts`
--

LOCK TABLES `attempts` WRITE;
/*!40000 ALTER TABLE `attempts` DISABLE KEYS */;
INSERT INTO `attempts` VALUES (1,1,1,1,'2026-10-23 11:23:57','2026-10-23 11:23:57',18.00,'SUBMITTED'),(2,1,2,1,'2026-10-23 11:23:57','2026-10-23 11:23:57',14.00,'SUBMITTED'),(3,2,3,1,'2026-10-23 11:23:57','2026-10-23 11:23:57',9.00,'SUBMITTED');
/*!40000 ALTER TABLE `attempts` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_attempt_validate` BEFORE INSERT ON `attempts` FOR EACH ROW BEGIN
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
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_attempt_score` BEFORE UPDATE ON `attempts` FOR EACH ROW BEGIN
 DECLARE max_allowed DECIMAL(8,2);
 SELECT max_score INTO max_allowed FROM quizzes WHERE quiz_id=NEW.quiz_id;
 IF NEW.score IS NOT NULL AND (NEW.score < 0 OR NEW.score > max_allowed) THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Score exceeds quiz maximum'; END IF;
 IF OLD.status='SUBMITTED' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Submitted attempt is immutable'; END IF;
 IF NEW.status='SUBMITTED' AND (NEW.score IS NULL OR NEW.submitted_at IS NULL) THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Submission needs score and timestamp'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_attempt_audit` AFTER UPDATE ON `attempts` FOR EACH ROW BEGIN
 IF OLD.status <> NEW.status AND NEW.status='SUBMITTED' THEN
  INSERT INTO audit_logs(entity_name,entity_id,action_type,performed_by,details)
  SELECT 'attempts',NEW.attempt_id,'SUBMITTED',s.user_id,CONCAT('score=',NEW.score)
  FROM enrollments e JOIN students s ON s.student_id=e.student_id WHERE e.enrollment_id=NEW.enrollment_id;
 END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `audit_logs`
--

DROP TABLE IF EXISTS `audit_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_logs`
--

LOCK TABLES `audit_logs` WRITE;
/*!40000 ALTER TABLE `audit_logs` DISABLE KEYS */;
INSERT INTO `audit_logs` VALUES (1,'enrollments',1,'ENROLLED',4,'course=1','2026-10-23 05:53:57'),(2,'enrollments',2,'ENROLLED',5,'course=1','2026-10-23 05:53:57'),(3,'enrollments',3,'ENROLLED',5,'course=2','2026-10-23 05:53:57'),(4,'attempts',1,'SUBMITTED',4,'score=18.00','2026-10-23 05:53:57'),(5,'attempts',2,'SUBMITTED',5,'score=14.00','2026-10-23 05:53:57'),(6,'attempts',3,'SUBMITTED',5,'score=9.00','2026-10-23 05:53:57'),(7,'enrollments',4,'ENROLLED',9,'course=1','2026-10-23 05:57:56'),(8,'enrollments',5,'ENROLLED',15,'course=1','2026-10-23 05:57:56'),(9,'enrollments',6,'ENROLLED',10,'course=1','2026-10-23 05:57:56'),(10,'enrollments',7,'ENROLLED',6,'course=1','2026-10-23 05:57:56'),(11,'enrollments',8,'ENROLLED',7,'course=1','2026-10-23 05:57:56'),(12,'enrollments',9,'ENROLLED',13,'course=1','2026-10-23 05:57:56'),(13,'enrollments',10,'ENROLLED',12,'course=1','2026-10-23 05:57:56'),(14,'enrollments',11,'ENROLLED',11,'course=1','2026-10-23 05:57:56'),(15,'enrollments',12,'ENROLLED',8,'course=1','2026-10-23 05:57:56'),(16,'enrollments',13,'ENROLLED',14,'course=1','2026-10-23 05:57:56'),(17,'enrollments',14,'ENROLLED',9,'course=2','2026-10-23 05:57:56'),(18,'enrollments',15,'ENROLLED',15,'course=2','2026-10-23 05:57:56'),(19,'enrollments',16,'ENROLLED',10,'course=2','2026-10-23 05:57:56'),(20,'enrollments',17,'ENROLLED',6,'course=2','2026-10-23 05:57:56'),(21,'enrollments',18,'ENROLLED',7,'course=2','2026-10-23 05:57:56'),(22,'enrollments',19,'ENROLLED',13,'course=2','2026-10-23 05:57:56'),(23,'enrollments',20,'ENROLLED',12,'course=2','2026-10-23 05:57:56'),(24,'enrollments',21,'ENROLLED',11,'course=2','2026-10-23 05:57:56'),(25,'enrollments',22,'ENROLLED',8,'course=2','2026-10-23 05:57:56'),(26,'enrollments',23,'ENROLLED',14,'course=2','2026-10-23 05:57:56');
/*!40000 ALTER TABLE `audit_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `certificates`
--

DROP TABLE IF EXISTS `certificates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `certificates`
--

LOCK TABLES `certificates` WRITE;
/*!40000 ALTER TABLE `certificates` DISABLE KEYS */;
INSERT INTO `certificates` VALUES (1,3,'CERT-3','2026-10-23 05:53:57');
/*!40000 ALTER TABLE `certificates` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `completions`
--

DROP TABLE IF EXISTS `completions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `completions` (
  `enrollment_id` int NOT NULL,
  `completion_status` enum('IN_PROGRESS','COMPLETED') NOT NULL DEFAULT 'IN_PROGRESS',
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`enrollment_id`),
  CONSTRAINT `completions_ibfk_1` FOREIGN KEY (`enrollment_id`) REFERENCES `enrollments` (`enrollment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `completions`
--

LOCK TABLES `completions` WRITE;
/*!40000 ALTER TABLE `completions` DISABLE KEYS */;
INSERT INTO `completions` VALUES (1,'IN_PROGRESS',NULL),(2,'IN_PROGRESS',NULL),(3,'COMPLETED','2026-10-23 11:23:57'),(4,'IN_PROGRESS',NULL),(5,'IN_PROGRESS',NULL),(6,'IN_PROGRESS',NULL),(7,'IN_PROGRESS',NULL),(8,'IN_PROGRESS',NULL),(9,'IN_PROGRESS',NULL),(10,'IN_PROGRESS',NULL),(11,'IN_PROGRESS',NULL),(12,'IN_PROGRESS',NULL),(13,'IN_PROGRESS',NULL),(14,'IN_PROGRESS',NULL),(15,'IN_PROGRESS',NULL),(16,'IN_PROGRESS',NULL),(17,'IN_PROGRESS',NULL),(18,'IN_PROGRESS',NULL),(19,'IN_PROGRESS',NULL),(20,'IN_PROGRESS',NULL),(21,'IN_PROGRESS',NULL),(22,'IN_PROGRESS',NULL),(23,'IN_PROGRESS',NULL);
/*!40000 ALTER TABLE `completions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `course_instructors`
--

DROP TABLE IF EXISTS `course_instructors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `course_instructors` (
  `course_id` int NOT NULL,
  `teacher_id` int NOT NULL,
  `instructor_role` enum('OWNER','INSTRUCTOR') NOT NULL DEFAULT 'INSTRUCTOR',
  `is_authorized` tinyint(1) NOT NULL DEFAULT '1',
  `assigned_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`course_id`,`teacher_id`),
  KEY `fk_ci_teacher` (`teacher_id`),
  CONSTRAINT `fk_ci_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`),
  CONSTRAINT `fk_ci_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `teachers` (`teacher_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `course_instructors`
--

LOCK TABLES `course_instructors` WRITE;
/*!40000 ALTER TABLE `course_instructors` DISABLE KEYS */;
INSERT INTO `course_instructors` VALUES (1,1,'OWNER',1,'2026-10-23 05:53:57'),(1,2,'INSTRUCTOR',1,'2026-10-23 05:53:57'),(2,2,'OWNER',1,'2026-10-23 05:53:57');
/*!40000 ALTER TABLE `course_instructors` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_course_instructor_update` BEFORE UPDATE ON `course_instructors` FOR EACH ROW BEGIN
 IF OLD.is_authorized=1 AND NEW.is_authorized=0
 AND (SELECT status FROM courses WHERE course_id=OLD.course_id)='PUBLISHED'
 AND (SELECT COUNT(*) FROM course_instructors WHERE course_id=OLD.course_id AND is_authorized=1)<=1 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Cannot disable final authorized instructor'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_course_instructor_remove` BEFORE DELETE ON `course_instructors` FOR EACH ROW BEGIN
 IF (SELECT status FROM courses WHERE course_id=OLD.course_id)='PUBLISHED'
 AND OLD.is_authorized=1
 AND (SELECT COUNT(*) FROM course_instructors WHERE course_id=OLD.course_id AND is_authorized=1) <= 1 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Cannot remove final authorized instructor'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `courses`
--

DROP TABLE IF EXISTS `courses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `courses` (
  `course_id` int NOT NULL AUTO_INCREMENT,
  `course_code` varchar(30) NOT NULL,
  `title` varchar(150) NOT NULL,
  `description` text,
  `status` enum('DRAFT','PUBLISHED','ARCHIVED') NOT NULL DEFAULT 'DRAFT',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`course_id`),
  UNIQUE KEY `course_code` (`course_code`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `courses`
--

LOCK TABLES `courses` WRITE;
/*!40000 ALTER TABLE `courses` DISABLE KEYS */;
INSERT INTO `courses` VALUES (1,'DBMS101','Database Management Systems','SQL and data modeling','PUBLISHED','2026-10-23 05:53:57'),(2,'PY101','Python Foundations','Programming basics','PUBLISHED','2026-10-23 05:53:57');
/*!40000 ALTER TABLE `courses` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_course_publish` BEFORE UPDATE ON `courses` FOR EACH ROW BEGIN
 IF NEW.status='PUBLISHED' AND (OLD.status <> 'PUBLISHED')
 AND NOT EXISTS(SELECT 1 FROM course_instructors WHERE course_id=OLD.course_id AND is_authorized=1) THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='A published course needs an authorized instructor'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `enrollments`
--

DROP TABLE IF EXISTS `enrollments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `enrollments` (
  `enrollment_id` int NOT NULL AUTO_INCREMENT,
  `student_id` int NOT NULL,
  `course_id` int NOT NULL,
  `enrolled_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` enum('ACTIVE','COMPLETED','CANCELLED') NOT NULL DEFAULT 'ACTIVE',
  `active_course_id` int GENERATED ALWAYS AS ((case when (`status` = _utf8mb4'ACTIVE') then `course_id` else NULL end)) STORED,
  PRIMARY KEY (`enrollment_id`),
  UNIQUE KEY `student_id` (`student_id`,`active_course_id`),
  KEY `idx_enrollment_course` (`course_id`,`status`),
  CONSTRAINT `enrollments_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`),
  CONSTRAINT `enrollments_ibfk_2` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `enrollments`
--

LOCK TABLES `enrollments` WRITE;
/*!40000 ALTER TABLE `enrollments` DISABLE KEYS */;
INSERT INTO `enrollments` (`enrollment_id`, `student_id`, `course_id`, `enrolled_at`, `status`) VALUES (1,1,1,'2026-10-23 05:53:57','ACTIVE'),(2,2,1,'2026-10-23 05:53:57','ACTIVE'),(3,2,2,'2026-10-23 05:53:57','COMPLETED'),(4,12,1,'2026-10-23 05:57:56','ACTIVE'),(5,11,1,'2026-10-23 05:57:56','ACTIVE'),(6,10,1,'2026-10-23 05:57:56','ACTIVE'),(7,9,1,'2026-10-23 05:57:56','ACTIVE'),(8,8,1,'2026-10-23 05:57:56','ACTIVE'),(9,7,1,'2026-10-23 05:57:56','ACTIVE'),(10,6,1,'2026-10-23 05:57:56','ACTIVE'),(11,5,1,'2026-10-23 05:57:56','ACTIVE'),(12,4,1,'2026-10-23 05:57:56','ACTIVE'),(13,3,1,'2026-10-23 05:57:56','ACTIVE'),(14,12,2,'2026-10-23 05:57:56','ACTIVE'),(15,11,2,'2026-10-23 05:57:56','ACTIVE'),(16,10,2,'2026-10-23 05:57:56','ACTIVE'),(17,9,2,'2026-10-23 05:57:56','ACTIVE'),(18,8,2,'2026-10-23 05:57:56','ACTIVE'),(19,7,2,'2026-10-23 05:57:56','ACTIVE'),(20,6,2,'2026-10-23 05:57:56','ACTIVE'),(21,5,2,'2026-10-23 05:57:56','ACTIVE'),(22,4,2,'2026-10-23 05:57:56','ACTIVE'),(23,3,2,'2026-10-23 05:57:56','ACTIVE');
/*!40000 ALTER TABLE `enrollments` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_enrollment_validate` BEFORE INSERT ON `enrollments` FOR EACH ROW BEGIN
 IF NOT EXISTS(SELECT 1 FROM students s JOIN users u ON u.user_id=s.user_id
               WHERE s.student_id=NEW.student_id AND u.status='ACTIVE') THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Only active students may enroll'; END IF;
 IF NOT EXISTS(SELECT 1 FROM courses WHERE course_id=NEW.course_id AND status='PUBLISHED') THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Course is not published'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_enrollment_audit` AFTER INSERT ON `enrollments` FOR EACH ROW BEGIN
 INSERT INTO audit_logs(entity_name,entity_id,action_type,performed_by,details)
 SELECT 'enrollments', NEW.enrollment_id,'ENROLLED',s.user_id,CONCAT('course=',NEW.course_id)
 FROM students s WHERE s.student_id=NEW.student_id;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `grade_change_history`
--

DROP TABLE IF EXISTS `grade_change_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grade_change_history`
--

LOCK TABLES `grade_change_history` WRITE;
/*!40000 ALTER TABLE `grade_change_history` DISABLE KEYS */;
INSERT INTO `grade_change_history` VALUES (1,1,1,90.00,92.00,'2026-10-23 05:53:57','Moderation after review');
/*!40000 ALTER TABLE `grade_change_history` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `grades`
--

DROP TABLE IF EXISTS `grades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `grades` (
  `grade_id` int NOT NULL AUTO_INCREMENT,
  `enrollment_id` int NOT NULL,
  `final_score` decimal(6,2) NOT NULL,
  `letter_grade` varchar(2) NOT NULL,
  `published` tinyint(1) NOT NULL DEFAULT '0',
  `published_at` datetime DEFAULT NULL,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`grade_id`),
  UNIQUE KEY `enrollment_id` (`enrollment_id`),
  CONSTRAINT `grades_ibfk_1` FOREIGN KEY (`enrollment_id`) REFERENCES `enrollments` (`enrollment_id`),
  CONSTRAINT `grades_chk_1` CHECK ((`final_score` between 0 and 100))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grades`
--

LOCK TABLES `grades` WRITE;
/*!40000 ALTER TABLE `grades` DISABLE KEYS */;
INSERT INTO `grades` VALUES (1,1,92.00,'A',1,'2026-10-23 11:23:57','2026-10-23 05:53:57'),(2,2,70.00,'C',1,'2026-10-23 11:23:57','2026-10-23 05:53:57'),(3,3,90.00,'A',1,'2026-10-23 11:23:57','2026-10-23 05:53:57');
/*!40000 ALTER TABLE `grades` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_grade_guard` BEFORE UPDATE ON `grades` FOR EACH ROW BEGIN
 IF OLD.published=1 AND (OLD.final_score<>NEW.final_score OR OLD.letter_grade<>NEW.letter_grade)
 AND COALESCE(@grade_change_approved,0)<>1 THEN
   SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Use authorized correction procedure for published grades';
 END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_grade_history` AFTER UPDATE ON `grades` FOR EACH ROW BEGIN
 IF OLD.published=1 AND (OLD.final_score<>NEW.final_score OR OLD.letter_grade<>NEW.letter_grade) THEN
  INSERT INTO grade_change_history(grade_id,changed_by,old_score,new_score,reason)
  VALUES(OLD.grade_id,@grade_actor,OLD.final_score,NEW.final_score,@grade_reason);
 END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `lesson_prerequisites`
--

DROP TABLE IF EXISTS `lesson_prerequisites`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lesson_prerequisites` (
  `lesson_id` int NOT NULL,
  `prerequisite_lesson_id` int NOT NULL,
  PRIMARY KEY (`lesson_id`,`prerequisite_lesson_id`),
  KEY `prerequisite_lesson_id` (`prerequisite_lesson_id`),
  CONSTRAINT `lesson_prerequisites_ibfk_1` FOREIGN KEY (`lesson_id`) REFERENCES `lessons` (`lesson_id`),
  CONSTRAINT `lesson_prerequisites_ibfk_2` FOREIGN KEY (`prerequisite_lesson_id`) REFERENCES `lessons` (`lesson_id`),
  CONSTRAINT `lesson_prerequisites_chk_1` CHECK ((`lesson_id` <> `prerequisite_lesson_id`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lesson_prerequisites`
--

LOCK TABLES `lesson_prerequisites` WRITE;
/*!40000 ALTER TABLE `lesson_prerequisites` DISABLE KEYS */;
INSERT INTO `lesson_prerequisites` VALUES (2,1),(3,2);
/*!40000 ALTER TABLE `lesson_prerequisites` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_prerequisite_validate` BEFORE INSERT ON `lesson_prerequisites` FOR EACH ROW BEGIN
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
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `lesson_progress`
--

DROP TABLE IF EXISTS `lesson_progress`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lesson_progress` (
  `enrollment_id` int NOT NULL,
  `lesson_id` int NOT NULL,
  `completed_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`enrollment_id`,`lesson_id`),
  KEY `lesson_id` (`lesson_id`),
  CONSTRAINT `lesson_progress_ibfk_1` FOREIGN KEY (`enrollment_id`) REFERENCES `enrollments` (`enrollment_id`),
  CONSTRAINT `lesson_progress_ibfk_2` FOREIGN KEY (`lesson_id`) REFERENCES `lessons` (`lesson_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lesson_progress`
--

LOCK TABLES `lesson_progress` WRITE;
/*!40000 ALTER TABLE `lesson_progress` DISABLE KEYS */;
INSERT INTO `lesson_progress` VALUES (1,1,'2026-10-23 11:23:57'),(2,1,'2026-10-23 11:23:57'),(3,4,'2026-10-23 11:23:57');
/*!40000 ALTER TABLE `lesson_progress` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_progress_validate` BEFORE INSERT ON `lesson_progress` FOR EACH ROW BEGIN
 DECLARE v_course INT; DECLARE v_lesson_course INT;
 SELECT course_id INTO v_course FROM enrollments WHERE enrollment_id=NEW.enrollment_id;
 SELECT m.course_id INTO v_lesson_course FROM lessons l JOIN modules m ON l.module_id=m.module_id
 WHERE l.lesson_id=NEW.lesson_id;
 IF v_course <> v_lesson_course THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Lesson is not in enrollment course'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `lessons`
--

DROP TABLE IF EXISTS `lessons`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lessons`
--

LOCK TABLES `lessons` WRITE;
/*!40000 ALTER TABLE `lessons` DISABLE KEYS */;
INSERT INTO `lessons` VALUES (1,1,'Primary Keys',NULL,1,'2026-10-22 11:23:57',1,1),(2,1,'Foreign Keys',NULL,2,'2026-10-22 11:23:57',1,1),(3,2,'SELECT Queries',NULL,1,'2026-10-22 11:23:57',1,1),(4,3,'Python Setup',NULL,1,'2026-10-22 11:23:57',1,1);
/*!40000 ALTER TABLE `lessons` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `modules`
--

DROP TABLE IF EXISTS `modules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `modules`
--

LOCK TABLES `modules` WRITE;
/*!40000 ALTER TABLE `modules` DISABLE KEYS */;
INSERT INTO `modules` VALUES (1,1,'Relational Concepts',NULL,1),(2,1,'SQL Basics',NULL,2),(3,2,'Python Introduction',NULL,1);
/*!40000 ALTER TABLE `modules` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `quizzes`
--

DROP TABLE IF EXISTS `quizzes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `quizzes`
--

LOCK TABLES `quizzes` WRITE;
/*!40000 ALTER TABLE `quizzes` DISABLE KEYS */;
INSERT INTO `quizzes` VALUES (1,1,'Primary Key Quiz',20.00,3,'2026-10-22 11:23:57','2026-11-22 11:23:57',1),(2,4,'Python Intro Quiz',10.00,2,'2026-10-22 11:23:57','2026-11-22 11:23:57',1);
/*!40000 ALTER TABLE `quizzes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `schema_versions`
--

DROP TABLE IF EXISTS `schema_versions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `schema_versions` (
  `version_no` int NOT NULL,
  `description` varchar(200) NOT NULL,
  `applied_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`version_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `schema_versions`
--

LOCK TABLES `schema_versions` WRITE;
/*!40000 ALTER TABLE `schema_versions` DISABLE KEYS */;
INSERT INTO `schema_versions` VALUES (1,'Core relational schema','2026-10-23 05:53:56'),(2,'Business integrity constraints and indexes','2026-10-23 05:53:56'),(3,'Transactions and stored programs','2026-10-23 05:53:56'),(4,'Views and reporting','2026-10-23 05:53:56'),(5,'Auditing and access controls','2026-10-23 05:53:56');
/*!40000 ALTER TABLE `schema_versions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students`
--

DROP TABLE IF EXISTS `students`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students` (
  `student_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `roll_no` varchar(30) NOT NULL,
  `enrollment_no` varchar(30) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `dob` date DEFAULT NULL,
  PRIMARY KEY (`student_id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `roll_no` (`roll_no`),
  UNIQUE KEY `enrollment_no` (`enrollment_no`),
  CONSTRAINT `fk_student_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students`
--

LOCK TABLES `students` WRITE;
/*!40000 ALTER TABLE `students` DISABLE KEYS */;
INSERT INTO `students` VALUES (1,4,'CSE001','ENR001',NULL,NULL),(2,5,'CSE002','ENR002',NULL,NULL),(3,14,'MOCK14','MENR14',NULL,NULL),(4,8,'MOCK8','MENR8',NULL,NULL),(5,11,'MOCK11','MENR11',NULL,NULL),(6,12,'MOCK12','MENR12',NULL,NULL),(7,13,'MOCK13','MENR13',NULL,NULL),(8,7,'MOCK7','MENR7',NULL,NULL),(9,6,'MOCK6','MENR6',NULL,NULL),(10,10,'MOCK10','MENR10',NULL,NULL),(11,15,'MOCK15','MENR15',NULL,NULL),(12,9,'MOCK9','MENR9',NULL,NULL);
/*!40000 ALTER TABLE `students` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_student_role` BEFORE INSERT ON `students` FOR EACH ROW BEGIN
 IF NOT EXISTS(SELECT 1 FROM users WHERE user_id=NEW.user_id AND role='STUDENT') THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Student profile needs a STUDENT user'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `teachers`
--

DROP TABLE IF EXISTS `teachers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `teachers`
--

LOCK TABLES `teachers` WRITE;
/*!40000 ALTER TABLE `teachers` DISABLE KEYS */;
INSERT INTO `teachers` VALUES (1,2,'FAC001','PhD Computer Science','Database instructor',NULL),(2,3,'FAC002','MTech Computer Science','SQL instructor',NULL);
/*!40000 ALTER TABLE `teachers` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_teacher_role` BEFORE INSERT ON `teachers` FOR EACH ROW BEGIN
 IF NOT EXISTS(SELECT 1 FROM users WHERE user_id=NEW.user_id AND role='TEACHER') THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Teacher profile needs a TEACHER user'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `full_name` varchar(120) NOT NULL,
  `email` varchar(190) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('ADMIN','TEACHER','STUDENT') NOT NULL,
  `status` enum('ACTIVE','INACTIVE') NOT NULL DEFAULT 'ACTIVE',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Demo Admin','admin@example.test','NOT_A_REAL_HASH','ADMIN','ACTIVE','2026-10-23 05:53:57'),(2,'Dr Anita Sharma','anita@example.test','NOT_A_REAL_HASH','TEACHER','ACTIVE','2026-10-23 05:53:57'),(3,'Prof Raj Mehta','raj@example.test','NOT_A_REAL_HASH','TEACHER','ACTIVE','2026-10-23 05:53:57'),(4,'Aarav Singh','aarav@example.test','NOT_A_REAL_HASH','STUDENT','ACTIVE','2026-10-23 05:53:57'),(5,'Diya Gupta','diya@example.test','NOT_A_REAL_HASH','STUDENT','ACTIVE','2026-10-23 05:53:57'),(6,'Rahul Verma','rahul.mock@example.test','DEMO_ONLY','STUDENT','ACTIVE','2026-10-23 05:57:56'),(7,'Priya Sharma','priya.mock@example.test','DEMO_ONLY','STUDENT','ACTIVE','2026-10-23 05:57:56'),(8,'Aman Gupta','aman.mock@example.test','DEMO_ONLY','STUDENT','ACTIVE','2026-10-23 05:57:56'),(9,'Sneha Patel','sneha.mock@example.test','DEMO_ONLY','STUDENT','ACTIVE','2026-10-23 05:57:56'),(10,'Rohit Singh','rohit.mock@example.test','DEMO_ONLY','STUDENT','ACTIVE','2026-10-23 05:57:56'),(11,'Anjali Yadav','anjali.mock@example.test','DEMO_ONLY','STUDENT','ACTIVE','2026-10-23 05:57:56'),(12,'Karan Mehta','karan.mock@example.test','DEMO_ONLY','STUDENT','ACTIVE','2026-10-23 05:57:56'),(13,'Neha Jain','neha.mock@example.test','DEMO_ONLY','STUDENT','ACTIVE','2026-10-23 05:57:56'),(14,'Aditya Kumar','aditya.mock@example.test','DEMO_ONLY','STUDENT','ACTIVE','2026-10-23 05:57:56'),(15,'Simran Kaur','simran.mock@example.test','DEMO_ONLY','STUDENT','ACTIVE','2026-10-23 05:57:56');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `v_course_completion`
--

DROP TABLE IF EXISTS `v_course_completion`;
/*!50001 DROP VIEW IF EXISTS `v_course_completion`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_course_completion` AS SELECT 
 1 AS `course_code`,
 1 AS `enrollments_with_completion_record`,
 1 AS `completed_count`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_course_enrollments`
--

DROP TABLE IF EXISTS `v_course_enrollments`;
/*!50001 DROP VIEW IF EXISTS `v_course_enrollments`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_course_enrollments` AS SELECT 
 1 AS `course_id`,
 1 AS `course_code`,
 1 AS `title`,
 1 AS `total_enrollments`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_quiz_performance`
--

DROP TABLE IF EXISTS `v_quiz_performance`;
/*!50001 DROP VIEW IF EXISTS `v_quiz_performance`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_quiz_performance` AS SELECT 
 1 AS `quiz_id`,
 1 AS `title`,
 1 AS `submissions`,
 1 AS `average_score`,
 1 AS `max_score`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_student_courses`
--

DROP TABLE IF EXISTS `v_student_courses`;
/*!50001 DROP VIEW IF EXISTS `v_student_courses`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_student_courses` AS SELECT 
 1 AS `student_id`,
 1 AS `full_name`,
 1 AS `course_code`,
 1 AS `title`,
 1 AS `enrollment_id`,
 1 AS `status`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_student_grades`
--

DROP TABLE IF EXISTS `v_student_grades`;
/*!50001 DROP VIEW IF EXISTS `v_student_grades`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_student_grades` AS SELECT 
 1 AS `full_name`,
 1 AS `course_code`,
 1 AS `final_score`,
 1 AS `letter_grade`,
 1 AS `published`*/;
SET character_set_client = @saved_cs_client;

--
-- Dumping routines for database 'minilms_db'
--
/*!50003 DROP FUNCTION IF EXISTS `fn_letter_grade` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` FUNCTION `fn_letter_grade`(p_score DECIMAL(6,2)) RETURNS varchar(2) CHARSET utf8mb4
    NO SQL
    DETERMINISTIC
BEGIN
 RETURN CASE WHEN p_score>=90 THEN 'A' WHEN p_score>=75 THEN 'B'
 WHEN p_score>=60 THEN 'C' WHEN p_score>=40 THEN 'D' ELSE 'F' END;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_correct_published_grade` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
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
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_enroll` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_enroll`(IN p_student INT, IN p_course INT)
BEGIN
 START TRANSACTION;
 INSERT INTO enrollments(student_id,course_id) VALUES(p_student,p_course);
 INSERT INTO completions(enrollment_id) VALUES(LAST_INSERT_ID());
 COMMIT;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_publish_grade` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
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
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_start_attempt` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_start_attempt`(IN p_enrollment INT,IN p_quiz INT)
BEGIN
 DECLARE next_no INT;
 START TRANSACTION;
 
 SELECT enrollment_id INTO @locked_enrollment FROM enrollments WHERE enrollment_id=p_enrollment FOR UPDATE;
 SELECT COUNT(*)+1 INTO next_no FROM attempts WHERE enrollment_id=p_enrollment AND quiz_id=p_quiz;
 INSERT INTO attempts(enrollment_id,quiz_id,attempt_no) VALUES(p_enrollment,p_quiz,next_no);
 COMMIT;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_submit_attempt` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_submit_attempt`(IN p_attempt INT, IN p_score DECIMAL(8,2))
BEGIN
 START TRANSACTION;
 UPDATE attempts SET score=p_score,submitted_at=NOW(),status='SUBMITTED'
 WHERE attempt_id=p_attempt AND status='IN_PROGRESS';
 IF ROW_COUNT()<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Attempt not found or already submitted'; END IF;
 COMMIT;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `sp_update_completion` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
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
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Final view structure for view `v_course_completion`
--

/*!50001 DROP VIEW IF EXISTS `v_course_completion`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = cp850 */;
/*!50001 SET character_set_results     = cp850 */;
/*!50001 SET collation_connection      = cp850_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_course_completion` AS select `c`.`course_code` AS `course_code`,count(`co`.`enrollment_id`) AS `enrollments_with_completion_record`,sum((`co`.`completion_status` = 'COMPLETED')) AS `completed_count` from ((`courses` `c` left join `enrollments` `e` on((`e`.`course_id` = `c`.`course_id`))) left join `completions` `co` on((`co`.`enrollment_id` = `e`.`enrollment_id`))) group by `c`.`course_id`,`c`.`course_code` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_course_enrollments`
--

/*!50001 DROP VIEW IF EXISTS `v_course_enrollments`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = cp850 */;
/*!50001 SET character_set_results     = cp850 */;
/*!50001 SET collation_connection      = cp850_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_course_enrollments` AS select `c`.`course_id` AS `course_id`,`c`.`course_code` AS `course_code`,`c`.`title` AS `title`,count(`e`.`enrollment_id`) AS `total_enrollments` from (`courses` `c` left join `enrollments` `e` on((`e`.`course_id` = `c`.`course_id`))) group by `c`.`course_id`,`c`.`course_code`,`c`.`title` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_quiz_performance`
--

/*!50001 DROP VIEW IF EXISTS `v_quiz_performance`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = cp850 */;
/*!50001 SET character_set_results     = cp850 */;
/*!50001 SET collation_connection      = cp850_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_quiz_performance` AS select `q`.`quiz_id` AS `quiz_id`,`q`.`title` AS `title`,count(`a`.`attempt_id`) AS `submissions`,round(avg(`a`.`score`),2) AS `average_score`,`q`.`max_score` AS `max_score` from (`quizzes` `q` left join `attempts` `a` on(((`a`.`quiz_id` = `q`.`quiz_id`) and (`a`.`status` = 'SUBMITTED')))) group by `q`.`quiz_id`,`q`.`title`,`q`.`max_score` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_student_courses`
--

/*!50001 DROP VIEW IF EXISTS `v_student_courses`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = cp850 */;
/*!50001 SET character_set_results     = cp850 */;
/*!50001 SET collation_connection      = cp850_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_student_courses` AS select `s`.`student_id` AS `student_id`,`u`.`full_name` AS `full_name`,`c`.`course_code` AS `course_code`,`c`.`title` AS `title`,`e`.`enrollment_id` AS `enrollment_id`,`e`.`status` AS `status` from (((`enrollments` `e` join `students` `s` on((`s`.`student_id` = `e`.`student_id`))) join `users` `u` on((`u`.`user_id` = `s`.`user_id`))) join `courses` `c` on((`c`.`course_id` = `e`.`course_id`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_student_grades`
--

/*!50001 DROP VIEW IF EXISTS `v_student_grades`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = cp850 */;
/*!50001 SET character_set_results     = cp850 */;
/*!50001 SET collation_connection      = cp850_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_student_grades` AS select `u`.`full_name` AS `full_name`,`c`.`course_code` AS `course_code`,`g`.`final_score` AS `final_score`,`g`.`letter_grade` AS `letter_grade`,`g`.`published` AS `published` from ((((`grades` `g` join `enrollments` `e` on((`e`.`enrollment_id` = `g`.`enrollment_id`))) join `students` `s` on((`s`.`student_id` = `e`.`student_id`))) join `users` `u` on((`u`.`user_id` = `s`.`user_id`))) join `courses` `c` on((`c`.`course_id` = `e`.`course_id`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-24 12:44:45
