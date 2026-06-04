# MUNDO Agent v1.1.9 — THE EMPEROR

独立 AI Agent：LLM 直连 + 10 工具 + Agentic Loop + Agent 调度 + 流式输出

> 融合 Claude Code（Git 工作树）、Hermes（安全沙箱）、Codex（多引擎搜索）精华

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/LiHongwei-cn/lihongwei-cn.git
cd lihongwei-cn/mundo-agent

# 安装（自动创建虚拟环境，需要 Python 3.10+）
chmod +x install.sh && ./install.sh

# 配置 API Key
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 启动
./run.sh
```

### macOS 双击启动

双击 `MUNDO.command` 即可启动。

### Windows 启动

双击 `mundo.bat` 或在终端运行：

```cmd
mundo.bat
```

## 核心特性

- **流式输出**：实时逐字输出，不等待
- **实时状态栏**：模型 · 上下文进度条 · 缓存命中率 · 会话时间
- **六套记忆**：自动提取 + 对话搜索 + Code Memory + Agent Memory + 项目隔离 + 自我整理
- **10 大工具**：
  - `terminal` — 执行 shell 命令
  - `read_file / write_file / edit_file` — 文件操作
  - `search_files` — 搜索文件内容
  - `web_search` — 多引擎搜索（DuckDuckGo/Google/Bing）
  - `list_directory` — 列出目录内容
  - `git_operation` — Git 操作（工作树隔离）
  - `python_execute` — 安全 Python 执行（沙箱保护）
  - `http_request / json_process / code_analysis`
- **28 个 AI 模型**：首次向导选择，支持多模型切换
- **Agent 调度**：自动检测 Hermes/Claude Code/Codex，按任务类型分发
- **分身并行**：复杂任务自动拆分，多线程并行执行
- **上下文管理**：/compact 压缩、/context 可视化、/effort 推理深度
- **LLM 错误自动重试**：429/5xx 自动重试，上下文溢出自动压缩恢复
- **权限审批**：danger/caution/safe 三级分类
- **情感智慧**：先共情再解决，直接但不冷漠

## 命令

```
/help            帮助手册
/quit            退出
/status          蒙多状态（含六套记忆统计）
/reset           重置对话上下文
/model           查看当前模型
/models          已配置模型列表
/switch P        切换 provider
/add             添加新 AI 模型
/compact         压缩上下文（省 token）
/context         上下文窗口使用率
/effort          推理深度（low/medium/high/max）
/remember K V    记住事实
/recall K        回忆事实
/memories        列出所有记忆
/memory          记忆系统状态
/search Q        搜索历史对话
/projects        列出所有项目
/tools           列出所有工具
/setup           重新运行设置向导
!command         直接执行 shell 命令
```

## 架构

```
mundo.py        入口 + CLI + 命令处理
core.py         Agentic Loop + IterationBudget + ContextCompressor + 错误重试
llm.py          多模型 LLM 客户端（消息清洗 + reasoning 支持）
tools.py        工具注册表 + 10 个工具实现
display.py      执行控制台（状态栏 + 活动流 + 极简输入）
memory.py       六套记忆架构（自动/对话搜索/Code/Agent/项目隔离/自我整理）
delegation.py   Agent 检测 + 任务拆分 + 并行执行 + 分身
approval.py     权限审批（danger/caution/safe）
setup.py        首次设置向导 + 28 个 Provider
models.py       模型能力矩阵
cloud_sync.py   云仓库同步
```

## 下载

| 平台 | 下载 |
|------|------|
| macOS | [mundo-v1.1.9-macos.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v1.1.9/mundo-v1.1.9-macos.zip) |
| Windows | [mundo-v1.1.9-windows.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v1.1.9/mundo-v1.1.9-windows.zip) |
| Linux | [mundo-v1.1.9-linux.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v1.1.9/mundo-v1.1.9-linux.zip) |
| 全平台 | [mundo-v1.1.9-all.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v1.1.9/mundo-v1.1.9-all.zip) |

## 许可证

MIT License — 完全免费开源
