"""工具循环防护 — 从 Hermes Agent tool_guardrails 提炼

检测三种失败模式：
1. 精确失败：同一工具+同一参数连续失败 → 陷入死循环
2. 同工具失败：同一工具不同参数连续失败 → 工具本身有问题
3. 无进展：幂等工具连续调用但结果不变 → 原地踏步

决策分级：allow → warn → block → halt
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Set


class GuardAction(Enum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    HALT = "halt"


@dataclass(frozen=True)
class ToolCallSig:
    """工具调用签名 = 工具名 + 参数哈希"""
    tool_name: str
    args_hash: str

    @classmethod
    def from_call(cls, tool_name: str, args: Any) -> "ToolCallSig":
        canonical = json.dumps(args or {}, sort_keys=True, ensure_ascii=False)
        h = hashlib.sha256(canonical.encode()).hexdigest()[:16]
        return cls(tool_name=tool_name, args_hash=h)


@dataclass
class GuardDecision:
    action: GuardAction = GuardAction.ALLOW
    code: str = "allow"
    message: str = ""


@dataclass
class GuardConfig:
    # 精确失败（同工具+同参数）
    exact_fail_warn: int = 2
    exact_fail_block: int = 5
    # 同工具失败（同工具，不同参数）
    same_tool_warn: int = 3
    same_tool_halt: int = 8
    # 无进展（幂等工具连续调用，结果不变）
    no_progress_warn: int = 2
    no_progress_block: int = 5
    # 硬停开关
    hard_stop_enabled: bool = False


# 幂等工具：读取操作，重复调用无副作用
IDEMPOTENT_TOOLS: FrozenSet[str] = frozenset({
    "read_file", "search_files", "web_search", "list_directory",
})

# 变更工具：写入操作，重复调用有副作用
MUTATING_TOOLS: FrozenSet[str] = frozenset({
    "terminal", "write_file", "edit_file", "patch",
})


class ToolGuardController:
    """工具循环防护控制器 — 无副作用，只观察和决策"""

    def __init__(self, config: Optional[GuardConfig] = None):
        self._config = config or GuardConfig()
        # 精确失败计数：(tool_name, args_hash) -> 连续失败次数
        self._exact_failures: Dict[tuple, int] = {}
        # 同工具失败计数：tool_name -> 连续失败次数
        self._tool_failures: Dict[str, int] = {}
        # 无进展计数：tool_name -> 连续调用次数（结果不变）
        self._no_progress: Dict[str, int] = {}
        # 上一次幂等工具结果哈希
        self._last_idempotent_result: Dict[str, str] = {}

    def observe(
        self,
        tool_name: str,
        args: Any,
        result: str,
        is_error: bool,
    ) -> GuardDecision:
        """观察一次工具调用，返回防护决策"""
        sig = ToolCallSig.from_call(tool_name, args)
        cfg = self._config

        # 1. 精确失败检测
        if is_error:
            key = (sig.tool_name, sig.args_hash)
            self._exact_failures[key] = self._exact_failures.get(key, 0) + 1
            count = self._exact_failures[key]

            if count >= cfg.exact_fail_block and cfg.hard_stop_enabled:
                return GuardDecision(
                    action=GuardAction.HALT,
                    code="exact_fail_halt",
                    message=f"[御史弹劾] {tool_name} 同参数连续失败 {count} 次，判定死循环，强制中止",
                )
            if count >= cfg.exact_fail_warn:
                return GuardDecision(
                    action=GuardAction.WARN if count < cfg.exact_fail_block else GuardAction.BLOCK,
                    code="exact_fail_warn",
                    message=f"[朝臣谏言] {tool_name} 已连续失败 {count} 次（同参数），建议换策略",
                )
        else:
            # 成功则重置精确失败计数
            self._exact_failures.pop((sig.tool_name, sig.args_hash), None)

        # 2. 同工具失败检测
        if is_error:
            self._tool_failures[tool_name] = self._tool_failures.get(tool_name, 0) + 1
            count = self._tool_failures[tool_name]

            if count >= cfg.same_tool_halt and cfg.hard_stop_enabled:
                return GuardDecision(
                    action=GuardAction.HALT,
                    code="same_tool_halt",
                    message=f"[御史弹劾] {tool_name} 连续失败 {count} 次，强制中止",
                )
            if count >= cfg.same_tool_warn:
                return GuardDecision(
                    action=GuardAction.WARN if count < cfg.same_tool_halt else GuardAction.BLOCK,
                    code="same_tool_warn",
                    message=f"[朝臣谏言] {tool_name} 已连续失败 {count} 次，建议换工具",
                )
        else:
            self._tool_failures.pop(tool_name, None)

        # 3. 无进展检测（仅幂等工具）
        if not is_error and tool_name in IDEMPOTENT_TOOLS:
            result_hash = hashlib.sha256(result.encode()).hexdigest()[:16]
            last_hash = self._last_idempotent_result.get(tool_name)

            if last_hash == result_hash:
                self._no_progress[tool_name] = self._no_progress.get(tool_name, 0) + 1
                count = self._no_progress[tool_name]

                if count >= cfg.no_progress_block and cfg.hard_stop_enabled:
                    return GuardDecision(
                        action=GuardAction.HALT,
                        code="no_progress_halt",
                        message=f"[御史弹劾] {tool_name} 连续 {count} 次无新结果，原地踏步，强制中止",
                    )
                if count >= cfg.no_progress_warn:
                    return GuardDecision(
                        action=GuardAction.WARN if count < cfg.no_progress_block else GuardAction.BLOCK,
                        code="no_progress_warn",
                        message=f"[朝臣谏言] {tool_name} 连续 {count} 次返回相同结果，可能在原地踏步",
                    )
            else:
                self._no_progress.pop(tool_name, None)

            self._last_idempotent_result[tool_name] = result_hash

        return GuardDecision()

    def reset(self):
        """重置所有计数器（新一轮对话开始时调用）"""
        self._exact_failures.clear()
        self._tool_failures.clear()
        self._no_progress.clear()
        self._last_idempotent_result.clear()

    def stats(self) -> Dict[str, Any]:
        """返回当前防护状态"""
        return {
            "exact_failures": dict(self._exact_failures),
            "tool_failures": dict(self._tool_failures),
            "no_progress": dict(self._no_progress),
        }
