"""蒙多的任务分发引擎 — 层级拆分 + 并行执行 + 结果汇总"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Callable
from llm import LLMClient
from agents import AgentManager, MundoClone


SYSTEM_PROMPT_SPLIT = """你是蒙多的任务拆分器。给定一个复杂任务，将其拆分为 2-5 个可独立执行的子任务。

输出格式（严格 JSON 数组）：
[
  {"id": 1, "task": "子任务描述", "type": "代码/研究/配置/测试/文档", "priority": "high/medium/low"},
  {"id": 2, "task": "子任务描述", "type": "...", "priority": "..."},
  ...
]

规则：
- 每个子任务必须能独立完成，不依赖其他子任务的输出
- 子任务描述要具体明确，包含足够的上下文
- 简单任务（1-2步就能完成）不需要拆分，直接返回空数组 []
- 输出纯 JSON，不要 markdown 代码块"""

SYSTEM_PROMPT_MERGE = """你是蒙多的结果汇总器。给定多个子任务的执行结果，汇总成一份完整的最终报告。

规则：
- 去重：相同信息只保留一份
- 矛盾：如果结果冲突，指出矛盾并给出蒙多的判断
- 遗漏：检查是否覆盖了原始任务的所有要求
- 格式：结构化输出，用标题分段
- 语言：中文"""


class TaskDelegator:
    """蒙多的任务分发引擎"""

    def __init__(self, llm_client: LLMClient, agent_manager: AgentManager):
        self.client = llm_client
        self.agent_mgr = agent_manager
        self.on_delegate: Optional[Callable] = None  # (agent_name, task, phase) -> None
        self.on_clone_start: Optional[Callable] = None  # (clone_id, task) -> None
        self.on_clone_done: Optional[Callable] = None  # (clone_id, result_preview) -> None

    def should_split(self, task: str) -> bool:
        """判断任务是否需要拆分"""
        # 快速关键词检测
        split_keywords = [
            "同时", "并行", "分别", "各自", "三个", "四个", "五个",
            "1)", "2)", "3)", "第一", "第二", "第三",
            "以及", "另外", "还有", "同时也", "还要",
            "simultaneously", "parallel", "both", "also",
        ]
        task_lower = task.lower()
        keyword_hits = sum(1 for kw in split_keywords if kw in task_lower)
        if keyword_hits >= 2:
            return True

        # 用 LLM 判断
        try:
            result = self.client.chat(
                messages=[
                    {"role": "system", "content": "判断任务复杂度。只回复 SPLIT（需要拆分）或 SIMPLE（简单任务）。"},
                    {"role": "user", "content": f"任务: {task}\n\n这个任务需要拆分为多个子任务并行执行吗？"},
                ],
                temperature=0.1,
                max_tokens=10,
            )
            msg = LLMClient.extract_response(result)
            return "SPLIT" in msg.get("content", "").upper()
        except Exception:
            return False

    def split_task(self, task: str) -> List[Dict]:
        """将复杂任务拆分为子任务列表"""
        try:
            result = self.client.chat(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_SPLIT},
                    {"role": "user", "content": f"拆分以下任务:\n\n{task}"},
                ],
                temperature=0.3,
                max_tokens=2000,
            )
            msg = LLMClient.extract_response(result)
            content = msg.get("content", "[]").strip()
            # 提取 JSON
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            subtasks = json.loads(content)
            if isinstance(subtasks, list):
                return subtasks
        except (json.JSONDecodeError, Exception):
            pass
        return []

    def execute_parallel(self, task: str, subtasks: List[Dict]) -> Dict:
        """并行执行子任务。返回 {subtask_id: result, ...}"""
        results = {}
        max_workers = min(len(subtasks), 4)

        # 决定每个子任务用什么 Agent
        assignments = []
        for st in subtasks:
            task_type = st.get("type", "")
            best_agent = self.agent_mgr.get_best_for(task_type)
            assignments.append({
                "subtask": st,
                "agent_key": best_agent,
            })

        # 并行执行
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for a in assignments:
                st = a["subtask"]
                agent_key = a["agent_key"]
                prompt = f"任务: {st['task']}\n\n原始上下文: {task}"

                if agent_key:
                    # 用外部 Agent
                    future = executor.submit(
                        self._run_external_agent, agent_key, prompt, st
                    )
                else:
                    # 用蒙多分身
                    future = executor.submit(
                        self._run_mundo_clone, st, task
                    )
                futures[future] = st

            for future in as_completed(futures):
                st = futures[future]
                try:
                    result = future.result(timeout=600)
                    results[st["id"]] = result
                except Exception as e:
                    results[st["id"]] = f"[执行失败: {e}]"

        return results

    def _run_external_agent(self, agent_key: str, prompt: str, subtask: Dict) -> str:
        """调用外部 Agent"""
        agent_name = self.agent_mgr.available.get(agent_key, {}).get("name", agent_key)
        if self.on_delegate:
            self.on_delegate(agent_name, subtask["task"], "start")

        result = self.agent_mgr.delegate(agent_key, prompt)

        if self.on_delegate:
            self.on_delegate(agent_name, subtask["task"], "done")
        return result

    def _run_mundo_clone(self, subtask: Dict, original_task: str) -> str:
        """用蒙多分身执行"""
        clone_id = subtask["id"]
        if self.on_clone_start:
            self.on_clone_start(clone_id, subtask["task"])

        clone = MundoClone(clone_id, self.client)
        system = f"""你是蒙多的分身 #{clone_id}。你正在执行一个子任务。
原始任务: {original_task[:200]}
你的子任务: {subtask['task']}
直接执行，给出结果。不要废话。"""
        result = clone.execute(system, subtask["task"])

        if self.on_clone_done:
            self.on_clone_done(clone_id, result[:100])
        return result

    def merge_results(self, original_task: str, subtasks: List[Dict], results: Dict) -> str:
        """汇总所有子任务结果"""
        parts = []
        for st in subtasks:
            sid = st["id"]
            r = results.get(sid, "[无结果]")
            parts.append(f"## 子任务 {sid}: {st['task']}\n{r}")

        all_results = "\n\n".join(parts)

        try:
            result = self.client.chat(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_MERGE},
                    {"role": "user", "content": f"原始任务: {original_task}\n\n子任务结果:\n{all_results}\n\n请汇总成最终报告。"},
                ],
                temperature=0.5,
                max_tokens=4096,
            )
            msg = LLMClient.extract_response(result)
            return msg.get("content", all_results)
        except Exception:
            return all_results

    def delegate_and_execute(self, task: str) -> Optional[str]:
        """完整的分发执行流程。如果不需要拆分返回 None。"""
        if not self.should_split(task):
            return None

        subtasks = self.split_task(task)
        if not subtasks:
            return None

        # 执行
        results = self.execute_parallel(task, subtasks)

        # 汇总
        final = self.merge_results(task, subtasks, results)
        return final
