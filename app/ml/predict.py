"""
Uses the saved per-user model to predict:
  - today's productivity (from current DailyStat so far)
  - tomorrow's productivity (from recent trend / averages)
  - a 7-day weekly productivity trend
"""

from datetime import date, timedelta
import numpy as np

from app.models import DailyStat, LanguageUsage
from app.ml.train import load_model, train_models
from app.ml.dataset_generator import FEATURE_COLUMNS


def _features_from_stat(stat, languages_used=1):
    return np.array([[
        stat.coding_time_seconds,
        stat.keyboard_count,
        stat.mouse_clicks,
        stat.compile_count,
        stat.project_switches,
        stat.idle_seconds,
        languages_used,
        stat.sessions_count,
    ]])


def _ensure_model(user_id):
    bundle = load_model(user_id)
    if bundle is None:
        train_models(user_id)
        bundle = load_model(user_id)
    return bundle


def _languages_used_today(user_id):
    today = date.today()
    rows = LanguageUsage.query.filter_by(user_id=user_id, date=today).all()
    return len(set(r.language for r in rows)) or 1


def predict_today(user_id):
    bundle = _ensure_model(user_id)
    stat = DailyStat.query.filter_by(user_id=user_id, date=date.today()).first()
    if stat is None:
        return 0.0
    X = _features_from_stat(stat, _languages_used_today(user_id))
    score = float(bundle["model"].predict(X)[0])
    return round(max(0, min(100, score)), 1)


def predict_tomorrow(user_id, lookback_days=7):
    """
    Uses the average of the last `lookback_days` DailyStat rows as the
    projected feature vector for tomorrow, then predicts on that.
    """
    bundle = _ensure_model(user_id)
    since = date.today() - timedelta(days=lookback_days)
    rows = DailyStat.query.filter(
        DailyStat.user_id == user_id, DailyStat.date >= since
    ).all()
    if not rows:
        return 0.0

    avg = {
        "coding_time": np.mean([r.coding_time_seconds for r in rows]),
        "keyboard_count": np.mean([r.keyboard_count for r in rows]),
        "mouse_clicks": np.mean([r.mouse_clicks for r in rows]),
        "compile_count": np.mean([r.compile_count for r in rows]),
        "project_switches": np.mean([r.project_switches for r in rows]),
        "idle_time": np.mean([r.idle_seconds for r in rows]),
        "languages_used": max(1, np.mean([r.languages_used or 1 for r in rows])),
        "sessions": np.mean([r.sessions_count for r in rows]),
    }
    X = np.array([[avg[c] for c in FEATURE_COLUMNS]])
    score = float(bundle["model"].predict(X)[0])
    return round(max(0, min(100, score)), 1)


def predict_weekly_trend(user_id):
    """
    Returns a 7-point trend: the model's prediction applied to each of
    the last 7 days' actual stats (a smoothed view of how productivity
    is trending, according to the model rather than the raw heuristic).
    """
    bundle = _ensure_model(user_id)
    today = date.today()
    trend = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        stat = DailyStat.query.filter_by(user_id=user_id, date=d).first()
        if stat is None:
            trend.append({"date": str(d), "predicted_score": 0.0})
            continue
        X = _features_from_stat(stat, stat.languages_used or 1)
        score = float(bundle["model"].predict(X)[0])
        trend.append({"date": str(d), "predicted_score": round(max(0, min(100, score)), 1)})
    return trend
