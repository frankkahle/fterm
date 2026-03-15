#!/bin/bash
# SOSterm uninstaller
set -e

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo ./uninstall.sh"
    exit 1
fi

echo "Uninstalling SOSterm..."

rm -rf /opt/SOSterm
rm -f /usr/local/bin/SOSterm
rm -f /usr/share/applications/SOSterm.desktop
rm -f /usr/share/icons/hicolor/scalable/apps/SOSterm.svg
for size in 16 24 32 48 64 128 256; do
    rm -f "/usr/share/icons/hicolor/${size}x${size}/apps/SOSterm.png"
done

if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
fi
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi

echo "SOSterm uninstalled."
