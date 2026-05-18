#!/bin/bash
# 设置 Telegram Bot 在 macOS 上开机自启
# Run: chmod +x setup_login_start.sh && ./setup_login_start.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMMAND_FILE="$SCRIPT_DIR/start_bot.command"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$PLIST_DIR/com.lihongwei.tgbot.plist"

if [ ! -f "$COMMAND_FILE" ]; then
    echo "ERROR: 找不到 start_bot.command"
    exit 1
fi

chmod +x "$COMMAND_FILE"

mkdir -p "$PLIST_DIR"

cat > "$PLIST_FILE" << PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.lihongwei.tgbot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$COMMAND_FILE</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/tgbot.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/tgbot.err</string>
</dict>
</plist>
PLISTEOF

launchctl load "$PLIST_FILE" 2>/dev/null && echo "已设置开机自启并立即启动。" || echo "已创建 LaunchAgent 配置，重启后生效。"
echo "配置文件: $PLIST_FILE"
echo "取消自启: launchctl unload $PLIST_FILE && rm $PLIST_FILE"
