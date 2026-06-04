"""蒙多 Claude Code 集成 — 自动路由到 Anthropic 端点

Claude Code CLI 使用 ANTHROPIC_API_KEY + ANTHROPIC_BASE_URL。
蒙多根据当前 provider 自动设置，无需手动配置。
"""

import os
import shutil
import subprocess


class ClaudeCodeAgent:
    """Claude Code CLI 封装"""

    def __init__(self):
        self.cmd = shutil.which("claude")

    def is_available(self) -> bool:
        return self.cmd is not None

    def exec_full_power(self, prompt: str, workdir: str = None) -> str:
        """全力模式执行 Claude Code"""
        if not self.is_available():
            return "[Claude Code 未安装]"

        cmd = [self.cmd, "-p", prompt, "--dangerously-skip-permissions"]
        env = os.environ.copy()

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=600, cwd=workdir, env=env,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return f"[Claude Code 退出码 {result.returncode}] {result.stderr.strip()[:500]}"
        except subprocess.TimeoutExpired:
            return "[Claude Code 超时 (600s)]"
        except Exception as e:
            return f"[Claude Code 异常: {e}]"
