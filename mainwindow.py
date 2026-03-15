"""Main window for SOSterm: menus, toolbar, statusbar, SSH sidebar."""

import os
import sys
import base64
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QMainWindow, QAction, QMenu, QToolBar, QStatusBar, QLabel,
    QMessageBox, QApplication, QVBoxLayout, QWidget, QSplitter,
)
from session_tab_manager import SessionTabManager
from preferences_dialog import PreferencesDialog
from session_manager import SessionManager
from settings import Settings
from themes import get_theme, get_theme_names, get_app_stylesheet
from find_bar import FindBar
from ssh_session_store import SSHSessionStore, SSHSession
from ssh_sidebar import SSHSidebarPanel
from ssh_dialogs import SSHSessionDialog, SSHGroupDialog, SSHImportDialog
from update_checker import UpdateChecker


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, settings=None, version=""):
        super().__init__()
        self._settings = settings or Settings()
        self._version = version
        self._session_manager = SessionManager()
        self._ssh_store = SSHSessionStore()

        self.setWindowTitle("SOSterm")
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
        self._status_timer.start(2000)

        # Update checker (auto-check after short delay to not slow startup)
        self._update_checker = UpdateChecker(self._version, self._settings)
        QTimer.singleShot(3000, self._auto_check_updates)

    def _setup_central_widget(self):
        # Horizontal splitter: SSH sidebar (left) | terminal area (right)
        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setChildrenCollapsible(False)

        # SSH sidebar
        self._ssh_sidebar = SSHSidebarPanel(self._ssh_store, self)
        self._ssh_sidebar.setVisible(True)
        self._splitter.addWidget(self._ssh_sidebar)

        # Terminal area (tabs + find bar)
        terminal_area = QWidget()
        layout = QVBoxLayout(terminal_area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tab_manager = SessionTabManager(self._settings, self)
        self._tab_manager.set_ssh_store(self._ssh_store)
        layout.addWidget(self._tab_manager, 1)

        self._find_bar = FindBar(self)
        self._find_bar.find_requested.connect(self._on_find_requested)
        self._find_bar.closed.connect(self._on_find_closed)
        layout.addWidget(self._find_bar)

        self._splitter.addWidget(terminal_area)

        # Set initial sizes: sidebar 220px, terminal gets the rest
        self._splitter.setSizes([220, 680])
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)

        self.setCentralWidget(self._splitter)

    def _setup_connections(self):
        self._tab_manager.current_terminal_changed.connect(self._on_terminal_changed)
        self._tab_manager.tab_count_changed.connect(self._on_tab_count_changed)
        self._tab_manager.terminal_title_changed.connect(self._on_title_changed)
        self._settings.settings_changed.connect(self._on_settings_changed)

        # SSH sidebar signals
        self._ssh_sidebar.connect_requested.connect(self._ssh_connect_session)
        self._ssh_sidebar.quick_connect_requested.connect(self._ssh_quick_connect)
        self._ssh_sidebar.edit_session_requested.connect(self._ssh_edit_session)
        self._ssh_sidebar.edit_group_requested.connect(self._ssh_edit_group)
        self._ssh_sidebar.delete_session_requested.connect(self._ssh_delete_session)
        self._ssh_sidebar.delete_group_requested.connect(self._ssh_delete_group)
        self._ssh_sidebar.new_session_requested.connect(self._ssh_show_new_session)
        self._ssh_sidebar.new_group_requested.connect(self._ssh_show_new_group)

    # --- Actions ---

    def _create_actions(self):
        # File actions
        self._new_tab_action = self._make_action("New Tab", "Ctrl+Shift+T", self._new_tab)
        self._close_tab_action = self._make_action("Close Tab", "Ctrl+Shift+W", self._close_tab)
        self._ssh_connect_action = self._make_action("SSH Connect...", "Ctrl+Shift+S", self._ssh_show_new_session)
        self._ssh_import_action = self._make_action("Import SSH Config...", None, self._ssh_import_config)
        self._ssh_import_remmina_action = self._make_action("Import from Remmina...", None, self._ssh_import_remmina)
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
        self._ssh_panel_action = self._make_action("SSH Sessions Panel", "Ctrl+Shift+P", self._toggle_ssh_panel)
        self._ssh_panel_action.setCheckable(True)
        self._ssh_panel_action.setChecked(True)

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
        file_menu.addAction(self._ssh_connect_action)
        file_menu.addAction(self._ssh_import_action)
        file_menu.addAction(self._ssh_import_remmina_action)
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
        view_menu.addAction(self._ssh_panel_action)
        view_menu.addSeparator()
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
        check_updates_action = help_menu.addAction("Check for Updates...")
        check_updates_action.triggered.connect(self._manual_check_updates)
        help_menu.addSeparator()
        about_action = help_menu.addAction("About SOSterm")
        about_action.triggered.connect(self._show_about)

    # --- Toolbar ---

    def _create_toolbar(self):
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)

        toolbar.addAction(self._new_tab_action)
        toolbar.addAction(self._ssh_connect_action)
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

        self._ssh_info_label = QLabel("")
        self._ssh_info_label.setMinimumWidth(100)
        self._statusbar.addPermanentWidget(self._ssh_info_label)

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
            self._ssh_info_label.setText("")
            return

        self._dims_label.setText(f"{terminal.cols}x{terminal.rows}")
        shell = self._settings.get_shell()
        self._shell_label.setText(os.path.basename(shell))
        self._cwd_label.setText(terminal.get_cwd())

        # SSH info
        ssh_id = terminal.get_ssh_session_id()
        if ssh_id:
            session = self._ssh_store.get_session(ssh_id)
            if session:
                label = "SSH: "
                if session.username:
                    label += f"{session.username}@"
                label += session.host
                self._ssh_info_label.setText(label)
            else:
                self._ssh_info_label.setText("SSH")
        else:
            self._ssh_info_label.setText("")

    # --- Signal handlers ---

    def _on_terminal_changed(self, terminal):
        self._update_statusbar()
        if terminal:
            title = terminal.get_title()
            if title:
                self.setWindowTitle(f"{title} - SOSterm")
            else:
                self.setWindowTitle("SOSterm")
        else:
            self.setWindowTitle("SOSterm")

    def _on_title_changed(self, title):
        """Update window title when the active terminal's OSC title changes."""
        if title:
            self.setWindowTitle(f"{title} - SOSterm")

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

    def tab_count(self):
        """Public accessor for the number of open tabs."""
        return self._tab_manager.count()

    def new_tab(self, shell=None, cwd=None):
        """Public method to create a new tab."""
        return self._tab_manager.new_tab(shell=shell, cwd=cwd)

    def apply_theme(self):
        """Public method to apply the current theme."""
        self._apply_current_theme()

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
            terminal.clear_terminal()

    def _reset(self):
        terminal = self._tab_manager.current_terminal()
        if terminal:
            terminal.reset_terminal()

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

    # --- SSH panel ---

    def _toggle_ssh_panel(self):
        visible = not self._ssh_sidebar.isVisible()
        self._ssh_sidebar.setVisible(visible)
        self._ssh_panel_action.setChecked(visible)

    # --- SSH operations ---

    def _ssh_connect_session(self, session):
        """Open a new tab connected to the given SSH session."""
        self._tab_manager.new_ssh_tab(session)

    def _ssh_quick_connect(self, text):
        """Parse quick connect string and open SSH tab."""
        session = self._parse_quick_connect(text)
        if session:
            self._ssh_store.add_session(session)
            self._ssh_sidebar.refresh()
            self._tab_manager.new_ssh_tab(session)

    def _parse_quick_connect(self, text):
        """Parse 'user@host[:port]' into an SSHSession."""
        text = text.strip()
        if not text:
            return None

        username = ""
        host = text
        port = 22

        # Extract user@
        if "@" in host:
            username, host = host.split("@", 1)

        # Extract :port
        if ":" in host:
            parts = host.rsplit(":", 1)
            host = parts[0]
            try:
                port = int(parts[1])
            except ValueError:
                pass

        if not host:
            return None

        return SSHSession(
            host=host,
            port=port,
            username=username,
            auth_method="password",
        )

    def _ssh_show_new_session(self):
        """Show dialog to create a new SSH session."""
        dialog = SSHSessionDialog(self._ssh_store, parent=self)
        if dialog.exec_() == dialog.Accepted:
            session = dialog.get_session()
            self._ssh_sidebar.refresh()
            if session:
                self._ssh_connect_session(session)

    def _ssh_edit_session(self, session):
        """Show dialog to edit an existing SSH session."""
        dialog = SSHSessionDialog(self._ssh_store, session=session, parent=self)
        if dialog.exec_() == dialog.Accepted:
            self._ssh_sidebar.refresh()

    def _ssh_delete_session(self, session):
        """Delete an SSH session after confirmation."""
        reply = QMessageBox.question(
            self, "Delete Session",
            f"Delete SSH session '{session.display_name()}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._ssh_store.delete_session(session.id)
            self._ssh_sidebar.refresh()

    def _ssh_show_new_group(self):
        """Show dialog to create a new SSH group."""
        dialog = SSHGroupDialog(self._ssh_store, parent=self)
        if dialog.exec_() == dialog.Accepted:
            self._ssh_sidebar.refresh()

    def _ssh_edit_group(self, group):
        """Show dialog to edit an existing SSH group."""
        dialog = SSHGroupDialog(self._ssh_store, group=group, parent=self)
        if dialog.exec_() == dialog.Accepted:
            self._ssh_sidebar.refresh()

    def _ssh_delete_group(self, group):
        """Delete an SSH group after confirmation."""
        reply = QMessageBox.question(
            self, "Delete Group",
            f"Delete group '{group.name}'? Sessions will be moved to ungrouped.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._ssh_store.delete_group(group.id)
            self._ssh_sidebar.refresh()

    def _ssh_import_config(self):
        """Import sessions from ~/.ssh/config."""
        candidates = self._ssh_store.import_ssh_config()
        if not candidates:
            QMessageBox.information(
                self, "Import SSH Config",
                "No new sessions found in ~/.ssh/config.",
            )
            return

        dialog = SSHImportDialog(candidates, parent=self)
        if dialog.exec_() == dialog.Accepted:
            selected = dialog.get_selected()
            for session in selected:
                self._ssh_store.add_session(session)
            self._ssh_sidebar.refresh()
            if selected:
                QMessageBox.information(
                    self, "Import SSH Config",
                    f"Imported {len(selected)} session(s).",
                )

    def _ssh_import_remmina(self):
        """Import SSH sessions from Remmina."""
        candidates = self._ssh_store.import_remmina()
        if not candidates:
            QMessageBox.information(
                self, "Import from Remmina",
                "No new SSH sessions found in Remmina.",
            )
            return

        dialog = SSHImportDialog(candidates, parent=self,
                                 title="Import from Remmina",
                                 label="Select SSH sessions to import from Remmina:")
        if dialog.exec_() == dialog.Accepted:
            selected = dialog.get_selected()
            # Create groups from Remmina group names
            group_map = {}  # group_name -> group_id
            for session in selected:
                gname = getattr(session, "_remmina_group", "")
                if gname and gname not in group_map:
                    # Check if group already exists
                    existing = [g for g in self._ssh_store.groups() if g.name == gname]
                    if existing:
                        group_map[gname] = existing[0].id
                    else:
                        from ssh_session_store import SSHGroup
                        group = SSHGroup(name=gname)
                        self._ssh_store.add_group(group)
                        group_map[gname] = group.id

            for session in selected:
                gname = getattr(session, "_remmina_group", "")
                if gname and gname in group_map:
                    session.group_id = group_map[gname]
                self._ssh_store.add_session(session)

            self._ssh_sidebar.refresh()
            if selected:
                QMessageBox.information(
                    self, "Import from Remmina",
                    f"Imported {len(selected)} session(s).",
                )

    # --- Update checking ---

    def _auto_check_updates(self):
        """Silently check for updates on startup (respects 24h cooldown)."""
        self._update_checker.auto_check(
            on_update=self._on_update_available,
        )

    def _manual_check_updates(self):
        """User-triggered update check (always checks, shows result)."""
        self._statusbar.showMessage("Checking for updates...", 5000)
        self._update_checker.check(
            on_update=self._on_update_available,
            on_finished=self._on_manual_check_finished,
            record_time=True,
        )

    def _on_update_available(self, version, download_url, changelog):
        """Show update notification."""
        msg = (
            f"<h3>SOSterm {version} is available</h3>"
            f"<p>You are running v{self._version}.</p>"
        )
        if changelog:
            msg += f"<p><b>What's new:</b> {changelog}</p>"
        if download_url:
            msg += (
                f'<p>Download: <a href="{download_url}">{download_url}</a></p>'
                "<p>After downloading, extract and run <code>sudo ./install.sh</code></p>"
            )
        else:
            msg += "<p>Visit <a href=\"https://github.com/frankkahle/SOSterm\">GitHub</a> to download.</p>"
        QMessageBox.information(self, "Update Available", msg)

    def _on_manual_check_finished(self, had_update):
        """Show 'up to date' message if no update was found (manual check only)."""
        if not had_update:
            self._statusbar.showMessage(f"SOSterm v{self._version} is up to date.", 5000)

    # --- Tools ---

    def _show_preferences(self):
        dialog = PreferencesDialog(self._settings, self)
        dialog.exec_()

    def _show_about(self):
        QMessageBox.about(
            self,
            "About SOSterm",
            f"<h2>SOSterm v{self._version}</h2>"
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
            terminal.set_padding(padding)

    # --- Window state ---

    def _restore_geometry(self):
        geo = self._settings.get("window_geometry")
        state = self._settings.get("window_state")
        if geo:
            from PyQt5.QtCore import QByteArray
            try:
                self.restoreGeometry(QByteArray(base64.b64decode(geo)))
            except Exception as e:
                print(f"SOSterm: failed to restore window geometry: {e}", file=sys.stderr)
        if state:
            from PyQt5.QtCore import QByteArray
            try:
                self.restoreState(QByteArray(base64.b64decode(state)))
            except Exception as e:
                print(f"SOSterm: failed to restore window state: {e}", file=sys.stderr)
        # Ensure the window isn't placed off-screen or behind a desktop panel
        screen = QApplication.primaryScreen()
        if screen:
            available = screen.availableGeometry()
            frame = self.frameGeometry()
            if frame.top() < available.top():
                self.move(frame.left(), available.top())
            if frame.left() < available.left():
                self.move(available.left(), self.y())

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
        # Save expanded state of SSH sidebar groups
        self._ssh_sidebar.save_expanded_state()

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
                    "Close SOSterm",
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
