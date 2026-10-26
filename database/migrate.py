"""MiniLMS Migration Runner
Runs versioned SQL migrations safely, checking schema_versions table.
"""
import os
import glob
import shutil
import subprocess
import pymysql
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'minilms_db'),
        charset='utf8mb4',
        autocommit=False
    )

def find_mysql_binary():
    # 1. PATH search
    which_mysql = shutil.which('mysql')
    if which_mysql:
        return which_mysql
    # 2. Known default Windows paths
    candidates = [
        r'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe',
        r'C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe',
        r'C:\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe',
        r'C:\xampp\mysql\bin\mysql.exe',
        r'C:\laragon\bin\mysql\current\bin\mysql.exe'
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def ensure_schema_versions(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS `schema_versions` (
              `version_no` int NOT NULL,
              `description` varchar(200) NOT NULL,
              `applied_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`version_no`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
    conn.commit()

def get_applied_versions(conn):
    ensure_schema_versions(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT version_no FROM schema_versions ORDER BY version_no;")
        return set(r[0] for r in cur.fetchall())

def run_migrations():
    conn = get_connection()
    applied = get_applied_versions(conn)
    print(f"[*] Currently applied versions: {sorted(list(applied)) if applied else 'None'}")

    migration_files = sorted(glob.glob(os.path.join(os.path.dirname(__file__), 'migrations', 'v*.sql')))
    if not migration_files:
        print("[!] No migration files found in database/migrations/")
        conn.close()
        return

    mysql_exe = find_mysql_binary()

    for fpath in migration_files:
        fname = os.path.basename(fpath)
        vnum_str = fname.split('_')[0].lstrip('v')
        try:
            vnum = int(vnum_str)
        except ValueError:
            continue

        if vnum in applied:
            print(f"[OK] Skipping {fname} (version {vnum} already recorded)")
            continue

        print(f"[+] Applying migration: {fname}...")
        with open(fpath, 'r', encoding='utf-8') as f:
            sql_text = f.read()

        if mysql_exe:
            cmd = [
                mysql_exe,
                '-h', os.getenv('DB_HOST', '127.0.0.1'),
                '-P', str(os.getenv('DB_PORT', '3306')),
                '-u', os.getenv('DB_USER', 'root'),
                f"--password={os.getenv('DB_PASSWORD', '')}",
                os.getenv('DB_NAME', 'minilms_db')
            ]
            res = subprocess.run(cmd, input=sql_text, text=True, capture_output=True)
            if res.returncode != 0:
                print(f"[X] Error executing migration {fname}:\n{res.stderr}")
                conn.close()
                raise RuntimeError(f"Migration {fname} failed: {res.stderr}")
        else:
            # Fallback execution via PyMySQL
            # Split on semicolons that are not inside DELIMITER blocks
            with conn.cursor() as cur:
                statements = [s.strip() for s in sql_text.split(';') if s.strip() and not s.strip().startswith('DELIMITER')]
                for stmt in statements:
                    cur.execute(stmt)
            conn.commit()

        # Verification step
        refreshed = get_applied_versions(conn)
        if vnum not in refreshed:
            # Explicitly record if the script didn't insert it
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO schema_versions (version_no, description, applied_at) VALUES (%s, %s, NOW()) ON DUPLICATE KEY UPDATE applied_at = NOW();",
                    (vnum, f"Applied from {fname}")
                )
            conn.commit()
            print(f"[OK] Recorded version {vnum} in schema_versions.")
        else:
            print(f"[OK] Migration {fname} applied and verified successfully.")

    conn.close()
    print("[*] All database migrations are up to date.")

if __name__ == '__main__':
    run_migrations()
