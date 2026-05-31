"""蒙多的权限审批系统 — Claude Code 风格 yes/no"""

import sys
import re
from typing import Tuple

# 颜色
G = "\033[38;5;178m"
R = "\033[0m"
D = "\033[2m"
A = "\033[38;5;136m"
OK = "\033[38;5;65m"
ERR = "\033[38;5;131m"
WARN = "\033[38;5;136m"
CYAN = "\033[38;5;87m"

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

# 需要确认的文件路径
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
    """分类命令风险等级。返回 (level, reason)。
    level: safe / caution / danger
    """
    cmd_lower = command.lower().strip()

    # 检查危险模式
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_lower):
            return "danger", reason

    # 检查敏感路径（write_file / read_file 场景）
    for pattern, reason in SENSITIVE_PATHS:
        if re.search(pattern, command):
            return "caution", reason

    # 检查是否写入系统目录
    if re.search(r"^/(?:bin|sbin|usr|etc|var|opt|lib)", command):
        return "caution", "写入系统目录"

    return "safe", ""


def classify_file_op(path: str, op: str) -> Tuple[str, str]:
    """分类文件操作风险。"""
    for pattern, reason in SENSITIVE_PATHS:
        if re.search(pattern, path):
            return "caution", f"{op} {reason}: {path}"

    # 写入 home 以外的目录（允许 /tmp）
    home = str(__import__("pathlib").Path.home())
    if not path.startswith(home) and path.startswith("/"):
        if path.startswith(("/tmp", "/var/tmp")):
            return "safe", ""
        return "caution", f"{op} 系统目录: {path}"

    return "safe", ""


def ask_approval(command: str, level: str, reason: str) -> bool:
    """显示审批提示，等待用户输入。返回是否批准。"""

    if level == "safe":
        return True

    color = WARN if level == "caution" else ERR
    icon = "⚠" if level == "caution" else "✗"

    print(f"\n  {color}{icon} 权限审批{R}")
    print(f"  {D}{'─' * 50}{R}")
    print(f"  {color}{reason}{R}")
    print(f"  {D}命令: {command[:80]}{R}")
    print(f"  {D}{'─' * 50}{R}")

    if level == "danger":
        print(f"  {ERR}此操作可能导致不可逆的损害{R}")
        prompt = f"  {ERR}确认执行？[y/N]：{R}"
    else:
        prompt = f"  {WARN}是否继续？[Y/n]：{R}"

    try:
        answer = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print(f"\n  {D}已取消{R}")
        return False

    if level == "danger":
        return answer == "y"
    else:
        return answer != "n"


def approve_tool_call(tool_name: str, args: dict) -> bool:
    """审批工具调用。返回是否批准。"""
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
