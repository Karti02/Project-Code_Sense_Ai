

from datetime import datetime
from app.extensions import db


class Screenshot(db.Model):
    __tablename__ = "screenshots"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey("coding_sessions.id"), nullable=True)

    file_path = db.Column(db.String(500), nullable=False)  # relative path
    taken_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Screenshot {self.file_path}>"
