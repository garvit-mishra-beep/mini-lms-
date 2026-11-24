"""Campus & Course Announcements Routes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.services import academic_service
from app.db import fetch_all

announcements_bp = Blueprint('announcements', __name__)

@announcements_bp.route('/')
@login_required
def index():
    announcements_list = academic_service.get_announcements_for_user(current_user)
    offerings = []
    if current_user.is_admin or current_user.is_coordinator:
        offerings = academic_service.get_all_offerings()
    elif current_user.is_teacher and current_user.teacher_id:
        offerings = academic_service.get_offerings_for_teacher(current_user.teacher_id)

    return render_template(
        'announcements/index.html',
        active='announcements',
        announcements=announcements_list,
        offerings=offerings
    )

@announcements_bp.route('/new', methods=['POST'])
@login_required
def create():
    if current_user.is_student:
        flash("Students are not permitted to publish announcements.", "error")
        return redirect(url_for('announcements.index'))

    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    offering_id = request.form.get('offering_id', type=int) or None

    if not title or not content:
        flash("Title and Content are mandatory.", "error")
        return redirect(url_for('announcements.index'))

    res = academic_service.create_announcement(
        title=title,
        content=content,
        author_id=current_user.id,
        offering_id=offering_id
    )
    flash(res['message'], "success" if res['success'] else "error")
    return redirect(url_for('announcements.index'))

@announcements_bp.route('/<int:announcement_id>/delete', methods=['POST'])
@login_required
def delete(announcement_id):
    res = academic_service.delete_announcement(
        announcement_id=announcement_id,
        user_id=current_user.id,
        is_admin=current_user.is_admin or current_user.is_coordinator
    )
    flash(res['message'], "success" if res['success'] else "error")
    return redirect(url_for('announcements.index'))
