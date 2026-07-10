
import time
import threading

try:
    import pyautogui
except Exception:  # pragma: no cover - headless / no display environments
    pyautogui = None

try:
    import keyboard as kb
except Exception:  # pragma: no cover
    kb = None

try:
    import mouse as ms
except Exception:  # pragma: no cover
    ms = None


class InputActivityMonitor:
    """
    Singleton-style monitor that keeps running counters of keyboard/mouse
    activity and the timestamp of the last detected input, for idle
    detection.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.keyboard_count = 0
        self.mouse_clicks = 0
        self.last_input_time = time.time()
        self._last_mouse_pos = None
        self._hooks_installed = False
        self._poll_thread = None
        self._running = False

    # ---------------- Hook installation ----------------

    def start(self):
        if self._running:
            return
        self._running = True

        if kb is not None:
            try:
                kb.on_press(self._on_key_press)
                self._hooks_installed = True
            except Exception:
                pass  # e.g. insufficient permissions

        if ms is not None:
            try:
                ms.on_click(self._on_mouse_click)
                self._hooks_installed = True
            except Exception:
                pass

        # Fallback / supplementary: poll mouse position to catch movement
        # even if click hooks aren't available.
        self._poll_thread = threading.Thread(target=self._poll_mouse_position, daemon=True)
        self._poll_thread.start()

    def stop(self):
        self._running = False
        if kb is not None:
            try:
                kb.unhook_all()
            except Exception:
                pass
        if ms is not None:
            try:
                ms.unhook_all()
            except Exception:
                pass

    # ---------------- Event handlers ----------------

    def _on_key_press(self, event=None):
        with self._lock:
            self.keyboard_count += 1
            self.last_input_time = time.time()

    def _on_mouse_click(self, *args, **kwargs):
        with self._lock:
            self.mouse_clicks += 1
            self.last_input_time = time.time()

    def _poll_mouse_position(self):
        while self._running:
            if pyautogui is not None:
                try:
                    pos = pyautogui.position()
                    if self._last_mouse_pos is not None and pos != self._last_mouse_pos:
                        with self._lock:
                            self.last_input_time = time.time()
                    self._last_mouse_pos = pos
                except Exception:
                    pass
            time.sleep(2)

    # ---------------- Reporting ----------------

    def snapshot_and_reset(self):
        """Return current counts and reset them (used when closing a session)."""
        with self._lock:
            data = {
                "keyboard_count": self.keyboard_count,
                "mouse_clicks": self.mouse_clicks,
            }
            self.keyboard_count = 0
            self.mouse_clicks = 0
            return data

    def seconds_since_last_input(self):
        return time.time() - self.last_input_time


# Module-level singleton used by services/activity_service.py
monitor = InputActivityMonitor()
