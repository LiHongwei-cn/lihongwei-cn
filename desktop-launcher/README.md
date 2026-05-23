# Claude Code 桌面快捷启动

Win / Mac 一键创建 Claude Code 桌面快捷方式，双击即开即用。无需每次打开终端输命令。

## 下载

| 平台 | 方式 |
|------|------|
| macOS | `tools/Claude Code.app` — 拖入 Dock 即可 |
| Windows | [claude-desktop.bat](https://raw.githubusercontent.com/LiHongwei-cn/lihongwei-cn/main/tools/claude-desktop.bat) |

## macOS 使用

1. 在 `tools/Claude Code.app` 找到启动器
2. 拖入 Dock 右侧固定
3. 点击图标即可启动 Claude Code 对话

首次打开提示"无法验证开发者"→ Finder 中右键 .app → 打开 → 确认。只需一次。

## Windows 使用

1. 下载 `claude-desktop.bat` 放到项目目录
2. 双击启动（自动检测 Windows Terminal）
3. 右键 → 发送到桌面可创建快捷方式

## 常见问题

### macOS：点击后 claude 命令未找到
确认 `~/.zshrc` 包含 `export PATH="$HOME/.local/bin:$PATH"`。

### macOS：Terminal 一闪而过
终端手动输入 `claude --version` 确认已安装。

### Windows：弹出旧式黑窗口
Microsoft Store 搜索安装 Windows Terminal（免费）。

## 详情

[桌面启动项目页面](https://lihongwei-cn.github.io/lihongwei-cn/desktop-launcher/)
