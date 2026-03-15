#!/bin/bash
# Build a portable, self-contained release tarball for SOSterm.
#
# Bundles the binary, all required shared libraries, Qt plugins,
# and QTermWidget data so it runs on any x86_64 Linux without
# needing to install any packages.
#
# Usage: ./release.sh
#
# Outputs:
#   dist/SOSterm-<version>.tar.gz   — distributable archive
#   dist/latest.json              — update server metadata
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Extract version from the C++ build header
VERSION_H="${SCRIPT_DIR}/cbuild/version.h"
if [ ! -f "$VERSION_H" ]; then
    echo "Error: $VERSION_H not found. Run cmake/make in cbuild/ first."
    exit 1
fi
VERSION=$(grep 'SOSTERM_VERSION "' "$VERSION_H" | head -1 | sed 's/.*"\(.*\)".*/\1/')

BINARY="${SCRIPT_DIR}/cbuild/SOSterm"
if [ ! -x "$BINARY" ]; then
    echo "Error: Compiled binary not found at $BINARY"
    echo "  Build first: cd cbuild && cmake .. && make -j\$(nproc)"
    exit 1
fi

echo "Building SOSterm v${VERSION} portable release..."

DIST_DIR="${SCRIPT_DIR}/dist"
RELEASE_NAME="SOSterm-${VERSION}"
STAGING="${DIST_DIR}/${RELEASE_NAME}"

# Clean previous staging
rm -rf "${STAGING}"
mkdir -p "${STAGING}/lib"
mkdir -p "${STAGING}/plugins/platforms"
mkdir -p "${STAGING}/resources"
mkdir -p "${STAGING}/colorschemes"
mkdir -p "${STAGING}/share/qtermwidget5/color-schemes"
mkdir -p "${STAGING}/share/qtermwidget5/kb-layouts"

# --- Binary ---
cp "${BINARY}" "${STAGING}/SOSterm.bin"
strip "${STAGING}/SOSterm.bin"

# --- Bundle shared libraries ---
# Copy all .so dependencies except core glibc/ld (those must come from the host)
SKIP_LIBS="linux-vdso|ld-linux|libc\.so|libm\.so|libdl\.so|libpthread|librt\.so"
echo "  Bundling shared libraries..."
ldd "${BINARY}" | grep "=>" | awk '{print $3}' | grep -vE "$SKIP_LIBS" | while read lib; do
    if [ -f "$lib" ]; then
        cp -L "$lib" "${STAGING}/lib/"
    fi
done

# --- Qt5 platform plugins (need at least xcb for X11, wayland for Wayland) ---
QT_PLUGINS=$(qmake -query QT_INSTALL_PLUGINS 2>/dev/null || echo "/usr/lib/x86_64-linux-gnu/qt5/plugins")
echo "  Bundling Qt platform plugins..."
for plugin in libqxcb.so libqwayland-generic.so libqwayland-egl.so; do
    if [ -f "${QT_PLUGINS}/platforms/${plugin}" ]; then
        cp -L "${QT_PLUGINS}/platforms/${plugin}" "${STAGING}/plugins/platforms/"
    fi
done

# Bundle xcb platform plugin dependencies
for lib in "${STAGING}/plugins/platforms/"*.so; do
    [ -f "$lib" ] || continue
    ldd "$lib" 2>/dev/null | grep "=>" | awk '{print $3}' | grep -vE "$SKIP_LIBS" | while read dep; do
        depname=$(basename "$dep")
        if [ -f "$dep" ] && [ ! -f "${STAGING}/lib/${depname}" ]; then
            cp -L "$dep" "${STAGING}/lib/"
        fi
    done
done

# --- QTermWidget data (color schemes, keyboard layouts) ---
QTERMWIDGET_DATA="/usr/share/qtermwidget5"
if [ -d "$QTERMWIDGET_DATA" ]; then
    echo "  Bundling QTermWidget data..."
    cp -a "${QTERMWIDGET_DATA}/color-schemes/"*.colorscheme "${STAGING}/share/qtermwidget5/color-schemes/" 2>/dev/null || true
    cp -a "${QTERMWIDGET_DATA}/kb-layouts/"*.keytab "${STAGING}/share/qtermwidget5/kb-layouts/" 2>/dev/null || true
fi

# --- App resources ---
cp "${SCRIPT_DIR}/resources/SOSterm.svg" "${STAGING}/resources/"
cp "${SCRIPT_DIR}/resources/sos-logo.png" "${STAGING}/resources/"
cp "${SCRIPT_DIR}/colorschemes/"*.colorscheme "${STAGING}/colorschemes/" 2>/dev/null || true

# --- Support files ---
cp "${SCRIPT_DIR}/SOSterm.desktop" "${STAGING}/"
cp "${SCRIPT_DIR}/uninstall.sh" "${STAGING}/"

# --- Launcher script (sets up library paths) ---
cat > "${STAGING}/SOSterm" << 'LAUNCHER'
#!/bin/bash
# Portable launcher — sets library paths so bundled .so files are found.
# Resolves symlinks so /usr/local/bin/SOSterm -> /opt/SOSterm/SOSterm works.
SELF="$0"
while [ -L "$SELF" ]; do
    DIR="$(cd "$(dirname "$SELF")" && pwd)"
    SELF="$(readlink "$SELF")"
    [[ "$SELF" != /* ]] && SELF="$DIR/$SELF"
done
SELF_DIR="$(cd "$(dirname "$SELF")" && pwd)"
export LD_LIBRARY_PATH="${SELF_DIR}/lib:${LD_LIBRARY_PATH}"
export QT_PLUGIN_PATH="${SELF_DIR}/plugins:${QT_PLUGIN_PATH}"
export XDG_DATA_DIRS="${SELF_DIR}/share:${XDG_DATA_DIRS:-/usr/share}"
exec "${SELF_DIR}/SOSterm.bin" "$@"
LAUNCHER
chmod +x "${STAGING}/SOSterm"

# --- Install script ---
cat > "${STAGING}/install.sh" << 'INSTALL'
#!/bin/bash
# SOSterm installer — installs portable bundle to /opt/SOSterm
set -e

APP_DIR="/opt/SOSterm"
BIN_LINK="/usr/local/bin/SOSterm"
DESKTOP_FILE="/usr/share/applications/SOSterm.desktop"
ICON_DIR="/usr/share/icons/hicolor"

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo ./install.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing SOSterm to ${APP_DIR}..."

# Remove old install
rm -rf "${APP_DIR}"

# Copy entire bundle
cp -a "${SCRIPT_DIR}" "${APP_DIR}"

# Create symlink
ln -sf "${APP_DIR}/SOSterm" "${BIN_LINK}"

# Install icon
if [ -f "${APP_DIR}/resources/SOSterm.svg" ]; then
    mkdir -p "${ICON_DIR}/scalable/apps"
    cp "${APP_DIR}/resources/SOSterm.svg" "${ICON_DIR}/scalable/apps/SOSterm.svg"
    if command -v rsvg-convert &>/dev/null; then
        for size in 16 24 32 48 64 128 256; do
            mkdir -p "${ICON_DIR}/${size}x${size}/apps"
            rsvg-convert -w "${size}" -h "${size}" \
                "${APP_DIR}/resources/SOSterm.svg" \
                -o "${ICON_DIR}/${size}x${size}/apps/SOSterm.png"
        done
        echo "  Generated PNG icons."
    fi
fi

# Install desktop file
if [ -f "${APP_DIR}/SOSterm.desktop" ]; then
    cp "${APP_DIR}/SOSterm.desktop" "${DESKTOP_FILE}"
fi

# Refresh caches
gtk-update-icon-cache -f -t "${ICON_DIR}" 2>/dev/null || true
update-desktop-database /usr/share/applications 2>/dev/null || true

echo ""
echo "SOSterm installed successfully!"
echo "  Command: SOSterm"
echo "  Menu:    Look for 'SOSterm' in your applications menu"
echo ""
echo "To uninstall: sudo /opt/SOSterm/uninstall.sh"
INSTALL
chmod +x "${STAGING}/install.sh"

# --- Create tarball ---
cd "${DIST_DIR}"
tar czf "${RELEASE_NAME}.tar.gz" "${RELEASE_NAME}/"
rm -rf "${STAGING}"

TARBALL="${DIST_DIR}/${RELEASE_NAME}.tar.gz"
SIZE=$(stat -c%s "${TARBALL}" 2>/dev/null || stat -f%z "${TARBALL}" 2>/dev/null)
SHA256=$(sha256sum "${TARBALL}" | cut -d' ' -f1)

# Generate latest.json
cat > "${DIST_DIR}/latest.json" << EOF
{
  "version": "${VERSION}",
  "download_url": "https://sos-tech.ca/updates/SOSterm/${RELEASE_NAME}.tar.gz",
  "changelog": "",
  "sha256": "${SHA256}",
  "size": ${SIZE},
  "min_version": "1.0.0"
}
EOF

echo ""
echo "Portable release built successfully:"
echo "  Tarball:     ${TARBALL}"
echo "  Size:        $(du -h "${TARBALL}" | cut -f1)"
echo "  SHA256:      ${SHA256}"
echo ""
echo "Deploy to update server:"
echo "  cp ${TARBALL} /mnt/sos-updates/SOSterm/"
echo "  cp ${DIST_DIR}/latest.json /mnt/sos-updates/SOSterm/"
