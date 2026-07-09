"""
Dashboard routes - the main landing page after login, plus the
JSON endpoint used for auto-refresh (polled by static/js/dashboard.js).
"""

from datetime import date
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user

from app.models import CodingSession, LanguageUsage, DailyStat
from app.services import stats_service
from app.utils.helpers import badge_list

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/")


def _build_dashboard_context():
    daily = stats_service.daily_summary(current_user.id)
    weekly = stats_service.weekly_summary(current_user.id)
    chart = stats_service.weekly_chart_data(current_user.id)
    lang_dist = stats_service.language_distribution(current_user.id, days=30)

    today_langs = LanguageUsage.query.filter_by(
        user_id=current_user.id, date=date.today()
    ).count()

    recent_sessions = (
        CodingSession.query.filter_by(user_id=current_user.id)
        .order_by(CodingSession.start_time.desc())
        .limit(8)
        .all()
    )

    all_time_stats = DailyStat.query.filter_by(user_id=current_user.id).all()
    total_hours_alltime = round(sum(s.coding_time_seconds for s in all_time_stats) / 3600, 1)

    badges = badge_list(current_user.current_streak, current_user.longest_streak,
                         total_hours_alltime)

    return {
        "daily": daily,
        "weekly": weekly,
        "chart": chart,
        "lang_dist": lang_dist,
        "today_langs": today_langs,
        "recent_sessions": recent_sessions,
        "streak": current_user.current_streak,
        "longest_streak": current_user.longest_streak,
        "daily_goal_minutes": current_user.daily_goal_minutes,
        "badges": badges,
    }


@dashboard_bp.route("/")
@login_required
def index():
    ctx = _build_dashboard_context()
    return render_template("dashboard.html", **ctx)


@dashboard_bp.route("/api/dashboard-data")
@login_required
def dashboard_data():
    """Polled every few seconds by the frontend for auto-refresh."""
    daily = stats_service.daily_summary(current_user.id)
    chart = stats_service.weekly_chart_data(current_user.id)
    lang_dist = stats_service.language_distribution(current_user.id, days=30)
    goal_reached = daily["coding_time_seconds"] >= (current_user.daily_goal_minutes * 60)

    return jsonify({
        "daily": daily,
        "chart": chart,
        "lang_dist": lang_dist,
        "streak": current_user.current_streak,
        "goal_reached": goal_reached,
    })
