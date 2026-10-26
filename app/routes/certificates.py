"""Certificates management and verification routes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.auth.decorators import role_required, teacher_required
from app.services import grading_service
from app.db import fetch_all, fetch_one

certificates_bp = Blueprint('certificates', __name__)

@certificates_bp.route('/')
@login_required
def index():
    sql = """
        SELECT cert.certificate_id, cert.certificate_code, cert.issued_at,
               e.enrollment_id, e.student_id,
               c.course_code, c.title as course_title,
               s.roll_no, s.enrollment_no, u.full_name as student_name,
               g.final_score, g.letter_grade
        FROM certificates cert
        JOIN completions co ON co.enrollment_id = cert.enrollment_id
        JOIN enrollments e ON e.enrollment_id = co.enrollment_id
        JOIN courses c ON c.course_id = e.course_id
        JOIN students s ON s.student_id = e.student_id
        JOIN users u ON u.user_id = s.user_id
        LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
    """
    params = []
    if current_user.is_student:
        sql += " WHERE e.student_id = %s"
        params.append(current_user.student_id)

    sql += " ORDER BY cert.issued_at DESC"
    certs = fetch_all(sql, tuple(params))
    return render_template('certificates/index.html', active='certificates', certificates=certs)

@certificates_bp.route('/view/<certificate_code>')
def view_certificate(certificate_code):
    cert = fetch_one("""
        SELECT cert.certificate_id, cert.certificate_code, cert.issued_at,
               c.course_code, c.title as course_title, c.description as course_desc,
               s.roll_no, s.enrollment_no, u.full_name as student_name,
               g.final_score, g.letter_grade,
               (SELECT u2.full_name FROM course_instructors ci
                JOIN teachers t ON t.teacher_id = ci.teacher_id
                JOIN users u2 ON u2.user_id = t.user_id
                WHERE ci.course_id = c.course_id AND ci.instructor_role = 'OWNER' LIMIT 1) as instructor_name
        FROM certificates cert
        JOIN completions co ON co.enrollment_id = cert.enrollment_id
        JOIN enrollments e ON e.enrollment_id = co.enrollment_id
        JOIN courses c ON c.course_id = e.course_id
        JOIN students s ON s.student_id = e.student_id
        JOIN users u ON u.user_id = s.user_id
        LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
        WHERE cert.certificate_code = %s
    """, (certificate_code.strip(),))

    if not cert:
        flash("Certificate verification code not found.", "error")
        return redirect(url_for('certificates.index'))

    return render_template('certificates/view.html', cert=cert)

@certificates_bp.route('/issue/<int:enrollment_id>', methods=['POST'])
@login_required
@teacher_required
def issue(enrollment_id):
    res = grading_service.issue_certificate_for_enrollment(enrollment_id, current_user.id)
    flash(res['message'], "success" if res['success'] else "error")
    return redirect(url_for('certificates.index'))
