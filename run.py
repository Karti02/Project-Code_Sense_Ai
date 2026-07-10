import os
from app import create_app
from app.services.activity_service import start_monitoring

config_name = os.environ.get("FLASK_ENV", "development")
app = create_app(config_name)

if __name__ == "__main__":
    # Starts the global keyboard/mouse hooks used for activity tracking.
    # Safe no-op if hooks can't be installed (e.g. missing OS permissions).
    start_monitoring()
    app.run(debug=app.config.get("DEBUG", True), host="127.0.0.1", port=5000)
