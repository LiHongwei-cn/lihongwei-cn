#!/bin/bash
# MUNDO Agent v2.2.3 — macOS 双击启动器
# 同步逻辑静默执行，Terminal 只显示蒙多

SRC="$HOME/Desktop/lihongwei-cn/mundo-agent"
DST="$HOME/.hermes/mundo-agent"

# 确保目标目录存在
mkdir -p "$DST"

# 同步版本文件（如果源存在）
if [ -f "$SRC/version.txt" ] && [ -f "$DST/version.txt" ]; then
    SRC_VER=$(cat "$SRC/version.txt" | tr -d '[:space:]')
    DST_VER=$(cat "$DST/version.txt" | tr -d '[:space:]')

    if [ "$SRC_VER" != "$DST_VER" ]; then
        echo "  版本不同步: $DST_VER → $SRC_VER，正在同步..."

        # 同步核心 Python 文件
        for f in mundo.py core.py llm.py setup.py tools.py display.py memory.py memory_import.py agents.py delegation.py claude_integration.py codex_integration.py hermes_integration.py policy.py security_hardening.py skill_cloud.py github_skill_crawler.py skill_cloud_scheduler.py; do
            [ -f "$SRC/$f" ] && cp "$SRC/$f" "$DST/$f"
        done

        # 同步配置目录
        if [ -d "$SRC/config" ]; then
            mkdir -p "$DST/config"
            cp "$SRC/config/"*.json "$DST/config/" 2>/dev/null
            cp "$SRC/config/"*.conf "$DST/config/" 2>/dev/null
        fi

        # 同步版本和依赖
        [ -f "$SRC/version.txt" ] && cp "$SRC/version.txt" "$DST/version.txt"
        [ -f "$SRC/requirements.txt" ] && cp "$SRC/requirements.txt" "$DST/requirements.txt"

        echo "  同步完成！"
    fi
fi

# 确保 setup_complete 存在（如果用户已配置 API Key）
if [ ! -f "$DST/.setup_complete" ] && [ -f "$DST/.env" ]; then
    # 检查是否有 API Key 配置
    if grep -q "API_KEY" "$DST/.env" 2>/dev/null; then
        echo "xiaomi
mimo-v2.5-pro" > "$DST/.setup_complete"
    fi
fi

cd "$DST"
export PYTHONDONTWRITEBYTECODE=1
exec python3 mundo.py "$@"
