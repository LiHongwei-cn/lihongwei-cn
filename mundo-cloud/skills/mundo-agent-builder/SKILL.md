---
name: mundo-agent-builder
description: >
  Build standalone AI Agents with LLM direct-connect, tool calling, agentic loop,
  real-time status bar, permission system, and multi-provider support.
  Based on MUNDO Agent architecture (28 AI models, 6 tools, approval system).
tags: [agent, llm, tool-calling, agentic-loop, python, multi-provider]
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

## User Preferences (from MUNDO development)

- User wants FULL independence — not a wrapper around Hermes/Claude Code
- Must support ALL published AI models, not just 5
- API keys MUST be local only (`.env`), never in cloud repos
- Permission prompts MUST match Claude Code's yes/no style
- Real-time status bar showing model/token/time is mandatory
- First-time setup wizard must show all available models with descriptions
