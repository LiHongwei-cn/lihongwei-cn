---
name: macos-troubleshooting
description: 诊断和修复 macOS 应用崩溃、系统异常。读取 crash logs、识别根因、应用针对性修复。覆盖 Terminal.app、系统偏好设置损坏、持久化状态异常等常见场景。
triggers:
  - 终端闪退/崩溃
  - 应用闪退
  - 崩溃日志/crash log
  - EXC_BAD_ACCESS/SIGBUS/SIGSEGV
  - DiagnosticReports
  - 系统异常/不稳定
  - mac crash/terminal crash
---

# macOS 应用崩溃诊断与修复

## 通用诊断流程

### 1. 定位崩溃日志

```bash
# 最近的崩溃报告（当前用户）
ls -lt ~/Library/Logs/DiagnosticReports/*.ips | head -10

# 已归档的崩溃报告
ls -lt ~/Library/Logs/DiagnosticReports/Retired/*.ips | head -10

# 按应用名过滤
find ~/Library/Logs/DiagnosticReports -name "*Terminal*" -o -name "*Safari*"
```

### 2. 读取崩溃摘要

`.ips` 文件是 JSON 格式。关键字段：

```bash
# 提取崩溃摘要（前 3 行包含 app_name、exception、termination）
head -3 ~/Library/Logs/DiagnosticReports/AppName-*.ips | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line)
        if 'exception' in d:
            print(f\"异常: {d['exception']['type']} / {d['exception']['signal']}\")
        if 'termination' in d:
            print(f\"终止: {d['termination']['indicator']}\")
    except: pass
"
```

### 3. 识别崩溃模式

| 调用栈关键词 | 含义 | 修复方向 |
|-------------|------|---------|
| `restoreWindowWithIdentifier` / `NSPersistentUIManager` | 窗口状态恢复损坏 | 清除 savedState + 关闭窗口恢复 |
| `_platform_memmove` / `EXC_BAD_ACCESS` | 内存访问越界/野指针 | 通常是状态文件损坏 |
| `objc_msgSend` | 消息发送到已释放对象 | 通常是 plist 损坏 |
| `dyld` / `Library not loaded` | 动态库缺失 | 重装应用或修复 dyld 缓存 |
| `SIGKILL` / `jetsam` | 内存不足被杀 | 检查内存压力 + 关闭后台应用 |

### 4. 应用修复

根据崩溃模式选择修复策略。详见 `references/crash-patterns.md`。

## 常用诊断命令

```bash
# 内存压力
memory_pressure 2>/dev/null || vm_stat

# 磁盘空间
df -h /

# 应用 preferences 检查
plutil -lint ~/Library/Preferences/com.apple.AppName.plist

# 清除应用持久化状态
defaults write com.apple.AppName NSQuitAlwaysKeepsWindows -bool false

# 查看应用 preferences 内容
defaults read com.apple.AppName | head -30

# 搜索 Saved Application State
find ~/Library -name "*.savedState" -type d

# 重置应用 preferences（核武器选项）
defaults delete com.apple.AppName
```

## 已记录的崩溃模式

- **Terminal.app 窗口恢复崩溃** → `references/terminal-crash-window-restore.md`
- **通用崩溃调试流程** — 适用于任何 macOS 原生应用（Terminal、Finder、Safari、系统偏好设置等）：
  1. `find ~/Library/Logs/DiagnosticReports -name "*<AppName>*" -type f | sort -r | head -5` — 查找崩溃报告
  2. 解析 `.ips` JSON：`exception.type`（EXC_BAD_ACCESS=内存越界）、`termination.code`（11=SIGSEGV）、`faultingThread`
  3. 匹配崩溃模式表（上方）选择修复策略
  4. 常见 bundle-id：Terminal=`com.apple.Terminal`、Finder=`com.apple.finder`、Safari=`com.apple.Safari`

## Pitfalls

- **不要直接删除 plist 而不先备份**：`cp foo.plist foo.plist.bak`
- **崩溃日志的 `procLaunch` 和 `captureTime` 间隔极短（<5秒）= 启动时崩溃**，不是使用中崩溃
- **连续多次崩溃（同一秒内 3-5 个 .ips）= 崩溃→自动重启→再崩溃循环**
- **`_platform_memmove` 几乎总是状态文件损坏**，不是内存硬件问题
- **`NSQuitAlwaysKeepsWindows = false` 代价是丢失窗口位置**，但比闪退强
- **macOS 26+ 的 Saved Application State 路径可能与旧版不同**，用 `find` 全盘搜
