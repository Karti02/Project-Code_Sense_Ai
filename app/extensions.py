"""
Shared Flask extension instances.
Kept in their own module to avoid circular imports between
app/__init__.py, models, and routes.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access CodeSense AI."
login_manager.login_message_category = "info"
