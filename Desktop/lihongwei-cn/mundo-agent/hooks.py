"""事件钩子系统 — 从 Claude Code hooks 提炼

支持两种钩子类型：
1. command型：执行确定性检查（快，无token消耗）
2. prompt型：用LLM做上下文感知决策（慢，消耗token，但更智能）

事件类型：
- PreToolUse: 工具执行前（可拒绝/修改参数）
- PostToolUse: 工具执行后（可修改结果）
- TurnStart: 对话轮次开始
- TurnEnd: 对话轮次结束
- OnError: 错误发生时
"""

import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class HookEvent(Enum):
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    TURN_START = "TurnStart"
    TURN_END = "TurnEnd"
    ON_ERROR = "OnError"


class HookDecision(Enum):
    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"
    MODIFY = "modify"


@dataclass
class HookResult:
    decision: HookDecision = HookDecision.ALLOW
    message: str = ""
    modified_input: Optional[Dict] = None
    modified_output: Optional[str] = None


@dataclass
class Hook:
    name: str
    event: HookEvent
    matcher: str = ".*"  # 工具名正则匹配
    handler: Optional[Callable] = None  # command型处理函数
    prompt: str = ""  # prompt型提示词
    timeout: int = 30
    priority: int = 50  # 越小越先执行
    _compiled_pattern: Any = field(default=None, repr=False)

    def __post_init__(self):
        self._compiled_pattern = re.compile(self.matcher)

    def matches(self, tool_name: str) -> bool:
        return bool(self._compiled_pattern.match(tool_name))


# 安全钩子模板（从 Claude Code security-guidance 提炼）
SECURITY_PATTERNS = {
    "command_injection": {
        "matcher": "terminal",
        "check": lambda args: any(
            kw in str(args.get("command", ""))
            for kw in ["eval(", "exec(", "$(", "`", "&&", "||", ";rm ", ";cat "]
        ),
        "message": "[禁军巡防] 检测到可能的命令注入模式",
        "decision": HookDecision.WARN,
    },
    "path_traversal": {
        "matcher": ".*",
        "check": lambda args: any(
            ".." in str(v) for v in args.values() if isinstance(v, str)
        ),
        "message": "[禁军巡防] 检测到路径遍历（..）",
        "decision": HookDecision.WARN,
    },
    "sensitive_file": {
        "matcher": "(write_file|edit_file|patch)",
        "check": lambda args: any(
            p in str(args.get("path", ""))
            for p in ["/etc/", "~/.ssh/", ".env", "credentials", "password", "secret"]
        ),
        "message": "[禁军巡防] 操作敏感文件",
        "decision": HookDecision.WARN,
    },
    "dangerous_rm": {
        "matcher": "terminal",
        "check": lambda args: any(
            pattern in str(args.get("command", ""))
            for pattern in ["rm -rf /", "rm -rf ~", "rm -rf *", "rm -f /"]
        ),
        "message": "[禁军巡防] 检测到危险的 rm 命令",
        "decision": HookDecision.DENY,
    },
}


class HookEngine:
    """事件钩子引擎"""

    def __init__(self):
        self._hooks: Dict[HookEvent, List[Hook]] = {e: [] for e in HookEvent}
        self._security_enabled = True
        self._stats = {"fired": 0, "denied": 0, "warned": 0}

    def register(self, hook: Hook):
        """注册钩子"""
        self._hooks[hook.event].append(hook)
        self._hooks[hook.event].sort(key=lambda h: h.priority)

    def unregister(self, name: str):
        """按名称注销钩子"""
        for event in self._hooks:
            self._hooks[event] = [h for h in self._hooks[event] if h.name != name]

    def enable_security_hooks(self):
        """启用内置安全钩子"""
        for name, pattern in SECURITY_PATTERNS.items():
            self.register(Hook(
                name=f"security_{name}",
                event=HookEvent.PRE_TOOL_USE,
                matcher=pattern["matcher"],
                handler=lambda ctx, _p=pattern: HookResult(
                    decision=_p["decision"],
                    message=_p["message"],
                ) if _p["check"](ctx.get("args", {})) else HookResult(),
                priority=10,
            ))
        self._security_enabled = True

    def fire(
        self,
        event: HookEvent,
        tool_name: str = "",
        args: Optional[Dict] = None,
        output: str = "",
        error: str = "",
    ) -> HookResult:
        """触发事件钩子，返回最终决策"""
        self._stats["fired"] += 1
        final = HookResult()
        context = {
            "tool_name": tool_name,
            "args": args or {},
            "output": output,
            "error": error,
        }

        for hook in self._hooks.get(event, []):
            if not hook.matches(tool_name):
                continue

            if hook.handler:
                try:
                    result = hook.handler(context)
                    if isinstance(result, HookResult):
                        if result.decision == HookDecision.DENY:
                            self._stats["denied"] += 1
                            return result
                        if result.decision == HookDecision.WARN:
                            self._stats["warned"] += 1
                            final = result
                        if result.decision == HookDecision.MODIFY:
                            final = result
                except Exception:
                    pass

        return final

    def stats(self) -> Dict[str, int]:
        return dict(self._stats)

    def reset_stats(self):
        self._stats = {"fired": 0, "denied": 0, "warned": 0}


def create_default_engine() -> HookEngine:
    """创建带安全钩子的默认引擎"""
    engine = HookEngine()
    engine.enable_security_hooks()
    return engine
