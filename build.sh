#!/bin/bash
# Build fterm as a compiled binary using PyInstaller.
#
# Usage:
#   ./build.sh          # Build onedir (fast startup, dist/fterm/ folder)
#   ./build.sh onefile  # Build single-file (one executable, slower startup)
#
# Requirements:
#   pip install pyinstaller

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

MODE="${1:-onedir}"

COMMON_ARGS=(
    --name fterm
    --windowed
    --add-data "resources:resources"
    --hidden-import=pyte
    --hidden-import=ptyprocess
    --hidden-import=wcwidth
    --hidden-import=configparser
    --hidden-import=PyQt5.sip
    --noconfirm
    main.py
)

if [ "$MODE" = "onefile" ]; then
    echo "Building fterm as single-file executable..."
    python3 -m PyInstaller --onefile "${COMMON_ARGS[@]}"
    echo ""
    echo "Build complete: dist/fterm"
    ls -lh dist/fterm
else
    echo "Building fterm as standalone directory..."
    python3 -m PyInstaller --onedir "${COMMON_ARGS[@]}"
    echo ""
    echo "Build complete: dist/fterm/"
    ls -lh dist/fterm/fterm
    du -sh dist/fterm/
fi
