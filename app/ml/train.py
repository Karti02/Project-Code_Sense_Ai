

import os
import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error

from app.ml.dataset_generator import build_dataset, FEATURE_COLUMNS, TARGET_COLUMN
from config import Config


def _model_path(user_id):
    return os.path.join(Config.MODEL_DIR, f"user_{user_id}_model.joblib")


def train_models(user_id, test_size=0.2, random_state=42):
    """
    Trains RandomForest + LinearRegression, picks the better one by R^2,
    and persists it. Returns a metrics dict for display on the ML page.
    """
    df = build_dataset(user_id)
    X = df[FEATURE_COLUMNS].values
    y = df[TARGET_COLUMN].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    rf = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=random_state)
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    rf_r2 = r2_score(y_test, rf_pred)
    rf_mae = mean_absolute_error(y_test, rf_pred)

    lr = LinearRegression()
    lr.fit(X_train, y_train)
    lr_pred = lr.predict(X_test)
    lr_r2 = r2_score(y_test, lr_pred)
    lr_mae = mean_absolute_error(y_test, lr_pred)

    if rf_r2 >= lr_r2:
        best_model, best_name, best_r2, best_mae = rf, "RandomForest", rf_r2, rf_mae
        feature_importance = dict(zip(FEATURE_COLUMNS, rf.feature_importances_.tolist()))
    else:
        best_model, best_name, best_r2, best_mae = lr, "LinearRegression", lr_r2, lr_mae
        # Linear regression "importance" via absolute coefficient magnitude, normalized
        coefs = np.abs(lr.coef_)
        total = coefs.sum() or 1
        feature_importance = dict(zip(FEATURE_COLUMNS, (coefs / total).tolist()))

    os.makedirs(Config.MODEL_DIR, exist_ok=True)
    joblib.dump({
        "model": best_model,
        "model_name": best_name,
        "feature_columns": FEATURE_COLUMNS,
    }, _model_path(user_id))

    return {
        "chosen_model": best_name,
        "chosen_r2": round(float(best_r2), 3),
        "chosen_mae": round(float(best_mae), 2),
        "random_forest": {"r2": round(float(rf_r2), 3), "mae": round(float(rf_mae), 2)},
        "linear_regression": {"r2": round(float(lr_r2), 3), "mae": round(float(lr_mae), 2)},
        "feature_importance": {k: round(v, 4) for k, v in
                                sorted(feature_importance.items(), key=lambda kv: -kv[1])},
        "training_rows": len(df),
    }


def load_model(user_id):
    path = _model_path(user_id)
    if not os.path.exists(path):
        return None
    return joblib.load(path)
