# 👑 MUNDO Agent v25.0 — THE EMPEROR

独立 AI Agent：LLM 直连 + 工具调用 + Agentic Loop + Agent 调度 + 流式输出

## 核心特性

- **流式输出**：实时看蒙多思考过程，逐字输出不等待
- **实时仪表盘**：token/turns/工具/Agent/分身，执行期间一览无余
- **子任务实时进度**：委派执行时每个子任务开始/完成/失败都有实时反馈
- **28 个 AI 模型**：MiMo/DeepSeek/Qwen/GLM/Kimi/ERNIE/豆包/OpenAI/Claude/Gemini/Mistral/Grok/OpenRouter
- **6 大工具**：terminal/read_file/write_file/search_files/web_search/list_directory
- **Agent 调度**：自动检测 Hermes/Claude Code/Codex/OpenCode，按任务类型分发
- **分身并行**：复杂任务自动拆分，多线程并行执行
- **记忆系统**：三层架构（热/温/冷），自动提取事实，相关性检索
- **上下文管理**：/compact 压缩、/context 可视化、/btw 旁问、/effort 推理深度
- **连接稳定性**：LLM API 3次重试+指数退避，外部 Agent 失败自动降级到蒙多分身
- **健壮性**：工具缺参返回清晰错误而非崩溃，API 消息自动清洗（None/空消息/非法字符）
- **智能输入框**：粘贴多行文本后自由移动光标，末尾回车提交，Option+Enter 强制提交
- **情感智慧**：先共情再解决，直接但不冷漠

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/LiHongwei-cn/lihongwei-cn.git
cd lihongwei-cn/mundo-agent

# 配置 API Key
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 启动
python3 mundo.py
```

## 命令

```
/help            帮助手册
/quit            退出
/status          蒙多状态
/reset           重置对话上下文
/model           查看当前模型
/models          已配置模型 + 能力矩阵
/switch P        切换 provider
/add             添加新 AI 模型
/compact         压缩上下文（省 token）
/context         上下文窗口使用率
/btw <问题>      旁问（不消耗上下文）
/effort          推理深度（low/medium/high/max）
/remember K V    记住事实
/recall K        回忆事实
/memories        列出所有记忆
/memory          记忆系统状态
/skills          列出本地 Skill
/agents          检测本地 Agent
/tools           列出所有工具
!command         直接执行 shell 命令
```

## 架构

```
mundo.py        入口 + CLI + 命令处理
engine.py       Agentic Loop（think → act → observe → repeat）
llm.py          多模型 LLM 客户端（流式 + 非流式）
tools.py        6 大工具实现
delegation.py   任务拆分 + 并行执行 + 结果汇总
agents.py       Agent 检测 + 调度 + 蒙多分身
display.py      执行控制台（流式输出 + 实时仪表盘）
memory.py       三层记忆系统
approval.py     权限审批
cloud_sync.py   云仓库同步
setup.py        首次设置向导
models.py       模型能力矩阵
```

## 下载

| 平台 | 下载 |
|------|------|
| macOS | [mundo-v25-macos.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v25.0/mundo-v25-macos.zip) |
| Windows | [mundo-v25-windows.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v25.0/mundo-v25-windows.zip) |
| Linux | [mundo-v25-linux.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v25.0/mundo-v25-linux.zip) |

## 许可证

MIT License — 完全免费开源
