#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./scripts/uninstall.sh)"
    exit 1
fi

echo "Uninstalling SOSterm..."

rm -rf /opt/SOSterm
rm -f /usr/local/bin/SOSterm
rm -f /usr/share/applications/SOSterm.desktop
rm -f /usr/share/icons/hicolor/scalable/apps/SOSterm.svg

echo "SOSterm uninstalled."
