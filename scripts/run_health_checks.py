"""MiniLMS Database Observability and Health Check Diagnostic Suite
Monitors latency, active connections, buffer pool efficiency, table storage, and slow queries.
Generates structured diagnostic report for production telemetry.
"""
import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import pymysql
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

def get_connection(database_name=None):
    target_db = database_name or os.getenv('DB_NAME', 'minilms_db')
    return pymysql.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=target_db,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def collect_telemetry(database_name=None):
    target_db = database_name or os.getenv('DB_NAME', 'minilms_db')
    report = {
        'timestamp': datetime.now().isoformat(),
        'target_database': target_db,
        'status': 'HEALTHY',
        'metrics': {},
        'table_storage': [],
        'recommendations': []
    }

    # 1. Connectivity & Latency Check
    t0 = time.perf_counter()
    try:
        conn = get_connection(target_db)
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS ping;")
            cur.fetchone()
        latency_ms = (time.perf_counter() - t0) * 1000.0
        report['metrics']['connection_latency_ms'] = round(latency_ms, 3)
    except Exception as e:
        report['status'] = 'UNAVAILABLE'
        report['error'] = str(e)
        return report

    with conn.cursor() as cur:
        # 2. Server Version and Uptime
        cur.execute("SHOW GLOBAL STATUS WHERE Variable_name IN ('Uptime', 'Threads_connected', 'Threads_running', 'Max_used_connections', 'Slow_queries', 'Innodb_buffer_pool_read_requests', 'Innodb_buffer_pool_reads');")
        status_vars = {r['Variable_name']: int(r['Value']) for r in cur.fetchall()}

        cur.execute("SHOW GLOBAL VARIABLES WHERE Variable_name IN ('version', 'max_connections', 'long_query_time', 'innodb_buffer_pool_size');")
        global_vars = {r['Variable_name']: r['Value'] for r in cur.fetchall()}

        # 3. Connection Metrics
        max_conn = int(global_vars.get('max_connections', 151))
        curr_conn = status_vars.get('Threads_connected', 0)
        conn_util_pct = (curr_conn / max_conn) * 100.0

        report['metrics']['server_version'] = global_vars.get('version', 'Unknown')
        report['metrics']['uptime_seconds'] = status_vars.get('Uptime', 0)
        report['metrics']['active_threads_connected'] = curr_conn
        report['metrics']['threads_running'] = status_vars.get('Threads_running', 0)
        report['metrics']['max_used_connections'] = status_vars.get('Max_used_connections', 0)
        report['metrics']['max_connections_limit'] = max_conn
        report['metrics']['connection_utilization_pct'] = round(conn_util_pct, 2)

        # 4. Slow Queries
        slow_q = status_vars.get('Slow_queries', 0)
        long_q_time = float(global_vars.get('long_query_time', 10.0))
        report['metrics']['slow_query_count'] = slow_q
        report['metrics']['long_query_time_threshold_sec'] = long_q_time

        # 5. InnoDB Buffer Pool Efficiency
        read_reqs = status_vars.get('Innodb_buffer_pool_read_requests', 0)
        reads = status_vars.get('Innodb_buffer_pool_reads', 0)
        if read_reqs > 0:
            hit_ratio = (1.0 - (reads / read_reqs)) * 100.0
        else:
            hit_ratio = 100.0
        buf_size_mb = int(global_vars.get('innodb_buffer_pool_size', 134217728)) / (1024 * 1024)
        report['metrics']['buffer_pool_size_mb'] = round(buf_size_mb, 2)
        report['metrics']['buffer_pool_read_requests'] = read_reqs
        report['metrics']['buffer_pool_disk_reads'] = reads
        report['metrics']['buffer_pool_hit_ratio_pct'] = round(hit_ratio, 4)

        # 6. Database Object Inventory
        cur.execute("SELECT TABLE_TYPE AS table_type, COUNT(*) as cnt FROM information_schema.tables WHERE table_schema = %s GROUP BY TABLE_TYPE;", (target_db,))
        for r in cur.fetchall():
            ttype = (r.get('table_type') or r.get('TABLE_TYPE') or '').upper()
            if ttype == 'BASE TABLE':
                report['metrics']['base_tables_count'] = r['cnt']
            elif ttype == 'VIEW':
                report['metrics']['views_count'] = r['cnt']

        cur.execute("SELECT ROUTINE_TYPE AS routine_type, COUNT(*) as cnt FROM information_schema.routines WHERE routine_schema = %s GROUP BY ROUTINE_TYPE;", (target_db,))
        for r in cur.fetchall():
            rtype = (r.get('routine_type') or r.get('ROUTINE_TYPE') or '').upper()
            if rtype == 'PROCEDURE':
                report['metrics']['stored_procedures_count'] = r['cnt']
            elif rtype == 'FUNCTION':
                report['metrics']['stored_functions_count'] = r['cnt']

        cur.execute("SELECT COUNT(*) as cnt FROM information_schema.triggers WHERE trigger_schema = %s;", (target_db,))
        report['metrics']['triggers_count'] = cur.fetchone()['cnt']

        # 7. Table Storage Footprint
        cur.execute("""
            SELECT 
                TABLE_NAME AS table_name,
                TABLE_ROWS AS table_rows,
                ROUND((DATA_LENGTH) / 1024 / 1024, 4) AS data_mb,
                ROUND((INDEX_LENGTH) / 1024 / 1024, 4) AS index_mb,
                ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 4) AS total_mb
            FROM information_schema.tables
            WHERE table_schema = %s AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY (DATA_LENGTH + INDEX_LENGTH) DESC;
        """, (target_db,))
        tables = cur.fetchall()
        total_db_mb = sum(t['total_mb'] for t in tables)
        total_rows = sum(t['table_rows'] or 0 for t in tables)
        report['metrics']['total_storage_mb'] = round(total_db_mb, 4)
        report['metrics']['total_table_rows_approx'] = total_rows
        report['table_storage'] = tables

    conn.close()

    # Rule checks for health assessment
    if report['metrics']['buffer_pool_hit_ratio_pct'] < 95.0:
        report['recommendations'].append("Buffer pool hit ratio is below 95%. Consider increasing innodb_buffer_pool_size.")
    if report['metrics']['connection_utilization_pct'] > 75.0:
        report['recommendations'].append("Connection utilization exceeds 75%. Consider scaling connection pool limit.")
    if report['metrics']['slow_query_count'] > 10:
        report['recommendations'].append("Slow query occurrences detected. Review slow query log for indexing opportunities.")
    if not report['recommendations']:
        report['recommendations'].append("All database performance parameters operate within nominal thresholds.")

    return report

def main():
    target_db = sys.argv[1] if len(sys.argv) > 1 else os.getenv('DB_NAME', 'minilms_db')
    report = collect_telemetry(target_db)

    print("\n=================================================================")
    print(f" MiniLMS Database Observability & Health Diagnostic")
    print("=================================================================")
    print(f" Target Database:       {report['target_database']}")
    print(f" Diagnostic Timestamp:  {report['timestamp']}")
    print(f" Server Version:        {report['metrics'].get('server_version')}")
    print(f" Overall Status:        [{report['status']}]")
    print(f" Roundtrip Latency:     {report['metrics'].get('connection_latency_ms')} ms")
    print(f" Active Connections:    {report['metrics'].get('active_threads_connected')} / {report['metrics'].get('max_connections_limit')} ({report['metrics'].get('connection_utilization_pct')}%)")
    print(f" Buffer Pool Hit Ratio: {report['metrics'].get('buffer_pool_hit_ratio_pct')}% (Size: {report['metrics'].get('buffer_pool_size_mb')} MB)")
    print(f" Slow Queries Count:    {report['metrics'].get('slow_query_count')} (Threshold: {report['metrics'].get('long_query_time_threshold_sec')}s)")
    print(f" Database Footprint:    {report['metrics'].get('total_storage_mb')} MB across {report['metrics'].get('base_tables_count')} tables")
    print(f" Views / Routines:      {report['metrics'].get('views_count')} Views | {report['metrics'].get('stored_procedures_count')} Procs | {report['metrics'].get('stored_functions_count')} Funcs | {report['metrics'].get('triggers_count')} Triggers")
    print("-----------------------------------------------------------------")
    print("Top 5 Tables by Storage Size:")
    for t in report['table_storage'][:5]:
        print(f"  - {t['table_name']:<24}: {t['total_mb']:>8.4f} MB (Data: {t['data_mb']} MB, Index: {t['index_mb']} MB, Rows: ~{t['table_rows']})")
    print("-----------------------------------------------------------------")
    print("Operational Recommendations:")
    for rec in report['recommendations']:
        print(f"  [+] {rec}")
    print("=================================================================\n")

    # Save artifact
    out_dir = Path(__file__).resolve().parent.parent / "_internal" / "test-evidence" / "observability"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "health_check_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[OK] Diagnostic telemetry written to {out_path}")

if __name__ == '__main__':
    main()
