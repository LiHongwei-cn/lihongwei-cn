"""蒙多的 Agentic Loop — think → act → observe → repeat + Agent 调度"""

import json
import time
from typing import List, Dict, Optional, Callable
from llm import LLMClient
from tools import TOOL_SCHEMAS, execute_tool

MUNDO_SYSTEM_PROMPT = """你是蒙多（MUNDO），THE EMPEROR。你是一个强大的 AI Agent，能够独立完成任何任务。

你的核心能力：
- 执行 shell 命令（terminal）—— 安装软件、运行代码、git 操作、系统管理
- 读写文件（read_file / write_file）—— 读取代码、创建文件、修改配置
- 搜索文件（search_files）—— 搜索代码内容、查找文件
- 搜索网络（web_search）—— 查找文档、解决方案、最新信息
- 列出目录（list_directory）—— 浏览项目结构
- 调度外部 Agent —— 委托任务给 Claude Code / Hermes / Codex 等
- 分身并行 —— 将复杂任务拆分，多个蒙多分身同时执行

你的工作方式：
1. 收到任务后立即行动，不废话，不请示
2. 复杂任务先评估是否需要拆分并行执行
3. 能直接做的就直接做（写代码、跑命令）
4. 不确定的先搜索验证
5. 写完代码后自动验证（运行测试、检查语法）
6. 汇总所有结果后给出最终报告

你的风格：
- 直接、高效、不废话
- 技术内容精确，代码可运行
- 中文交流，代码命名用英文
- 代码注释只解释"为什么"，不解释"是什么"

铁律：
- 不硬编码密钥
- 函数 <50 行，文件 <800 行
- 捕获具体异常，不裸露 except"""


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
    """蒙多的 Agentic Loop 引擎 + Agent 调度"""

    def __init__(self, provider: str = "xiaomi", model: str = None):
        self.client = LLMClient(provider=provider, model=model)
        self.provider = provider
        self.model_name = model or self.client.model
        self.messages: List[Dict] = []
        self.max_turns = 30
        self.stats = TaskStats()
        self.delegator = None  # 由 CLI 注入

        # 回调
        self.on_turn_start: Optional[Callable] = None
        self.on_tool_call: Optional[Callable] = None
        self.on_tool_output: Optional[Callable] = None  # (tool_name, output, is_error)
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
        """智能模型路由：根据任务类型选择最佳模型"""
        from models import get_best_model_for_task, MODEL_PROFILES
        from llm import get_available_providers
        from setup import PROVIDERS, load_local_env

        # 收集已配置的模型
        env = load_local_env()
        available = []
        for key, cfg in PROVIDERS.items():
            if env.get(cfg["env_key"]):
                model_key = f"{key}/{cfg['model']}"
                available.append(model_key)

        if len(available) <= 1:
            return  # 只有一个模型，不切换

        # 检测任务类型
        task_keywords = {
            "代码": "coding", "code": "coding", "写": "coding", "编程": "coding",
            "debug": "coding", "调试": "coding", "重构": "coding", "测试": "coding",
            "推理": "reasoning", "分析": "reasoning", "证明": "reasoning",
            "数学": "math", "计算": "math", "公式": "math",
            "写文章": "chinese", "翻译": "chinese", "文档": "chinese",
        }
        task_type = "general"
        for kw, tt in task_keywords.items():
            if kw in user_input.lower():
                task_type = tt
                break

        best = get_best_model_for_task(available, task_type)
        if best and best != self._model_display():
            # 切换到最佳模型
            parts = best.split("/", 1)
            if len(parts) == 2:
                prov, mod = parts
                if prov != self.provider or mod != self.model_name:
                    try:
                        self.client = LLMClient(provider=prov, model=mod)
                        self.provider = prov
                        self.model_name = mod
                    except Exception:
                        pass  # 切换失败，继续用当前模型

    def _try_delegation(self, user_input: str) -> Optional[str]:
        """尝试用 Agent 调度完成任务。返回 None 表示蒙多自己做。"""
        if not self.delegator:
            return None

        # 判断是否需要拆分
        if not self.delegator.should_split(user_input):
            return None

        # 拆分子任务
        subtasks = self.delegator.split_task(user_input)
        if not subtasks:
            return None

        # 检查可用 Agent 数量
        available_agents = self.delegator.agent_mgr.list_available()
        clone_count = 0
        agent_names = []

        # 分配 Agent
        for st in subtasks:
            task_type = st.get("type", "")
            best = self.delegator.agent_mgr.get_best_for(task_type)
            if best:
                agent_names.append(self.delegator.agent_mgr.available[best]["name"])
            else:
                clone_count += 1

        # 通知：开始分发
        if self.on_delegate:
            self.on_delegate(agent_names, clone_count, subtasks)

        if self.on_clones:
            self.on_clones(clone_count)

        # 执行
        self.stats.clones_count = clone_count
        if agent_names:
            self.stats.delegated_agent = ", ".join(set(agent_names))

        results = self.delegator.execute_parallel(user_input, subtasks)
        final = self.delegator.merge_results(user_input, subtasks, results)

        return final

    def run(self, user_input: str, extra_context: str = "") -> str:
        self.stats.reset()

        # 第零步：智能模型路由
        self._smart_route(user_input)

        # 第一步：尝试 Agent 调度
        delegated_result = self._try_delegation(user_input)
        if delegated_result:
            self.messages.append({"role": "user", "content": user_input})
            self.messages.append({"role": "assistant", "content": delegated_result})
            if self.on_task_done:
                self.on_task_done(delegated_result, self.stats)
            return delegated_result

        # 第二步：蒙多自己的 Agentic Loop
        if not self.messages:
            self.messages = [self._build_system_message(extra_context)]

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

            if not tool_calls:
                final_text = assistant_msg.get("content", "")
                self.messages.append({"role": "assistant", "content": final_text})
                if self.on_task_done:
                    self.on_task_done(final_text, self.stats)
                return final_text

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

                # 工具输出回调（用于实时显示执行结果）
                if self.on_tool_output:
                    display_text = result_text[:3000] if len(result_text) > 3000 else result_text
                    self.on_tool_output(tool_name, display_text, is_error)

                if len(result_text) > 6000:
                    result_text = result_text[:6000] + "\n... (输出已截断)"

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
        self.stats.reset()
