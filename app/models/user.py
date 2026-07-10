
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Authorization ---
    # "user" (default) or "admin". Kept as a plain string column (rather than
    # a bare boolean) so additional roles can be introduced later without a
    # schema change.
    role = db.Column(db.String(20), default="user", nullable=False)
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)

    # --- Settings ---
    screenshots_enabled = db.Column(db.Boolean, default=True)
    screenshot_interval = db.Column(db.Integer, default=300)  # seconds
    theme = db.Column(db.String(10), default="dark")          # "dark" / "light"
    daily_goal_minutes = db.Column(db.Integer, default=120)

    # --- Gamification ---
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_active_date = db.Column(db.Date, default=None, nullable=True)

    # --- Relationships ---
    sessions = db.relationship("CodingSession", backref="user", lazy=True,
                                cascade="all, delete-orphan")
    activity_logs = db.relationship("ActivityLog", backref="user", lazy=True,
                                     cascade="all, delete-orphan")
    screenshots = db.relationship("Screenshot", backref="user", lazy=True,
                                   cascade="all, delete-orphan")
    daily_stats = db.relationship("DailyStat", backref="user", lazy=True,
                                   cascade="all, delete-orphan")
    predictions = db.relationship("MLPrediction", backref="user", lazy=True,
                                   cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        """True if this account has administrator privileges."""
        return self.role == "admin"

    @property
    def is_active(self) -> bool:
        """Overrides UserMixin.is_active so deactivated accounts can't log in."""
        return self.is_active_account

    def update_streak(self):
        """Call once per day when user has a coding session, to update streak count."""
        today = date.today()
        if self.last_active_date == today:
            return  # already counted today
        if self.last_active_date and (today - self.last_active_date).days == 1:
            self.current_streak += 1
        else:
            self.current_streak = 1
        self.longest_streak = max(self.longest_streak, self.current_streak)
        self.last_active_date = today

    def __repr__(self):
        return f"<User {self.username}>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
