---
name: python-agent-dev
description: Python AI Agent 开发模式 — SSE 流式输出、prompt_toolkit TUI、Agentic Loop 回调链、API 响应安全处理
triggers: ["SSE 流式", "prompt_toolkit", "Agentic Loop", "LLM 流式输出", "终端 UI", "Agent 开发", "tool_calls 增量"]
---

# Python AI Agent 开发模式

构建独立 AI Agent 时的通用模式、陷阱和最佳实践。

## 核心模式

### 1. API 响应安全处理（CRITICAL）

所有 API 响应字段都可能是 `None`，即使 key 存在。

```python
# 错误 — content=None 时 len(None) 崩溃
m.get("content", "")

# 正确 — 用 or "" 兜底
m.get("content") or ""
```

OpenAI 兼容 API 中 tool_calls 消息：`{"content": null, "tool_calls": [...]}`

### 2. SSE 流式输出

用 `for raw_line in resp:` 而非 `resp.read(1024)`。后者可能阻塞。

流式 delta 的 `content`、`tool_calls` 字段可能为 null，必须 `or` 兜底。

tool_calls 在流式模式下分多 chunk 到达，需按 index 累积拼接。

### 3. 流式 token 估算

部分 provider 不返回 usage 数据。基于消息长度和已输出文字量估算：
- prompt_tokens = 总消息字符数 × 2/3
- completion_tokens = 已输出字符数 × 2/3

### 4. prompt_toolkit 多行输入

自定义 Enter 键：光标在末尾 → 提交，在中间 → 换行。Option+Enter 强制提交。

### 5. 输出方式一致性

`print_formatted_text` 和 `sys.stdout.write` 在 `patch_stdout` 中混用会冲突。选一种。

### 6. Agentic Loop 回调链

引擎不操作 UI，用回调解耦。stats 对象要在 on_turn_start 就传给 UI。

### 7. LLM 连接重试（CRITICAL）

所有 LLM API 调用必须有重试逻辑。3 次重试 + 指数退避（2s/4s/6s）。5xx 自动重试，4xx 不重试。

### 8. 外部 Agent 降级

外部 Agent（Claude Code/Hermes/Codex）subprocess 调用可能超时或失败。
用 `_retry_run()` 统一重试，失败后自动降级到蒙多分身（LLM clone）。

### 9. 流式输出状态嵌入

流式输出期间嵌入实时状态（token/时间/turn）。`print_formatted_text` 和 `sys.stdout.write` 混用会冲突，选一种。

```python
sys.stdout.write(text)
sys.stdout.flush()
if chunk_count % 15 == 0:
    status = f"T{turn} · {tok}tok · {elapsed}"
    sys.stdout.write(f"  \033[2m[{status}]\033[0m")
    sys.stdout.flush()
```

### 10. tool_call 参数 JSON 修复（CRITICAL）

LLM 可能返回截断的 JSON（如 `{"path`）。三层防御：

**第1层：引擎修复** — 补全缺失的括号/引号
**第2层：过滤无效 tool_calls** — 无法修复的丢弃，不存入 messages
**第3层：API 发送前清洗** — `sanitize_messages()` 将损坏 arguments 替换为 `"{}"`

### 11. 工具参数验证

所有 tool handler 用 `args.get()` 而非 `args[]`，缺参返回清晰错误：
```python
path = args.get("path", "")
if not path:
    return "[错误: tool 缺少 path 参数]"
```

## 详细参考

参见 `references/mundo-agent-patterns.md` 和 `references/retry-and-fallback.md`。
