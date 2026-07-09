"""
Settings routes: screenshot toggle/interval, theme, goal, data
export/import, and analytics reset.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, Response
from flask_login import login_required, current_user

from app.extensions import db
from app.services.export_service import export_user_data, import_user_data, reset_user_analytics
from app.collectors.screenshot_collector import get_collector_for_user
from config import Config

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/")
@login_required
def index():
    return render_template("settings.html", user=current_user)


@settings_bp.route("/update", methods=["POST"])
@login_required
def update():
    current_user.screenshots_enabled = bool(request.form.get("screenshots_enabled"))
    try:
        current_user.screenshot_interval = max(30, int(request.form.get("screenshot_interval", 300)))
    except (TypeError, ValueError):
        pass
    try:
        current_user.daily_goal_minutes = max(10, int(request.form.get("daily_goal_minutes", 120)))
    except (TypeError, ValueError):
        pass
    current_user.theme = "light" if request.form.get("theme") == "light" else "dark"

    db.session.commit()

    collector = get_collector_for_user(
        current_user.id, Config.SCREENSHOT_DIR,
        current_user.screenshot_interval, current_user.screenshots_enabled,
    )
    collector.configure(interval_seconds=current_user.screenshot_interval,
                         enabled=current_user.screenshots_enabled)

    flash("Settings saved.", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/export")
@login_required
def export_data():
    payload = export_user_data(current_user)
    return Response(
        payload,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment;filename={current_user.username}_export.json"},
    )


@settings_bp.route("/import", methods=["POST"])
@login_required
def import_data():
    file = request.files.get("import_file")
    if not file:
        flash("Please choose a JSON file to import.", "danger")
        return redirect(url_for("settings.index"))
    try:
        import_user_data(current_user, file.read().decode("utf-8"))
        flash("Data imported successfully.", "success")
    except Exception as exc:
        flash(f"Import failed: {exc}", "danger")
    return redirect(url_for("settings.index"))


@settings_bp.route("/reset", methods=["POST"])
@login_required
def reset_analytics():
    reset_user_analytics(current_user)
    flash("All analytics data has been reset.", "info")
    return redirect(url_for("settings.index"))
