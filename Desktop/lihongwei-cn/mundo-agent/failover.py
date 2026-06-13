"""错误恢复 Failover 链 — 从 Hermes Agent 错误分类提炼

自动错误分类 + failover 到备用模型：
1. classify_error：将异常映射到 FailoverReason
2. FailoverChain：维护主模型→备用模型链
3. 自动切换：可恢复错误 → 重试，不可恢复 → failover
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


class FailoverReason(Enum):
    CONNECTION = "connection"        # 连接中断（可重试）
    TIMEOUT = "timeout"              # 超时（可重试）
    RATE_LIMIT = "rate_limit"        # 限速（可重试，需退避）
    AUTH = "auth"                    # 认证失败（不可重试）
    SERVER = "server"                # 服务端错误（可重试）
    CONTEXT_LENGTH = "context_length"  # 上下文超长（需压缩）
    QUOTA = "quota"                  # 配额耗尽（需failover）
    UNKNOWN = "unknown"              # 未知错误


@dataclass
class FailoverConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    backoff_factor: float = 2.0
    jitter: bool = True


@dataclass
class FailoverEvent:
    model: str
    reason: FailoverReason
    error: str
    attempt: int
    timestamp: float = field(default_factory=time.time)


def classify_error(error: Exception, raw_msg: str = "") -> FailoverReason:
    """将异常映射到 FailoverReason"""
    msg = str(error).lower() + " " + raw_msg.lower()

    if isinstance(error, (ConnectionResetError, ConnectionRefusedError, BrokenPipeError)):
        return FailoverReason.CONNECTION
    if any(kw in msg for kw in ["reset", "broken pipe", "eof"]):
        return FailoverReason.CONNECTION
    if any(kw in msg for kw in ["timeout", "timed out"]):
        return FailoverReason.TIMEOUT
    if any(kw in msg for kw in ["429", "rate limit", "too many"]):
        return FailoverReason.RATE_LIMIT
    if any(kw in msg for kw in ["401", "unauthorized", "invalid api key"]):
        return FailoverReason.AUTH
    if any(kw in msg for kw in ["500", "502", "503", "504", "internal server"]):
        return FailoverReason.SERVER
    if any(kw in msg for kw in ["context length", "max_tokens", "too long"]):
        return FailoverReason.CONTEXT_LENGTH
    if any(kw in msg for kw in ["quota", "billing", "credits", "insufficient"]):
        return FailoverReason.QUOTA
    return FailoverReason.UNKNOWN


# 各 FailoverReason 的默认策略
REASON_STRATEGIES = {
    FailoverReason.CONNECTION: {"retryable": True, "failover": False},
    FailoverReason.TIMEOUT: {"retryable": True, "failover": False},
    FailoverReason.RATE_LIMIT: {"retryable": True, "failover": True},
    FailoverReason.AUTH: {"retryable": False, "failover": True},
    FailoverReason.SERVER: {"retryable": True, "failover": False},
    FailoverReason.CONTEXT_LENGTH: {"retryable": False, "failover": False},
    FailoverReason.QUOTA: {"retryable": False, "failover": True},
    FailoverReason.UNKNOWN: {"retryable": False, "failover": False},
}


class FailoverChain:
    """Failover 链 — 主模型失败时自动切换到备用模型"""

    def __init__(
        self,
        primary: str,
        fallbacks: Optional[List[str]] = None,
        config: Optional[FailoverConfig] = None,
        on_failover: Optional[Callable[[str, str, FailoverReason], None]] = None,
    ):
        self._primary = primary
        self._fallbacks = fallbacks or []
        self._config = config or FailoverConfig()
        self._on_failover = on_failover
        self._current_index = 0
        self._history: List[FailoverEvent] = []
        self._retry_counts: Dict[str, int] = {}

    @property
    def current_model(self) -> str:
        chain = [self._primary] + self._fallbacks
        return chain[min(self._current_index, len(chain) - 1)]

    def should_retry(self, error: Exception, raw_msg: str = "") -> Tuple[bool, float]:
        """判断是否应重试，返回 (是否重试, 延迟秒数)"""
        reason = classify_error(error, raw_msg)
        strategy = REASON_STRATEGIES.get(reason, {"retryable": False, "failover": False})

        model = self.current_model
        self._retry_counts[model] = self._retry_counts.get(model, 0) + 1

        if strategy["retryable"] and self._retry_counts[model] <= self._config.max_retries:
            delay = self._calc_delay(self._retry_counts[model])
            return True, delay

        if strategy["failover"]:
            return False, 0  # 不重试，应该 failover

        return False, 0

    def failover(self, error: Exception, raw_msg: str = "") -> Optional[str]:
        """切换到下一个备用模型，返回新模型名或 None（无备用）"""
        reason = classify_error(error, raw_msg)
        chain = [self._primary] + self._fallbacks

        self._history.append(FailoverEvent(
            model=self.current_model,
            reason=reason,
            error=str(error)[:200],
            attempt=self._retry_counts.get(self.current_model, 0),
        ))

        self._current_index += 1
        if self._current_index >= len(chain):
            return None  # 无备用模型

        new_model = chain[self._current_index]
        self._retry_counts[new_model] = 0  # 重置新模型的重试计数

        if self._on_failover:
            self._on_failover(self._history[-1].model, new_model, reason)

        return new_model

    def reset(self):
        """重置到主模型"""
        self._current_index = 0
        self._retry_counts.clear()

    def history(self) -> List[Dict[str, Any]]:
        return [
            {
                "model": e.model,
                "reason": e.reason.value,
                "error": e.error[:100],
                "attempt": e.attempt,
            }
            for e in self._history
        ]

    def stats(self) -> Dict[str, Any]:
        return {
            "current_model": self.current_model,
            "primary": self._primary,
            "fallbacks": self._fallbacks,
            "total_failovers": len(self._history),
            "retry_counts": dict(self._retry_counts),
        }

    def _calc_delay(self, attempt: int) -> float:
        delay = self._config.base_delay * (self._config.backoff_factor ** (attempt - 1))
        delay = min(delay, self._config.max_delay)
        if self._config.jitter:
            import random
            delay *= (0.5 + random.random())
        return delay
