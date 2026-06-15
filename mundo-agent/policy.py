"""蒙多 Policy 引擎 v2.2.0 — 皇帝的律法

不是简单的正则匹配。是可组合、可继承、可定制的规则引擎。
每条规则都有优先级、动作、条件。规则可以被覆盖、禁用、链式组合。

设计哲学：
- 规则是声明式的，不是命令式的
- 默认拒绝，显式允许
- 规则可继承：全局 → 项目 → 会话
- 每条规则都有理由，皇帝不接受无理由的裁决

v2.2.0: 合并 approval.py 的用户审批逻辑，成为唯一审批引擎
"""

import re
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Optional, Callable, Any, Tuple
from pathlib import Path

# Rich 渲染（可选）
try:
    from rich.console import Console
    _console = Console(highlight=False, force_terminal=True)
except ImportError:
    _console = None


# ═══════════════════════════════════════════════
# 枚举 — 规则的灵魂
# ═══════════════════════════════════════════════

class Action(Enum):
    ALLOW = auto()
    DENY = auto()
    ASK = auto()
    LOG = auto()
    ESCALATE = auto()


class Scope(Enum):
    GLOBAL = auto()      # 所有会话
    PROJECT = auto()     # 当前项目
    SESSION = auto()     # 当前会话
    TOOL = auto()        # 单次工具调用


class Severity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


# ═══════════════════════════════════════════════
# 规则 — 皇帝的一条律法
# ═══════════════════════════════════════════════

@dataclass
class Rule:
    name: str
    action: Action
    condition: Callable[[Dict[str, Any]], bool]
    scope: Scope = Scope.GLOBAL
    severity: Severity = Severity.MEDIUM
    reason: str = ""
    priority: int = 100
    enabled: bool = True
    tags: List[str] = field(default_factory=list)

    def evaluate(self, context: Dict[str, Any]) -> Optional[Action]:
        if not self.enabled:
            return None
        try:
            if self.condition(context):
                return self.action
        except Exception:
            pass
        return None


# ═══════════════════════════════════════════════
# 策略上下文 — 每次决策的战场情报
# ═══════════════════════════════════════════════

@dataclass
class PolicyContext:
    tool_name: str = ""
    tool_args: Dict = field(default_factory=dict)
    command: str = ""
    file_path: str = ""
    content: str = ""
    project_path: str = ""
    user_input: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "command": self.command,
            "file_path": self.file_path,
            "content": self.content,
            "project_path": self.project_path,
            "user_input": self.user_input,
            "metadata": self.metadata,
        }


@dataclass
class PolicyResult:
    action: Action
    rule: Optional[Rule] = None
    reason: str = ""
    details: str = ""

    @property
    def is_allowed(self) -> bool:
        return self.action == Action.ALLOW

    @property
    def is_denied(self) -> bool:
        return self.action == Action.DENY

    @property
    def needs_approval(self) -> bool:
        return self.action == Action.ASK


# ═══════════════════════════════════════════════
# 内置规则 — 皇帝的常备律法
# ═══════════════════════════════════════════════

def _cmd_contains(patterns: List[str]) -> Callable:
    def check(ctx: Dict) -> bool:
        cmd = ctx.get("command", "").lower()
        return any(p in cmd for p in patterns)
    return check


def _cmd_matches(pattern: str) -> Callable:
    regex = re.compile(pattern, re.IGNORECASE)
    def check(ctx: Dict) -> bool:
        return bool(regex.search(ctx.get("command", "")))
    return check


def _path_in_sensitive(ctx: Dict) -> bool:
    sensitive = [".env", ".ssh", ".gnupg", "credentials", "secret", "token", "password"]
    path = ctx.get("file_path", "").lower()
    return any(s in path for s in sensitive)


def _content_has_secrets(ctx: Dict) -> bool:
    patterns = [
        r"api[_-]?key\s*[:=]\s*['\"][^'\"]+['\"]",
        r"password\s*[:=]\s*['\"][^'\"]+['\"]",
        r"secret\s*[:=]\s*['\"][^'\"]+['\"]",
        r"token\s*[:=]\s*['\"][^'\"]+['\"]",
        r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
    ]
    content = ctx.get("content", "")
    return any(re.search(p, content, re.IGNORECASE) for p in patterns)


def _file_too_large(ctx: Dict) -> bool:
    content = ctx.get("content", "")
    return len(content) > 500_000


BUILTIN_RULES: List[Rule] = [
    # ─── 毁灭级操作 ───
    Rule(
        name="deny-disk-destruction",
        action=Action.DENY,
        condition=_cmd_matches(r"\b(mkfs|dd\s+.*of=/dev/|wipefs)\b"),
        severity=Severity.CRITICAL,
        reason="磁盘格式化/覆写 — 毁灭级操作",
        priority=10,
        tags=["destructive", "disk"],
    ),
    Rule(
        name="deny-recursive-force-delete",
        action=Action.DENY,
        condition=_cmd_matches(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--no-preserve-root)\b"),
        severity=Severity.CRITICAL,
        reason="递归强制删除 — 不可逆",
        priority=10,
        tags=["destructive", "filesystem"],
    ),
    Rule(
        name="deny-kill-all",
        action=Action.DENY,
        condition=_cmd_matches(r"\bkill\s+-9\s+-1\b"),
        severity=Severity.CRITICAL,
        reason="杀死所有进程 — 系统崩溃",
        priority=10,
        tags=["destructive", "process"],
    ),
    Rule(
        name="deny-shutdown",
        action=Action.DENY,
        condition=_cmd_matches(r"\b(shutdown|reboot|init\s+0|halt)\b"),
        severity=Severity.CRITICAL,
        reason="关机/重启 — 中断所有工作",
        priority=10,
        tags=["destructive", "system"],
    ),

    # ─── 安全边界 ───
    Rule(
        name="deny-sudo",
        action=Action.ASK,
        condition=_cmd_matches(r"\bsudo\b"),
        severity=Severity.HIGH,
        reason="sudo 提权 — 需要确认意图",
        priority=20,
        tags=["security", "privilege"],
    ),
    Rule(
        name="deny-force-push",
        action=Action.ASK,
        condition=_cmd_matches(r"\bgit\s+push\s+.*--force"),
        severity=Severity.HIGH,
        reason="Git 强制推送 — 可能覆盖远程历史",
        priority=20,
        tags=["git", "destructive"],
    ),
    Rule(
        name="deny-hard-reset",
        action=Action.ASK,
        condition=_cmd_matches(r"\bgit\s+reset\s+--hard"),
        severity=Severity.HIGH,
        reason="Git 硬重置 — 丢失未提交更改",
        priority=20,
        tags=["git", "destructive"],
    ),
    Rule(
        name="deny-pipe-remote",
        action=Action.ASK,
        condition=_cmd_matches(r"\b(curl|wget)\s+.*\|\s*(ba)?sh"),
        severity=Severity.HIGH,
        reason="管道执行远程脚本 — 安全风险",
        priority=20,
        tags=["security", "network"],
    ),

    # ─── 敏感文件 ───
    Rule(
        name="protect-sensitive-files",
        action=Action.ASK,
        condition=_path_in_sensitive,
        severity=Severity.HIGH,
        reason="敏感文件操作 — 可能泄露密钥",
        priority=30,
        tags=["security", "files"],
    ),
    Rule(
        name="protect-secrets-in-content",
        action=Action.DENY,
        condition=_content_has_secrets,
        severity=Severity.CRITICAL,
        reason="内容包含密钥 — 禁止泄露",
        priority=10,
        tags=["security", "secrets"],
    ),

    # ─── 资源保护 ───
    Rule(
        name="limit-file-size",
        action=Action.DENY,
        condition=_file_too_large,
        severity=Severity.MEDIUM,
        reason="文件过大 (>500KB) — 可能是误操作",
        priority=40,
        tags=["resource", "files"],
    ),
    Rule(
        name="deny-global-install",
        action=Action.ASK,
        condition=_cmd_matches(r"\b(npm|pip|brew)\s+(install|uninstall)\s+-g"),
        severity=Severity.MEDIUM,
        reason="全局安装/卸载 — 影响系统环境",
        priority=40,
        tags=["package", "system"],
    ),
    Rule(
        name="deny-docker-destructive",
        action=Action.ASK,
        condition=_cmd_matches(r"\bdocker\s+(rm|stop|kill|rmi)\b"),
        severity=Severity.MEDIUM,
        reason="Docker 容器/镜像操作 — 确认意图",
        priority=40,
        tags=["docker", "container"],
    ),
    Rule(
        name="deny-chmod-777",
        action=Action.ASK,
        condition=_cmd_matches(r"\bchmod\s+777\b"),
        severity=Severity.MEDIUM,
        reason="chmod 777 — 安全隐患",
        priority=40,
        tags=["security", "permissions"],
    ),

    # ─── 日志级 ───
    Rule(
        name="log-network-ops",
        action=Action.LOG,
        condition=_cmd_matches(r"\b(curl|wget|http)\b"),
        severity=Severity.LOW,
        reason="网络操作 — 记录审计",
        priority=80,
        tags=["network", "audit"],
    ),
    Rule(
        name="log-git-ops",
        action=Action.LOG,
        condition=_cmd_matches(r"\bgit\s+(push|pull|merge|rebase)\b"),
        severity=Severity.LOW,
        reason="Git 远程操作 — 记录审计",
        priority=80,
        tags=["git", "audit"],
    ),
]


# ═══════════════════════════════════════════════
# PolicyEngine — 皇帝的裁决大厅
# ═══════════════════════════════════════════════

class PolicyEngine:
    """结构化策略引擎 — 规则链式评估，优先级裁决"""

    def __init__(self):
        self._rules: List[Rule] = list(BUILTIN_RULES)
        self._overrides: Dict[str, Action] = {}
        self._audit_log: List[Dict] = []

    def add_rule(self, rule: Rule) -> None:
        self._rules = [r for r in self._rules if r.name != rule.name]
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority)

    def remove_rule(self, name: str) -> bool:
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.name != name]
        return len(self._rules) < before

    def override(self, rule_name: str, action: Action) -> None:
        self._overrides[rule_name] = action

    def disable_rule(self, name: str) -> None:
        for r in self._rules:
            if r.name == name:
                r.enabled = False
                break

    def enable_rule(self, name: str) -> None:
        for r in self._rules:
            if r.name == name:
                r.enabled = True
                break

    def evaluate(self, ctx: PolicyContext) -> PolicyResult:
        """按优先级遍历规则链，返回最高优先级的裁决"""
        d = ctx.to_dict()
        matched: List[Tuple[Rule, Action]] = []

        for rule in self._rules:
            action = rule.evaluate(d)
            if action is not None:
                # 检查覆盖
                if rule.name in self._overrides:
                    action = self._overrides[rule.name]
                matched.append((rule, action))

        if not matched:
            result = PolicyResult(action=Action.ALLOW, reason="无规则匹配，默认允许")
        else:
            # 最高优先级（最低 priority 值）的规则胜出
            top_rule, top_action = matched[0]
            result = PolicyResult(
                action=top_action,
                rule=top_rule,
                reason=top_rule.reason,
                details=f"规则: {top_rule.name} | 优先级: {top_rule.priority} | 严重性: {top_rule.severity.name}",
            )

        # 审计日志
        self._audit_log.append({
            "tool": ctx.tool_name,
            "command": ctx.command[:200],
            "action": result.action.name,
            "rule": result.rule.name if result.rule else "default",
            "reason": result.reason,
        })

        return result

    def evaluate_tool(self, tool_name: str, tool_args: Dict) -> PolicyResult:
        """快捷方法：评估工具调用"""
        ctx = PolicyContext(
            tool_name=tool_name,
            tool_args=tool_args,
            command=tool_args.get("command", ""),
            file_path=tool_args.get("path", ""),
            content=tool_args.get("content", ""),
        )
        return self.evaluate(ctx)

    def evaluate_command(self, command: str) -> PolicyResult:
        """快捷方法：评估 shell 命令"""
        ctx = PolicyContext(command=command, tool_name="terminal")
        return self.evaluate(ctx)

    def audit_log(self, limit: int = 20) -> List[Dict]:
        return self._audit_log[-limit:]

    def stats(self) -> Dict:
        total = len(self._rules)
        enabled = sum(1 for r in self._rules if r.enabled)
        by_action = {}
        for r in self._rules:
            by_action[r.action.name] = by_action.get(r.action.name, 0) + 1
        return {
            "total_rules": total,
            "enabled_rules": enabled,
            "by_action": by_action,
            "audit_entries": len(self._audit_log),
        }

    def list_rules(self, tag: str = "", enabled_only: bool = True) -> List[Rule]:
        rules = self._rules
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        if tag:
            rules = [r for r in rules if tag in r.tags]
        return rules

    def ask_user_approval(self, command: str, reason: str, severity: Severity) -> bool:
        """请求用户审批 — 用于 ASK 动作"""
        if severity in (Severity.CRITICAL, Severity.HIGH):
            # 危险操作：默认拒绝，需要明确确认
            if _console:
                _console.print(f"\n  [bold error]✗ 权限审批[/]")
                _console.print(f"  [error]{reason}[/]")
                _console.print(f"  [dim]命令: {command[:80]}[/]")
                if severity == Severity.CRITICAL:
                    _console.print(f"  [bold error]此操作可能导致不可逆的损害[/]")
            else:
                print(f"\n  ✗ 权限审批")
                print(f"  {reason}")
                print(f"  命令: {command[:80]}")
                if severity == Severity.CRITICAL:
                    print(f"  此操作可能导致不可逆的损害")
            try:
                answer = input(f"  \033[38;5;210m确认执行？[y/N]：\033[0m").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return False
            return answer == "y"
        else:
            # 中等风险：默认允许，需要明确拒绝
            if _console:
                _console.print(f"\n  [warning]⚠ 权限审批[/]")
                _console.print(f"  [warning]{reason}[/]")
                _console.print(f"  [dim]命令: {command[:80]}[/]")
            else:
                print(f"\n  ⚠ 权限审批")
                print(f"  {reason}")
                print(f"  命令: {command[:80]}")
            try:
                answer = input(f"  \033[38;5;223m是否继续？[Y/n]：\033[0m").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return False
            return answer != "n"

    def approve_tool_call(self, tool_name: str, args: Dict) -> bool:
        """审批工具调用 — 合并了 approval.py 的逻辑"""
        ctx = PolicyContext(
            tool_name=tool_name,
            tool_args=args,
            command=args.get("command", ""),
            file_path=args.get("path", ""),
            content=args.get("content", ""),
        )
        result = self.evaluate(ctx)

        if result.is_allowed:
            return True

        if result.is_denied:
            if _console:
                _console.print(f"\n  [bold error]✗ 策略拒绝[/]")
                _console.print(f"  [error]{result.reason}[/]")
            else:
                print(f"\n  ✗ 策略拒绝")
                print(f"  {result.reason}")
            return False

        if result.needs_approval:
            severity = result.rule.severity if result.rule else Severity.MEDIUM
            return self.ask_user_approval(
                command=ctx.command or f"{tool_name} → {args.get('path', '')}",
                reason=result.reason,
                severity=severity,
            )

        return True


# 全局单例
_engine: Optional[PolicyEngine] = None


def get_policy_engine() -> PolicyEngine:
    global _engine
    if _engine is None:
        _engine = PolicyEngine()
    return _engine
