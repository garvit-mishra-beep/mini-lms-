"""MiniLMS Migration Automation Runner
Executes version-controlled SQL migrations in strict numeric sequence.
Inspects schema_versions, validates execution, and supports dry-run mode.
"""
import os
import sys
import glob
import shutil
import subprocess
import argparse
from pathlib import Path
import pymysql
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

def get_connection(database_name=None):
    """Establishes a PyMySQL connection to the specified database."""
    target_db = database_name or os.getenv('DB_NAME', 'minilms_db')
    return pymysql.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=target_db,
        charset='utf8mb4',
        autocommit=False
    )

def find_mysql_binary():
    """Locates the mysql client executable on Windows or Linux."""
    which_mysql = shutil.which('mysql')
    if which_mysql:
        return which_mysql
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

def ensure_schema_versions_table(conn):
    """Ensures that the schema_versions tracking table exists."""
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
    """Retrieves dict of {version_no: (description, applied_at)}."""
    ensure_schema_versions_table(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT version_no, description, applied_at FROM schema_versions ORDER BY version_no;")
        return {r[0]: {'description': r[1], 'applied_at': r[2]} for r in cur.fetchall()}

def discover_migrations(migrations_dir=None):
    """Discovers all migration SQL files and extracts their version numbers."""
    if migrations_dir is None:
        migrations_dir = os.path.join(os.path.dirname(__file__), '..', 'database', 'migrations')
    migrations_dir = os.path.abspath(migrations_dir)
    files = sorted(glob.glob(os.path.join(migrations_dir, 'v*.sql')))
    migrations = []
    for f in files:
        fname = os.path.basename(f)
        try:
            vnum = int(fname.split('_')[0].lstrip('v'))
            migrations.append({
                'version_no': vnum,
                'filename': fname,
                'path': f
            })
        except ValueError:
            continue
    migrations.sort(key=lambda m: m['version_no'])
    return migrations

def inspect_status(target_db=None):
    """Prints the current status of all migrations."""
    conn = get_connection(target_db)
    target = target_db or os.getenv('DB_NAME', 'minilms_db')
    print(f"\n=======================================================")
    print(f" MiniLMS Migration Status Report: [{target}]")
    print(f"=======================================================")
    applied = get_applied_versions(conn)
    migrations = discover_migrations()

    print(f"{'Version':<10} | {'Status':<12} | {'Filename':<42} | {'Applied At / Description'}")
    print("-" * 90)

    for m in migrations:
        vno = m['version_no']
        if vno in applied:
            info = applied[vno]
            applied_str = str(info['applied_at'])[:19]
            print(f"v{vno:<9} | {'APPLIED':<12} | {m['filename']:<42} | {applied_str}")
        else:
            print(f"v{vno:<9} | {'PENDING':<12} | {m['filename']:<42} | Pending Execution")
    
    # Check for versions in schema_versions not in migration files
    mig_vnos = {m['version_no'] for m in migrations}
    for vno, info in applied.items():
        if vno not in mig_vnos:
            applied_str = str(info['applied_at'])[:19]
            print(f"v{vno:<9} | {'HISTORIC':<12} | {'[Baseline/Legacy Record]':<42} | {applied_str} - {info['description']}")

    pending_count = sum(1 for m in migrations if m['version_no'] not in applied)
    print("-" * 90)
    print(f"Total Migrations: {len(migrations)} | Applied: {len(applied)} | Pending: {pending_count}\n")
    conn.close()
    return pending_count

def apply_migration_file(file_path, target_db):
    """Executes a single migration SQL file against the target database."""
    mysql_exe = find_mysql_binary()
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    target = target_db or os.getenv('DB_NAME', 'minilms_db')

    if mysql_exe:
        cmd = [
            mysql_exe,
            '-h', os.getenv('DB_HOST', '127.0.0.1'),
            '-P', str(os.getenv('DB_PORT', '3306')),
            '-u', os.getenv('DB_USER', 'root'),
            f"--password={os.getenv('DB_PASSWORD', '')}",
            target
        ]
        proc = subprocess.run(cmd, input=sql_content, text=True, capture_output=True)
        if proc.returncode != 0:
            raise RuntimeError(f"mysql execution error (code {proc.returncode}): {proc.stderr}")
    else:
        # Fallback multi-statement cursor execution
        conn = get_connection(target)
        try:
            with conn.cursor() as cur:
                statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('DELIMITER')]
                for stmt in statements:
                    cur.execute(stmt)
            conn.commit()
        finally:
            conn.close()

def run_migrations(target_db=None, dry_run=False):
    """Executes all pending migrations in strict numeric order."""
    conn = get_connection(target_db)
    target = target_db or os.getenv('DB_NAME', 'minilms_db')
    applied = get_applied_versions(conn)
    migrations = discover_migrations()

    pending = [m for m in migrations if m['version_no'] not in applied]

    if not pending:
        print(f"[*] Target [{target}] is fully up to date. No pending migrations.")
        conn.close()
        return 0

    print(f"[*] Found {len(pending)} pending migration(s) for [{target}]:")
    for m in pending:
        print(f"    - v{m['version_no']}: {m['filename']}")

    if dry_run:
        print("\n[DRY RUN] No migrations were executed.")
        conn.close()
        return 0

    print(f"\n[*] Applying migrations to [{target}]...")
    for m in pending:
        vno = m['version_no']
        fname = m['filename']
        print(f"[+] Applying v{vno}: {fname} ...", end=" ", flush=True)
        try:
            apply_migration_file(m['path'], target)
            # Verify version was recorded in schema_versions
            refreshed = get_applied_versions(conn)
            if vno not in refreshed:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO schema_versions (version_no, description, applied_at) VALUES (%s, %s, NOW()) ON DUPLICATE KEY UPDATE applied_at = NOW();",
                        (vno, f"Applied via run_migrations: {fname}")
                    )
                conn.commit()
            print("DONE [OK]")
        except Exception as e:
            print("FAILED [X]")
            print(f"[!] Error applying {fname}: {e}")
            conn.close()
            return 1

    conn.close()
    print(f"\n[OK] All pending migrations successfully applied to [{target}].")
    return 0

def main():
    parser = argparse.ArgumentParser(description="MiniLMS Migration Automation Runner")
    parser.add_argument('--status', action='store_true', help="Inspect migration status and exit")
    parser.add_argument('--dry-run', action='store_true', help="Preview pending migrations without applying")
    parser.add_argument('--target-db', type=str, default=None, help="Target database name (default: from .env DB_NAME)")
    args = parser.parse_args()

    if args.status:
        inspect_status(args.target_db)
        sys.exit(0)

    exit_code = run_migrations(target_db=args.target_db, dry_run=args.dry_run)
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
