# 👑 MUNDO Agent v28.0 — THE EMPEROR

独立 AI Agent：LLM 直连 + 工具调用 + Agentic Loop + Agent 调度 + 流式输出

## v28.0 — 极简艺术 + Claude 六套记忆架构

核心改进：

- **蒙多帝王美学** — 极简设计 — 金+灰，无边框无装饰，一行状态栏
- **Hermes 风格状态栏** — 👑模型 ┃ 上下文 ┃ ▰▰▰▰▱▱▱▱▱▱▱▱ ┃ 缓存命中率 ┃ 会话时间 ┃ 任务计时
- **实时 Token 消耗** — 每次 LLM 调用后自动更新状态栏
- **缓存命中率** — 从 API usage 中提取 cached_tokens，显示命中百分比
- **醒目输入栏** — 一个 > 提示符 + Tab 自动补全
- **任务完成反馈** — ── + 统计行（tok/turns/tools/errors/retries）
- **Claude 六套记忆架构**：
  - 自动 Memory — 从对话中自动提取关键信息（轻量规则，不调 LLM）
  - 对话搜索 — FTS5 全文搜索历史对话
  - Code Memory — 代码模式、项目结构、技术偏好
  - Agents Memory — Agent 任务执行结果、成功/失败模式
  - Projects 隔离 — 按工作目录隔离记忆上下文
  - 自我整理 — 定期合并重复、淘汰过时、压缩低价值记忆
- **智能上下文压缩** — 优先压缩 tool 输出，保留对话，自动触发
- **LLM 错误自动重试** — 429/5xx 自动重试，上下文溢出自动压缩恢复
- **消息清洗增强** — surrogate 字符修复，content 类型强制转换
- **上下文管理**（借鉴 Claude Code）— /compact + /context，用户可控
- **Ctrl+C 中断** — 执行中随时优雅停止
- **7 大工具** — terminal / read_file / write_file / edit_file / search_files / web_search / list_directory
- **28 个 AI 模型** — MiMo/DeepSeek/Qwen/GLM/Kimi/ERNIE/豆包/OpenAI/Claude/Gemini/Mistral/Grok/OpenRouter...

## 核心特性

- **流式输出**：实时看蒙多思考过程，逐字输出不等待
- **实时状态栏**：模型 │ 上下文 │ 进度条 │ 缓存命中率 │ 会话时间
- **六套记忆**：自动提取 + 对话搜索 + Code Memory + Agent Memory + 项目隔离 + 自我整理
- **7 大工具**：含 edit_file 精确编辑（Claude Code 风格）
- **28 个 AI 模型**：首次向导选择，支持多模型协同
- **Agent 调度**：自动检测 Hermes/Claude Code/Codex，按任务类型分发
- **分身并行**：复杂任务自动拆分，多线程并行执行
- **上下文管理**：/compact 压缩、/context 可视化、/effort 推理深度
- **连接稳定性**：LLM API 3次重试+指数退避，流式失败自动降级
- **中断支持**：Ctrl+C 优雅停止当前任务
- **权限审批**：danger/caution/safe 三级分类
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
tools.py        工具注册表 + 7 个工具实现
display.py      执行控制台（Hermes 状态栏 + 活动流 + 醒目输入）
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
| macOS | [mundo-v28.0-macos.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v28.0/mundo-v28.0-macos.zip) |
| Windows | [mundo-v28.0-windows.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v28.0/mundo-v28.0-windows.zip) |
| Linux | [mundo-v28.0-linux.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v28.0/mundo-v28.0-linux.zip) |
| 全平台 | [mundo-v28.0-all.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v28.0/mundo-v28.0-all.zip) |

## 许可证

MIT License — 完全免费开源
