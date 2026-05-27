#!/bin/bash
# {{PROJECT_NAME}} 一键启动器 (macOS)
# 用法：双击 .command 文件

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LAUNCHER_URL="{{LAUNCHER_URL}}"

echo "========================================"
echo "  {{PROJECT_TITLE}}"
echo "========================================"
echo ""

# 检测应用安装
APP=""
for candidate in {{APP_CANDIDATES}}; do
  if [ -f "$candidate" ]; then
    APP="$candidate"
    break
  fi
done

if [ -z "$APP" ]; then
  echo "[X] 未检测到 {{APP_NAME}} 安装"
  echo ""
  echo "  1) 打开启动器网页"
  echo "  2) 手动操作说明"
  echo "  3) 退出"
  read -p "选项 [1-3]: " choice
  case $choice in
    1) open "$LAUNCHER_URL" ;;
    2) echo "{{MANUAL_INSTRUCTIONS}}" ;;
  esac
  exit 0
fi

echo "[OK] {{APP_NAME}}: $APP"
echo ""
echo "请选择："
echo "  1) {{MENU_OPTION_1}}"
echo "  2) {{MENU_OPTION_2}}"
echo "  3) {{MENU_OPTION_3}}"
echo "  4) 查看帮助"
echo "  5) 退出"
read -p "选项 [1-5]: " choice

case $choice in
  1) {{ACTION_1}} ;;
  2) {{ACTION_2}} ;;
  3) {{ACTION_3}} ;;
  4) echo "{{HELP_TEXT}}" ;;
esac
