
from datetime import date
from app.extensions import db


class DailyStat(db.Model):
    __tablename__ = "daily_stats"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, default=date.today)

    coding_time_seconds = db.Column(db.Integer, default=0)
    keyboard_count = db.Column(db.Integer, default=0)
    mouse_clicks = db.Column(db.Integer, default=0)
    compile_count = db.Column(db.Integer, default=0)
    project_switches = db.Column(db.Integer, default=0)
    idle_seconds = db.Column(db.Integer, default=0)
    languages_used = db.Column(db.Integer, default=0)
    sessions_count = db.Column(db.Integer, default=0)

    productivity_score = db.Column(db.Float, default=0.0)  # 0-100, computed heuristically or by ML

    __table_args__ = (
        db.UniqueConstraint("user_id", "date", name="uq_user_date"),
    )

    def __repr__(self):
        return f"<DailyStat {self.date} score={self.productivity_score}>"
