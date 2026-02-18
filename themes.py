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
    "Dracula": TerminalTheme(
        name="Dracula",
        terminal_bg="#282A36",
        terminal_fg="#F8F8F2",
        cursor_color="#F8F8F2",
        selection_bg="#44475A",
        selection_fg="#F8F8F2",
        black="#21222C",
        red="#FF5555",
        green="#50FA7B",
        yellow="#F1FA8C",
        blue="#BD93F9",
        magenta="#FF79C6",
        cyan="#8BE9FD",
        white="#F8F8F2",
        bright_black="#6272A4",
        bright_red="#FF6E6E",
        bright_green="#69FF94",
        bright_yellow="#FFFFA5",
        bright_blue="#D6ACFF",
        bright_magenta="#FF92DF",
        bright_cyan="#A4FFFF",
        bright_white="#FFFFFF",
        tab_bar_bg="#21222C",
        status_bar_bg="#44475A",
        status_bar_fg="#F8F8F2",
        menu_bg="#282A36",
        menu_fg="#F8F8F2",
        border_color="#44475A",
    ),
    "Nord": TerminalTheme(
        name="Nord",
        terminal_bg="#2E3440",
        terminal_fg="#D8DEE9",
        cursor_color="#D8DEE9",
        selection_bg="#434C5E",
        selection_fg="#ECEFF4",
        black="#3B4252",
        red="#BF616A",
        green="#A3BE8C",
        yellow="#EBCB8B",
        blue="#81A1C1",
        magenta="#B48EAD",
        cyan="#88C0D0",
        white="#E5E9F0",
        bright_black="#4C566A",
        bright_red="#BF616A",
        bright_green="#A3BE8C",
        bright_yellow="#EBCB8B",
        bright_blue="#81A1C1",
        bright_magenta="#B48EAD",
        bright_cyan="#8FBCBB",
        bright_white="#ECEFF4",
        tab_bar_bg="#3B4252",
        status_bar_bg="#434C5E",
        status_bar_fg="#ECEFF4",
        menu_bg="#2E3440",
        menu_fg="#D8DEE9",
        border_color="#4C566A",
    ),
    "Gruvbox": TerminalTheme(
        name="Gruvbox",
        terminal_bg="#282828",
        terminal_fg="#EBDBB2",
        cursor_color="#EBDBB2",
        selection_bg="#504945",
        selection_fg="#FBF1C7",
        black="#282828",
        red="#CC241D",
        green="#98971A",
        yellow="#D79921",
        blue="#458588",
        magenta="#B16286",
        cyan="#689D6A",
        white="#A89984",
        bright_black="#928374",
        bright_red="#FB4934",
        bright_green="#B8BB26",
        bright_yellow="#FABD2F",
        bright_blue="#83A598",
        bright_magenta="#D3869B",
        bright_cyan="#8EC07C",
        bright_white="#EBDBB2",
        tab_bar_bg="#1D2021",
        status_bar_bg="#504945",
        status_bar_fg="#EBDBB2",
        menu_bg="#282828",
        menu_fg="#EBDBB2",
        border_color="#504945",
    ),
    "Monokai": TerminalTheme(
        name="Monokai",
        terminal_bg="#272822",
        terminal_fg="#F8F8F2",
        cursor_color="#F8F8F0",
        selection_bg="#49483E",
        selection_fg="#F8F8F2",
        black="#272822",
        red="#F92672",
        green="#A6E22E",
        yellow="#F4BF75",
        blue="#66D9EF",
        magenta="#AE81FF",
        cyan="#A1EFE4",
        white="#F8F8F2",
        bright_black="#75715E",
        bright_red="#F92672",
        bright_green="#A6E22E",
        bright_yellow="#F4BF75",
        bright_blue="#66D9EF",
        bright_magenta="#AE81FF",
        bright_cyan="#A1EFE4",
        bright_white="#F9F8F5",
        tab_bar_bg="#1E1F1C",
        status_bar_bg="#49483E",
        status_bar_fg="#F8F8F2",
        menu_bg="#272822",
        menu_fg="#F8F8F2",
        border_color="#49483E",
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
