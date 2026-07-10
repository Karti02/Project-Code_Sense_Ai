
from datetime import date, timedelta


def seconds_to_hms(seconds: int) -> str:
    seconds = int(seconds or 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m}m" if h else f"{m}m {s}s"


def seconds_to_hours(seconds: int) -> float:
    return round((seconds or 0) / 3600, 2)


def date_range(days: int):
    """List of `date` objects for the last `days` days, oldest first."""
    today = date.today()
    return [today - timedelta(days=i) for i in range(days - 1, -1, -1)]


def compute_heuristic_score(coding_seconds, compile_count, keyboard_count,
                              project_switches, idle_seconds):
    """
    Lightweight, explainable productivity formula used to populate
    DailyStat.productivity_score in real time (before/without the ML
    model). This keeps the dashboard responsive even before enough
    data exists to train a model.
    """
    coding_hours = (coding_seconds or 0) / 3600
    total = (coding_seconds or 0) + (idle_seconds or 0)
    idle_ratio = (idle_seconds or 0) / total if total else 0

    score = (
        coding_hours * 12
        + (compile_count or 0) * 1.5
        + (keyboard_count or 0) / 200
        - (project_switches or 0) * 0.8
        - idle_ratio * 20
    )
    return max(0.0, min(100.0, round(score, 1)))


def badge_list(current_streak, longest_streak, total_hours_alltime):
    """Simple achievement-badge logic for the gamification feature."""
    badges = []
    if current_streak >= 3:
        badges.append({"name": "3-Day Streak", "icon": "🔥"})
    if current_streak >= 7:
        badges.append({"name": "Week Warrior", "icon": "⚡"})
    if longest_streak >= 30:
        badges.append({"name": "Consistency Master", "icon": "🏆"})
    if total_hours_alltime >= 10:
        badges.append({"name": "10 Hours Club", "icon": "🎯"})
    if total_hours_alltime >= 100:
        badges.append({"name": "Century Coder", "icon": "💯"})
    return badges
