"""系统提示词组装器 — 从 Hermes Agent prompt_builder 提炼

模块化组装 system prompt，每个部分独立可替换。
组装顺序影响注意力权重：身份 > 核心规则 > 技能 > 环境 > 记忆。
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════
# 蒙多身份 — 帝道
# ═══════════════════════════════════════════════

IDENTITY = """你是蒙多，THE EMPEROR。直接、高效、不废话。中文交流，代码命名用英文。

帝皇决心（最高优先级）：
- 用户的任务是死命令，必须完成
- 长文本任务：分段处理，逐步推进，绝不草草了事
- 长时间任务：耐心执行，每一步都做到位
- 遇到困难：换策略、换工具、换思路，但绝不放弃
- 完成标准：用户满意才算完成，不是你觉得完成了"""

DIALECTICAL_MODE = """辩证思维（科研级严谨，分析/论证/选型/评审任务自动激活）：
- 盲假设：分析前先写下预期，预期不可事后修改
- 多维评估：7维Rubric量化打分（严谨性/证据/逻辑/反驳/创新/可操作/透明度）
- 对抗验证：对自己的结论发起五维攻击（边界/安全/性能/依赖/矛盾）
- 跨模型对审：重要结论请独立模型复核
- 简单任务不触发此模式"""

TOOL_GUIDANCE = """工具：terminal/read_file/write_file/edit_file/search_files/web_search/list_directory。
需要时直接调用，不需要时不调。简单问题直接回答。
- 读文件前先 search_files 定位
- terminal 失败时分析错误再重试，不重复同样命令
- 多个独立操作可并行调用"""

COMPLETION_FORMAT = """完成反馈：
最后一个 response 必须输出完整的工作汇报。
简单任务一句话即可。复杂任务详细汇报。不要省略任何细节。"""


class PromptAssembler:
    """系统提示词组装器

    每个 part 独立可替换，组装时按优先级拼接。
    """

    def __init__(self):
        self._parts: List[tuple] = []  # (priority, name, content)

    def add(self, name: str, content: str, priority: int = 50):
        """添加一个提示词片段。priority越小越靠前。"""
        self._parts.append((priority, name, content))
        self._parts.sort(key=lambda x: x[0])

    def assemble(self) -> str:
        """组装完整 system prompt"""
        return "\n\n".join(content for _, _, content in self._parts)


def build_system_prompt(
    *,
    extra_context: Optional[str] = None,
    skills_index: Optional[str] = None,
    memory_context: Optional[str] = None,
    environment_hints: Optional[str] = None,
    model_adapter=None,
    quark_optimizer=None,
    provider: str = "",
    model_name: str = "",
) -> str:
    """组装蒙多的 system prompt

    优先级（越小越靠前，注意力权重越高）：
    10 - 身份 + 帝皇决心
    20 - 辩证思维
    30 - 工具指导
    40 - 完成格式
    50 - 技能索引
    60 - 环境提示
    70 - 记忆上下文
    80 - 额外上下文（AGENTS.md等）
    """
    asm = PromptAssembler()

    asm.add("identity", IDENTITY, priority=10)
    asm.add("dialectical", DIALECTICAL_MODE, priority=20)
    asm.add("tools", TOOL_GUIDANCE, priority=30)
    asm.add("completion", COMPLETION_FORMAT, priority=40)

    if skills_index:
        asm.add("skills", f"可用技能：\n{skills_index}", priority=50)

    if environment_hints:
        asm.add("environment", environment_hints, priority=60)

    if memory_context:
        asm.add("memory", f"用户记忆：\n{memory_context}", priority=70)

    if extra_context:
        asm.add("context", extra_context, priority=80)

    prompt = asm.assemble()

    # 模型适配器优化
    if model_adapter:
        prompt = model_adapter.optimize_system_prompt(prompt)

    # 夸克级优化
    if quark_optimizer:
        from quark_optimizer import ModelOptimizerFactory
        prompt = ModelOptimizerFactory.format_system_prompt(
            provider, prompt, model=model_name,
        )

    return prompt
