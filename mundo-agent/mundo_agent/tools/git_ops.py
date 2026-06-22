"""蒙多 Git 操作工具 — 重构版

改进：
- 统一错误处理
- 更多操作支持
- 安全检查
"""

import os
import subprocess
from typing import Dict

from .registry import register_tool, ToolParameter
from ..utils.errors import ToolError, ValidationError
from ..utils.logging import get_tool_logger

logger = get_tool_logger()


def _truncate(text: str, limit: int = 8000) -> str:
    """智能截断文本"""
    if len(text) <= limit:
        return text
    head = text[:int(limit * 0.6)]
    tail = text[-int(limit * 0.3):]
    return f"{head}\n... ({len(text)} 字符，省略中间部分) ...\n{tail}"


def _run_git(cmd: str, workdir: str, timeout: int = 30) -> str:
    """执行 Git 命令"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=workdir,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr[:1000]}"
        return _truncate(output or "(无输出)")
    except subprocess.TimeoutExpired:
        raise ToolError("git_operation", f"Git 命令超时 ({timeout}s)")
    except Exception as e:
        raise ToolError("git_operation", f"Git 操作失败: {e}")


@register_tool(
    name="git_operation",
    description="Git 操作工具。支持 status/diff/log/branch/commit/create_branch/create_worktree 等操作。",
    parameters=[
        ToolParameter("operation", "string", "Git 操作类型", required=True,
                     enum=["status", "diff", "diff_staged", "log", "branch",
                           "current_branch", "stash_list", "commit",
                           "create_branch", "create_worktree"]),
        ToolParameter("workdir", "string", "工作目录（默认当前目录）"),
        ToolParameter("message", "string", "提交信息（commit 操作需要）"),
        ToolParameter("branch_name", "string", "分支名称（create_branch/create_worktree 操作需要）"),
        ToolParameter("worktree_path", "string", "工作树路径（create_worktree 操作需要）"),
    ]
)
def git_operation(args: Dict) -> str:
    """执行 Git 操作"""
    operation = args.get("operation", "")
    if not operation:
        raise ValidationError("缺少 operation 参数", "operation")

    workdir = args.get("workdir") or os.getcwd()

    # 只读操作映射
    read_only_operations = {
        "status": "git status --short",
        "diff": "git diff",
        "diff_staged": "git diff --staged",
        "log": "git log --oneline -10",
        "branch": "git branch -a",
        "current_branch": "git rev-parse --abbrev-ref HEAD",
        "stash_list": "git stash list",
    }

    # 只读操作
    if operation in read_only_operations:
        cmd = read_only_operations[operation]
        return _run_git(cmd, workdir)

    # 写操作：commit
    elif operation == "commit":
        message = args.get("message", "")
        if not message:
            raise ValidationError("commit 操作需要 message 参数", "message")

        try:
            # 先添加所有更改
            subprocess.run("git add -A", shell=True, cwd=workdir, check=True)

            # 提交
            result = subprocess.run(
                f'git commit -m "{message}"',
                shell=True, capture_output=True, text=True, cwd=workdir,
            )

            if result.returncode != 0:
                raise ToolError("git_operation", f"提交失败: {result.stderr}")

            return f"✓ 已提交: {message}\n{result.stdout}"
        except ToolError:
            raise
        except Exception as e:
            raise ToolError("git_operation", f"提交失败: {e}")

    # 写操作：create_branch
    elif operation == "create_branch":
        branch_name = args.get("branch_name", "")
        if not branch_name:
            raise ValidationError("create_branch 操作需要 branch_name 参数", "branch_name")

        try:
            result = subprocess.run(
                f"git checkout -b {branch_name}",
                shell=True, capture_output=True, text=True, cwd=workdir,
            )

            if result.returncode != 0:
                raise ToolError("git_operation", f"创建分支失败: {result.stderr}")

            return f"✓ 已创建并切换到分支: {branch_name}\n{result.stdout}"
        except ToolError:
            raise
        except Exception as e:
            raise ToolError("git_operation", f"创建分支失败: {e}")

    # 写操作：create_worktree
    elif operation == "create_worktree":
        branch_name = args.get("branch_name", "")
        worktree_path = args.get("worktree_path", "")

        if not branch_name or not worktree_path:
            raise ValidationError(
                "create_worktree 需要 branch_name 和 worktree_path 参数",
                "branch_name" if not branch_name else "worktree_path"
            )

        try:
            # 创建新分支
            subprocess.run(
                f"git branch {branch_name}",
                shell=True, capture_output=True, text=True, cwd=workdir,
            )

            # 创建工作树
            result = subprocess.run(
                f"git worktree add {worktree_path} {branch_name}",
                shell=True, capture_output=True, text=True, cwd=workdir,
            )

            if result.returncode != 0:
                raise ToolError("git_operation", f"创建工作树失败: {result.stderr}")

            return f"✓ 已创建工作树: {worktree_path} (分支: {branch_name})\n{result.stdout}"
        except ToolError:
            raise
        except Exception as e:
            raise ToolError("git_operation", f"创建工作树失败: {e}")

    else:
        raise ToolError("git_operation", f"未知 Git 操作: {operation}")