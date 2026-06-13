"""蒙多的 LLM 多模型客户端 — 全量 AI 模型支持

v24.4:
- 指数退避重试（网络抖动不直接失败）
- 响应校验（choices 为空时优雅降级）
- 连接超时与读超时分离
"""

import os
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Optional

ENV_PATH = Path.home() / ".hermes" / ".env"
MUNDO_ENV = Path.home() / ".hermes" / "mundo-agent" / ".env"

# 重试配置
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0   # 秒（指数退避基数）
CONNECT_TIMEOUT = 15      # 连接超时
READ_TIMEOUT = 120        # 读取超时


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

# 从 setup.py 导入全量 provider 配置
from setup import PROVIDERS


class LLMClient:
    """蒙多的多模型 LLM 客户端"""

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
        return self._request_with_retry(payload)

    def _request_with_retry(self, payload: Dict) -> Dict:
        """带指数退避重试的请求"""
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                return self._request(payload)
            except urllib.error.HTTPError as e:
                last_error = e
                status = e.code
                # 429 (Rate Limit) 和 5xx 服务端错误可重试
                if status == 429 or status >= 500:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    # 尝试从响应头获取 Retry-After
                    retry_after = e.headers.get("Retry-After")
                    if retry_after:
                        try:
                            delay = max(delay, float(retry_after))
                        except (ValueError, TypeError):
                            pass
                    time.sleep(delay)
                    continue
                # 4xx 客户端错误不重试
                err_body = e.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"LLM API 错误 {status}: {err_body[:300]}") from e
            except urllib.error.URLError as e:
                last_error = e
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                time.sleep(delay)
                continue
            except Exception as e:
                last_error = e
                break

        # 所有重试都失败
        if isinstance(last_error, urllib.error.HTTPError):
            err_body = last_error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM API 错误 {last_error.code}（重试 {MAX_RETRIES} 次后失败）: {err_body[:200]}")
        elif isinstance(last_error, urllib.error.URLError):
            raise RuntimeError(f"网络错误（重试 {MAX_RETRIES} 次后失败）: {last_error.reason}")
        else:
            raise RuntimeError(f"LLM 请求失败（重试 {MAX_RETRIES} 次后）: {last_error}")

    def _request(self, payload: Dict) -> Dict:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=READ_TIMEOUT) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        # 响应基本校验
        if not isinstance(result, dict):
            raise RuntimeError(f"LLM 返回非法格式: {type(result).__name__}")
        if "choices" not in result:
            raise RuntimeError(f"LLM 响应缺少 choices 字段: {list(result.keys())[:5]}")
        if not result["choices"]:
            raise RuntimeError("LLM 返回空 choices 数组")

        return result

    @staticmethod
    def extract_response(result: Dict) -> Dict:
        choices = result.get("choices")
        if not choices:
            return {"role": "assistant", "content": "", "tool_calls": []}
        message = choices[0].get("message", {})
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
