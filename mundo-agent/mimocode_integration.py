"""蒙多 MiMo Code 集成 v2.1.0 — 将小米 MiMo Code 作为子 agent

集成自 https://github.com/XiaomiMiMo/MiMo-Code
CLI 命令: mimo (npm @mimo-ai/cli)
"""

import os
import subprocess
import shutil
from typing import Optional


class MiMoCodeAgent:
    """MiMo Code Agent 集成"""

    def __init__(self):
        self.cmd = shutil.which("mimo")

    def is_available(self) -> bool:
        return self.cmd is not None

    def get_version(self) -> str:
        if not self.is_available():
            return "N/A"
        try:
            result = subprocess.run(
                [self.cmd, "--version"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "unknown"

    def chat(self, prompt: str, workdir: Optional[str] = None,
             timeout: int = 60) -> str:
        if not self.is_available():
            return "[MiMo Code 未安装]"

        cmd = [self.cmd, "run", prompt]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=timeout, cwd=workdir,
            )
            output = result.stdout.strip()
            if result.returncode == 0 and output:
                return output
            # 有些情况下 returncode 非 0 但有输出
            if output:
                return output
            return f"[MiMo Code 退出码 {result.returncode}] {result.stderr.strip()[:500]}"
        except subprocess.TimeoutExpired:
            return f"[MiMo Code 超时 ({timeout}s)]"
        except Exception as e:
            return f"[MiMo Code 错误: {e}]"

    def get_info(self) -> dict:
        return {
            "name": "MiMo Code",
            "cmd": "mimo",
            "available": self.is_available(),
            "version": self.get_version() if self.is_available() else "N/A",
            "strengths": ["代码生成", "代码理解", "项目分析", "MiMo模型优化", "跨会话记忆"],
            "best_for": ["代码生成", "项目分析", "MiMo模型相关任务"],
        }
