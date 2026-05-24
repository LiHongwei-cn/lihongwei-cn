# Hermes Agent 一键启动器

<img src="hermes-logo.png" alt="Hermes Agent" width="120" style="border-radius:24px;box-shadow:0 8px 32px rgba(0,0,0,0.3)">

Nous Research 开源 AI Agent，Win / Mac 双击即用。支持 OpenRouter / OpenAI / Anthropic / DeepSeek 等多种模型后端。

## 下载

| 平台 | 下载 |
|------|------|
| Windows | [hermes-start.bat](https://raw.githubusercontent.com/LiHongwei-cn/lihongwei-cn/main/tools/hermes-start.bat) |
| macOS | [hermes-desktop.command](https://raw.githubusercontent.com/LiHongwei-cn/lihongwei-cn/main/tools/hermes-desktop.command) |

右键另存为，放到工作目录，双击即可。

### macOS Dock 固定（可选）

将以下命令复制到终端运行，自动创建 `.app` 并加入程序坞：

```bash
mkdir -p ~/Applications/hermes.app/Contents/MacOS ~/Applications/hermes.app/Contents/Resources
cat > ~/Applications/hermes.app/Contents/Info.plist << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleExecutable</key><string>hermes-launcher</string>
  <key>CFBundleIdentifier</key><string>com.lihongwei.hermes-agent</string>
  <key>CFBundleName</key><string>Hermes Agent</string>
  <key>CFBundlePackageType</key><string>APPL</string>
</dict></plist>
PLIST
cat > ~/Applications/hermes.app/Contents/MacOS/hermes-launcher << 'SH'
#!/bin/bash
H="$HOME/.local/bin/hermes"
[ ! -f "$H" ] && osascript -e 'display dialog "Hermes Agent 未安装" buttons {"好"} with icon stop' && exit 1
[ ! -f "$HOME/.hermes/.env" ] && osascript -e 'display dialog "请先运行：hermes setup" buttons {"好"} with icon caution' && exit 1
osascript -e 'tell app "Terminal" to activate' -e "tell app \"Terminal\" to do script \"clear; $H chat; exit\""
SH
chmod +x ~/Applications/hermes.app/Contents/MacOS/hermes-launcher
```

运行后打开 Finder → 前往 `~/Applications` → 将 `hermes.app` 拖入程序坞即可。

## 工作原理

```
hermes-start → 检测 hermes 命令 → 检查 API Key 配置 → 打开 Hermes Agent 对话
```

任一步失败都有明确的中文提示。

## 前置条件

### 1. 安装 Hermes Agent

**macOS / Linux：**
```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

**Windows（PowerShell）：**
```powershell
iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
```

安装完成后重启终端，确认 `hermes` 命令可用。

### 2. 配置 API Key

```bash
hermes setup
```

交互式配置向导，支持 OpenRouter、OpenAI、Anthropic、DeepSeek、HuggingFace 等。密钥保存在 `~/.hermes/.env`。

推荐 OpenRouter（200+ 模型，免费注册）。

## Hermes Agent 简介

- **自我进化**：从经验中创建技能、跨会话建立用户模型
- **多模型后端**：OpenRouter / OpenAI / Anthropic / DeepSeek / HuggingFace / Google
- **89 个内置技能**：浏览器自动化、GitHub 管理、论文写作、Notion/Linear 集成
- **消息平台接入**：Telegram、Discord、Slack、WhatsApp、Signal

## 自定义配置

用文本编辑器打开启动脚本，可按需修改：

```bash
# 指定模型和提供商
hermes chat --model "openai/gpt-5" --provider openrouter

# TUI 模式（界面更美观）
hermes --tui
```

## 常见问题

### 提示 hermes 命令未找到
```bash
source ~/.zshrc    # 或 source ~/.bashrc
```
仍未解决：重新运行安装脚本。

### 提示未检测到 API Key
运行 `hermes setup`，至少配置一个模型提供商。

### 如何更新
```bash
hermes update
```

### 如何卸载
```bash
hermes uninstall
```

### macOS 提示无法验证开发者
右键（Control+点击）`.command` 文件 → 打开 → 点"打开"。只需操作一次。

## 详情

[Hermes 启动器项目页面](https://lihongwei-cn.github.io/lihongwei-cn/hermes-launcher/) · [Hermes Agent 项目](https://github.com/NousResearch/hermes-agent)
