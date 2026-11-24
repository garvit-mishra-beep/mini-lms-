"""Intelligence & Academic Risk Management Routes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.auth.decorators import role_required, coordinator_required
from app.services import risk_service
from app.db import scalar, fetch_all

intelligence_bp = Blueprint('intelligence', __name__)

@intelligence_bp.route('/risks')
@login_required
@role_required('ADMIN', 'COORDINATOR', 'TEACHER')
def risks_dashboard():
    """Early Warning Academic Risk Dashboard for Academic Leadership & Faculty."""
    classification = request.args.get('classification', '').strip().upper() or None
    review_status = request.args.get('review_status', '').strip().upper() or None

    risks = risk_service.get_academic_risks(
        classification=classification,
        review_status=review_status
    )

    # Risk metrics summary
    metrics = {
        'total_assessed': scalar("SELECT COUNT(*) FROM academic_risks"),
        'high_risk': scalar("SELECT COUNT(*) FROM academic_risks WHERE risk_classification = 'HIGH'"),
        'moderate_risk': scalar("SELECT COUNT(*) FROM academic_risks WHERE risk_classification = 'MODERATE'"),
        'low_risk': scalar("SELECT COUNT(*) FROM academic_risks WHERE risk_classification = 'LOW'"),
        'pending_reviews': scalar("SELECT COUNT(*) FROM academic_risks WHERE review_status = 'PENDING' AND risk_classification IN ('HIGH', 'MODERATE')")
    }

    return render_template(
        'intelligence/risks_dashboard.html',
        active='intelligence',
        risks=risks,
        metrics=metrics,
        current_classification=classification,
        current_review_status=review_status
    )

@intelligence_bp.route('/risks/evaluate', methods=['POST'])
@login_required
@coordinator_required
def evaluate_all():
    """Trigger full system-wide risk evaluation across all active student enrollments."""
    count = risk_service.assess_all_active_enrollments()
    flash(f"Successfully re-evaluated academic risk scores across {count} active student enrollments.", "success")
    return redirect(url_for('intelligence.risks_dashboard'))

@intelligence_bp.route('/risks/review/<int:risk_id>', methods=['POST'])
@login_required
@role_required('ADMIN', 'COORDINATOR', 'TEACHER')
def submit_review(risk_id):
    """Faculty or Coordinator submits human oversight review decision."""
    status = request.form.get('review_status', '').strip().upper()
    notes = request.form.get('review_notes', '').strip()

    if not status or not notes:
        flash("Review status and justification notes are required for human oversight audit.", "error")
        return redirect(url_for('intelligence.risks_dashboard'))

    success = risk_service.submit_human_review(
        risk_id=risk_id,
        reviewer_id=current_user.user_id,
        review_status=status,
        review_notes=notes
    )

    if success:
        flash(f"Human review recorded successfully for Risk Record #{risk_id} ({status}).", "success")
    else:
        flash("Failed to record human review. Please verify input parameters.", "error")

    return redirect(url_for('intelligence.risks_dashboard'))

@intelligence_bp.route('/my-support')
@login_required
def student_support():
    """Non-punitive, constructive guidance page for students to view academic support recommendations."""
    if not current_user.is_student or not current_user.student_id:
        flash("Personal academic support view is available for student accounts.", "info")
        return redirect(url_for('dashboard.index'))

    profile = risk_service.get_student_support_profile(current_user.student_id)
    return render_template(
        'intelligence/student_support.html',
        active='support',
        profile=profile
    )
