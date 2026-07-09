"""
Detects which application the user is currently working in, and (when
possible) the file/window title, so we can infer the project and file
being edited.

Works cross-platform on a best-effort basis:
  - Windows: uses `pygetwindow` (falls back to psutil process list)
  - Linux:   uses `wmctrl` / `xdotool` if installed (falls back to psutil)
  - macOS:   uses AppleScript via `osascript` (falls back to psutil)

If none of the platform tools are available, we fall back to scanning
running processes with psutil and matching against Config.TRACKED_APPS,
so the app still works out of the box (title/file just won't be known).
"""

import platform
import subprocess
import psutil

from config import Config


def _match_tracked_app(process_name: str):
    """Match a raw process name against the configured tracked-app map."""
    if not process_name:
        return None
    key = process_name.strip()
    if key in Config.TRACKED_APPS:
        return Config.TRACKED_APPS[key]
    lowered = key.lower()
    for proc_key, app_label in Config.TRACKED_APPS.items():
        if proc_key.lower() in lowered:
            return app_label
    return None


def _active_window_windows():
    try:
        import pygetwindow as gw
        win = gw.getActiveWindow()
        if win:
            return win.title
    except Exception:
        pass
    return None


def _active_window_linux():
    for cmd in (["xdotool", "getactivewindow", "getwindowname"],
                ["wmctrl", "-a", ":ACTIVE:"]):
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=1)
            return out.decode(errors="ignore").strip()
        except Exception:
            continue
    return None


def _active_window_mac():
    script = (
        'tell application "System Events" to get name of first process '
        'whose frontmost is true'
    )
    try:
        out = subprocess.check_output(["osascript", "-e", script], timeout=1)
        return out.decode(errors="ignore").strip()
    except Exception:
        return None


def get_active_window_title():
    """Return the raw active window title string, or None if unavailable."""
    system = platform.system()
    if system == "Windows":
        return _active_window_windows()
    if system == "Linux":
        return _active_window_linux()
    if system == "Darwin":
        return _active_window_mac()
    return None


def get_active_app_via_processes():
    """
    Fallback: scan running processes and return the first one that matches
    a tracked IDE/terminal. Not as accurate as window-title detection but
    works everywhere psutil works.
    """
    try:
        for proc in psutil.process_iter(["name"]):
            name = proc.info.get("name") or ""
            label = _match_tracked_app(name)
            if label:
                return label
    except Exception:
        pass
    return "Unknown"


def get_current_activity():
    """
    Returns a dict describing what the user is currently doing:
        {
            "app_name": "VS Code",
            "window_title": "main.py - CodeSense AI - Visual Studio Code",
            "file_name": "main.py"   # best-effort guess from title
        }
    """
    title = get_active_window_title()
    app_name = "Unknown"
    file_name = ""

    if title:
        app_name = _match_tracked_app(title) or "Unknown"
        # Many IDE titles look like "filename.ext - ProjectName - App"
        first_segment = title.split(" - ")[0].strip()
        if "." in first_segment and " " not in first_segment:
            file_name = first_segment

    if app_name == "Unknown":
        app_name = get_active_app_via_processes()

    return {
        "app_name": app_name,
        "window_title": title or "",
        "file_name": file_name,
    }
