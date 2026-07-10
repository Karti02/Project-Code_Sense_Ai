
from datetime import datetime
from app.extensions import db


class CodingSession(db.Model):
    __tablename__ = "coding_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    app_name = db.Column(db.String(120), default="Unknown")
    project_name = db.Column(db.String(200), default="Unknown")
    file_name = db.Column(db.String(200), default="")
    language = db.Column(db.String(50), default="Unknown")

    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, default=0)
    idle_seconds = db.Column(db.Integer, default=0)

    keyboard_count = db.Column(db.Integer, default=0)
    mouse_clicks = db.Column(db.Integer, default=0)
    compile_count = db.Column(db.Integer, default=0)

    is_active = db.Column(db.Boolean, default=True)

    def close(self):
        """Mark session ended and compute duration."""
        self.end_time = datetime.utcnow()
        self.is_active = False
        if self.start_time:
            self.duration_seconds = int((self.end_time - self.start_time).total_seconds())

    def __repr__(self):
        return f"<CodingSession {self.app_name}/{self.language} user={self.user_id}>"


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey("coding_sessions.id"), nullable=True)

    event_type = db.Column(db.String(50))   # "app_switch", "idle_start", "idle_end", "compile"
    app_name = db.Column(db.String(120))
    detail = db.Column(db.String(255), default="")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ActivityLog {self.event_type} @ {self.timestamp}>"
