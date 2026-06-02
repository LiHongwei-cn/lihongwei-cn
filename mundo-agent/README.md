# 👑 MUNDO Agent v27.0 — THE EMPEROR

独立 AI Agent：LLM 直连 + 工具调用 + Agentic Loop + Agent 调度 + 流式输出

## v27.0 — 底层架构优化（借鉴 Hermes + Claude Code）

核心改进：

- **IterationBudget** — Token 预算控制，per-turn + 总量监控，预算警告
- **智能上下文压缩** — 优先压缩 tool 输出，保留对话上下文，自动触发
- **LLM 错误自动重试** — 429/5xx 自动重试，上下文溢出自动压缩恢复
- **Slash 命令自动补全** — 输入 / 后按 Tab 显示可用命令
- **消息清洗增强** — surrogate 字符修复，content 类型强制转换
- **工具错误信息增强** — terminal 失败时提供修复建议（权限/路径/命令）
- **记忆检索优化** — 多词匹配加分，分类权重排序（教训>事实>偏好>摘要）
- **流式降级通知** — 流式不可用时告知用户，不再静默降级
- **智能截断** — 大输出保留首尾，中间省略（vs 旧版只保留头部）
- **增强消息清洗**（借鉴 Hermes message_sanitization）— surrogate 修复、JSON 修复
- **KawaiiSpinner 动画**（借鉴 Hermes）— 执行中的动画反馈
- **edit_file 精确编辑**（借鉴 Claude Code）— 替换整文件覆盖，精准修改
- **上下文管理**（借鉴 Claude Code）— /compact + /context，用户可控
- **简化记忆系统** — 三层(热/温/冷) → 双层(事实+摘要)，不再白耗 token
- **Ctrl+C 中断** — 执行中随时优雅停止
- **7 大工具** — terminal / read_file / write_file / edit_file / search_files / web_search / list_directory
- **28 个 AI 模型** — MiMo/DeepSeek/Qwen/GLM/Kimi/ERNIE/豆包/OpenAI/Claude/Gemini/Mistral/Grok/OpenRouter...

## 核心特性

- **流式输出**：实时看蒙多思考过程，逐字输出不等待
- **实时指示器**：token/turns/工具，精简不喧宾夺主
- **7 大工具**：含 edit_file 精确编辑（Claude Code 风格）
- **28 个 AI 模型**：首次向导选择，支持多模型协同
- **Agent 调度**：自动检测 Hermes/Claude Code/Codex，按任务类型分发
- **分身并行**：复杂任务自动拆分，多线程并行执行
- **记忆系统**：双层架构（事实+摘要），相关性检索，token 预算控制
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
/status          蒙多状态
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
/tools           列出所有工具
/setup           重新运行设置向导
!command         直接执行 shell 命令
```

## 架构

```
mundo.py        入口 + CLI + 命令处理（精简 ~450 行）
core.py         Agentic Loop（中断支持 + 上下文预算 + 流式降级）
llm.py          多模型 LLM 客户端（消息清洗 + reasoning 支持）
tools.py        工具注册表 + 7 个工具实现
display.py      执行控制台（KawaiiSpinner 风格 + 精简状态栏）
memory.py       双层记忆系统（事实 + 摘要）
delegation.py   Agent 检测 + 任务拆分 + 并行执行 + 分身
approval.py     权限审批（danger/caution/safe）
setup.py        首次设置向导 + 28 个 Provider
models.py       模型能力矩阵
cloud_sync.py   云仓库同步
```

## 下载

| 平台 | 下载 |
|------|------|
| macOS | [mundo-v27.0-macos.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v27.0/mundo-v27.0-macos.zip) |
| Windows | [mundo-v27.0-windows.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v27.0/mundo-v27.0-windows.zip) |
| Linux | [mundo-v27.0-linux.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v27.0/mundo-v27.0-linux.zip) |
| 全平台 | [mundo-v27.0-all.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/mundo-v27.0/mundo-v27.0-all.zip) |

## 许可证

MIT License — 完全免费开源
