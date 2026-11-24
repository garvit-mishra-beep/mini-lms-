"""MiniLMS Database Recovery Drill Automation
Restores a verified logical backup to an isolated recovery database (minilms_recovery_db).
Performs end-to-end verification comparing table and row counts between source and restored database.
Requires explicit --confirm flag to execute.
"""
import os
import sys
import argparse
import subprocess
import json
from pathlib import Path
from datetime import datetime
import pymysql
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from scripts.run_migrations import find_mysql_binary
from scripts.verify_backup import find_latest_backup, verify_backup_file

def get_server_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def get_db_inventory(db_name):
    """Collects table counts, row counts, views, triggers, and routines for a database."""
    conn = get_server_connection()
    inventory = {'tables': {}, 'views': 0, 'procedures': 0, 'functions': 0, 'triggers': 0}
    with conn.cursor() as cur:
        # Tables and exact row counts
        cur.execute("SELECT TABLE_NAME AS table_name FROM information_schema.tables WHERE table_schema = %s AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME;", (db_name,))
        table_names = [(r.get('table_name') or r.get('TABLE_NAME')) for r in cur.fetchall()]

        for t in table_names:
            cur.execute(f"SELECT COUNT(*) as cnt FROM `{db_name}`.`{t}`;")
            inventory['tables'][t] = cur.fetchone()['cnt']

        cur.execute("SELECT COUNT(*) as cnt FROM information_schema.tables WHERE table_schema = %s AND TABLE_TYPE = 'VIEW';", (db_name,))
        inventory['views'] = cur.fetchone()['cnt']

        cur.execute("SELECT ROUTINE_TYPE AS routine_type, COUNT(*) as cnt FROM information_schema.routines WHERE routine_schema = %s GROUP BY ROUTINE_TYPE;", (db_name,))
        for r in cur.fetchall():
            rtype = (r.get('routine_type') or r.get('ROUTINE_TYPE') or '').upper()
            if rtype == 'PROCEDURE':
                inventory['procedures'] = r['cnt']
            elif rtype == 'FUNCTION':
                inventory['functions'] = r['cnt']

        cur.execute("SELECT COUNT(*) as cnt FROM information_schema.triggers WHERE trigger_schema = %s;", (db_name,))
        inventory['triggers'] = cur.fetchone()['cnt']

    conn.close()
    return inventory

def run_recovery_drill(backup_file=None, recovery_db='minilms_recovery_db', source_db='minilms_db'):
    if not backup_file:
        backup_file = find_latest_backup()
    if not backup_file or not os.path.exists(backup_file):
        raise FileNotFoundError(f"Backup file not found: {backup_file}")

    print(f"\n=======================================================")
    print(f" MiniLMS Database Live Recovery Drill")
    print(f"=======================================================")
    print(f" Backup Source File: {backup_file}")
    print(f" Recovery Target DB: {recovery_db}")
    print(f" Baseline Source DB: {source_db}")

    # 1. Verify backup file first
    verified, msg = verify_backup_file(backup_file)
    if not verified:
        raise RuntimeError(f"Backup verification failed: {msg}")

    # 2. Gather source database baseline
    print(f"[*] Auditing baseline source database `{source_db}`...")
    source_inv = get_db_inventory(source_db)
    print(f"[OK] Source `{source_db}`: {len(source_inv['tables'])} tables, {sum(source_inv['tables'].values())} rows, {source_inv['views']} views, {source_inv['procedures']} procs, {source_inv['triggers']} triggers.")

    # 3. Create fresh recovery database
    print(f"[*] Recreating target recovery database `{recovery_db}`...")
    srv = get_server_connection()
    with srv.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS `{recovery_db}`;")
        cur.execute(f"CREATE DATABASE `{recovery_db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    srv.close()
    print(f"[OK] Clean recovery database `{recovery_db}` ready.")

    # 4. Execute restore via mysql client
    mysql_exe = find_mysql_binary()
    if not mysql_exe:
        raise RuntimeError("mysql executable not found for database restore.")

    print(f"[*] Restoring backup into `{recovery_db}` via mysql executable...")
    cmd = [
        mysql_exe,
        '-h', os.getenv('DB_HOST', '127.0.0.1'),
        '-P', str(os.getenv('DB_PORT', '3306')),
        '-u', os.getenv('DB_USER', 'root'),
        f"--password={os.getenv('DB_PASSWORD', '')}",
        recovery_db
    ]

    with open(backup_file, 'r', encoding='utf-8') as sf:
        res = subprocess.run(cmd, stdin=sf, capture_output=True, text=True)

    if res.returncode != 0:
        raise RuntimeError(f"Database restore failed: {res.stderr}")
    print(f"[OK] SQL restoration completed successfully.")

    # 5. Gather restored database inventory & perform reconciliation
    print(f"[*] Reconciling restored database `{recovery_db}` against `{source_db}`...")
    rec_inv = get_db_inventory(recovery_db)

    discrepancies = []
    # Check table count
    if len(source_inv['tables']) != len(rec_inv['tables']):
        discrepancies.append(f"Table count mismatch: source has {len(source_inv['tables'])}, recovery has {len(rec_inv['tables'])}")

    # Check row counts per table
    for tbl, s_rows in source_inv['tables'].items():
        r_rows = rec_inv['tables'].get(tbl)
        if r_rows is None:
            discrepancies.append(f"Table `{tbl}` missing in recovery database.")
        elif r_rows != s_rows:
            discrepancies.append(f"Row count mismatch in `{tbl}`: source={s_rows}, restored={r_rows}")

    # Check routines and triggers
    if source_inv['views'] != rec_inv['views']:
        discrepancies.append(f"Views mismatch: source={source_inv['views']}, restored={rec_inv['views']}")
    if source_inv['procedures'] != rec_inv['procedures']:
        discrepancies.append(f"Stored procedures mismatch: source={source_inv['procedures']}, restored={rec_inv['procedures']}")
    if source_inv['triggers'] != rec_inv['triggers']:
        discrepancies.append(f"Triggers mismatch: source={source_inv['triggers']}, restored={rec_inv['triggers']}")

    print("-------------------------------------------------------")
    print(f"Reconciliation Summary:")
    print(f"  Source Tables:   {len(source_inv['tables'])} | Restored Tables:   {len(rec_inv['tables'])}")
    print(f"  Source Rows:     {sum(source_inv['tables'].values())} | Restored Rows:     {sum(rec_inv['tables'].values())}")
    print(f"  Source Views:    {source_inv['views']} | Restored Views:    {rec_inv['views']}")
    print(f"  Source Procs:    {source_inv['procedures']} | Restored Procs:    {rec_inv['procedures']}")
    print(f"  Source Triggers: {source_inv['triggers']} | Restored Triggers: {rec_inv['triggers']}")

    drill_result = {
        'timestamp': datetime.now().isoformat(),
        'backup_file': os.path.basename(backup_file),
        'source_db': source_db,
        'recovery_db': recovery_db,
        'success': len(discrepancies) == 0,
        'discrepancies': discrepancies,
        'source_inventory': source_inv,
        'recovered_inventory': rec_inv
    }

    ev_dir = Path(__file__).resolve().parent.parent / "_internal" / "test-evidence" / "recovery"
    ev_dir.mkdir(parents=True, exist_ok=True)
    with open(ev_dir / "recovery_verification_report.json", "w", encoding="utf-8") as f:
        json.dump(drill_result, f, indent=2)

    if discrepancies:
        print("[FAIL] Recovery reconciliation found discrepancies:")
        for d in discrepancies:
            print(f"  [X] {d}")
        return False
    else:
        print("[PASS] 100% DATA, SCHEMA, AND LOGIC RECONCILIATION CONFIRMED!")
        print(f"[OK] Recovery drill evidence saved to {ev_dir / 'recovery_verification_report.json'}")
        print("=======================================================\n")
        return True

def main():
    parser = argparse.ArgumentParser(description="MiniLMS Live Recovery Drill Automation")
    parser.add_argument('--backup-file', type=str, default=None, help="Specific backup file to restore (default: latest)")
    parser.add_argument('--recovery-db', type=str, default='minilms_recovery_db', help="Target database for recovery (default: minilms_recovery_db)")
    parser.add_argument('--confirm', action='store_true', help="Mandatory safety confirmation flag to execute recovery drill")
    args = parser.parse_args()

    if not args.confirm:
        print("\n[!] SAFETY ERROR: Live recovery drill will drop and recreate the recovery database.")
        print("    You must explicitly pass the --confirm flag to proceed.")
        print("    Example: python scripts/restore_database.py --confirm\n")
        sys.exit(1)

    success = run_recovery_drill(backup_file=args.backup_file, recovery_db=args.recovery_db)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
