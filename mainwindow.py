"""Main window for fterm: menus, toolbar, statusbar."""

import os
import base64
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QMainWindow, QAction, QMenu, QToolBar, QStatusBar, QLabel,
    QMessageBox, QApplication, QVBoxLayout, QWidget,
)
from session_tab_manager import SessionTabManager
from preferences_dialog import PreferencesDialog
from session_manager import SessionManager
from settings import Settings
from themes import get_theme, get_theme_names, get_app_stylesheet
from find_bar import FindBar


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, settings=None):
        super().__init__()
        self._settings = settings or Settings()
        self._session_manager = SessionManager()

        self.setWindowTitle("fterm")
        self.resize(900, 600)

        self._setup_central_widget()
        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self._create_statusbar()
        self._apply_current_theme()
        self._setup_connections()
        self._restore_geometry()

        # Status bar update timer
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_statusbar)
        self._status_timer.start(1000)

    def _setup_central_widget(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tab_manager = SessionTabManager(self._settings, self)
        layout.addWidget(self._tab_manager, 1)

        self._find_bar = FindBar(self)
        self._find_bar.find_requested.connect(self._on_find_requested)
        self._find_bar.closed.connect(self._on_find_closed)
        layout.addWidget(self._find_bar)

        self.setCentralWidget(central)

    def _setup_connections(self):
        self._tab_manager.current_terminal_changed.connect(self._on_terminal_changed)
        self._tab_manager.tab_count_changed.connect(self._on_tab_count_changed)
        self._tab_manager.terminal_title_changed.connect(self._on_title_changed)
        self._settings.settings_changed.connect(self._on_settings_changed)

    # --- Actions ---

    def _create_actions(self):
        # File actions
        self._new_tab_action = self._make_action("New Tab", "Ctrl+Shift+T", self._new_tab)
        self._close_tab_action = self._make_action("Close Tab", "Ctrl+Shift+W", self._close_tab)
        self._exit_action = self._make_action("Exit", "Alt+F4", self.close)

        # Edit actions
        self._copy_action = self._make_action("Copy", "Ctrl+Shift+C", self._copy)
        self._paste_action = self._make_action("Paste", "Ctrl+Shift+V", self._paste)
        self._find_action = self._make_action("Find", "Ctrl+Shift+F", self._show_find)
        self._select_all_action = self._make_action("Select All", None, self._select_all)
        self._clear_action = self._make_action("Clear", None, self._clear)
        self._reset_action = self._make_action("Reset", None, self._reset)

        # View actions
        self._zoom_in_action = self._make_action("Zoom In", "Ctrl+Shift+=", self._zoom_in)
        self._zoom_out_action = self._make_action("Zoom Out", "Ctrl+Shift+-", self._zoom_out)
        self._zoom_reset_action = self._make_action("Reset Zoom", "Ctrl+Shift+0", self._zoom_reset)
        self._fullscreen_action = self._make_action("Full Screen", "F11", self._toggle_fullscreen)
        self._fullscreen_action.setCheckable(True)

        # Tab switching
        self._next_tab_action = self._make_action("Next Tab", "Ctrl+Tab", self._next_tab)
        self._prev_tab_action = self._make_action("Previous Tab", "Ctrl+Shift+Tab", self._prev_tab)

    def _make_action(self, text, shortcut, slot):
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        return action

    # --- Menus ---

    def _create_menus(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self._new_tab_action)
        file_menu.addAction(self._close_tab_action)
        file_menu.addSeparator()
        file_menu.addAction(self._exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(self._copy_action)
        edit_menu.addAction(self._paste_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self._find_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self._select_all_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self._clear_action)
        edit_menu.addAction(self._reset_action)

        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self._zoom_in_action)
        view_menu.addAction(self._zoom_out_action)
        view_menu.addAction(self._zoom_reset_action)
        view_menu.addSeparator()
        view_menu.addAction(self._fullscreen_action)

        # Tabs menu
        tabs_menu = menubar.addMenu("&Tabs")
        tabs_menu.addAction(self._next_tab_action)
        tabs_menu.addAction(self._prev_tab_action)

        # Tools menu
        tools_menu = menubar.addMenu("T&ools")
        prefs_action = tools_menu.addAction("Preferences...")
        prefs_action.triggered.connect(self._show_preferences)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        about_action = help_menu.addAction("About fterm")
        about_action.triggered.connect(self._show_about)

    # --- Toolbar ---

    def _create_toolbar(self):
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)

        toolbar.addAction(self._new_tab_action)
        toolbar.addSeparator()
        toolbar.addAction(self._copy_action)
        toolbar.addAction(self._paste_action)
        toolbar.addSeparator()
        toolbar.addAction(self._zoom_in_action)
        toolbar.addAction(self._zoom_out_action)

    # --- Status bar ---

    def _create_statusbar(self):
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)

        self._dims_label = QLabel("80x24")
        self._dims_label.setMinimumWidth(80)
        self._statusbar.addPermanentWidget(self._dims_label)

        self._shell_label = QLabel("")
        self._shell_label.setMinimumWidth(80)
        self._statusbar.addPermanentWidget(self._shell_label)

        self._cwd_label = QLabel("")
        self._cwd_label.setMinimumWidth(200)
        self._statusbar.addPermanentWidget(self._cwd_label)

    def _update_statusbar(self):
        terminal = self._tab_manager.current_terminal()
        if terminal is None:
            self._dims_label.setText("")
            self._shell_label.setText("")
            self._cwd_label.setText("")
            return

        self._dims_label.setText(f"{terminal._cols}x{terminal._rows}")
        shell = self._settings.get_shell()
        self._shell_label.setText(os.path.basename(shell))
        self._cwd_label.setText(terminal.get_cwd())

    # --- Signal handlers ---

    def _on_terminal_changed(self, terminal):
        self._update_statusbar()
        if terminal:
            title = terminal.get_title()
            if title:
                self.setWindowTitle(f"{title} - fterm")
            else:
                self.setWindowTitle("fterm")
        else:
            self.setWindowTitle("fterm")

    def _on_title_changed(self, title):
        """Update window title when the active terminal's OSC title changes."""
        if title:
            self.setWindowTitle(f"{title} - fterm")

    def _on_tab_count_changed(self, count):
        if count == 0:
            self._update_statusbar()
            self.close()  # Close window when last tab exits

    def _on_settings_changed(self, key, value):
        if key == "theme":
            self._apply_current_theme()
        elif key in ("font_family", "font_size"):
            self._apply_font_change()
        elif key == "terminal_padding":
            self._apply_padding_change()

    # --- Tab operations ---

    def _new_tab(self):
        self._tab_manager.new_tab()

    def _close_tab(self):
        if self._tab_manager.count() > 0:
            self._tab_manager.close_tab()
        if self._tab_manager.count() == 0:
            self.close()

    def _next_tab(self):
        current = self._tab_manager.currentIndex()
        count = self._tab_manager.count()
        if count > 1:
            self._tab_manager.setCurrentIndex((current + 1) % count)

    def _prev_tab(self):
        current = self._tab_manager.currentIndex()
        count = self._tab_manager.count()
        if count > 1:
            self._tab_manager.setCurrentIndex((current - 1) % count)

    # --- Edit operations ---

    def _copy(self):
        terminal = self._tab_manager.current_terminal()
        if terminal:
            terminal.copy_selection()

    def _paste(self):
        terminal = self._tab_manager.current_terminal()
        if terminal:
            terminal.paste_clipboard()

    def _select_all(self):
        terminal = self._tab_manager.current_terminal()
        if terminal:
            terminal.select_all()

    def _clear(self):
        terminal = self._tab_manager.current_terminal()
        if terminal:
            terminal._clear_terminal()

    def _reset(self):
        terminal = self._tab_manager.current_terminal()
        if terminal:
            terminal._reset_terminal()

    # --- Find ---

    def _show_find(self):
        self._find_bar.show_bar()

    def _on_find_requested(self, query, forward):
        terminal = self._tab_manager.current_terminal()
        if terminal:
            current, total = terminal.find_in_scrollback(query, forward)
            self._find_bar.set_match_info(current, total)

    def _on_find_closed(self):
        terminal = self._tab_manager.current_terminal()
        if terminal:
            terminal.clear_selection()
            terminal.setFocus()

    # --- View operations ---

    def _zoom_in(self):
        terminal = self._tab_manager.current_terminal()
        if terminal:
            terminal.zoom_in()

    def _zoom_out(self):
        terminal = self._tab_manager.current_terminal()
        if terminal:
            terminal.zoom_out()

    def _zoom_reset(self):
        terminal = self._tab_manager.current_terminal()
        if terminal:
            terminal.zoom_reset()

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self._fullscreen_action.setChecked(False)
        else:
            self.showFullScreen()
            self._fullscreen_action.setChecked(True)

    # --- Tools ---

    def _show_preferences(self):
        dialog = PreferencesDialog(self._settings, self)
        dialog.exec_()

    def _show_about(self):
        from main import VERSION
        QMessageBox.about(
            self,
            "About fterm",
            f"<h2>fterm v{VERSION}</h2>"
            "<p>A terminal emulator built from scratch</p>"
            "<p>Built with Python, PyQt5, and pyte</p>"
            "<p>&copy; SOS Tech Services</p>",
        )

    # --- Theme ---

    def _apply_current_theme(self):
        theme_name = self._settings.get("theme", "Dark")
        theme = get_theme(theme_name)
        self.setStyleSheet(get_app_stylesheet(theme))

        # Apply to all open terminals
        for i in range(self._tab_manager.count()):
            terminal = self._tab_manager.widget(i)
            terminal.apply_theme(theme)

    def _apply_font_change(self):
        family = self._settings.get("font_family", "Monospace")
        size = self._settings.get("font_size", 11)
        for i in range(self._tab_manager.count()):
            terminal = self._tab_manager.widget(i)
            terminal.update_font(family, size)

    def _apply_padding_change(self):
        padding = self._settings.get("terminal_padding", 4)
        for i in range(self._tab_manager.count()):
            terminal = self._tab_manager.widget(i)
            terminal._padding = padding
            terminal._recalculate_grid()
            terminal.update()

    # --- Window state ---

    def _restore_geometry(self):
        geo = self._settings.get("window_geometry")
        state = self._settings.get("window_state")
        if geo:
            from PyQt5.QtCore import QByteArray
            try:
                self.restoreGeometry(QByteArray(base64.b64decode(geo)))
            except Exception:
                pass
        if state:
            from PyQt5.QtCore import QByteArray
            try:
                self.restoreState(QByteArray(base64.b64decode(state)))
            except Exception:
                pass

    def _save_geometry(self):
        geo = base64.b64encode(bytes(self.saveGeometry())).decode("ascii")
        state = base64.b64encode(bytes(self.saveState())).decode("ascii")
        self._settings.set("window_geometry", geo)
        self._settings.set("window_state", state)

    # --- Session ---

    def restore_session(self):
        if self._settings.get("restore_session", True):
            return self._session_manager.restore_session(self._tab_manager)
        return False

    # --- Close event ---

    def closeEvent(self, event):
        # Save session
        if self._settings.get("auto_save_session", True):
            self._session_manager.save_session(self._tab_manager)

        # Save geometry
        self._save_geometry()

        # Check for running processes
        if self._settings.get("confirm_close_running", True):
            running = 0
            for i in range(self._tab_manager.count()):
                terminal = self._tab_manager.widget(i)
                if terminal.get_process().is_alive():
                    running += 1
            if running > 0:
                reply = QMessageBox.question(
                    self,
                    "Close fterm",
                    f"{running} terminal(s) still running. Close anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    event.ignore()
                    return

        # Terminate all processes
        self._tab_manager.close_all_tabs()
        event.accept()
