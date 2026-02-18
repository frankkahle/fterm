"""Find bar widget for searching terminal scrollback."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel,
)
from PyQt5.QtGui import QKeySequence


class FindBar(QWidget):
    """Inline search bar for terminal scrollback."""

    find_requested = pyqtSignal(str, bool)  # query, forward
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Find...")
        self._search_edit.returnPressed.connect(self._find_next)
        self._search_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._search_edit, 1)

        self._prev_btn = QPushButton("Prev")
        self._prev_btn.setFixedWidth(50)
        self._prev_btn.clicked.connect(self._find_prev)
        layout.addWidget(self._prev_btn)

        self._next_btn = QPushButton("Next")
        self._next_btn.setFixedWidth(50)
        self._next_btn.clicked.connect(self._find_next)
        layout.addWidget(self._next_btn)

        self._match_label = QLabel("")
        self._match_label.setMinimumWidth(60)
        layout.addWidget(self._match_label)

        self._close_btn = QPushButton("X")
        self._close_btn.setFixedWidth(28)
        self._close_btn.clicked.connect(self.hide_bar)
        layout.addWidget(self._close_btn)

    def show_bar(self):
        """Show and focus the find bar."""
        self.setVisible(True)
        self._search_edit.setFocus()
        self._search_edit.selectAll()

    def hide_bar(self):
        """Hide the find bar and return focus to terminal."""
        self.setVisible(False)
        self.closed.emit()

    def set_match_info(self, current, total):
        """Update the match count label."""
        if total > 0:
            self._match_label.setText(f"{current}/{total}")
        else:
            self._match_label.setText("No matches")

    def get_query(self):
        return self._search_edit.text()

    def _find_next(self):
        query = self._search_edit.text()
        if query:
            self.find_requested.emit(query, True)

    def _find_prev(self):
        query = self._search_edit.text()
        if query:
            self.find_requested.emit(query, False)

    def _on_text_changed(self, text):
        if text:
            self.find_requested.emit(text, True)
        else:
            self._match_label.setText("")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide_bar()
        else:
            super().keyPressEvent(event)
