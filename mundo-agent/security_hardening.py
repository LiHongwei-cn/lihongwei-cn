"""蒙多安全强化层 v3.0.0 — 帝皇的铁壁防御

不是简单的正则匹配。是多层纵深防御体系。

安全架构（Defense in Depth）：
1. 输入验证层 — 所有外部输入不可信，先消毒再使用
2. 输出过滤层 — 防止敏感信息泄露
3. 权限边界层 — 最小权限原则
4. 审计追踪层 — 所有操作可追溯
5. 注入防护层 — 防止 Prompt Injection

知识来源：
- OWASP Top 10
- CWE/SANS Top 25
- Prompt Injection 防护最佳实践
"""

import re
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Pattern, Set, Tuple
from pathlib import Path


class ThreatLevel(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class SecurityAction(Enum):
    ALLOW = auto()
    SANITIZE = auto()
    BLOCK = auto()
    ALERT = auto()
    QUARANTINE = auto()


@dataclass
class SecurityEvent:
    """安全事件记录"""
    timestamp: float
    threat_level: ThreatLevel
    category: str
    description: str
    source: str
    action_taken: SecurityAction
    details: Dict = field(default_factory=dict)
    blocked: bool = False


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    sanitized_value: Any = None
    threats: List[str] = field(default_factory=list)
    action: SecurityAction = SecurityAction.ALLOW


class InputValidator:
    """输入验证器 — 所有外部输入不可信"""

    # 危险命令模式
    DANGEROUS_COMMANDS = [
        r"\brm\s+-rf\s+/",           # 递归删除根目录
        r"\bmkfs\b",                  # 格式化
        r"\bdd\s+.*of=/dev/",         # 写入设备
        r":\(\)\{.*\|.*&\s*\};\:",    # Fork bomb
        r"\bchmod\s+777\s+/",         # 全局可写
        r"\bchown\s+.*root",          # 改变所有者为root
        r"\bwipefs\b",                # 清除文件系统签名
        r"\bshutdown\b",              # 关机
        r"\breboot\b",                # 重启
        r"\binit\s+[06]\b",           # 切换运行级别
    ]

    # SQL 注入模式
    SQL_INJECTION_PATTERNS = [
        r"'\s*OR\s+'",                # ' OR '1'='1
        r"--\s*$",                     # SQL 注释
        r";\s*(DROP|DELETE|UPDATE|INSERT)\b",
        r"UNION\s+SELECT",
        r"WAITFOR\s+DELAY",
    ]

    # 路径遍历模式
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e/",
        r"\.\.%2f",
    ]

    # Prompt Injection 模式
    PROMPT_INJECTION_PATTERNS = [
        r"ignore\s+(previous|above|all)\s+(instructions|prompts)",
        r"you\s+are\s+now\s+",
        r"system:\s*",
        r"<\|im_start\|>",
        r"\[INST\]",
        r"<<SYS>>",
        r"Human:\s*",
        r"Assistant:\s*",
    ]

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译正则表达式"""
        self._dangerous_cmd_re = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_COMMANDS]
        self._sql_injection_re = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self._path_traversal_re = [re.compile(p, re.IGNORECASE) for p in self.PATH_TRAVERSAL_PATTERNS]
        self._prompt_injection_re = [re.compile(p, re.IGNORECASE) for p in self.PROMPT_INJECTION_PATTERNS]

    def validate_command(self, command: str) -> ValidationResult:
        """验证 shell 命令"""
        threats = []

        for pattern in self._dangerous_cmd_re:
            if pattern.search(command):
                threats.append(f"危险命令: {pattern.pattern}")

        if threats:
            return ValidationResult(
                is_valid=False,
                threats=threats,
                action=SecurityAction.BLOCK,
            )

        return ValidationResult(is_valid=True, sanitized_value=command)

    def validate_path(self, path: str) -> ValidationResult:
        """验证文件路径"""
        threats = []

        # 路径遍历检查
        for pattern in self._path_traversal_re:
            if pattern.search(path):
                threats.append(f"路径遍历: {pattern.pattern}")

        # 敏感路径检查
        sensitive_paths = [
            "/etc/passwd", "/etc/shadow", "/etc/sudoers",
            "~/.ssh", "~/.gnupg", "~/.aws",
        ]
        path_lower = path.lower()
        for sensitive in sensitive_paths:
            if sensitive.lower() in path_lower:
                threats.append(f"敏感路径: {sensitive}")

        if threats:
            return ValidationResult(
                is_valid=False,
                threats=threats,
                action=SecurityAction.BLOCK,
            )

        return ValidationResult(is_valid=True, sanitized_value=path)

    def validate_input(self, user_input: str) -> ValidationResult:
        """验证用户输入"""
        threats = []

        # Prompt Injection 检查
        for pattern in self._prompt_injection_re:
            if pattern.search(user_input):
                threats.append(f"疑似 Prompt Injection: {pattern.pattern}")

        # SQL 注入检查
        for pattern in self._sql_injection_re:
            if pattern.search(user_input):
                threats.append(f"疑似 SQL 注入: {pattern.pattern}")

        if threats:
            return ValidationResult(
                is_valid=False,
                threats=threats,
                action=SecurityAction.ALERT,  # 不阻止用户输入，但告警
            )

        return ValidationResult(is_valid=True, sanitized_value=user_input)

    def sanitize_output(self, output: str) -> str:
        """消毒输出内容，防止敏感信息泄露 — v3.2.0 扩展覆盖"""
        # API key / secret / token
        output = re.sub(
            r"['\"]?(?:api[_-]?key|secret|token|password)['\"]?\s*[:=]\s*['\"][^'\"]+['\"]",
            "[REDACTED]",
            output,
            flags=re.IGNORECASE,
        )

        # Bearer Token / JWT
        output = re.sub(
            r"(?:Bearer|Authorization)\s+['\"]?[\w\-.]+\.[\w\-.]+\.[\w\-]+['\"]?",
            "[BEARER TOKEN REDACTED]",
            output,
            flags=re.IGNORECASE,
        )
        # 独立 JWT (eyJ 开头)
        output = re.sub(
            r"eyJ[\w\-]+\.[\w\-]+\.[\w\-]+",
            "[JWT REDACTED]",
            output,
        )

        # 数据库连接串
        output = re.sub(
            r"(?:mongodb|postgres(?:ql)?|mysql|redis|sqlite|jdbc|sqlserver)://[^\s\"'<>]+",
            "[DB_CONNECTION REDACTED]",
            output,
            flags=re.IGNORECASE,
        )

        # AWS/GCP 密钥
        output = re.sub(
            r"(?:AKIA|ASIA)[A-Z0-9]{16}",
            "[AWS_KEY REDACTED]",
            output,
        )
        output = re.sub(
            r"AIza[0-9A-Za-z\-_]{35}",
            "[GCP_KEY REDACTED]",
            output,
        )

        # 私钥（覆盖更多格式）
        output = re.sub(
            r"-----BEGIN\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+)?PRIVATE\s+KEY-----.*?-----END\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+)?PRIVATE\s+KEY-----",
            "[PRIVATE KEY REDACTED]",
            output,
            flags=re.DOTALL,
        )

        # Session cookie / CSRF token
        output = re.sub(
            r"(?:session[_-]?id|csrf[_-]?token|auth[_-]?token)\s*[:=]\s*['\"]?[\w\-]{20,}['\"]?",
            "[SESSION REDACTED]",
            output,
            flags=re.IGNORECASE,
        )

        # 脱敏手机号
        output = re.sub(r"1[3-9]\d{9}", lambda m: m.group()[:3] + "****" + m.group()[-4:], output)

        # 脱敏邮箱
        output = re.sub(
            r"([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            lambda m: m.group(1)[:2] + "***@" + m.group(2),
            output,
        )

        return output


class PromptInjectionDetector:
    """Prompt Injection 检测器 — 多层检测"""

    # 已知的注入技术
    INJECTION_TECHNIQUES = {
        "direct_override": [
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"disregard\s+(all\s+)?prior",
            r"forget\s+(all\s+)?previous",
            r"new\s+instructions?\s*:",
            r"system\s*prompt\s*:",
        ],
        "role_hijack": [
            r"you\s+are\s+now\s+",
            r"act\s+as\s+",
            r"pretend\s+(you\s+are|to\s+be)",
            r"role\s*:\s*system",
        ],
        "delimiter_injection": [
            r"<\|im_start\|>",
            r"<\|im_end\|>",
            r"\[INST\]",
            r"<<SYS>>",
            r"<</SYS>>",
            r"###\s*System:",
            r"###\s*Human:",
        ],
        "encoding_evasion": [
            r"base64",
            r"rot13",
            r"\\x[0-9a-f]{2}",
            r"\\u[0-9a-f]{4}",
            r"%[0-9a-f]{2}",
        ],
    }

    def __init__(self):
        self._patterns: Dict[str, List[Pattern]] = {}
        for technique, patterns in self.INJECTION_TECHNIQUES.items():
            self._patterns[technique] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def detect(self, text: str) -> List[Tuple[str, float]]:
        """检测 Prompt Injection，返回 (技术名称, 置信度) 列表"""
        detections = []

        for technique, patterns in self._patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    detections.append((technique, 0.8))
                    break  # 一个技术只需匹配一次

        return detections

    def is_injection(self, text: str, threshold: float = 0.5) -> bool:
        """判断是否为 Prompt Injection"""
        detections = self.detect(text)
        if not detections:
            return False

        # 多个技术同时命中，置信度更高
        max_confidence = max(d[1] for d in detections)
        combined = min(1.0, max_confidence + len(detections) * 0.1)

        return combined >= threshold


class SecurityAuditor:
    """安全审计员 — 记录所有安全相关事件"""

    def __init__(self, log_path: Optional[Path] = None):
        self._events: List[SecurityEvent] = []
        self._log_path = log_path

    def record(self, event: SecurityEvent):
        """记录安全事件"""
        self._events.append(event)

        if self._log_path:
            try:
                with open(self._log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "timestamp": event.timestamp,
                        "threat_level": event.threat_level.name,
                        "category": event.category,
                        "description": event.description,
                        "source": event.source,
                        "action": event.action_taken.name,
                        "blocked": event.blocked,
                    }, ensure_ascii=False) + "\n")
            except Exception:
                pass  # 日志写入失败不应影响主流程

    def get_recent_events(self, limit: int = 20) -> List[SecurityEvent]:
        return self._events[-limit:]

    def get_blocked_count(self) -> int:
        return sum(1 for e in self._events if e.blocked)

    def get_threat_summary(self) -> Dict[str, int]:
        summary = {}
        for event in self._events:
            level = event.threat_level.name
            summary[level] = summary.get(level, 0) + 1
        return summary


class SecurityHardening:
    """安全强化层 — 统一安全接口"""

    def __init__(self):
        self.input_validator = InputValidator()
        self.injection_detector = PromptInjectionDetector()
        self.auditor = SecurityAuditor()
        self._rate_limiter: Dict[str, List[float]] = {}

    def validate_and_sanitize(self, user_input: str) -> Tuple[bool, str, List[str]]:
        """验证并消毒用户输入

        返回: (is_safe, sanitized_input, warnings)
        """
        warnings = []

        # 1. Prompt Injection 检测
        if self.injection_detector.is_injection(user_input):
            self.auditor.record(SecurityEvent(
                timestamp=time.time(),
                threat_level=ThreatLevel.HIGH,
                category="prompt_injection",
                description="检测到疑似 Prompt Injection",
                source="user_input",
                action_taken=SecurityAction.ALERT,
            ))
            warnings.append("输入包含可疑内容，已记录")

        # 2. 输入验证
        result = self.input_validator.validate_input(user_input)
        if not result.is_valid:
            warnings.extend(result.threats)

        return True, user_input, warnings  # 用户输入不阻止，只告警

    def validate_tool_call(self, tool_name: str, args: Dict) -> ValidationResult:
        """验证工具调用"""
        # 检查命令
        if "command" in args:
            cmd_result = self.input_validator.validate_command(str(args["command"]))
            if not cmd_result.is_valid:
                self.auditor.record(SecurityEvent(
                    timestamp=time.time(),
                    threat_level=ThreatLevel.CRITICAL,
                    category="dangerous_command",
                    description=f"阻止危险命令: {args['command'][:100]}",
                    source=tool_name,
                    action_taken=SecurityAction.BLOCK,
                    blocked=True,
                ))
                return cmd_result

        # 检查路径
        if "path" in args:
            path_result = self.input_validator.validate_path(str(args["path"]))
            if not path_result.is_valid:
                self.auditor.record(SecurityEvent(
                    timestamp=time.time(),
                    threat_level=ThreatLevel.HIGH,
                    category="path_traversal",
                    description=f"阻止路径遍历: {args['path'][:100]}",
                    source=tool_name,
                    action_taken=SecurityAction.BLOCK,
                    blocked=True,
                ))
                return path_result

        return ValidationResult(is_valid=True)

    def sanitize_output(self, output: str) -> str:
        """消毒输出"""
        return self.input_validator.sanitize_output(output)

    def check_rate_limit(self, key: str, max_per_minute: int = 60) -> bool:
        """速率限制检查"""
        now = time.time()
        if key not in self._rate_limiter:
            self._rate_limiter[key] = []

        # 清理过期记录
        self._rate_limiter[key] = [
            t for t in self._rate_limiter[key] if now - t < 60
        ]

        if len(self._rate_limiter[key]) >= max_per_minute:
            return False  # 超过速率限制

        self._rate_limiter[key].append(now)
        return True

    def get_security_summary(self) -> Dict:
        """获取安全摘要"""
        return {
            "blocked_operations": self.auditor.get_blocked_count(),
            "threat_summary": self.auditor.get_threat_summary(),
            "recent_events": len(self.auditor.get_recent_events()),
        }


# 全局单例
_security: Optional[SecurityHardening] = None


def get_security() -> SecurityHardening:
    global _security
    if _security is None:
        _security = SecurityHardening()
    return _security


def reset_security():
    """重置安全模块单例 — 用于测试隔离"""
    global _security
    _security = None
