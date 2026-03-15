#!/bin/bash
set -e

INSTALL_DIR="/opt/SOSterm"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_DIR/cbuild"

# Check for root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./scripts/install.sh)"
    exit 1
fi

# Build if needed
if [ ! -f "$BUILD_DIR/SOSterm" ]; then
    echo "Building SOSterm..."
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"
    cmake "$PROJECT_DIR"
    make -j"$(nproc)"
    cd "$PROJECT_DIR"
fi

echo "Installing SOSterm to $INSTALL_DIR..."

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/colorschemes"
mkdir -p "$INSTALL_DIR/resources"

# Install binary
install -m 755 "$BUILD_DIR/SOSterm" "$INSTALL_DIR/SOSterm"

# Install colorschemes
cp "$PROJECT_DIR"/colorschemes/*.colorscheme "$INSTALL_DIR/colorschemes/"

# Install resources
cp "$PROJECT_DIR"/resources/SOSterm.svg "$INSTALL_DIR/resources/"
cp "$PROJECT_DIR"/resources/sos-logo.png "$INSTALL_DIR/resources/"

# Install desktop entry and icon
install -Dm 644 "$PROJECT_DIR/SOSterm.desktop" /usr/share/applications/SOSterm.desktop
install -Dm 644 "$PROJECT_DIR/resources/SOSterm.svg" /usr/share/icons/hicolor/scalable/apps/SOSterm.svg

# Create symlink in PATH
ln -sf "$INSTALL_DIR/SOSterm" /usr/local/bin/SOSterm

echo "SOSterm installed successfully to $INSTALL_DIR"
echo "Run 'SOSterm' to start."
