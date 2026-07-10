

import os
import numpy as np
import pandas as pd

from app.models import DailyStat, LanguageUsage
from config import Config

FEATURE_COLUMNS = [
    "coding_time", "keyboard_count", "mouse_clicks", "compile_count",
    "project_switches", "idle_time", "languages_used", "sessions",
]
TARGET_COLUMN = "productivity_score"


def _heuristic_productivity_score(row):
    """
    Simple, explainable formula used to (a) label synthetic rows and
    (b) as a sanity baseline: rewards coding time & compiles, penalizes
    idle time and excessive context switching.
    """
    coding_hours = row["coding_time"] / 3600
    idle_ratio = row["idle_time"] / max(row["coding_time"] + row["idle_time"], 1)

    score = (
        coding_hours * 12
        + row["compile_count"] * 1.5
        + row["keyboard_count"] / 200
        - row["project_switches"] * 0.8
        - idle_ratio * 20
    )
    return float(np.clip(score, 0, 100))


def _real_rows_for_user(user_id):
    rows = DailyStat.query.filter_by(user_id=user_id).all()
    lang_counts = {}
    for r in LanguageUsage.query.filter_by(user_id=user_id).all():
        lang_counts.setdefault(r.date, set()).add(r.language)

    data = []
    for r in rows:
        if r.coding_time_seconds <= 0 and r.sessions_count == 0:
            continue
        data.append({
            "coding_time": r.coding_time_seconds,
            "keyboard_count": r.keyboard_count,
            "mouse_clicks": r.mouse_clicks,
            "compile_count": r.compile_count,
            "project_switches": r.project_switches,
            "idle_time": r.idle_seconds,
            "languages_used": len(lang_counts.get(r.date, [])) or r.languages_used or 1,
            "sessions": r.sessions_count,
            "productivity_score": r.productivity_score if r.productivity_score > 0
            else None,  # filled in below if missing
        })
    return data


def _generate_synthetic_rows(n=150, seed=42):
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        coding_time = int(rng.uniform(600, 6 * 3600))          # 10 min - 6 hr
        keyboard_count = int(rng.uniform(200, 15000))
        mouse_clicks = int(rng.uniform(50, 3000))
        compile_count = int(rng.uniform(0, 40))
        project_switches = int(rng.uniform(0, 15))
        idle_time = int(rng.uniform(0, 3600))
        languages_used = int(rng.integers(1, 5))
        sessions = int(rng.integers(1, 8))

        row = {
            "coding_time": coding_time,
            "keyboard_count": keyboard_count,
            "mouse_clicks": mouse_clicks,
            "compile_count": compile_count,
            "project_switches": project_switches,
            "idle_time": idle_time,
            "languages_used": languages_used,
            "sessions": sessions,
        }
        base_score = _heuristic_productivity_score(row)
        noise = rng.normal(0, 4)
        row["productivity_score"] = float(np.clip(base_score + noise, 0, 100))
        rows.append(row)
    return rows


def build_dataset(user_id, min_rows=60, save_csv=True):
    """
    Returns a pandas DataFrame with FEATURE_COLUMNS + TARGET_COLUMN,
    combining real activity (if any) with enough synthetic rows to
    reach `min_rows` total, so the model can train even for new users.
    """
    real_rows = _real_rows_for_user(user_id)
    for row in real_rows:
        if row["productivity_score"] is None:
            row["productivity_score"] = _heuristic_productivity_score(row)

    n_needed = max(0, min_rows - len(real_rows))
    synthetic_rows = _generate_synthetic_rows(n=n_needed) if n_needed else []

    all_rows = real_rows + synthetic_rows
    df = pd.DataFrame(all_rows, columns=FEATURE_COLUMNS + [TARGET_COLUMN])

    if save_csv:
        os.makedirs(Config.DATASET_DIR, exist_ok=True)
        path = os.path.join(Config.DATASET_DIR, f"user_{user_id}_dataset.csv")
        df.to_csv(path, index=False)

    return df
