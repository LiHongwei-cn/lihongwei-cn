"""蒙多 LLM 客户端 — 重构版

改进：
- 统一错误处理
- 重试机制优化
- 消息清洗增强
- 性能监控
"""

import os
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Iterator, Optional

from ..utils.errors import LLMError, ContextOverflowError, NetworkError
from ..utils.logging import get_llm_logger

logger = get_llm_logger()


_env_loaded = False

def _load_env():
    """加载环境变量（仅首次调用时执行）"""
    global _env_loaded
    if _env_loaded:
        return
    _env_loaded = True

    env_paths = [
        Path.home() / ".hermes" / "mundo-agent" / ".env",
        Path.home() / ".hermes" / ".env",
    ]

    for path in env_paths:
        if not path.exists():
            continue
        try:
            for line in path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
        except Exception as e:
            logger.warning(f"加载环境变量失败 {path}: {e}")


# 不在模块导入时加载，延迟到 LLMClient.__init__ 时


# ═══════════════════════════════════════════════
# 可重试错误判断
# ═══════════════════════════════════════════════

RETRYABLE_CODES = {429, 500, 502, 503, 504}
CONTEXT_OVERFLOW_CODES = {400, 413}


def _is_retryable(code: int) -> bool:
    """判断是否可重试"""
    return code in RETRYABLE_CODES


def _is_context_overflow(code: int, body: str) -> bool:
    """判断是否上下文溢出"""
    if code in CONTEXT_OVERFLOW_CODES:
        keywords = ["context", "too long", "maximum", "token", "limit"]
        return any(kw in body.lower() for kw in keywords)
    return False


# ═══════════════════════════════════════════════
# 消息清洗
# ═══════════════════════════════════════════════

def _fix_surrogates(text: str) -> str:
    """修复 surrogate 字符"""
    try:
        text.encode("utf-8")
        return text
    except UnicodeEncodeError:
        return text.encode("utf-8", errors="replace").decode("utf-8")


def _coerce_content(value) -> str:
    """强制转换 content 为字符串"""
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

        role = msg.get("role", "")
        content = msg.get("content")
        tool_calls = msg.get("tool_calls")
        tool_call_id = msg.get("tool_call_id")

        # 快速检查：是否需要修改
        needs_copy = False

        # content 检查
        if content is not None:
            if not isinstance(content, str) or content != _fix_surrogates(content):
                needs_copy = True

        # tool_calls 检查
        if tool_calls:
            for tc in tool_calls:
                func = tc.get("function", {})
                raw_args = func.get("arguments", "{}")
                if not isinstance(raw_args, str):
                    needs_copy = True
                    break
                try:
                    json.loads(raw_args)
                except (json.JSONDecodeError, TypeError):
                    needs_copy = True
                    break

        # tool role 无 content
        if role == "tool" and content is None:
            needs_copy = True

        # 空消息过滤
        if (content is None or content == "") and not tool_calls and not tool_call_id and role not in ("system",):
            continue

        # 无需修改则直接引用（零拷贝）
        if not needs_copy:
            cleaned.append(msg)
            continue

        # 需要修改，创建副本
        m = dict(msg)
        if "content" in m:
            m["content"] = _coerce_content(m["content"])

        if tool_calls:
            valid_tcs = []
            for tc in tool_calls:
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

        if role == "tool" and "content" not in m:
            m["content"] = ""

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

    # 尝试修复
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
# LLM 客户端
# ═══════════════════════════════════════════════

class LLMClient:
    """LLM 客户端"""

    def __init__(self, provider: str = "xiaomi", model: str = None, api_key: str = None):
        _load_env()  # 延迟加载环境变量
        from setup import PROVIDERS

        cfg = PROVIDERS.get(provider)
        if not cfg:
            raise LLMError(f"未知 provider: {provider}", "INVALID_PROVIDER")

        self.provider = provider
        self.model = model or cfg["model"]
        self.base_url = cfg["base_url"]
        self.anthropic_base_url = cfg.get("anthropic_base_url", "")
        self.api_key = api_key or os.environ.get(cfg["env_key"], "")

        if not self.api_key:
            raise LLMError(
                f"缺少 {cfg['env_key']}。运行 /setup 或 /add 配置。",
                "MISSING_API_KEY"
            )

        logger.debug(f"初始化 LLM 客户端: {provider}/{self.model}")

    def chat(self, messages: List[Dict], tools: List[Dict] = None,
             temperature: float = 0.7, max_tokens: int = 4096) -> Dict:
        """非流式聊天"""
        payload = self._build_payload(messages, tools, temperature, max_tokens, stream=False)
        return self._request_with_retry(payload)

    def chat_stream(self, messages: List[Dict], tools: List[Dict] = None,
                    temperature: float = 0.7, max_tokens: int = 4096) -> Iterator[Dict]:
        """流式聊天"""
        payload = self._build_payload(messages, tools, temperature, max_tokens, stream=True)
        yield from self._request_stream(payload)

    def _build_payload(self, messages, tools, temperature, max_tokens, stream=False):
        """构建请求载荷"""
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
        """带重试的请求"""
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
                logger.debug(f"LLM 请求 (尝试 {attempt + 1}/{max_retries})")

                with urllib.request.urlopen(req, timeout=180) as resp:
                    return json.loads(resp.read().decode("utf-8"))

            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")

                # 上下文溢出 — 不重试，直接报错让引擎压缩
                if _is_context_overflow(e.code, err_body):
                    raise ContextOverflowError(f"上下文过长 (HTTP {e.code})")

                # 可重试错误
                if _is_retryable(e.code) and attempt < max_retries - 1:
                    wait = min(2 ** attempt * 2, 30)
                    logger.warning(f"LLM 请求失败 ({e.code})，{wait}s 后重试")
                    time.sleep(wait)
                    continue

                raise LLMError(f"LLM API 错误 {e.code}: {err_body[:300]}", "API_ERROR", e.code)

            except urllib.error.URLError as e:
                last_error = e.reason
                if attempt < max_retries - 1:
                    wait = 2 * (attempt + 1)
                    logger.warning(f"网络错误，{wait}s 后重试: {last_error}")
                    time.sleep(wait)
                    continue

                raise NetworkError(f"网络错误: {last_error}")

            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    wait = 2 * (attempt + 1)
                    logger.warning(f"请求异常，{wait}s 后重试: {last_error}")
                    time.sleep(wait)
                    continue

                raise LLMError(f"请求异常: {last_error}", "REQUEST_ERROR")

        raise LLMError("LLM 调用失败: 重试耗尽", "RETRY_EXHAUSTED")

    def _request_stream(self, payload: Dict) -> Iterator[Dict]:
        """流式请求"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            resp = urllib.request.urlopen(req, timeout=180)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            if _is_context_overflow(e.code, err_body):
                raise ContextOverflowError(f"上下文过长 (HTTP {e.code})")
            raise LLMError(f"LLM API 错误 {e.code}: {err_body[:300]}", "API_ERROR", e.code)
        except urllib.error.URLError as e:
            raise NetworkError(f"网络错误: {e.reason}")

        import socket

        last_data_time = time.time()
        STREAM_IDLE_TIMEOUT = 120  # 120 秒无数据 → 超时

        try:
            for raw_line in resp:
                now = time.time()

                # 检查 idle timeout
                if now - last_data_time > STREAM_IDLE_TIMEOUT:
                    raise LLMError(f"流式读取超时（{STREAM_IDLE_TIMEOUT}s 无数据）", "STREAM_TIMEOUT")

                last_data_time = now

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
            raise LLMError(f"流式读取超时（{STREAM_IDLE_TIMEOUT}s 无数据）", "STREAM_TIMEOUT")
        except LLMError:
            raise
        except Exception as e:
            err = str(e).lower()
            if "timed out" in err or "timeout" in err or "reset" in err or "broken pipe" in err:
                raise NetworkError(f"流式连接中断: {e}")
            raise
        finally:
            try:
                resp.close()
            except Exception:
                pass

    @staticmethod
    def extract_stream_delta(chunk: Dict) -> Dict:
        """提取流式响应的 delta"""
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
        """提取响应"""
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
        """提取 token 使用情况"""
        usage = result.get("usage", {})
        return {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }


def get_available_providers() -> List[str]:
    """获取可用的 provider 列表"""
    from setup import PROVIDERS

    available = []
    for name, cfg in PROVIDERS.items():
        if os.environ.get(cfg["env_key"]):
            available.append(name)
    return available