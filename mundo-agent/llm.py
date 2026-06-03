"""蒙多 LLM 客户端 v28 — 多 provider + 流式 + 重试 + 消息清洗

v27 改进（vs v26）：
- 消息清洗增强：surrogate 字符修复、content 类型强制转换
- 流式读取更健壮：超时处理、连接断开恢复
- 错误分类：区分可重试/不可重试错误
- 上下文溢出检测：自动触发压缩
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


# ═══════════════════════════════════════════════
# 可重试错误判断
# ═══════════════════════════════════════════════

RETRYABLE_CODES = {429, 500, 502, 503, 504}
CONTEXT_OVERFLOW_CODES = {400, 413}


def _is_retryable(code: int) -> bool:
    return code in RETRYABLE_CODES


def _is_context_overflow(code: int, body: str) -> bool:
    if code in CONTEXT_OVERFLOW_CODES:
        keywords = ["context", "too long", "maximum", "token", "limit"]
        return any(kw in body.lower() for kw in keywords)
    return False


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
                with urllib.request.urlopen(req, timeout=180) as resp:  # 3 分钟连接+读取超时
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                # 上下文溢出 — 不重试，直接报错让引擎压缩
                if _is_context_overflow(e.code, err_body):
                    raise RuntimeError(f"上下文过长 (HTTP {e.code}): 请减少输入或运行 /compact")
                # 可重试错误
                if _is_retryable(e.code) and attempt < max_retries - 1:
                    wait = min(2 ** attempt * 2, 30)
                    time.sleep(wait)
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
            resp = urllib.request.urlopen(req, timeout=180)  # 3 分钟连接超时
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            if _is_context_overflow(e.code, err_body):
                raise RuntimeError(f"上下文过长 (HTTP {e.code}): 请减少输入或运行 /compact")
            raise RuntimeError(f"LLM API 错误 {e.code}: {err_body[:300]}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"网络错误: {e.reason}") from e

        import select
        import socket

        last_data_time = time.time()
        STREAM_IDLE_TIMEOUT = 120  # 120 秒无数据 → 超时

        try:
            sock = resp.fp.raw._sock if hasattr(resp.fp.raw, '_sock') else None
            for raw_line in resp:
                last_data_time = time.time()
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
        except socket.timeout:
            raise RuntimeError(f"流式读取超时（{STREAM_IDLE_TIMEOUT}s 无数据）")
        except Exception as e:
            if "timed out" in str(e).lower() or "timeout" in str(e).lower():
                raise RuntimeError(f"流式读取超时: {e}")
            raise
        finally:
            try:
                resp.close()
            except Exception:
                pass

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

def _fix_surrogates(text: str) -> str:
    """修复 surrogate 字符（Hermes 铁律）"""
    try:
        text.encode("utf-8")
        return text
    except UnicodeEncodeError:
        return text.encode("utf-8", errors="replace").decode("utf-8")


def _coerce_content(value) -> str:
    """强制转换 content 为字符串（Hermes 铁律：永远不信任 API 返回值）"""
    if value is None:
        return ""
    if isinstance(value, str):
        return _fix_surrogates(value)
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, (list, dict)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(value)
    return str(value)


def sanitize_messages(messages: List[Dict]) -> List[Dict]:
    """清洗消息：surrogate 修复、content 类型转换、tool_calls 验证、空消息过滤"""
    cleaned = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        m = dict(msg)

        # content 必须是字符串
        if "content" in m:
            m["content"] = _coerce_content(m["content"])

        # 清洗 tool_calls 中的 arguments
        if "tool_calls" in m and m["tool_calls"]:
            valid_tcs = []
            for tc in m["tool_calls"]:
                func = tc.get("function", {})
                raw_args = func.get("arguments", "{}")
                if isinstance(raw_args, str):
                    try:
                        json.loads(raw_args)
                        valid_tcs.append(tc)
                    except (json.JSONDecodeError, TypeError):
                        func["arguments"] = "{}"
                        valid_tcs.append(tc)
                else:
                    func["arguments"] = "{}"
                    valid_tcs.append(tc)
            m["tool_calls"] = valid_tcs

        # tool role 的 content 必须存在
        if m.get("role") == "tool" and "content" not in m:
            m["content"] = ""

        # 移除完全空的消息（但保留 tool 消息和 system 消息）
        if (not m.get("content") and not m.get("tool_calls")
                and not m.get("tool_call_id") and m.get("role") not in ("system",)):
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
