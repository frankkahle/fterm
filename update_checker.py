"""Background update checker for SOSterm.

Checks https://sos-tech.ca/updates/fterm/latest.json for new versions.
Runs in a QThread to avoid blocking the UI. Respects a 24-hour cooldown
between automatic checks.
"""

import json
import time
import urllib.request
import urllib.error
from PyQt5.QtCore import QThread, pyqtSignal

UPDATE_URL = "https://sos-tech.ca/updates/fterm/latest.json"
CHECK_COOLDOWN = 86400  # 24 hours in seconds


def compare_versions(current, remote):
    """Return True if remote is newer than current (semver comparison)."""
    try:
        cur = [int(x) for x in current.split(".")]
        rem = [int(x) for x in remote.split(".")]
        return rem > cur
    except (ValueError, AttributeError):
        return False


class UpdateCheckThread(QThread):
    """Background thread that checks for updates."""

    update_available = pyqtSignal(str, str, str)  # version, download_url, changelog
    check_finished = pyqtSignal(bool)  # had_update

    def __init__(self, current_version, parent=None):
        super().__init__(parent)
        self._current_version = current_version

    def run(self):
        try:
            req = urllib.request.Request(
                UPDATE_URL,
                headers={"User-Agent": f"SOSterm/{self._current_version}"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            remote_version = data.get("version", "")
            download_url = data.get("download_url", "")
            changelog = data.get("changelog", "")

            if compare_versions(self._current_version, remote_version):
                self.update_available.emit(remote_version, download_url, changelog)
                self.check_finished.emit(True)
            else:
                self.check_finished.emit(False)
        except (urllib.error.URLError, json.JSONDecodeError, OSError, KeyError):
            self.check_finished.emit(False)


class UpdateChecker:
    """Manages update checks with cooldown logic."""

    def __init__(self, current_version, settings):
        self._current_version = current_version
        self._settings = settings
        self._thread = None

    def should_auto_check(self):
        """Return True if enough time has passed since last check."""
        last = self._settings.get("last_update_check", 0)
        return (time.time() - last) >= CHECK_COOLDOWN

    def check(self, on_update=None, on_finished=None, record_time=True):
        """Start a background update check.

        on_update: callback(version, download_url, changelog)
        on_finished: callback(had_update)
        """
        if self._thread and self._thread.isRunning():
            return

        self._thread = UpdateCheckThread(self._current_version)
        if on_update:
            self._thread.update_available.connect(on_update)
        if on_finished:
            self._thread.check_finished.connect(on_finished)
        if record_time:
            self._settings.set("last_update_check", time.time())
        self._thread.start()

    def auto_check(self, on_update=None, on_finished=None):
        """Check only if cooldown has elapsed."""
        if self.should_auto_check():
            self.check(on_update=on_update, on_finished=on_finished)
