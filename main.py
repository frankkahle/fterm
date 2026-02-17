#!/usr/bin/env python3
"""fterm - A terminal emulator built from scratch.

Built with Python 3, PyQt5, and pyte (VT100 parser).
"""

import sys
import os
import argparse

# Suppress noisy Qt/Wayland warnings
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.wayland.warning=false")

# Ensure the application directory is in the path
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from PyQt5.QtWidgets import QApplication, QStyleFactory
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from settings import Settings
from mainwindow import MainWindow

VERSION = "1.0.1"


def parse_args():
    parser = argparse.ArgumentParser(
        description="fterm - A terminal emulator built from scratch"
    )
    parser.add_argument(
        "-e", "--execute",
        help="Shell to execute (default: $SHELL or /bin/bash)",
    )
    parser.add_argument(
        "-d", "--directory",
        help="Starting working directory",
    )
    parser.add_argument(
        "-n", "--new",
        action="store_true",
        help="Start fresh (ignore saved session)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Enable high-DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("fterm")
    app.setOrganizationName("SOS Tech Services")
    app.setApplicationVersion(VERSION)

    # Force Fusion style so system dark theme doesn't bleed through
    app.setStyle(QStyleFactory.create("Fusion"))

    # Set application icon
    icon_path = os.path.join(app_dir, "resources", "fterm.svg")
    if not os.path.exists(icon_path):
        # Installed location
        icon_path = "/opt/fterm/resources/fterm.svg"
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    settings = Settings()
    window = MainWindow(settings)

    # Restore session or start fresh
    restored = False
    if not args.new:
        restored = window.restore_session()

    # Ensure at least one tab is open
    if window._tab_manager.count() == 0:
        shell = args.execute or None
        cwd = args.directory or None
        window._tab_manager.new_tab(shell=shell, cwd=cwd)

    window.show()

    # Apply theme after show for proper rendering
    window._apply_current_theme()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
