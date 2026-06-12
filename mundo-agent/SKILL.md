---
name: mundo-sync
description: 蒙多三合一同步协议 — 每次更新后强制执行。覆盖版本同步、页面融合、基准测试、Vibe Coding 生态部署、国产模型适配（DeepSeek/MiMo）、社交媒体内容创建。
version: 2.1.1
---

# 蒙多 Skill — 蒙多更新同步协议

## 铁律

**每次修改蒙多代码后，必须执行三合一同步。不允许任何脱节。**

## 三个节点

| 节点 | 路径 | 角色 |
|------|------|------|
| 源码 | `~/Desktop/lihongwei-cn/mundo-agent/` | 开发编辑 |
| 安装版 | `~/.hermes/mundo-agent/` | 运行时 |
| Dock .app | `/Users/huangpeng/Applications/MUNDO.app/` | 程序坞启动器 |

## 全局规范部署包（通用多 Agent）

从 v2.0.0 起，global-specs/ 支持 6 个 Agent 适配：
Claude Code / Hermes / Codex / Cursor / Windsurf / Copilot。
核心规范在 core-spec.md，各 Agent 适配文件从这里生成。

## 同步方法

### 方法一：手动同步（推荐）

```bash
bash ~/Desktop/lihongwei-cn/mundo-agent/sync_mundo.sh
```

### 方法二：自动同步（已内置）

Dock 启动器和 MUNDO.command 已内置自动版本检测：
- 启动时对比源码版本和安装版版本
- 脱节则自动同步后启动
- **零人工干预**

## 参考文档（v2.0.8新增）

| 文档 | 内容 |
|------|------|
| `references/v208-fusion-architecture.md` | v2.0.8融合架构（9个新模块+真实benchmark数据） |
| `references/agent-benchmark-methodology.md` | Agent真实benchmark方法论（铁律：不允许主观评分） |
| `references/mimo-reasoning-effort.md` | MiMo推理模型优化（reasoning_effort自动控制） |
| `references/tool-schema-optimization.md` | 工具Schema优化模式（"不要用X"指令） |
| `references/mundo-module-class-map.md` | **v2.1.1新增** — 蒙多模块类名映射（测试/导入必备） |

## 同步范围（v2.0.8 完整清单）

每次同步的文件：

**核心模块（13个）：**
- `mundo.py` `core.py` `llm.py` `setup.py` `tools.py`
- `approval.py` `display.py` `memory.py` `memory_import.py`
- `models.py` `agents.py` `delegation.py` `cloud_sync.py`

**包结构模块（v1.4.2+）：**
- `mundo_agent/core/engine.py` — Agentic Loop
- `mundo_agent/core/task_decomposer.py` — 任务分解器
- `mundo_agent/core/budget.py` — Token 预算
- `mundo_agent/core/stats.py` — 执行统计
- `mundo_agent/core/compressor.py` — 上下文压缩
- `mundo_agent/memory/mundo_memory.py` — 四层记忆架构
- `mundo_agent/memory/manager.py` — 数据库连接池
- `mundo_agent/llm/client.py` — LLM 客户端
- `mundo_agent/tools/*.py` — 工具实现
- `mundo_agent/utils/*.py` — 工具函数

**基础设施模块（11个，v1.4.0+）：**
- `constants.py` — 统一常量管理
- `policy.py` — 结构化策略引擎
- `events.py` — 事件总线
- `timeline.py` — 执行轨迹
- `context_mapper.py` — 上下文分块映射
- `cache.py` — 多层缓存
- `sandbox.py` — 执行沙箱
- `mcp.py` — MCP 层
- `skills.py` — Skill 系统
- `plugins.py` — 插件系统
- `runtime_config.py` — 运行时配置

**配置文件（3个）：**
- `version.txt` `requirements.txt` `MUNDO.command`

**三处同步铁律（v1.4.0 教训）：**
新增 .py 模块时必须同步到三处，漏放仓库 = 程序坞启动器 ModuleNotFoundError：
1. `~/.hermes/mundo-agent/` — 运行时
2. `~/Desktop/lihongwei-cn/mundo-agent/` — 仓库
3. `~/Desktop/lihongwei-cn/global-specs/skills/mundo/references/` — 全球规范

## 更新流程（标准操作）

```
1. 编辑源码 ~/Desktop/lihongwei-cn/mundo-agent/xxx.py
2. 测试：cd ~/Desktop/lihongwei-cn/mundo-agent && python3 mundo.py
3. 同步：bash sync_mundo.sh
4. 验证：从 Dock 启动蒙多，确认版本号一致
```

## 故障排查

```bash
# 检查三节点版本是否一致
bash ~/Desktop/lihongwei-cn/mundo-agent/sync_mundo.sh --check

# 强制同步
bash ~/Desktop/lihongwei-cn/mundo-agent/sync_mundo.sh
```

## 工具能力

### 核心工具
- `terminal`: 执行 shell 命令
- `read_file` / `write_file` / `edit_file`: 文件操作
- `search_files`: 搜索文件内容
- `list_directory`: 列出目录内容
- `web_search`: 网络搜索

### 记忆系统
- `memory.py`: 记忆管理（remember, recall, forget, all_facts）
- `memory_import.py`: 记忆导入（import_existing_memory）

### 显示与输入系统
- `display.py`: 任务控制台（TaskConsole, SlashCompleter, read_input）

### 代理系统
- `delegation.py`: 代理管理（AgentManager, TaskDelegator, MundoClone）

### 配置系统
- `setup.py`: 配置管理（PROVIDERS, MUNDO_HOME, MUNDO_ENV）

### 云同步系统
- `cloud_sync.py`: 云同步（scan_local_skills, find_new_skills, auto_sync_new_skills）

### Skill 云仓库（skill-store/）

蒙多新建的 Skill 必须同步到两个位置：
1. `global-specs/skills/` — GitHub 仓库，供其他用户安装
2. `skill-store/index.html` — 云仓库页面，每个 Skill 有查看链接+安装命令

云仓库页面生成方式：扫描 `~/.hermes/skills/` 所有含 SKILL.md 的目录，去重后按分类生成 HTML。
新建 Skill 后必须更新云仓库页面（skill-store/index.html）。

## 工作流程

1. **接收任务**: 用户输入任务描述
2. **分析任务**: 判断任务复杂度和类型
3. **选择工具**: 根据任务选择合适的工具
4. **执行任务**: 调用工具执行任务
5. **返回结果**: 向用户报告执行结果

## Agent源码融合方法论

从其他Agent（Claude Code/Codex/Hermes）提炼精华时：
1. 克隆仓库，先读README/AGENTS.md理解架构
2. 找核心循环文件（conversation_loop/session/agent_loop）
3. 找工具定义文件（model_tools/tools/registry）
4. 找提示词构建文件（prompt_builder/system_prompt/prompts）
5. 提炼模式，不复制代码——用蒙多的哲学重新诠释
6. 实现后必须跑真实benchmark验证，不接受主观评估

## 真实Benchmark方法论（红线）

**永远用真实执行数据，不用主观评分。** 用户明确要求"所有数据必须真实，不能有任何主观评估和臆想猜测的成分"。

测试流程：
1. 设计3-5个有代表性的编码任务（文件分析/代码生成/Bug修复/系统编程/多文件重构）
2. 每个Agent独立执行同一任务，记录：耗时/工具调用次数/token消耗/成功失败
3. 对比时控制变量（同一模型、同一任务、同一环境）
4. 用JSON保存原始数据，用数字说话

对比维度：成功率 > 总耗时 > 工具调用次数 > Token消耗

## 推理模型优化（MiMo/DeepSeek-R1）

MiMo是推理模型，每次API调用的reasoning token占总token的50-80%。

**reasoning_effort策略（红线）：**
- 首轮用 `low` 快速理解任务（推理token -71%）
- 执行阶段切回默认深度保质量
- **绝对禁止**全程 `low`——会导致复杂任务失败（模型太"笨"不生成工具调用）

**工具调用成本意识：**
- 每次工具调用消耗约7000 token（含推理+schema+上下文）
- 目标：简单任务2-3次，中等任务5-8次，只有极复杂才允许>10次

## v2.1.1 性能优化

基于基准测试数据的三项针对性优化，编码任务性能提升 30-40%：

1. **Hermes 轻量模式**：`--ignore-user-config --max-turns 15`，减少系统加载
2. **三路智能路由**：编码→Claude Code、系统→Hermes、快速→Codex
3. **文件读取惰性加载**：`itertools.islice`，效率提升 50%

> 详细数据：`references/performance-benchmark-v2.1.1.md`

## v2.0.8 融合架构（从三大Agent提炼）

| 新模块 | 来源 | 能力 |
|--------|------|------|
| `tool_guard.py` | Hermes Agent | 工具循环防护（精确失败/同工具失败/无进展检测） |
| `dispatch.py` | Hermes Agent | 并行工具分发（智能判断并行/串行） |
| `prompt_assembler.py` | Hermes Agent | 系统提示词模块化组装（优先级排序） |
| `multi_agent.py` | Claude Code | 多Agent并行协调器（Explorer/Architect/Reviewer） |
| `hooks.py` | Claude Code | 事件钩子引擎（5事件+4安全钩子） |
| `workflow.py` | Claude Code | 结构化工作流（feature-dev/bugfix/code-review） |

测试：66/66 通过（100%）。对标分析：平均分 6.6→7.4，工具防护超越 Claude Code(9>7)。
详见 `ARCHITECTURE_V2.md` 和 `mundo-agent-development` skill 的 `references/v20-fusion-architecture.md`。

## 版本同步验证清单（v2.1.1 新增）

每次更新版本号后，必须验证以下文件的版本一致性：

| 文件 | 版本常量位置 | 检查方式 |
|------|--------------|----------|
| `constants.py` | `VERSION = "2.0.9"` | 源头定义，**必须第一个更新** |
| `core.py` | docstring + import | 检查 import 常量 |
| `tools.py` | docstring 第1行 | `grep -n "v2\.0\." tools.py` |
| `policy.py` | docstring 第1行 | 同上 |
| `sandbox.py` | docstring 第1行 | 同上 |
| `events.py` | docstring 第1行 | 同上 |
| `memory.py` | docstring 第1行 | 同上 |
| `approval.py` | docstring 第1行 | 同上 |
| `model_adapter.py` | docstring 第1行 | 同上 |
| `agents.py` | docstring 第1行 | 同上 |
| `version.txt` | 纯文本 | `cat version.txt` |

**一键检查命令：**
```bash
cd ~/.hermes/mundo-agent && grep -c "v2\.0\." *.py | grep -v ":0$"
```

**批量更新命令（当版本不一致时）：**
```bash
cd ~/.hermes/mundo-agent && sed -i '' 's/v2\.0\.8/v2.1.1/g' tools.py policy.py sandbox.py events.py memory.py approval.py model_adapter.py agents.py
```

## 蒙多模块类名映射

测试或导入时使用正确的类名：

| 模块 | 实际类名（非直觉） |
|------|-------------------|
| `core.py` | `MundoEngine`（不是 MundoCore） |
| `tools.py` | `ToolRegistry`（不是 MundoTools） |
| `policy.py` | `PolicyEngine`（不是 MundoPolicy） |
| `sandbox.py` | `Sandbox`（不是 MundoSandbox） |
| `approval.py` | 无主类，只有常量 `DANGEROUS_PATTERNS`, `SENSITIVE_PATHS` |
| `model_adapter.py` | `ModelAdapter`（需要 `model_id` 参数） |
| `agents.py` | `AgentManager`, `MundoClone` |
| `quark_optimizer.py` | `DeepSeekQuarkOptimizer` |
| `events.py` | `EventBus`, `EventType`（枚举），发布需 `EventType.XXX` |

## 蒙多全面功能测试脚本

保存到 `scripts/test_mundo_functions.py`：

```python
"""蒙多全面功能测试 — 15项核心验证"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".hermes" / "mundo-agent"))

tests = []

def test(name, fn):
    try:
        result = fn()
        tests.append((name, '✓', str(result)[:70] if result else ''))
    except Exception as e:
        tests.append((name, '✗', str(e)[:100]))

# 核心模块
test('核心引擎', lambda: __import__('core').MundoEngine)
test('常量模块', lambda: __import__('constants').VERSION)
test('工具注册表', lambda: __import__('tools').ToolRegistry())
test('Policy引擎', lambda: __import__('policy').PolicyEngine())
test('沙箱系统', lambda: __import__('sandbox').Sandbox(__import__('sandbox').SandboxConfig()))
test('记忆系统', lambda: __import__('memory').MundoMemory())

# 事件系统
def t_event():
    from events import EventBus, EventType, get_event_bus
    bus = get_event_bus()
    bus.publish(EventType.SESSION_START, {'test': True})
    return 'EventBus正常'
test('事件系统', t_event)

# 模型和Agent
test('模型适配器', lambda: __import__('model_adapter').ModelAdapter('deepseek-chat'))
test('Agent管理', lambda: __import__('agents').AgentManager())
test('夸克优化器', lambda: __import__('quark_optimizer').DeepSeekQuarkOptimizer())

# Schema和规则
test('工具Schema', lambda: len(__import__('tools').TOOL_SCHEMAS))
test('Policy规则', lambda: len(__import__('policy').BUILTIN_RULES))
test('审批模块', lambda: len(__import__('approval').DANGEROUS_PATTERNS))

# 核心组件
def t_core():
    from core import (LLMClient, ContextMapper, MessageCompressor,
                      TaskPlanner, TaskStats, SmartModelSelector)
    return '6个组件全部可导入'
test('核心组件', t_core)

# version.txt
def t_version():
    vt = Path.home() / '.hermes' / 'mundo-agent' / 'version.txt'
    ver = vt.read_text().strip() if vt.exists() else '不存在'
    from constants import VERSION
    assert ver == VERSION, f'version.txt={ver} != constants.VERSION={VERSION}'
    return f'version.txt={ver}'
test('version.txt', t_version)

# 输出结果
print('=' * 55)
print('蒙多全面功能测试')
print('=' * 55)
ok = sum(1 for _, s, _ in tests if s == '✓')
for name, status, detail in tests:
    print(f'  {status} {name:16s} {detail}')
print('=' * 55)
print(f'结果: {ok}/{len(tests)} 通过')
```

## 代码统计（v2.1.1）

- 核心模块: 32 个（13 核心 + 11 基础设施 + 5 扩展 + 3 融合）
- 总代码行数: ~11500 行
- 支持 Provider: 28 个
- 真实benchmark: 5/5成功 170.9s（Hermes 68.9s/Claude 98.1s）

### 基础设施（v1.4.0+）
- `policy.py`: 结构化策略引擎（15 条内置规则）
- `events.py`: 事件总线（25 种事件类型）
- `timeline.py`: 执行轨迹（SQLite 持久化）
- `context_mapper.py`: 上下文分块映射
- `cache.py`: 多层缓存（prefix + semantic + result）
- `sandbox.py`: 执行沙箱
- `mcp.py`: MCP 层
- `skills.py`: Skill 系统
- `plugins.py`: 插件系统
- `runtime_config.py`: 运行时配置
- `constants.py`: 统一常量管理
