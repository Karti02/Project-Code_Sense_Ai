
import os
from config import Config


def detect_language(file_name: str) -> str:
    """Return the language name for a given file, or 'Unknown'."""
    if not file_name:
        return "Unknown"
    _, ext = os.path.splitext(file_name)
    return Config.LANGUAGE_EXTENSIONS.get(ext.lower(), "Unknown")


def detect_project_name(file_path: str) -> str:
    """
    Best-effort project name: the immediate parent folder of the file,
    or the folder above it if the parent looks like a generic 'src'.
    """
    if not file_path:
        return "Unknown"
    folder = os.path.dirname(os.path.abspath(file_path))
    name = os.path.basename(folder)
    if name.lower() in ("src", "app", "lib") and os.path.dirname(folder):
        name = os.path.basename(os.path.dirname(folder))
    return name or "Unknown"


def is_supported_language(language: str) -> bool:
    return language in set(Config.LANGUAGE_EXTENSIONS.values())
