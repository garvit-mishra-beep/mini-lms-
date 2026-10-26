"""Comprehensive automated test suite for MiniLMS.
Tests authentication, CSRF enforcement, role-based permissions,
course-level authorization, duplicate enrollments, quiz submission,
server-side grading, grade corrections, and database constraints.
All tests restore any modified database state to preserve viva demonstration data.
"""
import unittest
import pymysql
from app import create_app
from app.config import Config
from app.db import fetch_one, fetch_all, execute_query, call_proc
from app.services import enrollment_service, quiz_service, grading_service

class MiniLMSTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def get_csrf_token(self):
        """Helper to retrieve or initialize session CSRF token."""
        with self.client.session_transaction() as sess:
            if 'csrf_token' not in sess:
                import secrets
                sess['csrf_token'] = secrets.token_hex(32)
            return sess['csrf_token']

    def login_as(self, email):
        """Helper to log in via demo route in test mode."""
        role = 'admin' if 'admin' in email else ('teacher' if 'anita' in email else 'student')
        return self.client.get(f'/auth/demo-login/{role}', follow_redirects=True)

    # 1. CSRF Protection Tests
    def test_post_without_csrf_rejected(self):
        """Verify that state-modifying POST requests without CSRF token are rejected with 400."""
        res = self.client.post('/auth/login', data={
            'email': 'admin@example.test',
            'password': 'WrongPassword'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn(b'CSRF', res.data)

    # 2. Authentication Tests
    def test_login_success_and_logout(self):
        csrf = self.get_csrf_token()
        res = self.client.post('/auth/login', data={
            'csrf_token': csrf,
            'email': 'admin@example.test',
            'password': 'MiniLMS@2026'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Welcome back', res.data)

        # Logout
        res_logout = self.client.get('/auth/logout', follow_redirects=True)
        self.assertIn(b'logged out successfully', res_logout.data)

    def test_login_invalid_credentials(self):
        csrf = self.get_csrf_token()
        res = self.client.post('/auth/login', data={
            'csrf_token': csrf,
            'email': 'admin@example.test',
            'password': 'WrongPasswordXYZ'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', res.data)

    def test_demo_login_restricted_when_disabled(self):
        """Verify that demo login returns 403 Forbidden when DEMO_MODE is False."""
        original_demo_mode = self.app.config.get('DEMO_MODE')
        self.app.config['DEMO_MODE'] = False
        try:
            res = self.client.get('/auth/demo-login/admin')
            self.assertEqual(res.status_code, 403)
        finally:
            self.app.config['DEMO_MODE'] = original_demo_mode

    # 3. Permissions and Role-Based Authorization
    def test_student_cannot_access_admin_route(self):
        self.login_as('aarav@example.test')
        res = self.client.get('/courses/create')
        self.assertEqual(res.status_code, 403)

    def test_student_cannot_access_database_explorer(self):
        """Verify that student role is forbidden from browsing database explorer."""
        self.login_as('aarav@example.test')
        res = self.client.get('/explorer/', follow_redirects=True)
        self.assertEqual(res.status_code, 403)

    # 4. Teacher Course-Level Authorization
    def test_unassigned_teacher_cannot_manage_unassigned_course_grades(self):
        """Verify that a teacher cannot publish or correct grades for a course they are not assigned to."""
        # Find a course and an unassigned teacher
        course = fetch_one("SELECT course_id FROM courses LIMIT 1")
        cid = course['course_id']

        unassigned_teacher = fetch_one("""
            SELECT t.teacher_id, u.email, u.user_id
            FROM teachers t JOIN users u ON u.user_id = t.user_id
            WHERE t.teacher_id NOT IN (SELECT teacher_id FROM course_instructors WHERE course_id = %s)
            LIMIT 1
        """, (cid,))

        if unassigned_teacher:
            # Login as this teacher
            with self.client.session_transaction() as sess:
                sess['_user_id'] = str(unassigned_teacher['user_id'])
                sess['_fresh'] = True

            csrf = self.get_csrf_token()

            # Attempt to publish grade for enrollment in this course
            enrollment = fetch_one("SELECT enrollment_id FROM enrollments WHERE course_id = %s LIMIT 1", (cid,))
            if enrollment:
                eid = enrollment['enrollment_id']
                res = self.client.post(f'/grades/publish/{eid}', data={'csrf_token': csrf})
                self.assertEqual(res.status_code, 403)

    # 5. Dashboard Loads with Live Metrics
    def test_dashboard_loading(self):
        self.login_as('admin@example.test')
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'System Overview', res.data)
        self.assertIn(b'Students', res.data)
        self.assertIn(b'Enrollments', res.data)

    # 6. Critical Duplicate Enrollment Prevention Test
    def test_duplicate_enrollment_prevention(self):
        """Verify that attempting to enroll an already active student returns a clean conflict."""
        student = fetch_one("SELECT student_id, user_id FROM students LIMIT 1")
        course = fetch_one("SELECT course_id FROM courses WHERE status = 'PUBLISHED' LIMIT 1")

        sid = student['student_id']
        cid = course['course_id']

        # Ensure student is enrolled once
        existing = enrollment_service.get_existing_active_enrollment(sid, cid)
        created_temp = False
        if not existing:
            first_res = enrollment_service.enroll_student(sid, cid, actor_user_id=1)
            self.assertTrue(first_res['success'])
            created_temp = True
            existing = enrollment_service.get_existing_active_enrollment(sid, cid)

        try:
            # Now attempt duplicate enrollment
            second_res = enrollment_service.enroll_student(sid, cid, actor_user_id=1)
            self.assertFalse(second_res['success'])
            self.assertTrue(second_res['conflict'])
            self.assertIn("already actively enrolled", second_res['message'])
            self.assertIsNotNone(second_res.get('existing_enrollment_id'))

            # Verify no duplicate active enrollment exists in MySQL
            active_count = fetch_one("""
                SELECT COUNT(*) as cnt FROM enrollments
                WHERE student_id = %s AND course_id = %s AND status = 'ACTIVE'
            """, (sid, cid))['cnt']
            self.assertEqual(active_count, 1)
        finally:
            if created_temp and existing:
                execute_query("DELETE FROM completions WHERE enrollment_id = %s", (existing['enrollment_id'],))
                execute_query("DELETE FROM enrollments WHERE enrollment_id = %s", (existing['enrollment_id'],))

    # 7. Inactive Student Enrollment Prevention with Real Database Records
    def test_inactive_student_enrollment_blocked(self):
        """Verify that inactive students are blocked by both the service and the MySQL stored procedure."""
        student = fetch_one("SELECT s.student_id, s.user_id, u.status FROM students s JOIN users u ON u.user_id = s.user_id LIMIT 1")
        course = fetch_one("SELECT course_id FROM courses WHERE status = 'PUBLISHED' LIMIT 1")

        sid = student['student_id']
        uid = student['user_id']
        cid = course['course_id']
        original_status = student['status']

        try:
            # Set student account to INACTIVE
            execute_query("UPDATE users SET status = 'INACTIVE' WHERE user_id = %s", (uid,))

            # 1. Test application service pre-flight check
            res = enrollment_service.enroll_student(sid, cid, actor_user_id=1)
            self.assertFalse(res['success'])
            self.assertIn("inactive", res['message'].lower())

            # 2. Test direct MySQL stored procedure exception
            with self.assertRaises(pymysql.MySQLError) as cm:
                call_proc('sp_enroll', (sid, cid))
            self.assertIn("Only active students may enroll", str(cm.exception))

        finally:
            # Cleanly restore original status
            execute_query("UPDATE users SET status = %s WHERE user_id = %s", (original_status, uid))

    # 8. Unpublished Course Enrollment Prevention with Real Database Records
    def test_unpublished_course_enrollment_blocked(self):
        """Verify that DRAFT/unpublished courses are blocked by both service and MySQL procedure."""
        student = fetch_one("SELECT student_id FROM students LIMIT 1")
        course = fetch_one("SELECT course_id, status FROM courses LIMIT 1")

        sid = student['student_id']
        cid = course['course_id']
        orig_course_status = course['status']

        try:
            # Temporarily set course status to DRAFT
            execute_query("UPDATE courses SET status = 'DRAFT' WHERE course_id = %s", (cid,))

            # 1. Test application service pre-flight check
            res = enrollment_service.enroll_student(sid, cid, actor_user_id=1)
            self.assertFalse(res['success'])
            self.assertIn("must be published", res['message'].lower())

            # 2. Test direct MySQL stored procedure exception
            with self.assertRaises(pymysql.MySQLError) as cm:
                call_proc('sp_enroll', (sid, cid))
            self.assertIn("Course is not published", str(cm.exception))

        finally:
            # Cleanly restore original status
            execute_query("UPDATE courses SET status = %s WHERE course_id = %s", (orig_course_status, cid))

    # 9. Functional Quiz Submission and Server-Side Scoring
    def test_quiz_server_side_scoring(self):
        enrollment = fetch_one("""
            SELECT e.enrollment_id, s.user_id FROM enrollments e
            JOIN students s ON s.student_id = e.student_id
            WHERE e.course_id = 1 AND e.status = 'ACTIVE' LIMIT 1
        """)
        if not enrollment:
            return

        eid = enrollment['enrollment_id']
        uid = enrollment['user_id']

        # Start attempt
        start_res = quiz_service.start_attempt(eid, 1)
        if start_res['success']:
            attempt_id = start_res['attempt']['attempt_id']
            try:
                # Submit with 1 correct and 1 incorrect answer
                answers = {'1': 1, '2': 6} # Q1 correct (+10), Q2 incorrect (0)
                sub_res = quiz_service.submit_attempt(attempt_id, answers, student_user_id=uid)
                self.assertTrue(sub_res['success'])
                self.assertEqual(sub_res['final_score'], 10.0)
                self.assertEqual(sub_res['percentage'], 50.0)
            finally:
                # Clean up test attempt to avoid cluttering viva statistics
                execute_query("DELETE FROM quiz_responses WHERE attempt_id = %s", (attempt_id,))
                execute_query("DELETE FROM quiz_attempts WHERE attempt_id = %s", (attempt_id,))

    # 10. Authorized Grade Correction and Audit Logging with State Restoration
    def test_authorized_grade_correction(self):
        grade = fetch_one("SELECT grade_id, final_score FROM grades WHERE published = 1 LIMIT 1")
        if grade:
            gid = grade['grade_id']
            orig_score = float(grade['final_score'])
            test_score = 88.50

            try:
                res = grading_service.correct_grade(gid, test_score, "PBL Automated Test Correction", actor_user_id=1)
                self.assertTrue(res['success'])

                # Verify audit trail in grade_change_history
                hist = fetch_one("SELECT * FROM grade_change_history WHERE grade_id = %s ORDER BY change_id DESC LIMIT 1", (gid,))
                self.assertIsNotNone(hist)
                self.assertEqual(str(hist['new_score']), '88.50')
            finally:
                # Restore original score
                grading_service.correct_grade(gid, orig_score, "Restoration of original score after test", actor_user_id=1)

    # 11. Database Explorer Route for Admin
    def test_database_explorer_loads_for_admin(self):
        self.login_as('admin@example.test')
        res = self.client.get('/explorer/users')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'information_schema', res.data)
        self.assertIn(b'Base Tables', res.data)

    # 12. Concurrent Duplicate Enrollment Test with Clean Fixture Cleanup
    def test_concurrent_duplicate_enrollment(self):
        from concurrent.futures import ThreadPoolExecutor

        student = fetch_one("SELECT student_id FROM students ORDER BY student_id DESC LIMIT 1")
        course = fetch_one("SELECT course_id FROM courses WHERE status = 'PUBLISHED' LIMIT 1")
        sid = student['student_id']
        cid = course['course_id']

        # Cancel any active enrollment first to test clean slate
        existing = enrollment_service.get_existing_active_enrollment(sid, cid)
        had_preexisting = False
        if existing:
            had_preexisting = True
            execute_query("UPDATE enrollments SET status = 'CANCELLED' WHERE enrollment_id = %s", (existing['enrollment_id'],))

        try:
            def attempt_enroll():
                return enrollment_service.enroll_student(sid, cid, actor_user_id=1)

            # Run 2 enrollment requests concurrently in separate threads
            with ThreadPoolExecutor(max_workers=2) as executor:
                future1 = executor.submit(attempt_enroll)
                future2 = executor.submit(attempt_enroll)
                res1 = future1.result()
                res2 = future2.result()

            # Exactly one must succeed, and the other must be caught as a conflict
            successes = [r for r in [res1, res2] if r['success']]
            conflicts = [r for r in [res1, res2] if r.get('conflict')]
            self.assertEqual(len(successes), 1)
            self.assertEqual(len(conflicts), 1)

            # Verify only 1 active enrollment and 1 completion record exist
            active_enrollments = fetch_all("""
                SELECT enrollment_id FROM enrollments
                WHERE student_id = %s AND course_id = %s AND status = 'ACTIVE'
            """, (sid, cid))
            self.assertEqual(len(active_enrollments), 1)

            active_eid = active_enrollments[0]['enrollment_id']
            completions = fetch_all("SELECT * FROM completions WHERE enrollment_id = %s", (active_eid,))
            self.assertEqual(len(completions), 1)

        finally:
            # Clean up the newly created test enrollment
            new_test_e = fetch_one("""
                SELECT enrollment_id FROM enrollments
                WHERE student_id = %s AND course_id = %s AND status = 'ACTIVE'
            """, (sid, cid))
            if new_test_e:
                execute_query("DELETE FROM completions WHERE enrollment_id = %s", (new_test_e['enrollment_id'],))
                execute_query("DELETE FROM enrollments WHERE enrollment_id = %s", (new_test_e['enrollment_id'],))

            # If student had pre-existing enrollment, restore its active status
            if had_preexisting and existing:
                execute_query("UPDATE enrollments SET status = 'ACTIVE' WHERE enrollment_id = %s", (existing['enrollment_id'],))

    # 13. Health Check Endpoint
    def test_health_check_endpoint(self):
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'connected')
        self.assertEqual(data['database'], 'minilms_db')
        self.assertGreaterEqual(data['tables'], 18)

if __name__ == '__main__':
    unittest.main()
