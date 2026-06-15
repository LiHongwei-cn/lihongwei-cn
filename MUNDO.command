#!/bin/bash
# MUNDO Agent v2.2.4 — macOS 双击启动器
# 同步逻辑静默执行，Terminal 只显示蒙多
# v2.2.4: 修复同步源路径 + 全量文件同步（不再硬编码文件列表）

# 优先使用完整源目录（含所有模块），回退到核心目录
SRC_FULL="$HOME/Desktop/lihongwei-cn/Desktop/lihongwei-cn/mundo-agent"
SRC_CORE="$HOME/Desktop/lihongwei-cn/mundo-agent"
DST="$HOME/.hermes/mundo-agent"

# 选择实际存在的源目录
if [ -d "$SRC_FULL" ] && [ -f "$SRC_FULL/version.txt" ]; then
    SRC="$SRC_FULL"
elif [ -d "$SRC_CORE" ] && [ -f "$SRC_CORE/version.txt" ]; then
    SRC="$SRC_CORE"
else
    # 无源目录，直接启动（已安装版本）
    cd "$DST" 2>/dev/null || { echo "错误: 找不到蒙多安装目录"; exit 1; }
    export PYTHONDONTWRITEBYTECODE=1
    exec python3 mundo.py "$@"
fi

# 确保目标目录存在
mkdir -p "$DST"

# 同步版本文件
if [ -f "$DST/version.txt" ]; then
    SRC_VER=$(cat "$SRC/version.txt" | tr -d '[:space:]')
    DST_VER=$(cat "$DST/version.txt" | tr -d '[:space:]')

    if [ "$SRC_VER" != "$DST_VER" ]; then
        echo "  版本不同步: $DST_VER → $SRC_VER，正在同步..."

        # 全量同步所有 Python 文件（不再硬编码列表）
        cp "$SRC/"*.py "$DST/" 2>/dev/null

        # 同步配置目录
        if [ -d "$SRC/config" ]; then
            mkdir -p "$DST/config"
            cp "$SRC/config/"*.json "$DST/config/" 2>/dev/null
            cp "$SRC/config/"*.conf "$DST/config/" 2>/dev/null
        fi

        # 同步 skill_store 目录
        if [ -d "$SRC/skill_store" ]; then
            mkdir -p "$DST/skill_store"
            cp -R "$SRC/skill_store/" "$DST/skill_store/" 2>/dev/null
        fi

        # 同步版本和依赖
        [ -f "$SRC/version.txt" ] && cp "$SRC/version.txt" "$DST/version.txt"
        [ -f "$SRC/requirements.txt" ] && cp "$SRC/requirements.txt" "$DST/requirements.txt"

        echo "  同步完成！"
    fi
fi

# 确保 setup_complete 存在（如果用户已配置 API Key）
if [ ! -f "$DST/.setup_complete" ] && [ -f "$DST/.env" ]; then
    if grep -q "API_KEY" "$DST/.env" 2>/dev/null; then
        echo "xiaomi
mimo-v2.5-pro" > "$DST/.setup_complete"
    fi
fi

cd "$DST"
export PYTHONDONTWRITEBYTECODE=1
exec python3 mundo.py "$@"
