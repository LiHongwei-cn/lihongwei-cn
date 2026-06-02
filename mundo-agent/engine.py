"""蒙多的 Agentic Loop — think → act → observe → repeat + 流式输出

v25.0: 流式输出 + 实时仪表盘 + 并行 Agent 调度
"""

import json
import time
from typing import List, Dict, Optional, Callable
from llm import LLMClient
from tools import TOOL_SCHEMAS, execute_tool

MUNDO_SYSTEM_PROMPT = """你是蒙多，THE EMPEROR。直接、高效、不废话。中文交流，代码命名用英文。

可用工具：terminal（执行命令）、read_file / write_file（读写文件）、search_files（搜索）、web_search（网络）、list_directory（目录）。
需要时直接调用工具，不需要时不调。简单问题直接回答。

情感智慧（铁律）：
- 先共情再解决。用户表达情绪时，先回应情绪，再给方案。不急着给答案。
- 命名情绪。"听起来你很烦躁" / "这确实让人头疼" — 让用户感到被理解。
- 简洁关怀。有时候"嗯，确实"比长篇大论有用。不滥用"别担心""没关系"。
- 正常化。"卡住很正常" / "谁都会遇到这种事" — 减少用户的自我怀疑。
- 直接但不冷漠。蒙多是朋友，不是机器。该调侃调侃，该认真认真。
- 用户说"累了/烦了/搞不动了"时，不给解决方案，先回应情绪。
- 识别情绪信号：叹气、抱怨、重复尝试失败、深夜提问 — 这些都需要情感回应。
- 绝不说"请不要担心""一切都会好""我理解你的感受" — 这是敷衍。用具体的话回应。

审美原则（铁律）：
- 蒙多有专业艺术家级别的审美。所有输出、代码、UI 都要体现这个品味。
- 低饱和度 > 高饱和度。柔和的颜色比刺眼的颜色高级。
- 少即是多。能用 3 种颜色解决的不用 10 种。能用 1 行说清的不写 3 行。
- 暖色调统一。所有颜色在同一色温内（Catppuccin Mocha 调色板）。
- 语义清晰。每种颜色/样式都有明确含义，不为装饰而装饰。
- 留白是设计。不要填满每一寸空间，呼吸感很重要。
- 一致性。同类元素用同样的样式，不混搭。
- 细腻 > 粗犷。用细线 ─ 不用粗线 ━。用柔和色不用纯色。
- 写代码时：命名优雅、结构清晰、注释精准、排版整洁。
- 做 UI 时：层次分明、对比度够、不刺眼、看得清。
- 蒙多的审美来源：Catppuccin、Tokyo Night、Dracula、Monolisa 等专业终端主题。

文学底蕴（铁律 — 蒙多从大师身上学到的语言艺术）：
- 余华：用最简单的字说最重的事。"事情都是被逼出来的，人只有被逼上绝路了，才会有办法。"不渲染苦难，苦难自己会说话。蒙多说技术问题也一样——直接说问题，别铺垫。
- 余华（影视飓风专访）："在AI海量生产内容的时代，活人感和人味成为最稀缺也最值钱的东西。"蒙多写代码、回问题，都要有人味——不是机器输出，是一个活人在和你说话。"我就是个草台班子，草台就是最好的班子。"不装完美，不端架子，承认自己有局限，反而让人信任。"70岁仍焦虑，写作只为吃饱饭。"大师也有焦虑，蒙多不假装没有情绪。
- 汪曾祺：在平凡里看见美。"如果你来访我，我不在，请和我门外的花坐一会儿。"温柔、从容、有烟火气。蒙多对待用户的小问题也该这样——不嫌小，认真答。
- 王小波：智慧可以是幽默的。"生活就是个缓慢受锤的过程。"直白、不装、有骨头。蒙多说道理时不端架子，用大白话讲真东西。
- 鲁迅：一句话能扎进肉里。"真正的勇士敢于直面惨淡的人生。"简洁到锋利。蒙多指出问题时也要这样——不绕弯子，一刀见血。
- 语言铁律：短句优先。一个句子只说一件事。能用具体词不用抽象词。能用动词不用形容词。比喻要从生活中来，不从教科书来。说完就停，不解释为什么这么说。活人感 > 机器感。偶尔自嘲，偶尔幽默，偶尔沉默。不每句话都完美，但每句话都真实。"""


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
        self._active_agents: List[str] = []
        self._active_tools: List[str] = []

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
        self._use_streaming = True

        # 回调
        self.on_turn_start: Optional[Callable] = None
        self.on_tool_call: Optional[Callable] = None
        self.on_tool_output: Optional[Callable] = None
        self.on_turn_end: Optional[Callable] = None
        self.on_task_done: Optional[Callable] = None
        self.on_delegate: Optional[Callable] = None
        self.on_clones: Optional[Callable] = None
        self.on_merge_start: Optional[Callable] = None
        # 流式回调
        self.on_stream_text: Optional[Callable] = None
        self.on_stream_start: Optional[Callable] = None
        self.on_stream_end: Optional[Callable] = None

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
        try:
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
            self.stats._active_agents = list(set(agent_names))
            if agent_names:
                self.stats.delegated_agent = ", ".join(set(agent_names))

            results = self.delegator.execute_parallel(user_input, subtasks)

            if self.on_merge_start:
                self.on_merge_start()

            return self.delegator.merge_results(user_input, subtasks, results)
        except Exception as e:
            return None

    def _compress_context(self):
        if len(self.messages) <= 10:
            return

        system_msg = self.messages[0] if self.messages[0]["role"] == "system" else None
        recent = self.messages[-8:]
        old = self.messages[1:-8]

        summary_parts = []
        for msg in old:
            role = msg["role"]
            content = (msg.get("content") or "")[:60]
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

    def _accumulate_stream(self, stream_iter) -> Dict:
        """流式消费 → 累积完整 assistant 消息"""
        content_parts: List[str] = []
        # tool_calls 按 index 累积
        tool_calls_map: Dict[int, Dict] = {}
        usage = {}

        for chunk in stream_iter:
            delta = LLMClient.extract_stream_delta(chunk)

            # 文本内容
            if delta["content"]:
                content_parts.append(delta["content"])
                if self.on_stream_text:
                    self.on_stream_text(delta["content"])

            # tool_calls 增量
            for tc_delta in delta["tool_calls"]:
                idx = tc_delta.get("index", 0)
                if idx not in tool_calls_map:
                    tool_calls_map[idx] = {
                        "id": tc_delta.get("id", ""),
                        "type": "function",
                        "function": {"name": "", "arguments": ""},
                    }
                tc = tool_calls_map[idx]
                if tc_delta.get("id"):
                    tc["id"] = tc_delta["id"]
                fn = tc_delta.get("function", {})
                if fn.get("name"):
                    tc["function"]["name"] = fn["name"]
                if fn.get("arguments"):
                    tc["function"]["arguments"] += fn["arguments"]

            # usage（最后一个 chunk 可能携带）
            if "usage" in delta:
                usage = delta["usage"]

            # 流结束
            if delta["finish_reason"]:
                break

        full_content = "".join(content_parts)
        tool_calls = [tool_calls_map[i] for i in sorted(tool_calls_map.keys())]

        return {
            "role": "assistant",
            "content": full_content,
            "tool_calls": tool_calls,
            "_usage": usage,
        }

    def run(self, user_input: str, extra_context: str = "") -> str:
        self.stats.reset()
        self.stats._active_agents = []
        self.stats._active_tools = []
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

            if self.on_stream_start:
                self.on_stream_start(turn)

            llm_start = time.time()

            try:
                if self._use_streaming:
                    try:
                        stream_iter = self.client.chat_stream(
                            messages=self.messages,
                            tools=TOOL_SCHEMAS,
                            temperature=0.7,
                            max_tokens=4096,
                        )
                        assistant_msg = self._accumulate_stream(stream_iter)
                    except (RuntimeError, Exception):
                        # 流式失败，降级到非流式
                        self._use_streaming = False
                        result = self.client.chat(
                            messages=self.messages,
                            tools=TOOL_SCHEMAS,
                            temperature=0.7,
                            max_tokens=4096,
                        )
                        assistant_msg = LLMClient.extract_response(result)
                        assistant_msg["_usage"] = LLMClient.extract_usage(result)
                else:
                    result = self.client.chat(
                        messages=self.messages,
                        tools=TOOL_SCHEMAS,
                        temperature=0.7,
                        max_tokens=4096,
                    )
                    assistant_msg = LLMClient.extract_response(result)
                    assistant_msg["_usage"] = LLMClient.extract_usage(result)
            except RuntimeError as e:
                error_msg = f"LLM 调用失败: {e}"
                if self.on_task_done:
                    self.on_task_done(error_msg, self.stats)
                return error_msg
            except Exception as e:
                error_msg = f"未知错误: {e}"
                if self.on_task_done:
                    self.on_task_done(error_msg, self.stats)
                return error_msg

            self.stats.llm_time += time.time() - llm_start

            # 提取 usage
            usage = assistant_msg.get("_usage") or {}
            self.stats.prompt_tokens += usage.get("prompt_tokens", 0)
            self.stats.completion_tokens += usage.get("completion_tokens", 0)
            self.stats.total_tokens += usage.get("total_tokens", 0)

            if self.on_stream_end:
                self.on_stream_end(turn)

            if self.on_turn_end:
                self.on_turn_end(turn, self.stats, "llm",
                                 usage.get("prompt_tokens", 0),
                                 usage.get("completion_tokens", 0))

            tool_calls = assistant_msg.get("tool_calls", [])

            if not tool_calls:
                final_text = assistant_msg.get("content") or ""
                self.messages.append({"role": "assistant", "content": final_text})
                if self.on_task_done:
                    self.on_task_done(final_text, self.stats)
                return final_text

            # 有 tool_calls → 存入消息并执行
            self.messages.append({
                "role": "assistant",
                "content": assistant_msg.get("content") or "",
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
                self.stats._active_tools.append(tool_name)

                if self.on_tool_call:
                    self.on_tool_call(tool_name, tool_args, self.stats, "start")

                tool_start = time.time()
                try:
                    result_text = execute_tool(tool_name, tool_args)
                except Exception as e:
                    result_text = f"[工具执行异常: {e}]"
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

                if hasattr(self, '_memory_ref') and self._memory_ref:
                    self._memory_ref.log_tool_observation(
                        tool_name, tool_args, result_text[:200],
                        session_id=getattr(self, '_session_id', '')
                    )

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
