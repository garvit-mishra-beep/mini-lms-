# MiniLMS Installation and Setup Guide

## 1. Prerequisites

Before installing MiniLMS, ensure your system meets the following requirements:

- **Operating System**: Windows 10/11, Ubuntu 20.04+, macOS 12+
- **Python**: Version 3.10, 3.11, or 3.12 (Python 3.14 compatible)
- **Database**: MySQL Server 8.0 Community Edition (or higher)
- **Git**: Version 2.30+

---

## 2. Local Environment Setup

### 2.1 Clone the Repository
```bash
git clone https://github.com/<your-username>/MiniLMS.git
cd MiniLMS
```

### 2.2 Create and Activate a Python Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2.3 Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Database Initialization

### 3.1 Configure MySQL Server
Ensure MySQL 8.0 service is running and accessible on port `3306`. Create an empty database:

```sql
CREATE DATABASE minilms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3.2 Configure Environment Variables
Copy `.env.example` to `.env` and configure your database connection parameters:

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
SECRET_KEY=generate_a_secure_random_key
PORT=5000
FLASK_ENV=development
```

### 3.3 Apply Database Schema & Migrations
Execute the automated migration runner to apply baseline schema and incremental migrations (`v001` through `v012`):

```bash
python scripts/run_migrations.py
```

### 3.4 Seed Demonstration Data & Password Hashes
Seed demo user accounts across all 4 stakeholder roles:

```bash
python database/seed_passwords.py
```

---

## 4. Launching the Application

### 4.1 Development Mode
Run using the Flask development server:
```bash
python run.py
```
Open your browser and navigate to: **http://127.0.0.1:5000**

### 4.2 Production Mode (WSGI)
**On Windows (Waitress):**
```bash
python run_production.py
```

**On Linux / Docker (Gunicorn):**
```bash
gunicorn --workers 4 --bind 0.0.0.0:5000 wsgi:application
```

---

## 5. Docker Deployment

To launch MiniLMS with containerized MySQL and web application services:

```bash
docker-compose -f deployment/docker-compose.yml up -d --build
```
The application will be available at **http://localhost:5000**.

---

## 6. Seed Accounts for Local Testing

| Role | Username | Email | Default Demo Password | Access Rights |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin@minilms.edu` | `admin123` | Full system administration, audit logs, DevOps, user provisioning |
| **Instructor** | `prof_sharma` | `rajesh.sharma@minilms.edu` | `prof123` | Course management, attendance recording, grading, rubric evaluations |
| **Student** | `student_arun` | `arun.patel@minilms.edu` | `student123` | Enrolled courses, modular lessons, quiz attempts, grade visibility |
| **Parent** | `parent_ramesh` | `ramesh.patel@example.com` | `parent123` | Student academic progress, attendance monitoring, fee alerts |
