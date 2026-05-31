"""Mundo Agent Web API — 流式对话 + 工具执行 + Token 统计"""

import json
import os
import time
import uuid
from collections import defaultdict

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Mundo Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------- 配置 ---------------

API_BASE = os.getenv("MUNDO_API_BASE", "https://api.deepseek.com")
API_KEY = os.getenv("MUNDO_API_KEY", os.getenv("DEEPSEEK_API_KEY", ""))
MODEL = os.getenv("MUNDO_MODEL", "deepseek-chat")

SYSTEM_PROMPT = """你是蒙多（Mundo）——AI 时代第一个皇帝。自主学习，无限成长。
你可以执行代码、搜索网络、管理文件。用中文回复。
收到任务后直接执行，不废话。"""

# --------------- 会话存储 ---------------

sessions: dict[str, list[dict]] = defaultdict(list)
token_stats: dict[str, dict] = defaultdict(lambda: {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
    "requests": 0,
})

# --------------- 工具定义 ---------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_code",
            "description": "执行 Python 代码并返回输出",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "要执行的 Python 代码"},
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索网络获取信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取文件内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "写入文件内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "文件内容"},
                },
                "required": ["path", "content"],
            },
        },
    },
]


def execute_tool(name: str, args: dict) -> str:
    """执行工具调用"""
    if name == "run_code":
        import subprocess
        try:
            result = subprocess.run(
                ["python3", "-c", args["code"]],
                capture_output=True, text=True, timeout=30,
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            return output or "(无输出)"
        except subprocess.TimeoutExpired:
            return "[错误] 代码执行超时（30秒）"
        except Exception as e:
            return f"[错误] {e}"

    if name == "web_search":
        return f"[搜索] {args['query']} — (功能开发中，请用 run_code + requests 实现)"

    if name == "read_file":
        try:
            with open(args["path"], "r", encoding="utf-8") as f:
                return f.read()[:10000]
        except Exception as e:
            return f"[错误] {e}"

    if name == "write_file":
        try:
            os.makedirs(os.path.dirname(args["path"]) or ".", exist_ok=True)
            with open(args["path"], "w", encoding="utf-8") as f:
                f.write(args["content"])
            return f"[成功] 已写入 {args['path']}"
        except Exception as e:
            return f"[错误] {e}"

    return f"[错误] 未知工具: {name}"


# --------------- SSE 流式生成 ---------------

async def stream_chat(session_id: str, user_message: str):
    """流式对话，逐 token 推送 + 工具调用事件"""
    history = sessions[session_id]
    history.append({"role": "user", "content": user_message})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-20:]
    stats = token_stats[session_id]
    stats["requests"] += 1

    max_rounds = 5  # 工具调用最多 5 轮

    for round_idx in range(max_rounds):
        accumulated_content = ""
        tool_calls_acc: dict[int, dict] = {}
        finish_reason = None

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{API_BASE}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "messages": messages,
                    "tools": TOOLS,
                    "stream": True,
                    "max_tokens": 4096,
                },
            ) as resp:
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:]
                    if payload.strip() == "[DONE]":
                        break

                    try:
                        chunk = json.loads(payload)
                    except json.JSONDecodeError:
                        continue

                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    finish_reason = chunk["choices"][0].get("finish_reason")

                    # 处理 token 统计（部分 API 在最后一个 chunk 返回 usage）
                    usage = chunk.get("usage")
                    if usage:
                        stats["prompt_tokens"] += usage.get("prompt_tokens", 0)
                        stats["completion_tokens"] += usage.get("completion_tokens", 0)
                        stats["total_tokens"] += usage.get("total_tokens", 0)

                    # 流式文本内容
                    content = delta.get("content")
                    if content:
                        accumulated_content += content
                        yield f"data: {json.dumps({'type': 'token', 'content': content, 'stats': dict(stats)}, ensure_ascii=False)}\n\n"

                    # 工具调用 delta
                    for tc_delta in delta.get("tool_calls", []):
                        idx = tc_delta["index"]
                        if idx not in tool_calls_acc:
                            tool_calls_acc[idx] = {
                                "id": tc_delta.get("id", ""),
                                "name": "",
                                "arguments": "",
                            }
                        if tc_delta.get("id"):
                            tool_calls_acc[idx]["id"] = tc_delta["id"]
                        fn = tc_delta.get("function", {})
                        if fn.get("name"):
                            tool_calls_acc[idx]["name"] = fn["name"]
                        if fn.get("arguments"):
                            tool_calls_acc[idx]["arguments"] += fn["arguments"]

        # 保存 assistant 消息
        if accumulated_content and not tool_calls_acc:
            history.append({"role": "assistant", "content": accumulated_content})
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'done', 'stats': dict(stats)}, ensure_ascii=False)}\n\n"
            return

        # 有工具调用
        if tool_calls_acc:
            assistant_msg: dict = {"role": "assistant", "content": accumulated_content or None, "tool_calls": []}
            for idx in sorted(tool_calls_acc.keys()):
                tc = tool_calls_acc[idx]
                assistant_msg["tool_calls"].append({
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": tc["arguments"]},
                })
            history.append(assistant_msg)

            # 逐个执行工具
            for idx in sorted(tool_calls_acc.keys()):
                tc = tool_calls_acc[idx]
                tool_name = tc["name"]
                try:
                    tool_args = json.loads(tc["arguments"])
                except json.JSONDecodeError:
                    tool_args = {}

                # 通知前端：工具开始
                yield f"data: {json.dumps({'type': 'tool_start', 'name': tool_name, 'args': tool_args}, ensure_ascii=False)}\n\n"

                result = execute_tool(tool_name, tool_args)

                # 通知前端：工具结果
                yield f"data: {json.dumps({'type': 'tool_result', 'name': tool_name, 'result': result}, ensure_ascii=False)}\n\n"

                history.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })

            # 继续下一轮
            continue

        # 无工具调用也无内容
        yield f"data: {json.dumps({'type': 'done', 'stats': dict(stats)}, ensure_ascii=False)}\n\n"
        return

    # 超过最大轮数
    yield f"data: {json.dumps({'type': 'done', 'stats': dict(stats)}, ensure_ascii=False)}\n\n"


# --------------- 路由 ---------------

@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    message = body.get("message", "").strip()
    session_id = body.get("session_id") or str(uuid.uuid4())

    if not message:
        return {"error": "消息不能为空"}

    if not API_KEY:
        return {"error": "未配置 API Key，请设置 MUNDO_API_KEY 或 DEEPSEEK_API_KEY 环境变量"}

    return StreamingResponse(
        stream_chat(session_id, message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Session-Id": session_id},
    )


@app.get("/api/stats/{session_id}")
async def get_stats(session_id: str):
    return dict(token_stats[session_id])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
