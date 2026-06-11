"""蒙多任务委托 v3.0.0 — 结构化结果 + 智能路由

融合精华：
- Hermes Agent：delegate_task并行分发、子代理隔离
- Claude Code：自定义Agent、系统提示词注入
- Codex CLI：沙箱执行、自动审批
- MiMo Code：中文优化路由

v3.0.0 改进：
- 结构化结果（ok/output/error/duration/agent）
- 智能路由（关键词匹配+LLM辅助）
- 版本兼容性检测
- 超时全链路透传
"""

import os
import json
import time
import shutil
import subprocess
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
from llm import LLMClient


# ═══════════════════════════════════════════════
# 结构化结果
# ═══════════════════════════════════════════════

@dataclass
class DelegateResult:
    ok: bool = False
    agent: str = ""
    output: str = ""
    error: str = ""
    duration: float = 0.0

    def __str__(self) -> str:
        tag = "✓" if self.ok else "✗"
        s = f"[{tag}] {self.agent} ({self.duration:.1f}s)\n{self.output}"
        if self.error:
            s += f"\n[stderr] {self.error}"
        return s


# ═══════════════════════════════════════════════
# Agent 定义
# ═══════════════════════════════════════════════

def _check_cmd(name: str) -> bool:
    return shutil.which(name) is not None


def _retry_run(cmd: list, timeout: int = 600, max_retries: int = 2, label: str = "") -> str:
    for attempt in range(max_retries + 1):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            output = r.stdout.strip()
            if output:
                return output
            if attempt < max_retries:
                time.sleep(2 * (attempt + 1))
                continue
            return f"[{label} 无输出]"
        except subprocess.TimeoutExpired:
            if attempt < max_retries:
                time.sleep(3 * (attempt + 1))
                continue
            return f"[{label} 超时 ({timeout}s)]"
        except FileNotFoundError:
            return f"[{label} 未安装]"
        except Exception as e:
            if attempt < max_retries:
                time.sleep(2 * (attempt + 1))
                continue
            return f"[{label} 错误: {e}]"
    return f"[{label} 重试耗尽]"


def _setup_agent_env():
    from setup import get_saved_provider, PROVIDERS
    provider = get_saved_provider()
    cfg = PROVIDERS.get(provider, {})
    api_key = os.environ.get(cfg.get("env_key", ""), "")
    if not api_key:
        return
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_BASE_URL"] = cfg.get("base_url", "")
    anthropic_url = cfg.get("anthropic_base_url", "")
    if anthropic_url:
        os.environ["ANTHROPIC_API_KEY"] = api_key
        os.environ["ANTHROPIC_BASE_URL"] = anthropic_url
    elif provider == "anthropic":
        os.environ["ANTHROPIC_API_KEY"] = api_key


def _codex_run(prompt: str, **kw) -> str:
    _setup_agent_env()
    try:
        from codex_integration import CodexAgent
        agent = CodexAgent()
        if not agent.is_available():
            return "[Codex 未安装]"
        workdir = kw.get('workdir')
        timeout = min(kw.get('timeout', 20), 20)
        result = agent.exec_full_auto(prompt, workdir=workdir, timeout=timeout)
        if "404" in result or "responses" in result.lower():
            return _claude_run(prompt, **kw)
        return result
    except Exception as e:
        return f"[Codex 错误: {e}]"


def _claude_run(prompt: str, **kw) -> str:
    _setup_agent_env()
    try:
        from claude_integration import ClaudeCodeAgent
        agent = ClaudeCodeAgent()
        if not agent.is_available():
            return "[Claude Code 未安装]"
        workdir = kw.get('workdir')
        timeout = kw.get('timeout', 300)
        return agent.exec_smart(prompt, workdir=workdir, timeout=timeout)
    except Exception as e:
        return f"[Claude Code 错误: {e}]"


def _hermes_run(prompt: str, **kw) -> str:
    try:
        from hermes_integration import HermesAgent
        agent = HermesAgent()
        if not agent.is_available():
            return "[Hermes Agent 未安装]"
        workdir = kw.get('workdir')
        timeout = kw.get('timeout', 300)
        return agent.chat_one_shot(prompt, timeout=timeout, workdir=workdir, lite=True)
    except Exception as e:
        return f"[Hermes 错误: {e}]"


def _mimocode_run(prompt: str, **kw) -> str:
    try:
        from mimocode_integration import MiMoCodeAgent
        agent = MiMoCodeAgent()
        if not agent.is_available():
            return "[MiMo Code 未安装]"
        workdir = kw.get('workdir')
        timeout = kw.get('timeout', 60)
        return agent.chat(prompt, workdir=workdir, timeout=timeout)
    except Exception as e:
        return f"[MiMo Code 错误: {e}]"


AGENT_REGISTRY = {
    "hermes": {
        "name": "Hermes Agent",
        "cmd": "hermes",
        "detect": lambda: _check_cmd("hermes"),
        "run": lambda prompt, **kw: _hermes_run(prompt, **kw),
        "strengths": ["工具调用", "多平台网关", "记忆系统", "技能管理"],
        "best_for": ["系统管理", "多平台通知", "定时任务", "记忆持久化"],
    },
    "claude": {
        "name": "Claude Code",
        "cmd": "claude",
        "detect": lambda: _check_cmd("claude"),
        "run": lambda prompt, **kw: _claude_run(prompt, **kw),
        "strengths": ["代码编写", "重构", "调试", "多文件编辑", "Git 操作"],
        "best_for": ["代码编写", "重构", "调试", "新功能开发", "测试编写"],
    },
    "codex": {
        "name": "OpenAI Codex",
        "cmd": "codex",
        "detect": lambda: _check_cmd("codex"),
        "run": lambda prompt, **kw: _codex_run(prompt, **kw),
        "strengths": ["代码生成", "全自动化", "沙箱执行", "PR审查"],
        "best_for": ["快速原型", "代码生成", "一次性脚本", "batch fix"],
    },
    "mimocode": {
        "name": "MiMo Code",
        "cmd": "mimo",
        "detect": lambda: _check_cmd("mimo"),
        "run": lambda prompt, **kw: _mimocode_run(prompt, **kw),
        "strengths": ["代码生成", "代码理解", "项目分析", "中文优化"],
        "best_for": ["代码生成", "项目分析", "中文代码任务"],
    },
}


# ═══════════════════════════════════════════════
# Agent 管理器
# ═══════════════════════════════════════════════

class AgentManager:

    _instance = None

    def __repr__(self) -> str:
        return f"AgentManager(available={list(self.available.keys())})"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.available = {}
            cls._instance._detect_all()
        return cls._instance

    def _detect_all(self):
        self.available = {}
        for key, agent in AGENT_REGISTRY.items():
            if agent["detect"]():
                self.available[key] = {**agent, "status": "ready"}

    def refresh(self):
        self._detect_all()

    def list_available(self) -> List[dict]:
        return [
            {"key": k, "name": v["name"], "strengths": v["strengths"], "best_for": v["best_for"]}
            for k, v in self.available.items()
        ]

    def get_best_for_smart(self, task_type: str) -> Optional[str]:
        task_lower = task_type.lower()
        coding_keywords = ["代码", "code", "编写", "write", "实现", "implement",
                           "重构", "refactor", "调试", "debug", "测试", "test"]
        system_keywords = ["系统", "system", "管理", "manage", "配置", "config",
                           "部署", "deploy", "监控", "monitor", "网关", "gateway"]
        quick_keywords = ["快速", "quick", "原型", "prototype", "一次性", "one-shot",
                          "批量", "batch", "生成", "generate"]

        scores = {}
        if "claude" in self.available:
            claude_score = sum(1 for kw in coding_keywords if kw in task_lower)
            if claude_score > 0:
                scores["claude"] = claude_score
        if "hermes" in self.available:
            hermes_score = sum(1 for kw in system_keywords if kw in task_lower)
            if hermes_score > 0:
                scores["hermes"] = hermes_score
        if "codex" in self.available:
            codex_score = sum(1 for kw in quick_keywords if kw in task_lower)
            if codex_score > 0:
                scores["codex"] = codex_score
        if "mimocode" in self.available:
            if any(kw in task_lower for kw in ["中文", "chinese"]):
                scores["mimocode"] = 2

        if scores:
            return max(scores, key=lambda k: scores[k])
        if "claude" in self.available:
            return "claude"
        return next(iter(self.available), None)

    def delegate(self, agent_key: str, prompt: str, **kwargs) -> DelegateResult:
        t0 = time.time()
        if agent_key == "auto":
            agent_key = self.get_best_for_smart(prompt) or next(iter(self.available), None)
            if not agent_key:
                return DelegateResult(ok=False, agent="auto", error="无可用 agent",
                                      duration=time.time() - t0)

        agent = self.available.get(agent_key)
        if not agent:
            avail = ", ".join(self.available.keys()) or "无"
            return DelegateResult(ok=False, agent=agent_key,
                                  error=f"Agent {agent_key} 不可用。已检测到: {avail}",
                                  duration=time.time() - t0)
        try:
            output = agent["run"](prompt, **kwargs)
            elapsed = time.time() - t0
            is_err = output.startswith("[") and any(
                kw in output for kw in ("错误", "超时", "未安装", "异常", "Error")
            )
            return DelegateResult(ok=not is_err, agent=agent_key,
                                  output=output, duration=elapsed)
        except Exception as e:
            return DelegateResult(ok=False, agent=agent_key,
                                  error=str(e), duration=time.time() - t0)


# ═══════════════════════════════════════════════
# 蒙多分身
# ═══════════════════════════════════════════════

class MundoClone:

    def __repr__(self) -> str:
        return f"MundoClone(id={self.id})"

    def __init__(self, clone_id: int, llm_client):
        self.id = clone_id
        self.client = llm_client

    def execute(self, system_prompt: str, task: str, max_retries: int = 3) -> str:
        last_error = None
        for attempt in range(max_retries):
            try:
                result = self.client.chat(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": task},
                    ],
                    temperature=0.7, max_tokens=4096,
                )
                content = LLMClient.extract_response(result).get("content") or ""
                if content:
                    return content
                last_error = "空回复"
            except Exception as e:
                last_error = str(e)
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
        return f"[分身 {self.id} 失败 ({max_retries}次重试): {last_error}]"


# ═══════════════════════════════════════════════
# 任务委托引擎
# ═══════════════════════════════════════════════

SPLIT_PROMPT = """你是蒙多的任务拆分器。给定一个复杂任务，拆分为 2-5 个可独立执行的子任务。

输出格式（严格 JSON 数组）：
[{"id": 1, "task": "子任务描述", "type": "代码/研究/配置/测试/文档", "priority": "high/medium/low"}]

规则：
- 每个子任务必须能独立完成
- 简单任务直接返回空数组 []
- 纯 JSON，不要代码块"""

MERGE_PROMPT = """你是蒙多的结果汇总器。给定多个子任务结果，汇总成最终报告。
去重、指出矛盾、检查遗漏。中文输出。"""


class TaskDelegator:

    def __repr__(self) -> str:
        return "TaskDelegator()"

    def __init__(self, llm_client: LLMClient, agent_manager: AgentManager):
        self.client = llm_client
        self.agent_mgr = agent_manager
        self.on_subtask_progress: Optional[Callable] = None

    def should_split(self, task: str) -> bool:
        try:
            result = self.client.chat(
                messages=[
                    {"role": "system", "content": "判断任务复杂度。只回复 SPLIT 或 SIMPLE。"},
                    {"role": "user", "content": f"任务: {task}\n\n需要拆分为多个子任务并行执行吗？"},
                ],
                temperature=0.1, max_tokens=10,
            )
            return "SPLIT" in (LLMClient.extract_response(result).get("content") or "").upper()
        except Exception:
            return False

    def split_task(self, task: str) -> List[Dict]:
        try:
            result = self.client.chat(
                messages=[
                    {"role": "system", "content": SPLIT_PROMPT},
                    {"role": "user", "content": f"拆分以下任务:\n\n{task}"},
                ],
                temperature=0.3, max_tokens=1000,
            )
            content = LLMClient.extract_response(result).get("content") or ""
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
                content = content.rsplit("```", 1)[0]
            return json.loads(content)
        except Exception:
            return []

    def execute_parallel(self, task: str, system_prompt: str = "",
                         max_workers: int = 3) -> List[DelegateResult]:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        subtasks = self.split_task(task)
        if not subtasks:
            return [self.agent_mgr.delegate("auto", task)]

        results = []
        with ThreadPoolExecutor(max_workers=min(len(subtasks), max_workers)) as executor:
            futures = {}
            for sub in subtasks:
                sub_task = sub.get("task", "")
                agent_key = self.agent_mgr.get_best_for_smart(sub_task) or "auto"
                futures[executor.submit(self.agent_mgr.delegate, agent_key, sub_task)] = sub

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    if self.on_subtask_progress:
                        self.on_subtask_progress(futures[future], result)
                except Exception as e:
                    sub = futures[future]
                    results.append(DelegateResult(
                        ok=False, agent="unknown",
                        error=str(e), duration=0
                    ))
        return results
