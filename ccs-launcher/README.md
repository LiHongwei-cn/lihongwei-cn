# CCS 一键启动器

Claude Code 接入 DeepSeek，Win / Mac 双击即用。自动检测 CCS 代理、自动读取密钥、自动启动对话。

## 下载

| 平台 | 下载 |
|------|------|
| Windows | [claude-start.bat](https://raw.githubusercontent.com/LiHongwei-cn/lihongwei-cn/main/tools/claude-start.bat) |
| macOS | [claude-desktop.command](https://raw.githubusercontent.com/LiHongwei-cn/lihongwei-cn/main/tools/claude-desktop.command) |

右键另存为，放到工作目录，双击即可。

## 工作原理

```
claude-start → 检测 claude 命令 → 读取环境变量密钥 → 启动 CCS 代理 → 打开 Claude Code
```

任一步失败都有明确的中文提示。

## 前置条件

### 1. 安装 Claude Code

需要 Node.js 18+：

```bash
npm install -g @anthropic-ai/claude-code
```

### 2. 安装 CCS 代理

将 CCS 项目放到工作目录下，确保有 `server.js`、`index.js` 或 `app.js` 入口文件。

CCS（Claude Code Server）是本地代理，将 Claude Code 的 Anthropic API 请求转发到 DeepSeek API。

### 3. 配置 API Key

**Windows：**
```cmd
setx ANTHROPIC_API_KEY "sk-你的deepseek密钥"
```

**macOS：**
```bash
echo 'export ANTHROPIC_API_KEY="sk-你的deepseek密钥"' >> ~/.zshrc && source ~/.zshrc
```

也支持 `DEEPSEEK_API_KEY`，脚本会自动读取。

## 自定义配置

用文本编辑器打开启动脚本，修改以下变量：

**Windows（.bat）：**
```cmd
set "ANTHROPIC_BASE_URL=http://127.0.0.1:3000"
```

**macOS（.command）：**
```bash
export ANTHROPIC_BASE_URL="http://127.0.0.1:3000"
```

## 常见问题

### 双击后窗口一闪而过
脚本检测到错误后退出了。打开终端手动运行启动脚本查看完整错误信息。

### 提示 claude 命令未找到
```bash
npm install -g @anthropic-ai/claude-code

# 如果装完还是找不到，添加 PATH
# Windows
setx PATH "%PATH%;%APPDATA%\npm"
# macOS
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

### CCS 代理无响应
```bash
cd 你的CCS目录
node server.js
```
手动能启动但脚本不能 → 检查启动脚本中的端口号是否一致。

### 连不上 DeepSeek API
需配置代理时，在启动脚本中加：
```cmd
:: Windows
set HTTPS_PROXY=http://127.0.0.1:7897

# macOS
export HTTPS_PROXY="http://127.0.0.1:7897"
```

### macOS 提示无法验证开发者
右键（Control+点击）`.command` 文件 → 打开 → 点"打开"。只需操作一次。

## 详情

[CCS 启动器项目页面](https://lihongwei-cn.github.io/lihongwei-cn/ccs-launcher/)
