"""蒙多任务委托 v2.0.8 — 结构化结果 + 智能路由 + 全参数透传

v2.0.8 改进：
- 适配新版 agent：Hermes v0.16.0、Claude Code v2.1.170、Codex v0.138.0
- 自动版本检测与兼容性验证
- 增强错误处理与重试机制
- 保持 AI 模型配置不变（xiaomi/mimo-v2.5-pro）

v2.0.8 改进：
- DelegateResult 结构化结果（ok/output/error/duration/agent）
- timeout/workdir 全链路透传到所有 agent
- auto 智能路由模式
- AgentManager 单例缓存
- hermes 支持 workdir
"""

import os
import json
import time
import shutil
import subprocess
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Callable
from llm import LLMClient
try:
    from codex_integration import CodexAgent, smart_route
except ImportError:
    CodexAgent = None
    smart_route = None

try:
    from claude_integration import ClaudeCodeAgent
except ImportError:
    ClaudeCodeAgent = None

try:
    from hermes_integration import HermesAgent
except ImportError:
    HermesAgent = None


# ═══════════════════════════════════════════════
# 结构化结果
# ═══════════════════════════════════════════════

@dataclass
class DelegateResult:
    """委派结果 — 结构化，便于上层判断和展示"""
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




# ═══════════════════════════════════════════════
# 版本检测与兼容性验证
# ═══════════════════════════════════════════════

EXPECTED_VERSIONS = {
    "hermes": {"min": "0.16.0", "cmd": ["hermes", "--version"]},
    "claude": {"min": "2.1.170", "cmd": ["claude", "--version"]},
    "codex": {"min": "0.138.0", "cmd": ["codex", "--version"]},
}

def _extract_version(output: str) -> str:
    """从命令输出中提取版本号"""
    import re
    # 匹配 vX.Y.Z 或 X.Y.Z 格式
    match = re.search(r'v?(\d+\.\d+\.\d+)', output)
    return match.group(1) if match else ""

def _check_version_compatibility() -> dict:
    """检查所有 agent 版本兼容性"""
    results = {}
    for agent, info in EXPECTED_VERSIONS.items():
        try:
            r = subprocess.run(info["cmd"], capture_output=True, text=True, timeout=10)
            version = _extract_version(r.stdout)
            results[agent] = {
                "installed": version,
                "expected": info["min"],
                "compatible": version >= info["min"] if version else False,
            }
        except Exception:
            results[agent] = {"installed": "", "expected": info["min"], "compatible": False}
    return results

def _setup_agent_env():
    """根据当前 provider 自动设置 Codex/Claude Code 所需环境变量"""
    from setup import get_saved_provider, PROVIDERS
    provider = get_saved_provider()
    cfg = PROVIDERS.get(provider, {})
    api_key = os.environ.get(cfg.get("env_key", ""), "")
    if not api_key:
        return

    # Codex 走 OpenAI 兼容端点
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_BASE_URL"] = cfg.get("base_url", "")

    # Claude Code 走 Anthropic 端点（小米专属）
    anthropic_url = cfg.get("anthropic_base_url", "")
    if anthropic_url:
        os.environ["ANTHROPIC_API_KEY"] = api_key
        os.environ["ANTHROPIC_BASE_URL"] = anthropic_url
    elif provider == "anthropic":
        os.environ["ANTHROPIC_API_KEY"] = api_key


def _codex_run(prompt: str, **kw) -> str:
    """Codex 调用入口 — 自动路由到 OpenAI 兼容端点"""
    _setup_agent_env()
    try:
        from codex_integration import CodexAgent
        agent = CodexAgent()
        if not agent.is_available():
            return "[Codex 未安装]"
        workdir = kw.get('workdir')
        timeout = kw.get('timeout', 300)
        return agent.exec_full_auto(prompt, workdir=workdir, timeout=timeout)
    except Exception as e:
        return f"[Codex 错误: {e}]"



def _claude_run(prompt: str, **kw) -> str:
    """Claude Code 调用入口 — 自动路由到 Anthropic 端点（智能模式）"""
    _setup_agent_env()
    try:
        from claude_integration import ClaudeCodeAgent
        agent = ClaudeCodeAgent()
        if not agent.is_available():
            return "[Claude Code 未安装]"
        workdir = kw.get('workdir')
        timeout = kw.get('timeout', 300)
        # 使用智能模式，根据任务复杂度自动选择努力级别
        return agent.exec_smart(prompt, workdir=workdir, timeout=timeout)
    except Exception as e:
        return f"[Claude Code 错误: {e}]"



def _hermes_run(prompt: str, **kw) -> str:
    """Hermes Agent 调用入口 — 使用 hermes_integration.py 的全功能封装"""
    try:
        from hermes_integration import HermesAgent
        agent = HermesAgent()
        if not agent.is_available():
            return "[Hermes Agent 未安装]"
        workdir = kw.get('workdir')
        timeout = kw.get('timeout', 300)
        return agent.chat_one_shot(prompt, timeout=timeout, workdir=workdir)
    except Exception as e:
        return f"[Hermes 错误: {e}]"

AGENT_REGISTRY = {
    "hermes": {
        "name": "Hermes Agent",
        "cmd": "hermes",
        "detect": lambda: _check_cmd("hermes"),
        "run": lambda prompt, **kw: _hermes_run(prompt, **kw),
        "strengths": ["工具调用", "多平台网关", "记忆系统", "技能管理", "定时任务", "会话管理"],
        "best_for": ["系统管理", "多平台通知", "定时任务", "记忆持久化", "技能加载", "网关管理"],
    },
    "claude": {
        "name": "Claude Code",
        "cmd": "claude",
        "detect": lambda: _check_cmd("claude"),
        "run": lambda prompt, **kw: _claude_run(prompt, **kw),
        "strengths": ["代码编写", "重构", "调试", "多文件编辑", "Git 操作", "结构化输出", "自定义Agent"],
        "best_for": ["代码编写", "重构", "调试", "新功能开发", "测试编写", "代码审查"],
    },
    "codex": {
        "name": "OpenAI Codex",
        "cmd": "codex",
        "detect": lambda: _check_cmd("codex"),
        "run": lambda prompt, **kw: _codex_run(prompt, **kw),
        "strengths": ["代码生成", "全自动化", "沙箱执行", "PR审查", "并行worktree", "MiMo驱动"],
        "best_for": ["快速原型", "代码生成", "一次性脚本", "batch fix", "issue修复", "PR审查", "中文代码"],
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
            cls._instance.version_info = _check_version_compatibility()
        return cls._instance

    def _detect_all(self):
        self.available = {}
        for key, agent in AGENT_REGISTRY.items():
            if agent["detect"]():
                self.available[key] = {**agent, "status": "ready"}

    def refresh(self):
        """重新检测可用 agent 并更新版本信息"""
        self._detect_all()
        self.version_info = _check_version_compatibility()

    def list_available(self) -> List[dict]:
        return [
            {"key": k, "name": v["name"], "strengths": v["strengths"], "best_for": v["best_for"]}
            for k, v in self.available.items()
        ]

    def get_version_report(self) -> str:
        """获取所有 agent 版本报告"""
        lines = ["Agent 版本状态："]
        for agent, info in self.version_info.items():
            status = "✓" if info["compatible"] else "✗"
            lines.append(f"  {status} {agent}: {info['installed']} (要求 >= {info['expected']})")
        return "\n".join(lines)

    def get_best_for(self, task_type: str) -> Optional[str]:
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
        return max(scores, key=scores.get) if scores else None

    def get_best_for_smart(self, task_type: str) -> Optional[str]:
        """智能路由：根据任务类型自动选择最佳 Agent（Claude vs Codex）"""
        if smart_route:
            route = smart_route(task_type)
            if route == 'codex' and 'codex' in self.available:
                return 'codex'
            if route == 'claude' and 'claude' in self.available:
                return 'claude'
        return self.get_best_for(task_type)

    def delegate(self, agent_key: str, prompt: str, **kwargs) -> DelegateResult:
        """委派任务给指定 agent，返回结构化结果"""
        t0 = time.time()

        # auto 模式：智能路由
        if agent_key == "auto":
            agent_key = self.get_best_for_smart(prompt) or (
                next(iter(self.available), None)
            )
            if not agent_key:
                return DelegateResult(
                    ok=False, agent="auto", error="无可用 agent",
                    duration=time.time() - t0,
                )

        agent = self.available.get(agent_key)
        if not agent:
            avail = ", ".join(self.available.keys()) or "无"
            return DelegateResult(
                ok=False, agent=agent_key,
                error=f"Agent {agent_key} 不可用。已检测到: {avail}",
                duration=time.time() - t0,
            )

        try:
            output = agent["run"](prompt, **kwargs)
            elapsed = time.time() - t0
            # 判断是否成功：不以 [ 错误/超时/未安装 开头
            is_err = output.startswith("[") and any(
                kw in output for kw in ("错误", "超时", "未安装", "异常", "Error")
            )
            return DelegateResult(
                ok=not is_err, agent=agent_key,
                output=output, duration=elapsed,
            )
        except Exception as e:
            return DelegateResult(
                ok=False, agent=agent_key,
                error=str(e), duration=time.time() - t0,
            )


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
                temperature=0.3, max_tokens=2000,
            )
            content = (LLMClient.extract_response(result).get("content") or "[]").strip()
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            subtasks = json.loads(content)
            return subtasks if isinstance(subtasks, list) else []
        except Exception:
            return []

    def execute_parallel(self, task: str, subtasks: List[Dict]) -> Dict:
        results = {}
        max_workers = min(len(subtasks), 4)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for st in subtasks:
                task_type = st.get("type", "")
                best_agent = self.agent_mgr.get_best_for_smart(task_type)
                agent_name = self.agent_mgr.available.get(best_agent, {}).get("name", f"分身#{st['id']}") if best_agent else f"分身#{st['id']}"
                prompt = f"任务: {st['task']}\n\n原始上下文: {task}"

                if self.on_subtask_progress:
                    self.on_subtask_progress(st["id"], st["task"], agent_name, "start", None)

                if best_agent:
                    future = executor.submit(self._run_with_fallback, best_agent, prompt, st, task)
                else:
                    future = executor.submit(self._run_clone, st, task)
                futures[future] = (st, agent_name)

            for future in as_completed(futures):
                st, agent_name = futures[future]
                try:
                    result = future.result(timeout=600)
                    results[st["id"]] = result
                    if self.on_subtask_progress:
                        preview = (result or "")[:80].replace("\n", " ")
                        self.on_subtask_progress(st["id"], st["task"], agent_name, "done", preview)
                except Exception as e:
                    results[st["id"]] = f"[执行失败: {e}]"
                    if self.on_subtask_progress:
                        self.on_subtask_progress(st["id"], st["task"], agent_name, "error", str(e)[:80])
        return results

    def _run_with_fallback(self, agent_key: str, prompt: str, subtask: Dict, original_task: str) -> str:
        result = self.agent_mgr.delegate(agent_key, prompt)
        check_text = (result.output or "") + (result.error or "")
        if any(k in check_text for k in ["超时", "未安装", "不可用", "错误", "失败", "重试耗尽", "无输出"]):
            return self._run_clone(subtask, original_task)
        return result.output or str(result)

    def _run_clone(self, subtask: Dict, original_task: str) -> str:
        clone = MundoClone(subtask["id"], self.client)
        system = f"""你是蒙多的分身 #{subtask['id']}。正在执行子任务。
原始任务: {original_task[:200]}
你的子任务: {subtask['task']}
直接执行，不废话。"""
        return clone.execute(system, subtask["task"])

    def merge_results(self, original_task: str, subtasks: List[Dict], results: Dict) -> str:
        parts = []
        for st in subtasks:
            r = results.get(st["id"], "[无结果]")
            parts.append(f"## 子任务 {st['id']}: {st['task']}\n{r}")
        all_results = "\n\n".join(parts)

        try:
            result = self.client.chat(
                messages=[
                    {"role": "system", "content": MERGE_PROMPT},
                    {"role": "user", "content": f"原始任务: {original_task}\n\n子任务结果:\n{all_results}\n\n请汇总成最终报告。"},
                ],
                temperature=0.5, max_tokens=4096,
            )
            return LLMClient.extract_response(result).get("content") or all_results
        except Exception:
            return all_results
