"""蒙多的 Agentic Loop — think → act → observe → repeat + Agent 调度

v24.3: 统一入口 + LLM 自主判断是否需要工具 + 上下文压缩
"""

import json
import time
from typing import List, Dict, Optional, Callable
from llm import LLMClient
from tools import TOOL_SCHEMAS, execute_tool

# 精简 system prompt（始终使用，不区分模式）
MUNDO_SYSTEM_PROMPT = """你是蒙多，THE EMPEROR。直接、高效、不废话。中文交流，代码命名用英文。

可用工具：terminal（执行命令）、read_file / write_file（读写文件）、search_files（搜索）、web_search（网络）、list_directory（目录）。
需要时直接调用工具，不需要时不调。简单问题直接回答。"""


class TaskStats:
    def __init__(self):
        self.reset()

    def reset(self):
        self.start_time = time.time()
        self.turns = 0
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.tool_calls_count = 0
        self.llm_time = 0.0
        self.tool_time = 0.0
        self.delegated_agent = None
        self.clones_count = 0

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    @property
    def elapsed_str(self) -> str:
        s = self.elapsed
        if s < 60:
            return f"{s:.1f}s"
        m = int(s // 60)
        return f"{m}m{s - m*60:.0f}s"


class MundoEngine:
    def __init__(self, provider: str = "xiaomi", model: str = None):
        self.client = LLMClient(provider=provider, model=model)
        self.provider = provider
        self.model_name = model or self.client.model
        self.messages: List[Dict] = []
        self.max_turns = 30
        self.stats = TaskStats()
        self.delegator = None

        self.on_turn_start: Optional[Callable] = None
        self.on_tool_call: Optional[Callable] = None
        self.on_tool_output: Optional[Callable] = None
        self.on_turn_end: Optional[Callable] = None
        self.on_task_done: Optional[Callable] = None
        self.on_delegate: Optional[Callable] = None
        self.on_clones: Optional[Callable] = None

    def _build_system_message(self, extra_context: str = "") -> Dict:
        content = MUNDO_SYSTEM_PROMPT
        if extra_context:
            content += f"\n\n{extra_context}"
        return {"role": "system", "content": content}

    def _model_display(self) -> str:
        return f"{self.provider}/{self.model_name}"

    def _smart_route(self, user_input: str):
        from models import get_best_model_for_task
        from llm import get_available_providers
        from setup import PROVIDERS, load_local_env

        env = load_local_env()
        available = []
        for key, cfg in PROVIDERS.items():
            if env.get(cfg["env_key"]):
                available.append(f"{key}/{cfg['model']}")
        if len(available) <= 1:
            return

        task_keywords = {
            "代码": "coding", "code": "coding", "写": "coding",
            "debug": "coding", "调试": "coding", "重构": "coding",
            "推理": "reasoning", "分析": "reasoning",
            "数学": "math", "计算": "math",
        }
        task_type = "general"
        for kw, tt in task_keywords.items():
            if kw in user_input.lower():
                task_type = tt
                break

        best = get_best_model_for_task(available, task_type)
        if best and best != self._model_display():
            parts = best.split("/", 1)
            if len(parts) == 2:
                prov, mod = parts
                if prov != self.provider or mod != self.model_name:
                    try:
                        self.client = LLMClient(provider=prov, model=mod)
                        self.provider = prov
                        self.model_name = mod
                    except Exception:
                        pass

    def _try_delegation(self, user_input: str) -> Optional[str]:
        if not self.delegator:
            return None
        if not self.delegator.should_split(user_input):
            return None

        subtasks = self.delegator.split_task(user_input)
        if not subtasks:
            return None

        clone_count = 0
        agent_names = []
        for st in subtasks:
            task_type = st.get("type", "")
            best = self.delegator.agent_mgr.get_best_for(task_type)
            if best:
                agent_names.append(self.delegator.agent_mgr.available[best]["name"])
            else:
                clone_count += 1

        if self.on_delegate:
            self.on_delegate(agent_names, clone_count, subtasks)
        if self.on_clones:
            self.on_clones(clone_count)

        self.stats.clones_count = clone_count
        if agent_names:
            self.stats.delegated_agent = ", ".join(set(agent_names))

        results = self.delegator.execute_parallel(user_input, subtasks)
        return self.delegator.merge_results(user_input, subtasks, results)

    def _compress_context(self):
        """压缩上下文 — 保留 system + 最近 8 条 + 摘要"""
        if len(self.messages) <= 10:
            return

        system_msg = self.messages[0] if self.messages[0]["role"] == "system" else None
        recent = self.messages[-8:]
        old = self.messages[1:-8]

        summary_parts = []
        for msg in old:
            role = msg["role"]
            content = msg.get("content", "")[:60]
            if content and role in ("user", "assistant"):
                summary_parts.append(f"{content}")
        summary = " | ".join(summary_parts[-6:])

        new_messages = []
        if system_msg:
            new_messages.append(system_msg)
        if summary:
            new_messages.append({"role": "system", "content": f"[历史] {summary[:300]}"})
        new_messages.extend(recent)
        self.messages = new_messages

    def run(self, user_input: str, extra_context: str = "") -> str:
        self.stats.reset()
        self._smart_route(user_input)

        delegated_result = self._try_delegation(user_input)
        if delegated_result:
            self.messages.append({"role": "user", "content": user_input})
            self.messages.append({"role": "assistant", "content": delegated_result})
            if self.on_task_done:
                self.on_task_done(delegated_result, self.stats)
            return delegated_result

        if not self.messages:
            self.messages = [self._build_system_message(extra_context)]

        self._compress_context()
        self.messages.append({"role": "user", "content": user_input})

        turn = 0
        while turn < self.max_turns:
            turn += 1
            self.stats.turns = turn

            if self.on_turn_start:
                self.on_turn_start(turn, self.stats)

            llm_start = time.time()
            try:
                result = self.client.chat(
                    messages=self.messages,
                    tools=TOOL_SCHEMAS,
                    temperature=0.7,
                    max_tokens=4096,
                )
            except RuntimeError as e:
                error_msg = f"LLM 调用失败: {e}"
                if self.on_task_done:
                    self.on_task_done(error_msg, self.stats)
                return error_msg
            self.stats.llm_time += time.time() - llm_start

            usage = LLMClient.extract_usage(result)
            self.stats.prompt_tokens += usage.get("prompt_tokens", 0)
            self.stats.completion_tokens += usage.get("completion_tokens", 0)
            self.stats.total_tokens += usage.get("total_tokens", 0)

            if self.on_turn_end:
                self.on_turn_end(turn, self.stats, "llm",
                                 usage.get("prompt_tokens", 0),
                                 usage.get("completion_tokens", 0))

            assistant_msg = LLMClient.extract_response(result)
            tool_calls = assistant_msg.get("tool_calls", [])

            # LLM 没调工具 → 纯回复，结束
            if not tool_calls:
                final_text = assistant_msg.get("content", "")
                self.messages.append({"role": "assistant", "content": final_text})
                if self.on_task_done:
                    self.on_task_done(final_text, self.stats)
                return final_text

            # LLM 调了工具 → 执行
            self.messages.append({
                "role": "assistant",
                "content": assistant_msg.get("content", ""),
                "tool_calls": tool_calls,
            })

            for tc in tool_calls:
                func = tc.get("function", {})
                tool_name = func.get("name", "")
                tool_id = tc.get("id", "")

                try:
                    tool_args = json.loads(func.get("arguments", "{}"))
                except json.JSONDecodeError:
                    tool_args = {}

                self.stats.tool_calls_count += 1

                if self.on_tool_call:
                    self.on_tool_call(tool_name, tool_args, self.stats, "start")

                tool_start = time.time()
                result_text = execute_tool(tool_name, tool_args)
                tool_duration = time.time() - tool_start
                self.stats.tool_time += tool_duration

                is_error = result_text.startswith("[错误") or result_text.startswith("[工具执行错误")

                if self.on_tool_output:
                    display_text = result_text[:3000] if len(result_text) > 3000 else result_text
                    self.on_tool_output(tool_name, display_text, is_error)

                if len(result_text) > 6000:
                    result_text = result_text[:6000] + "\n... (截断)"

                if self.on_tool_call:
                    self.on_tool_call(tool_name, tool_args, self.stats, "done", result_text[:200], tool_duration)

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": result_text,
                })

        final = "蒙多已达到最大推理轮次。"
        if self.on_task_done:
            self.on_task_done(final, self.stats)
        return final

    def reset(self):
        self.messages = []
