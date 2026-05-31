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

## Terminal UI Design (LESSONS LEARNED)

The user has an extremely strong preference for minimal, clean terminal UI. **Do NOT use emoji icons in the status/input area.** What NOT to do:

```
BAD (5-line bottom, 3 emoji icons — user called this "太繁杂"):
  📊 5.8K tokens (3.2K→2.6K) ⏱ 12.3s T3 · 2 tools
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ← gold bar
  👑 xiaomi/mimo-v2.5-pro · v24.3                    ← model line
  > 用户输入
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ← gold bar
```

```
GOOD (3-line bottom, Hermes style, flat status — user approved):
  MUNDO · xiaomi/mimo-v2.5-pro · 5.8K tokens · ⏱ 12.3s · T3
  ──────────────────────────────────────────────────
  > 用户输入
```

Rules:
- **BOTTOM_LINES = 3** (status + separator + input). No more.
- **No emoji** in status bar or input area. Text-only, dot-separated.
- **One thin separator line** (`─` * terminal_width), not gold bars (`━`).
- Status line is flat: `MUNDO · model · tokens · ⏱ elapsed · turns`
- Input prompt is just `> ` with no decoration.

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

## Sync Workflow (MANDATORY)

After ANY code change to Mundo agent files, sync these three places **without being asked**:
1. `cp` to local install dir `~/.hermes/mundo-agent/`
2. Update `README.md` version numbers + feature descriptions (all 4 languages: zh/en/ja/ko)
3. Update website `mundo-agent/index.html` and main `index.html`
4. `git add + commit + push`

## Smart Routing (v24.3+)

Simple chat consumes way too many tokens if you send full system prompt + all tool schemas. Detect conversation type and route to a lighter path.

### Detection Logic (`_is_simple_chat()`)
- Short message (≤20 chars) → chat
- Greeting/filler patterns (`你好|hi|hello|谢谢|ok|好的`) → chat
- Question patterns (`什么是|谁是|解释一下|你觉得`) → chat
- Ends with `?`/`？` and < 80 chars → chat
- Contains task keywords (`写|创建|修复|搜索|代码|脚本|帮我`) → task
- > 200 chars → task
- Default: < 60 chars → chat, else → task

### Two Paths
| | Chat Mode | Task Mode |
|---|---|---|
| System prompt | ~50 chars (MUNDO_CHAT_PROMPT) | ~500 chars (full) |
| Tools | None (tools=None) | TOOL_SCHEMAS |
| max_tokens | 512 | 4096 |
| Context | Separate chat_messages, last 10 turns | Full messages with compression |

**Expected savings**: 60-80% token reduction for casual conversation.

### Context Auto-Compression
When `len(messages) > 20`, compress: keep system + last 8 messages + summary of middle. Summary is `[user] ... | [assistant] ...` concatenated, capped at 400 chars.

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
- **Memory import on first deploy**: Read `~/.claude/CLAUDE.md` for user preferences, `~/.hermes/.env` for API keys. Use `.memory_imported` flag to avoid re-scanning. See `references/memory-import-pattern.md` for full implementation.
- **Output stream design**: Log methods (`log_thinking`, `log_tool_start`, `log_tool_output`, `log_tool_done`) must ONLY write to stdout. Do NOT call status bar redraws between log lines. The output should be a clean scroll stream. Status/info bar shows only at: task start, task done.

## References

- `references/mundo-agent-architecture.md` — 28-provider model catalog, API quirks
- `references/agent-delegation-pattern.md` — Task splitting, agent assignment, result merging
- `references/memory-system-v2-architecture.md` — 3-layer memory (hot/warm/cold)
- `references/terminal-ui-patterns.md` — Scroll region pitfall, safe ANSI codes, raw input, banner duplication, output stream design
- `references/context-management-commands.md` — /compact /context /btw /effort implementation
- `references/cloud-sync-pattern.md` — Skill upload/download, quality scoring
- `references/memory-import-pattern.md` — First-deploy memory import from Hermes/Claude Code
- `references/smart-routing-token-optimization.md` — Chat vs task detection, dual-path LLM routing, context compression

## User Preferences (from MUNDO development)

- User wants FULL independence — not a wrapper around Hermes/Claude Code
- Must support ALL published AI models, not just 5
- API keys MUST be local only (`.env`), never in cloud repos
- Permission prompts MUST match Claude Code's yes/no style
- Real-time status bar showing model/token/time is mandatory
- First-time setup wizard must show all available models with descriptions
