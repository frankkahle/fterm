"""SSH session sidebar panel for fterm."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QMenu, QLabel, QSizePolicy,
)

from ssh_session_store import SSHSessionStore, SSHSession, SSHGroup


class SSHSidebarPanel(QWidget):
    """Sidebar panel showing SSH session directory."""

    connect_requested = pyqtSignal(object)        # SSHSession
    quick_connect_requested = pyqtSignal(str)      # "user@host[:port]"
    edit_session_requested = pyqtSignal(object)    # SSHSession
    edit_group_requested = pyqtSignal(object)      # SSHGroup
    delete_session_requested = pyqtSignal(object)  # SSHSession
    delete_group_requested = pyqtSignal(object)    # SSHGroup
    new_session_requested = pyqtSignal()
    new_group_requested = pyqtSignal()

    def __init__(self, store: SSHSessionStore, parent=None):
        super().__init__(parent)
        self._store = store

        self.setMinimumWidth(180)
        self.setMaximumWidth(350)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header
        header = QLabel("SSH Sessions")
        header.setStyleSheet("font-weight: bold; padding: 2px;")
        layout.addWidget(header)

        # Quick connect bar
        qc_layout = QHBoxLayout()
        qc_layout.setSpacing(2)
        self._quick_edit = QLineEdit()
        self._quick_edit.setPlaceholderText("user@host[:port]")
        self._quick_edit.returnPressed.connect(self._on_quick_connect)
        qc_layout.addWidget(self._quick_edit)
        qc_btn = QPushButton("Connect")
        qc_btn.setFixedWidth(60)
        qc_btn.clicked.connect(self._on_quick_connect)
        qc_layout.addWidget(qc_btn)
        layout.addLayout(qc_layout)

        # Tree widget
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setRootIsDecorated(True)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._context_menu)
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._tree.itemActivated.connect(self._on_item_activated)
        layout.addWidget(self._tree, 1)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)
        new_session_btn = QPushButton("+ Session")
        new_session_btn.clicked.connect(self.new_session_requested)
        btn_layout.addWidget(new_session_btn)
        new_group_btn = QPushButton("+ Group")
        new_group_btn.clicked.connect(self.new_group_requested)
        btn_layout.addWidget(new_group_btn)
        layout.addLayout(btn_layout)

    def refresh(self):
        """Rebuild the tree from the store."""
        self._tree.clear()

        # Add groups
        for group in self._store.groups():
            group_item = QTreeWidgetItem(self._tree)
            group_item.setText(0, group.name)
            group_item.setData(0, Qt.UserRole, ("group", group.id))
            if group.color:
                group_item.setForeground(0, QColor(group.color))
            group_item.setExpanded(group.expanded)

            # Sessions in this group
            for session in self._store.sessions_in_group(group.id):
                sess_item = QTreeWidgetItem(group_item)
                sess_item.setText(0, session.display_name())
                sess_item.setData(0, Qt.UserRole, ("session", session.id))
                if session.color:
                    sess_item.setForeground(0, QColor(session.color))

        # Ungrouped sessions
        for session in self._store.ungrouped_sessions():
            sess_item = QTreeWidgetItem(self._tree)
            sess_item.setText(0, session.display_name())
            sess_item.setData(0, Qt.UserRole, ("session", session.id))
            if session.color:
                sess_item.setForeground(0, QColor(session.color))

    def _get_item_data(self, item):
        """Return (type, id) tuple from a tree item."""
        if item is None:
            return None, None
        data = item.data(0, Qt.UserRole)
        if data:
            return data
        return None, None

    def _on_quick_connect(self):
        text = self._quick_edit.text().strip()
        if text:
            self.quick_connect_requested.emit(text)
            self._quick_edit.clear()

    def _on_item_double_clicked(self, item, column):
        kind, item_id = self._get_item_data(item)
        if kind == "session":
            session = self._store.get_session(item_id)
            if session:
                self.connect_requested.emit(session)

    def _on_item_activated(self, item, column):
        # Enter key on a session item
        kind, item_id = self._get_item_data(item)
        if kind == "session":
            session = self._store.get_session(item_id)
            if session:
                self.connect_requested.emit(session)

    def _context_menu(self, pos):
        item = self._tree.itemAt(pos)
        menu = QMenu(self)

        if item:
            kind, item_id = self._get_item_data(item)
            if kind == "session":
                session = self._store.get_session(item_id)
                if session:
                    connect_act = menu.addAction("Connect")
                    connect_act.triggered.connect(
                        lambda: self.connect_requested.emit(session))
                    edit_act = menu.addAction("Edit")
                    edit_act.triggered.connect(
                        lambda: self.edit_session_requested.emit(session))
                    delete_act = menu.addAction("Delete")
                    delete_act.triggered.connect(
                        lambda: self.delete_session_requested.emit(session))
                    menu.addSeparator()

            elif kind == "group":
                group = self._store.get_group(item_id)
                if group:
                    edit_act = menu.addAction("Edit Group")
                    edit_act.triggered.connect(
                        lambda: self.edit_group_requested.emit(group))
                    delete_act = menu.addAction("Delete Group")
                    delete_act.triggered.connect(
                        lambda: self.delete_group_requested.emit(group))
                    menu.addSeparator()

        new_session_act = menu.addAction("New Session...")
        new_session_act.triggered.connect(self.new_session_requested)
        new_group_act = menu.addAction("New Group...")
        new_group_act.triggered.connect(self.new_group_requested)

        menu.exec_(self._tree.viewport().mapToGlobal(pos))

    def save_expanded_state(self):
        """Persist expanded/collapsed state of groups back to the store."""
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            kind, item_id = self._get_item_data(item)
            if kind == "group":
                group = self._store.get_group(item_id)
                if group:
                    group.expanded = item.isExpanded()
        self._store.save()
