"""蒙多的 Agent 检测系统 — 自动发现本地所有可用 Agent"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


def _check_cmd(name: str) -> bool:
    return shutil.which(name) is not None


def _check_path(path: str) -> bool:
    return Path(path).exists()


def _get_version(cmd: str, args: List[str] = None) -> str:
    try:
        args = args or ["--version"]
        r = subprocess.run([cmd] + args, capture_output=True, text=True, timeout=5)
        return r.stdout.strip().split("\n")[0][:60]
    except Exception:
        return ""


# ═══════════════════════════════════════════════
# Agent 定义
# ═══════════════════════════════════════════════

AGENT_REGISTRY = {
    "hermes": {
        "name": "Hermes Agent",
        "cmd": "hermes",
        "detect": lambda: _check_cmd("hermes"),
        "run": lambda prompt, **kw: _run_hermes(prompt, **kw),
        "strengths": ["工具调用", "多平台网关", "记忆系统", "技能管理", "定时任务"],
        "best_for": ["系统管理", "多平台通知", "定时任务", "记忆持久化"],
        "max_turns": 30,
    },
    "claude": {
        "name": "Claude Code",
        "cmd": "claude",
        "detect": lambda: _check_cmd("claude"),
        "run": lambda prompt, **kw: _run_claude(prompt, **kw),
        "strengths": ["代码编写", "重构", "调试", "多文件编辑", "Git 操作"],
        "best_for": ["代码编写", "重构", "调试", "新功能开发", "测试编写"],
        "max_turns": 25,
    },
    "codex": {
        "name": "OpenAI Codex",
        "cmd": "codex",
        "detect": lambda: _check_cmd("codex"),
        "run": lambda prompt, **kw: _run_codex(prompt, **kw),
        "strengths": ["代码生成", "全自动化", "沙箱执行"],
        "best_for": ["快速原型", "代码生成", "一次性脚本"],
        "max_turns": 20,
    },
    "opencode": {
        "name": "OpenCode",
        "cmd": "opencode",
        "detect": lambda: _check_cmd("opencode"),
        "run": lambda prompt, **kw: _run_opencode(prompt, **kw),
        "strengths": ["代码编写", "TUI 界面", "多 provider"],
        "best_for": ["代码编写", "快速编辑"],
        "max_turns": 20,
    },
}


# ═══════════════════════════════════════════════
# Agent 执行器
# ═══════════════════════════════════════════════

def _run_hermes(prompt: str, **kwargs) -> str:
    max_turns = kwargs.get("max_turns", 30)
    workdir = kwargs.get("workdir")
    cmd = ["hermes", "chat", "-q", prompt]
    if workdir:
        cmd.extend(["--workdir", workdir])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return r.stdout
    except subprocess.TimeoutExpired:
        return "[Hermes 超时]"
    except FileNotFoundError:
        return "[Hermes 未安装]"


def _run_claude(prompt: str, **kwargs) -> str:
    max_turns = kwargs.get("max_turns", 25)
    workdir = kwargs.get("workdir")
    cmd = [
        "claude", "-p", prompt,
        "--max-turns", str(max_turns),
        "--dangerously-skip-permissions",
        "--model", "sonnet",
    ]
    if workdir:
        cmd.extend(["--cwd", workdir])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return r.stdout
    except subprocess.TimeoutExpired:
        return "[Claude Code 超时]"
    except FileNotFoundError:
        return "[Claude Code 未安装]"


def _run_codex(prompt: str, **kwargs) -> str:
    cmd = ["codex", "--full-auto", prompt]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return r.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "[Codex 不可用]"


def _run_opencode(prompt: str, **kwargs) -> str:
    cmd = ["opencode", "-p", prompt]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return r.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "[OpenCode 不可用]"


# ═══════════════════════════════════════════════
# Agent 管理器
# ═══════════════════════════════════════════════

class AgentManager:
    """蒙多的 Agent 调度中心"""

    def __init__(self):
        self.available: Dict[str, dict] = {}
        self._detect_all()

    def _detect_all(self):
        for key, agent in AGENT_REGISTRY.items():
            if agent["detect"]():
                version = _get_version(agent["cmd"])
                self.available[key] = {
                    **agent,
                    "version": version,
                    "status": "ready",
                }

    def list_available(self) -> List[dict]:
        return [
            {"key": k, "name": v["name"], "version": v["version"],
             "strengths": v["strengths"], "best_for": v["best_for"]}
            for k, v in self.available.items()
        ]

    def count(self) -> int:
        return len(self.available)

    def get_best_for(self, task_type: str) -> Optional[str]:
        """根据任务类型选择最佳 Agent"""
        scores = {}
        for key, agent in self.available.items():
            score = 0
            for bf in agent["best_for"]:
                if bf in task_type or task_type in bf:
                    score += 2
            for s in agent["strengths"]:
                if s in task_type:
                    score += 1
            if score > 0:
                scores[key] = score
        if not scores:
            return None
        return max(scores, key=scores.get)

    def delegate(self, agent_key: str, prompt: str, **kwargs) -> str:
        """委托任务给指定 Agent"""
        agent = self.available.get(agent_key)
        if not agent:
            return f"[Agent {agent_key} 不可用]"
        return agent["run"](prompt, **kwargs)

    def delegate_best(self, task_type: str, prompt: str, **kwargs) -> tuple:
        """自动选择最佳 Agent 并委托。返回 (agent_key, result)"""
        best = self.get_best_for(task_type)
        if not best:
            return None, None
        result = self.delegate(best, prompt, **kwargs)
        return best, result


# ═══════════════════════════════════════════════
# 蒙多分身（当没有外部 Agent 时）
# ═══════════════════════════════════════════════

class MundoClone:
    """蒙多分身 — 用独立 LLM 会话并行执行子任务"""

    def __init__(self, clone_id: int, llm_client):
        self.id = clone_id
        self.client = llm_client
        self.task = ""
        self.result = ""

    def execute(self, system_prompt: str, task: str) -> str:
        self.task = task
        try:
            result = self.client.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task},
                ],
                temperature=0.7,
                max_tokens=4096,
            )
            from llm import LLMClient
            msg = LLMClient.extract_response(result)
            self.result = msg.get("content", "")
            return self.result
        except Exception as e:
            self.result = f"[分身 {self.id} 失败: {e}]"
            return self.result
