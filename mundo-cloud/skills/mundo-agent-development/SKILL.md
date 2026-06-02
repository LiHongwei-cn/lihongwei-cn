---
name: mundo-agent-development
description: 开发、调试、更新 MUNDO Agent 的完整工作流。覆盖 bug 修复、功能开发、流式输出、连接稳定性、三处同步、GitHub Release 发布。
triggers: mundo, 蒙多, mundo-agent, 蒙多更新, mundo fix, mundo feature
---

# MUNDO Agent 开发工作流

MUNDO 是独立 AI Agent（~/.hermes/mundo-agent/），拥有 LLM 直连 + 工具调用 + Agentic Loop + Agent 调度。

## 核心文件

| 文件 | 职责 |
|------|------|
| `mundo.py` | 入口 + CLI + 命令处理 + 回调注册 |
| `engine.py` | Agentic Loop（think → act → observe → repeat） |
| `llm.py` | 多模型 LLM 客户端（流式 + 非流式 + 重试） |
| `display.py` | 执行控制台（流式输出 + 实时仪表盘） |
| `delegation.py` | 任务拆分 + 并行执行 + 结果汇总 |
| `agents.py` | Agent 检测 + 调度 + 蒙多分身 |
| `memory.py` | 三层记忆系统 |
| `tools.py` | 6 大工具实现 |
| `setup.py` | 首次设置向导 + Provider 配置 |

## 三处同步铁律（每次修改必须执行）

每次代码改动必须同步到三处，缺一不可：

1. **本地** `~/.hermes/mundo-agent/` — 用户实际运行的副本
2. **仓库** `~/Desktop/lihongwei-cn/mundo-agent/` — Git 跟踪
3. **GitHub** `origin/main` — 远程推送

```bash
# 同步步骤
cp ~/.hermes/mundo-agent/<changed_files> ~/Desktop/lihongwei-cn/mundo-agent/
cd ~/Desktop/lihongwei-cn && git add mundo-agent/<files> && git commit -m "<type>: <desc>" && git push
```

验证同步：
```bash
diff ~/.hermes/mundo-agent/<file> mundo-agent/<file> && echo "✓ 一致"
git log --oneline origin/main -1
```

## 四处内容同步（功能更新时）

除代码外，还需更新：
1. **根 README.md** — 功能列表、版本号（中/英/日/韩四语）
2. **mundo-agent/index.html** — 网站页面、changelog、下载链接
3. **mundo-agent/README.md** — 项目 README
4. **GitHub Release** — zip 包（macOS/Windows/Linux/全平台）

```bash
gh release create mundo-v<version> \
  /tmp/mundo-v<version>-macos.zip \
  /tmp/mundo-v<version>-windows.zip \
  /tmp/mundo-v<version>-linux.zip \
  /tmp/mundo-v<version>-all.zip \
  --title "MUNDO Agent v<version> — <主题>" \
  --notes "## v<version> 更新..."
```

## 版本号管理

`mundo.py` 中 `VERSION = "x.y.z"` 是硬编码，不读 version.txt。更新时两处都要改。

## 关键 Pitfalls

### 1. None content 崩溃（CRITICAL）
```python
# 错误：content 存在但值为 None 时，.get("content", "") 返回 None
m.get("content", "")

# 正确：or "" 兜底
m.get("content") or ""
```
这条规则适用于所有访问 message content 的地方：memory.py、engine.py、mundo.py、display.py。
记忆压缩、上下文计算、流式估算——任何涉及 message content 的地方都要检查。

### 1b. tool_call JSON 损坏（CRITICAL）
LLM 可能返回截断的 JSON 参数（如 `{"path`），导致：
- `json.loads` 失败 → tool_args 为 `{}` → 工具缺参报错
- 损坏的 assistant 消息（含无效 tool_calls）存入 messages
- 下次 API 调用发送损坏消息 → API 400 "unexpected end of data"

**三层防御：**
```python
# 第1层：引擎侧修复截断 JSON
@staticmethod
def _repair_json(raw: str):
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # 补全缺失的括号和引号
    open_braces = raw.count("{") - raw.count("}")
    quote_count = raw.count('"') - raw.count('\\"')
    if quote_count % 2 != 0:
        raw += '"'
    raw += "}" * max(0, open_braces)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None  # 无法修复 → 丢弃该 tool_call

# 第2层：过滤无效 tool_calls
valid_tool_calls = []
for tc in tool_calls:
    func = tc.get("function", {})
    if not func.get("name"):
        continue
    raw_args = func.get("arguments", "{}")
    try:
        json.loads(raw_args)
        valid_tool_calls.append(tc)
    except json.JSONDecodeError:
        fixed = _repair_json(raw_args)
        if fixed is not None:
            tc["function"]["arguments"] = json.dumps(fixed)
            valid_tool_calls.append(tc)

# 第3层：API 发送前清洗
# _sanitize_messages() 检查所有 tool_calls 的 arguments
# 损坏的 → 替换为 "{}"
```

### 1c. 工具参数验证（CRITICAL）
所有 tool handler 必须用 `args.get()` 而非 `args[]`，缺参返回清晰错误：
```python
def _run_write_file(args: Dict) -> str:
    path = args.get("path", "")
    if not path:
        return "[错误: write_file 缺少 path 参数]"
    content = args.get("content", "")
    if not content:
        return "[错误: write_file 缺少 content 参数]"
```
每个 handler 开头都验证必填参数。execute_tool 已有 try/except，但返回清晰错误比捕获 KeyError 更好。

### 2. 回调被覆盖
mundo.py 中 `on_turn_end` 等回调可能被后面的代码覆盖为空 lambda。注册回调后检查是否被覆盖：
```bash
grep -n "on_turn_end" mundo.py
```

### 3. 流式输出与 prompt_toolkit 冲突（CRITICAL）
`print_formatted_text(PT_ANSI(...))` 和 `sys.stdout.write()` 在 `patch_stdout` 上下文中混用会冲突：
- ANSI 码双重编码 → 显示为 `?[2m` 裸码
- 输出位置错乱

**规则：选一种输出方式，不混用。**
- 流式输出用 `sys.stdout.write(text)` + `sys.stdout.flush()`
- 结构化日志用 `print_formatted_text(PT_ANSI(...))`
- 状态栏追加用 `sys.stdout.write(f"\033[2m[status]\033[0m")`

不要在 `stream_text` 中用 `print_formatted_text` 包裹已含 ANSI 码的文本。

### 4. SSE 流式读取
`resp.read(1024)` 可能阻塞。用 `for raw_line in resp:` 逐行读取更稳定。

### 5. Token 估算（API 不返回 usage 时）
```python
# 基于消息总长度估算 prompt tokens
total_chars = sum(len((m.get("content") or "")) for m in messages)
prompt_tokens = total_chars * 2 // 3

# 基于已输出文字量估算 completion tokens
completion_tokens = len(stream_buffer) * 2 // 3
```

### 6. 流式降级
某些 provider 不支持 `stream=True`。引擎应先尝试流式，失败后自动降级到非流式。

### 7. Agent 失败降级
外部 Agent（Claude Code/Hermes）可能超时。应自动降级到蒙多分身执行。

## 输入框（prompt_toolkit）

多行输入需要自定义 KeyBindings：
- Enter 在末尾 → 提交
- Enter 在中间 → 换行（自由编辑）
- Option+Enter → 强制提交
- `multiline=True` 启用多行编辑

## 用户偏好

- 用户每次修改后都会问"有没有同步更新"——**主动展示三处同步状态**（local/remote/GitHub），不需要用户问
- 用户要求实时反馈：token 消耗（逐个往上跳）、运行时间、子任务进度（开始/完成/失败）
- 用户要求所有 AI 模型连接都有重试机制（3次+指数退避）
- 版本更新时必须同步 README + index.html + 项目 README + GitHub Release
- 用户会逐行审查 UI 输出——ANSI 裸码、重复输出、缺少反馈都是不可接受的
- 输入框必须支持粘贴多行文本后自由移动光标，末尾回车提交

## 委派执行进度回调

delegation.py 的 `execute_parallel` 必须有实时进度回调：
```python
# 回调签名: (subtask_id, task_desc, agent_name, phase, preview)
self.on_subtask_progress: Optional[Callable] = None

# 在 execute_parallel 中每个子任务开始/完成/失败时调用
if self.on_subtask_progress:
    self.on_subtask_progress(st["id"], st["task"], agent_name, "start", None)
```
phase 值: "start" / "done" / "error"。用户看不到进度 = 用户认为蒙多卡死了。
