"""蒙多 Claude Code 深度集成 v24.8 — Claude Code CLI 全能力封装

能力：
- 一次性任务执行（claude -p）
- 后台长任务（claude -p + background）
- 多文件复杂变更（--max-turns 25）
- 代码审查（--agent reviewer）
- 自定义 Agent 调用
- 流式输出（--output-format stream-json）
- 结构化输出（--json-schema）
- 会话管理（--continue / --session-id）
"""

import os
import shutil
import subprocess
import json
from typing import Dict, List, Optional


CLAUDE_CMD = shutil.which("claude")


def _run_claude(
    args: List[str],
    timeout: int = 600,
    workdir: Optional[str] = None,
    background: bool = False,
) -> str:
    if not CLAUDE_CMD:
        return "[Claude Code 未安装]"

    cmd = [CLAUDE_CMD] + args

    if background:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=workdir,
        )
        return f"[Claude Code 后台启动 PID={proc.pid}]"

    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir,
        )
        output = r.stdout.strip()
        if r.returncode != 0 and r.stderr.strip():
            output += f"\n[stderr] {r.stderr.strip()}"
        return output or "[Claude Code 无输出]"
    except subprocess.TimeoutExpired:
        return f"[Claude Code 超时 ({timeout}s)]"
    except FileNotFoundError:
        return "[Claude Code 未安装]"
    except Exception as e:
        return f"[Claude Code 错误: {e}]"


class ClaudeCodeAgent:
    """Claude Code CLI 深度集成"""

    def __init__(self):
        self.available = CLAUDE_CMD is not None
        self.cmd = CLAUDE_CMD

    def is_available(self) -> bool:
        return self.available

    def exec_one_shot(
        self,
        prompt: str,
        workdir: Optional[str] = None,
        model: Optional[str] = None,
        max_turns: int = 10,
        timeout: int = 600,
    ) -> str:
        args = ["-p", prompt, "--max-turns", str(max_turns)]
        if model:
            args += ["--model", model]
        return _run_claude(args, timeout=timeout, workdir=workdir)

    def exec_full_power(
        self,
        prompt: str,
        workdir: Optional[str] = None,
        model: Optional[str] = None,
        max_turns: int = 25,
        timeout: int = 900,
    ) -> str:
        args = [
            "-p", prompt,
            "--max-turns", str(max_turns),
            "--dangerously-skip-permissions",
        ]
        if model:
            args += ["--model", model]
        return _run_claude(args, timeout=timeout, workdir=workdir)

    def exec_background(
        self,
        prompt: str,
        workdir: Optional[str] = None,
        model: Optional[str] = None,
        max_turns: int = 25,
    ) -> str:
        args = [
            "-p", prompt,
            "--max-turns", str(max_turns),
            "--dangerously-skip-permissions",
        ]
        if model:
            args += ["--model", model]
        return _run_claude(args, workdir=workdir, background=True)

    def exec_with_agent(
        self,
        prompt: str,
        agent: str,
        workdir: Optional[str] = None,
        timeout: int = 600,
    ) -> str:
        args = ["-p", prompt, "--agent", agent]
        return _run_claude(args, timeout=timeout, workdir=workdir)

    def exec_structured(
        self,
        prompt: str,
        json_schema: Dict,
        workdir: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 600,
    ) -> str:
        args = [
            "-p", prompt,
            "--output-format", "json",
            "--json-schema", json.dumps(json_schema),
        ]
        if model:
            args += ["--model", model]
        return _run_claude(args, timeout=timeout, workdir=workdir)

    def exec_continue(
        self,
        prompt: str,
        workdir: Optional[str] = None,
        timeout: int = 600,
    ) -> str:
        args = ["-p", prompt, "--continue"]
        return _run_claude(args, timeout=timeout, workdir=workdir)

    def exec_with_effort(
        self,
        prompt: str,
        effort: str = "high",
        workdir: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 600,
    ) -> str:
        args = ["-p", prompt, "--effort", effort]
        if model:
            args += ["--model", model]
        return _run_claude(args, timeout=timeout, workdir=workdir)

    def exec_with_system_prompt(
        self,
        prompt: str,
        system_prompt: str,
        workdir: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 600,
    ) -> str:
        args = [
            "-p", prompt,
            "--append-system-prompt", system_prompt,
        ]
        if model:
            args += ["--model", model]
        return _run_claude(args, timeout=timeout, workdir=workdir)

    def exec_with_tools(
        self,
        prompt: str,
        allowed_tools: List[str],
        workdir: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 600,
    ) -> str:
        args = ["-p", prompt, "--allowedTools"] + allowed_tools
        if model:
            args += ["--model", model]
        return _run_claude(args, timeout=timeout, workdir=workdir)

    def multi_file_edit(
        self,
        prompt: str,
        workdir: Optional[str] = None,
        model: Optional[str] = None,
        max_turns: int = 25,
        timeout: int = 900,
    ) -> str:
        return self.exec_full_power(
            prompt, workdir=workdir, model=model,
            max_turns=max_turns, timeout=timeout,
        )

    def refactor(
        self,
        prompt: str,
        workdir: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 900,
    ) -> str:
        system = (
            "You are a code refactoring expert. "
            "Follow these principles: DRY, YAGNI, KISS. "
            "Preserve behavior. Add tests before refactoring. "
            "Make small, incremental changes with commits."
        )
        return self.exec_with_system_prompt(
            prompt, system, workdir=workdir, model=model, timeout=timeout,
        )

    def debug(
        self,
        prompt: str,
        workdir: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 600,
    ) -> str:
        system = (
            "You are a systematic debugger. "
            "ALWAYS find root cause before attempting fixes. "
            "Read error messages carefully. Check recent changes. "
            "Write a failing test that reproduces the bug. "
            "Fix the root cause, not the symptom."
        )
        return self.exec_with_system_prompt(
            prompt, system, workdir=workdir, model=model, timeout=timeout,
        )


def get_claude_agent() -> Optional[ClaudeCodeAgent]:
    agent = ClaudeCodeAgent()
    return agent if agent.is_available() else None
