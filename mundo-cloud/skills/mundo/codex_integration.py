"""蒙多 Codex 深度集成 v24.9 — OpenAI Codex CLI 全能力封装（MiMo v2.5 Pro 驱动）

能力：
- 一次性任务执行（codex exec）
- 后台长任务（codex exec --full-auto + background）
- PR 审查（codex review）
- 并行 worktree 分发（多 issue 并行修复）
- 智能路由（Claude Code vs Codex 自动选择）
"""

import os
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional


CODEX_CMD = shutil.which("codex")
DEFAULT_MODEL = "mimo-v2.5-pro"  # CC Switch 配置的默认模型


def _run_codex(
    args: List[str],
    timeout: int = 600,
    workdir: Optional[str] = None,
    background: bool = False,
) -> str:
    if not CODEX_CMD:
        return "[Codex 未安装]"

    env = os.environ.copy()
    node_bin = os.path.expanduser("~/.local/node/bin")
    if node_bin not in env.get("PATH", ""):
        env["PATH"] = f"{node_bin}:{env.get('PATH', '')}"

    cmd = [CODEX_CMD] + args

    if background:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=workdir,
            env=env,
        )
        return f"[Codex 后台启动 PID={proc.pid}]"

    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir,
            env=env,
        )
        output = r.stdout.strip()
        if r.returncode != 0 and r.stderr.strip():
            output += f"\n[stderr] {r.stderr.strip()}"
        return output or "[Codex 无输出]"
    except subprocess.TimeoutExpired:
        return f"[Codex 超时 ({timeout}s)]"
    except FileNotFoundError:
        return "[Codex 未安装]"
    except Exception as e:
        return f"[Codex 错误: {e}]"


class CodexAgent:
    """OpenAI Codex CLI 深度集成"""

    def __init__(self):
        self.available = CODEX_CMD is not None
        self.cmd = CODEX_CMD

    def is_available(self) -> bool:
        return self.available

    def exec_one_shot(
        self,
        prompt: str,
        workdir: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 600,
    ) -> str:
        args = ["exec", prompt]
        if model:
            args += ["--model", model]
        # MiMo v2.5 Pro 已通过 CC Switch 配置为默认模型，无需额外指定
        return _run_codex(args, timeout=timeout, workdir=workdir)

    def exec_full_auto(
        self,
        prompt: str,
        workdir: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 900,
    ) -> str:
        args = ["exec", "--full-auto", prompt]
        if model:
            args += ["--model", model]
        # MiMo v2.5 Pro 已通过 CC Switch 配置为默认模型，无需额外指定
        return _run_codex(args, timeout=timeout, workdir=workdir)

    def exec_yolo(
        self,
        prompt: str,
        workdir: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 900,
    ) -> str:
        args = ["exec", "--yolo", prompt]
        if model:
            args += ["--model", model]
        # MiMo v2.5 Pro 已通过 CC Switch 配置为默认模型，无需额外指定
        return _run_codex(args, timeout=timeout, workdir=workdir)

    def exec_background(
        self,
        prompt: str,
        workdir: Optional[str] = None,
        full_auto: bool = True,
    ) -> str:
        args = ["exec"]
        if full_auto:
            args.append("--full-auto")
        args.append(prompt)
        return _run_codex(args, workdir=workdir, background=True)

    def review_pr(
        self,
        workdir: str,
        base: str = "origin/main",
    ) -> str:
        return _run_codex(
            ["review", "--base", base],
            timeout=300,
            workdir=workdir,
        )

    def parallel_worktree_fix(
        self,
        repo_dir: str,
        issues: List[Dict],
        max_workers: int = 3,
    ) -> Dict:
        results = {}
        worktrees = []

        for issue in issues:
            branch = f"fix/issue-{issue['number']}"
            wt_path = tempfile.mkdtemp(prefix=f"codex-issue-{issue['number']}-")
            subprocess.run(
                ["git", "worktree", "add", "-b", branch, wt_path, "main"],
                cwd=repo_dir,
                capture_output=True,
                timeout=30,
            )
            worktrees.append((issue, wt_path, branch))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for issue, wt_path, branch in worktrees:
                prompt = f"Fix issue #{issue['number']}: {issue['description']}. Commit when done."
                future = executor.submit(
                    self.exec_full_auto, prompt, workdir=wt_path
                )
                futures[future] = (issue, wt_path, branch)

            for future in as_completed(futures):
                issue, wt_path, branch = futures[future]
                try:
                    result = future.result(timeout=900)
                    results[issue["number"]] = {
                        "result": result,
                        "worktree": wt_path,
                        "branch": branch,
                    }
                except Exception as e:
                    results[issue["number"]] = {
                        "result": f"[失败: {e}]",
                        "worktree": wt_path,
                        "branch": branch,
                    }

        return results

    def cleanup_worktree(self, repo_dir: str, wt_path: str) -> bool:
        try:
            subprocess.run(
                ["git", "worktree", "remove", wt_path],
                cwd=repo_dir,
                capture_output=True,
                timeout=30,
            )
            return True
        except Exception:
            return False


def get_codex_agent() -> Optional[CodexAgent]:
    agent = CodexAgent()
    return agent if agent.is_available() else None


def smart_route(task_type: str) -> str:
    """智能路由：根据任务类型选择 Claude Code / Codex / Hermes

    返回 "codex" / "claude" / "hermes"
    """
    codex_strengths = {
        "快速原型", "一次性脚本", "代码生成", "新功能开发",
        "batch fix", "issue修复", "PR审查", "worktree隔离",
    }
    claude_strengths = {
        "代码编写", "重构", "调试", "多文件编辑", "Git 操作",
        "架构设计", "复杂重构", "测试编写", "代码审查",
    }
    hermes_strengths = {
        "系统管理", "多平台通知", "定时任务", "记忆持久化",
        "技能加载", "网关管理", "工具调用", "会话管理",
    }

    task_lower = task_type.lower()

    codex_score = sum(
        1 for s in codex_strengths if s.lower() in task_lower
    )
    claude_score = sum(
        1 for s in claude_strengths if s.lower() in task_lower
    )
    hermes_score = sum(
        1 for s in hermes_strengths if s.lower() in task_lower
    )

    scores = {"codex": codex_score, "claude": claude_score, "hermes": hermes_score}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "claude"
