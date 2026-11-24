"""MiniLMS Zero-State Database Setup Script
Reinitializes the database from scratch:
1. Creates target database with utf8mb4 collation.
2. Applies baseline schema (schema.sql).
3. Sequentially executes all migrations (v006 through v012).
4. Optionally seeds initial test/dev datasets.
"""
import os
import sys
import argparse
from pathlib import Path
import pymysql
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from scripts.run_migrations import find_mysql_binary, run_migrations

def get_server_connection():
    """Connects to MySQL server without selecting a specific database."""
    return pymysql.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        charset='utf8mb4',
        autocommit=True
    )

def setup_database(database_name=None, drop_existing=False, seed_data=False):
    """Sets up a complete, fully migrated database."""
    target_db = database_name or os.getenv('DB_NAME', 'minilms_db')
    print(f"\n=======================================================")
    print(f" MiniLMS Zero-State Database Setup: [{target_db}]")
    print(f"=======================================================")

    srv_conn = get_server_connection()
    with srv_conn.cursor() as cur:
        if drop_existing:
            print(f"[!] Dropping existing database `{target_db}` (if exists)...")
            cur.execute(f"DROP DATABASE IF EXISTS `{target_db}`;")
        print(f"[+] Creating database `{target_db}` (CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci)...")
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{target_db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    srv_conn.close()

    # Apply base schema
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema', 'schema.sql')
    if os.path.exists(schema_path):
        print(f"[+] Applying base schema from {os.path.basename(schema_path)}...")
        mysql_exe = find_mysql_binary()
        if mysql_exe:
            import subprocess
            cmd = [
                mysql_exe,
                '-h', os.getenv('DB_HOST', '127.0.0.1'),
                '-P', str(os.getenv('DB_PORT', '3306')),
                '-u', os.getenv('DB_USER', 'root'),
                f"--password={os.getenv('DB_PASSWORD', '')}",
                target_db
            ]
            with open(schema_path, 'r', encoding='utf-8') as sf:
                res = subprocess.run(cmd, stdin=sf, capture_output=True, text=True)
                if res.returncode != 0:
                    raise RuntimeError(f"Error applying base schema: {res.stderr}")
        else:
            raise RuntimeError("mysql binary not found to load schema.sql")
        print("[OK] Base schema applied successfully.")

    # Run all migrations up to v012
    print(f"[+] Applying version-controlled migrations up to v012...")
    res = run_migrations(target_db=target_db, dry_run=False)
    if res != 0:
        raise RuntimeError("Migration pipeline failed during setup.")

    # Seed data if requested
    if seed_data:
        print(f"[+] Seeding core development data...")
        from database.seed.seed_dev_data import seed_database
        seed_database(target_db)
        print("[OK] Core dev data seeded successfully.")

    print(f"\n[SUCCESS] Zero-state database setup complete for [{target_db}].\n")

def main():
    parser = argparse.ArgumentParser(description="MiniLMS Zero-State Database Setup")
    parser.add_argument('--target-db', type=str, default=None, help="Target database name (default: from .env)")
    parser.add_argument('--force-drop', action='store_true', help="Drop database if it already exists")
    parser.add_argument('--seed', action='store_true', help="Seed development dataset after migration")
    args = parser.parse_args()

    setup_database(
        database_name=args.target_db,
        drop_existing=args.force_drop,
        seed_data=args.seed
    )

if __name__ == '__main__':
    main()
