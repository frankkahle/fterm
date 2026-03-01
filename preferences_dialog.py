"""Preferences dialog for fterm settings."""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QComboBox, QSpinBox, QCheckBox, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QFontComboBox,
    QDialogButtonBox,
)
from themes import get_theme_names


class PreferencesDialog(QDialog):
    """Settings dialog with tabbed interface."""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("Preferences")
        self.setMinimumSize(450, 400)

        layout = QVBoxLayout(self)

        # Tab widget
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        self._setup_general_tab()
        self._setup_appearance_tab()
        self._setup_session_tab()

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Apply).clicked.connect(self._apply)
        layout.addWidget(buttons)

    def _setup_general_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Shell group
        shell_group = QGroupBox("Shell")
        shell_layout = QFormLayout(shell_group)

        self._shell_edit = QLineEdit()
        self._shell_edit.setPlaceholderText("Leave empty for default ($SHELL)")
        self._shell_edit.setText(self._settings.get("shell", ""))
        shell_layout.addRow("Shell command:", self._shell_edit)

        layout.addWidget(shell_group)

        # Behavior group
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout(behavior_group)

        self._scrollback_spin = QSpinBox()
        self._scrollback_spin.setRange(100, 100000)
        self._scrollback_spin.setSingleStep(1000)
        self._scrollback_spin.setValue(self._settings.get("scrollback_lines", 10000))

        scroll_layout = QHBoxLayout()
        scroll_layout.addWidget(QLabel("Scrollback lines:"))
        scroll_layout.addWidget(self._scrollback_spin)
        behavior_layout.addLayout(scroll_layout)

        self._confirm_close_check = QCheckBox("Confirm close when processes are running")
        self._confirm_close_check.setChecked(self._settings.get("confirm_close_running", True))
        behavior_layout.addWidget(self._confirm_close_check)

        layout.addWidget(behavior_group)
        layout.addStretch()

        self._tabs.addTab(tab, "General")

    def _setup_appearance_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Theme group
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout(theme_group)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(get_theme_names())
        current_theme = self._settings.get("theme", "Dark")
        idx = self._theme_combo.findText(current_theme)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)
        theme_layout.addRow("Color theme:", self._theme_combo)

        layout.addWidget(theme_group)

        # Font group
        font_group = QGroupBox("Font")
        font_layout = QFormLayout(font_group)

        self._font_combo = QFontComboBox()
        self._font_combo.setCurrentFont(
            QFont(self._settings.get("font_family", "Monospace"))
        )
        font_layout.addRow("Font family:", self._font_combo)

        self._font_size_spin = QSpinBox()
        self._font_size_spin.setRange(6, 72)
        self._font_size_spin.setValue(self._settings.get("font_size", 11))
        font_layout.addRow("Font size:", self._font_size_spin)

        layout.addWidget(font_group)

        # Cursor group
        cursor_group = QGroupBox("Cursor")
        cursor_layout = QFormLayout(cursor_group)

        self._cursor_style_combo = QComboBox()
        self._cursor_style_combo.addItems(["block", "underline", "bar"])
        current_style = self._settings.get("cursor_style", "block")
        idx = self._cursor_style_combo.findText(current_style)
        if idx >= 0:
            self._cursor_style_combo.setCurrentIndex(idx)
        cursor_layout.addRow("Cursor style:", self._cursor_style_combo)

        self._cursor_blink_check = QCheckBox("Blink cursor")
        self._cursor_blink_check.setChecked(self._settings.get("cursor_blink", True))
        cursor_layout.addRow(self._cursor_blink_check)

        layout.addWidget(cursor_group)

        # Padding group
        padding_group = QGroupBox("Terminal")
        padding_layout = QFormLayout(padding_group)

        self._padding_spin = QSpinBox()
        self._padding_spin.setRange(0, 32)
        self._padding_spin.setSingleStep(2)
        self._padding_spin.setValue(self._settings.get("terminal_padding", 4))
        padding_layout.addRow("Padding (px):", self._padding_spin)

        layout.addWidget(padding_group)
        layout.addStretch()

        self._tabs.addTab(tab, "Appearance")

    def _setup_session_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        session_group = QGroupBox("Session")
        session_layout = QVBoxLayout(session_group)

        self._auto_save_check = QCheckBox("Auto-save session on exit")
        self._auto_save_check.setChecked(self._settings.get("auto_save_session", True))
        session_layout.addWidget(self._auto_save_check)

        self._restore_check = QCheckBox("Restore previous session on startup")
        self._restore_check.setChecked(self._settings.get("restore_session", True))
        session_layout.addWidget(self._restore_check)

        layout.addWidget(session_group)
        layout.addStretch()

        self._tabs.addTab(tab, "Session")

    def _apply(self):
        """Apply settings without closing."""
        self._settings.set("shell", self._shell_edit.text())
        self._settings.set("scrollback_lines", self._scrollback_spin.value())
        self._settings.set("confirm_close_running", self._confirm_close_check.isChecked())
        self._settings.set("theme", self._theme_combo.currentText())
        self._settings.set("font_family", self._font_combo.currentFont().family())
        self._settings.set("font_size", self._font_size_spin.value())
        self._settings.set("cursor_style", self._cursor_style_combo.currentText())
        self._settings.set("cursor_blink", self._cursor_blink_check.isChecked())
        self._settings.set("terminal_padding", self._padding_spin.value())
        self._settings.set("auto_save_session", self._auto_save_check.isChecked())
        self._settings.set("restore_session", self._restore_check.isChecked())

    def _accept(self):
        """Apply and close."""
        self._apply()
        self.accept()
