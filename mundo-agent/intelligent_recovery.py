"""蒙多智能错误恢复 v3.0.0 — 帝皇的不死之身

不是简单的重试。是根据错误类型智能选择恢复策略。

恢复策略（Recovery Strategies）：
1. 瞬时错误 → 指数退避重试
2. 资源不足 → 降级/切换
3. 权限不足 → 提示用户
4. 网络问题 → 切换端点/重连
5. 逻辑错误 → 换思路/换工具
6. 上下文溢出 → 压缩/截断

知识来源：
- Circuit Breaker Pattern (Nygard, 2018)
- Retry with Exponential Backoff
- Graceful Degradation
- Bulkhead Pattern
"""

import time
import random
import hashlib
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import defaultdict


class ErrorCategory(Enum):
    TRANSIENT = auto()      # 瞬时错误（网络抖动、超时）
    RESOURCE = auto()       # 资源不足（内存、token、配额）
    PERMISSION = auto()     # 权限不足
    NETWORK = auto()        # 网络问题（DNS、连接）
    LOGIC = auto()          # 逻辑错误（工具失败、参数错误）
    CONTEXT = auto()        # 上下文问题（溢出、截断）
    UNKNOWN = auto()        # 未知错误


class RecoveryStrategy(Enum):
    RETRY_IMMEDIATE = "retry_immediate"       # 立即重试
    RETRY_BACKOFF = "retry_backoff"           # 指数退避重试
    RETRY_WITH_VARIATION = "retry_variation"  # 改变参数重试
    SWITCH_ENDPOINT = "switch_endpoint"       # 切换API端点
    COMPRESS_CONTEXT = "compress_context"     # 压缩上下文
    DEGRADE_QUALITY = "degrade_quality"       # 降级质量
    ASK_USER = "ask_user"                     # 询问用户
    SWITCH_TOOL = "switch_tool"               # 切换工具
    ABORT = "abort"                           # 中止任务


@dataclass
class ErrorRecord:
    """错误记录"""
    timestamp: float
    error_type: str
    error_message: str
    category: ErrorCategory
    tool_name: str
    args_hash: str
    recovery_strategy: RecoveryStrategy
    recovery_success: bool
    duration_ms: float


@dataclass
class RecoveryPlan:
    """恢复计划"""
    strategy: RecoveryStrategy
    max_attempts: int
    backoff_base: float
    backoff_max: float
    jitter: bool
    fallback_strategy: Optional[RecoveryStrategy] = None
    parameters: Dict = field(default_factory=dict)


class ErrorClassifier:
    """错误分类器 — 理解错误的本质"""

    ERROR_PATTERNS = {
        ErrorCategory.TRANSIENT: [
            (r"timeout", 0.9),
            (r"timed?\s*out", 0.9),
            (r"temporary", 0.8),
            (r"retry", 0.7),
            (r"429", 0.95),   # Rate limit
            (r"503", 0.9),    # Service unavailable
        ],
        ErrorCategory.RESOURCE: [
            (r"out\s+of\s+memory", 0.95),
            (r"quota\s+exceeded", 0.9),
            (r"token\s+limit", 0.9),
            (r"context\s+(length|window)", 0.95),
            (r"too\s+many\s+tokens", 0.9),
            (r"413", 0.9),    # Payload too large
        ],
        ErrorCategory.PERMISSION: [
            (r"permission\s+denied", 0.95),
            (r"access\s+denied", 0.95),
            (r"forbidden", 0.9),
            (r"401", 0.95),   # Unauthorized
            (r"403", 0.95),   # Forbidden
            (r"unauthorized", 0.9),
            (r"invalid\s+api\s+key", 0.95),
        ],
        ErrorCategory.NETWORK: [
            (r"connection\s+(refused|reset|error)", 0.95),
            (r"dns\s+resolution", 0.9),
            (r"network\s+unreachable", 0.95),
            (r"broken\s+pipe", 0.9),
            (r"eof", 0.85),
            (r"ssl", 0.8),
        ],
        ErrorCategory.LOGIC: [
            (r"not\s+found", 0.8),
            (r"file\s+not\s+found", 0.9),
            (r"no\s+such\s+file", 0.9),
            (r"invalid\s+(argument|parameter)", 0.85),
            (r"type\s+error", 0.85),
            (r"value\s+error", 0.85),
            (r"key\s+error", 0.85),
        ],
        ErrorCategory.CONTEXT: [
            (r"context\s+(length|window)\s+exceeded", 0.95),
            (r"message\s+too\s+long", 0.9),
            (r"prompt\s+is\s+too\s+long", 0.95),
            (r"maximum\s+context", 0.9),
        ],
    }

    def classify(self, error: Exception, error_message: str) -> Tuple[ErrorCategory, float]:
        """分类错误，返回 (类别, 置信度)"""
        msg = error_message.lower()
        error_type = type(error).__name__.lower()

        best_category = ErrorCategory.UNKNOWN
        best_confidence = 0.0

        for category, patterns in self.ERROR_PATTERNS.items():
            for pattern, base_confidence in patterns:
                import re
                if re.search(pattern, msg) or re.search(pattern, error_type):
                    if base_confidence > best_confidence:
                        best_category = category
                        best_confidence = base_confidence

        return best_category, best_confidence


class RecoveryStrategySelector:
    """恢复策略选择器"""

    STRATEGY_MAP = {
        ErrorCategory.TRANSIENT: [
            RecoveryPlan(
                strategy=RecoveryStrategy.RETRY_BACKOFF,
                max_attempts=3,
                backoff_base=1.0,
                backoff_max=30.0,
                jitter=True,
            ),
        ],
        ErrorCategory.RESOURCE: [
            RecoveryPlan(
                strategy=RecoveryStrategy.COMPRESS_CONTEXT,
                max_attempts=2,
                backoff_base=0,
                backoff_max=0,
                jitter=False,
            ),
            RecoveryPlan(
                strategy=RecoveryStrategy.DEGRADE_QUALITY,
                max_attempts=1,
                backoff_base=0,
                backoff_max=0,
                jitter=False,
            ),
        ],
        ErrorCategory.PERMISSION: [
            RecoveryPlan(
                strategy=RecoveryStrategy.ASK_USER,
                max_attempts=1,
                backoff_base=0,
                backoff_max=0,
                jitter=False,
            ),
        ],
        ErrorCategory.NETWORK: [
            RecoveryPlan(
                strategy=RecoveryStrategy.SWITCH_ENDPOINT,
                max_attempts=2,
                backoff_base=2.0,
                backoff_max=30.0,
                jitter=True,
                fallback_strategy=RecoveryStrategy.RETRY_BACKOFF,
            ),
        ],
        ErrorCategory.LOGIC: [
            RecoveryPlan(
                strategy=RecoveryStrategy.SWITCH_TOOL,
                max_attempts=2,
                backoff_base=0,
                backoff_max=0,
                jitter=False,
                fallback_strategy=RecoveryStrategy.RETRY_WITH_VARIATION,
            ),
        ],
        ErrorCategory.CONTEXT: [
            RecoveryPlan(
                strategy=RecoveryStrategy.COMPRESS_CONTEXT,
                max_attempts=3,
                backoff_base=0,
                backoff_max=0,
                jitter=False,
            ),
        ],
        ErrorCategory.UNKNOWN: [
            RecoveryPlan(
                strategy=RecoveryStrategy.RETRY_BACKOFF,
                max_attempts=2,
                backoff_base=2.0,
                backoff_max=15.0,
                jitter=True,
                fallback_strategy=RecoveryStrategy.ABORT,
            ),
        ],
    }

    def select(self, category: ErrorCategory, attempt: int) -> RecoveryPlan:
        """根据错误类别和尝试次数选择恢复策略"""
        plans = self.STRATEGY_MAP.get(category, self.STRATEGY_MAP[ErrorCategory.UNKNOWN])

        for plan in plans:
            if attempt < plan.max_attempts:
                return plan

        # 所有策略都用完，使用最后一个的 fallback
        last_plan = plans[-1]
        if last_plan.fallback_strategy:
            return RecoveryPlan(
                strategy=last_plan.fallback_strategy,
                max_attempts=1,
                backoff_base=0,
                backoff_max=0,
                jitter=False,
            )

        return RecoveryPlan(
            strategy=RecoveryStrategy.ABORT,
            max_attempts=0,
            backoff_base=0,
            backoff_max=0,
            jitter=False,
        )


class IntelligentRecovery:
    """智能错误恢复引擎"""

    def __init__(self):
        self.classifier = ErrorClassifier()
        self.strategy_selector = RecoveryStrategySelector()
        self._error_history: List[ErrorRecord] = []
        self._category_counts: Dict[ErrorCategory, int] = defaultdict(int)
        self._strategy_success: Dict[RecoveryStrategy, Tuple[int, int]] = defaultdict(lambda: (0, 0))

    def analyze_error(self, error: Exception, error_message: str) -> Tuple[ErrorCategory, float]:
        """分析错误"""
        return self.classifier.classify(error, error_message)

    def get_recovery_plan(self, category: ErrorCategory, attempt: int) -> RecoveryPlan:
        """获取恢复计划"""
        return self.strategy_selector.select(category, attempt)

    def calculate_delay(self, plan: RecoveryPlan, attempt: int) -> float:
        """计算延迟时间"""
        if plan.strategy == RecoveryStrategy.RETRY_IMMEDIATE:
            return 0

        if plan.backoff_base == 0:
            return 0

        delay = min(
            plan.backoff_base * (2 ** attempt),
            plan.backoff_max,
        )

        if plan.jitter:
            delay = delay * (0.5 + random.random() * 0.5)

        return delay

    def record_recovery(self, record: ErrorRecord):
        """记录恢复结果"""
        self._error_history.append(record)
        self._category_counts[record.category] += 1

        success, total = self._strategy_success[record.recovery_strategy]
        if record.recovery_success:
            self._strategy_success[record.recovery_strategy] = (success + 1, total + 1)
        else:
            self._strategy_success[record.recovery_strategy] = (success, total + 1)

    def get_strategy_effectiveness(self) -> Dict[RecoveryStrategy, float]:
        """获取各策略的有效率"""
        effectiveness = {}
        for strategy, (success, total) in self._strategy_success.items():
            if total > 0:
                effectiveness[strategy] = success / total
        return effectiveness

    def get_error_summary(self) -> Dict:
        """获取错误摘要"""
        return {
            "total_errors": len(self._error_history),
            "by_category": dict(self._category_counts),
            "strategy_effectiveness": {
                k.value: v for k, v in self.get_strategy_effectiveness().items()
            },
        }

    def should_escalate(self, tool_name: str) -> bool:
        """判断是否需要升级处理"""
        recent = [r for r in self._error_history[-10:] if r.tool_name == tool_name]

        if len(recent) >= 5:
            return True  # 同一工具连续失败太多次

        # 检查是否有权限问题
        if any(r.category == ErrorCategory.PERMISSION for r in recent[-3:]):
            return True

        return False

    def reset(self):
        """重置"""
        self._error_history.clear()
        self._category_counts.clear()
        self._strategy_success.clear()


class ContextCompressor:
    """上下文压缩器 — 处理上下文溢出"""

    def __init__(self):
        self._compression_count = 0

    def compress_messages(self, messages: List[Dict], target_ratio: float = 0.7) -> List[Dict]:
        """压缩消息列表"""
        if len(messages) <= 4:
            return messages

        self._compression_count += 1

        # 保留系统消息和最近的消息
        system_msgs = [m for m in messages if m.get("role") == "system"]
        non_system = [m for m in messages if m.get("role") != "system"]

        if len(non_system) <= 4:
            return messages

        # 保留最近的 N 条
        keep_recent = max(4, int(len(non_system) * target_ratio))
        recent = non_system[-keep_recent:]

        # 对较早的消息生成摘要
        early = non_system[:-keep_recent]
        summary = self._summarize_messages(early)

        result = system_msgs + [{"role": "system", "content": f"[上下文压缩摘要] {summary}"}] + recent

        return result

    def _summarize_messages(self, messages: List[Dict]) -> str:
        """生成消息摘要"""
        parts = []
        for msg in messages:
            content = msg.get("content", "")
            if content:
                parts.append(content[:100])

        return " | ".join(parts[-10:]) if parts else "(无内容)"

    def truncate_content(self, content: str, max_tokens: int = 4000) -> str:
        """截断内容"""
        # 粗略估算：1 token ≈ 2 中文字 或 4 英文字
        estimated_tokens = len(content) / 2
        if estimated_tokens <= max_tokens:
            return content

        # 按比例截断
        ratio = max_tokens / estimated_tokens
        target_length = int(len(content) * ratio)

        # 保留开头和结尾
        keep_start = int(target_length * 0.7)
        keep_end = target_length - keep_start

        return content[:keep_start] + "\n...(已截断)...\n" + content[-keep_end:]


# 全局单例
_recovery: Optional[IntelligentRecovery] = None
_compressor: Optional[ContextCompressor] = None


def get_recovery() -> IntelligentRecovery:
    global _recovery
    if _recovery is None:
        _recovery = IntelligentRecovery()
    return _recovery


def get_compressor() -> ContextCompressor:
    global _compressor
    if _compressor is None:
        _compressor = ContextCompressor()
    return _compressor
