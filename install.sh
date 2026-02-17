#!/bin/bash
# fterm installer — installs to /opt/fterm with desktop integration
set -e

APP_DIR="/opt/fterm"
BIN_LINK="/usr/local/bin/fterm"
DESKTOP_FILE="/usr/share/applications/fterm.desktop"
ICON_DIR="/usr/share/icons/hicolor"

# Check for root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo ./install.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing fterm to ${APP_DIR}..."

# Install application files
mkdir -p "${APP_DIR}/resources"
cp "${SCRIPT_DIR}/main.py" "${APP_DIR}/"
cp "${SCRIPT_DIR}/mainwindow.py" "${APP_DIR}/"
cp "${SCRIPT_DIR}/terminal_widget.py" "${APP_DIR}/"
cp "${SCRIPT_DIR}/terminal_process.py" "${APP_DIR}/"
cp "${SCRIPT_DIR}/session_tab_manager.py" "${APP_DIR}/"
cp "${SCRIPT_DIR}/settings.py" "${APP_DIR}/"
cp "${SCRIPT_DIR}/themes.py" "${APP_DIR}/"
cp "${SCRIPT_DIR}/preferences_dialog.py" "${APP_DIR}/"
cp "${SCRIPT_DIR}/session_manager.py" "${APP_DIR}/"
cp "${SCRIPT_DIR}/requirements.txt" "${APP_DIR}/"
cp "${SCRIPT_DIR}/resources/fterm.svg" "${APP_DIR}/resources/"

# Create launcher script
cat > "${BIN_LINK}" << 'LAUNCHER'
#!/bin/bash
exec python3 /opt/fterm/main.py "$@"
LAUNCHER
chmod +x "${BIN_LINK}"

# Install icon at multiple sizes (SVG goes in scalable)
mkdir -p "${ICON_DIR}/scalable/apps"
cp "${SCRIPT_DIR}/resources/fterm.svg" "${ICON_DIR}/scalable/apps/fterm.svg"

# Generate PNG icons from SVG if rsvg-convert is available
if command -v rsvg-convert &>/dev/null; then
    for size in 16 24 32 48 64 128 256; do
        mkdir -p "${ICON_DIR}/${size}x${size}/apps"
        rsvg-convert -w "${size}" -h "${size}" \
            "${SCRIPT_DIR}/resources/fterm.svg" \
            -o "${ICON_DIR}/${size}x${size}/apps/fterm.png"
    done
    echo "  Generated PNG icons at multiple sizes."
else
    echo "  Note: Install librsvg2-bin for PNG icon generation (optional)."
fi

# Install desktop file
cp "${SCRIPT_DIR}/fterm.desktop" "${DESKTOP_FILE}"

# Update icon cache and desktop database
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t "${ICON_DIR}" 2>/dev/null || true
fi
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi

echo ""
echo "fterm installed successfully!"
echo "  Application: ${APP_DIR}"
echo "  Command:     fterm"
echo "  Menu:        Look for 'fterm' in your applications menu"
echo ""
echo "To uninstall: sudo /opt/fterm/uninstall.sh"
