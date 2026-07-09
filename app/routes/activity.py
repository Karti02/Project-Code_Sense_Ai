"""
Activity routes: the live monitor tick endpoint, the activity history
page (with search/filter by date), and manual compile-event logging.
"""

from datetime import datetime
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user

from app.models import CodingSession, ActivityLog
from app.services import activity_service

activity_bp = Blueprint("activity", __name__, url_prefix="/activity")


@activity_bp.route("/tick", methods=["POST"])
@login_required
def tick():
    """
    Called every few seconds by the browser (see static/js/dashboard.js)
    to advance the activity monitor for the logged-in user.
    """
    result = activity_service.tick(current_user)
    return jsonify(result)


@activity_bp.route("/compile", methods=["POST"])
@login_required
def register_compile():
    activity_service.register_compile_event(current_user)
    return jsonify({"ok": True})


@activity_bp.route("/history")
@login_required
def history():
    query = CodingSession.query.filter_by(user_id=current_user.id)

    date_str = request.args.get("date")
    search = request.args.get("q", "").strip()

    if date_str:
        try:
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
            query = query.filter(
                CodingSession.start_time >= datetime(day.year, day.month, day.day),
                CodingSession.start_time < datetime(day.year, day.month, day.day, 23, 59, 59),
            )
        except ValueError:
            pass

    if search:
        like = f"%{search}%"
        query = query.filter(
            (CodingSession.app_name.ilike(like))
            | (CodingSession.project_name.ilike(like))
            | (CodingSession.file_name.ilike(like))
            | (CodingSession.language.ilike(like))
        )

    sessions = query.order_by(CodingSession.start_time.desc()).limit(200).all()

    recent_logs = (
        ActivityLog.query.filter_by(user_id=current_user.id)
        .order_by(ActivityLog.timestamp.desc())
        .limit(50)
        .all()
    )

    return render_template(
        "activity.html", sessions=sessions, logs=recent_logs,
        date_filter=date_str or "", search=search,
    )
