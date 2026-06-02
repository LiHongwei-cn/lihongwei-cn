"""蒙多的 LLM 多模型客户端 — 全量 AI 模型支持 + 流式输出"""

import os
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Iterator, Callable, Optional

ENV_PATH = Path.home() / ".hermes" / ".env"
MUNDO_ENV = Path.home() / ".hermes" / "mundo-agent" / ".env"


def _load_env():
    for path in [MUNDO_ENV, ENV_PATH]:
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()

from setup import PROVIDERS


class LLMClient:

    def __init__(self, provider: str = "xiaomi", model: str = None, api_key: str = None):
        cfg = PROVIDERS.get(provider)
        if not cfg:
            raise ValueError(f"未知 provider: {provider}")

        self.provider = provider
        self.model = model or cfg["model"]
        self.base_url = cfg["base_url"]
        self.api_key = api_key or os.environ.get(cfg["env_key"], "")

        if not self.api_key:
            raise ValueError(
                f"缺少 {cfg['env_key']}。运行 /setup 或 /add 配置，或在 ~/.hermes/mundo-agent/.env 中设置。"
            )

    def chat(self, messages: List[Dict], tools: List[Dict] = None,
             temperature: float = 0.7, max_tokens: int = 4096) -> Dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        return self._request(payload)

    def chat_stream(self, messages: List[Dict], tools: List[Dict] = None,
                    temperature: float = 0.7, max_tokens: int = 4096) -> Iterator[Dict]:
        """流式输出 — 逐 chunk yield，支持实时显示"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        yield from self._request_stream(payload)

    def _request(self, payload: Dict) -> Dict:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = json.dumps(payload).encode("utf-8")

        last_error = None
        for attempt in range(3):
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                if e.code >= 500 and attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise RuntimeError(f"LLM API 错误 {e.code}: {err_body[:300]}") from e
            except urllib.error.URLError as e:
                last_error = e.reason
                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise RuntimeError(f"网络错误: {last_error}") from e
            except Exception as e:
                last_error = str(e)
                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise RuntimeError(f"请求异常: {last_error}") from e

    def _request_stream(self, payload: Dict) -> Iterator[Dict]:
        """SSE 流式请求 — readline 方式，更稳定"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            resp = urllib.request.urlopen(req, timeout=120)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM API 错误 {e.code}: {err_body[:300]}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"网络错误: {e.reason}") from e

        try:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line or line.startswith(":"):
                    continue
                if line.startswith("data: "):
                    payload_str = line[6:]
                    if payload_str == "[DONE]":
                        return
                    try:
                        yield json.loads(payload_str)
                    except json.JSONDecodeError:
                        continue
        finally:
            resp.close()

    @staticmethod
    def extract_stream_delta(chunk: Dict) -> Dict:
        choice = chunk.get("choices") or [{}]
        first = choice[0] if choice else {}
        delta = first.get("delta") or {}
        result = {
            "content": delta.get("content") or "",
            "tool_calls": delta.get("tool_calls") or [],
            "finish_reason": first.get("finish_reason"),
        }
        if "usage" in chunk:
            result["usage"] = chunk["usage"]
        return result

    @staticmethod
    def extract_response(result: Dict) -> Dict:
        choice = result.get("choices", [{}])[0]
        message = choice.get("message", {})
        return {
            "role": "assistant",
            "content": message.get("content", ""),
            "tool_calls": message.get("tool_calls", []),
        }

    @staticmethod
    def extract_usage(result: Dict) -> Dict:
        usage = result.get("usage", {})
        return {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }


def get_available_providers() -> List[str]:
    available = []
    for name, cfg in PROVIDERS.items():
        if os.environ.get(cfg["env_key"]):
            available.append(name)
    return available
