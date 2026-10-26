"""Database access layer for MiniLMS.
Provides connection context managers, parameterized execution, and error helpers.
"""
from contextlib import contextmanager
from decimal import Decimal
import pymysql
from pymysql.cursors import DictCursor
from app.config import Config

def get_connection():
    """Create a new raw PyMySQL connection to minilms_db."""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset='utf8mb4',
        cursorclass=DictCursor,
        autocommit=False,
        connect_timeout=6
    )

@contextmanager
def db_cursor(commit=False):
    """Context manager yielding a cursor, auto-closing and managing commit/rollback."""
    con = get_connection()
    try:
        with con.cursor() as cur:
            yield cur
        if commit:
            con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

@contextmanager
def transaction():
    """Context manager for explicit multi-statement atomic transactions."""
    con = get_connection()
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def fetch_all(sql, params=()):
    """Execute SQL query and return all rows as list of dicts."""
    with db_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()

def fetch_one(sql, params=()):
    """Execute SQL query and return first row as dict, or None."""
    with db_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()

def execute_query(sql, params=(), commit=True):
    """Execute INSERT/UPDATE/DELETE query and return (rowcount, lastrowid)."""
    con = get_connection()
    try:
        with con.cursor() as cur:
            cur.execute(sql, params)
            rc = cur.rowcount
            last_id = cur.lastrowid
        if commit:
            con.commit()
        return rc, last_id
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def scalar(sql, params=(), default=0):
    """Execute query and return the first column of the first row."""
    row = fetch_one(sql, params)
    if row:
        val = next(iter(row.values()))
        return val if val is not None else default
    return default

def call_proc(proc_name, params=()):
    """Call a stored procedure and consume all result sets."""
    con = get_connection()
    try:
        with con.cursor() as cur:
            cur.callproc(proc_name, params)
            results = []
            while True:
                rows = cur.fetchall()
                if rows:
                    results.append(rows)
                if not cur.nextset():
                    break
        con.commit()
        return results
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def record_audit_log(entity_name, entity_id, action_type, user_id, details=""):
    """Helper to write to audit_logs table."""
    try:
        execute_query(
            """INSERT INTO audit_logs (entity_name, entity_id, action_type, performed_by, details)
               VALUES (%s, %s, %s, %s, %s)""",
            (entity_name, entity_id, action_type, user_id, details)
        )
    except Exception as e:
        # Don't let audit logging fail the primary business action if table issue
        print(f"Warning: Audit log insertion failed: {e}")
