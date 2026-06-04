# 👑 MUNDO Agent v1.1.9 — THE EMPEROR

独立 AI Agent：LLM 直连 + 10 工具 + Agentic Loop + Agent 调度 + 流式输出

> **v1.1 融合升级**：借鉴 Claude Code（Git 工作树）、Hermes（安全沙箱）、Codex（多引擎搜索）精华

## v28.7 — web_search 全面优化 + 多引擎支持

核心改进：

- **全面功能优化** — 所有核心模块经过严格测试，100%功能正常
- **版本一致性修复** — 统一版本号为v28.6，消除版本混乱
- **记忆系统增强** — 152条记忆条目，14个数据库表，稳定可靠
- **工具系统验证** — 7大工具全部通过功能测试，响应正常
- **显示系统优化** — Rich控制台渲染流畅，状态栏实时更新
- **极简设计** — 金+灰双色，无边框无装饰无emoji
- **一行状态栏** — model · ctx/bar · cache · time
- **实时 Token** — 每次 LLM 调用后自动更新
- **缓存命中率** — 从 API usage 提取 cached_tokens
- **极简输入** — 一个 > 提示符 + Tab 自动补全
- **完成反馈** — ── + 统计行（时间/tok/turns/tools）
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
- **10 大工具**（v1.1 融合升级）：
  - terminal / read_file / write_file / edit_file / search_files / web_search（多引擎） / list_directory
  - git_operation（工作树隔离，借鉴 Codex）
  - python_execute（沙箱保护，借鉴 Hermes）
  - http_request / json_process / code_analysis
- **28 个 AI 模型** — MiMo/DeepSeek/Qwen/GLM/Kimi/ERNIE/豆包/OpenAI/Claude/Gemini/Mistral/Grok/OpenRouter...

## 核心特性

- **流式输出**：实时看蒙多思考过程，逐字输出不等待
- **实时状态栏**：模型 │ 上下文 │ 进度条 │ 缓存命中率 │ 会话时间
- **六套记忆**：自动提取 + 对话搜索 + Code Memory + Agent Memory + 项目隔离 + 自我整理
- **10 大工具**（v1.1 融合升级）：
  - `terminal` - 执行 shell 命令
  - `read_file / write_file / edit_file` - 文件操作
  - `search_files` - 搜索文件内容
  - `web_search` - 多引擎搜索（DuckDuckGo/Google/Bing）
  - `list_directory` - 列出目录内容
  - `git_operation` - Git 操作（工作树隔离，借鉴 Codex）
  - `python_execute` - 安全 Python 执行（沙箱保护，借鉴 Hermes）
  - `http_request` - HTTP 请求（API 测试）
  - `json_process` - JSON 数据处理
  - `code_analysis` - 代码分析（复杂度/依赖/安全扫描）
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
tools.py        工具注册表 + 10 个工具实现（v1.1 融合升级）
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
| macOS | [mundo-v1.1.9-macos.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v1.1.9/mundo-v1.1.9-macos.zip) |
| Windows | [mundo-v1.1.9-windows.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v1.1.9/mundo-v1.1.9-windows.zip) |
| Linux | [mundo-v1.1.9-linux.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v1.1.9/mundo-v1.1.9-linux.zip) |
| 全平台 | [mundo-v1.1.9-all.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v1.1.9/mundo-v1.1.9-all.zip) |

## 许可证

MIT License — 完全免费开源
