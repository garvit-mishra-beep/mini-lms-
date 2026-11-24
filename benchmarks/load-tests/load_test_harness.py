"""Python Concurrency and Load Testing Harness for MiniLMS Phase 11.
Simulates Scenarios A-E (Student, Enrollment, Faculty, Reporting, Mixed)
across concurrency tiers: 5, 10, 25, 50 virtual users against Flask WSGI.
"""
import sys
import os
import time
import json
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from app import create_app
from app.db import get_connection

def run_load_test(concurrency_tiers=[5, 10, 25, 50], requests_per_tier=100):
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()

    print("=== Starting MiniLMS Multi-Tier Concurrency Load Test ===")
    
    # Establish simulated authenticated sessions
    role_sessions = {
        'student': {'_user_id': '151', 'role': 'STUDENT', 'full_name': 'Aarav Sharma'},
        'teacher': {'_user_id': '31', 'role': 'TEACHER', 'full_name': 'Dr. Vivaan Verma'},
        'coordinator': {'_user_id': '16', 'role': 'COORDINATOR', 'full_name': 'Coord Aditya Gupta'},
        'admin': {'_user_id': '1', 'role': 'ADMIN', 'full_name': 'System Administrator'}
    }

    endpoints = [
        # Scenario A: Student browsing
        ('/courses/', 'student', 'GET'),
        ('/attendance/', 'student', 'GET'),
        ('/assignments/', 'student', 'GET'),
        ('/intelligence/my-support', 'student', 'GET'),
        
        # Scenario B: Coordinator & Offerings
        ('/coordinator/offerings', 'coordinator', 'GET'),
        ('/coordinator/faculty', 'coordinator', 'GET'),
        
        # Scenario C: Faculty & Grading
        ('/attendance/', 'teacher', 'GET'),
        ('/assignments/', 'teacher', 'GET'),
        
        # Scenario D: Reporting & Executive Dashboard
        ('/analytics/reports', 'admin', 'GET'),
        ('/analytics/report/OR-01', 'admin', 'GET'),
        ('/analytics/report/MR-01', 'admin', 'GET'),
        ('/analytics/executive', 'admin', 'GET'),
    ]

    results_by_tier = []

    def make_request(req_id, endpoint, role, method):
        # Create dedicated test client per thread for clean session isolation
        c = app.test_client()
        with c.session_transaction() as sess:
            for k, v in role_sessions[role].items():
                sess[k] = v
        
        t0 = time.perf_counter()
        try:
            if method == 'GET':
                res = c.get(endpoint)
            else:
                res = c.get(endpoint)
            t1 = time.perf_counter()
            lat_ms = (t1 - t0) * 1000.0
            return {
                'req_id': req_id,
                'status_code': res.status_code,
                'latency_ms': lat_ms,
                'success': res.status_code in [200, 302]
            }
        except Exception as e:
            t1 = time.perf_counter()
            return {
                'req_id': req_id,
                'status_code': 500,
                'latency_ms': (t1 - t0) * 1000.0,
                'success': False,
                'error': str(e)
            }

    for conc in concurrency_tiers:
        print(f"\n--- Testing Concurrency Level: {conc} Concurrent Users ({requests_per_tier} requests) ---")
        latencies = []
        success_count = 0
        fail_count = 0
        
        wall_start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=conc) as executor:
            futures = []
            for i in range(requests_per_tier):
                ep, role, meth = endpoints[i % len(endpoints)]
                futures.append(executor.submit(make_request, i, ep, role, meth))
            
            for f in as_completed(futures):
                res = f.result()
                latencies.append(res['latency_ms'])
                if res['success']:
                    success_count += 1
                else:
                    fail_count += 1
                    
        wall_end = time.perf_counter()
        total_wall_s = wall_end - wall_start
        throughput_rps = round(requests_per_tier / total_wall_s, 2)
        
        med_lat = round(statistics.median(latencies), 2)
        sorted_lat = sorted(latencies)
        p95_lat = round(sorted_lat[int(0.95 * len(sorted_lat))], 2)
        p99_lat = round(sorted_lat[int(0.99 * len(sorted_lat))], 2)
        err_rate_pct = round((fail_count / requests_per_tier) * 100.0, 2)

        tier_summary = {
            'concurrent_users': conc,
            'total_requests': requests_per_tier,
            'successful_requests': success_count,
            'failed_requests': fail_count,
            'throughput_rps': throughput_rps,
            'median_latency_ms': med_lat,
            'p95_latency_ms': p95_lat,
            'p99_latency_ms': p99_lat,
            'error_rate_pct': err_rate_pct,
            'wall_time_seconds': round(total_wall_s, 3)
        }
        results_by_tier.append(tier_summary)
        
        print(f"  Throughput    : {throughput_rps} req/sec")
        print(f"  Median Latency: {med_lat} ms")
        print(f"  p95 Latency   : {p95_lat} ms")
        print(f"  p99 Latency   : {p99_lat} ms")
        print(f"  Error Rate    : {err_rate_pct}%")

    os.makedirs("docs/stage-4/evidence/load-tests", exist_ok=True)
    out_file = "docs/stage-4/evidence/load-tests/load_test_results.json"
    with open(out_file, "w") as f:
        json.dump(results_by_tier, f, indent=2)
        
    print(f"\nLoad testing completed! Results saved to {out_file}")
    return results_by_tier

if __name__ == '__main__':
    run_load_test()
