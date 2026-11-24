"""Intelligent Academic Early Warning & Risk Detection Service for MiniLMS.
Provides explainable, deterministic heuristic risk assessment, cold-start handling,
and human-in-the-loop review and intervention workflows.
"""
from datetime import datetime
from app.db import fetch_all, fetch_one, execute_query, get_connection

def calculate_heuristic_risk(attendance_pct: float, grade_pct: float, overdue_count: int, total_sessions: int) -> dict:
    """Evaluate academic risk using explainable pedagogical rules."""
    # Cold-Start / Data Sufficiency Check
    if total_sessions < 3:
        return {
            'risk_score': 0.0,
            'risk_classification': 'INSUFFICIENT_DATA',
            'data_sufficiency': 'INSUFFICIENT_DATA',
            'attendance_deficit': 0.0,
            'grade_deficit': 0.0,
            'overdue_factor': 0.0,
            'explanation': f"Course offering has conducted only {total_sessions} session(s). Minimum 3 sessions required for reliable risk evaluation."
        }

    # 1. Attendance Deficit: max(0, (75.0 - att_pct) / 75.0 * 100)
    att_deficit = max(0.0, ((75.0 - attendance_pct) / 75.0) * 100.0) if attendance_pct < 75.0 else 0.0

    # 2. Assessment Deficit: max(0, (50.0 - grade_pct) / 50.0 * 100)
    grade_deficit = max(0.0, ((50.0 - grade_pct) / 50.0) * 100.0) if grade_pct < 50.0 else 0.0

    # 3. Overdue Factor: min(100, overdue_count * 25.0)
    overdue_factor = min(100.0, overdue_count * 25.0)

    # 4. Composite Weighted Score: 40% Attendance + 40% Grade + 20% Overdue
    composite_score = round((0.40 * att_deficit) + (0.40 * grade_deficit) + (0.20 * overdue_factor), 2)

    # Classification
    if composite_score >= 60.0 or attendance_pct < 60.0:
        classification = 'HIGH'
    elif composite_score >= 30.0:
        classification = 'MODERATE'
    else:
        classification = 'LOW'

    explanation = (
        f"Composite Risk Score: {composite_score:.2f}/100.00. "
        f"Attendance: {attendance_pct:.1f}% (Deficit: {att_deficit:.1f}%), "
        f"Average Score: {grade_pct:.1f}% (Deficit: {grade_deficit:.1f}%), "
        f"Overdue Work: {overdue_count} items. Classification: {classification}."
    )

    return {
        'risk_score': composite_score,
        'risk_classification': classification,
        'data_sufficiency': 'SUFFICIENT',
        'attendance_deficit': round(att_deficit, 2),
        'grade_deficit': round(grade_deficit, 2),
        'overdue_factor': round(overdue_factor, 2),
        'explanation': explanation
    }

def assess_student_risk(student_id: int, offering_id: int) -> dict:
    """Assess academic risk for a specific student in an offering via stored procedure."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CALL sp_assess_student_academic_risk(%s, %s, @out_score, @out_class, @out_expl)
            """, (student_id, offering_id))
            cur.execute("""
                SELECT @out_score as risk_score, @out_class as risk_classification, @out_expl as explanation
            """)
            res = cur.fetchone()
            conn.commit()

            # Fetch stored risk record
            cur.execute("""
                SELECT * FROM v_academic_risk_summary 
                WHERE student_id = %s AND course_code IN (
                    SELECT c.course_code FROM course_offerings co 
                    JOIN courses c ON co.course_id = c.course_id 
                    WHERE co.offering_id = %s
                )
            """, (student_id, offering_id))
            record = cur.fetchone()
            return record or res
    finally:
        conn.close()

def assess_all_active_enrollments() -> int:
    """Run risk evaluation across all active student enrollments."""
    active_enrollments = fetch_all("""
        SELECT student_id, offering_id 
        FROM enrollments 
        WHERE status = 'ACTIVE' AND offering_id IS NOT NULL
    """)
    count = 0
    for enr in active_enrollments:
        assess_student_risk(enr['student_id'], enr['offering_id'])
        count += 1
    return count

def get_academic_risks(department_id: int = None, classification: str = None, review_status: str = None) -> list:
    """Query academic risks view with filtering."""
    sql = "SELECT * FROM v_academic_risk_summary WHERE 1=1"
    params = []

    if classification:
        sql += " AND risk_classification = %s"
        params.append(classification)

    if review_status:
        sql += " AND review_status = %s"
        params.append(review_status)

    sql += " ORDER BY risk_score DESC, attendance_pct ASC"
    return fetch_all(sql, params)

def get_student_support_profile(student_id: int) -> list:
    """Retrieve non-punitive, constructive risk overview for a student."""
    return fetch_all("""
        SELECT risk_id, course_code, course_title, section_name, attendance_pct, assessment_pct,
               overdue_count, risk_classification, explanation, review_status, review_notes
        FROM v_academic_risk_summary
        WHERE student_id = %s
    """, (student_id,))

def submit_human_review(risk_id: int, reviewer_id: int, review_status: str, review_notes: str) -> bool:
    """Faculty or Coordinator submits human oversight review decision."""
    valid_statuses = ('CONFIRMED', 'DISMISSED', 'INTERVENTION_PLANNED')
    if review_status not in valid_statuses:
        return False

    affected, _ = execute_query("""
        UPDATE academic_risks
        SET review_status = %s,
            reviewer_id = %s,
            review_notes = %s,
            reviewed_at = NOW()
        WHERE risk_id = %s
    """, (review_status, reviewer_id, review_notes.strip(), risk_id))

    if affected:
        # Append to audit logs
        execute_query("""
            INSERT INTO audit_logs (entity_name, entity_id, action_type, performed_by, details)
            VALUES ('academic_risks', %s, 'HUMAN_RISK_REVIEW', %s, %s)
        """, (risk_id, reviewer_id, f"Review status updated to {review_status}. Notes: {review_notes[:100]}"))
        return True
    return False
