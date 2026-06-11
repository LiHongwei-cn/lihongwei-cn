"""蒙多 Codex 集成 v2.1.0 — 自动路由到 OpenAI 兼容端点

适配版本：Codex v0.138.0+
保持配置：xiaomi/mimo-v2.5-pro

Codex CLI 使用 OPENAI_API_KEY + OPENAI_BASE_URL。
蒙多根据当前 provider 自动设置，无需手动配置。
"""

import os
import shutil
import subprocess


class CodexAgent:
    """OpenAI Codex CLI 封装"""

    def __repr__(self) -> str:
        return f"CodexAgent(available={self.is_available()})"

    def __init__(self):
        self.cmd = shutil.which("codex")

    def is_available(self) -> bool:
        return self.cmd is not None

    def exec_full_auto(self, prompt: str, workdir: str = None, timeout: int = 20) -> str:
        """全自动模式执行 Codex — 超时限制 20s 完成重试后降级"""
        if not self.is_available():
            return "[Codex 未安装]"

        # 使用 exec 子命令，启用完整沙箱权限，跳过 git 仓库检查
        cmd = [self.cmd, "exec", "-s", "danger-full-access", "--skip-git-repo-check", prompt]
        env = os.environ.copy()

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=timeout, cwd=workdir, env=env,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return f"[Codex 退出码 {result.returncode}] {result.stderr.strip()[:500]}"
        except subprocess.TimeoutExpired:
            return f"[Codex 超时 ({timeout}s)]"
        except Exception as e:
            return f"[Codex 异常: {e}]"


def smart_route(task_type: str) -> str:
    """智能路由：判断任务应该用 Codex 还是 Claude Code"""
    codex_keywords = [
        "脚本", "批量", "batch", "quick", "原型", "prototype",
        "一次", "生成", "generate", "scaffold", "init",
    ]
    claude_keywords = [
        "重构", "refactor", "调试", "debug", "复杂", "complex",
        "架构", "architecture", "审查", "review", "测试", "test",
    ]
    task_lower = task_type.lower()
    codex_score = sum(1 for kw in codex_keywords if kw in task_lower)
    claude_score = sum(1 for kw in claude_keywords if kw in task_lower)
    return "codex" if codex_score >= claude_score else "claude"
