"""蒙多 LLM 客户端 v26 — 多 provider + 流式 + 重试 + 消息清洗

改进（vs v25）：
- 消息清洗更健壮（借鉴 Hermes message_sanitization）
- 流式读取用 readline（SSE 铁律）
- 重试逻辑统一，指数退避
- 支持 reasoning_content 字段（DeepSeek R1 等）
"""

import os
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Iterator, Optional

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
                f"缺少 {cfg['env_key']}。运行 /setup 或 /add 配置。"
            )

    def chat(self, messages: List[Dict], tools: List[Dict] = None,
             temperature: float = 0.7, max_tokens: int = 4096) -> Dict:
        payload = self._build_payload(messages, tools, temperature, max_tokens, stream=False)
        return self._request_with_retry(payload)

    def chat_stream(self, messages: List[Dict], tools: List[Dict] = None,
                    temperature: float = 0.7, max_tokens: int = 4096) -> Iterator[Dict]:
        payload = self._build_payload(messages, tools, temperature, max_tokens, stream=True)
        yield from self._request_stream(payload)

    def _build_payload(self, messages, tools, temperature, max_tokens, stream=False):
        payload = {
            "model": self.model,
            "messages": sanitize_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        return payload

    def _request_with_retry(self, payload: Dict, max_retries: int = 3) -> Dict:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        last_error = None
        for attempt in range(max_retries):
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                if e.code >= 500 and attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise RuntimeError(f"LLM API 错误 {e.code}: {err_body[:300]}") from e
            except urllib.error.URLError as e:
                last_error = e.reason
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise RuntimeError(f"网络错误: {last_error}") from e
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise RuntimeError(f"请求异常: {last_error}") from e

    def _request_stream(self, payload: Dict) -> Iterator[Dict]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
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
        # DeepSeek R1 等 reasoning 模型
        if delta.get("reasoning_content"):
            result["reasoning"] = delta["reasoning_content"]
        return result

    @staticmethod
    def extract_response(result: Dict) -> Dict:
        choice = result.get("choices", [{}])[0]
        message = choice.get("message", {})
        resp = {
            "role": "assistant",
            "content": message.get("content") or "",
            "tool_calls": message.get("tool_calls", []),
        }
        if message.get("reasoning_content"):
            resp["reasoning"] = message["reasoning_content"]
        return resp

    @staticmethod
    def extract_usage(result: Dict) -> Dict:
        usage = result.get("usage", {})
        return {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }


# ═══════════════════════════════════════════════
# 消息清洗 — 借鉴 Hermes message_sanitization
# ═══════════════════════════════════════════════

def sanitize_messages(messages: List[Dict]) -> List[Dict]:
    """清洗消息：确保 content 为字符串，修复损坏的 tool_calls，移除空消息"""
    cleaned = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        m = dict(msg)
        # content 必须是字符串（None → ""）
        if "content" in m:
            if m["content"] is None:
                m["content"] = ""
            elif not isinstance(m["content"], str):
                m["content"] = str(m["content"])
        # 清洗 tool_calls 中的 arguments
        if "tool_calls" in m and m["tool_calls"]:
            valid_tcs = []
            for tc in m["tool_calls"]:
                func = tc.get("function", {})
                raw_args = func.get("arguments", "{}")
                try:
                    json.loads(raw_args)
                    valid_tcs.append(tc)
                except (json.JSONDecodeError, TypeError):
                    func["arguments"] = "{}"
                    valid_tcs.append(tc)
            m["tool_calls"] = valid_tcs
        # 移除完全空的消息
        if not m.get("content") and not m.get("tool_calls") and not m.get("tool_call_id"):
            continue
        cleaned.append(m)
    return cleaned if cleaned else [{"role": "user", "content": "继续"}]


def repair_json(raw: str):
    """尝试修复截断的 JSON 字符串"""
    if not raw or not raw.strip():
        return {}
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    open_braces = raw.count("{") - raw.count("}")
    open_brackets = raw.count("[") - raw.count("]")
    quote_count = raw.count('"') - raw.count('\\"')
    if quote_count % 2 != 0:
        raw += '"'
    raw += "]" * max(0, open_brackets)
    raw += "}" * max(0, open_braces)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def get_available_providers() -> List[str]:
    available = []
    for name, cfg in PROVIDERS.items():
        if os.environ.get(cfg["env_key"]):
            available.append(name)
    return available
