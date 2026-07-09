"""
Export / import service - lets a user back up or restore their data
(daily stats, sessions, language usage) as JSON, and reset all analytics.
"""

import json
from datetime import datetime, date

from app.extensions import db
from app.models import CodingSession, ActivityLog, LanguageUsage, DailyStat, MLPrediction


def _serialize(obj, fields):
    out = {}
    for f in fields:
        val = getattr(obj, f)
        if isinstance(val, (datetime, date)):
            val = val.isoformat()
        out[f] = val
    return out


def export_user_data(user):
    data = {
        "exported_at": datetime.utcnow().isoformat(),
        "username": user.username,
        "daily_stats": [
            _serialize(r, ["date", "coding_time_seconds", "keyboard_count", "mouse_clicks",
                           "compile_count", "project_switches", "idle_seconds",
                           "languages_used", "sessions_count", "productivity_score"])
            for r in DailyStat.query.filter_by(user_id=user.id).all()
        ],
        "sessions": [
            _serialize(r, ["app_name", "project_name", "file_name", "language",
                           "start_time", "end_time", "duration_seconds", "idle_seconds",
                           "keyboard_count", "mouse_clicks", "compile_count"])
            for r in CodingSession.query.filter_by(user_id=user.id).all()
        ],
        "language_usage": [
            _serialize(r, ["language", "date", "seconds_spent"])
            for r in LanguageUsage.query.filter_by(user_id=user.id).all()
        ],
    }
    return json.dumps(data, indent=2)


def import_user_data(user, json_text):
    """Import previously-exported JSON, adding to (not replacing) existing data."""
    data = json.loads(json_text)

    for row in data.get("daily_stats", []):
        stat = DailyStat(
            user_id=user.id,
            date=datetime.fromisoformat(row["date"]).date(),
            coding_time_seconds=row.get("coding_time_seconds", 0),
            keyboard_count=row.get("keyboard_count", 0),
            mouse_clicks=row.get("mouse_clicks", 0),
            compile_count=row.get("compile_count", 0),
            project_switches=row.get("project_switches", 0),
            idle_seconds=row.get("idle_seconds", 0),
            languages_used=row.get("languages_used", 0),
            sessions_count=row.get("sessions_count", 0),
            productivity_score=row.get("productivity_score", 0.0),
        )
        db.session.add(stat)

    for row in data.get("language_usage", []):
        lang = LanguageUsage(
            user_id=user.id,
            language=row["language"],
            date=datetime.fromisoformat(row["date"]).date(),
            seconds_spent=row.get("seconds_spent", 0),
        )
        db.session.add(lang)

    db.session.commit()
    return True


def reset_user_analytics(user):
    """Danger zone: wipes all activity data for a user, keeps the account."""
    CodingSession.query.filter_by(user_id=user.id).delete()
    ActivityLog.query.filter_by(user_id=user.id).delete()
    LanguageUsage.query.filter_by(user_id=user.id).delete()
    DailyStat.query.filter_by(user_id=user.id).delete()
    MLPrediction.query.filter_by(user_id=user.id).delete()
    db.session.commit()
