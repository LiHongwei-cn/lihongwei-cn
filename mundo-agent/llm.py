"""蒙多 LLM 客户端 v1.2.7 — 多 provider + 流式 + 重试 + 消息清洗 + 超时增强

v1.2.7 改进：
- 流式请求支持重试（流式无重试，卡死就死）★核心修复
- 空闲超时 120s → 45s，更快检测卡死
- DNS 预检：连接前 8s 内探测端点可达性，不可达直接报错
- 渐进超时：首次 90s，重试 180s（模型可能慢）
- 随机退避抖动防雪崩
- 更精确的超时错误分类和用户提示
"""

import os
import json
import time
import socket
import random
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Iterator, Optional


# ═══════════════════════════════════════════════
# 超时配置（集中管理，一处改全局生效）
# ═══════════════════════════════════════════════

class TimeoutConfig:
    DNS_TIMEOUT = 8               # DNS 解析超时
    READ_TIMEOUT_FIRST = 90       # 首次请求读取超时
    READ_TIMEOUT_RETRY = 180      # 重试请求读取超时（模型可能慢）
    STREAM_CONNECT_TIMEOUT = 30   # 流式连接超时
    STREAM_IDLE_TIMEOUT = 45      # 流式空闲超时（45s 无数据 → 卡死）
    STREAM_TOTAL_TIMEOUT = 300    # 流式总超时（5 分钟）
    MAX_RETRIES = 3               # 最大重试
    BACKOFF_MAX = 30              # 最大退避秒数


RETRYABLE_CODES = {429, 500, 502, 503, 504}
CONTEXT_OVERFLOW_CODES = {400, 413}


def _is_retryable(code: int) -> bool:
    return code in RETRYABLE_CODES


def _is_context_overflow(code: int, body: str) -> bool:
    if code in CONTEXT_OVERFLOW_CODES:
        keywords = ["context", "too long", "maximum", "token", "limit"]
        return any(kw in body.lower() for kw in keywords)
    return False


def _is_timeout_error(e: Exception) -> bool:
    """判断是否为超时/连接类错误（应重试）"""
    if isinstance(e, (socket.timeout, ConnectionError, ConnectionResetError,
                       ConnectionRefusedError, BrokenPipeError, TimeoutError)):
        return True
    err = str(e).lower()
    keywords = ["timed out", "timeout", "reset", "broken pipe",
                "connection refused", "connection reset", "eof",
                "remote end closed", "bad status line", "incomplete read"]
    if any(kw in err for kw in keywords):
        return True
    if isinstance(e, urllib.error.URLError):
        reason = str(getattr(e, 'reason', '')).lower()
        return any(kw in reason for kw in ["timed out", "timeout", "refused", "reset", "eof"])
    return False


def _backoff_sleep(attempt: int):
    """指数退避 + 随机抖动防雪崩"""
    base = min(2 ** attempt * 2, TimeoutConfig.BACKOFF_MAX)
    jitter = random.uniform(0, base * 0.3)
    time.sleep(base + jitter)


def _dns_precheck(host: str) -> bool:
    """DNS 预检：8s 内探测域名可达性"""
    old = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(TimeoutConfig.DNS_TIMEOUT)
        socket.getaddrinfo(host, 443)
        return True
    except (socket.gaierror, socket.timeout, OSError):
        return False
    finally:
        socket.setdefaulttimeout(old)

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

    def __repr__(self) -> str:
        return f"LLMClient(provider={self.provider}, model={self.model})"

    def __init__(self, provider: str = "xiaomi", model: str = None, api_key: str = None):
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
        # 提取 host 用于 DNS 预检
        from urllib.parse import urlparse
        self._host = urlparse(self.base_url).hostname

    def _check_connectivity(self) -> Optional[str]:
        """快速检查端点可达性，返回错误信息或 None"""
        if not _dns_precheck(self._host):
            return f"DNS 解析失败: {self._host}（请检查网络连接）"
        return None

    def chat(self, messages: List[Dict], tools: List[Dict] = None,
             temperature: float = 0.7, max_tokens: int = 4096) -> Dict:
        payload = self._build_payload(messages, tools, temperature, max_tokens, stream=False)
        return self._request_with_retry(payload)

    def chat_stream(self, messages: List[Dict], tools: List[Dict] = None,
                    temperature: float = 0.7, max_tokens: int = 4096) -> Iterator[Dict]:
        payload = self._build_payload(messages, tools, temperature, max_tokens, stream=True)
        yield from self._request_stream_with_retry(payload)

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

    def _request_with_retry(self, payload: Dict, max_retries: int = None) -> Dict:
        max_retries = max_retries or TimeoutConfig.MAX_RETRIES
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        # DNS 预检：8s 内确认端点可达，不可达直接报错不等 3 分钟
        conn_err = self._check_connectivity()
        if conn_err:
            raise RuntimeError(conn_err)

        last_error = None
        for attempt in range(max_retries):
            # 渐进超时：首次 90s，重试 180s（模型可能慢）
            timeout = TimeoutConfig.READ_TIMEOUT_FIRST if attempt == 0 else TimeoutConfig.READ_TIMEOUT_RETRY
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                if _is_context_overflow(e.code, err_body):
                    raise RuntimeError(f"上下文过长 (HTTP {e.code}): 请减少输入或运行 /compact")
                if _is_retryable(e.code) and attempt < max_retries - 1:
                    _backoff_sleep(attempt)
                    continue
                raise RuntimeError(f"LLM API 错误 {e.code}: {err_body[:300]}") from e
            except (urllib.error.URLError, socket.timeout, TimeoutError,
                    ConnectionError, ConnectionResetError, BrokenPipeError, OSError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    _backoff_sleep(attempt)
                    continue
                raise RuntimeError(f"网络错误 ({type(e).__name__}): {getattr(e, 'reason', e)}") from e
            except Exception as e:
                last_error = e
                if _is_timeout_error(e) and attempt < max_retries - 1:
                    _backoff_sleep(attempt)
                    continue
                raise RuntimeError(f"请求异常: {e}") from e

    def _request_stream_with_retry(self, payload: Dict, max_retries: int = None) -> Iterator[Dict]:
        """流式请求，支持重试和超时检测"""
        max_retries = max_retries or TimeoutConfig.MAX_RETRIES
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        # DNS 预检
        conn_err = self._check_connectivity()
        if conn_err:
            raise RuntimeError(conn_err)

        last_error = None
        for attempt in range(max_retries):
            resp = None
            try:
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                timeout = TimeoutConfig.STREAM_CONNECT_TIMEOUT if attempt == 0 else TimeoutConfig.READ_TIMEOUT_RETRY
                resp = urllib.request.urlopen(req, timeout=timeout)
                yield from self._read_stream(resp)
                return  # 成功完成
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                if _is_context_overflow(e.code, err_body):
                    raise RuntimeError(f"上下文过长 (HTTP {e.code}): 请减少输入或运行 /compact")
                if _is_retryable(e.code) and attempt < max_retries - 1:
                    _backoff_sleep(attempt)
                    continue
                raise RuntimeError(f"LLM API 错误 {e.code}: {err_body[:300]}") from e
            except (urllib.error.URLError, socket.timeout, TimeoutError,
                    ConnectionError, ConnectionResetError, BrokenPipeError,
                    OSError, RuntimeError) as e:
                last_error = e
                if (_is_timeout_error(e) or "流式" in str(e)) and attempt < max_retries - 1:
                    _backoff_sleep(attempt)
                    continue
                raise
            finally:
                if resp:
                    try:
                        resp.close()
                    except Exception:
                        pass

    def _read_stream(self, resp) -> Iterator[Dict]:
        """读取流式响应，带空闲超时检测（45s 无数据 → 卡死）"""
        last_data_time = time.time()
        stream_start = time.time()
        chunk_count = 0
        idle_timeout = TimeoutConfig.STREAM_IDLE_TIMEOUT

        try:
            for raw_line in resp:
                now = time.time()
                # 总超时
                if now - stream_start > TimeoutConfig.STREAM_TOTAL_TIMEOUT:
                    raise RuntimeError(f"流式总超时（{TimeoutConfig.STREAM_TOTAL_TIMEOUT}s），已收到 {chunk_count} 个 chunk")
                # 空闲超时
                if now - last_data_time > idle_timeout:
                    raise RuntimeError(f"流式空闲超时（{idle_timeout}s 无数据），已收到 {chunk_count} 个 chunk")
                last_data_time = now
                chunk_count += 1

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
        except socket.timeout as e:
            raise RuntimeError(f"流式读取超时（socket.timeout），已运行 {time.time() - stream_start:.0f}s，收到 {chunk_count} 个 chunk") from e
        except RuntimeError:
            raise
        except Exception as e:
            err = str(e).lower()
            if any(kw in err for kw in ["timed out", "timeout", "reset", "broken pipe", "eof", "incomplete"]):
                raise RuntimeError(f"流式连接中断 ({type(e).__name__}): {e}") from e
            raise

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
