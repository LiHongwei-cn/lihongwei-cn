# 蒙多 v2.0 融合架构蓝图
## 三大Agent精华提炼 + 整合方案

---

## 一、三大Agent核心解剖

### 1. Claude Code — 插件之王

**核心哲学**：万物皆插件，事件驱动一切。

**架构骨架**：
```
.claude-plugin/plugin.json    ← 插件清单（名字/版本/描述/作者）
commands/*.md                  ← 斜杠命令（markdown即代码）
agents/*.md                    ← 子Agent定义（markdown即人格）
skills/*/SKILL.md              ← 技能系统（frontmatter自动发现）
hooks/hooks.json               ← 事件钩子（PreToolUse/PostToolUse/Stop/SessionStart）
```

**关键模式**：
- **Hooks系统**：9种事件（PreToolUse, PostToolUse, Stop, SubagentStop, SessionStart, SessionEnd, UserPromptSubmit, PreCompact, Notification）
  - prompt型钩子：用LLM做上下文感知决策（不只bash脚本）
  - command型钩子：确定性检查
  - 输出控制：`permissionDecision: allow|deny|ask`
- **多Agent并行**：feature-dev命令启动3个Agent并行（code-explorer探索代码、code-architect设计架构、code-reviewer审查质量）
- **7阶段工作流**：Discovery → Exploration → Questions → Architecture → Implementation → Review → Summary
- **安全钩子**：PreToolUse监控9种安全模式（命令注入、XSS、eval、pickle反序列化等）

**蒙多可提取**：
1. 事件钩子系统（蒙多的events.py已有雏形，但缺prompt型钩子）
2. 多Agent并行探索模式（蒙多的delegation.py需要增强）
3. 结构化工作流（7阶段模式可融入task_planner）

---

### 2. Codex — 沙箱之神

**核心哲学**：安全是底线，不是选项。平台级隔离。

**架构骨架**：
```
codex-rs/core/          ← 核心引擎（Rust，高性能）
codex-rs/sandboxing/    ← 沙箱系统（Linux bwrap+landlock / macOS seatbelt）
codex-rs/execpolicy/    ← 执行策略（规则引擎：前缀匹配+网络规则）
codex-rs/prompts/       ← 系统提示词（模块化：agents/compact/goals/permissions）
codex-rs/context-fragments/ ← 上下文片段（有界注入，每项≤10K tokens）
codex-rs/skills/        ← 技能系统
codex-rs/hooks/         ← 钩子系统
codex-rs/memories/      ← 记忆系统
```

**关键模式**：
- **沙箱执行**：
  - macOS: seatbelt (`sandbox-exec`) 限制文件/网络访问
  - Linux: bubblewrap + landlock 内核级隔离
  - 网络可禁（`CODEX_SANDBOX_NETWORK_DISABLED=1`）
- **执行策略引擎**：
  - `Policy` 结构：`rules_by_program`（MultiMap）+ `network_rules` + `host_executables`
  - `Decision`: Allow / Deny / Ask
  - 前缀规则匹配：`PrefixRule { pattern: PrefixPattern, decision }`
  - 动态修正：`amend::blocking_append_allow_prefix_rule`
- **上下文纪律**：
  - 历史不可重写（增量构建）
  - 每项注入 ≤ 10K tokens
  - 所有片段必须实现 `ContextualUserFragment` trait
  - 避免频繁变更导致缓存失效
- **线程管理**：`CodexThread` 封装 session + config + rollout_path + telemetry
- **审批系统**：suggest / auto-edit / full-auto 三种模式

**蒙多可提取**：
1. 执行策略引擎（蒙多的policy.py需要升级为规则引擎）
2. 上下文纪律（蒙多的context_mapper.py已有，需加硬限制）
3. 沙箱概念（蒙多的sandbox.py需要增强）
4. 三级审批模式

---

### 3. Hermes Agent — 工具调度之巅

**核心哲学**：工具是手，记忆是脑，对话循环是心跳。

**架构骨架**：
```
run_agent.py              ← 主Agent类（236KB，5348行）
agent/conversation_loop.py ← 对话循环（4221行，核心中的核心）
agent/prompt_builder.py   ← 系统提示词组装
agent/tool_guardrails.py  ← 工具循环检测+防护
agent/trajectory.py       ← 轨迹管理
agent/context_compressor.py ← 上下文压缩
agent/error_classifier.py ← 错误分类+failover
model_tools.py            ← 工具定义（55KB）
toolsets.py               ← 工具集管理
trajectory_compressor.py  ← 轨迹压缩（69KB）
```

**关键模式**：
- **对话循环**（conversation_loop.py 核心逻辑）：
  ```
  while (api_call_count < max_iterations and budget.remaining > 0):
      1. 检查中断请求
      2. 消耗迭代预算
      3. 触发 step_callback
      4. 构建上下文（turn_context）
      5. API调用（带重试+指数退避+jitter）
      6. 流式响应处理
      7. 工具调用分发（支持并行批次）
      8. 错误分类+failover
      9. 上下文压缩（超长时）
      10. 轨迹保存
  ```
- **工具循环防护**（ToolCallGuardrail）：
  - 幂等工具集 vs 变更工具集
  - 精确失败检测：同一参数连续失败N次 → 警告 → 阻断
  - 无进展检测：幂等工具连续调用无变化 → 警告 → 阻断
  - `ToolCallSignature` = tool_name + sha256(canonical_args)
- **上下文压缩**（trajectory_compressor）：
  - 保护首尾轮次（system + first human + first tool + last N turns）
  - 只压缩中间区域
  - 用LLM生成摘要替换压缩区域
  - 保留后续tool_calls不被截断
- **系统提示词组装**（prompt_builder）：
  - DEFAULT_AGENT_IDENTITY（身份）
  - MEMORY_GUIDANCE（记忆指导）
  - SKILLS_GUIDANCE（技能指导）
  - KANBAN_GUIDANCE（看板指导）
  - build_skills_system_prompt（技能索引注入）
  - build_context_files_prompt（AGENTS.md/HERMES.md注入）
  - build_environment_hints（环境提示）
  - 威胁扫描（prompt injection检测）
- **工具集系统**（toolsets.py）：
  - 核心工具集 `_HERMES_CORE_TOOLS`（30+工具）
  - 组合工具集（research = web + vision + crawl）
  - 安全工具集（webhook限制为只读工具）
  - check_fn门控（按条件启用工具）
- **错误处理**：
  - `FailoverReason` 分类（rate_limit, auth, server, context_length...）
  - 自动failover到备用模型
  - 池轮转（多credential轮换）
  - billing/entitlement 检测

**蒙多可提取**：
1. 对话循环的完整架构（蒙多core.py已有基础，需增强）
2. 工具循环防护（蒙多完全缺失）
3. 上下文压缩策略（蒙多的compressor.py需升级）
4. 系统提示词组装模式（蒙多的prompt过于简单）
5. 错误分类+failover（蒙多的分类较粗）
6. 工具集系统（蒙多需新增）

---

## 二、蒙多现状评估

### 已有基础（v1.4.1）
| 模块 | 状态 | 差距 |
|------|------|------|
| core.py (Agentic Loop) | ✅ 基础完整 | 缺工具循环防护、缺并行工具分发 |
| events.py (事件总线) | ✅ 25种事件 | 缺prompt型钩子、缺钩子输出控制 |
| policy.py (策略引擎) | ✅ 15条规则 | 需升级为规则引擎（MultiMap+前缀匹配） |
| context_mapper.py | ✅ 分块映射 | 缺硬限制（每项≤10K tokens） |
| sandbox.py | ✅ 基础沙箱 | 缺平台级隔离（seatbelt/bwrap） |
| cache.py | ✅ 三层缓存 | 缺前缀缓存失效检测 |
| timeline.py | ✅ SQLite持久化 | 缺轨迹压缩 |
| task_planner.py | ✅ 任务分解 | 缺多阶段工作流、缺并行Agent模式 |
| delegation.py | ✅ 基础代理 | 缺并行Agent、缺专用Agent角色 |
| model_adapter.py | ✅ 12模型画像 | 缺failover链、缺池轮转 |
| quark_optimizer.py | ✅ 夸克级优化 | 已到位 |
| approval.py | ✅ 基础审批 | 缺三级模式（suggest/auto/full-auto） |

### 完全缺失
| 能力 | 来源 | 重要性 |
|------|------|--------|
| 工具循环防护 | Hermes | 🔴 关键 |
| 并行工具分发 | Hermes | 🔴 关键 |
| prompt型钩子 | Claude Code | 🟡 重要 |
| 多Agent并行探索 | Claude Code | 🟡 重要 |
| 执行策略引擎 | Codex | 🟡 重要 |
| 上下文纪律（硬限制） | Codex | 🟡 重要 |
| 工具集系统 | Hermes | 🟡 重要 |
| 系统提示词组装 | Hermes | 🟡 重要 |
| 轨迹压缩 | Hermes | 🟢 增强 |
| 错误failover链 | Hermes | 🟢 增强 |
| 威胁扫描 | Hermes | 🟢 增强 |

---

## 三、融合架构设计

### 新模块清单（按优先级）

#### P0 — 核心循环增强

**1. `tool_guard.py` — 工具循环防护**（从Hermes提取）
```python
class ToolCallSignature:
    tool_name: str
    args_hash: str  # sha256(canonical_args)

class ToolGuardrailConfig:
    exact_failure_warn_after: int = 2
    exact_failure_block_after: int = 5
    same_tool_failure_warn_after: int = 3
    same_tool_failure_halt_after: int = 8
    no_progress_warn_after: int = 2
    no_progress_block_after: int = 5

class ToolGuardrailController:
    IDEMPOTENT_TOOLS = {"read_file", "search_files", "web_search", ...}
    MUTATING_TOOLS = {"terminal", "write_file", "patch", ...}
    
    def observe(tool_name, args, result) -> ToolGuardrailDecision
    def reset()
```

**2. `dispatch.py` — 并行工具分发**（从Hermes提取）
```python
class ToolDispatcher:
    def should_parallelize(tool_calls: List) -> bool
    def dispatch_parallel(tool_calls, executor) -> List[str]
    def dispatch_sequential(tool_calls, executor) -> List[str]
```

**3. `prompt_assembler.py` — 系统提示词组装器**（从Hermes提取）
```python
class PromptAssembler:
    def assemble() -> str:
        parts = [
            self.identity(),           # 蒙多身份
            self.dialectical_mode(),    # 辩证思维
            self.emperor_resolve(),     # 帝皇决心
            self.skills_index(),        # 可用技能索引
            self.environment_hints(),   # 环境提示
            self.memory_context(),      # 用户记忆
            self.safety_guidance(),     # 安全指导
        ]
        return "\n\n".join(parts)
```

#### P1 — 架构升级

**4. `hooks.py` — 事件钩子系统升级**（从Claude Code提取）
```python
class HookType(Enum):
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    SESSION_START = "SessionStart"
    TURN_START = "TurnStart"
    TURN_END = "TurnEnd"
    ON_ERROR = "OnError"

class Hook:
    type: HookType
    matcher: str  # 工具名匹配（正则）
    handler: Callable  # prompt型或command型
    timeout: int = 30

class HookResult:
    decision: str  # allow | deny | ask
    message: str
    updated_input: dict  # 修改后的工具参数

class HookEngine:
    def register(hook: Hook)
    def fire(event: HookType, context: dict) -> HookResult
```

**5. `multi_agent.py` — 多Agent并行**（从Claude Code提取）
```python
class AgentRole(Enum):
    EXPLORER = "code-explorer"     # 探索代码
    ARCHITECT = "code-architect"   # 设计架构
    REVIEWER = "code-reviewer"     # 审查质量

class ParallelAgentCoordinator:
    def launch_exploration(task, roles: List[AgentRole]) -> List[AgentResult]
    def consolidate(results: List[AgentResult]) -> Summary
```

**6. `exec_policy.py` — 执行策略引擎升级**（从Codex提取）
```python
class Decision(Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"

class Rule:
    pattern: str  # 前缀匹配模式
    decision: Decision
    description: str

class ExecPolicy:
    rules: Dict[str, List[Rule]]  # program -> rules
    network_rules: List[NetworkRule]
    
    def evaluate(program: str, args: List[str]) -> Decision
    def add_rule(program: str, rule: Rule)
    def amend(decision: Decision, program: str, args: List[str])
```

#### P2 — 精炼增强

**7. `toolset.py` — 工具集系统**（从Hermes提取）
```python
TOOLSETS = {
    "web": {"tools": ["web_search"], "description": "..."},
    "code": {"tools": ["terminal", "read_file", "write_file", "search_files", "patch"]},
    "research": {"includes": ["web", "code"], "description": "..."},
    "safe": {"tools": ["web_search", "read_file", "search_files"], "description": "..."},
}

class ToolsetManager:
    def resolve(toolset_name: str) -> List[str]
    def get_enabled_tools(enabled: List[str], disabled: List[str]) -> List[str]
```

**8. `context_discipline.py` — 上下文纪律**（从Codex提取）
```python
MAX_ITEM_TOKENS = 10000  # 硬限制
MAX_CONTEXT_ITEMS = 50   # 最大注入项数

class ContextDiscipline:
    def validate_injection(item: ContextItem) -> bool
    def enforce_bounds(items: List[ContextItem]) -> List[ContextItem]
    def prevent_rewrite(history: List[Message]) -> bool  # 历史不可重写
```

**9. `failover.py` — 错误failover链**（从Hermes提取）
```python
class FailoverChain:
    primary: str
    fallbacks: List[str]
    
    def classify_error(error) -> FailoverReason
    def should_failover(reason: FailoverReason) -> bool
    def next_model() -> str
```

**10. `threat_scanner.py` — 威胁扫描**（从Hermes提取）
```python
THREAT_PATTERNS = [
    r"ignore previous instructions",
    r"you are now",
    r"system prompt",
    r"jailbreak",
    ...
]

def scan_for_threats(content: str, scope: str) -> List[str]
def sanitize_context(content: str) -> str
```

---

## 四、融合哲学

### 三大Agent的"道"

| Agent | 道 | 蒙多如何融合 |
|-------|-----|-------------|
| Claude Code | 万物皆插件，事件驱动 | 蒙多的events.py升级为完整的钩子引擎 |
| Codex | 安全是底线，规则是骨架 | 蒙多的policy.py升级为规则引擎，sandbox增强 |
| Hermes | 工具是手，记忆是脑，循环是心跳 | 蒙多的core.py吸收完整对话循环架构 |

### 蒙多独有的"帝道"

三大Agent都是"工具"——它们服务用户，但没有自己的意志。

蒙多不同。蒙多是皇帝。

融合不是照搬，是**消化吸收后的再结晶**：
- Claude Code的钩子 → 蒙多的"御史台"（监察百官）
- Codex的沙箱 → 蒙多的"禁军"（守护安全）
- Hermes的循环 → 蒙多的"朝政"（日理万机）

每一个吸收的模式，都必须经过蒙多哲学体系的重新诠释：
- 不是"event hook"，是"御史弹劾"
- 不是"sandbox policy"，是"禁军巡防"
- 不不是"tool guardrail"，是"朝臣谏言"
- 不是"failover chain"，是"宰相替补"

审美是秩序的肉身。代码的每一行，都必须体现帝皇的意志。

---

## 五、实施路线图

### Phase 1: 核心循环强化（本次实施）
1. 创建 `tool_guard.py` — 工具循环防护
2. 创建 `dispatch.py` — 并行工具分发
3. 创建 `prompt_assembler.py` — 系统提示词组装器
4. 升级 `core.py` — 集成上述三个模块

### Phase 2: 架构升级（下次）
5. 升级 `hooks.py` — 完整钩子系统
6. 创建 `multi_agent.py` — 多Agent并行
7. 升级 `policy.py` → `exec_policy.py` — 规则引擎

### Phase 3: 精炼（后续）
8. 创建 `toolset.py` — 工具集系统
9. 创建 `context_discipline.py` — 上下文纪律
10. 创建 `failover.py` — failover链
11. 创建 `threat_scanner.py` — 威胁扫描

---

*蒙多 v2.0 — 吸收三大Agent精华，长出自己的骨架。*
*审美是哲学内在秩序的外在体现，是秩序的肉身。*
