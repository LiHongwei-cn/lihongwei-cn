"""蒙多的权限审批系统 v2.0.9 — Rich 渲染"""

import sys
import re
from pathlib import Path
from typing import Tuple

from rich.console import Console
from rich.panel import Panel

console = Console(highlight=False, force_terminal=True)

# 危险命令模式
DANGEROUS_PATTERNS = [
    (r"\brm\s+(-[rf]+\s+|.*--no-preserve-root)", "删除文件（递归/强制）"),
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f", "递归强制删除"),
    (r"\bmkfs\b", "格式化磁盘"),
    (r"\bdd\s+.*of=/dev/", "写入磁盘设备"),
    (r"\bchmod\s+777\b", "设置 777 权限"),
    (r"\bchown\s+.*root", "变更为 root 所有"),
    (r"\bshutdown\b|\breboot\b|\binit\s+0\b", "关机/重启"),
    (r"\bkill\s+-9\s+-1\b", "杀死所有进程"),
    (r"\bgit\s+push\s+.*--force", "Git 强制推送"),
    (r"\bgit\s+reset\s+--hard", "Git 硬重置"),
    (r"\bgit\s+clean\s+-[a-zA-Z]*f", "Git 清理未跟踪文件"),
    (r"\bcurl\s+.*\|\s*(ba)?sh", "管道执行远程脚本"),
    (r"\bwget\s+.*\|\s*(ba)?sh", "管道执行远程脚本"),
    (r"\bsudo\b", "需要 sudo 权限"),
    (r"\b(npm|pip)\s+(install|uninstall)\s+-g", "全局安装/卸载包"),
    (r"\bdocker\s+(rm|stop|kill)\b", "Docker 容器操作"),
    (r"\bDROP\s+TABLE\b", "删除数据库表"),
    (r"\bDELETE\s+FROM\b.*WHERE", "删除数据库记录"),
]

SENSITIVE_PATHS = [
    (r"/etc/", "系统配置文件"),
    (r"/usr/", "系统程序目录"),
    (r"/var/", "系统变量目录"),
    (r"~/\.ssh/", "SSH 密钥目录"),
    (r"~/\.gnupg/", "GPG 密钥目录"),
    (r"~/\.aws/", "AWS 凭证目录"),
    (r"\.env$", "环境变量文件"),
    (r"\.pem$", "证书/密钥文件"),
    (r"\.key$", "密钥文件"),
    (r"id_rsa|id_ed25519", "SSH 私钥"),
]


def classify_command(command: str) -> Tuple[str, str]:
    cmd_lower = command.lower().strip()
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_lower):
            return "danger", reason
    for pattern, reason in SENSITIVE_PATHS:
        if re.search(pattern, command):
            return "caution", reason
    if re.search(r"^/(?:bin|sbin|usr|etc|var|opt|lib)", command):
        return "caution", "写入系统目录"
    return "safe", ""


def classify_file_op(path: str, op: str) -> Tuple[str, str]:
    for pattern, reason in SENSITIVE_PATHS:
        if re.search(pattern, path):
            return "caution", f"{op} {reason}: {path}"
    home = str(Path.home())
    if not path.startswith(home) and path.startswith("/"):
        if path.startswith(("/tmp", "/var/tmp")):
            return "safe", ""
        return "caution", f"{op} 系统目录: {path}"
    return "safe", ""


def ask_approval(command: str, level: str, reason: str) -> bool:
    if level == "safe":
        return True

    if level == "danger":
        console.print(f"\n  [bold error]✗ 权限审批[/]")
        console.print(f"  [error]{reason}[/]")
        console.print(f"  [dim]命令: {command[:80]}[/]")
        console.print(f"  [bold error]此操作可能导致不可逆的损害[/]")
        try:
            answer = input(f"  \033[38;5;210m确认执行？[y/N]：\033[0m").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        return answer == "y"
    else:
        console.print(f"\n  [warning]⚠ 权限审批[/]")
        console.print(f"  [warning]{reason}[/]")
        console.print(f"  [dim]命令: {command[:80]}[/]")
        try:
            answer = input(f"  \033[38;5;223m是否继续？[Y/n]：\033[0m").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        return answer != "n"


def approve_tool_call(tool_name: str, args: dict) -> bool:
    if tool_name == "terminal":
        cmd = args.get("command", "")
        level, reason = classify_command(cmd)
        return ask_approval(cmd, level, reason)

    if tool_name == "write_file":
        path = args.get("path", "")
        level, reason = classify_file_op(path, "写入")
        if level != "safe":
            return ask_approval(f"write_file → {path}", level, reason)

    if tool_name == "read_file":
        path = args.get("path", "")
        level, reason = classify_file_op(path, "读取")
        if level != "safe":
            return ask_approval(f"read_file → {path}", level, reason)

    return True
