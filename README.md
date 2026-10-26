# MiniLMS — Full-Stack Educational Platform & DBMS Showcase

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-black.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-4479A1.svg?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Tests](https://img.shields.io/badge/Tests-16%20Passed-success.svg?logo=pytest&logoColor=white)](tests/test_minilms.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-ready, full-stack Learning Management System (LMS) built with **Python Flask**, **MySQL 8.0**, and **Vanilla Modern CSS/JavaScript**. Designed to demonstrate enterprise relational database management, multi-role RBAC security, ACID transactions, and live analytical dashboards.

---

## 🚀 Key Architectural Highlights

### 1. Robust Relational Constraints & Atomic Transactions
- **Duplicate Enrollment Prevention**: Handles uniqueness on `(student_id, course_id)` via atomic stored procedure `sp_enroll`. Detects existing active enrollments with row-level locks (`FOR UPDATE`), returning user-friendly conflict resolution messages rather than unhandled MySQL error 1062.
- **Course Publishing Guard**: MySQL trigger `trg_course_publish` prevents publishing courses without at least one assigned, authorized faculty instructor.
- **Prerequisite Validation**: Trigger `trg_prerequisite_validate` enforces that lesson prerequisites remain in the same course and prevents cyclic dependencies via recursive CTE checks.
- **Comprehensive Audit Trails**: All quiz attempt submissions, enrollment operations, and authorized grade corrections via `sp_correct_published_grade` are audited in `audit_logs` and `grade_change_history`.

### 2. Multi-Role Authentication & Access Control
- **Administrator**: Complete system control over users, courses, faculty assignments, system diagnostics, and exclusive access to the **Database Explorer**.
- **Teacher / Faculty**: Restricted course syllabus management, module & lesson sequencing, quiz administration, gradebook review, authorized grade corrections, and certificate generation **strictly for courses they are assigned to**.
- **Student**: Course catalog browsing, atomic self-enrollment, interactive lesson reader, quiz assessments with server-side grading, and verifiable certificate viewing.
- **Controlled Demo Role Switcher**: 1-click header role switcher is strictly gated by the `DEMO_MODE=true` configuration flag and local loopback IP checks, preventing unauthorized privilege escalation in production deployments.

### 3. Server-Side CSRF & Error Containment
- **CSRF Protection**: Cryptographically secure, session-bound CSRF tokens are injected into all HTML forms and verified on all `POST`, `PUT`, `DELETE`, and `PATCH` requests via `before_request`. Invalid tokens are rejected with HTTP 400.
- **Error Information Protection**: Internal database exceptions and SQL syntax errors are masked from user-facing templates and JSON endpoints unless `DEBUG=True`.

### 4. Interactive Quiz Engine
- Normalized relational tables: `quiz_questions`, `quiz_options`, and `attempt_answers`.
- Server-side answer evaluation ensuring scores cannot be forged by client browsers.
- Real-time score calculation, percentage display, and attempt history tracking.

### 5. Live Visual Analytics (Chart.js)
- Real-time charts for Course Enrollments, Grade Distributions, Completion Percentages, and Quiz Performance powered directly by live SQL views (`v_course_enrollments`, `v_student_grades`, `v_course_completion`, `v_quiz_performance`).

### 6. DBMS Showcase & Database Explorer (Admin Only)
- Visual schema inspection for all 21 base tables and 5 SQL views.
- Table metadata inspection: data types, nullable constraints, keys (`PRI`, `UNI`, `MUL`), defaults, and foreign key relationships.
- Curated SQL demonstration workbench:
  - 5-table Relational JOINs
  - MySQL 8.0 Window Functions (`DENSE_RANK() OVER (PARTITION BY ... ORDER BY ...)`)
  - Aggregations with `GROUP BY` and `HAVING`
  - Correlated Subqueries with `NOT EXISTS`
  - Common Table Expressions (CTEs)

---

## 🛠️ Installation & Setup

### Prerequisites
1. **Python 3.10+**
2. **MySQL 8.0+** running locally (default port: `3306`)
3. **Git**

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/garvit-mishra-beep/mini-lms-.git
cd mini-lms-
```

### Step 2: Set Up Python Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create your local `.env` from the provided template:
```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```
Edit `.env` and set your MySQL root password:
```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_actual_mysql_password
DB_NAME=minilms_db
TEST_DB_NAME=minilms_test_db
FLASK_SECRET_KEY=generate_a_random_secret_key_here
PORT=5000
DEMO_MODE=true
DEMO_USER_PASSWORD=MiniLMS@2026
```

### Step 5: Initialize the MySQL Database
Import the starter database schema and seed data:
```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS minilms_db;"
mysql -u root -p minilms_db < database/schema/schema.sql
```

Apply migrations and initialize password hashes:
```bash
python database/migrate.py
python database/seed_passwords.py
```

### Step 6: Launch MiniLMS

#### Option A: Interactive Windows Operations Menu
Double-click `start_windows.bat` or run:
```cmd
start_windows.bat
```
Choose `[1]` to launch the server with automatic health checks.

#### Option B: Direct Python Execution
```bash
python run.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## 👥 Default Demo Credentials

When `DEMO_MODE=true`, you can switch between roles with 1 click in the top navigation bar, or log in manually with the following accounts:

| Role | Full Name | Email | Password | Assigned Courses |
|---|---|---|---|---|
| **Administrator** | Demo Admin | `admin@example.test` | `MiniLMS@2026` | System Wide (Full Access) |
| **Faculty / Teacher** | Dr Anita Sharma | `anita@example.test` | `MiniLMS@2026` | CS101, CS201 |
| **Faculty / Teacher** | Prof Raj Mehta | `raj@example.test` | `MiniLMS@2026` | CS202, CS301 |
| **Student** | Aarav Singh | `aarav@example.test` | `MiniLMS@2026` | Enrolled Courses |
| **Student** | Diya Gupta | `diya@example.test` | `MiniLMS@2026` | Enrolled Courses |

---

## 🧪 Automated Testing

The automated test suite in `tests/test_minilms.py` verifies all 16 core security and concurrency business rules:

| # | Test Case | Description |
|---|---|---|
| 1 | `test_post_without_csrf_rejected` | HTTP 400 rejection on unverified CSRF POST requests |
| 2 | `test_login_success_and_logout` | Complete session lifecycle verification |
| 3 | `test_login_invalid_credentials` | Rejection of bad credentials |
| 4 | `test_demo_login_restricted_when_disabled` | HTTP 403 when `DEMO_MODE=False` |
| 5 | `test_student_cannot_access_admin_route` | HTTP 403 RBAC authorization guard |
| 6 | `test_student_cannot_access_database_explorer`| Database Explorer protected from students |
| 7 | `test_unassigned_teacher_cannot_manage_grades`| Teacher course isolation enforcement |
| 8 | `test_dashboard_loading` | Analytical dashboard loading and SQL view verification |
| 9 | `test_duplicate_enrollment_prevention` | Atomic duplicate prevention via `sp_enroll` |
| 10 | `test_inactive_student_enrollment_blocked` | Inactive status verification at DB & service layer |
| 11 | `test_unpublished_course_enrollment_blocked`| Draft course enrollment rejection |
| 12 | `test_quiz_server_side_scoring` | Server-side quiz calculation and attempt recording |
| 13 | `test_authorized_grade_correction` | Audit logging in `grade_change_history` |
| 14 | `test_database_explorer_loads_for_admin` | Schema introspection verification |
| 15 | `test_concurrent_duplicate_enrollment` | Multi-threaded race condition safety (1 success, 1 conflict) |
| 16 | `test_health_check_endpoint` | System diagnostic & DB ping health check |

Run the test suite directly with:
```bash
python -m unittest tests/test_minilms.py -v
```

---

## 📂 Project Structure

```text
MiniLMS/
├── app/
│   ├── __init__.py           # Flask application factory, CSRF filter, error sanitizers
│   ├── config.py             # Environment configuration & secret key resolution
│   ├── db.py                 # PyMySQL connection pool, transaction context & query helpers
│   ├── auth/                 # User model, session management & RBAC decorators
│   ├── services/             # Core business logic (enrollment, quiz evaluation, grading)
│   ├── routes/               # Modular Flask blueprints (dashboard, courses, quizzes, explorer)
│   ├── templates/            # Jinja2 templates with component hierarchy
│   └── static/
│       ├── css/style.css     # Responsive design system with dark/light mode
│       └── js/main.js        # Theme toggle, sidebar navigation & client-side interactions
├── database/
│   ├── schema/
│   │   └── schema.sql        # Complete baseline schema and demo dataset
│   ├── migrations/           # Version-controlled idempotent SQL migrations
│   ├── rollback/             # Reversible rollback definitions
│   ├── migrate.py            # Automated migration execution runner
│   ├── rollback.py           # Automated schema version rollback runner
│   └── seed_passwords.py     # Secure demo account password initializer
├── tests/
│   └── test_minilms.py       # 16-case automated unit, security & concurrency test suite
├── app.py                    # Server entry point
├── run.py                    # Standalone development server runner
├── requirements.txt          # Python project dependencies
├── .env.example              # Sanitized configuration template
├── .gitignore                # Production ignore rules
├── start_windows.bat         # Interactive Windows 11 operations launcher
├── LICENSE                   # MIT License
└── README.md                 # Project documentation
```

---

## 🔒 Security Best Practices

1. **Never commit `.env`**: Always keep actual passwords and secret keys inside `.env` (guaranteed by `.gitignore`).
2. **Production Mode**: When deploying outside of local demonstration, ensure `DEMO_MODE=false` in `.env`.
3. **Database Credentials**: Never use MySQL `root` without a password or in public environments.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
