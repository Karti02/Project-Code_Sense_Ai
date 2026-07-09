"""
Admin routes - dashboard and user management, restricted to accounts
with role == "admin". Every route in this blueprint MUST be decorated
with @admin_required (in addition to @login_required) - never rely on
template-level hiding of links alone, since that isn't real access control.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, CodingSession, Screenshot
from app.utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
@admin_required
def _guard_all_admin_routes():
    """
    Belt-and-suspenders: admin_required already checks authentication and
    role, and runs before every view in this blueprint - so even a future
    route added without its own decorator stays protected. The per-view
    decorators below are kept too for clarity and defense in depth.
    """
    return None


@admin_bp.route("/")
@login_required
@admin_required
def index():
    total_users = User.query.count()
    admin_count = User.query.filter_by(role="admin").count()
    total_sessions = CodingSession.query.count()
    total_screenshots = Screenshot.query.count()
    users = User.query.order_by(User.created_at.desc()).all()

    return render_template(
        "admin/dashboard.html",
        users=users,
        total_users=total_users,
        admin_count=admin_count,
        total_sessions=total_sessions,
        total_screenshots=total_screenshots,
    )


@admin_bp.route("/users/<int:user_id>/toggle-admin", methods=["POST"])
@login_required
@admin_required
def toggle_admin(user_id):
    if user_id == current_user.id:
        flash("You can't change your own admin status.", "danger")
        return redirect(url_for("admin.index"))

    user = User.query.get_or_404(user_id)
    user.role = "user" if user.is_admin else "admin"
    db.session.commit()
    flash(f"Updated {user.username}'s role to '{user.role}'.", "success")
    return redirect(url_for("admin.index"))


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def toggle_active(user_id):
    if user_id == current_user.id:
        flash("You can't deactivate your own account.", "danger")
        return redirect(url_for("admin.index"))

    user = User.query.get_or_404(user_id)
    user.is_active_account = not user.is_active_account
    db.session.commit()
    state = "activated" if user.is_active_account else "deactivated"
    flash(f"Account for {user.username} has been {state}.", "success")
    return redirect(url_for("admin.index"))
