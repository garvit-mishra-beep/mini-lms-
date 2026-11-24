# Changelog

All notable changes to the **MiniLMS** platform are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-11-24

### Added
- **Relational Database Architecture**: 30 physical base tables normalized to Boyce-Codd Normal Form (BCNF) in MySQL 8.0 InnoDB.
- **Role-Based Access Control (RBAC)**: Support for four distinct stakeholder portals: `Admin`, `Instructor`, `Student`, and `Parent`.
- **Relational Views**: 14 SQL views implementing business rollups, statutory attendance warnings (<75%), and FERPA privacy masking (`v_student_public_directory`, `v_audit_summary_masked`).
- **Programmability**: 11 stored procedures for transactional business workflows (`sp_enroll_student`, `sp_bulk_record_attendance`, `sp_calculate_course_grade`) and 2 stored functions (`fn_calculate_risk_score`, `fn_letter_grade`).
- **Database Triggers**: 23 active triggers enforcing automated audit logging, seat capacity limits, and historical attendance immutability.
- **Advanced SQL Portfolio**: 25 production-grade SQL queries covering window functions (`DENSE_RANK()`, `SUM() OVER`), CTEs, hierarchical aggregations, and self-joins.
- **Reporting Services**: 16 institutional reporting modules with CSV/PDF exports and Chart.js visualizations.
- **Academic Early Warning System (EWS)**: Multi-factor explainable risk detection engine computing composite student risk scores using a $40\%$ Attendance + $40\%$ Assessment Marks + $20\%$ LMS Activity heuristic.
- **Performance Optimization**: 19 custom B-tree indexes, including 5 dedicated workload indexes evaluated against 25,147 synthetic records.
- **Database DevOps**: Automated migration pipeline managing schema versions `v001` through `v012` tracked in `schema_versions`.
- **Disaster Recovery**: Verified logical backup automation (`scripts/backup_database.py`), checksum verification (`scripts/verify_backup.py`), and 100% parity recovery drills (`scripts/restore_database.py`).
- **Production Deployment Assets**: Docker containerization (`Dockerfile`, `docker-compose.yml`), Nginx reverse proxy configuration, and Linux systemd unit definitions.

### Changed
- Refactored monolithic Flask application into 18 modular domain Blueprints under `app/routes/`.
- Replaced legacy unparameterized database queries with 100% parameterized PyMySQL queries.
- Migrated plain text password storage to secure bcrypt/scrypt cryptographic hashing.
- Reorganized repository structure to separate public open-source software artifacts from internal academic audit documentation.

### Security
- Enforced strict input sanitization and parameterized SQL execution across all database touchpoints.
- Implemented FERPA data privacy views redacting student contact numbers and personal emails.
- Configured CSRF token verification and secure session cookies (`HttpOnly`, `SameSite=Lax`).
- Established tamper-resistant forensic audit logs capturing user actions, IP addresses, and state diffs.
