"""Core terminal widget: renders terminal grid, handles input."""

import re
import pyte
import pyte.modes as modes
from wcwidth import wcwidth
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint, QRect, QUrl
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QFontMetrics, QFontDatabase,
    QKeySequence, QClipboard, QPen, QBrush, QCursor, QDesktopServices,
)
from PyQt5.QtWidgets import QWidget, QApplication, QMenu, QAction, QScrollBar, QHBoxLayout

from terminal_process import TerminalProcess
from themes import get_theme, get_ansi_palette, get_xterm_256_color

# URL regex for clickable link detection
_URL_RE = re.compile(
    r'https?://[^\s<>\'")\]}>]+|'
    r'www\.[^\s<>\'")\]}>]+'
)


# Map pyte color names to ANSI indices
_ANSI_COLOR_NAMES = {
    "black": 0, "red": 1, "green": 2, "brown": 3, "yellow": 3,
    "blue": 4, "magenta": 5, "cyan": 6, "white": 7,
    "brightblack": 8, "brightred": 9, "brightgreen": 10,
    "brightbrown": 11, "brightyellow": 11,
    "brightblue": 12, "brightmagenta": 13, "brightcyan": 14,
    "brightwhite": 15,
}


class TerminalScreen(pyte.HistoryScreen):
    """Extended pyte screen with alt-screen buffer and title/bell support."""

    def __init__(self, columns, lines, history=10000):
        super().__init__(columns, lines, history=history)
        self._alt_buffer = None
        self._alt_cursor = None
        self._alt_mode = False
        self.title = ""
        self.icon_name = ""
        self._title_changed_callback = None
        self._bell_callback = None
        self._write_callback = None  # write back to PTY for query responses

    def set_write_callback(self, callback):
        """Set callback to write data back to the PTY (for DSR/DA responses)."""
        self._write_callback = callback

    def write_process_input(self, data):
        """Override pyte noop: actually write responses back to the PTY.

        Called by pyte when the child process sends terminal queries
        like DSR (ESC[6n) or DA (ESC[c) that expect a response.
        """
        if self._write_callback and data:
            self._write_callback(data.encode("utf-8") if isinstance(data, str) else data)

    def set_title_callback(self, callback):
        self._title_changed_callback = callback

    def set_bell_callback(self, callback):
        self._bell_callback = callback

    def set_title(self, param):
        self.title = param
        if self._title_changed_callback:
            self._title_changed_callback(param)

    def set_icon_name(self, param):
        self.icon_name = param

    def bell(self):
        if self._bell_callback:
            self._bell_callback()

    def set_mode(self, *mds, **kwargs):
        """Intercept alt-screen mode switches."""
        for mode in mds:
            if mode in (47, 1047, 1049):
                self._enter_alt_screen(save_cursor=(mode == 1049))
        super().set_mode(*mds, **kwargs)

    def reset_mode(self, *mds, **kwargs):
        """Intercept alt-screen mode resets."""
        for mode in mds:
            if mode in (47, 1047, 1049):
                self._exit_alt_screen(restore_cursor=(mode == 1049))
        super().reset_mode(*mds, **kwargs)

    def _enter_alt_screen(self, save_cursor=True):
        if self._alt_mode:
            return
        self._alt_mode = True
        # Save main buffer
        self._alt_buffer = {}
        for line_no in self.buffer:
            self._alt_buffer[line_no] = dict(self.buffer[line_no])
        if save_cursor:
            self._alt_cursor = self.cursor
        # Clear alt screen
        self.erase_in_display(2)

    def _exit_alt_screen(self, restore_cursor=True):
        if not self._alt_mode:
            return
        self._alt_mode = False
        # Restore main buffer
        if self._alt_buffer is not None:
            self.buffer.clear()
            for line_no, line_data in self._alt_buffer.items():
                self.buffer[line_no] = line_data
            self._alt_buffer = None
        if restore_cursor and self._alt_cursor is not None:
            self.cursor = self._alt_cursor
            self._alt_cursor = None

    @property
    def in_alt_screen(self):
        return self._alt_mode


class TerminalWidget(QWidget):
    """Custom widget that renders a terminal grid with QPainter."""

    title_changed = pyqtSignal(str)
    process_exited = pyqtSignal(int)

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self._settings = settings

        # Terminal state
        self._rows = 24
        self._cols = 80
        self._scrollback_offset = 0
        self._padding = settings.get("terminal_padding", 4) if settings else 4

        # Theme/appearance
        theme_name = settings.get("theme", "Dark") if settings else "Dark"
        self._theme = get_theme(theme_name)
        self._setup_font()

        # pyte screen + stream
        scrollback = settings.get("scrollback_lines", 10000) if settings else 10000
        self._screen = TerminalScreen(self._cols, self._rows, history=scrollback)
        self._stream = pyte.ByteStream(self._screen)

        # Title / bell / write-back callbacks
        self._screen.set_title_callback(self._on_title_changed)
        self._screen.set_bell_callback(self._on_bell)

        # Process
        self._process = TerminalProcess(self)

        # Connect write-back so pyte can respond to terminal queries (DSR, DA)
        self._screen.set_write_callback(self._process.write)
        self._process.data_ready.connect(self._on_data_ready)
        self._process.process_exited.connect(self._on_process_exited)

        # Cursor blink timer
        self._cursor_visible = True
        self._cursor_timer = QTimer(self)
        blink = settings.get("cursor_blink", True) if settings else True
        if blink:
            self._cursor_timer.timeout.connect(self._toggle_cursor)
            self._cursor_timer.start(530)

        # Render coalescing: batch rapid PTY output into single repaints
        self._repaint_pending = False
        self._repaint_timer = QTimer(self)
        self._repaint_timer.setSingleShot(True)
        self._repaint_timer.setInterval(8)  # ~120 fps max
        self._repaint_timer.timeout.connect(self._flush_repaint)

        # Selection state — coordinates are display-row based (what's visible)
        self._selecting = False
        self._selection_start = None  # (display_row, col)
        self._selection_end = None
        self._double_click_word = False

        # Visual bell state
        self._bell_active = False
        self._bell_timer = QTimer(self)
        self._bell_timer.setSingleShot(True)
        self._bell_timer.timeout.connect(self._clear_bell)

        # Triple-click timer (distinguish double from triple click)
        self._click_count = 0
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.setInterval(400)
        self._click_timer.timeout.connect(self._reset_click_count)

        # URL hover state
        self._hovered_url = None  # (start_row, start_col, end_row, end_col, url_text)

        # URL detection cache (invalidated on new data)
        self._url_cache = None
        self._url_cache_valid = False

        # Widget setup
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAttribute(Qt.WA_InputMethodEnabled, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setMouseTracking(True)
        self.setMinimumSize(200, 100)

        # Scrollbar
        self._scrollbar = QScrollBar(Qt.Vertical, self)
        self._scrollbar.setVisible(False)
        self._scrollbar.valueChanged.connect(self._on_scrollbar_changed)

    # --- Font setup ---

    def _setup_font(self):
        family = self._settings.get("font_family", "Monospace") if self._settings else "Monospace"
        size = self._settings.get("font_size", 11) if self._settings else 11
        zoom = self._settings.get("zoom_level", 0) if self._settings else 0
        self._base_font_size = size
        self._zoom_level = zoom
        effective_size = max(6, size + zoom)
        self._font = QFont(family, effective_size)
        self._font.setStyleHint(QFont.Monospace)
        self._font.setFixedPitch(True)
        fm = QFontMetrics(self._font)
        self._cell_width = fm.horizontalAdvance("M")
        self._cell_height = fm.height()
        self._font_ascent = fm.ascent()
        if self._cell_width < 1:
            self._cell_width = 8
        if self._cell_height < 1:
            self._cell_height = 16
        # Pre-create font variants for bold/italic rendering
        self._font_bold = QFont(self._font)
        self._font_bold.setBold(True)
        self._font_italic = QFont(self._font)
        self._font_italic.setItalic(True)
        self._font_bold_italic = QFont(self._font)
        self._font_bold_italic.setBold(True)
        self._font_bold_italic.setItalic(True)

    def update_font(self, family=None, size=None):
        """Update font and recalculate grid."""
        if family:
            if self._settings:
                self._settings.set("font_family", family)
        if size is not None:
            self._base_font_size = size
            if self._settings:
                self._settings.set("font_size", size)
        self._setup_font()
        self._recalculate_grid()
        self.update()

    def zoom_in(self):
        self._zoom_level += 1
        if self._settings:
            self._settings.set("zoom_level", self._zoom_level)
        self._setup_font()
        self._recalculate_grid()
        self.update()

    def zoom_out(self):
        if self._base_font_size + self._zoom_level > 6:
            self._zoom_level -= 1
            if self._settings:
                self._settings.set("zoom_level", self._zoom_level)
            self._setup_font()
            self._recalculate_grid()
            self.update()

    def zoom_reset(self):
        self._zoom_level = 0
        if self._settings:
            self._settings.set("zoom_level", 0)
        self._setup_font()
        self._recalculate_grid()
        self.update()

    # --- Process lifecycle ---

    def start_process(self, shell=None, cwd=None):
        """Start the shell process."""
        if shell is None:
            shell = self._settings.get_shell() if self._settings else "/bin/bash"
        # Tell shells whether background is light or dark via COLORFGBG
        bg = QColor(self._theme.terminal_bg)
        is_light = (bg.red() * 299 + bg.green() * 587 + bg.blue() * 114) / 1000 > 128
        colorfgbg = "0;15" if is_light else "15;0"
        self._process.start(shell=shell, rows=self._rows, cols=self._cols,
                            cwd=cwd, colorfgbg=colorfgbg)

    def get_process(self):
        return self._process

    @property
    def cols(self):
        return self._cols

    @property
    def rows(self):
        return self._rows

    def set_padding(self, padding):
        """Set terminal padding and recalculate grid."""
        self._padding = padding
        self._recalculate_grid()
        self.update()

    def get_cwd(self):
        return self._process.get_cwd()

    def get_title(self):
        return self._screen.title or ""

    # --- Data handling ---

    def _on_data_ready(self, data):
        """Feed raw bytes from PTY into pyte, coalesce repaints."""
        self._stream.feed(data)
        self._url_cache_valid = False
        self._update_scrollbar()
        # Auto-scroll to bottom on new output
        if self._scrollback_offset > 0 and not self._screen.in_alt_screen:
            self._scrollback_offset = 0
        # Coalesce: schedule a repaint if one isn't already pending
        if not self._repaint_pending:
            self._repaint_pending = True
            self._repaint_timer.start()

    def _flush_repaint(self):
        """Execute the coalesced repaint."""
        self._repaint_pending = False
        self.update()

    def _on_process_exited(self, status):
        self.process_exited.emit(status)

    def _on_title_changed(self, title):
        self.title_changed.emit(title)

    def _on_bell(self):
        """Visual bell: briefly flash background."""
        self._bell_active = True
        self.update()
        self._bell_timer.start(120)

    def _clear_bell(self):
        self._bell_active = False
        self.update()

    # --- Cursor blink ---

    def _toggle_cursor(self):
        self._cursor_visible = not self._cursor_visible
        self.update()

    # --- Grid calculations ---

    def _recalculate_grid(self):
        """Recalculate rows/cols from widget size and resize PTY."""
        sb_width = self._scrollbar.width() if self._scrollbar.isVisible() else 0
        pad = self._padding * 2
        available_width = self.width() - sb_width - pad
        available_height = self.height() - pad
        new_cols = max(2, available_width // self._cell_width)
        new_rows = max(1, available_height // self._cell_height)

        if new_cols != self._cols or new_rows != self._rows:
            self._cols = new_cols
            self._rows = new_rows
            self._screen.resize(new_rows, new_cols)
            self._process.resize(new_rows, new_cols)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._recalculate_grid()
        # Position scrollbar (outside padding area)
        sb_width = 14
        self._scrollbar.setGeometry(
            self.width() - sb_width, 0, sb_width, self.height()
        )
        self._update_scrollbar()

    # --- Color resolution ---

    def _resolve_color(self, color, is_fg=True):
        """Resolve a pyte color spec to a QColor."""
        if color == "default":
            if is_fg:
                return QColor(self._theme.terminal_fg)
            else:
                return QColor(self._theme.terminal_bg)

        # Named ANSI color
        if isinstance(color, str) and color in _ANSI_COLOR_NAMES:
            idx = _ANSI_COLOR_NAMES[color]
            return get_ansi_palette(self._theme)[idx]

        if isinstance(color, str):
            # 24-bit truecolor (hex string like "ff00aa") — check before
            # isdigit() since all-digit hex strings like "999999" would
            # otherwise be misinterpreted as a 256-color index.
            if len(color) == 6:
                try:
                    r = int(color[0:2], 16)
                    g = int(color[2:4], 16)
                    b = int(color[4:6], 16)
                    return QColor(r, g, b)
                except ValueError:
                    pass

            # 256-color index (string of digits, 0-255)
            if color.isdigit() and len(color) <= 3:
                idx = int(color)
                if idx <= 255:
                    return get_xterm_256_color(idx, self._theme)

        # Fallback
        if is_fg:
            return QColor(self._theme.terminal_fg)
        return QColor(self._theme.terminal_bg)

    @staticmethod
    def _luminance(c):
        """Perceived brightness (0-255) of a QColor."""
        return (c.red() * 299 + c.green() * 587 + c.blue() * 114) / 1000

    def _ensure_contrast(self, fg, bg):
        """If fg is too close to bg, swap to the theme's opposite default."""
        if abs(self._luminance(fg) - self._luminance(bg)) < 40:
            return QColor(self._theme.terminal_fg)
        return fg

    # --- Display row <-> data source mapping ---

    def _get_history_lines(self):
        """Return the history top deque (direct reference, no copy)."""
        if hasattr(self._screen.history, 'top'):
            return self._screen.history.top
        return []

    def _get_line_data(self, display_row, history_lines=None):
        """Get the character data for a display row, accounting for scrollback.

        Returns (line_data, is_history):
            line_data: dict (screen buffer row) or list (history line)
            is_history: True if this row comes from scrollback history
        """
        if self._scrollback_offset > 0 and not self._screen.in_alt_screen:
            if history_lines is None:
                history_lines = self._get_history_lines()
            history_len = len(history_lines)
            history_line_idx = history_len - self._scrollback_offset + display_row
            if history_line_idx < 0:
                return None, False
            elif history_line_idx < history_len:
                return history_lines[history_line_idx], True
            else:
                screen_row = history_line_idx - history_len
                return self._screen.buffer.get(screen_row, {}), False
        else:
            return self._screen.buffer.get(display_row, {}), False

    def _get_char_at(self, line_data, col, is_history):
        """Get a character from line data at the given column."""
        if line_data is None:
            return self._screen.default_char
        if is_history:
            # History lines are lists
            if col < len(line_data):
                return line_data[col]
            return self._screen.default_char
        else:
            # Screen buffer rows are dicts
            return line_data.get(col, self._screen.default_char)

    # --- Selection helpers ---

    def _pos_to_cell(self, pos):
        """Convert a QPoint (widget coords) to (display_row, col)."""
        col = max(0, min((pos.x() - self._padding) // self._cell_width, self._cols - 1))
        row = max(0, min((pos.y() - self._padding) // self._cell_height, self._rows - 1))
        return (row, col)

    def _is_in_selection(self, display_row, col):
        """Check if (display_row, col) is within the current selection."""
        if self._selection_start is None or self._selection_end is None:
            return False
        sr, sc = self._selection_start
        er, ec = self._selection_end
        # Normalize: ensure start <= end
        if (sr, sc) > (er, ec):
            sr, sc, er, ec = er, ec, sr, sc
        if display_row < sr or display_row > er:
            return False
        if display_row == sr and display_row == er:
            return sc <= col <= ec
        if display_row == sr:
            return col >= sc
        if display_row == er:
            return col <= ec
        return True

    def _get_selected_text(self):
        """Extract selected text from whatever is currently displayed."""
        if self._selection_start is None or self._selection_end is None:
            return ""
        sr, sc = self._selection_start
        er, ec = self._selection_end
        if (sr, sc) > (er, ec):
            sr, sc, er, ec = er, ec, sr, sc

        history_lines = self._get_history_lines()
        lines = []
        for display_row in range(sr, er + 1):
            line_data, is_history = self._get_line_data(display_row, history_lines)
            line_chars = []
            start_col = sc if display_row == sr else 0
            end_col = ec if display_row == er else self._cols - 1

            for col in range(start_col, end_col + 1):
                char = self._get_char_at(line_data, col, is_history)
                line_chars.append(char.data if char.data else " ")

            line = "".join(line_chars).rstrip()
            lines.append(line)

        return "\n".join(lines)

    def has_selection(self):
        return self._selection_start is not None and self._selection_end is not None

    def clear_selection(self):
        self._selection_start = None
        self._selection_end = None
        self.update()

    def select_all(self):
        """Select all visible text."""
        self._selection_start = (0, 0)
        self._selection_end = (self._rows - 1, self._cols - 1)
        self.update()

    # --- Clipboard ---

    def copy_selection(self):
        """Copy selected text to clipboard."""
        text = self._get_selected_text()
        if text:
            QApplication.clipboard().setText(text)
        return bool(text)

    def paste_clipboard(self):
        """Paste clipboard text into terminal."""
        text = QApplication.clipboard().text()
        if text:
            # Bracket paste if mode 2004 is active
            if 2004 in self._screen.mode:
                data = b"\x1b[200~" + text.encode("utf-8") + b"\x1b[201~"
            else:
                data = text.encode("utf-8")
            self._process.write(data)

    # --- Paint ---

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(self._font)

        # Background
        bg_color = QColor(self._theme.terminal_bg)
        if self._bell_active:
            bg_color = bg_color.lighter(150)
        painter.fillRect(self.rect(), bg_color)

        # Apply padding offset
        painter.translate(self._padding, self._padding)

        screen = self._screen
        history_lines = self._get_history_lines()

        # Build URL map for this paint cycle (for underline rendering)
        url_cells = self._find_urls_on_screen(history_lines)

        for display_row in range(self._rows):
            line_data, is_history = self._get_line_data(display_row, history_lines)
            if line_data is None:
                continue
            self._paint_line(painter, display_row, line_data, is_history, url_cells)

        # Draw cursor:
        # - Only when not scrolled back
        # - Only when blink state is visible
        # - Only when terminal hasn't hidden cursor via \e[?25l
        cursor_hidden = getattr(screen.cursor, 'hidden', False)
        if self._scrollback_offset == 0 and self._cursor_visible and not cursor_hidden:
            self._paint_cursor(painter, screen.cursor.y, screen.cursor.x)

        painter.end()

    def _paint_line(self, painter, display_row, line_data, is_history, url_cells=None):
        """Paint one line from either screen buffer or history."""
        y = display_row * self._cell_height
        screen = self._screen

        col = 0
        while col < self._cols:
            char = self._get_char_at(line_data, col, is_history)
            char_data = char.data if char.data else " "

            # Resolve colors
            fg = self._resolve_color(char.fg, is_fg=True)
            bg = self._resolve_color(char.bg, is_fg=False)

            # Handle bold -> bright color mapping for base ANSI colors (0-7)
            if char.bold and isinstance(char.fg, str) and char.fg in _ANSI_COLOR_NAMES:
                idx = _ANSI_COLOR_NAMES[char.fg]
                if idx < 8:
                    fg = get_ansi_palette(self._theme)[idx + 8]

            # Reverse video
            if char.reverse:
                fg, bg = bg, fg

            # Ensure minimum contrast so text is never invisible
            fg = self._ensure_contrast(fg, bg)

            # Selection highlighting
            in_sel = self._is_in_selection(display_row, col)
            if in_sel:
                bg = QColor(self._theme.selection_bg)
                fg = QColor(self._theme.selection_fg)

            x = col * self._cell_width

            # Wide character handling
            char_width = 1
            wc = wcwidth(char_data) if char_data and char_data != " " else 1
            if wc > 1:
                char_width = wc

            cell_rect = QRect(x, y, self._cell_width * char_width, self._cell_height)

            # Draw cell background
            if bg != QColor(self._theme.terminal_bg) or in_sel:
                painter.fillRect(cell_rect, bg)

            # Check if this cell is part of a URL
            is_url = url_cells and (display_row, col) in url_cells

            # Draw character
            if char_data.strip():
                # URL text gets a distinct color
                draw_fg = QColor("#5599DD") if is_url and not in_sel else fg
                painter.setPen(draw_fg)
                if char.bold and char.italics:
                    painter.setFont(self._font_bold_italic)
                elif char.bold:
                    painter.setFont(self._font_bold)
                elif char.italics:
                    painter.setFont(self._font_italic)
                painter.drawText(x, y + self._font_ascent, char_data)
                if char.bold or char.italics:
                    painter.setFont(self._font)

            # Underline (from terminal attr or URL hover)
            is_hovered_url = (self._hovered_url and
                              url_cells and (display_row, col) in url_cells and
                              url_cells[(display_row, col)] == self._hovered_url[4])
            if char.underscore or is_hovered_url:
                painter.setPen(QColor("#5599DD") if is_hovered_url else fg)
                underline_y = y + self._cell_height - 1
                painter.drawLine(x, underline_y, x + self._cell_width * char_width, underline_y)

            # Strikethrough
            if char.strikethrough:
                painter.setPen(fg)
                strike_y = y + self._cell_height // 2
                painter.drawLine(x, strike_y, x + self._cell_width * char_width, strike_y)

            col += char_width

    def _paint_cursor(self, painter, row, col):
        """Draw the cursor at the given position."""
        x = col * self._cell_width
        y = row * self._cell_height
        cursor_color = QColor(self._theme.cursor_color)

        style = self._settings.get("cursor_style", "block") if self._settings else "block"

        if style == "block":
            painter.fillRect(x, y, self._cell_width, self._cell_height, cursor_color)
            # Draw the character under the cursor in inverted color
            char = self._screen.buffer.get(row, {}).get(col, self._screen.default_char)
            if char.data and char.data.strip():
                painter.setPen(QColor(self._theme.terminal_bg))
                painter.drawText(x, y + self._font_ascent, char.data)
        elif style == "underline":
            painter.fillRect(x, y + self._cell_height - 2, self._cell_width, 2, cursor_color)
        elif style == "bar":
            painter.fillRect(x, y, 2, self._cell_height, cursor_color)

    # --- Scrollbar ---

    def _update_scrollbar(self):
        history_len = len(self._screen.history.top) if hasattr(self._screen.history, 'top') else 0
        if history_len > 0 and not self._screen.in_alt_screen:
            self._scrollbar.setVisible(True)
            self._scrollbar.setRange(0, history_len)
            self._scrollbar.setValue(history_len - self._scrollback_offset)
            self._scrollbar.setPageStep(self._rows)
        else:
            self._scrollbar.setVisible(False)

    def _on_scrollbar_changed(self, value):
        history_len = len(self._screen.history.top) if hasattr(self._screen.history, 'top') else 0
        self._scrollback_offset = max(0, history_len - value)
        self._url_cache_valid = False
        self.update()

    # --- URL detection ---

    def _get_line_text(self, display_row, history_lines=None):
        """Get the text content of a display row as a string."""
        line_data, is_history = self._get_line_data(display_row, history_lines)
        if line_data is None:
            return ""
        chars = []
        for col in range(self._cols):
            char = self._get_char_at(line_data, col, is_history)
            chars.append(char.data if char.data else " ")
        return "".join(chars)

    def _find_urls_on_screen(self, history_lines=None):
        """Find all URLs on the visible screen. Returns {(row,col): url_text}."""
        if self._url_cache_valid and self._url_cache is not None:
            return self._url_cache
        url_cells = {}
        for display_row in range(self._rows):
            line_text = self._get_line_text(display_row, history_lines)
            for match in _URL_RE.finditer(line_text):
                url_text = match.group()
                for col in range(match.start(), match.end()):
                    url_cells[(display_row, col)] = url_text
        self._url_cache = url_cells
        self._url_cache_valid = True
        return url_cells

    def _url_at_pos(self, display_row, col):
        """Return the URL string at the given cell, or None."""
        line_text = self._get_line_text(display_row)
        for match in _URL_RE.finditer(line_text):
            if match.start() <= col < match.end():
                return match.group()
        return None

    def _reset_click_count(self):
        self._click_count = 0

    # --- Mouse reporting ---

    def _mouse_reporting_active(self):
        """Check if any mouse tracking mode is enabled."""
        # X10 (9), X11 normal (1000), button (1002), any (1003)
        return any(m in self._screen.mode for m in (9, 1000, 1002, 1003))

    def _send_mouse_event(self, event, button, release=False):
        """Send mouse event to the child process using SGR encoding."""
        row, col = self._pos_to_cell(event.pos())
        # SGR 1006 encoding: ESC[<button;col+1;row+1M (press) or m (release)
        if 1006 in self._screen.mode:
            suffix = "m" if release else "M"
            seq = f"\x1b[<{button};{col+1};{row+1}{suffix}"
            self._process.write(seq.encode())
        else:
            # Legacy X10/X11 encoding
            if not release:
                cb = button + 32
                cx = col + 33
                cy = row + 33
                if cx < 256 and cy < 256:
                    self._process.write(bytes([0x1b, 0x5b, 0x4d, cb, cx, cy]))

    # --- Mouse events ---

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Track clicks for triple-click detection
            self._click_count += 1
            self._click_timer.start()

            # Ctrl+click on URL -> open in browser
            if event.modifiers() & Qt.ControlModifier:
                row, col = self._pos_to_cell(event.pos())
                url = self._url_at_pos(row, col)
                if url:
                    if not url.startswith("http"):
                        url = "http://" + url
                    QDesktopServices.openUrl(QUrl(url))
                    return

            # Mouse reporting: send to child process
            if self._mouse_reporting_active():
                self._send_mouse_event(event, 0)
                return

            # Triple-click: select entire line
            if self._click_count >= 3:
                self._click_count = 0
                display_row, _ = self._pos_to_cell(event.pos())
                self._selection_start = (display_row, 0)
                self._selection_end = (display_row, self._cols - 1)
                self._selecting = False
                self.update()
                return

            self._selecting = True
            self._selection_start = self._pos_to_cell(event.pos())
            self._selection_end = self._selection_start
            self._double_click_word = False
            self.update()

        elif event.button() == Qt.MiddleButton:
            if self._mouse_reporting_active():
                self._send_mouse_event(event, 1)
                return
            # Middle-click paste (X11 style)
            self.paste_clipboard()

        elif event.button() == Qt.RightButton:
            if self._mouse_reporting_active():
                self._send_mouse_event(event, 2)
                return
            # Right-click handled by contextMenuEvent

    def mouseMoveEvent(self, event):
        # Mouse motion reporting (mode 1002 button, 1003 any)
        if event.buttons() & Qt.LeftButton and self._mouse_reporting_active():
            if 1002 in self._screen.mode or 1003 in self._screen.mode:
                self._send_mouse_event(event, 32)  # button + motion flag
            return
        if not event.buttons() and 1003 in self._screen.mode:
            self._send_mouse_event(event, 35)  # no button + motion
            return

        # URL hover detection (when Ctrl is held)
        if event.modifiers() & Qt.ControlModifier:
            row, col = self._pos_to_cell(event.pos())
            url = self._url_at_pos(row, col)
            if url:
                if self._hovered_url is None or self._hovered_url[4] != url:
                    self._hovered_url = (row, col, row, col, url)
                    self.setCursor(QCursor(Qt.PointingHandCursor))
                    self.update()
            elif self._hovered_url is not None:
                self._hovered_url = None
                self.setCursor(QCursor(Qt.IBeamCursor))
                self.update()
        elif self._hovered_url is not None:
            self._hovered_url = None
            self.setCursor(QCursor(Qt.IBeamCursor))
            self.update()

        # Selection drag
        if self._selecting and event.buttons() & Qt.LeftButton:
            self._selection_end = self._pos_to_cell(event.pos())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._mouse_reporting_active():
                self._send_mouse_event(event, 0, release=True)
                return
            self._selecting = False
            if self._selection_start == self._selection_end:
                # Click without drag - clear selection
                self._selection_start = None
                self._selection_end = None
                self.update()
        elif event.button() == Qt.MiddleButton:
            if self._mouse_reporting_active():
                self._send_mouse_event(event, 1, release=True)
        elif event.button() == Qt.RightButton:
            if self._mouse_reporting_active():
                self._send_mouse_event(event, 2, release=True)

    def mouseDoubleClickEvent(self, event):
        """Double-click selects a word."""
        if event.button() == Qt.LeftButton:
            if self._mouse_reporting_active():
                return  # Let app handle it

            display_row, col = self._pos_to_cell(event.pos())
            line_data, is_history = self._get_line_data(display_row)

            # Find word boundaries
            start_col = col
            end_col = col

            def is_word_char(c):
                return c.isalnum() or c in ("_", "-", ".", "/", "~")

            char = self._get_char_at(line_data, col, is_history)
            if not is_word_char(char.data if char.data else " "):
                return

            while start_col > 0:
                c = self._get_char_at(line_data, start_col - 1, is_history)
                if not is_word_char(c.data if c.data else " "):
                    break
                start_col -= 1

            while end_col < self._cols - 1:
                c = self._get_char_at(line_data, end_col + 1, is_history)
                if not is_word_char(c.data if c.data else " "):
                    break
                end_col += 1

            self._selection_start = (display_row, start_col)
            self._selection_end = (display_row, end_col)
            self._double_click_word = True
            self.update()

    def wheelEvent(self, event):
        """Mouse wheel: scroll through history or send to child process."""
        if self._screen.in_alt_screen:
            # In alt screen (e.g., less, vim), send arrow keys to process
            delta = event.angleDelta().y()
            if self._mouse_reporting_active():
                # Send wheel events as mouse button 64/65
                btn = 64 if delta > 0 else 65
                self._send_mouse_event(event, btn)
            else:
                if delta > 0:
                    self._process.write(b"\x1b[A" * 3)  # Up arrow x3
                elif delta < 0:
                    self._process.write(b"\x1b[B" * 3)  # Down arrow x3
        else:
            # Normal mode: scroll through history
            delta = event.angleDelta().y()
            history_len = len(self._screen.history.top) if hasattr(self._screen.history, 'top') else 0
            if delta > 0:
                self._scrollback_offset = min(
                    self._scrollback_offset + 3, history_len
                )
            elif delta < 0:
                self._scrollback_offset = max(
                    self._scrollback_offset - 3, 0
                )
            self._update_scrollbar()
            self.update()

    # --- Context menu ---

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        copy_action = menu.addAction("Copy")
        copy_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        copy_action.setEnabled(self.has_selection())
        copy_action.triggered.connect(self.copy_selection)

        paste_action = menu.addAction("Paste")
        paste_action.setShortcut(QKeySequence("Ctrl+Shift+V"))
        paste_action.triggered.connect(self.paste_clipboard)

        select_all_action = menu.addAction("Select All")
        select_all_action.triggered.connect(self.select_all)

        menu.addSeparator()

        clear_action = menu.addAction("Clear")
        clear_action.triggered.connect(self.clear_terminal)

        reset_action = menu.addAction("Reset")
        reset_action.triggered.connect(self.reset_terminal)

        menu.exec_(event.globalPos())

    def clear_terminal(self):
        """Clear the screen (like 'clear' command)."""
        self._process.write(b"\x1b[2J\x1b[H")

    def reset_terminal(self):
        """Full reset of terminal state."""
        self._screen.reset()
        self._scrollback_offset = 0
        self.update()

    # --- Keyboard input ---

    def focusNextPrevChild(self, next):
        """Prevent Tab/Shift+Tab from navigating away; let keyPressEvent handle them."""
        return False

    def keyPressEvent(self, event):
        """Map Qt key events to terminal escape sequences."""
        key = event.key()
        mods = event.modifiers()
        text = event.text()

        # Reset scroll on typing
        if self._scrollback_offset > 0:
            self._scrollback_offset = 0
            self._update_scrollbar()

        # Clear selection on typing (except for copy shortcut)
        if not (mods & Qt.ShiftModifier and mods & Qt.ControlModifier and key == Qt.Key_C):
            if self.has_selection() and key not in (Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta):
                self.clear_selection()

        # Ctrl+Shift shortcuts (terminal-specific, don't send to shell)
        if mods & Qt.ControlModifier and mods & Qt.ShiftModifier:
            if key == Qt.Key_C:
                self.copy_selection()
                return
            elif key == Qt.Key_V:
                self.paste_clipboard()
                return
            # Let other Ctrl+Shift combos (T, W, F, Tab) propagate to MainWindow
            event.ignore()
            return

        # Special keys mapping
        seq = self._map_key(key, mods)
        if seq is not None:
            self._process.write(seq)
            return

        # Ctrl+letter (send as control character)
        if mods & Qt.ControlModifier and not mods & Qt.ShiftModifier:
            if Qt.Key_A <= key <= Qt.Key_Z:
                ctrl_char = key - Qt.Key_A + 1
                self._process.write(bytes([ctrl_char]))
                return
            # Ctrl+[ = ESC
            if key == Qt.Key_BracketLeft:
                self._process.write(b"\x1b")
                return
            # Ctrl+] = GS
            if key == Qt.Key_BracketRight:
                self._process.write(b"\x1d")
                return
            # Ctrl+\ = FS
            if key == Qt.Key_Backslash:
                self._process.write(b"\x1c")
                return

        # Alt+key: send as ESC + key
        if mods & Qt.AltModifier and text:
            self._process.write(b"\x1b" + text.encode("utf-8"))
            return

        # Regular text
        if text:
            self._process.write(text.encode("utf-8"))
            return

        # Pass unhandled events up
        super().keyPressEvent(event)

    # Static keymap for non-cursor keys (never changes)
    _STATIC_KEYMAP = {
        Qt.Key_Return: b"\r",
        Qt.Key_Enter: b"\r",
        Qt.Key_Backspace: b"\x7f",
        Qt.Key_Tab: b"\t",
        Qt.Key_Escape: b"\x1b",
        Qt.Key_Home: b"\x1b[H",
        Qt.Key_End: b"\x1b[F",
        Qt.Key_Insert: b"\x1b[2~",
        Qt.Key_Delete: b"\x1b[3~",
        Qt.Key_PageUp: b"\x1b[5~",
        Qt.Key_PageDown: b"\x1b[6~",
        Qt.Key_F1: b"\x1bOP",
        Qt.Key_F2: b"\x1bOQ",
        Qt.Key_F3: b"\x1bOR",
        Qt.Key_F4: b"\x1bOS",
        Qt.Key_F5: b"\x1b[15~",
        Qt.Key_F6: b"\x1b[17~",
        Qt.Key_F7: b"\x1b[18~",
        Qt.Key_F8: b"\x1b[19~",
        Qt.Key_F9: b"\x1b[20~",
        Qt.Key_F10: b"\x1b[21~",
        Qt.Key_F12: b"\x1b[24~",
    }

    # Cursor keys depend on DECCKM mode
    _CURSOR_KEYS = {
        Qt.Key_Up: b"A",
        Qt.Key_Down: b"B",
        Qt.Key_Right: b"C",
        Qt.Key_Left: b"D",
    }

    def _map_key(self, key, mods):
        """Map a Qt key to a terminal escape sequence, or return None."""
        seq = self._STATIC_KEYMAP.get(key)
        if seq is not None:
            return seq
        suffix = self._CURSOR_KEYS.get(key)
        if suffix is not None:
            prefix = b"\x1bO" if 1 in self._screen.mode else b"\x1b["
            return prefix + suffix
        return None

    # --- Theme ---

    def apply_theme(self, theme):
        """Apply a new theme to this terminal."""
        self._theme = theme
        self.update()

    # --- Session data ---

    def get_session_data(self):
        return {
            "cwd": self.get_cwd(),
            "title": self.get_title(),
        }

    # --- Find in scrollback ---

    def find_in_scrollback(self, query, forward=True):
        """Search scrollback + screen buffer for query. Returns (current_match, total_matches).

        Scrolls to the first/next match and highlights it via selection.
        """
        if not query:
            return (0, 0)

        query_lower = query.lower()
        history_lines = self._get_history_lines()
        matches = []  # list of (absolute_row, start_col, end_col)

        # Search history lines
        for i, line in enumerate(history_lines):
            text = ""
            for col in range(self._cols):
                if col < len(line):
                    text += line[col].data if line[col].data else " "
                else:
                    text += " "
            idx = 0
            while True:
                pos = text.lower().find(query_lower, idx)
                if pos < 0:
                    break
                matches.append((-len(history_lines) + i, pos, pos + len(query) - 1))
                idx = pos + 1

        # Search screen buffer
        for row in range(self._rows):
            buf_row = self._screen.buffer.get(row, {})
            text = ""
            for col in range(self._cols):
                char = buf_row.get(col, self._screen.default_char)
                text += char.data if char.data else " "
            idx = 0
            while True:
                pos = text.lower().find(query_lower, idx)
                if pos < 0:
                    break
                matches.append((row, pos, pos + len(query) - 1))
                idx = pos + 1

        if not matches:
            self.clear_selection()
            return (0, 0)

        # Find the best match relative to current scroll position
        # Current view center in absolute coordinates
        current_center = -self._scrollback_offset + self._rows // 2

        # Find closest match to center in the given direction
        best_idx = 0
        if hasattr(self, '_last_find_idx') and self._last_find_query == query_lower:
            if forward:
                best_idx = (self._last_find_idx + 1) % len(matches)
            else:
                best_idx = (self._last_find_idx - 1) % len(matches)
        else:
            # First search: find closest match
            min_dist = float('inf')
            for i, (abs_row, sc, ec) in enumerate(matches):
                dist = abs(abs_row - current_center)
                if dist < min_dist:
                    min_dist = dist
                    best_idx = i

        self._last_find_idx = best_idx
        self._last_find_query = query_lower

        abs_row, sc, ec = matches[best_idx]
        history_len = len(history_lines)

        # Scroll to make the match visible
        if abs_row < 0:
            # Match is in history
            self._scrollback_offset = history_len + abs_row - self._rows // 2
            self._scrollback_offset = max(0, min(self._scrollback_offset, history_len))
        else:
            # Match is on screen
            self._scrollback_offset = 0

        # Calculate display row and set selection
        if self._scrollback_offset > 0:
            display_row = abs_row + history_len - (history_len - self._scrollback_offset)
        else:
            display_row = abs_row

        display_row = max(0, min(display_row, self._rows - 1))
        self._selection_start = (display_row, sc)
        self._selection_end = (display_row, ec)

        self._update_scrollbar()
        self.update()
        return (best_idx + 1, len(matches))

    # --- Cleanup ---

    def terminate(self):
        """Terminate the underlying process."""
        self._cursor_timer.stop()
        self._repaint_timer.stop()
        self._process.terminate()
