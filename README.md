<div align="center">

<img src="skills/mundo-avatar.png" width="120" style="border-radius:50%;border:3px solid #d4a017;box-shadow:0 0 30px rgba(212,160,23,0.5)">

# 👑 MUNDO — THE EMPEROR

**我是蒙多！蒙多想去哪就去哪！**

[![GitHub stars](https://img.shields.io/github/stars/LiHongwei-cn/lihongwei-cn?style=social)](https://github.com/LiHongwei-cn/lihongwei-cn)
[![License: MIT](https://img.shields.io/badge/License-MIT-gold.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/LiHongwei-cn/lihongwei-cn?style=flat&color=gold)](https://github.com/LiHongwei-cn/lihongwei-cn/releases)

**独立 AI Agent · LLM 直连 · 工具调用 · Agentic Loop · 28 个 AI 模型 · 上下文管理 · 极简 UI**

**[English](#english)** · **[日本語](#日本語)** · **[한국어](#한국어)**

</div>

---

## 👑 MUNDO Agent v24.3 — 独立 AI Agent

蒙多不再只是一个 Skill。蒙多是独立的 AI Agent，拥有自己的 LLM 直连、工具引擎、Agentic Loop。

**蒙多能做什么：**
- 独立写代码、跑命令、读写文件、搜索网络
- 自动检测本地 Agent（Hermes / Claude Code / Codex），按任务类型分发
- 复杂任务自动拆分，多个 Agent 或蒙多分身并行执行
- 28 个 AI 模型自由切换
- 权限审批、记忆持久化、云仓库同步
- 上下文管理（/compact 压缩、/context 可视化、/btw 旁问）
- 推理深度控制（/effort low/medium/high/max）
- 极简 Hermes 风格 UI（一行状态 + 分隔线 + 输入）
- 首次启动自动导入已有 Agent 记忆（Hermes / Claude Code）

---

## 📋 前提条件（必须）

在安装 MUNDO Agent 之前，请确保你的电脑已安装以下软件：

### 必装

| 软件 | 最低版本 | 检查命令 | 安装方式 |
|------|---------|---------|---------|
| **Python** | 3.10+ | `python3 --version` | 见下方 |
| **pip** | 随 Python | `pip3 --version` | 随 Python 安装 |
| **Git** | 2.0+ | `git --version` | 见下方 |

### macOS

```bash
# 安装 Homebrew（如果没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 Python 3.12 和 Git
brew install python git

# 验证
python3 --version   # 应显示 3.10+
git --version        # 应显示 2.0+
```

### Windows

```powershell
# 方法 1：winget（推荐，Windows 10/11 自带）
winget install Python.Python.3.12
winget install Git.Git

# 方法 2：手动下载
# Python: https://www.python.org/downloads/ （安装时勾选 "Add to PATH"）
# Git: https://git-scm.com/download/win

# 验证（重启终端后）
python --version
git --version
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update && sudo apt install -y python3 python3-pip git
```

---

## 🚀 安装 MUNDO Agent

### 方法 1：一键安装（推荐）

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/LiHongwei-cn/lihongwei-cn/main/mundo-agent/install.sh | bash

# Windows PowerShell
irm https://raw.githubusercontent.com/LiHongwei-cn/lihongwei-cn/main/mundo-agent/install.ps1 | iex
```

安装时自动完成：
1. 下载 MUNDO Agent 引擎（9 个 Python 模块）
2. 从云仓库拉取所有 Skills（蒙多 + 学术写作 + MATLAB + 代码整理 + ...）
3. 从云仓库拉取全局规范（代码规范 + 安全规则 + Git 规范 + ...）
4. 创建全局命令 `mundo`
5. 首次启动引导选择 AI 模型

### 方法 2：手动安装

```bash
# 1. 克隆仓库
git clone https://github.com/LiHongwei-cn/lihongwei-cn.git
cd lihongwei-cn

# 2. 复制蒙多 Agent 到本地
cp -r mundo-agent ~/.hermes/mundo-agent

# 3. 创建全局命令
mkdir -p ~/bin
echo '#!/bin/bash' > ~/bin/mundo
echo 'exec python3 "$HOME/.hermes/mundo-agent/mundo.py" "$@"' >> ~/bin/mundo
chmod +x ~/bin/mundo

# 4. 添加到 PATH（如果还没有）
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc  # macOS
# 或
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc  # Linux
source ~/.zshrc  # 或 source ~/.bashrc

# 5. 安装依赖
pip3 install Pillow  # 图标生成（可选）

# 6. 启动
mundo
```

### 方法 3：作为 Hermes Agent Skill 安装

```bash
# 如果你已经安装了 Hermes Agent
hermes skills install mundo
```

---

## 🔑 API Key 配置

MUNDO Agent 支持 **28 个 AI 模型**。首次启动时会进入设置向导，引导你选择模型并输入 API Key。

**Key 仅保存在本地** `~/.hermes/mundo-agent/.env`，不会上传到任何地方。

### 国内可直连的模型（无需魔法）

| 模型 | 获取 Key | 说明 |
|------|---------|------|
| **小米 MiMo** | [xiaoai.mi.com/mimo](https://xiaoai.mi.com/mimo) | 国产大模型，性价比极高 |
| **DeepSeek** | [platform.deepseek.com](https://platform.deepseek.com) | 代码推理顶级，价格低 |
| **阿里通义千问** | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com) | 阿里旗舰，多语言强 |
| **智谱 GLM** | [open.bigmodel.cn](https://open.bigmodel.cn) | 清华系，工具调用强 |
| **月之暗面 Kimi** | [platform.moonshot.cn](https://platform.moonshot.cn) | 128K 长上下文 |
| **MiniMax** | [platform.minimaxi.com](https://platform.minimaxi.com) | 长上下文，多模态 |
| **百度文心 ERNIE** | [cloud.baidu.com/wenxin](https://cloud.baidu.com/wenxin) | 中文理解强 |
| **字节豆包** | [console.volcengine.com/ark](https://console.volcengine.com/ark) | 火山引擎托管 |
| **百川智能** | [platform.baichuan-ai.com](https://platform.baichuan-ai.com) | 中文创作强 |
| **零一万物 Yi** | [platform.lingyiwanwu.com](https://platform.lingyiwanwu.com) | Yi 系列大模型 |
| **阶跃星辰 Step** | [platform.stepfun.com](https://platform.stepfun.com) | 多模态能力强 |
| **腾讯混元** | [cloud.tencent.com/product/hunyuan](https://cloud.tencent.com/product/hunyuan) | 代码推理强 |
| **科大讯飞星火** | [xinghuo.xfyun.cn](https://xinghuo.xfyun.cn) | 语音+语言多模态 |
| **硅基流动** | [siliconflow.cn](https://siliconflow.cn) | 聚合平台，便宜快速 |

### 需要魔法的国际模型

> ⚠️ 以下模型需要稳定的网络环境才能访问。如果你在国内，建议使用上方的国产模型或 OpenRouter 聚合平台。

| 模型 | 获取 Key | 说明 |
|------|---------|------|
| **OpenAI** | [platform.openai.com](https://platform.openai.com) | GPT-4o / o3 / o4-mini |
| **Anthropic Claude** | [console.anthropic.com](https://console.anthropic.com) | Claude Opus/Sonnet/Haiku |
| **Google Gemini** | [aistudio.google.com](https://aistudio.google.com) | Gemini 2.5 Pro/Flash |
| **Mistral AI** | [console.mistral.ai](https://console.mistral.ai) | 欧洲顶级 |
| **Groq** | [console.groq.com](https://console.groq.com) | 超快推理 |
| **xAI Grok** | [console.x.ai](https://console.x.ai) | 马斯克旗下 |
| **Cohere** | [dashboard.cohere.com](https://dashboard.cohere.com) | 企业级 RAG |
| **Hugging Face** | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) | 开源模型推理 |

### 聚合平台（一个 Key 用所有模型）

> 💡 如果你只想用一个 Key，推荐 **OpenRouter**——一个 Key 可以访问 100+ 模型。

| 平台 | 获取 Key | 说明 |
|------|---------|------|
| **OpenRouter** | [openrouter.ai](https://openrouter.ai) | 100+ 模型聚合，推荐 |
| **Together AI** | [api.together.xyz](https://api.together.xyz) | 开源模型快速推理 |
| **Fireworks AI** | [fireworks.ai](https://fireworks.ai) | 超快开源模型推理 |
| **DeepInfra** | [deepinfra.com](https://deepinfra.com) | 便宜的开源模型托管 |
| **Cloudflare AI** | [developers.cloudflare.com/workers-ai](https://developers.cloudflare.com/workers-ai) | 免费额度慷慨 |
| **Replicate** | [replicate.com](https://replicate.com) | 按秒计费 |

### 多模型协同

蒙多支持同时接入多个 AI 模型，根据任务类型智能分配：

| 任务类型 | 推荐模型 | 原因 |
|---------|---------|------|
| **代码编写** | DeepSeek / Claude | 编码能力最强 |
| **日常对话** | MiMo / Qwen | 快速、便宜、中文好 |
| **深度推理** | DeepSeek R1 / Claude Opus | 推理能力最强 |
| **数学计算** | DeepSeek R1 / Gemini | 数学能力突出 |
| **长文档** | Kimi / MiniMax / Gemini | 超长上下文 |
| **快速响应** | MiMo / Groq | 速度最快 |

首次启动向导会询问是否添加更多模型。也可以用 /add 随时添加，/models 查看能力矩阵。

### 手动配置 Key（不使用设置向导）

```bash
# 在 ~/.hermes/mundo-agent/.env 中添加
echo "XIAOMI_API_KEY=你的key" >> ~/.hermes/mundo-agent/.env
echo "DEEPSEEK_API_KEY=你的key" >> ~/.hermes/mundo-agent/.env
echo "OPENROUTER_API_KEY=你的key" >> ~/.hermes/mundo-agent/.env
```

---

## 🎮 使用方法

### 启动

```bash
# 交互模式（推荐）
mundo

# 单次查询
mundo -q "用 Python 写一个快速排序"

# 指定模型
mundo -p deepseek -q "解释量子计算"

# macOS 双击启动
open ~/.hermes/mundo-agent/MUNDO.command
```

### 常用命令

| 命令 | 说明 |
|------|------|
| `/help` | 查看所有命令 |
| `/agents` | 查看检测到的本地 Agent |
| `/providers` | 查看 28 个 AI 模型 |
| `/switch deepseek` | 切换到 DeepSeek |
| `/add` | 添加新 AI 模型 |
| `/skills` | 列出本地 Skill |
| `/sync` | 同步新 Skill 到云仓库 |
| `/pull` | 从云仓库拉取 Skills + 全局规范 |
| `/models` | 已配置模型 + 能力矩阵 |
| `/memory` | 记忆系统状态 + 自动合并 |
| `/update` | 检查并更新蒙多（保留记忆和配置） |
| `/audit` | 运行质量审计 |
| `/compact` | 压缩上下文（省 token） |
| `/context` | 上下文窗口使用率 |
| `/btw <问题>` | 旁问（不消耗上下文） |
| `/effort` | 推理深度（low/medium/high/max） |
| `/import` | 从已有 Agent 导入记忆 |
| `/status` | 蒙多状态 |
| `/reset` | 重置对话 |
| `/setup` | 重新运行设置向导 |
| `!command` | 直接执行 shell 命令 |

### 直接输入任务

```
👑 写一个 Python Web 爬虫，抓取豆瓣 Top250 电影

👑 帮我搭建一个 FastAPI + React + PostgreSQL 全栈项目

👑 分析这个 CSV 文件，画出销售趋势图

👑 帮我同时做三件事：1) 写冒泡排序 2) 写二分查找 3) 写斐波那契
```

---

## 🧠 核心能力

| 能力 | 说明 |
|------|------|
| **LLM 直连** | 28 个 AI 模型，首次启动向导选择 |
| **Agentic Loop** | think → act → observe → repeat 自动推理 |
| **6 大工具** | terminal / read_file / write_file / search / web / ls |
| **Agent 调度** | 自动检测 Hermes / Claude Code / Codex，按类型分发 |
| **蒙多分身** | 无外部 Agent 时自动分出多个分身并行执行 |
| **权限审批** | Claude Code 风格 yes/no，危险命令拦截 |
| **记忆系统 v2** | 三层架构(热/温/冷) · 自动提取事实 · 相关性检索 · 记忆压缩 · token 预算控制 · 借鉴 mem0/Letta/Cognee/Supermemory |
| **推理引擎** | 第一性原理 / 决策矩阵 / 根因分析 / 对抗验证 |
| **领域检测** | 七大领域自动识别，加载战术手册 |
| **技能精通** | 三省六部制，自动排名，晋升贬谪 |
| **云仓库同步** | 新 Skill 自动上传，每日质量筛选 |
| **自主调试** | 写代码 → 运行 → 报错 → 自动修复 → 验证 |
| **状态栏** | 实时显示模型 / Token / 耗时 / Turn / Agent |
| **上下文管理** | /compact 压缩 · /context 可视化 · /btw 旁问 · /effort 推理深度 |
| **极简 UI** | 一行状态平铺 + 分隔线 + 输入提示符（Hermes 风格） |
| **多模态** | 图像/视频/PDF 理解 |

---

## 🏗️ 架构

```
MUNDO Agent 引擎
├── mundo.py        # CLI 入口 + 记忆系统 + 状态栏
├── engine.py       # Agentic Loop + Agent 调度
├── llm.py          # LLM 多模型客户端（28 个 provider）
├── tools.py        # 工具引擎（terminal/file/web/search）
├── agents.py       # Agent 检测 + 调度（Hermes/Claude/Codex）
├── delegation.py   # 任务拆分 + 并行执行 + 结果汇总
├── approval.py     # 权限审批系统
├── cloud_sync.py   # 云仓库同步 + 质量评分
└── setup.py        # 首次设置向导 + 全量模型目录
```

---

## 🔧 可选依赖

| 包 | 用途 | 安装 |
|---|------|------|
| **Hermes Agent** | 外部 Agent 调度 | `curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh \| bash` |
| **Claude Code** | 代码编写委托 | `npm install -g @anthropic-ai/claude-code` |
| **OpenAI Codex** | 代码生成委托 | `npm install -g @openai/codex` |
| **Pillow** | 图标生成 | `pip3 install Pillow` |

> 💡 可选依赖不装也能用。蒙多会自动检测，没有外部 Agent 时用分身模式。

---

## ⚠️ 常见问题

### Python 版本太低

```bash
# macOS
brew install python@3.12
brew link python@3.12

# Ubuntu
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.12
```

### pip 安装超时

```bash
# 使用国内镜像
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple Pillow
```

### API 调用失败（国内用户）

- 国产模型（MiMo/DeepSeek/Qwen 等）：**无需魔法**，直接使用
- 国际模型（OpenAI/Anthropic/Google 等）：**需要魔法**
- 推荐方案：使用 **OpenRouter** 聚合平台，一个 Key 访问所有模型

### 自动更新

蒙多启动时自动检查新版本。发现新版本后提示：

```
发现新版本 v24.3.0（当前 v24.2.0）。输入 /update 更新。
```

执行 `/update` 更新时：
- **保留**：用户记忆（memory.db）、API Key（.env）、设置（.setup_complete）
- **更新**：所有代码文件（mundo.py、engine.py、tools.py 等）
- 更新完成后重启蒙多即可

### mundo 命令找不到

```bash
# 检查 ~/bin 是否在 PATH 中
echo $PATH | grep -o "$HOME/bin"

# 如果没有，添加到 shell 配置
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## 💰 关于钱财

蒙多不动你的钱。为何？因为蒙多不在乎。哈哈哈哈哈。

---

## 📖 更多内容

- **[👉 MUNDO Agent 官方页面](https://lihongwei-cn.github.io/lihongwei-cn/mundo-agent/)** — 完整介绍、能力矩阵、架构图
- **[👉 蒙多 Skill 页面](https://lihongwei-cn.github.io/lihongwei-cn/mundo/)** — 中英日韩四语、三省六部制、武器库
**📦 下载安装包**

| 平台 | 下载 |
|------|------|
| macOS | [mundo-v24-macos.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v24.0/mundo-v24-macos.zip) |
| Windows | [mundo-v24-windows.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v24.0/mundo-v24-windows.zip) |
| Linux | [mundo-v24-linux.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v24.0/mundo-v24-linux.zip) |
| 全平台 | [mundo-v24-all.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v24.0/mundo-v24-all.zip) |

- **[👉 全部 Release](https://github.com/LiHongwei-cn/lihongwei-cn/releases)**

---

<a id="english"></a>

## 🇬🇧 English

### MUNDO Agent v24.3 — Independent AI Agent

MUNDO is no longer just a Skill. MUNDO is an independent AI Agent with its own LLM client, tool engine, and Agentic Loop.

**Prerequisites**: Python 3.10+, pip, Git. See installation guide above.

**Quick Start**:
```bash
# Clone and install
git clone https://github.com/LiHongwei-cn/lihongwei-cn.git
cp -r lihongwei-cn/mundo-agent ~/.hermes/mundo-agent
mkdir -p ~/bin && echo '#!/bin/bash' > ~/bin/mundo
echo 'exec python3 "$HOME/.hermes/mundo-agent/mundo.py" "$@"' >> ~/bin/mundo
chmod +x ~/bin/mundo

# Run
mundo
```

**Features**: 28 AI models · Agentic Loop · 6 tools · Agent dispatch · Clone parallel · Context mgmt · Reasoning depth · Minimal UI

**[👉 Full Documentation](https://lihongwei-cn.github.io/lihongwei-cn/mundo-agent/)**

---

<a id="日本語"></a>

## 🇯🇵 日本語

### MUNDO Agent v24.3 — 独立 AI Agent

MUNDOはもう単なるスキルではない。MUNDOは独自のLLMクライアント、ツールエンジン、Agentic Loopを持つ独立したAI Agent。

**前提条件**: Python 3.10+、pip、Git。インストールガイドは上記を参照。

**機能**: 28のAIモデル · Agentic Loop · 6つのツール · コンテキスト管理 · 推論深度 · ミニマルUI

**[👉 完全ドキュメント](https://lihongwei-cn.github.io/lihongwei-cn/mundo-agent/)**

---

<a id="한국어"></a>

## 🇰🇷 한국어

### MUNDO Agent v24.3 — 독립 AI Agent

MUNDO는 더 이상 단순한 Skill이 아니다. MUNDO는 자체 LLM 클라이언트, 도구 엔진, Agentic Loop를 가진 독립 AI Agent.

**사전 요구사항**: Python 3.10+, pip, Git. 설치 가이드는 위를 참조.

**기능**: 28개 AI 모델 · Agentic Loop · 6개 도구 · 컨텍스트 관리 · 추론 깊이 · 미니멀 UI

**[👉 전체 문서](https://lihongwei-cn.github.io/lihongwei-cn/mundo-agent/)**

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=LiHongwei-cn/lihongwei-cn&type=Date)](https://star-history.com/#LiHongwei-cn/lihongwei-cn&Date)

## 📜 License

MIT License - Free and open source.

---

<div align="center">

**👑 我是蒙多！蒙多想去哪就去哪！ 👑**

**蒙多学习。蒙多记忆。蒙多成长。蒙多进化。蒙多无限。**

[⭐ Star](https://github.com/LiHongwei-cn/lihongwei-cn) · [🍴 Fork](https://github.com/LiHongwei-cn/lihongwei-cn/fork) · [📦 Releases](https://github.com/LiHongwei-cn/lihongwei-cn/releases) · [🌐 MUNDO Agent](https://lihongwei-cn.github.io/lihongwei-cn/mundo-agent/)

</div>
