"""
LanguageUsage: aggregated time-per-language, per user, per day.
Kept separate (rather than recomputed each time from sessions) so
dashboard/analytics queries stay fast.
"""

from datetime import date
from app.extensions import db


class LanguageUsage(db.Model):
    __tablename__ = "language_usage"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    language = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, default=date.today)
    seconds_spent = db.Column(db.Integer, default=0)

    __table_args__ = (
        db.UniqueConstraint("user_id", "language", "date", name="uq_user_lang_date"),
    )

    def __repr__(self):
        return f"<LanguageUsage {self.language} {self.date} {self.seconds_spent}s>"
