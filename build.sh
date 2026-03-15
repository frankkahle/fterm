#!/bin/bash
# Build SOSterm as a compiled binary using PyInstaller.
#
# Usage:
#   ./build.sh          # Build onedir (fast startup, dist/SOSterm/ folder)
#   ./build.sh onefile  # Build single-file (one executable, slower startup)
#
# Requirements:
#   pip install pyinstaller

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

MODE="${1:-onedir}"

# All Python source files that PyInstaller must include
HIDDEN_IMPORTS=(
    --hidden-import=pyte
    --hidden-import=pyte.streams
    --hidden-import=pyte.screens
    --hidden-import=pyte.control
    --hidden-import=pyte.escape
    --hidden-import=pyte.graphics
    --hidden-import=pyte.modes
    --hidden-import=ptyprocess
    --hidden-import=wcwidth
    --hidden-import=configparser
    --hidden-import=PyQt5.sip
    --hidden-import=PyQt5.QtSvg
    --hidden-import=json
    --hidden-import=codecs
    --hidden-import=select
    --hidden-import=signal
)

# Exclude unnecessary modules to reduce size
EXCLUDES=(
    --exclude-module=tkinter
    --exclude-module=unittest
    --exclude-module=email
    --exclude-module=http
    --exclude-module=xmlrpc
    --exclude-module=doctest
    --exclude-module=pydoc
)

COMMON_ARGS=(
    --name SOSterm
    --console
    --add-data "resources:resources"
    "${HIDDEN_IMPORTS[@]}"
    "${EXCLUDES[@]}"
    --noconfirm
    --strip
    main.py
)

if [ "$MODE" = "onefile" ]; then
    echo "Building SOSterm as single-file executable..."
    python3 -m PyInstaller --onefile "${COMMON_ARGS[@]}"
    echo ""
    echo "Build complete: dist/SOSterm"
    ls -lh dist/SOSterm
else
    echo "Building SOSterm as standalone directory..."
    python3 -m PyInstaller --onedir "${COMMON_ARGS[@]}"
    echo ""
    echo "Build complete: dist/SOSterm/"
    ls -lh dist/SOSterm/SOSterm
    du -sh dist/SOSterm/
fi
