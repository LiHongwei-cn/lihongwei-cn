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

## Architecture (4 layers)

1. **LLM Client** — OpenAI-compatible API, multi-provider support
2. **Tool Engine** — terminal/file/web/search with schema + handler
3. **Agentic Loop** — call LLM → parse tool_calls → execute → inject results → repeat
4. **Status Bar** — real-time model/token/time/turn display

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
━━ 任务分发 ━━
  ▸ 调用 Claude Code...
  👑 分身 #1 已出动
  👑 分身 #2 已出动
  共 3 个子任务
```

## Pitfalls

- **MiMo base_url**: Use `/v1` not `/anthropic` (404)
- **/tmp paths**: Must be classified as `safe` in approval system, not `caution`
- **env fallback**: Always check `~/.hermes/.env` first, then mundo `.env`
- **setup wizard in non-interactive mode**: `-q` flag must skip setup if no `.setup_complete`
- **Task splitting keywords**: Need ≥2 keyword hits to trigger (1 hit is too aggressive)
- **External agent timeout**: Claude Code gets 600s, Hermes gets 300s

## User Preferences (from MUNDO development)

- User wants FULL independence — not a wrapper around Hermes/Claude Code
- Must support ALL published AI models, not just 5
- API keys MUST be local only (`.env`), never in cloud repos
- Permission prompts MUST match Claude Code's yes/no style
- Real-time status bar showing model/token/time is mandatory
- First-time setup wizard must show all available models with descriptions
