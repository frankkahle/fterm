"""Settings persistence using JSON configuration."""

import json
import os
from PyQt5.QtCore import QObject, pyqtSignal


DEFAULT_SETTINGS = {
    "font_family": "Monospace",
    "font_size": 11,
    "theme": "Light",
    "scrollback_lines": 10000,
    "cursor_style": "block",  # block, underline, bar
    "cursor_blink": True,
    "shell": "",  # empty = use $SHELL or /bin/bash
    "confirm_close_running": True,
    "auto_save_session": True,
    "restore_session": True,
    "window_geometry": None,
    "window_state": None,
    "zoom_level": 0,
}

CONFIG_DIR = os.path.expanduser("~/.config/fterm")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")


class Settings(QObject):
    """Application settings backed by a JSON file."""

    settings_changed = pyqtSignal(str, object)  # key, value

    def __init__(self):
        super().__init__()
        self._data = dict(DEFAULT_SETTINGS)
        self._ensure_config_dir()
        self.load()

    def _ensure_config_dir(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)

    def load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                for key, value in stored.items():
                    if key in DEFAULT_SETTINGS:
                        self._data[key] = value
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        self._ensure_config_dir()
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except OSError:
            pass

    def get(self, key, default=None):
        return self._data.get(key, default if default is not None else DEFAULT_SETTINGS.get(key))

    def set(self, key, value):
        old = self._data.get(key)
        self._data[key] = value
        if old != value:
            self.settings_changed.emit(key, value)
            self.save()

    def get_shell(self):
        """Return the configured shell or fall back to $SHELL or /bin/bash."""
        shell = self._data.get("shell", "")
        if shell:
            return shell
        return os.environ.get("SHELL", "/bin/bash")
