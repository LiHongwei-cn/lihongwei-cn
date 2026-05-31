"""蒙多的 Agentic Loop — think → act → observe → repeat + Agent 调度

v24.3: 智能路由 — 简单对话走轻量通道，任务走完整 Loop
"""

import json
import re
import time
from typing import List, Dict, Optional, Callable
from llm import LLMClient
from tools import TOOL_SCHEMAS, execute_tool


# 完整 system prompt（任务模式）
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

铁律：
- 不硬编码密钥
- 函数 <50 行，文件 <800 行
- 捕获具体异常，不裸露 except"""

# 轻量 system prompt（对话模式）
MUNDO_CHAT_PROMPT = """你是蒙多，一个直接、高效的 AI 助手。
- 简洁回答，不废话
- 中文交流
- 代码命名用英文
- 不确定的说不确定，不编造"""


# 简单对话关键词检测
_CHAT_PATTERNS = [
    r"^.{0,20}$",  # 短消息（≤20字符大概率是聊天）
    r"^(你好|hi|hello|hey|嗨|哈喽|早|晚安|谢谢|thanks|ok|好的|嗯|哦)",
    r"^(什么是|谁是|怎么理解|解释一下|聊聊|说说|你觉得|你怎么看)",
    r"(吗|呢|吧|啊|呀|哈)\??$",
]

_TASK_PATTERNS = [
    r"(写|创建|生成|编写|实现|开发|搭建|部署|配置|安装|修复|重构|优化|测试|调试)",
    r"(代码|脚本|程序|文件|项目|接口|API|数据库|服务器)",
    r"(帮我|给我想|帮我做|帮我写|帮我查|帮我找|帮我运行|帮我执行)",
    r"(terminal|command|run|exec|install|git|pip|npm|docker)",
    r"(搜索|查找|抓取|爬取|下载|上传|同步|推送)",
]


def _is_simple_chat(user_input: str) -> bool:
    """判断是否为简单对话（不需要工具）"""
    text = user_input.strip()

    # 长消息大概率是任务
    if len(text) > 200:
        return False

    # 匹配任务关键词 → 不是简单对话
    for pattern in _TASK_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False

    # 匹配对话模式 → 是简单对话
    for pattern in _CHAT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    # 问号结尾的短消息 → 大概率是对话
    if text.endswith("?") or text.endswith("？") and len(text) < 80:
        return True

    # 默认：短消息是对话，长消息是任务
    return len(text) < 60


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
        self.chat_messages: List[Dict] = []  # 对话上下文（轻量）
        self.max_turns = 30
        self.stats = TaskStats()
        self.delegator = None

        # 回调
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
        """智能模型路由：根据任务类型选择最佳模型"""
        from models import get_best_model_for_task
        from llm import get_available_providers
        from setup import PROVIDERS, load_local_env

        env = load_local_env()
        available = []
        for key, cfg in PROVIDERS.items():
            if env.get(cfg["env_key"]):
                model_key = f"{key}/{cfg['model']}"
                available.append(model_key)

        if len(available) <= 1:
            return

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
        """尝试用 Agent 调度完成任务"""
        if not self.delegator:
            return None
        if not self.delegator.should_split(user_input):
            return None

        subtasks = self.delegator.split_task(user_input)
        if not subtasks:
            return None

        available_agents = self.delegator.agent_mgr.list_available()
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
        final = self.delegator.merge_results(user_input, subtasks, results)
        return final

    def _run_chat(self, user_input: str) -> str:
        """轻量对话模式 — 不用工具，精简 prompt，省 token"""
        if not self.chat_messages:
            self.chat_messages = [{"role": "system", "content": MUNDO_CHAT_PROMPT}]

        self.chat_messages.append({"role": "user", "content": user_input})

        # 控制上下文长度：只保留 system + 最近 10 轮
        if len(self.chat_messages) > 21:
            self.chat_messages = [self.chat_messages[0]] + self.chat_messages[-20:]

        if self.on_turn_start:
            self.on_turn_start(1, self.stats)

        llm_start = time.time()
        try:
            result = self.client.chat(
                messages=self.chat_messages,
                tools=None,  # 不传工具
                temperature=0.7,
                max_tokens=512,  # 对话不需要长回复
            )
        except RuntimeError as e:
            return f"LLM 调用失败: {e}"
        self.stats.llm_time = time.time() - llm_start
        self.stats.turns = 1

        usage = LLMClient.extract_usage(result)
        self.stats.prompt_tokens = usage.get("prompt_tokens", 0)
        self.stats.completion_tokens = usage.get("completion_tokens", 0)
        self.stats.total_tokens = usage.get("total_tokens", 0)

        assistant_msg = LLMClient.extract_response(result)
        text = assistant_msg.get("content", "")
        self.chat_messages.append({"role": "assistant", "content": text})

        if self.on_task_done:
            self.on_task_done(text, self.stats)
        return text

    def run(self, user_input: str, extra_context: str = "") -> str:
        self.stats.reset()

        # 智能路由：简单对话走轻量通道
        if _is_simple_chat(user_input):
            return self._run_chat(user_input)

        # 复杂任务：智能模型路由
        self._smart_route(user_input)

        # 尝试 Agent 调度
        delegated_result = self._try_delegation(user_input)
        if delegated_result:
            self.messages.append({"role": "user", "content": user_input})
            self.messages.append({"role": "assistant", "content": delegated_result})
            if self.on_task_done:
                self.on_task_done(delegated_result, self.stats)
            return delegated_result

        # Agentic Loop
        if not self.messages:
            self.messages = [self._build_system_message(extra_context)]

        # 上下文压缩：消息太多时压缩旧消息
        if len(self.messages) > 20:
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

    def _compress_context(self):
        """压缩上下文 — 保留 system + 最近 8 条 + 摘要"""
        system_msg = self.messages[0] if self.messages[0]["role"] == "system" else None
        recent = self.messages[-8:]
        old = self.messages[1:-8] if len(self.messages) > 9 else []

        if not old:
            return

        # 生成简短摘要
        summary_parts = []
        for msg in old:
            role = msg["role"]
            content = msg.get("content", "")[:80]
            if content and role in ("user", "assistant"):
                summary_parts.append(f"[{role}] {content}")
        summary = " | ".join(summary_parts[-6:])

        new_messages = []
        if system_msg:
            new_messages.append(system_msg)
        new_messages.append({
            "role": "system",
            "content": f"[历史摘要] {summary[:400]}"
        })
        new_messages.extend(recent)

        self.messages = new_messages

    def reset(self):
        self.messages = []
        self.chat_messages = []
