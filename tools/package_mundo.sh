#!/usr/bin/env bash
# package_mundo.sh — Build Mundo release zips.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION="${1:?Usage: package_mundo.sh <version>}"
OUT_DIR="$REPO_ROOT/mundo-cloud/dist/$VERSION"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

# collect files
STAGING=$(mktemp -d)
cp -r "$REPO_ROOT/mundo-cloud/skills/mundo" "$STAGING/mundo"
cp -r "$REPO_ROOT/mundo-cloud/scripts" "$STAGING/mundo/scripts"
cp -r "$REPO_ROOT/mundo-cloud/sync" "$STAGING/mundo/sync"
cp "$REPO_ROOT/mundo-cloud/README.md" "$STAGING/mundo/"

# cross-platform install scripts
cat > "$STAGING/mundo/install.sh" << 'INSTALLEOF'
#!/usr/bin/env bash
set -euo pipefail
TARGET="$HOME/.hermes/skills/mundo"
mkdir -p "$TARGET"
cp -r "$(dirname "$0")/SKILL.md" "$TARGET/"
cp -r "$(dirname "$0")/references" "$TARGET/" 2>/dev/null || true
echo "Mundo installed to $TARGET"
echo "Restart Hermes to activate."
INSTALLEOF
chmod +x "$STAGING/mundo/install.sh"

cat > "$STAGING/mundo/install.bat" << 'INSTALLEOF'
@echo off
set TARGET=%USERPROFILE%\.hermes\skills\mundo
if not exist "%TARGET%" mkdir "%TARGET%"
copy /Y "%~dp0SKILL.md" "%TARGET%\"
if exist "%~dp0references" xcopy /E /I /Y "%~dp0references" "%TARGET%\references"
echo Mundo installed to %TARGET%
echo Restart Hermes to activate.
INSTALLEOF

# create zips (content is identical, naming for platform discoverability)
for platform in macos windows linux; do
    zip_name="mundo-${VERSION}-${platform}.zip"
    (cd "$STAGING" && zip -r "$OUT_DIR/$zip_name" mundo/)
done

# cleanup
rm -rf "$STAGING"

echo "Built:"
ls -lh "$OUT_DIR"
