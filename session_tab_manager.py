"""Tab widget managing multiple terminal sessions for fterm."""

import os
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QTabWidget, QMenu, QApplication,
)
from terminal_widget import TerminalWidget


class SessionTabManager(QTabWidget):
    """Tab widget that manages multiple terminal tabs."""

    current_terminal_changed = pyqtSignal(object)  # TerminalWidget or None
    tab_count_changed = pyqtSignal(int)
    terminal_title_changed = pyqtSignal(str)  # OSC title from active terminal

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._tab_counter = 0

        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)

        # Tab bar context menu
        self.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabBar().customContextMenuRequested.connect(self._tab_context_menu)

        # Signals
        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self._on_current_changed)

    def current_terminal(self):
        """Return the currently active TerminalWidget."""
        return self.currentWidget()

    def _on_current_changed(self, index):
        terminal = self.widget(index)
        self.current_terminal_changed.emit(terminal)

    # --- Tab operations ---

    def new_tab(self, shell=None, cwd=None):
        """Create a new terminal tab."""
        terminal = TerminalWidget(settings=self._settings, parent=self)

        # Connect title change signal
        terminal.title_changed.connect(
            lambda title, t=terminal: self._on_title_changed(t, title)
        )
        terminal.process_exited.connect(
            lambda status, t=terminal: self._on_process_exited(t, status)
        )

        self._tab_counter += 1
        title = f"Term {self._tab_counter}"
        index = self.addTab(terminal, title)
        self.setCurrentIndex(index)

        # Start the shell process
        terminal.start_process(shell=shell, cwd=cwd)
        terminal.setFocus()

        self.tab_count_changed.emit(self.count())
        return terminal

    def close_tab(self, index=None):
        """Close a tab and terminate its process."""
        if index is None:
            index = self.currentIndex()
        if index < 0 or index >= self.count():
            return False

        terminal = self.widget(index)
        terminal.terminate()
        self.removeTab(index)
        terminal.deleteLater()
        self.tab_count_changed.emit(self.count())
        return True

    def close_all_tabs(self):
        """Close all tabs."""
        while self.count() > 0:
            self.close_tab(0)

    def close_other_tabs(self, index):
        """Close all tabs except the specified one."""
        i = self.count() - 1
        while i >= 0:
            if i != index:
                self.close_tab(i)
                if index > i:
                    index -= 1
            i -= 1

    def _on_title_changed(self, terminal, title):
        """Store the OSC title as tooltip; propagate to window if active tab."""
        index = self.indexOf(terminal)
        if index >= 0 and title:
            self.setTabToolTip(index, title)
            # If this is the active tab, update window title
            if index == self.currentIndex():
                self.terminal_title_changed.emit(title)

    def _on_process_exited(self, terminal, status):
        """Auto-close the tab when its shell exits."""
        index = self.indexOf(terminal)
        if index >= 0:
            self.close_tab(index)

    def _tab_context_menu(self, pos):
        """Show context menu for tab bar."""
        index = self.tabBar().tabAt(pos)
        if index < 0:
            return

        menu = QMenu(self)

        close_action = menu.addAction("Close")
        close_action.triggered.connect(lambda: self.close_tab(index))

        close_others = menu.addAction("Close Others")
        close_others.triggered.connect(lambda: self.close_other_tabs(index))

        close_all = menu.addAction("Close All")
        close_all.triggered.connect(self.close_all_tabs)

        menu.addSeparator()

        terminal = self.widget(index)
        if terminal:
            cwd = terminal.get_cwd()
            copy_cwd = menu.addAction("Copy Working Directory")
            copy_cwd.triggered.connect(
                lambda: QApplication.clipboard().setText(cwd)
            )

        menu.exec_(self.tabBar().mapToGlobal(pos))

    # --- Session support ---

    def get_session_data(self):
        """Return session data for all open tabs."""
        tabs = []
        for i in range(self.count()):
            terminal = self.widget(i)
            tabs.append(terminal.get_session_data())
        return {
            "tabs": tabs,
            "active_index": self.currentIndex(),
        }

    def restore_session_data(self, data):
        """Restore tabs from session data."""
        for tab_data in data.get("tabs", []):
            cwd = tab_data.get("cwd")
            if cwd and os.path.isdir(cwd):
                self.new_tab(cwd=cwd)
            else:
                self.new_tab()

        active = data.get("active_index", 0)
        if 0 <= active < self.count():
            self.setCurrentIndex(active)
