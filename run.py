import os
from app import create_app
from app.services.activity_service import start_monitoring

config_name = os.environ.get("FLASK_ENV", "development")
app = create_app(config_name)

if __name__ == "__main__":
    start_monitoring()
    app.run(debug=app.config.get("DEBUG", True), host="127.0.0.1", port=5000)
