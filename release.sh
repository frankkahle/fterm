#!/bin/bash
# Build a release tarball and server metadata for fterm.
#
# Usage: ./release.sh
#
# Outputs:
#   dist/fterm-<version>.tar.gz   — distributable archive
#   dist/latest.json              — upload to https://sos-tech.ca/updates/fterm/
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Extract version from main.py
VERSION=$(python3 -c "
import re, sys
with open('${SCRIPT_DIR}/main.py') as f:
    m = re.search(r'VERSION\s*=\s*\"(.+?)\"', f.read())
    print(m.group(1) if m else '')
")

if [ -z "$VERSION" ]; then
    echo "Error: Could not extract VERSION from main.py"
    exit 1
fi

echo "Building fterm v${VERSION} release..."

DIST_DIR="${SCRIPT_DIR}/dist"
RELEASE_NAME="fterm-${VERSION}"
STAGING="${DIST_DIR}/${RELEASE_NAME}"

# Clean previous staging
rm -rf "${STAGING}"
mkdir -p "${STAGING}/resources"

# Copy source files
SOURCE_FILES=(
    main.py mainwindow.py terminal_widget.py terminal_process.py
    session_tab_manager.py settings.py themes.py preferences_dialog.py
    session_manager.py find_bar.py ssh_session_store.py ssh_sidebar.py
    ssh_dialogs.py update_checker.py requirements.txt
    install.sh uninstall.sh
)

for f in "${SOURCE_FILES[@]}"; do
    cp "${SCRIPT_DIR}/${f}" "${STAGING}/"
done

# Copy resources
cp "${SCRIPT_DIR}/resources/fterm.svg" "${STAGING}/resources/"
if [ -f "${SCRIPT_DIR}/fterm.desktop" ]; then
    cp "${SCRIPT_DIR}/fterm.desktop" "${STAGING}/"
fi

# Copy build script if present
if [ -f "${SCRIPT_DIR}/build.sh" ]; then
    cp "${SCRIPT_DIR}/build.sh" "${STAGING}/"
fi

# Create tarball
cd "${DIST_DIR}"
tar czf "${RELEASE_NAME}.tar.gz" "${RELEASE_NAME}/"
rm -rf "${STAGING}"

TARBALL="${DIST_DIR}/${RELEASE_NAME}.tar.gz"
SIZE=$(stat -c%s "${TARBALL}" 2>/dev/null || stat -f%z "${TARBALL}" 2>/dev/null)
SHA256=$(sha256sum "${TARBALL}" | cut -d' ' -f1)

# Generate latest.json for the update server
cat > "${DIST_DIR}/latest.json" << EOF
{
  "version": "${VERSION}",
  "download_url": "https://sos-tech.ca/updates/fterm/${RELEASE_NAME}.tar.gz",
  "changelog": "",
  "sha256": "${SHA256}",
  "size": ${SIZE},
  "min_version": "1.0.0"
}
EOF

echo ""
echo "Release built successfully:"
echo "  Tarball:     ${TARBALL}"
echo "  Size:        ${SIZE} bytes"
echo "  SHA256:      ${SHA256}"
echo ""
echo "Server files to upload to https://sos-tech.ca/updates/fterm/:"
echo "  1. ${TARBALL}"
echo "  2. ${DIST_DIR}/latest.json"
echo ""
echo "Upload commands:"
echo "  scp ${TARBALL} server:/var/www/sos-tech.ca/updates/fterm/"
echo "  scp ${DIST_DIR}/latest.json server:/var/www/sos-tech.ca/updates/fterm/"
