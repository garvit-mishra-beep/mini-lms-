"""Seed academic risk assessments for active enrollments."""
from app.services.risk_service import assess_all_active_enrollments, get_academic_risks

def seed():
    count = assess_all_active_enrollments()
    print(f"Assessed {count} active student enrollments.")
    risks = get_academic_risks()
    print(f"Total risk records: {len(risks)}")
    for r in risks[:5]:
        print(f"  {r['roll_no']} ({r['student_name']}) in {r['course_code']}: Score={r['risk_score']}, Class={r['risk_classification']}")

if __name__ == '__main__':
    seed()
