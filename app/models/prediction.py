
from datetime import datetime
from app.extensions import db


class MLPrediction(db.Model):
    __tablename__ = "ml_predictions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    prediction_type = db.Column(db.String(20))   # "today", "tomorrow", "weekly"
    predicted_score = db.Column(db.Float)
    model_used = db.Column(db.String(50))        # "RandomForest" / "LinearRegression"
    model_accuracy = db.Column(db.Float, default=0.0)  # R^2 on test split at train time
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MLPrediction {self.prediction_type}={self.predicted_score:.1f}>"
