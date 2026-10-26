"""Seed secure development password hashes for demo accounts.
Replaces placeholder NOT_A_REAL_HASH / DEMO_ONLY with secure Werkzeug password hashes.
Default password for demo accounts is 'MiniLMS@2026' (or overridden by DEMO_USER_PASSWORD in .env).
"""
import os
import pymysql
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

DEMO_PWD = os.getenv('DEMO_USER_PASSWORD', 'MiniLMS@2026')

def seed_passwords():
    conn = pymysql.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'minilms_db'),
        charset='utf8mb4',
        autocommit=False
    )
    
    hashed = generate_password_hash(DEMO_PWD)
    updated = 0
    with conn.cursor() as cur:
        cur.execute("SELECT user_id, email, password_hash, role FROM users;")
        users = cur.fetchall()
        for uid, email, phash, role in users:
            if phash in ('NOT_A_REAL_HASH', 'DEMO_ONLY') or not phash.startswith('scrypt:') and not phash.startswith('pbkdf2:'):
                cur.execute("UPDATE users SET password_hash = %s WHERE user_id = %s;", (hashed, uid))
                updated += 1
                print(f"Updated user #{uid} ({email}, {role}) with secure hash.")
    conn.commit()
    conn.close()
    print(f"Password seeding complete: {updated} user(s) updated. Default demo password is: {DEMO_PWD}")

if __name__ == '__main__':
    seed_passwords()
