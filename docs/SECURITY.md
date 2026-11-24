# MiniLMS Security Architecture and Compliance

## 1. Security Overview

MiniLMS incorporates multi-layered defense-in-depth security covering database authentication, authorization, session hygiene, parameter escaping, data masking, and automated forensic auditing.

---

## 2. Role-Based Access Control (RBAC)

The application enforces strict role-based authorization across four operational roles:

```
┌────────────────────────────────────────────────────────────────────────┐
│                              ADMIN                                     │
│  - User provisioning, role assignments, department & course creation   │
│  - Full access to security audit trails and system configurations       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
       ┌────────────────────────────┴───────────────────────────┐
       ▼                                                        ▼
┌──────────────┐                                         ┌──────────────┐
│  INSTRUCTOR  │                                         │   STUDENT    │
│  - Syllabus  │                                         │  - Modules   │
│  - Attendance│                                         │  - Quizzes   │
│  - Grading   │                                         │  - Progress  │
└──────┬───────┘                                         └──────┬───────┘
       │                                                        │
       └────────────────────────────┬───────────────────────────┘
                                    ▼
                             ┌──────────────┐
                             │    PARENT    │
                             │  - Progress  │
                             │  - Attendance│
                             └──────────────┘
```

- **Enforcement**: Routes are protected via `@login_required` and custom `@role_required(['Admin', 'Instructor'])` decorators (`app/auth/decorators.py`).
- **Session Protection**: Flask sessions utilize `HttpOnly`, `SameSite=Lax`, and configurable `Secure` flags to mitigate Cross-Site Scripting (XSS) session hijacking.

---

## 3. SQL Injection Defense

MiniLMS enforces **100% parameterized SQL query execution** across all database interactions:
- Application queries execute through `execute_query(sql, params)` in `app/db.py`, ensuring all user-supplied data is passed as parameterized tuple inputs to PyMySQL.
- Stored procedures (`sp_enroll_student`, `sp_bulk_record_attendance`) encapsulate procedural DML, preventing dynamic SQL concatenation.
- All search and filter forms pass through sanitized database parameters.

---

## 4. Password Security and Storage

- User credentials use industry-standard **bcrypt** and **scrypt** cryptographic hashing with unique salt generation.
- Raw passwords are never persisted in database tables, memory dumps, or log files.
- Authentication attempts verify against `password_hash` via `werkzeug.security.check_password_hash`.

---

## 5. FERPA Data Privacy & Data Masking

To comply with academic privacy regulations (e.g., Family Educational Rights and Privacy Act - FERPA):
- **`v_student_public_directory`**: Public campus directory queries access a privacy-masked view that redacts sensitive personal telephone numbers (`CONCAT('XXXXXX', RIGHT(phone, 4))`) and masks personal email domains.
- **`v_audit_summary_masked`**: Masks internal IP addresses and sensitive user payload details for non-super-admin compliance reviewers.

---

## 6. Database Audit Trails and Forensics

- **Trigger-Based Auditing**: 23 database triggers automatically write immutable audit logs on insert, update, or delete operations affecting critical entities (`users`, `courses`, `enrollments`, `grades`, `attendance_records`).
- **Audit Schema**: `audit_logs` captures:
  - `user_id`: Authenticated user executing the action.
  - `action`: Specific operation type (`INSERT`, `UPDATE`, `DELETE`, `LOGIN`, `RISK_ASSESSMENT`).
  - `table_name`: Target relational entity.
  - `record_id`: Clustered key of the modified record.
  - `old_values` / `new_values`: JSON payloads capturing pre- and post-operation states.
  - `ip_address`: Client network address.
  - `timestamp`: UTC timestamp of event occurrence.
- **Tampering Resistance**: `trg_prevent_attendance_tampering` prevents retroactive modifications to verified attendance sessions.
