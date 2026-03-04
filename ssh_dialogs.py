"""SSH session and group editor dialogs for fterm."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QComboBox, QPushButton, QLabel,
    QFileDialog, QListWidget, QListWidgetItem, QDialogButtonBox,
    QColorDialog,
)

from ssh_session_store import SSHSession, SSHGroup


class SSHSessionDialog(QDialog):
    """Dialog for creating/editing an SSH session."""

    def __init__(self, store, session=None, parent=None):
        super().__init__(parent)
        self._store = store
        self._session = session
        self._editing = session is not None

        self.setWindowTitle("Edit SSH Session" if self._editing else "New SSH Session")
        self.setMinimumWidth(400)
        self._setup_ui()

        if self._editing:
            self._populate(session)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Optional display name")
        form.addRow("Name:", self._name_edit)

        self._host_edit = QLineEdit()
        self._host_edit.setPlaceholderText("hostname or IP")
        form.addRow("Host:", self._host_edit)

        self._port_spin = QSpinBox()
        self._port_spin.setRange(1, 65535)
        self._port_spin.setValue(22)
        form.addRow("Port:", self._port_spin)

        self._user_edit = QLineEdit()
        self._user_edit.setPlaceholderText("username")
        form.addRow("Username:", self._user_edit)

        self._auth_combo = QComboBox()
        self._auth_combo.addItems(["key", "password"])
        self._auth_combo.currentTextChanged.connect(self._on_auth_changed)
        form.addRow("Auth Method:", self._auth_combo)

        # Identity file row
        id_layout = QHBoxLayout()
        self._identity_edit = QLineEdit()
        self._identity_edit.setPlaceholderText("~/.ssh/id_rsa")
        id_layout.addWidget(self._identity_edit)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_identity)
        id_layout.addWidget(browse_btn)
        form.addRow("Identity File:", id_layout)

        self._startup_edit = QLineEdit()
        self._startup_edit.setPlaceholderText("Optional command to run on connect")
        form.addRow("Startup Cmd:", self._startup_edit)

        self._group_combo = QComboBox()
        self._group_combo.addItem("(None)", "")
        for group in self._store.groups():
            self._group_combo.addItem(group.name, group.id)
        form.addRow("Group:", self._group_combo)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate(self, session):
        self._name_edit.setText(session.name)
        self._host_edit.setText(session.host)
        self._port_spin.setValue(session.port)
        self._user_edit.setText(session.username)
        idx = self._auth_combo.findText(session.auth_method)
        if idx >= 0:
            self._auth_combo.setCurrentIndex(idx)
        self._identity_edit.setText(session.identity_file)
        self._startup_edit.setText(session.startup_command)
        # Select group
        gidx = self._group_combo.findData(session.group_id)
        if gidx >= 0:
            self._group_combo.setCurrentIndex(gidx)

    def _on_auth_changed(self, method):
        self._identity_edit.setEnabled(method == "key")

    def _browse_identity(self):
        import os
        start_dir = os.path.expanduser("~/.ssh")
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Identity File", start_dir, "All Files (*)"
        )
        if path:
            # Use ~ shorthand if possible
            home = os.path.expanduser("~")
            if path.startswith(home):
                path = "~" + path[len(home):]
            self._identity_edit.setText(path)

    def _on_accept(self):
        host = self._host_edit.text().strip()
        if not host:
            self._host_edit.setFocus()
            return

        if self._editing:
            session = self._session
        else:
            session = SSHSession()

        session.name = self._name_edit.text().strip()
        session.host = host
        session.port = self._port_spin.value()
        session.username = self._user_edit.text().strip()
        session.auth_method = self._auth_combo.currentText()
        session.identity_file = self._identity_edit.text().strip()
        session.startup_command = self._startup_edit.text().strip()
        session.group_id = self._group_combo.currentData() or ""

        if self._editing:
            self._store.update_session(session)
        else:
            self._store.add_session(session)

        self._result_session = session
        self.accept()

    def get_session(self):
        return getattr(self, "_result_session", None)


class SSHGroupDialog(QDialog):
    """Dialog for creating/editing an SSH group."""

    def __init__(self, store, group=None, parent=None):
        super().__init__(parent)
        self._store = store
        self._group = group
        self._editing = group is not None
        self._selected_color = group.color if group else ""

        self.setWindowTitle("Edit Group" if self._editing else "New Group")
        self.setMinimumWidth(300)
        self._setup_ui()

        if self._editing:
            self._name_edit.setText(group.name)
            if group.color:
                self._update_color_preview(group.color)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Group name")
        form.addRow("Name:", self._name_edit)

        color_layout = QHBoxLayout()
        self._color_preview = QLabel("  ")
        self._color_preview.setFixedSize(24, 24)
        self._color_preview.setStyleSheet("background-color: transparent; border: 1px solid gray;")
        color_layout.addWidget(self._color_preview)
        color_btn = QPushButton("Pick Color...")
        color_btn.clicked.connect(self._pick_color)
        color_layout.addWidget(color_btn)
        color_layout.addStretch()
        form.addRow("Color:", color_layout)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _pick_color(self):
        from PyQt5.QtGui import QColor
        initial = QColor(self._selected_color) if self._selected_color else QColor(Qt.white)
        color = QColorDialog.getColor(initial, self, "Pick Group Color")
        if color.isValid():
            self._selected_color = color.name()
            self._update_color_preview(self._selected_color)

    def _update_color_preview(self, color):
        self._color_preview.setStyleSheet(
            f"background-color: {color}; border: 1px solid gray;"
        )

    def _on_accept(self):
        name = self._name_edit.text().strip()
        if not name:
            self._name_edit.setFocus()
            return

        if self._editing:
            group = self._group
        else:
            group = SSHGroup()

        group.name = name
        group.color = self._selected_color

        if self._editing:
            self._store.update_group(group)
        else:
            self._store.add_group(group)

        self._result_group = group
        self.accept()

    def get_group(self):
        return getattr(self, "_result_group", None)


class SSHImportDialog(QDialog):
    """Dialog for importing sessions from ~/.ssh/config or Remmina."""

    def __init__(self, candidates, parent=None, title=None, label=None):
        super().__init__(parent)
        self._candidates = candidates
        self._title = title or "Import SSH Config"
        self._label = label or "Select sessions to import from ~/.ssh/config:"

        self.setWindowTitle(self._title)
        self.setMinimumWidth(450)
        self.setMinimumHeight(350)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(self._label))

        self._list = QListWidget()
        for candidate in self._candidates:
            item = QListWidgetItem(candidate.display_name())
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self._list.addItem(item)
        layout.addWidget(self._list)

        # Select/Deselect buttons
        sel_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all)
        sel_layout.addWidget(select_all_btn)
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self._deselect_all)
        sel_layout.addWidget(deselect_all_btn)
        sel_layout.addStretch()
        layout.addLayout(sel_layout)

        # Import / Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Import")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _select_all(self):
        for i in range(self._list.count()):
            self._list.item(i).setCheckState(Qt.Checked)

    def _deselect_all(self):
        for i in range(self._list.count()):
            self._list.item(i).setCheckState(Qt.Unchecked)

    def get_selected(self):
        """Return the list of selected candidate sessions."""
        selected = []
        for i in range(self._list.count()):
            if self._list.item(i).checkState() == Qt.Checked:
                selected.append(self._candidates[i])
        return selected
