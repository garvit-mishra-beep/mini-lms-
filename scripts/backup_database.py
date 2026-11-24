"""MiniLMS Database Logical Backup Automation
Generates consistent, timestamped SQL backup with all DDL, data, views, triggers, and routines.
Generates a companion SHA-256 cryptographic checksum file for integrity verification.
"""
import os
import sys
import shutil
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
import pymysql
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

def find_mysqldump_binary():
    """Locates mysqldump executable on Windows or Linux."""
    which_dump = shutil.which('mysqldump')
    if which_dump:
        return which_dump
    candidates = [
        r'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe',
        r'C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqldump.exe',
        r'C:\Program Files\MySQL\MySQL Server 5.7\bin\mysqldump.exe',
        r'C:\xampp\mysql\bin\mysqldump.exe',
        r'C:\laragon\bin\mysql\current\bin\mysqldump.exe'
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def compute_sha256(file_path):
    """Computes SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()

def execute_backup(database_name=None, output_dir=None):
    """Executes mysqldump and outputs .sql and .sha256 files."""
    target_db = database_name or os.getenv('DB_NAME', 'minilms_db')
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'database', 'backup')
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"{target_db}_backup_{timestamp}.sql"
    backup_path = os.path.abspath(os.path.join(output_dir, backup_filename))
    checksum_path = f"{backup_path}.sha256"

    mysqldump_exe = find_mysqldump_binary()
    if not mysqldump_exe:
        raise RuntimeError("mysqldump binary not found. Cannot proceed with consistent logical backup.")

    print(f"\n=======================================================")
    print(f" MiniLMS Database Logical Backup Runner")
    print(f"=======================================================")
    print(f" Source Database:  {target_db}")
    print(f" Target File:      {backup_path}")
    print(f" mysqldump Binary: {mysqldump_exe}")

    cmd = [
        mysqldump_exe,
        '-h', os.getenv('DB_HOST', '127.0.0.1'),
        '-P', str(os.getenv('DB_PORT', '3306')),
        '-u', os.getenv('DB_USER', 'root'),
        f"--password={os.getenv('DB_PASSWORD', '')}",
        '--single-transaction',
        '--routines',
        '--triggers',
        '--events',
        '--add-drop-table',
        '--set-gtid-purged=OFF',
        '--default-character-set=utf8mb4',
        target_db
    ]

    print("[*] Executing mysqldump with transaction consistency...")
    with open(backup_path, 'w', encoding='utf-8') as out_f:
        res = subprocess.run(cmd, stdout=out_f, stderr=subprocess.PIPE, text=True)

    if res.returncode != 0:
        if os.path.exists(backup_path):
            os.remove(backup_path)
        raise RuntimeError(f"mysqldump failed (code {res.returncode}): {res.stderr}")

    file_size_bytes = os.path.getsize(backup_path)
    file_size_kb = file_size_bytes / 1024.0

    print(f"[OK] Dump created successfully ({file_size_kb:.2f} KB).")
    print("[*] Generating SHA-256 cryptographic verification checksum...")
    sha256_hash = compute_sha256(backup_path)

    with open(checksum_path, 'w', encoding='utf-8') as cs_f:
        cs_f.write(f"{sha256_hash}  {backup_filename}\n")

    print(f"[OK] Checksum saved: {checksum_path}")
    print(f"     SHA-256: {sha256_hash}")

    metadata = {
        'database': target_db,
        'timestamp': timestamp,
        'backup_file': backup_filename,
        'backup_path': backup_path,
        'file_size_bytes': file_size_bytes,
        'file_size_kb': round(file_size_kb, 2),
        'sha256': sha256_hash
    }

    # Save evidence metadata
    ev_dir = Path(__file__).resolve().parent.parent / "_internal" / "test-evidence" / "backup"
    ev_dir.mkdir(parents=True, exist_ok=True)
    with open(ev_dir / "backup_metadata.json", "w", encoding="utf-8") as f:
        import json
        json.dump(metadata, f, indent=2)

    print("=======================================================\n")
    return backup_path, checksum_path, sha256_hash

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else None
    execute_backup(target)
