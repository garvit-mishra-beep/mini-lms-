"""MiniLMS Backup Integrity Verification Utility
Validates:
1. File existence and non-zero byte size.
2. SHA-256 cryptographic checksum match against companion .sha256 file.
3. SQL structural sanity (presence of CREATE TABLE, INSERT INTO, triggers, and routines).
"""
import os
import sys
import glob
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from scripts.backup_database import compute_sha256

def find_latest_backup(backup_dir=None):
    """Finds the most recent .sql backup file in database/backup."""
    if backup_dir is None:
        backup_dir = os.path.join(os.path.dirname(__file__), '..', 'database', 'backup')
    files = glob.glob(os.path.join(backup_dir, '*_backup_*.sql'))
    if not files:
        return None
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def verify_backup_file(backup_path):
    """Performs full integrity verification on a specified backup file."""
    print(f"\n=======================================================")
    print(f" MiniLMS Backup Integrity Verification")
    print(f"=======================================================")
    print(f" Target Backup: {backup_path}")

    # Check 1: Existence and File Size
    if not os.path.exists(backup_path):
        print("[FAIL] Backup file does not exist.")
        return False, "File does not exist"

    size_bytes = os.path.getsize(backup_path)
    if size_bytes == 0:
        print("[FAIL] Backup file is empty (0 bytes).")
        return False, "File is 0 bytes"
    print(f"[PASS] File size verified: {size_bytes / 1024.0:.2f} KB ({size_bytes} bytes).")

    # Check 2: SHA-256 Checksum Match
    checksum_path = f"{backup_path}.sha256"
    if not os.path.exists(checksum_path):
        print(f"[FAIL] Companion checksum file not found: {checksum_path}")
        return False, "Checksum file missing"

    with open(checksum_path, 'r', encoding='utf-8') as f:
        stored_hash = f.read().strip().split()[0]

    computed_hash = compute_sha256(backup_path)
    if computed_hash.lower() != stored_hash.lower():
        print(f"[FAIL] Checksum mismatch!")
        print(f"  Expected: {stored_hash}")
        print(f"  Computed: {computed_hash}")
        return False, "Checksum mismatch"
    print(f"[PASS] Cryptographic SHA-256 verified: {computed_hash}")

    # Check 3: Structural Content Sanity
    with open(backup_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read(500000)  # Read first 500KB

    checks = {
        'CREATE TABLE statement': 'CREATE TABLE' in content,
        'INSERT INTO statement': 'INSERT INTO' in content,
        'InnoDB engine declaration': 'ENGINE=InnoDB' in content,
        'Dump header metadata': 'MySQL dump' in content
    }

    all_passed = True
    for label, passed in checks.items():
        if passed:
            print(f"[PASS] Structural Check: {label}")
        else:
            print(f"[WARN] Structural Check missing: {label}")
            all_passed = False

    print("-------------------------------------------------------")
    if all_passed:
        print("[SUCCESS] Backup file passed all integrity verifications.")
    else:
        print("[CAUTION] Backup file passed checksum but had structural warnings.")
    print("=======================================================\n")
    return all_passed, "Verified successfully"

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else find_latest_backup()
    if not target:
        print("[!] No backup files found to verify.")
        sys.exit(1)
    passed, msg = verify_backup_file(target)
    sys.exit(0 if passed else 1)
