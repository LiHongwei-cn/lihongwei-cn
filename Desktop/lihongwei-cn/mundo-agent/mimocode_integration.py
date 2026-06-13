"""蒙多 MiMo Code 集成 v1.1 — MiMo Code CLI 封装

适配版本：MiMo Code v0.1.0+
MiMo Code 是小米的代码 AI 工具，中文优化。
"""

import os
import shutil
import subprocess


class MiMoCodeAgent:
    """MiMo Code CLI 封装"""

    def __repr__(self) -> str:
        return f"MiMoCodeAgent(available={self.is_available()})"

    def __init__(self):
        self.cmd = shutil.which("mimo")

    def is_available(self) -> bool:
        return self.cmd is not None

    def chat(self, prompt: str, workdir: str = None, timeout: int = 120) -> str:
        """单次对话模式 — 使用 mimo run"""
        if not self.is_available():
            return "[MiMo Code 未安装]"

        # 先检查是否有配置凭证
        try:
            check = subprocess.run(
                [self.cmd, "providers", "list"],
                capture_output=True, text=True, timeout=10,
            )
            if "0 credentials" in check.stdout:
                return "[MiMo Code 未配置凭证，运行 mimo providers login 配置]"
        except Exception:
            pass

        cmd = [self.cmd, "run", prompt]
        env = os.environ.copy()

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=timeout, cwd=workdir, env=env,
            )
            output = result.stdout.strip()
            if result.returncode == 0 and output:
                return output
            if output:
                return output
            error = result.stderr.strip()[:500]
            return f"[MiMo Code 退出码 {result.returncode}] {error}"
        except subprocess.TimeoutExpired:
            return f"[MiMo Code 超时 ({timeout}s)]"
        except Exception as e:
            return f"[MiMo Code 异常: {e}]"
