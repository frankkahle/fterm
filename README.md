# fterm

A terminal emulator built from scratch with Python, PyQt5, and pyte.

**Version 1.0.0** | **SOS Tech Services**

## Features

- **Full VT100/xterm emulation** via pyte — colored output, cursor movement, alt-screen apps (vim, htop, less, nano)
- **Multiple tabs** — Ctrl+Shift+T to open, Ctrl+Shift+W to close, Ctrl+Tab to switch
- **Right-click context menu** — Copy, Paste, Select All, Clear, Reset
- **Mouse text selection** — click and drag, double-click to select word
- **Scrollback history** — mouse wheel to scroll, configurable buffer size (default 10,000 lines)
- **256-color and truecolor support** — ANSI 16-color palette, xterm-256 color cube, 24-bit RGB
- **Themes** — Dark, Light, and Solarized Dark built-in
- **Configurable** — font, cursor style (block/underline/bar), cursor blink, scrollback size
- **Session restore** — remembers open tabs and working directories across restarts
- **Zoom** — Ctrl+Shift+=/- to zoom in/out
- **Preferences dialog** — GUI settings for shell, appearance, and session options
- **Desktop integration** — installs as a system application with icon in your programs menu

## Install

Requires Python 3, PyQt5, and Linux.

```bash
# Install system dependencies
sudo apt install python3-pyqt5 librsvg2-bin

# Install Python dependencies
pip install pyte ptyprocess wcwidth

# Clone and install
git clone https://github.com/frankkahle/fterm.git
cd fterm
sudo ./install.sh
```

This installs fterm to `/opt/fterm`, creates the `fterm` command, and adds it to your applications menu with an icon.

To uninstall:

```bash
sudo /opt/fterm/uninstall.sh
```

## Run Without Installing

```bash
git clone https://github.com/frankkahle/fterm.git
cd fterm
python3 main.py
```

## Usage

```bash
fterm                  # Start with default shell
fterm -e /bin/zsh      # Start with a specific shell
fterm -d ~/projects    # Start in a specific directory
fterm -n               # Start fresh (ignore saved session)
```

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+Shift+T | New tab |
| Ctrl+Shift+W | Close tab |
| Ctrl+Tab | Next tab |
| Ctrl+Shift+Tab | Previous tab |
| Ctrl+Shift+C | Copy selection |
| Ctrl+Shift+V | Paste |
| Ctrl+Shift+= | Zoom in |
| Ctrl+Shift+- | Zoom out |
| Ctrl+Shift+0 | Reset zoom |
| F11 | Toggle fullscreen |

Note: Ctrl+C sends SIGINT to the shell as expected. Copy uses Ctrl+Shift+C.

## Configuration

Settings are stored in `~/.config/fterm/settings.json` and can be edited via Tools > Preferences.

## Dependencies

- [PyQt5](https://riverbankcomputing.com/software/pyqt/) — GUI toolkit
- [pyte](https://github.com/selectel/pyte) — VT100 terminal emulator in Python
- [ptyprocess](https://github.com/pexpect/ptyprocess) — PTY process wrapper
- [wcwidth](https://github.com/jquast/wcwidth) — wide character width lookup

## License

Copyright SOS Tech Services
