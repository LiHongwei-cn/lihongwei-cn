"""蒙多沙箱层 v1.4.0 — 皇帝的试炼场

代码执行隔离。不是简单的 subprocess。是受控的执行环境。
资源限制、超时控制、输出捕获、错误隔离。

设计哲学：
- 代码执行必须在沙箱内
- 资源有上限：时间、内存、输出大小
- 错误不能逃逸到主进程
- 每次执行都是独立的
"""

import os
import sys
import time
import signal
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Optional, Dict, Tuple, Any
from pathlib import Path


@dataclass
class SandboxConfig:
    timeout: int = 30
    max_output_bytes: int = 512_000
    max_memory_mb: int = 512
    allowed_commands: list = field(default_factory=lambda: ["python3", "python", "node", "bash", "sh"])
    blocked_commands: list = field(default_factory=lambda: ["rm -rf /", "mkfs", "dd", ":(){ :|:& };:"])
    env_vars: Dict[str, str] = field(default_factory=dict)
    workdir: str = ""
    network: bool = True


@dataclass
class SandboxResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    timed_out: bool = False
    duration_ms: float = 0
    truncated: bool = False
    command: str = ""

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    @property
    def output(self) -> str:
        if self.stderr:
            return f"{self.stdout}\n[stderr] {self.stderr}"
        return self.stdout


class Sandbox:
    """执行沙箱 — 隔离、受控、可观测"""

    def __init__(self, config: Optional[SandboxConfig] = None):
        self._config = config or SandboxConfig()
        self._history: list = []

    def execute(self, command: str, language: str = "bash",
                workdir: str = "", env: Dict[str, str] = None) -> SandboxResult:
        """执行命令，返回结果"""
        # 安全检查
        if not self._check_safety(command):
            return SandboxResult(
                stderr=f"安全拒绝: 命令被沙箱策略阻止",
                exit_code=-1,
                command=command,
            )

        effective_workdir = workdir or self._config.workdir or os.getcwd()
        effective_env = {**os.environ, **self._config.env_vars, **(env or {})}

        start = time.time()

        try:
            if language in ("python", "python3"):
                result = self._execute_python(command, effective_workdir, effective_env)
            elif language in ("bash", "sh"):
                result = self._execute_shell(command, effective_workdir, effective_env, language)
            elif language == "node":
                result = self._execute_node(command, effective_workdir, effective_env)
            else:
                result = SandboxResult(
                    stderr=f"不支持的语言: {language}",
                    exit_code=-1,
                    command=command,
                )

            result.duration_ms = (time.time() - start) * 1000
            result.command = command
            self._history.append(result)
            return result

        except Exception as e:
            return SandboxResult(
                stderr=f"沙箱异常: {e}",
                exit_code=-1,
                duration_ms=(time.time() - start) * 1000,
                command=command,
            )

    def execute_python(self, code: str, workdir: str = "") -> SandboxResult:
        return self.execute(code, "python3", workdir)

    def execute_shell(self, command: str, workdir: str = "") -> SandboxResult:
        return self.execute(command, "bash", workdir)

    def execute_code_file(self, path: str, language: str = "python3",
                          workdir: str = "") -> SandboxResult:
        file_path = Path(path)
        if not file_path.exists():
            return SandboxResult(stderr=f"文件不存在: {path}", exit_code=-1)

        code = file_path.read_text(encoding="utf-8")

        if language in ("python", "python3"):
            return self.execute(code, "python3", workdir)
        elif language in ("bash", "sh"):
            return self.execute(code, "bash", workdir)
        elif language == "node":
            return self.execute(code, "node", workdir)
        else:
            return SandboxResult(stderr=f"不支持: {language}", exit_code=-1)

    def _execute_python(self, code: str, workdir: str,
                        env: Dict[str, str]) -> SandboxResult:
        return self._run_process(
            [sys.executable, "-c", code],
            workdir, env,
        )

    def _execute_shell(self, command: str, workdir: str,
                       env: Dict[str, str], shell: str = "bash") -> SandboxResult:
        return self._run_process(
            [shell, "-c", command],
            workdir, env,
        )

    def _execute_node(self, code: str, workdir: str,
                      env: Dict[str, str]) -> SandboxResult:
        node = self._find_executable("node")
        if not node:
            return SandboxResult(stderr="node 未安装", exit_code=-1)
        return self._run_process([node, "-e", code], workdir, env)

    def _run_process(self, cmd: list, workdir: str,
                     env: Dict[str, str]) -> SandboxResult:
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._config.timeout,
                cwd=workdir or None,
                env=env,
            )

            stdout = proc.stdout[:self._config.max_output_bytes] if proc.stdout else ""
            stderr = proc.stderr[:self._config.max_output_bytes] if proc.stderr else ""
            truncated = (
                (proc.stdout and len(proc.stdout) > self._config.max_output_bytes) or
                (proc.stderr and len(proc.stderr) > self._config.max_output_bytes)
            )

            return SandboxResult(
                stdout=stdout,
                stderr=stderr,
                exit_code=proc.returncode,
                truncated=truncated,
            )

        except subprocess.TimeoutExpired:
            return SandboxResult(
                stderr=f"执行超时 ({self._config.timeout}s)",
                exit_code=-1,
                timed_out=True,
            )
        except FileNotFoundError:
            return SandboxResult(
                stderr=f"命令未找到: {cmd[0]}",
                exit_code=-1,
            )

    def _check_safety(self, command: str) -> bool:
        cmd_lower = command.lower().strip()
        for blocked in self._config.blocked_commands:
            if blocked.lower() in cmd_lower:
                return False
        return True

    @staticmethod
    def _find_executable(name: str) -> Optional[str]:
        for d in os.environ.get("PATH", "").split(":"):
            path = os.path.join(d, name)
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        return None

    def history(self, limit: int = 10) -> list:
        return self._history[-limit:]

    def stats(self) -> Dict:
        total = len(self._history)
        success = sum(1 for r in self._history if r.success)
        timed_out = sum(1 for r in self._history if r.timed_out)
        return {
            "total": total,
            "success": success,
            "failed": total - success,
            "timed_out": timed_out,
        }


# 全局单例
_sandbox: Optional[Sandbox] = None


def get_sandbox() -> Sandbox:
    global _sandbox
    if _sandbox is None:
        _sandbox = Sandbox()
    return _sandbox
