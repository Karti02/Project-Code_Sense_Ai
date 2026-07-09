"""
CodeSense AI - Application Configuration
Central place for all configurable settings.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # --- Core Flask settings ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "codesense-ai-dev-secret-key-change-me")

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'codesense.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Folders ---
    SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
    DATASET_DIR = os.path.join(BASE_DIR, "datasets")
    REPORTS_DIR = os.path.join(BASE_DIR, "reports")
    MODEL_DIR = os.path.join(BASE_DIR, "app", "ml", "saved_models")

    # --- Activity monitor defaults ---
    IDLE_THRESHOLD_SECONDS = 60          # no input for this long => idle
    SCREENSHOT_INTERVAL_SECONDS = 300    # every 5 minutes
    SCREENSHOTS_ENABLED_DEFAULT = True

    # --- Supported IDE / app process names ---
    TRACKED_APPS = {
        "Code.exe": "VS Code",
        "code": "VS Code",
        "pycharm64.exe": "PyCharm",
        "pycharm": "PyCharm",
        "cursor": "Cursor IDE",
        "Cursor.exe": "Cursor IDE",
        "notepad++.exe": "Notepad++",
        "notepad++": "Notepad++",
        "WindowsTerminal.exe": "Terminal",
        "cmd.exe": "Terminal",
        "bash": "Terminal",
        "zsh": "Terminal",
        "Terminal": "Terminal",
    }

    # --- Supported languages by file extension ---
    LANGUAGE_EXTENSIONS = {
        ".py": "Python",
        ".c": "C",
        ".cpp": "C++",
        ".cc": "C++",
        ".h": "C",
        ".hpp": "C++",
        ".java": "Java",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".html": "HTML",
        ".htm": "HTML",
        ".css": "CSS",
        ".php": "PHP",
        ".go": "Go",
        ".rs": "Rust",
        ".kt": "Kotlin",
        ".swift": "Swift",
        ".sql": "SQL",
        ".json": "JSON",
        ".md": "Markdown",
    }


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
