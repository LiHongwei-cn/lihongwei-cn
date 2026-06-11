"""MiMo Responses API 代理 v1.3
将 OpenAI responses API 转换为 MiMo chat/completions API
支持流式和非流式响应，处理 MiMo 的 reasoning_content 字段
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, AsyncGenerator

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse, StreamingResponse
    import uvicorn
    import httpx
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8765
MIMO_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"
MIMO_MODEL = "mimo-v2.5-pro"
DEFAULT_MAX_TOKENS = 4096


def get_api_key() -> str:
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if "XIAOMI_API_KEY" in line:
                    return line.strip().split("=", 1)[1]
    return os.environ.get("XIAOMI_API_KEY", "")


def convert_responses_to_chat(data: Dict[str, Any]) -> Dict[str, Any]:
    messages = []
    if "instructions" in data:
        messages.append({"role": "system", "content": data["instructions"]})

    input_content = data.get("input", "")
    if isinstance(input_content, str):
        messages.append({"role": "user", "content": input_content})
    elif isinstance(input_content, list):
        for item in input_content:
            if isinstance(item, dict):
                role = item.get("role", "user")
                content = item.get("content", "")
                if isinstance(content, list):
                    text_parts = [p.get("text", "") for p in content if p.get("type") == "text"]
                    content = "\n".join(text_parts)
                messages.append({"role": role, "content": content})
            elif isinstance(item, str):
                messages.append({"role": "user", "content": item})

    max_tokens = data.get("max_output_tokens", DEFAULT_MAX_TOKENS)
    if max_tokens < 200:
        max_tokens = 200

    return {
        "model": data.get("model", MIMO_MODEL),
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": data.get("temperature", 0.7),
        "stream": data.get("stream", False),
    }


def convert_chat_to_responses(chat_response: Dict[str, Any], request_id: str = None) -> Dict[str, Any]:
    if not request_id:
        request_id = f"resp_{int(time.time() * 1000)}"

    content = ""
    if "choices" in chat_response and chat_response["choices"]:
        choice = chat_response["choices"][0]
        if "message" in choice:
            content = choice["message"].get("content", "")
            if not content and "reasoning_content" in choice["message"]:
                content = choice["message"]["reasoning_content"]

    return {
        "id": request_id,
        "object": "response",
        "created_at": chat_response.get("created", 0),
        "status": "completed",
        "model": chat_response.get("model", MIMO_MODEL),
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": content}],
            }
        ],
        "usage": chat_response.get("usage", {}),
    }


async def stream_responses(request_id: str, chat_request: Dict[str, Any], api_key: str) -> AsyncGenerator[str, None]:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    yield f"data: {json.dumps({'type': 'response.created', 'response': {'id': request_id, 'status': 'in_progress'}})}\n\n"

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{MIMO_BASE_URL}/chat/completions",
                headers=headers,
                json=chat_request,
            ) as response:
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    chunk_str = line[6:]
                    if chunk_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(chunk_str)
                        if "choices" in chunk and chunk["choices"]:
                            choice = chunk["choices"][0]
                            if "delta" in choice:
                                delta_content = choice["delta"].get("content", "")
                                if not delta_content and "reasoning_content" in choice["delta"]:
                                    delta_content = choice["delta"]["reasoning_content"]
                                if delta_content:
                                    yield f"data: {json.dumps({'type': 'response.output_text.delta', 'response_id': request_id, 'output_index': 0, 'content_index': 0, 'delta': delta_content})}\n\n"
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    yield f"data: {json.dumps({'type': 'response.completed', 'response': {'id': request_id, 'status': 'completed'}})}\n\n"


if HAS_DEPS:
    app = FastAPI(title="MiMo Responses API Proxy")

    @app.post("/v1/responses")
    async def handle_responses(request: Request):
        try:
            data = await request.json()
            api_key = get_api_key()
            if not api_key:
                return JSONResponse(status_code=401, content={"error": "API key not found"})

            chat_request = convert_responses_to_chat(data)
            request_id = f"resp_{int(time.time() * 1000)}"

            if data.get("stream", False):
                return StreamingResponse(
                    stream_responses(request_id, chat_request, api_key),
                    media_type="text/event-stream",
                )
            else:
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                async with httpx.AsyncClient(timeout=120) as client:
                    response = await client.post(f"{MIMO_BASE_URL}/chat/completions", headers=headers, json=chat_request)
                    if response.status_code != 200:
                        return JSONResponse(status_code=response.status_code, content={"error": response.text})
                    chat_response = response.json()
                    return JSONResponse(content=convert_chat_to_responses(chat_response, request_id))
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

    @app.get("/v1/models")
    async def handle_models():
        api_key = get_api_key()
        if not api_key:
            return JSONResponse(status_code=401, content={"error": "API key not found"})
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MIMO_BASE_URL}/models", headers={"Authorization": f"Bearer {api_key}"})
            return JSONResponse(content=response.json())

    @app.get("/health")
    async def health():
        return {"status": "ok", "proxy": "mimo-responses-proxy"}


def start_proxy():
    if not HAS_DEPS:
        print("缺少依赖: pip install fastapi uvicorn httpx")
        return False
    print(f"启动 MiMo Responses API 代理: http://{PROXY_HOST}:{PROXY_PORT}")
    uvicorn.run(app, host=PROXY_HOST, port=PROXY_PORT, log_level="info")
    return True


if __name__ == "__main__":
    start_proxy()
