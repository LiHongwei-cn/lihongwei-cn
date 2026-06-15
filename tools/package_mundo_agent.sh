#!/usr/bin/env bash
# package_mundo_agent.sh — 打包 MUNDO Agent 发布版
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION="${1:?用法: package_mundo_agent.sh <version>}"
OUT_DIR="$REPO_ROOT/mundo-cloud/dist/$VERSION"
AGENT_DIR="$REPO_ROOT/mundo-agent"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

# 收集文件
STAGING=$(mktemp -d)
mkdir -p "$STAGING/mundo-agent"

# 核心 Python 文件
CORE_FILES=(
    "mundo.py"
    "core.py"
    "llm.py"
    "tools.py"
    "memory.py"
    "memory_import.py"
    "setup.py"
    "display.py"
    "agents.py"
    "delegation.py"
    "hermes_integration.py"
    "claude_integration.py"
    "codex_integration.py"
    "policy.py"
    "security_hardening.py"
    "skill_cloud.py"
    "github_skill_crawler.py"
    "skill_cloud_scheduler.py"
    "version.txt"
    "requirements.txt"
)

for file in "${CORE_FILES[@]}"; do
    if [ -f "$AGENT_DIR/$file" ]; then
        cp "$AGENT_DIR/$file" "$STAGING/mundo-agent/"
    fi
done

# 复制 skills 目录（如果存在）
if [ -d "$AGENT_DIR/skills" ]; then
    cp -r "$AGENT_DIR/skills" "$STAGING/mundo-agent/"
fi

# 创建跨平台安装脚本
cat > "$STAGING/mundo-agent/install.sh" << 'INSTALLEOF'
#!/usr/bin/env bash
set -euo pipefail
TARGET="$HOME/.hermes/mundo-agent"
mkdir -p "$TARGET"
cp -r "$(dirname "$0")/"* "$TARGET/"
cd "$TARGET"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "MUNDO Agent installed to $TARGET"
echo "Run: python3 $TARGET/mundo.py"
INSTALLEOF
chmod +x "$STAGING/mundo-agent/install.sh"

cat > "$STAGING/mundo-agent/install.bat" << 'INSTALLEOF'
@echo off
set TARGET=%USERPROFILE%\.hermes\mundo-agent
if not exist "%TARGET%" mkdir "%TARGET%"
xcopy /E /I /Y "%~dp0*" "%TARGET%"
cd /d "%TARGET%"
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
echo MUNDO Agent installed to %TARGET%
echo Run: python %TARGET%\mundo.py
INSTALLEOF

# 创建启动脚本
cat > "$STAGING/mundo-agent/run.sh" << 'RUNEOF'
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
if [ -d "venv" ]; then
    source venv/bin/activate
fi
python3 mundo.py "$@"
RUNEOF
chmod +x "$STAGING/mundo-agent/run.sh"

cat > "$STAGING/mundo-agent/run.bat" << 'RUNEOF'
@echo off
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"
if exist "venv\Scripts\activate.bat" call venv\Scripts\activate.bat
python mundo.py %*
RUNEOF

# 创建 zips
for platform in macos windows linux; do
    zip_name="mundo-agent-${VERSION}-${platform}.zip"
    (cd "$STAGING" && zip -r "$OUT_DIR/$zip_name" mundo-agent/)
done

# 创建全平台包
(cd "$STAGING" && zip -r "$OUT_DIR/mundo-agent-${VERSION}-all.zip" mundo-agent/)

# 清理
rm -rf "$STAGING"

echo "打包完成: $OUT_DIR"
ls -la "$OUT_DIR"
