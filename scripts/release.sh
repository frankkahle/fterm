#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_DIR/cbuild"

# Extract version from CMakeLists.txt
VERSION=$(grep 'project(SOSterm VERSION' "$PROJECT_DIR/CMakeLists.txt" | sed 's/.*VERSION \([^ ]*\).*/\1/')
if [ -z "$VERSION" ]; then
    echo "Could not determine version"
    exit 1
fi

echo "Building SOSterm v$VERSION..."

# Build
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"
cmake "$PROJECT_DIR" -DCMAKE_BUILD_TYPE=Release
make -j"$(nproc)"

# Create dist directory
DIST_DIR="$PROJECT_DIR/dist"
TARBALL_NAME="SOSterm-${VERSION}-linux-x86_64"
STAGING="$DIST_DIR/$TARBALL_NAME"

rm -rf "$STAGING"
mkdir -p "$STAGING"
mkdir -p "$STAGING/colorschemes"
mkdir -p "$STAGING/resources"
mkdir -p "$STAGING/scripts"

# Copy files
cp "$BUILD_DIR/SOSterm" "$STAGING/"
cp "$PROJECT_DIR"/colorschemes/*.colorscheme "$STAGING/colorschemes/"
cp "$PROJECT_DIR"/resources/SOSterm.svg "$STAGING/resources/"
cp "$PROJECT_DIR"/resources/sos-logo.png "$STAGING/resources/"
cp "$PROJECT_DIR"/scripts/install.sh "$STAGING/scripts/"
cp "$PROJECT_DIR"/scripts/uninstall.sh "$STAGING/scripts/"
cp "$PROJECT_DIR"/SOSterm.desktop "$STAGING/"

# Create tarball
cd "$DIST_DIR"
tar czf "${TARBALL_NAME}.tar.gz" "$TARBALL_NAME"
rm -rf "$STAGING"

echo ""
echo "Release built: dist/${TARBALL_NAME}.tar.gz"
echo ""

# Generate latest.json template
cat > "$DIST_DIR/latest.json" <<JSONEOF
{
  "version": "$VERSION",
  "download_url": "",
  "changelog": ""
}
JSONEOF

echo "Edit dist/latest.json with changelog and download URL."
echo "Then deploy to /mnt/sos-updates/fterm/"
