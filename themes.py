"""Theme system with ANSI color palettes for fterm."""

from dataclasses import dataclass, field
from typing import Dict, List
from PyQt5.QtGui import QColor


@dataclass
class TerminalTheme:
    name: str
    # Terminal colors
    terminal_bg: str
    terminal_fg: str
    cursor_color: str
    selection_bg: str
    selection_fg: str
    # ANSI 16-color palette (indices 0-15)
    black: str
    red: str
    green: str
    yellow: str
    blue: str
    magenta: str
    cyan: str
    white: str
    bright_black: str
    bright_red: str
    bright_green: str
    bright_yellow: str
    bright_blue: str
    bright_magenta: str
    bright_cyan: str
    bright_white: str
    # UI chrome
    tab_bar_bg: str = "#252526"
    status_bar_bg: str = "#007ACC"
    status_bar_fg: str = "#FFFFFF"
    menu_bg: str = "#2D2D2D"
    menu_fg: str = "#D4D4D4"
    border_color: str = "#404040"


THEMES: Dict[str, TerminalTheme] = {
    "Dark": TerminalTheme(
        name="Dark",
        terminal_bg="#1E1E1E",
        terminal_fg="#D4D4D4",
        cursor_color="#AEAFAD",
        selection_bg="#264F78",
        selection_fg="#FFFFFF",
        black="#000000",
        red="#CD3131",
        green="#0DBC79",
        yellow="#E5E510",
        blue="#2472C8",
        magenta="#BC3FBC",
        cyan="#11A8CD",
        white="#E5E5E5",
        bright_black="#666666",
        bright_red="#F14C4C",
        bright_green="#23D18B",
        bright_yellow="#F5F543",
        bright_blue="#3B8EEA",
        bright_magenta="#D670D6",
        bright_cyan="#29B8DB",
        bright_white="#FFFFFF",
        tab_bar_bg="#252526",
        status_bar_bg="#007ACC",
        status_bar_fg="#FFFFFF",
        menu_bg="#2D2D2D",
        menu_fg="#D4D4D4",
        border_color="#404040",
    ),
    "Light": TerminalTheme(
        name="Light",
        terminal_bg="#FFFFFF",
        terminal_fg="#000000",
        cursor_color="#000000",
        selection_bg="#ADD6FF",
        selection_fg="#000000",
        black="#000000",
        red="#CD3131",
        green="#00BC00",
        yellow="#949800",
        blue="#0451A5",
        magenta="#BC05BC",
        cyan="#0598BC",
        white="#555555",
        bright_black="#666666",
        bright_red="#CD3131",
        bright_green="#14CE14",
        bright_yellow="#B5BA00",
        bright_blue="#0451A5",
        bright_magenta="#BC05BC",
        bright_cyan="#0598BC",
        bright_white="#A5A5A5",
        tab_bar_bg="#E8E8E8",
        status_bar_bg="#007ACC",
        status_bar_fg="#FFFFFF",
        menu_bg="#F0F0F0",
        menu_fg="#000000",
        border_color="#CCCCCC",
    ),
    "Solarized Dark": TerminalTheme(
        name="Solarized Dark",
        terminal_bg="#002B36",
        terminal_fg="#839496",
        cursor_color="#839496",
        selection_bg="#073642",
        selection_fg="#93A1A1",
        black="#073642",
        red="#DC322F",
        green="#859900",
        yellow="#B58900",
        blue="#268BD2",
        magenta="#D33682",
        cyan="#2AA198",
        white="#EEE8D5",
        bright_black="#002B36",
        bright_red="#CB4B16",
        bright_green="#586E75",
        bright_yellow="#657B83",
        bright_blue="#839496",
        bright_magenta="#6C71C4",
        bright_cyan="#93A1A1",
        bright_white="#FDF6E3",
        tab_bar_bg="#073642",
        status_bar_bg="#073642",
        status_bar_fg="#839496",
        menu_bg="#002B36",
        menu_fg="#839496",
        border_color="#073642",
    ),
}


def get_theme(name: str) -> TerminalTheme:
    """Get a theme by name, defaulting to Dark."""
    return THEMES.get(name, THEMES["Dark"])


def get_theme_names() -> list:
    """Return list of available theme names."""
    return list(THEMES.keys())


def get_ansi_palette(theme: TerminalTheme) -> List[QColor]:
    """Return 16-element QColor list for ANSI colors 0-15."""
    return [
        QColor(theme.black),
        QColor(theme.red),
        QColor(theme.green),
        QColor(theme.yellow),
        QColor(theme.blue),
        QColor(theme.magenta),
        QColor(theme.cyan),
        QColor(theme.white),
        QColor(theme.bright_black),
        QColor(theme.bright_red),
        QColor(theme.bright_green),
        QColor(theme.bright_yellow),
        QColor(theme.bright_blue),
        QColor(theme.bright_magenta),
        QColor(theme.bright_cyan),
        QColor(theme.bright_white),
    ]


# Pre-computed xterm-256 color cube (indices 16-231) and grayscale (232-255)
_XTERM_256_CACHE = None


def get_xterm_256_color(index: int, theme: TerminalTheme) -> QColor:
    """Resolve an xterm-256 color index to a QColor.

    0-15:    Theme ANSI palette
    16-231:  6x6x6 color cube
    232-255: Grayscale ramp
    """
    if index < 16:
        return get_ansi_palette(theme)[index]
    elif index < 232:
        # 6x6x6 color cube
        index -= 16
        b = index % 6
        index //= 6
        g = index % 6
        r = index // 6
        return QColor(
            r * 51 if r else 0,
            g * 51 if g else 0,
            b * 51 if b else 0,
        )
    else:
        # Grayscale ramp: 232-255 -> 8, 18, 28, ..., 238
        gray = 8 + (index - 232) * 10
        return QColor(gray, gray, gray)


def get_app_stylesheet(theme: TerminalTheme) -> str:
    """Generate a Qt stylesheet for the application based on theme."""
    return f"""
        QMainWindow {{
            background-color: {theme.terminal_bg};
        }}
        QMenuBar {{
            background-color: {theme.menu_bg};
            color: {theme.menu_fg};
            border-bottom: 1px solid {theme.border_color};
        }}
        QMenuBar::item:selected {{
            background-color: {theme.selection_bg};
            color: {theme.selection_fg};
        }}
        QMenu {{
            background-color: {theme.menu_bg};
            color: {theme.menu_fg};
            border: 1px solid {theme.border_color};
        }}
        QMenu::item:selected {{
            background-color: {theme.selection_bg};
            color: {theme.selection_fg};
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {theme.border_color};
        }}
        QTabWidget::pane {{
            border: 1px solid {theme.border_color};
        }}
        QTabBar {{
            background-color: {theme.tab_bar_bg};
        }}
        QTabBar::tab {{
            background-color: {theme.tab_bar_bg};
            color: {theme.menu_fg};
            padding: 6px 14px;
            border: 1px solid {theme.border_color};
            border-bottom: none;
            margin-right: 1px;
        }}
        QTabBar::tab:selected {{
            background-color: {theme.terminal_bg};
            color: {theme.terminal_fg};
        }}
        QTabBar::tab:hover {{
            background-color: {theme.selection_bg};
        }}
        QStatusBar {{
            background-color: {theme.status_bar_bg};
            color: {theme.status_bar_fg};
            border-top: 1px solid {theme.border_color};
        }}
        QStatusBar QLabel {{
            color: {theme.status_bar_fg};
            padding: 0 8px;
        }}
        QToolBar {{
            background-color: {theme.tab_bar_bg};
            border-bottom: 1px solid {theme.border_color};
            spacing: 2px;
            padding: 2px;
        }}
        QToolButton {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 3px;
            padding: 3px;
            color: {theme.menu_fg};
        }}
        QToolButton:hover {{
            background-color: {theme.selection_bg};
            border: 1px solid {theme.border_color};
        }}
        QDialog {{
            background-color: {theme.menu_bg};
            color: {theme.menu_fg};
        }}
        QLabel {{
            color: {theme.menu_fg};
        }}
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {theme.terminal_bg};
            color: {theme.terminal_fg};
            border: 1px solid {theme.border_color};
            padding: 3px;
        }}
        QCheckBox {{
            color: {theme.menu_fg};
        }}
        QPushButton {{
            background-color: {theme.tab_bar_bg};
            color: {theme.menu_fg};
            border: 1px solid {theme.border_color};
            padding: 5px 15px;
            border-radius: 3px;
        }}
        QPushButton:hover {{
            background-color: {theme.selection_bg};
            color: {theme.selection_fg};
        }}
        QComboBox {{
            background-color: {theme.terminal_bg};
            color: {theme.terminal_fg};
            border: 1px solid {theme.border_color};
            padding: 3px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {theme.menu_bg};
            color: {theme.menu_fg};
            selection-background-color: {theme.selection_bg};
            selection-color: {theme.selection_fg};
        }}
        QSpinBox {{
            background-color: {theme.terminal_bg};
            color: {theme.terminal_fg};
            border: 1px solid {theme.border_color};
        }}
        QGroupBox {{
            color: {theme.menu_fg};
            border: 1px solid {theme.border_color};
            margin-top: 6px;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            padding: 0 5px;
        }}
        QScrollBar:vertical {{
            background-color: {theme.tab_bar_bg};
            width: 14px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {theme.border_color};
            min-height: 20px;
            border-radius: 3px;
            margin: 2px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """
