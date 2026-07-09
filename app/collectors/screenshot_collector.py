"""
Automatically captures periodic screenshots while the user is coding,
using PyAutoGUI, and saves them under:

    screenshots/YYYY/MM/DD/HHMMSS.png

Runs as a background thread started by services/activity_service.py.
Can be paused/resumed/reconfigured from Settings without restarting
the whole app.
"""

import os
import time
import threading
from datetime import datetime

try:
    import pyautogui
except Exception:  # pragma: no cover - no display available
    pyautogui = None


class ScreenshotCollector:
    def __init__(self, base_dir: str, interval_seconds: int = 300, enabled: bool = True):
        self.base_dir = base_dir
        self.interval_seconds = interval_seconds
        self.enabled = enabled
        self._thread = None
        self._running = False
        self.on_capture = None  # optional callback(file_path) e.g. to save DB row

    def configure(self, interval_seconds=None, enabled=None):
        if interval_seconds is not None:
            self.interval_seconds = interval_seconds
        if enabled is not None:
            self.enabled = enabled

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _run_loop(self):
        while self._running:
            if self.enabled and pyautogui is not None:
                try:
                    self.capture_now()
                except Exception:
                    pass
            time.sleep(max(5, self.interval_seconds))

    def capture_now(self):
        """Take one screenshot immediately and return the relative saved path."""
        if pyautogui is None:
            return None

        now = datetime.now()
        rel_dir = os.path.join(now.strftime("%Y"), now.strftime("%m"), now.strftime("%d"))
        full_dir = os.path.join(self.base_dir, rel_dir)
        os.makedirs(full_dir, exist_ok=True)

        file_name = now.strftime("%H%M%S") + ".png"
        rel_path = os.path.join(rel_dir, file_name)
        full_path = os.path.join(full_dir, file_name)

        screenshot = pyautogui.screenshot()
        screenshot.save(full_path)

        if self.on_capture:
            try:
                self.on_capture(rel_path)
            except Exception:
                pass

        return rel_path


# Per-user collectors are created lazily in activity_service.py, since
# interval/enabled settings are per-user.
collectors_by_user = {}


def get_collector_for_user(user_id, base_dir, interval_seconds=300, enabled=True):
    collector = collectors_by_user.get(user_id)
    if collector is None:
        collector = ScreenshotCollector(base_dir, interval_seconds, enabled)
        collectors_by_user[user_id] = collector
    else:
        collector.configure(interval_seconds=interval_seconds, enabled=enabled)
    return collector
