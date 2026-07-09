"""
Machine learning routes: shows model accuracy/feature importance, and
lets the user trigger training + view today/tomorrow/weekly predictions.
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import MLPrediction
from app.ml import train as ml_train
from app.ml import predict as ml_predict

ml_bp = Blueprint("ml", __name__, url_prefix="/ml")


@ml_bp.route("/")
@login_required
def index():
    bundle = ml_train.load_model(current_user.id)
    metrics = None
    if bundle is None:
        metrics = ml_train.train_models(current_user.id)

    today_score = ml_predict.predict_today(current_user.id)
    tomorrow_score = ml_predict.predict_tomorrow(current_user.id)
    trend = ml_predict.predict_weekly_trend(current_user.id)

    return render_template(
        "ml.html", metrics=metrics, today_score=today_score,
        tomorrow_score=tomorrow_score, trend=trend,
        model_name=(bundle or {}).get("model_name") if bundle else
        (metrics or {}).get("chosen_model"),
    )


@ml_bp.route("/retrain", methods=["POST"])
@login_required
def retrain():
    metrics = ml_train.train_models(current_user.id)
    return jsonify(metrics)


@ml_bp.route("/predict", methods=["POST"])
@login_required
def predict():
    kind = request.json.get("type", "today") if request.is_json else "today"

    if kind == "tomorrow":
        score = ml_predict.predict_tomorrow(current_user.id)
    elif kind == "weekly":
        return jsonify({"trend": ml_predict.predict_weekly_trend(current_user.id)})
    else:
        score = ml_predict.predict_today(current_user.id)

    bundle = ml_train.load_model(current_user.id)
    record = MLPrediction(
        user_id=current_user.id,
        prediction_type=kind,
        predicted_score=score,
        model_used=(bundle or {}).get("model_name", "Unknown"),
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({"prediction_type": kind, "score": score})
