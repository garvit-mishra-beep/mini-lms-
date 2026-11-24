"""Query Portfolio Execution & Validation Harness.
Executes all 25 queries (Q01-Q20, SM01-SM05) against the live minilms_db database.
Measures execution latency, row counts returned, and generates verification telemetry.
"""
import os
import time
import re
import pymysql
from app.db import get_connection

def parse_queries(sql_file_path):
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by double dash comment headers identifying queries (e.g., -- Q01:, -- SM01:)
    pattern = r'--\s*([QS][M0-9]{2,3}):\s*(.*?)\n(.*?)(?=\n--\s*[QS][M0-9]{2,3}:|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    queries = []
    for code, title, sql in matches:
        clean_sql = sql.strip().rstrip(';')
        queries.append({
            'code': code.strip(),
            'title': title.strip(),
            'sql': clean_sql
        })
    return queries

def execute_all_queries():
    queries = parse_queries('database/queries/queries.sql')
    print(f"Loaded {len(queries)} queries from database/queries/queries.sql.")

    conn = get_connection()
    results = []

    try:
        with conn.cursor() as cur:
            for q in queries:
                start = time.perf_counter()
                try:
                    cur.execute(q['sql'])
                    rows = cur.fetchall()
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    results.append({
                        'code': q['code'],
                        'title': q['title'],
                        'status': 'SUCCESS',
                        'rows': len(rows),
                        'latency_ms': round(elapsed_ms, 2),
                        'sample': rows[0] if rows else None
                    })
                    print(f"[{q['code']}] {q['title'][:45]:<45} | SUCCESS | {len(rows)} rows | {elapsed_ms:.2f} ms")
                except Exception as e:
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    results.append({
                        'code': q['code'],
                        'title': q['title'],
                        'status': f'ERROR: {e}',
                        'rows': 0,
                        'latency_ms': round(elapsed_ms, 2),
                        'sample': None
                    })
                    print(f"[{q['code']}] {q['title'][:45]:<45} | FAILED  | {e}")
    finally:
        conn.close()

    # Write summary evidence file
    evidence_path = '_internal/test-evidence/query_portfolio_evidence.txt'
    os.makedirs(os.path.dirname(evidence_path), exist_ok=True)
    with open(evidence_path, 'w', encoding='utf-8') as out:
        out.write("========================================================================================\n")
        out.write("               MINILMS ADVANCED SQL QUERY PORTFOLIO EXECUTION EVIDENCE                  \n")
        out.write("========================================================================================\n\n")
        out.write(f"{'Code':<6} | {'Query Title':<50} | {'Status':<10} | {'Rows':<6} | {'Latency':<10}\n")
        out.write("-" * 90 + "\n")
        
        total_latency = 0.0
        success_count = 0
        for r in results:
            total_latency += r['latency_ms']
            if r['status'] == 'SUCCESS':
                success_count += 1
            out.write(f"{r['code']:<6} | {r['title'][:50]:<50} | {r['status']:<10} | {r['rows']:<6} | {r['latency_ms']:>6.2f} ms\n")
            
        out.write("-" * 90 + "\n")
        out.write(f"Total Queries Executed: {len(results)} | Successful: {success_count} | Failed: {len(results) - success_count}\n")
        out.write(f"Cumulative Execution Time: {total_latency:.2f} ms | Average Latency: {total_latency/len(results):.2f} ms\n")

    print(f"\nExecution evidence written to {evidence_path}.")
    return results

if __name__ == '__main__':
    execute_all_queries()
