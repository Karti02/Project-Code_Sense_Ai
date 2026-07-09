"""
Analytics service - uses Pandas to turn raw DailyStat / CodingSession /
LanguageUsage rows into the summaries shown on the Dashboard, Activity
and Reports pages.
"""

from datetime import date, timedelta

import pandas as pd

from app.models import DailyStat, CodingSession, LanguageUsage


def _daily_stats_df(user_id, days=30):
    since = date.today() - timedelta(days=days)
    rows = DailyStat.query.filter(DailyStat.user_id == user_id, DailyStat.date >= since).all()
    data = [{
        "date": r.date,
        "coding_time_seconds": r.coding_time_seconds,
        "keyboard_count": r.keyboard_count,
        "mouse_clicks": r.mouse_clicks,
        "compile_count": r.compile_count,
        "project_switches": r.project_switches,
        "idle_seconds": r.idle_seconds,
        "languages_used": r.languages_used,
        "sessions_count": r.sessions_count,
        "productivity_score": r.productivity_score,
    } for r in rows]
    return pd.DataFrame(data)


def _sessions_df(user_id, days=30):
    since = date.today() - timedelta(days=days)
    rows = CodingSession.query.filter(
        CodingSession.user_id == user_id,
        CodingSession.start_time >= since,
    ).all()
    data = [{
        "app_name": r.app_name,
        "project_name": r.project_name,
        "language": r.language,
        "duration_seconds": r.duration_seconds,
        "start_time": r.start_time,
        "compile_count": r.compile_count,
    } for r in rows]
    return pd.DataFrame(data)


def daily_summary(user_id):
    today = date.today()
    stat = DailyStat.query.filter_by(user_id=user_id, date=today).first()
    if not stat:
        return {
            "coding_time_seconds": 0, "keyboard_count": 0, "mouse_clicks": 0,
            "compile_count": 0, "sessions_count": 0, "productivity_score": 0.0,
        }
    return {
        "coding_time_seconds": stat.coding_time_seconds,
        "keyboard_count": stat.keyboard_count,
        "mouse_clicks": stat.mouse_clicks,
        "compile_count": stat.compile_count,
        "sessions_count": stat.sessions_count,
        "productivity_score": round(stat.productivity_score, 1),
    }


def weekly_summary(user_id):
    df = _daily_stats_df(user_id, days=7)
    if df.empty:
        return {"total_hours": 0.0, "avg_score": 0.0, "by_day": []}
    total_hours = round(df["coding_time_seconds"].sum() / 3600, 2)
    avg_score = round(df["productivity_score"].mean(), 1)
    by_day = [
        {"date": str(row["date"]), "hours": round(row["coding_time_seconds"] / 3600, 2),
         "score": round(row["productivity_score"], 1)}
        for _, row in df.sort_values("date").iterrows()
    ]
    return {"total_hours": total_hours, "avg_score": avg_score, "by_day": by_day}


def monthly_summary(user_id):
    df = _daily_stats_df(user_id, days=30)
    if df.empty:
        return {"total_hours": 0.0, "avg_score": 0.0, "days_active": 0}
    return {
        "total_hours": round(df["coding_time_seconds"].sum() / 3600, 2),
        "avg_score": round(df["productivity_score"].mean(), 1),
        "days_active": int((df["coding_time_seconds"] > 0).sum()),
    }


def most_used_language(user_id, days=30):
    since = date.today() - timedelta(days=days)
    rows = LanguageUsage.query.filter(
        LanguageUsage.user_id == user_id, LanguageUsage.date >= since
    ).all()
    if not rows:
        return None
    df = pd.DataFrame([{"language": r.language, "seconds": r.seconds_spent} for r in rows])
    grouped = df.groupby("language")["seconds"].sum().sort_values(ascending=False)
    return grouped.index[0] if len(grouped) else None


def language_distribution(user_id, days=30):
    since = date.today() - timedelta(days=days)
    rows = LanguageUsage.query.filter(
        LanguageUsage.user_id == user_id, LanguageUsage.date >= since
    ).all()
    if not rows:
        return {}
    df = pd.DataFrame([{"language": r.language, "seconds": r.seconds_spent} for r in rows])
    grouped = df.groupby("language")["seconds"].sum().sort_values(ascending=False)
    return {lang: int(secs) for lang, secs in grouped.items()}


def most_productive_day(user_id, days=30):
    df = _daily_stats_df(user_id, days=days)
    if df.empty:
        return None
    best = df.loc[df["productivity_score"].idxmax()]
    return {"date": str(best["date"]), "score": round(best["productivity_score"], 1)}


def average_and_longest_session(user_id, days=30):
    df = _sessions_df(user_id, days=days)
    if df.empty:
        return {"average_seconds": 0, "longest_seconds": 0}
    return {
        "average_seconds": int(df["duration_seconds"].mean()),
        "longest_seconds": int(df["duration_seconds"].max()),
    }


def project_usage(user_id, days=30):
    df = _sessions_df(user_id, days=days)
    if df.empty:
        return {}
    grouped = df.groupby("project_name")["duration_seconds"].sum().sort_values(ascending=False)
    return {proj: int(secs) for proj, secs in grouped.items()}


def weekly_chart_data(user_id):
    """Last 7 days of coding hours, for the Chart.js bar/line chart."""
    df = _daily_stats_df(user_id, days=7)
    labels, hours = [], []
    today = date.today()
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        labels.append(d.strftime("%a"))
        if not df.empty and d in set(df["date"]):
            row = df[df["date"] == d].iloc[0]
            hours.append(round(row["coding_time_seconds"] / 3600, 2))
        else:
            hours.append(0.0)
    return {"labels": labels, "hours": hours}
