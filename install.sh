#!/bin/bash
# SOSterm installer — installs to /opt/SOSterm with desktop integration
set -e

APP_DIR="/opt/SOSterm"
BIN_LINK="/usr/local/bin/SOSterm"
DESKTOP_FILE="/usr/share/applications/SOSterm.desktop"
ICON_DIR="/usr/share/icons/hicolor"

# Check for root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo ./install.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing SOSterm to ${APP_DIR}..."

# Detect which build is available
BINARY=""
if [ -x "${SCRIPT_DIR}/cbuild/SOSterm" ]; then
    BINARY="${SCRIPT_DIR}/cbuild/SOSterm"
    echo "  Using C++ build (cbuild/SOSterm)..."
elif [ -x "${SCRIPT_DIR}/SOSterm" ]; then
    # Release tarball: binary is in the same directory
    BINARY="${SCRIPT_DIR}/SOSterm"
    echo "  Using packaged binary..."
else
    echo "Error: No compiled SOSterm binary found."
    echo "  Build first: cd cbuild && cmake .. && make -j\$(nproc)"
    exit 1
fi

# Install
rm -rf "${APP_DIR}"
mkdir -p "${APP_DIR}/resources" "${APP_DIR}/colorschemes"

cp "${BINARY}" "${APP_DIR}/SOSterm"
chmod +x "${APP_DIR}/SOSterm"

# Copy resources
if [ -d "${SCRIPT_DIR}/resources" ]; then
    cp -a "${SCRIPT_DIR}/resources/"* "${APP_DIR}/resources/" 2>/dev/null || true
fi

# Copy colorschemes
if [ -d "${SCRIPT_DIR}/colorschemes" ]; then
    cp "${SCRIPT_DIR}/colorschemes/"*.colorscheme "${APP_DIR}/colorschemes/" 2>/dev/null || true
fi

# Copy uninstall script
cp "${SCRIPT_DIR}/uninstall.sh" "${APP_DIR}/" 2>/dev/null || true

# Create launcher symlink
ln -sf "${APP_DIR}/SOSterm" "${BIN_LINK}"

# Install icon at multiple sizes (SVG goes in scalable)
if [ -f "${SCRIPT_DIR}/resources/SOSterm.svg" ]; then
    mkdir -p "${ICON_DIR}/scalable/apps"
    cp "${SCRIPT_DIR}/resources/SOSterm.svg" "${ICON_DIR}/scalable/apps/SOSterm.svg"

    # Generate PNG icons from SVG if rsvg-convert is available
    if command -v rsvg-convert &>/dev/null; then
        for size in 16 24 32 48 64 128 256; do
            mkdir -p "${ICON_DIR}/${size}x${size}/apps"
            rsvg-convert -w "${size}" -h "${size}" \
                "${SCRIPT_DIR}/resources/SOSterm.svg" \
                -o "${ICON_DIR}/${size}x${size}/apps/SOSterm.png"
        done
        echo "  Generated PNG icons at multiple sizes."
    fi
fi

# Install desktop file
if [ -f "${SCRIPT_DIR}/SOSterm.desktop" ]; then
    cp "${SCRIPT_DIR}/SOSterm.desktop" "${DESKTOP_FILE}"
fi

# Update icon cache and desktop database
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t "${ICON_DIR}" 2>/dev/null || true
fi
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi

echo ""
echo "SOSterm installed successfully!"
echo "  Application: ${APP_DIR}"
echo "  Command:     SOSterm"
echo "  Menu:        Look for 'SOSterm' in your applications menu"
echo ""
echo "To uninstall: sudo /opt/SOSterm/uninstall.sh"
