"""
CodeSense AI - Application factory.
Creates and configures the Flask app, registers extensions and blueprints.
"""

import os
from flask import Flask

from config import config_map
from app.extensions import db, login_manager


def _ensure_user_columns(db):
    """
    Lightweight, dependency-free "migration" for the `users` table.

    This project doesn't use Flask-Migrate/Alembic, so `db.create_all()`
    alone won't add new columns to a database file that already existed
    before the `role` / `is_active_account` columns were introduced. This
    adds them if missing, defaulting every existing row to the safe,
    non-privileged values (role='user', is_active_account=1).
    """
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    if "users" not in inspector.get_table_names():
        return

    existing_columns = {col["name"] for col in inspector.get_columns("users")}
    with db.engine.begin() as conn:
        if "role" not in existing_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL"))
        if "is_active_account" not in existing_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_active_account BOOLEAN DEFAULT 1 NOT NULL"))


def create_app(config_name="development"):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_map.get(config_name, config_map["default"]))

    # Ensure required folders exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["SCREENSHOT_DIR"], exist_ok=True)
    os.makedirs(app.config["DATASET_DIR"], exist_ok=True)
    os.makedirs(app.config["REPORTS_DIR"], exist_ok=True)
    os.makedirs(app.config["MODEL_DIR"], exist_ok=True)

    # --- Extensions ---
    db.init_app(app)
    login_manager.init_app(app)

    # --- Models (must be imported after db.init_app so tables register) ---
    with app.app_context():
        from app import models  # noqa: F401

    # --- Blueprints ---
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.activity import activity_bp
    from app.routes.ml_routes import ml_bp
    from app.routes.reports import reports_bp
    from app.routes.settings import settings_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(ml_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(admin_bp)

    # --- Create tables on first run ---
    with app.app_context():
        db.create_all()
        _ensure_user_columns(db)

    # --- CLI commands ---
    from app.cli import register_cli
    register_cli(app)

    # --- Error handlers ---
    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template("errors/403.html"), 403

    # --- Template helpers ---
    @app.template_filter("hms")
    def hms_filter(seconds):
        """Format seconds as H:MM:SS for templates."""
        seconds = int(seconds or 0)
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{h}:{m:02d}:{s:02d}"

    return app
