"""Setup isolated benchmark database for Phase 11 performance engineering."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import get_connection

def setup_benchmark_db():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Create database
            print("Creating isolated database minilms_benchmark_db...")
            cur.execute("CREATE DATABASE IF NOT EXISTS minilms_benchmark_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            
            # 2. Get all tables in minilms_db
            cur.execute("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA='minilms_db' AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME")
            base_tables = [r['TABLE_NAME'] for r in cur.fetchall()]
            
            cur.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            for t in base_tables:
                cur.execute(f"SHOW CREATE TABLE `minilms_db`.`{t}`")
                create_sql = cur.fetchone()['Create Table']
                # Drop existing in benchmark db
                cur.execute(f"DROP TABLE IF EXISTS `minilms_benchmark_db`.`{t}`")
                # Create in benchmark db
                cur.execute(f"USE `minilms_benchmark_db`")
                cur.execute(create_sql)
                print(f"  Cloned table: {t}")
            
            # 3. Clone Views
            cur.execute("SELECT TABLE_NAME, VIEW_DEFINITION FROM information_schema.VIEWS WHERE TABLE_SCHEMA='minilms_db'")
            views = cur.fetchall()
            for v in views:
                vname = v['TABLE_NAME']
                cur.execute(f"SHOW CREATE VIEW `minilms_db`.`{vname}`")
                cview_sql = cur.fetchone()['Create View']
                cur.execute(f"DROP VIEW IF EXISTS `minilms_benchmark_db`.`{vname}`")
                # Replace minilms_db references if any
                cview_sql = cview_sql.replace("`minilms_db`.", "`minilms_benchmark_db`.")
                cur.execute(cview_sql)
                print(f"  Cloned view: {vname}")

            # 4. Clone Stored Procedures & Functions
            cur.execute("SELECT ROUTINE_NAME, ROUTINE_TYPE FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA='minilms_db'")
            routines = cur.fetchall()
            for r in routines:
                rname = r['ROUTINE_NAME']
                rtype = r['ROUTINE_TYPE']
                if rtype == 'PROCEDURE':
                    cur.execute(f"SHOW CREATE PROCEDURE `minilms_db`.`{rname}`")
                    cproc_sql = cur.fetchone()['Create Procedure']
                    cur.execute(f"DROP PROCEDURE IF EXISTS `minilms_benchmark_db`.`{rname}`")
                    cproc_sql = cproc_sql.replace("`minilms_db`.", "`minilms_benchmark_db`.")
                    cur.execute(cproc_sql)
                    print(f"  Cloned procedure: {rname}")
                elif rtype == 'FUNCTION':
                    cur.execute(f"SHOW CREATE FUNCTION `minilms_db`.`{rname}`")
                    cfunc_sql = cur.fetchone()['Create Function']
                    cur.execute(f"DROP FUNCTION IF EXISTS `minilms_benchmark_db`.`{rname}`")
                    cfunc_sql = cfunc_sql.replace("`minilms_db`.", "`minilms_benchmark_db`.")
                    cur.execute(cfunc_sql)
                    print(f"  Cloned function: {rname}")

            # 5. Clone Triggers
            cur.execute("SELECT TRIGGER_NAME, EVENT_OBJECT_TABLE FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA='minilms_db'")
            triggers = cur.fetchall()
            for trg in triggers:
                trg_name = trg['TRIGGER_NAME']
                cur.execute(f"SHOW CREATE TRIGGER `minilms_db`.`{trg_name}`")
                ctrg_sql = cur.fetchone()['SQL Original Statement']
                cur.execute(f"DROP TRIGGER IF EXISTS `minilms_benchmark_db`.`{trg_name}`")
                ctrg_sql = ctrg_sql.replace("`minilms_db`.", "`minilms_benchmark_db`.")
                cur.execute(ctrg_sql)
                print(f"  Cloned trigger: {trg_name}")

            cur.execute("SET FOREIGN_KEY_CHECKS = 1")
            cur.execute("USE `minilms_db`")
            print("Successfully initialized minilms_benchmark_db schema!")
    finally:
        conn.close()

if __name__ == '__main__':
    setup_benchmark_db()
