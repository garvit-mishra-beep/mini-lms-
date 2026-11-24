# MiniLMS — Enterprise Relational Learning Management System

[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-MySQL%208.0%20InnoDB-orange.svg)](https://www.mysql.com/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.x-green.svg)](https://flask.palletsprojects.com/)
[![Normal Form](https://img.shields.io/badge/Schema-BCNF%20Compliant-purple.svg)](docs/DATABASE_DESIGN.md)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

MiniLMS is an enterprise-grade academic management and analytics platform engineered with a strict focus on **relational database architecture, data integrity, transactional concurrency control, and analytical query performance**. Built on **MySQL 8.0 InnoDB** and **Python Flask**, MiniLMS demonstrates that relational database management systems (RDBMS) can enforce complex business logic, regulatory data privacy, and explainable intelligence directly within the storage engine.

---

## Table of Contents
- [Problem Statement](#problem-statement)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Stakeholder Roles & Portals](#stakeholder-roles--portals)
- [System Architecture](#system-architecture)
- [Database Architecture](#database-architecture)
- [Important Database Capabilities](#important-database-capabilities)
- [Application Screenshots](#application-screenshots)
- [Installation & Local Setup](#installation--local-setup)
- [Database Initialization & Migrations](#database-initialization--migrations)
- [Application Startup](#application-startup)
- [Production Deployment](#production-deployment)
- [Repository Structure](#repository-structure)
- [Verified Technical Results](#verified-technical-results)
- [Known Limitations](#known-limitations)
- [Future Roadmap](#future-roadmap)
- [Contributing & Security](#contributing--security)
- [License](#license)

---

## Problem Statement

Traditional educational institutions frequently struggle with fragmented Learning Management Systems (LMS) where business logic is loosely enforced at the application layer, leading to:
1. **Concurrent Over-Enrollment**: Race conditions during course registration allowing enrollment beyond physical classroom limits.
2. **Attendance Tampering**: Lack of cryptographic or trigger-based immutability allowing unauthorized historical grade or attendance modifications.
3. **Data Redundancy & Anomalies**: Poorly normalized schemas (violating 3NF/BCNF) causing orphaned records upon faculty or course deletion.
4. **Late Student Interventions**: Academic failure detected only after end-semester examinations rather than continuously through explainable predictive risk analytics.

MiniLMS resolves these challenges by anchoring business rules, concurrency locks, data privacy filters, and audit logs directly within **MySQL 8.0 declarative constraints, stored programs, and database triggers**.

---

## Key Features

- **Relational Integrity by Design**: 30 BCNF-normalized base tables, 41 foreign keys with cascade/restrict rules, and 19 CHECK constraints.
- **ACID Transactions & Concurrency**: Pessimistic row-level locking (`SELECT ... FOR UPDATE`) in `sp_enroll_student` eliminating registration race conditions.
- **Automated Trigger Auditing**: 23 database triggers writing immutable forensic logs of all DML events (`INSERT`, `UPDATE`, `DELETE`) with pre- and post-operation JSON state diffs.
- **Explainable Academic Early Warning System (EWS)**: Multi-factor student risk calculation evaluating Attendance ($40\%$), Assessment Marks ($40\%$), and LMS Activity ($20\%$) implemented via MySQL stored function `fn_calculate_risk_score`.
- **FERPA Data Privacy Masking**: Relational views (`v_student_public_directory`, `v_audit_summary_masked`) providing field-level redaction of telephone numbers, personal emails, and network IPs.
- **Advanced SQL Analytics**: 25 production SQL queries employing Common Table Expressions (CTEs), window ranking functions (`DENSE_RANK()`), and hierarchical rollups.
- **Institutional Reporting Suite**: 16 parameter-driven reports with Chart.js visualization, CSV export, and PDF generation.
- **Database DevOps**: Automated forward-and-rollback schema migration framework managing versions `v001` through `v012`.
- **Disaster Recovery**: Automated point-in-time recovery and verification drill achieving 100% database parity.

---

## Technology Stack

| Layer | Technology / Tool | Version / Purpose |
| :--- | :--- | :--- |
| **Database Engine** | MySQL Server (Community Edition) | 8.0 (InnoDB Engine with ACID & MVCC support) |
| **Backend Runtime** | Python | 3.10+ (PyMySQL connection driver) |
| **Web Framework** | Flask | 3.x (18 Modular Blueprints, Jinja2 Templates) |
| **Authentication** | Flask-Login & Werkzeug | Cryptographic password hashing (bcrypt / scrypt) |
| **Visualization** | Chart.js | 4.x (Dynamic grade distributions, risk charts) |
| **DevOps & Containers** | Docker, Gunicorn, Nginx | Multi-stage Dockerfile, docker-compose orchestration |

---

## Stakeholder Roles & Portals

MiniLMS implements granular Role-Based Access Control (RBAC) across four distinct stakeholder personas:

1. **Administrator (Dean / Registrar)**:
   - System configuration, department and course catalog management, user onboarding.
   - Institutional KPI dashboards, university-wide grade distributions, and full security audit trails.
2. **Instructor (Faculty)**:
   - Course offering management, modular lesson organization, and assignment creation.
   - Session-level attendance marking, rubric-based submission grading, and student risk triage.
3. **Student**:
   - Course catalog exploration, prerequisite-validated enrollment, and lesson completion tracking.
   - Continuous assessment submission, quiz attempts with instant feedback, and grade appeal filing.
4. **Parent / Guardian**:
   - M:N guardian linkage allowing parents to monitor attendance records, fee status, and academic progress for dependent students.

---

## System Architecture

MiniLMS is organized according to a decoupled 3-tier architectural model:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION TIER                               │
│  - 18 Modular Flask Blueprints (Domain-driven controller routes)       │
│  - Semantic Jinja2 Server-Side Templates                               │
│  - Responsive CSS & Interactive Chart.js Visualizations                │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST / Form Submissions
┌───────────────────────────────────▼────────────────────────────────────┐
│                         BUSINESS LOGIC TIER                            │
│  - Domain Services (Enrollment, Grading, Attendance, Risk Analytics)   │
│  - Role-Based Access Control (RBAC: Admin, Instructor, Student, Parent)│
│  - PyMySQL Connection Pool with context-managed transactions           │
│  - Explainable Academic Early Warning Engine (40/40/20 heuristic)      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Parameterized SQL over TCP/IP
┌───────────────────────────────────▼────────────────────────────────────┐
│                          DATA STORAGE TIER                             │
│  - MySQL 8.0 InnoDB Storage Engine (Row-level locking, MVCC)          │
│  - 30 Physical Base Relational Tables (BCNF normalized)                │
│  - 14 Relational Views (Analytics, Rollups, FERPA Privacy Masking)     │
│  - 11 Stored Procedures & 2 Deterministic Stored Functions             │
│  - 23 Active Database Triggers (Automated audits, capacity checks)     │
│  - 41 Foreign Keys, 22 Unique Keys, 19 CHECK Constraints               │
│  - 19 Workload-Specific B-Tree Performance Indexes                     │
└────────────────────────────────────────────────────────────────────────┘
```

For complete architectural specifications, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Database Architecture

The schema features 30 physical base tables structured into five functional domains:

1. **Identity & RBAC**: `users`, `students`, `teachers`, `parents`, `parent_student_map`.
2. **Curriculum & Scheduling**: `departments`, `courses`, `academic_terms`, `course_offerings`, `course_instructors`, `modules`, `lessons`, `lesson_prerequisites`, `lesson_progress`.
3. **Enrollment & Attendance**: `enrollments`, `attendance_sessions`, `attendance_records`.
4. **Assessment & Grading**: `assignments`, `submissions`, `quizzes`, `quiz_questions`, `quiz_options`, `quiz_attempts`, `grades`, `grade_appeals`, `certificates`.
5. **Governance & Analytics**: `announcements`, `academic_risks`, `academic_interventions`, `audit_logs`, `schema_versions`.

For schema definitions, normalization proofs, and relational diagrams, see [docs/DATABASE_DESIGN.md](docs/DATABASE_DESIGN.md).

---

## Important Database Capabilities

### 1. Concurrency Control in Course Enrollment
When concurrent students attempt to enroll in a course offering near maximum capacity, `sp_enroll_student` acquires a row lock:

```sql
-- Excerpt from database/procedures/sp_enroll_student.sql
START TRANSACTION;
SELECT current_enrolled, max_capacity 
FROM course_offerings 
WHERE offering_id = p_offering_id 
FOR UPDATE;

IF v_current_enrolled >= v_max_capacity THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Course offering has reached maximum capacity';
END IF;
-- Perform enrollment insert and increment current_enrolled atomically
COMMIT;
```

### 2. Explainable Early Warning Calculation
Student risk level is computed deterministically inside MySQL:

```sql
-- Excerpt from database/functions/fn_calculate_risk_score.sql
-- Composite score = 40% Attendance deficit + 40% Mark deficit + 20% LMS Inactivity
SET v_risk_score = (GREATEST(0, (75.0 - p_att_pct)) * 0.40 * (100.0 / 75.0)) +
                   (GREATEST(0, (50.0 - p_avg_marks)) * 0.40 * (100.0 / 50.0)) +
                   (GREATEST(0, (10 - p_login_count)) * 0.20 * (100.0 / 10.0));
RETURN LEAST(100.0, GREATEST(0.0, v_risk_score));
```

### 3. FERPA Privacy Masking View
Contact details are masked dynamically for non-privileged directory lookups:

```sql
-- Excerpt from database/views/v_student_public_directory.sql
CREATE VIEW v_student_public_directory AS
SELECT 
    s.student_id,
    u.full_name,
    CONCAT(LEFT(u.email, 1), '***@', SUBSTRING_INDEX(u.email, '@', -1)) AS masked_email,
    CONCAT('XXXXXX', RIGHT(s.phone, 4)) AS masked_phone,
    s.program,
    s.semester
FROM students s
JOIN users u ON s.user_id = u.user_id
WHERE u.is_active = 1;
```

---

## Core Application Workflows

MiniLMS organizes academic operations across five interconnected workflows:

| Workflow | Description | Target Role |
| :--- | :--- | :---: |
| **Executive Dashboard** | University-wide enrollment, department GPAs, retention metrics | Admin |
| **Early Warning Triage** | Automated 40/40/20 composite risk scoring and intervention tracking | Admin / Instructor |
| **Grading & Assessment** | Continuous assessment submissions, rubric marking, GPA updates | Instructor |
| **Modular Learning** | Lesson sequencing, prerequisite locking, progress tracking | Student |
| **Student Directory** | FERPA-compliant privacy masking of sensitive contact details | All |

---

## Installation & Local Setup

### 1. Prerequisites
- **Python**: 3.10+
- **MySQL Server**: 8.0+
- **Git**

### 2. Clone the Repository
```bash
git clone https://github.com/<your-username>/MiniLMS.git
cd MiniLMS
```

### 3. Virtual Environment Setup
```bash
# On Linux / macOS
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Database Initialization & Migrations

### 1. Create MySQL Database
```sql
CREATE DATABASE minilms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and update your database credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=minilms_db
SECRET_KEY=generate_a_secure_random_key_here
PORT=5000
```

### 3. Run Automated Migrations
Apply baseline schema and all incremental migration scripts (`v001` through `v012`):
```bash
python database/migrate.py
```

### 4. Seed Demo Credentials
Seed demonstration user accounts across all 4 stakeholder roles:
```bash
python database/seed_passwords.py
```

---

## Application Startup

### Development Mode
```bash
python run.py
```
Open **http://127.0.0.1:5000** in your web browser.

#### Demo User Credentials

| Role | Username | Password | Email |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | `admin@minilms.edu` |
| **Instructor** | `prof_sharma` | `prof123` | `rajesh.sharma@minilms.edu` |
| **Student** | `student_arun` | `student123` | `arun.patel@minilms.edu` |
| **Parent** | `parent_ramesh` | `parent123` | `ramesh.patel@example.com` |

---

## Production Deployment

### Option 1: Docker Compose (Recommended)
Launch containerized MySQL 8.0 and the Gunicorn Flask web server:
```bash
docker-compose -f deployment/docker-compose.yml up -d --build
```

### Option 2: Production WSGI Server
Run with Gunicorn (Linux/macOS) or Waitress (Windows):
```bash
# Linux / macOS (Gunicorn)
gunicorn --workers 4 --bind 0.0.0.0:5000 wsgi:application

# Windows (Waitress)
waitress-serve --port=5000 wsgi:application
```

---

## Repository Structure

```text
MiniLMS/
├── app/                        # Flask application source
│   ├── auth/                   # Authentication & RBAC decorators
│   ├── routes/                 # 19 Modular domain Blueprints
│   ├── services/               # Core business logic services
│   ├── static/                 # CSS & JavaScript client assets
│   ├── templates/              # Jinja2 presentation templates
│   ├── config.py               # Twelve-factor configuration
│   ├── db.py                   # PyMySQL connection pool & transaction manager
│   └── __init__.py             # Application factory
│
├── database/                   # Database engineering scripts
│   ├── schema/                 # Master relational DDL schema
│   │   └── schema.sql
│   ├── migrations/             # Incremental versioned migrations (v006 - v012)
│   ├── queries/                # Advanced 25-query SQL portfolio
│   │   └── queries.sql
│   ├── security/               # Database user roles, privileges & restricted views
│   ├── migrate.py              # Automated migration execution engine
│   └── seed_passwords.py       # Cryptographic password generator & role seeder
│
├── deployment/                 # Production deployment configuration
│   ├── Dockerfile              # Security-hardened container specification
│   ├── docker-compose.yml      # Multi-container orchestration (Web + MySQL 8.0)
│   ├── nginx.conf              # Reverse proxy configuration
│   ├── systemd/                # Linux systemd service unit
│   └── README.md               # Infrastructure deployment manual
│
├── docs/                       # Technical architecture & design documentation
│   ├── ARCHITECTURE.md         # Multi-tier system architecture
│   ├── DATABASE_DESIGN.md      # Schema specifications & BCNF proofs
│   ├── INSTALLATION.md         # Detailed installation guide
│   └── SECURITY.md             # Security architecture & RBAC
│
├── .github/                    # CI/CD configuration
│   └── workflows/smoke_test.yml # GitHub Actions code quality workflow
│
├── .env.example                # Template environment variables
├── .gitignore                  # Git exclusion rules
├── LICENSE                     # MIT Open Source License
├── README.md                   # Project documentation
├── requirements.txt            # Python dependencies
├── run.py                      # Flask development entry point
└── wsgi.py                     # WSGI standard callable
```
├── SECURITY.md                 # Security advisory policy
└── LICENSE                     # MIT Open Source License
```

---

## Verified Technical Results

The technical baseline of MiniLMS has been independently validated:

- **Schema Scale**: 30 physical base tables, 14 relational views, 11 stored procedures, 2 stored functions, 23 triggers, and 41 foreign keys operating with zero integrity violations.
- **Data Profiling**: 613 verified demonstration records in `minilms_db`, and 25,147 synthetic records scaled across 30 tables in `minilms_benchmark_db`.
- **Query Performance**: Dedicated workload indexes maintain sub-3ms average execution across high-frequency institutional reports and windowed rankings under synthetic load.
- **Disaster Recovery**: Automated point-in-time recovery drill restored 100% of tables, views, triggers, and routines with zero byte discrepancies.

---

## Known Limitations

1. **Horizontal Scaling**: Designed as a single-primary MySQL 8.0 relational architecture; high-concurrency multi-region deployments require MySQL Group Replication or Galera Cluster read replicas.
2. **File Storage**: Assignment submission files are currently persisted on local or container file volumes; enterprise production requires object storage backends (AWS S3 / GCP Cloud Storage).
3. **Real-Time WebSockets**: Notifications and chat utilize HTTP polling; asynchronous Push Notifications or WebSocket channels represent a natural future enhancement.

---

## Future Roadmap

- [ ] **Multi-Tenant Sharding**: Support multiple university campuses using tenant-keyed relational partitioning.
- [ ] **S3 / Cloud Storage Integration**: Pluggable storage drivers for assignment file attachments.
- [ ] **LTI 1.3 / IMS Global Compliance**: Learning Tools Interoperability for third-party tool integration.
- [ ] **Automated Proctoring**: Real-time event streaming for online quiz attempt surveillance.

---

## Contributing & Security

- Contributions are welcome! Please open an issue or submit a pull request following standard Git feature-branch workflows.
- For security vulnerabilities, please refer to our [Security Policy](SECURITY.md).

---

## License

This project is licensed under the terms of the [MIT License](LICENSE).
