"""Session save/restore for fterm."""

import json
import os

from settings import CONFIG_DIR

SESSION_FILE = os.path.join(CONFIG_DIR, "session.json")


class SessionManager:
    """Saves and restores terminal session state."""

    def save_session(self, tab_manager):
        """Save session data from the tab manager."""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        data = tab_manager.get_session_data()
        try:
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass

    def restore_session(self, tab_manager):
        """Restore session data into the tab manager."""
        if not os.path.exists(SESSION_FILE):
            return False
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("tabs"):
                tab_manager.restore_session_data(data)
                return True
        except (json.JSONDecodeError, OSError):
            pass
        return False
