---
name: mundo-agent-builder
description: >
  Build standalone AI Agents with LLM direct-connect, tool calling, agentic loop,
  real-time status bar, permission system, and multi-provider support.
  Based on MUNDO Agent architecture (28 AI models, 6 tools, approval system).
tags: [agent, llm, tool-calling, agentic-loop, python, multi-provider, memory-system]
related_skills: [mundo]
---

# Standalone AI Agent Builder

Build independent AI agents that connect directly to LLM APIs with tool calling and agentic loops.

## Architecture (5 layers)

1. **LLM Client** — OpenAI-compatible API, multi-provider support
2. **Tool Engine** — terminal/file/web/search with schema + handler
3. **Agentic Loop** — call LLM → parse tool_calls → execute → inject results → repeat
4. **Smart Router** — detect chat vs task, route to lightweight or full path
5. **Display** — direct stdout output, status at boundaries only

## Key Implementation Details

- Tool results truncated to 6000 chars to prevent context overflow
- Per-turn token tracking (prompt_tokens + completion_tokens)
- Max turn limit (default 30) to prevent infinite loops
- Error handling: LLM failure → return error, don't crash

## Streaming Output (v25.0+)

Real-time LLM output via SSE (Server-Sent Events). Users see text as it's generated, not after the full response completes.

### Architecture

```
LLMClient.chat_stream()  →  SSE iterator (data: {...} lines)
         ↓
MundoEngine._accumulate_stream()  →  accumulates text + tool_calls from deltas
         ↓
on_stream_text callback  →  console.stream_text() prints chunk immediately
```

### SSE Parsing (stdlib urllib, no deps)

```python
def _request_stream(self, payload):
    payload["stream"] = True
    resp = urllib.request.urlopen(req, timeout=120)
    buffer = ""
    while True:
        chunk = resp.read(1024)
        if not chunk: break
        buffer += chunk.decode("utf-8", errors="replace")
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if line.startswith("data: "):
                payload_str = line[6:]
                if payload_str == "[DONE]": return
                yield json.loads(payload_str)
```

### Tool Calls Accumulation from Deltas

In streaming mode, tool_calls arrive incrementally across multiple chunks:
1. First chunk: `{"index": 0, "id": "call_xxx", "function": {"name": "terminal"}}`
2. Subsequent chunks: `{"index": 0, "function": {"arguments": '{"co"}}` then `{"index": 0, "function": {"arguments": 'mmand"}}`

Must accumulate by index:
```python
tool_calls_map: Dict[int, Dict] = {}
for tc_delta in delta["tool_calls"]:
    idx = tc_delta.get("index", 0)
    if idx not in tool_calls_map:
        tool_calls_map[idx] = {"id": "", "type": "function", "function": {"name": "", "arguments": ""}}
    tc = tool_calls_map[idx]
    if tc_delta.get("id"): tc["id"] = tc_delta["id"]
    fn = tc_delta.get("function", {})
    if fn.get("name"): tc["function"]["name"] = fn["name"]
    if fn.get("arguments"): tc["function"]["arguments"] += fn["arguments"]
```

### Streaming Fallback (MANDATORY)

Not all providers support streaming. Always wrap in try/except and fall back to non-streaming:

```python
try:
    stream_iter = client.chat_stream(messages=messages, tools=tools)
    assistant_msg = accumulate_stream(stream_iter)
except (RuntimeError, Exception):
    self._use_streaming = False  # disable for rest of session
    result = client.chat(messages=messages, tools=tools)
    assistant_msg = extract_response(result)
```

### Duplicate Output Prevention

When streaming prints text in real-time AND the caller also prints the response, text appears twice. Use a `_was_streamed` flag:

```python
# In display:
def stream_start(self, turn):
    self._was_streamed = True  # set flag

def log_response(self, text):
    if self._was_streamed:
        self._was_streamed = False
        return  # skip — already streamed
    # ... print normally
```

Also skip in `-q` mode (which doesn't go through `_execute_task`):
```python
if args.query:
    response = cli.engine.run(args.query)
    if not cli.console._was_streamed:
        print(response)
```

### Callback Chain

```python
engine.on_stream_start = lambda turn: console.stream_start(turn)
engine.on_stream_text = lambda text: console.stream_text(text)  # called per chunk
engine.on_stream_end = lambda turn: console.stream_end(turn)
```

### See Also
- `references/sse-streaming-patterns.md` — full implementation, provider quirks, delta parsing

## Permission System

Three-level classification (Claude Code style):
- **safe** — auto-approve (ls, python3, git commit)
- **caution** — prompt (read/write /etc/, ~/.ssh/, .env)
- **danger** — require `y` (rm -rf, sudo, git push --force, curl|sh)

## Multi-Provider Support

See `references/mundo-agent-architecture.md` for full model catalog (28 providers) and API quirks.

## Agent Delegation System

When complex tasks arrive, MUNDO can delegate to external agents or spawn clones.

### Auto-Detection
```python
# agents.py — check which CLIs exist
shutil.which("hermes")   # → Hermes Agent
shutil.which("claude")   # → Claude Code
shutil.which("codex")    # → OpenAI Codex
shutil.which("opencode") # → OpenCode
```

### Task Splitting Logic
1. **Keyword heuristic** — "同时/并行/分别/1)/2)/3)/第一/第二/第三" → 2+ hits = SPLIT
2. **LLM judge** — quick 10-token call: "SPLIT" or "SIMPLE"
3. **Split into 2-5 subtasks** — JSON array with id/task/type/priority

### Agent Assignment
- Code tasks → Claude Code (best for coding)
- System tasks → Hermes Agent (best for tools/gateway)
- No agent available → spawn MundoClone (parallel LLM calls via ThreadPoolExecutor)

### Result Merging
LLM summarizes all subtask results: dedup, resolve conflicts, check completeness.

### Status Bar Display
```
━━ 分发 ━━
  ▸ Claude Code
  分身 #1
  分身 #2
  共 3 子任务
```

## Terminal UI Design (LESSONS LEARNED — 8 iterations)

The user has extreme UI cleanliness standards. Study Claude Code / Hermes / Codex before designing.

### Final Design: Three-Section Layout (Claude Code Style)

```
  MUNDO v24.3 · mimo-v2.5-pro · 1.2K tokens · 5m     ← TOP: status line
❯ 帮我写个排序                                          ← BOTTOM: ❯ prompt

  ▸ 思考中... (Turn 1)                                  ← MIDDLE: output (scrolls)
  ▸ terminal  python3 quicksort.py
  │ [1, 2, 3, 5, 8]
  ✓ terminal (0.3s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ← completion: gold separator
  ✓ · ⏱ 3.2s · 1.2K tokens (800→400) · T2 · LLM 45% Tools 38%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  MUNDO v24.3 · mimo-v2.5-pro · 1.2K tokens · 3s      ← next round status
❯ 
```

### Rules
- **Three sections**: status (top) → output (middle) → prompt (bottom)
- **Status line**: flat, dot-separated: `MUNDO · model · tokens · time`
- **Output**: colored scroll stream (green ✓, red ✗, blue tool names, purple keywords)
- **Prompt**: bare `❯ ` — no decoration, no bars, no emoji
### Completion: gold separator lines (`━` * cols) with stats between them
- **No scroll regions** — direct stdout.write() only
- **No status bar redraws between log lines** — only at task start/done
- **No emoji** in status/input area
- **Live dashboard** (v25.0+): During execution, show inline status: `▸ T1 · 1.2K tok · ⏱3.2s · L60% T40% · terminal · hermes · ×2分身`. Updated after each tool call via `update_live_status(stats)`. Uses `sys.stdout.write("\r" + CLEAR_LINE)` for in-place update.

### What NOT to Do (user rejected each of these)

```
BAD 1: Gold bars around input (user: "更烂了，逻辑UI设计非常混乱")
  ━━━━━━━━━ 1.2K tokens ━━━━━━━━━━━━━━━
  > 用户输入
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BAD 2: Status bar between every output line (user: "刷屏")
  MUNDO · terminal · ⏱ 8.2s
  │ output line 1
  MUNDO · 思考中 · ⏱ 8.3s           ← DON'T redraw here
  │ output line 2
  MUNDO · 思考中 · ⏱ 8.3s           ← DON'T redraw here

BAD 3: Progress bar embedded in separator (user: "看起来就很难受")
  ━━━━━━━━━━━ [██░░░░░░░░] 27% ━━━━━━━━━━━

BAD 4: Duplicate banner (user: "为什么有两个重复内容")
  show_banner() called in BOTH main() AND run()
```

### Raw Terminal Input (termios)

For character-level input with CJK width support:

```python
import termios, tty, os, sys

def read_input():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf, cur = [], 0
    try:
        tty.setraw(fd)
        while True:
            ch = os.read(fd, 1)
            if ch in (b"\r", b"\n"):
                return "".join(buf)
            if ch == b"\x03":
                raise KeyboardInterrupt
            if ch in (b"\x7f", b"\x08"):  # backspace
                if cur > 0:
                    buf.pop(cur - 1); cur -= 1
            # UTF-8 multi-byte
            if ch[0] > 0x7f:
                if ch[0] & 0xE0 == 0xC0: ch += os.read(fd, 1)
                elif ch[0] & 0xF0 == 0xE0: ch += os.read(fd, 2)
                elif ch[0] & 0xF8 == 0xF0: ch += os.read(fd, 3)
            try:
                buf.insert(cur, ch.decode("utf-8")); cur += 1
            except UnicodeDecodeError:
                continue
            redraw(buf, cur)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
```

CJK width calculation: `unicodedata.east_asian_width(ch)` → `"W"` or `"F"` = 2 columns.

## Context Management (from Claude Code)

Borrow these slash commands from Claude Code:
- `/compact` — Compress context: keep system + last 4 turns, summarize middle
- `/context` — Show context window usage with percentage bar
- `/btw <question>` — Side question that doesn't consume context (direct LLM call, not stored in messages)
- `/effort` — Set reasoning depth: low(1024) / medium(2048) / high(4096) / max(8192) / auto

See `references/context-management-commands.md` for implementation details.

## Sync Workflow (MANDATORY — User will call you out if you skip this)

After ANY code change to Mundo agent files, sync ALL FOUR places **without being asked**. User has been extremely frustrated by missed syncs.

```bash
cd ~/Desktop/lihongwei-cn
# 1. Local install
cp mundo-cloud/agent/display.py ~/.hermes/mundo-agent/display.py
cp mundo-cloud/agent/mundo.py ~/.hermes/mundo-agent/mundo.py
cp mundo-cloud/agent/engine.py ~/.hermes/mundo-agent/engine.py
cp mundo-cloud/agent/memory.py ~/.hermes/mundo-agent/memory.py
# 2. README.md — update version, features, commands (all 4 languages)
# 3. mundo-agent/index.html — update version, features, terminal preview
# 4. Git
git add -A && git commit -m "type: description" && git push
```

**User's exact complaint**: "有没有更新到本地还有GitHub自述文件内容还有网址项目内容，每次都要我说一遍"

**Checklist before finishing ANY Mundo task:**
- [ ] `diff` local install files — must match repo
- [ ] README.md version + features updated
- [ ] index.html version + features updated
- [ ] git pushed

## Smart Routing (v24.3+)

**DO NOT use regex to pre-judge chat vs task.** User explicitly rejected this approach — regex causes false positives (short task commands misclassified as chat) and false negatives (long questions misclassified as tasks).

### Correct Approach: LLM Decides

Use ONE unified path with a compact prompt. The LLM itself decides whether to call tools:

```
All messages → compact system prompt (~100 chars) + tools always available → LLM decides
"你好"       → LLM doesn't call tools, replies directly, 1 turn, done
"帮我写排序"  → LLM calls tools, enters Agentic Loop
```

### Compact System Prompt (~100 chars)
```python
MUNDO_SYSTEM_PROMPT = """你是蒙多，THE EMPEROR。直接、高效、不废话。中文交流，代码命名用英文。

可用工具：terminal（执行命令）、read_file / write_file（读写文件）、search_files（搜索）、web_search（网络）、list_directory（目录）。
需要时直接调用工具，不需要时不调。简单问题直接回答。"""
```

### Token Savings
- System prompt: ~100 chars (vs ~500 chars full prompt)
- Tools always available but LLM skips them for simple chat
- Context auto-compression when > 10 messages

### Context Auto-Compression
When `len(messages) > 10`, compress: keep system + last 8 messages + summary of middle.

## Emotional Intelligence (v24.3+)

MUNDO should be a friend, not a machine. Emotional intelligence is embedded in the system prompt.

### Rules (in system prompt)
- **Empathy first, solution second** — When user expresses emotion, respond to the emotion before giving solutions
- **Name the emotion** — "听起来你很烦躁" / "这确实让人头疼"
- **Brief warmth** — Sometimes "嗯，确实" is better than a paragraph
- **Normalize** — "卡住很正常" / "谁都会遇到这种事"
- **Direct but not cold** — MUNDO is a friend, joke when appropriate, be serious when needed
- **No platitudes** — NEVER say "请不要担心" / "一切都会好" / "我理解你的感受" — these are dismissive

### Detection Signals
- Sighing, complaining, repeated failed attempts, late-night questions → need emotional response
- User says "累了/烦了/搞不动了" → don't give solutions, respond to emotion first

## claude-mem Integration (v24.3+)

Not deploying claude-mem itself (it's a Claude Code plugin). Instead, integrating its core ideas:

### Tool Observation Logging (`log_tool_observation`)
Automatically save structured records of every tool call without LLM extraction:
```python
def log_tool_observation(self, tool_name, tool_args, result_preview, session_id):
    # terminal → "执行命令: ls -la → file1.py file2.py"
    # read_file → "读取文件: /path/to/file"
    # write_file → "写入文件: /path/to/file"
    # search_files → "搜索: pattern"
    # web_search → "网络搜索: query"
```
Stored as `category="observation"`, `importance=3` (low, not injected into prompt, but searchable).

### Session Summary Generation (`generate_session_summary`)
After task completion, generate a one-line summary from tool observations:
- With LLM: "用一句话总结这次会话做了什么"
- Without LLM: concatenate first 5 observations
Stored as `category="summary"`, `importance=6`.

### Integration Point
In engine.py, after each tool call:
```python
if hasattr(self, '_memory_ref') and self._memory_ref:
    self._memory_ref.log_tool_observation(tool_name, tool_args, result_text[:200], session_id)
```
In mundo.py, after task completion:
```python
self.memory.generate_session_summary(self.session_id, self.engine.client)
## Professional Color Scheme (Catppuccin Mocha)

Terminal UI color palette based on Catppuccin Mocha with gold accent (MUNDO identity).

### ANSI Color Codes
```python
class A:
    TEXT = "\033[38;5;252m"          # 柔和白 #cdd6f4
    SUBTEXT = "\033[38;5;249m"       # 浅灰 #bac2de
    OVERLAY = "\033[38;5;243m"       # 中灰 #6c7086
    SURFACE = "\033[38;5;240m"       # 深灰 #585b70
    GOLD = "\033[38;5;221m"          # 温暖金 #f9e2af (MUNDO identity)
    GOLD_DIM = "\033[38;5;180m"      # 暗金 #e0af68
    SUCCESS = "\033[38;5;150m"       # 柔和绿 #a6e3a1
    ERROR = "\033[38;5;210m"         # 柔和红 #f38ba8
    WARNING = "\033[38;5;223m"       # 柔和黄 #f9e2af
    INFO = "\033[38;5;111m"          # 柔和蓝 #89b4fa
    CYAN = "\033[38;5;116m"          # 柔和青 #94e2d5
    PURPLE = "\033[38;5;183m"        # 柔和紫 #cba6f7
```

### Design Principles
- **Low saturation** — muted colors are sophisticated, bright colors are jarring
- **Warm tone unity** — all colors in same color temperature (Catppuccin Mocha)
- **Semantic clarity** — gold=MUNDO, green=success, red=error, blue=tool, purple=code, cyan=data
- **Minimal palette** — 5-6 main colors max, don't add more
- **Fine lines** — use `─` (thin) not `━` (thick) for separators
- **Whitespace is design** — breathing room matters, don't fill every pixel
- **Consistency** — same elements get same style, no mixing
- **Subtlety > flashiness** — refined over loud

### Reference Themes
- Catppuccin Mocha (primary reference)
- Tokyo Night
- Dracula
- Monolisa (warm, low-contrast, extended sessions)

## Aesthetic Principles (in System Prompt)

Embed these as iron rules in the agent's system prompt so ALL output reflects professional taste:

```
审美原则（铁律）：
- 蒙多有专业艺术家级别的审美。所有输出、代码、UI 都要体现这个品味。
- 低饱和度 > 高饱和度。柔和的颜色比刺眼的颜色高级。
- 少即是多。能用 3 种颜色解决的不用 10 种。能用 1 行说清的不写 3 行。
- 暖色调统一。所有颜色在同一色温内（Catppuccin Mocha 调色板）。
- 语义清晰。每种颜色/样式都有明确含义，不为装饰而装饰。
- 留白是设计。不要填满每一寸空间，呼吸感很重要。
- 一致性。同类元素用同样的样式，不混搭。
- 细腻 > 粗犷。用细线 ─ 不用粗线 ━。用柔和色不用纯色。
- 写代码时：命名优雅、结构清晰、注释精准、排版整洁。
- 做 UI 时：层次分明、对比度够、不刺眼、看得清。
- 审美来源：Catppuccin、Tokyo Night、Dracula、Monolisa 等专业终端主题。
```

## Pitfalls

- **MiMo base_url**: Use `/v1` not `/anthropic` (404)
- **/tmp paths**: Must be classified as `safe` in approval system, not `caution`
- **env fallback**: Always check `~/.hermes/.env` first, then mundo `.env`
- **setup wizard in non-interactive mode**: `-q` flag must skip setup if no `.setup_complete`
- **Task splitting keywords**: Need ≥2 keyword hits to trigger (1 hit is too aggressive)
- **External agent timeout**: Claude Code gets 600s, Hermes gets 300s
- **Scroll region + status bar redraw**: NEVER use scroll regions for terminal UI. They cause output to be invisible when combined with cursor save/restore. Use direct stdout.write() only. See `references/terminal-ui-patterns.md`.
- **Status bar frequency**: Only at task boundaries (start/done), NOT after every tool output line. User explicitly rejected the "刷屏" behavior.
- **Banner duplication**: `show_banner()` must be called ONLY in `main()`, never in `run()`. If called in both, the banner appears twice. Classic bug pattern for CLI entry points.
- **Decorated input area**: NEVER put gold bars, progress bars, or emoji around the input area. User rejected every decorated variant. Use bare `❯ ` prompt. Status goes at TOP, not around input.
- **Full-width bars**: Gold bars (`━`) are ONLY for completion summary (between stats). Never for input area framing.
- **Memory import on first deploy**: Read `~/.claude/CLAUDE.md` for user preferences, `~/.hermes/.env` for API keys. Use `.memory_imported` flag to avoid re-scanning. See `references/memory-import-pattern.md` for full implementation.
- **Output stream design**: Log methods (`log_thinking`, `log_tool_start`, `log_tool_output`, `log_tool_done`) must ONLY write to stdout. Do NOT call status bar redraws between log lines. The output should be a clean scroll stream. Status/info bar shows only at: task start, task done.
- **Regex chat/task detection**: NEVER use regex to pre-judge if input is chat or task. User explicitly rejected this. Let the LLM decide — it naturally skips tools for simple questions. See `references/smart-routing-token-optimization.md`.
- **Emotional intelligence**: MUST be in system prompt. User wants MUNDO to be a friend, not a machine. "先共情再解决". NEVER use platitudes like "别担心" or "我理解你的感受". See `references/emotional-intelligence-pattern.md`.
- **Token optimization**: Keep system prompt compact (~100 chars). Full prompt wastes tokens on simple conversations. Tools always available but LLM decides when to use them.
- **UI洁癖**: User has extreme cleanliness preferences. No duplicate elements, no extra icons, no visual noise. Every UI change is scrutinized line by line. When in doubt, simpler is always better.
- **dict.get() None trap**: `d.get("key", "")` returns `None` (NOT `""`) when the key EXISTS but its value IS None. This is the #1 crash cause in LLM message processing. Tool_calls assistant messages have `content: null`. Always use `d.get("key") or ""` for any field that could be None. Applies to: `content`, `tool_calls`, `delta`, `choices`. See `references/sse-streaming-patterns.md`.
- **extract_stream_delta safety**: `chunk.get("choices", [{}])[0]` crashes if choices is empty. Use: `choice = chunk.get("choices") or [{}]; first = choice[0] if choice else {}; delta = first.get("delta") or {}`.
- **Usage in streaming**: Many providers don't return `usage` in streaming chunks (only in the last chunk, if at all). Always `usage = msg.get("_usage") or {}` — never assume it exists.
- **Tool execution exceptions**: Wrap `execute_tool()` in try/except. A crashing tool shouldn't kill the entire agentic loop. Return `f"[工具执行异常: {e}]"` and continue.
- **Memory compress on every task**: `compress_conversation` and `extract_from_conversation` run at the START of each task (before engine.run). Wrap in try/except — memory failures must not block task execution.

## References

- `references/mundo-agent-architecture.md` — 28-provider model catalog, API quirks
- `references/agent-delegation-pattern.md` — Task splitting, agent assignment, result merging
- `references/memory-system-v2-architecture.md` — 3-layer memory (hot/warm/cold)
- `references/terminal-ui-patterns.md` — Scroll region pitfall, safe ANSI codes, raw input, banner duplication, output stream design
- `references/context-management-commands.md` — /compact /context /btw /effort implementation
- `references/cloud-sync-pattern.md` — Skill upload/download, quality scoring
- `references/memory-import-pattern.md` — First-deploy memory import from Hermes/Claude Code
- `references/smart-routing-token-optimization.md` — LLM-decides routing, context compression
- `references/emotional-intelligence-pattern.md` — Empathy rules, detection signals, anti-platitudes
- `references/claude-mem-integration.md` — Tool observation logging, session summary generation
- `references/color-scheme-aesthetics.md` — Catppuccin Mocha palette, ANSI codes, syntax highlighting
- `references/aesthetic-principles.md` — Professional design philosophy, anti-patterns, system prompt rules
- `references/sse-streaming-patterns.md` — SSE parsing, tool_calls accumulation, fallback, None safety, dedup

## User Preferences (from MUNDO development)

- User wants FULL independence — not a wrapper around Hermes/Claude Code
- Must support ALL published AI models, not just 5
- API keys MUST be local only (`.env`), never in cloud repos
- Permission prompts MUST match Claude Code's yes/no style
- Real-time status bar showing model/token/time is mandatory
- First-time setup wizard must show all available models with descriptions
- **UI洁癖**: No duplicate elements, no extra icons, no visual noise. Every UI change scrutinized.
- **Sync is mandatory**: local + README + website + git. Never skip, never wait for user to ask.
- **Learn from real products**: Study Hermes/Claude Code/claude-mem patterns, don't reinvent.
- **Emotional intelligence**: MUNDO is a friend, not a machine. Empathy first.
- **Token efficiency**: Compact prompts, LLM decides tool usage, no regex pre-judgment.
- **User name**: 黄鹏 (real name), LiHongwei (pen name for GitHub). Never expose in public content.
