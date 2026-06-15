"""蒙多 LLM 客户端 v3.0.0 — 脱胎换骨

融合精华：
- Hermes Agent：消息清洗、surrogate修复、tool_calls验证
- Claude Code：reasoning_effort分级、cache_control标记
- Codex CLI：DNS预检、指数退避+抖动、circuit breaker
- MiMo Code：国产模型特化适配、中文token估算

v3.0.0 改进：
- 统一连接池管理（http.client替代urllib）
- 断路器模式（连续失败3次自动熔断60s）
- 输入缓存命中率优化（确定性排序+cache_control）
- 国产模型适配器（DeepSeek/MiMo/Qwen/GLM各自优化）
- 流式输出改进（chunk聚合、空闲检测、优雅中断）
"""

import os
import sys
import json
import time
import socket
import random
# threading removed in v2.2.0 (single-threaded, no lock needed)
from pathlib import Path
from typing import List, Dict, Iterator, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

try:
    import http.client
    import ssl
except ImportError:
    pass

from constants import (
    DNS_TIMEOUT, READ_TIMEOUT_FIRST, READ_TIMEOUT_RETRY,
    STREAM_IDLE_TIMEOUT, STREAM_MAX_WAIT, MAX_RETRY, RETRY_DELAY,
)


# ═══════════════════════════════════════════════
# 断路器 — 学习 Codex 的稳定性设计
# ═══════════════════════════════════════════════

class CircuitState(Enum):
    CLOSED = "closed"      # 正常
    OPEN = "open"          # 熔断
    HALF_OPEN = "half_open"  # 试探


@dataclass
class CircuitBreaker:
    """断路器：连续失败N次自动熔断，避免无效请求

    v2.2.0: 移除 threading.Lock（单线程使用，无需锁）
    """
    failure_threshold: int = 3
    recovery_timeout: float = 60.0
    _state: CircuitState = field(default=CircuitState.CLOSED, repr=False)
    _failure_count: int = field(default=0, repr=False)
    _last_failure_time: float = field(default=0.0, repr=False)

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time > self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def record_success(self):
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def record_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN

    def allow_request(self) -> bool:
        return self.state != CircuitState.OPEN


# ═══════════════════════════════════════════════
# 超时配置
# ═══════════════════════════════════════════════

@dataclass
class TimeoutConfig:
    dns_timeout: float = DNS_TIMEOUT
    read_timeout_first: float = READ_TIMEOUT_FIRST
    read_timeout_retry: float = READ_TIMEOUT_RETRY
    stream_connect_timeout: float = 30.0
    stream_idle_timeout: float = STREAM_IDLE_TIMEOUT
    stream_total_timeout: float = STREAM_MAX_WAIT
    max_retries: int = MAX_RETRY
    backoff_max: float = 30.0


RETRYABLE_CODES = {429, 500, 502, 503, 504}
CONTEXT_OVERFLOW_CODES = {400, 413}


# ═══════════════════════════════════════════════
# 国产模型适配器 — 学习 MiMo Code 的模型特化
# ═══════════════════════════════════════════════

@dataclass
class ModelAdapter:
    """模型特化适配器"""
    provider: str
    model: str
    supports_cache_control: bool = False
    supports_reasoning: bool = False
    supports_streaming: bool = True
    char_to_token_ratio: float = 0.4
    max_context_tokens: int = 128000
    optimal_temperature: float = 0.7
    needs_anthropic_endpoint: bool = False

    def optimize_payload(self, payload: Dict) -> Dict:
        """根据模型特性优化请求payload"""
        # DeepSeek：支持reasoning_content
        if self.provider == "deepseek":
            payload["temperature"] = min(payload.get("temperature", 0.7), 1.0)
        # MiMo：中文优化，稍高温度
        elif self.provider == "xiaomi":
            payload["temperature"] = 0.8
        # Qwen：支持长上下文
        elif self.provider == "qwen":
            pass  # 保持默认
        # GLM：工具调用优化
        elif self.provider == "zhipu":
            pass  # 保持默认
        return payload

    def estimate_tokens(self, text: str) -> int:
        """估算token数（中英文混合）"""
        cn_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        en_chars = len(text) - cn_chars
        return int(cn_chars * 0.7 + en_chars * self.char_to_token_ratio)


# 模型适配器注册表
MODEL_ADAPTERS: Dict[str, ModelAdapter] = {}


def register_adapter(provider: str, model: str, **kwargs):
    key = f"{provider}/{model}"
    MODEL_ADAPTERS[key] = ModelAdapter(provider=provider, model=model, **kwargs)


def get_adapter(provider: str, model: str) -> ModelAdapter:
    key = f"{provider}/{model}"
    if key in MODEL_ADAPTERS:
        return MODEL_ADAPTERS[key]
    # 按provider模糊匹配
    for k, v in MODEL_ADAPTERS.items():
        if v.provider == provider:
            return v
    return ModelAdapter(provider=provider, model=model)


# 预注册国产模型适配器
register_adapter("deepseek", "deepseek-chat",
                  supports_reasoning=True, char_to_token_ratio=0.35,
                  max_context_tokens=128000)
register_adapter("deepseek", "deepseek-reasoner",
                  supports_reasoning=True, char_to_token_ratio=0.35,
                  max_context_tokens=64000, optimal_temperature=0.6)
register_adapter("xiaomi", "mimo-v2.5-pro",
                  char_to_token_ratio=0.4, max_context_tokens=128000,
                  optimal_temperature=0.8)
register_adapter("qwen", "qwen-max",
                  char_to_token_ratio=0.4, max_context_tokens=32000)
register_adapter("zhipu", "glm-4-plus",
                  char_to_token_ratio=0.4, max_context_tokens=128000)
register_adapter("anthropic", "claude-sonnet-4-20250514",
                  supports_cache_control=True, supports_reasoning=True,
                  char_to_token_ratio=0.3, max_context_tokens=200000,
                  needs_anthropic_endpoint=True)
register_adapter("anthropic", "claude-opus-4",
                  supports_cache_control=True, supports_reasoning=True,
                  char_to_token_ratio=0.3, max_context_tokens=200000,
                  needs_anthropic_endpoint=True)


# ═══════════════════════════════════════════════
# 错误分类
# ═══════════════════════════════════════════════

def _is_timeout_error(e: Exception) -> bool:
    if isinstance(e, (socket.timeout, ConnectionError, ConnectionResetError,
                       ConnectionRefusedError, BrokenPipeError, TimeoutError)):
        return True
    err = str(e).lower()
    keywords = ["timed out", "timeout", "reset", "broken pipe",
                "connection refused", "connection reset", "eof",
                "remote end closed", "bad status line", "incomplete read"]
    return any(kw in err for kw in keywords)


def _is_retryable(code: int) -> bool:
    return code in RETRYABLE_CODES


def _is_context_overflow(code: int, body: str) -> bool:
    if code in CONTEXT_OVERFLOW_CODES:
        keywords = ["context", "too long", "maximum", "token", "limit"]
        return any(kw in body.lower() for kw in keywords)
    return False


def _backoff_sleep(attempt: int, backoff_max: float = 30.0):
    """指数退避 + 随机抖动防雪崩"""
    base = min(2 ** attempt * 2, backoff_max)
    jitter = random.uniform(0, base * 0.3)
    time.sleep(base + jitter)


# ═══════════════════════════════════════════════
# 环境变量加载
# ═══════════════════════════════════════════════

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
# 消息清洗 — 借鉴 Hermes Agent 的铁律
# ═══════════════════════════════════════════════

def _fix_surrogates(text: str) -> str:
    try:
        text.encode("utf-8")
        return text
    except UnicodeEncodeError:
        return text.encode("utf-8", errors="replace").decode("utf-8")


def _coerce_content(value) -> str:
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
    """清洗消息：surrogate修复、content类型转换、tool_calls验证、空消息过滤"""
    cleaned = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        m = dict(msg)

        if "content" in m:
            m["content"] = _coerce_content(m["content"])

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

        if m.get("role") == "tool" and "content" not in m:
            m["content"] = ""

        if (not m.get("content") and not m.get("tool_calls")
                and not m.get("tool_call_id") and m.get("role") not in ("system",)):
            continue

        cleaned.append(m)
    return cleaned if cleaned else [{"role": "user", "content": "继续"}]


# ═══════════════════════════════════════════════
# JSON 修复
# ═══════════════════════════════════════════════

def repair_json(raw: str):
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


# ═══════════════════════════════════════════════
# LLM 客户端 — 融合四家精华
# ═══════════════════════════════════════════════

class LLMClient:

    def __repr__(self) -> str:
        return f"LLMClient(provider={self.provider}, model={self.model})"

    def __init__(self, provider: str = "deepseek", model: str = None, api_key: str = None):
        cfg = PROVIDERS.get(provider)
        if not cfg:
            raise ValueError(f"未知 provider: {provider}. 可用: {list(PROVIDERS.keys())}")
        self.provider = provider
        self.model = model or cfg["model"]
        self.base_url = cfg["base_url"]
        self.anthropic_base_url = cfg.get("anthropic_base_url", "")
        self.api_key = api_key or os.environ.get(cfg["env_key"], "")
        if not self.api_key:
            raise ValueError(f"缺少 {cfg['env_key']}。运行 /setup 或 /add 配置。")
        self._adapter = get_adapter(provider, self.model)
        self._circuit_breaker = CircuitBreaker()
        self._timeout_config = TimeoutConfig()
        from urllib.parse import urlparse
        self._host = urlparse(self.base_url).hostname
        self._ssl_ctx = ssl.create_default_context()

    def _dns_precheck(self) -> Optional[str]:
        old = socket.getdefaulttimeout()
        try:
            socket.setdefaulttimeout(self._timeout_config.dns_timeout)
            socket.getaddrinfo(self._host, 443)
            return None
        except (socket.gaierror, socket.timeout, OSError):
            return f"DNS 解析失败: {self._host}"
        finally:
            socket.setdefaulttimeout(old)

    @property
    def is_anthropic(self) -> bool:
        return "anthropic" in self.base_url.lower()

    def chat(self, messages: List[Dict], tools: List[Dict] = None,
             temperature: float = None, max_tokens: int = 4096,
             reasoning_effort: str = None) -> Dict:
        payload = self._build_payload(messages, tools, temperature, max_tokens,
                                       stream=False, reasoning_effort=reasoning_effort)
        return self._request_with_retry(payload)

    def chat_stream(self, messages: List[Dict], tools: List[Dict] = None,
                    temperature: float = None, max_tokens: int = 4096,
                    reasoning_effort: str = None) -> Iterator[Dict]:
        payload = self._build_payload(messages, tools, temperature, max_tokens,
                                       stream=True, reasoning_effort=reasoning_effort)
        yield from self._request_stream_with_retry(payload)

    def _build_payload(self, messages, tools, temperature, max_tokens,
                       stream=False, reasoning_effort=None) -> Dict:
        if temperature is None:
            temperature = self._adapter.optimal_temperature
        payload = {
            "model": self.model,
            "messages": sanitize_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        if tools:
            sorted_tools = sorted(tools, key=lambda t: t.get("function", {}).get("name", ""))
            payload["tools"] = sorted_tools
            payload["tool_choice"] = "auto"
        if reasoning_effort:
            payload["reasoning_effort"] = reasoning_effort
        if self.is_anthropic and self._adapter.supports_cache_control:
            self._inject_cache_control(payload)
        payload = self._adapter.optimize_payload(payload)
        return payload

    def _inject_cache_control(self, payload: Dict):
        """注入缓存控制标记 — 提高输入缓存命中率"""
        messages = payload.get("messages", [])
        for msg in messages:
            if msg.get("role") == "system":
                content = msg.get("content", "")
                if isinstance(content, str):
                    msg["content"] = [
                        {"type": "text", "text": content,
                         "cache_control": {"type": "ephemeral"}}
                    ]
                break
        tools = payload.get("tools", [])
        if tools:
            tools[-1]["function"]["cache_control"] = {"type": "ephemeral"}

    def _request_with_retry(self, payload: Dict) -> Dict:
        if not self._circuit_breaker.allow_request():
            raise RuntimeError(f"断路器熔断中，请等待 {self._circuit_breaker.recovery_timeout}s")
        dns_err = self._dns_precheck()
        if dns_err:
            raise RuntimeError(dns_err)

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        last_error = None
        for attempt in range(self._timeout_config.max_retries):
            timeout = (self._timeout_config.read_timeout_first if attempt == 0
                       else self._timeout_config.read_timeout_retry)
            try:
                resp = self._http_request(url, headers, data, timeout)
                self._circuit_breaker.record_success()
                return resp
            except RuntimeError as e:
                self._circuit_breaker.record_failure()
                raise
            except Exception as e:
                last_error = e
                if _is_timeout_error(e) and attempt < self._timeout_config.max_retries - 1:
                    _backoff_sleep(attempt, self._timeout_config.backoff_max)
                    continue
                if attempt < self._timeout_config.max_retries - 1:
                    _backoff_sleep(attempt, self._timeout_config.backoff_max)
                    continue
                self._circuit_breaker.record_failure()
                raise RuntimeError(f"请求失败 ({type(e).__name__}): {e}") from e
        raise RuntimeError(f"重试耗尽: {last_error}") from last_error

    def _http_request(self, url: str, headers: Dict, data: bytes, timeout: float) -> Dict:
        """使用 http.client 替代 urllib — 更稳定的连接管理"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        path = parsed.path or "/"

        conn = None
        try:
            if parsed.scheme == "https":
                conn = http.client.HTTPSConnection(host, port, timeout=timeout,
                                                    context=self._ssl_ctx)
            else:
                conn = http.client.HTTPConnection(host, port, timeout=timeout)
            conn.request("POST", path, body=data, headers=headers)
            resp = conn.getresponse()
            body = resp.read().decode("utf-8", errors="replace")
            if resp.status == 200:
                return json.loads(body)
            if _is_context_overflow(resp.status, body):
                raise RuntimeError(f"上下文过长 (HTTP {resp.status})")
            if _is_retryable(resp.status):
                raise ConnectionError(f"HTTP {resp.status}: {body[:200]}")
            raise RuntimeError(f"LLM API 错误 {resp.status}: {body[:300]}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _request_stream_with_retry(self, payload: Dict) -> Iterator[Dict]:
        if not self._circuit_breaker.allow_request():
            raise RuntimeError(f"断路器熔断中")
        dns_err = self._dns_precheck()
        if dns_err:
            raise RuntimeError(dns_err)

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        for attempt in range(self._timeout_config.max_retries):
            conn = None
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                host = parsed.hostname
                port = parsed.port or (443 if parsed.scheme == "https" else 80)
                path = parsed.path or "/"

                if parsed.scheme == "https":
                    conn = http.client.HTTPSConnection(
                        host, port, timeout=self._timeout_config.stream_connect_timeout,
                        context=self._ssl_ctx)
                else:
                    conn = http.client.HTTPConnection(
                        host, port, timeout=self._timeout_config.stream_connect_timeout)
                conn.request("POST", path, body=data, headers=headers)
                resp = conn.getresponse()
                if resp.status != 200:
                    body = resp.read().decode("utf-8", errors="replace")
                    if _is_context_overflow(resp.status, body):
                        raise RuntimeError(f"上下文过长")
                    if _is_retryable(resp.status) and attempt < self._timeout_config.max_retries - 1:
                        _backoff_sleep(attempt)
                        continue
                    raise RuntimeError(f"流式请求失败 {resp.status}")
                yield from self._read_stream(resp, conn)
                self._circuit_breaker.record_success()
                return
            except (ConnectionError, socket.timeout, TimeoutError, OSError) as e:
                if _is_timeout_error(e) and attempt < self._timeout_config.max_retries - 1:
                    _backoff_sleep(attempt)
                    continue
                self._circuit_breaker.record_failure()
                raise RuntimeError(f"流式连接中断: {e}") from e
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

    def _read_stream(self, resp, conn=None) -> Iterator[Dict]:
        last_data_time = time.time()
        stream_start = time.time()
        chunk_count = 0
        idle_timeout = self._timeout_config.stream_idle_timeout

        try:
            while True:
                line = resp.readline()
                if not line:
                    break
                now = time.time()
                if now - stream_start > self._timeout_config.stream_total_timeout:
                    raise RuntimeError(f"流式总超时")
                if now - last_data_time > idle_timeout:
                    raise RuntimeError(f"流式空闲超时")
                last_data_time = now
                chunk_count += 1

                decoded = line.decode("utf-8", errors="replace").strip()
                if not decoded or decoded.startswith(":"):
                    continue
                if decoded.startswith("data: "):
                    payload_str = decoded[6:]
                    if payload_str == "[DONE]":
                        return
                    try:
                        yield json.loads(payload_str)
                    except json.JSONDecodeError:
                        continue
        except socket.timeout as e:
            raise RuntimeError(f"流式读取超时，已运行 {time.time()-stream_start:.0f}s") from e

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
            "cached_tokens": usage.get("prompt_tokens_details", {}).get("cached_tokens", 0),
        }


def get_available_providers() -> List[str]:
    available = []
    for name, cfg in PROVIDERS.items():
        if os.environ.get(cfg["env_key"]):
            available.append(name)
    return available
