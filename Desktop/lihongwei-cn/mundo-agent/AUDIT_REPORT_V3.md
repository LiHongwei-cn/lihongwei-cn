# 蒙多Agent 全栈安全与架构审计报告 v3.0.0

**审计日期**: 2026-07-09
**审计范围**: 全部源代码（约15000行 Python）
**审计方法**: 逐文件逐函数静态分析 + 安全模式匹配 + 架构评估
**审计标准**: OWASP Top 10 + CWE/SANS Top 25 + AI Agent最佳实践

---

## 🔴 P0 — 严重安全漏洞（必须立即修复）

### VULN-001: `examples/mcp_server_demo.py` — eval() 任意代码执行

**位置**: `examples/mcp_server_demo.py:40`
```python
result = eval(expression, {"__builtins__": {}}, {})
```

**风险**: `__builtins__ = {}` 不安全。攻击者可以用：
```python
().__class__.__bases__[0].__subclasses__()
```
逃逸沙箱，执行任意系统命令。这是Python安全领域的经典漏洞。

**修复方案**: 使用 `ast.literal_eval()` 或限制到纯数学运算的 parser。

**严重性**: CRITICAL (CVSS 9.8)

---

### VULN-002: `tools.py` — subprocess shell=True 命令注入

**位置**: `tools.py:356`
```python
result = subprocess.run(cmd, shell=True, capture_output=True=True, timeout=30, cwd=workdir)
```

**风险**: 当 `operation` 通过 dict 查表得到固定命令时风险较低，但 `_terminal()` 函数（约L160）直接将用户输入的 command 传入 `shell=True`，这是 Agent 的正常行为但缺乏安全拦截。

**问题**: 
- `_terminal()` 没有调用 `security.validate_command()` 做前置校验
- `policy.evaluate_command()` 也未在执行前被调用
- `sandbox.execute()` 存在但未被 `_terminal()` 使用

**根因**: `security_hardening.py` 和 `policy.py` 设计了但**没有集成到工具执行链中**。安全层形同虚设。

**修复方案**: 在 `_terminal()` 和 `_python_execute()` 中，必须先经过 policy + security 双层校验再执行。

**严重性**: CRITICAL

---

### VULN-003: `mundo_agent/tools/terminal.py` — shell=True 无安全拦截

**位置**: `mundo_agent/tools/terminal.py:79`
```python
cmd, shell=True, capture_output=True, text=True,
```

**同 VULN-002**。`mundo_agent/` 子包中的工具同样没有安全层集成。

**严重性**: CRITICAL

---

### VULN-004: `mundo_agent/tools/git_ops.py` — 多处 shell=True

**位置**: `mundo_agent/tools/git_ops.py:33, 92, 97, 118, 145, 151`

**风险**: git 操作通过 `shell=True` 执行，branch_name/message 等参数未做转义。恶意 branch_name 如 `; rm -rf /` 可导致命令注入。

**修复方案**: 统一使用列表参数（不传 shell=True），或对参数做 shlex.quote()。

**严重性**: HIGH

---

### VULN-005: `mundo.py` — os.system() 直接执行

**位置**: `mundo.py:543, 557, 665`
```python
os.system(line[1:])  # 用户输入直接执行
os.system("clear")
```

**风险**: `os.system()` 使用 shell 执行，比 `subprocess` 更危险。

**修复方案**: 替换为 `subprocess.run(["clear"])` 或等效的安全调用。

**严重性**: HIGH

---

### VULN-006: `memory.py:606` — f-string SQL 拼接

**位置**: `memory.py:606`
```python
conn.execute(f"DELETE FROM [{table_name}]")
```

**风险**: table_name 来自 `sqlite_master` 查询结果（内部来源），使用方括号做了基本防护。但模式本身不安全——如果 table_name 被污染（虽然当前不太可能），可导致 SQL 注入。

**修复方案**: 使用白名单验证 table_name，或至少只允许字母数字下划线。

**严重性**: MEDIUM（当前数据来源可控，但模式不安全）

---

### VULN-007: `timeline.py:174` — f-string SQL 拼接

**位置**: `timeline.py:174`
```python
sql = f"SELECT * FROM timeline WHERE {where} ORDER BY timestamp DESC LIMIT ?"
```

**分析**: `where` 由 `conditions` 列表通过 `" AND ".join()` 拼接而成，而 conditions 中的每个条件都是固定格式 `"field = ?"`，参数通过 `params` 传递。**这个模式是安全的**——参数化查询 + 结构化拼接。

**结论**: 误报，实际安全。但建议添加注释说明安全性。

**严重性**: LOW（模式看起来危险但实际安全）

---

## 🟠 P1 — 架构缺陷（严重影响可靠性）

### ARCH-001: 安全层未集成到执行链

**描述**: `security_hardening.py`、`policy.py`、`sandbox.py` 三个安全模块都已实现，但 `tools.py` 中的工具执行函数（`_terminal`, `_python_execute`, `_read_file`, `_write_file`）**完全没有调用这些安全模块**。

**影响**: 
- 安全层写了但不用 = 形同虚设
- `core.py` 中调用了 `self.security.check_tool_call()` 但只在主循环中，工具 handler 本身没有安全拦截

**修复方案**: 
1. 在 `ToolRegistry.execute()` 中统一注入安全检查
2. 每个工具 handler 不需要自己做安全检查，由注册表统一拦截

---

### ARCH-002: 两套工具系统并存

**项目中存在两套独立的工具实现**:
1. 根目录 `tools.py` — 直接被 `core.py` 使用
2. `mundo_agent/tools/` — 模块化重构版本

**问题**:
- 两套代码逻辑重复但不完全一致
- 安全行为不一致（根目录版本缺少安全检查，子包版本也缺少）
- 维护成本翻倍

**修复方案**: 统一为一套，推荐保留 `mundo_agent/tools/` 的模块化结构，废弃根目录 `tools.py`。

---

### ARCH-003: 全局单例无生命周期管理

**所有基础设施模块都使用全局单例模式**:
```python
_engine: Optional[PolicyEngine] = None
def get_policy_engine() -> PolicyEngine:
    global _engine
    if _engine is None:
        _engine = PolicyEngine()
    return _engine
```

**涉及文件**: `policy.py`, `security_hardening.py`, `sandbox.py`, `events.py`, `timeline.py`, `cache.py`, `runtime_config.py`, `reflection_engine.py`, `intelligent_recovery.py`, `knowledge_retriever.py`

**问题**:
- 无法在测试中注入 mock
- 无法支持多实例（多会话并行）
- 无清理/重置机制
- 全局状态互相依赖，调试困难

**修复方案**: 引入依赖注入容器或至少使用 `contextvars` 替代 `global`。

---

### ARCH-004: core.py God Object 问题

**`core.py` 的 `MundoEngine` 类承担了过多职责**:
- LLM 调用管理
- 消息历史管理  
- 流式处理
- 错误分类与恢复
- 工具调用编排
- 反射循环
- 安全检查
- 知识检索
- 工作流编排
- 上下文压缩
- 信号处理
- 统计收集

**行数**: 842行，但职责超过12个。

**修复方案**: 拆分为:
- `MundoEngine` — 编排器（组合其他模块）
- `ConversationManager` — 消息历史
- `ToolOrchestrator` — 工具编排
- `StreamHandler` — 流式处理
- `ErrorHandler` — 错误分类与恢复

---

### ARCH-005: 错误处理不一致

**问题**:
- `_classify_error()` 和 `intelligent_recovery.py` 的 `ErrorClassifier` 做同样的事，逻辑重复
- `core.py` 的 `_handle_llm_error()` 和 `intelligent_recovery.py` 的恢复策略重复
- `tools.py` 的 `ToolRegistry.execute()` 捕获所有异常为字符串，丢失了异常上下文

**修复方案**: 统一错误分类和恢复机制。

---

## 🟡 P2 — 代码质量问题

### CODE-001: 导入链过长

**`core.py` 开头有57行 import**，说明核心引擎对太多模块有直接依赖。

**修复方案**: 使用延迟导入或依赖注入减少耦合。

---

### CODE-002: `_normalize_args` 函数缺失

**`tools.py:71`** 调用了 `_normalize_args(args, name)` 但该函数的定义在搜索中未找到完整实现。可能是一个遗留的不完整代码。

---

### CODE-003: 硬编码的魔术数字

**多处硬编码**:
- `tools.py:74`: `"缺少" in result` — 硬编码中文字符串判断
- `memory.py:606`: `f"DELETE FROM [{table_name}]"` — 表名格式
- 各处 timeout、retry 等值散布在代码中

**修复方案**: 集中到 `constants.py`。

---

### CODE-004: `v3_backup/` 目录

项目根目录有 `v3_backup/` 目录，包含旧版代码。应清理或移入版本控制。

---

### CODE-005: 数据库连接未使用连接池

**`memory.py`** 每次操作都 `sqlite3.connect()`，没有连接复用。虽然 SQLite 的 connect 开销不大，但在高频调用场景下仍有优化空间。

**`REFACTOR_SUMMARY.md`** 声称已实现连接池，但 `memory.py` 中的实际代码并未使用。

---

## 🟢 P3 — AI Agent 最佳实践

### AGENT-001: 缺少输入消毒（Prompt Injection 防护）

**`core.py` 的 `_prepare_messages()` 和 `_build_system_message()`** 没有对用户输入做 prompt injection 检测。

**`security_hardening.py`** 定义了 `PROMPT_INJECTION_PATTERNS`，但**从未被调用**。

**最佳实践**: 在用户输入进入上下文前，必须扫描 prompt injection 模式。

---

### AGENT-002: 缺少工具输出消毒

**`ToolRegistry.execute()` 的返回值直接拼接到上下文中**，没有经过 `security.sanitize_output()` 处理。

**风险**: 恶意文件内容（如包含 prompt injection 的文件）可以通过 `read_file` 的输出注入到 LLM 上下文中。

**修复方案**: 工具输出必须经过消毒后再注入上下文。

---

### AGENT-003: 工具循环防护存在但未充分利用

**`tool_guard.py`** 设计良好（Hermes 的三模式检测），但 `core.py` 中的集成只用了基本的检查，没有使用 `HALT` 级别的防护。

---

### AGENT-004: 缺少工具调用的幂等性标记

**Hermes Agent 的最佳实践**: 区分幂等工具（read_file）和非幂等工具（write_file, terminal），对非幂等工具的重复调用应更严格防护。

**当前状态**: `tool_guard.py` 有 `idempotent` 概念但未在注册时标记每个工具。

---

### AGENT-005: 反射引擎的自我评估缺乏客观基准

**`reflection_engine.py`** 的反射完全依赖 LLM 自我评估，没有客观的外部验证机制（如：文件是否真的被创建、测试是否真的通过）。

**最佳实践**: 反射应结合客观指标（工具返回码、文件存在性检查等）。

---

## 🔵 P4 — 网安最佳实践

### SEC-001: API Key 保护

**`llm.py`** 从环境变量读取 API key，但：
- 没有检查 key 是否为空/默认值
- 错误消息中可能泄露 key 片段
- 没有 key 轮换机制

---

### SEC-002: SQLite 数据库无加密

**`memory.db`、`timeline.db`、`checkpoint.db`** 明文存储在磁盘上，包含所有对话历史和记忆数据。

**修复方案**: 使用 SQLCipher 或至少提醒用户注意数据安全。

---

### SEC-003: 日志中可能泄露敏感信息

**`events.jsonl`** (699KB) 记录了所有事件，可能包含敏感的工具调用参数和输出。

---

### SEC-004: 网络请求无 TLS 固定

**`llm.py`** 使用 `http.client` 发起 HTTPS 请求，但没有证书固定（Certificate Pinning），存在中间人攻击风险。

---

## 📋 修复优先级矩阵

| 编号 | 问题 | 严重性 | 修复难度 | 优先级 |
|------|------|--------|----------|--------|
| VULN-001 | eval() 代码执行 | CRITICAL | 简单 | **立即** |
| VULN-002 | shell=True 无安全拦截 | CRITICAL | 中等 | **立即** |
| VULN-003 | mundo_agent shell注入 | CRITICAL | 中等 | **立即** |
| VULN-004 | git_ops shell注入 | HIGH | 简单 | **今天** |
| VULN-005 | os.system 直接执行 | HIGH | 简单 | **今天** |
| ARCH-001 | 安全层未集成 | CRITICAL | 中等 | **今天** |
| ARCH-002 | 两套工具系统 | HIGH | 复杂 | 本周 |
| ARCH-003 | 全局单例无DI | MEDIUM | 复杂 | 本周 |
| ARCH-004 | God Object | MEDIUM | 复杂 | 本周 |
| AGENT-001 | 缺少Prompt Injection防护 | HIGH | 简单 | **今天** |
| AGENT-002 | 缺少输出消毒 | HIGH | 简单 | **今天** |
| AGENT-005 | 反射缺乏客观基准 | MEDIUM | 中等 | 本周 |
| SEC-001 | API Key保护 | MEDIUM | 简单 | 本周 |
| SEC-002 | 数据库无加密 | LOW | 复杂 | 下周 |

---

## 🏗️ 重构路线图

### Phase 1: 紧急安全修复（今天）
1. 修复 eval() 漏洞
2. 统一安全拦截层 — 在 ToolRegistry.execute() 中注入
3. 修复 shell=True → 列表参数
4. 替换 os.system → subprocess
5. 集成 Prompt Injection 检测
6. 集成输出消毒

### Phase 2: 架构统一（本周）
7. 合并两套工具系统
8. 统一错误分类与恢复
9. 引入依赖注入基础
10. 清理 v3_backup/ 和废弃代码

### Phase 3: 深度加固（下周）
11. 工具幂等性标记
12. 反射引擎客观验证
13. API Key 安全加固
14. 日志脱敏
15. 完整测试覆盖

---

*蒙多不接受有漏洞的帝国。每一行代码都必须经得起审视。*
