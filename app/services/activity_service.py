

from datetime import datetime, date

from app.extensions import db
from app.models import CodingSession, ActivityLog, LanguageUsage, DailyStat
from app.collectors.window_collector import get_current_activity
from app.collectors.input_collector import monitor as input_monitor
from app.collectors.language_detector import detect_language, detect_project_name
from config import Config

# Tracks the currently-open session id per user, in memory.
_active_session_by_user = {}


def _get_or_create_daily_stat(user_id, day=None):
    day = day or date.today()
    stat = DailyStat.query.filter_by(user_id=user_id, date=day).first()
    if stat is None:
        stat = DailyStat(user_id=user_id, date=day)
        db.session.add(stat)
        db.session.flush()
    return stat


def _bump_language_usage(user_id, language, seconds):
    if not language or language == "Unknown" or seconds <= 0:
        return
    today = date.today()
    row = LanguageUsage.query.filter_by(user_id=user_id, language=language, date=today).first()
    if row is None:
        row = LanguageUsage(user_id=user_id, language=language, date=today, seconds_spent=0)
        db.session.add(row)
        db.session.flush()
    row.seconds_spent += seconds


def start_monitoring():
    """Start the global keyboard/mouse hooks. Safe to call multiple times."""
    input_monitor.start()


def tick(user):
    """
    Main polling function - call this periodically for a logged in user.
    Returns a small dict describing the current activity, useful for the
    live dashboard.
    """
    activity = get_current_activity()
    app_name = activity["app_name"]
    file_name = activity["file_name"]
    language = detect_language(file_name)
    project_name = detect_project_name(file_name) if file_name else "Unknown"

    session_id = _active_session_by_user.get(user.id)
    session = CodingSession.query.get(session_id) if session_id else None

    idle_seconds = input_monitor.seconds_since_last_input()
    is_idle = idle_seconds >= Config.IDLE_THRESHOLD_SECONDS

    changed_context = (
        session is None
        or session.app_name != app_name
        or session.file_name != file_name
    )

    if changed_context:
        if session is not None:
            _close_session(session)
        session = CodingSession(
            user_id=user.id,
            app_name=app_name,
            project_name=project_name,
            file_name=file_name,
            language=language,
            start_time=datetime.utcnow(),
        )
        db.session.add(session)
        db.session.flush()
        _active_session_by_user[user.id] = session.id

        log = ActivityLog(user_id=user.id, session_id=session.id,
                           event_type="app_switch", app_name=app_name,
                           detail=f"{project_name}/{file_name}")
        db.session.add(log)

        stat = _get_or_create_daily_stat(user.id)
        stat.project_switches += 1
        stat.sessions_count += 1

    if is_idle:
        session.idle_seconds += 5  # approx, matches expected tick interval

    counts = input_monitor.snapshot_and_reset()
    session.keyboard_count += counts["keyboard_count"]
    session.mouse_clicks += counts["mouse_clicks"]

    stat = _get_or_create_daily_stat(user.id)
    stat.keyboard_count += counts["keyboard_count"]
    stat.mouse_clicks += counts["mouse_clicks"]
    stat.coding_time_seconds += 0 if is_idle else 5
    stat.idle_seconds += 5 if is_idle else 0
    _bump_language_usage(user.id, language, 0 if is_idle else 5)

    db.session.commit()

    return {
        "app_name": app_name,
        "project_name": project_name,
        "file_name": file_name,
        "language": language,
        "is_idle": is_idle,
    }


def register_compile_event(user, language_hint=None):
    """Call this when a compile/run action is detected (e.g. via a
    keyboard shortcut hook, or a manual 'I compiled' button in the UI)."""
    session_id = _active_session_by_user.get(user.id)
    session = CodingSession.query.get(session_id) if session_id else None
    if session:
        session.compile_count += 1

    stat = _get_or_create_daily_stat(user.id)
    stat.compile_count += 1

    log = ActivityLog(user_id=user.id, session_id=session_id,
                       event_type="compile", app_name=session.app_name if session else "Unknown",
                       detail=language_hint or "")
    db.session.add(log)
    db.session.commit()


def _close_session(session):
    session.close()
    db.session.add(session)


def close_active_session(user):
    session_id = _active_session_by_user.pop(user.id, None)
    if not session_id:
        return
    session = CodingSession.query.get(session_id)
    if session and session.is_active:
        _close_session(session)
        db.session.commit()
        user.update_streak()
        db.session.commit()
