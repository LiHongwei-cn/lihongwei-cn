"""蒙多终端执行工具 — 重构版

改进：
- 安全检查
- 超时保护
- 输出格式化
"""

import os
import subprocess
from typing import Dict

from .registry import register_tool, ToolParameter
from ..utils.errors import ToolError, ValidationError
from ..utils.logging import get_tool_logger

logger = get_tool_logger()

# 危险命令模式
DANGEROUS_PATTERNS = [
    "rm -rf /",
    "rm -rf /*",
    "mkfs",
    "dd if=",
    "> /dev/sda",
    "chmod 777 /",
    "shutdown",
    "reboot",
    "halt",
    "init 0",
    "init 6",
]


def _is_dangerous_command(cmd: str) -> bool:
    """检查命令是否危险"""
    cmd_lower = cmd.lower().strip()
    for pattern in DANGEROUS_PATTERNS:
        if pattern in cmd_lower:
            return True
    return False


def _truncate(text: str, limit: int = 8000) -> str:
    """智能截断文本"""
    if len(text) <= limit:
        return text
    head = text[:int(limit * 0.6)]
    tail = text[-int(limit * 0.3):]
    return f"{head}\n... ({len(text)} 字符，省略中间部分) ...\n{tail}"


@register_tool(
    name="terminal",
    description="执行 shell 命令。用于运行代码、安装包、git 操作、系统管理。返回 stdout/stderr。",
    parameters=[
        ToolParameter("command", "string", "要执行的 shell 命令", required=True),
        ToolParameter("workdir", "string", "工作目录（可选，默认当前目录）"),
        ToolParameter("timeout", "integer", "超时秒数（默认 120）", default=120),
    ]
)
def terminal(args: Dict) -> str:
    """执行终端命令"""
    cmd = args.get("command", "")
    if not cmd:
        raise ValidationError("缺少 command 参数", "command")

    # 安全检查
    if _is_dangerous_command(cmd):
        raise ToolError("terminal", f"拒绝执行危险命令: {cmd}")

    workdir = args.get("workdir") or os.getcwd()
    timeout = args.get("timeout", 120)

    try:
        logger.debug(f"执行命令: {cmd} (目录: {workdir}, 超时: {timeout}s)")

        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=workdir,
        )

        output = result.stdout

        if result.stderr:
            # stderr 截断到 2000 字符
            stderr = result.stderr[:2000]
            if len(result.stderr) > 2000:
                stderr += f"\n... ({len(result.stderr)} 字符，已截断)"
            output += f"\n[stderr]\n{stderr}"

        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
            stderr = result.stderr or ""

            # 提供有用的错误提示
            if "command not found" in stderr:
                output += "\n提示: 命令未找到，检查拼写或安装对应包"
            elif "Permission denied" in stderr:
                output += "\n提示: 权限不足，尝试加 sudo 或检查文件权限"
            elif "No such file" in stderr:
                output += "\n提示: 文件/目录不存在，检查路径"

        return _truncate(output or "(无输出)")

    except subprocess.TimeoutExpired:
        raise ToolError("terminal", f"命令执行超过 {timeout} 秒")
    except PermissionError:
        raise ToolError("terminal", "权限不足")
    except Exception as e:
        raise ToolError("terminal", f"{type(e).__name__}: {e}")