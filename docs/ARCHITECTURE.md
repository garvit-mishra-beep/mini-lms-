# MiniLMS System Architecture

## 1. Architectural Overview

MiniLMS is architected as an enterprise-grade, relational academic management and analytics platform. Built using Python, Flask, and MySQL 8.0 InnoDB, the system prioritizes **database-enforced data integrity**, strict **ACID transactional semantics**, and **clear separation of concerns** across a 3-tier architectural model.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION TIER                               │
│  - 18 Modular Flask Blueprints (Modular routing & request validation)  │
│  - Semantic Jinja2 Server-Side Templates                               │
│  - Responsive CSS / Vanilla JS & Chart.js Visualizations              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST / Form Submissions
┌───────────────────────────────────▼────────────────────────────────────┐
│                         BUSINESS LOGIC TIER                            │
│  - Service Layer (enrollment, grading, attendance, risk analysis)      │
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

---

## 2. Multi-Tier Layer Responsibilities

### 2.1 Presentation Tier
- **Routing & Controllers**: 18 specialized Flask Blueprints located in `app/routes/` organize route handling by domain (`auth`, `courses`, `enrollments`, `students`, `teachers`, `attendance`, `assignments`, `grades`, `quizzes`, `modules`, `coordinator`, `intelligence`, `analytics`, `audit`, `certificates`, `explorer`, `settings`, `announcements`).
- **Template Rendering**: Modular Jinja2 templates in `app/templates/` extend a unified `base.html` shell.
- **Client Assets**: Lightweight vanilla JavaScript and Chart.js 4.x render interactive grade distributions, enrollment trends, and risk triage charts without heavy frontend dependencies.

### 2.2 Business Logic Tier
- **Domain Services**: Encapsulate operational rules in `app/services/` (`academic_service.py`, `enrollment_service.py`, `grading_service.py`, `reporting_service.py`, `risk_service.py`, `user_service.py`, `file_service.py`).
- **Connection Management**: `app/db.py` provides context managers (`get_db_connection()`, `transaction()`) over PyMySQL, ensuring deterministic transaction commits, automated rollbacks on exceptions, and explicit connection reuse.
- **Early Warning Engine**: Executes an explainable multi-factor evaluation algorithm ($40\%$ Attendance + $40\%$ Continuous Assessment Marks + $20\%$ LMS Activity) to detect students at academic risk before final examinations.

### 2.3 Data Storage Tier
- **Storage Engine**: MySQL 8.0 InnoDB provides robust ACID guarantees, foreign key cascades, and row-level locking (`SELECT ... FOR UPDATE`).
- **In-Database Computations**: Complex calculations (such as risk score determination, grade-to-letter translation, and audit logging) are implemented directly in MySQL stored programs and triggers to prevent distributed state discrepancies.

---

## 3. Concurrency Control and Transaction Model

MiniLMS enforces explicit transaction isolation to eliminate common multi-user anomalies:

1. **Course Capacity Enforcement**:
   - `sp_enroll_student` executes within a serializable transaction block utilizing `SELECT current_enrolled, max_capacity FROM course_offerings WHERE offering_id = ? FOR UPDATE`.
   - Acquires an exclusive row-level lock on the offering record, preventing race conditions and over-enrollment under concurrent seat requests.
2. **Attendance Batch Ingestion**:
   - `sp_bulk_record_attendance` atomically commits or rolls back entire class rosters, guaranteeing that attendance records and associated audit entries remain synchronized.
3. **Trigger-Based Immutability**:
   - `trg_prevent_attendance_tampering` rejects unauthorized retroactive updates to historical attendance records, preserving forensic chain of custody.

---

## 4. Production Process Model

In production environments, MiniLMS runs behind an industry-standard reverse proxy and WSGI application server:
- **Nginx**: Handles SSL/TLS termination, request buffering, static asset caching, and rate limiting.
- **Gunicorn / Waitress**: Executes multiple pre-forked worker processes running `wsgi.py` (Gunicorn on POSIX, Waitress on Windows).
- **Environment Parity**: Configured strictly via environment variables following Twelve-Factor App principles.
