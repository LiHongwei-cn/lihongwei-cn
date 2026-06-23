"""蒙多反射引擎 v3.0.0 — 帝皇的自我审视

核心哲学：先思考，再执行，再检查，再修复。
不是简单的重试，是每次行动后的深度反思。

反射循环（Reflexion Loop）：
1. THINK   — 分析任务，制定策略，预判风险
2. EXECUTE — 执行工具调用
3. REFLECT — 检查结果，评估质量，发现偏差
4. REPAIR  — 修正策略，调整方向，弥补缺陷

知识来源：
- Reflexion (Shinn et al., 2023): 自然语言反馈驱动的强化学习
- ReAct (Yao et al., 2022): 推理与行动交织
- Chain-of-Thought: 逐步推理
- Tree-of-Thought: 分支探索
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple


class Phase(Enum):
    THINK = auto()
    EXECUTE = auto()
    REFLECT = auto()
    REPAIR = auto()


class ReflectionVerdict(Enum):
    SUCCESS = "success"           # 任务完成
    PARTIAL = "partial"           # 部分完成，需继续
    FAILURE = "failure"           # 失败，需修复
    STUCK = "stuck"              # 卡住，需换策略
    HALLUCINATION = "hallucination"  # 幻觉，需纠正


@dataclass
class ReflectionEntry:
    """一次反射记录"""
    turn: int
    phase: Phase
    thought: str
    action: str
    result: str
    verdict: ReflectionVerdict
    lessons: List[str]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "turn": self.turn,
            "phase": self.phase.name,
            "thought": self.thought[:500],
            "action": self.action[:200],
            "result": self.result[:500],
            "verdict": self.verdict.value,
            "lessons": self.lessons,
        }


@dataclass
class TaskMemory:
    """任务记忆 — 记录历史尝试，避免重复错误"""
    attempts: List[Dict] = field(default_factory=list)
    failed_strategies: List[str] = field(default_factory=list)
    successful_patterns: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)

    def record_attempt(self, strategy: str, result: str, success: bool):
        self.attempts.append({
            "strategy": strategy[:200],
            "result": result[:500],
            "success": success,
            "timestamp": time.time(),
        })
        if success:
            self.successful_patterns.append(strategy[:200])
        else:
            self.failed_strategies.append(strategy[:200])

    def record_lesson(self, lesson: str):
        if lesson not in self.lessons_learned:
            self.lessons_learned.append(lesson)

    def get_context(self) -> str:
        """生成记忆上下文，注入到反思提示中"""
        parts = []
        if self.failed_strategies:
            recent_fails = self.failed_strategies[-3:]
            parts.append(f"已失败的策略（避免重复）: {'; '.join(recent_fails)}")
        if self.successful_patterns:
            recent_success = self.successful_patterns[-2:]
            parts.append(f"有效的策略（可复用）: {'; '.join(recent_success)}")
        if self.lessons_learned:
            recent_lessons = self.lessons_learned[-5:]
            parts.append(f"经验教训: {'; '.join(recent_lessons)}")
        return "\n".join(parts) if parts else ""


class ReflectionEngine:
    """反射引擎 — 帝皇的自我审视之心"""

    # 反思提示模板
    THINK_PROMPT = """你正在执行一个任务。在行动前，请先思考：

任务: {task}
当前状态: {state}
历史尝试: {history}

请回答：
1. 这个任务的核心目标是什么？
2. 最佳执行策略是什么？
3. 可能遇到什么风险？
4. 如何验证结果是否正确？

用简洁的中文回答，不要废话。"""

    REFLECT_PROMPT = """你刚刚执行了一个动作，请反思：

动作: {action}
结果: {result}
预期: {expected}
历史教训: {lessons}

请判断：
1. 结果是否符合预期？（成功/部分成功/失败）
2. 如果失败，原因是什么？
3. 下一步应该怎么做？
4. 有什么经验教训？

用简洁的中文回答。"""

    REPAIR_PROMPT = """上次执行失败了，需要修复：

失败原因: {failure}
已尝试的策略: {failed_strategies}
可用工具: {available_tools}

请制定修复方案：
1. 换什么策略？
2. 用什么工具？
3. 参数如何调整？
4. 如何避免同样的错误？

用简洁的中文回答。"""

    def __init__(self):
        self.history: List[ReflectionEntry] = []
        self.task_memory = TaskMemory()
        self._current_phase = Phase.THINK
        self._turn_count = 0

    @property
    def current_phase(self) -> Phase:
        return self._current_phase

    def advance_phase(self) -> Phase:
        """推进到下一阶段"""
        phase_order = [Phase.THINK, Phase.EXECUTE, Phase.REFLECT, Phase.REPAIR]
        current_idx = phase_order.index(self._current_phase)
        self._current_phase = phase_order[(current_idx + 1) % len(phase_order)]
        return self._current_phase

    def generate_think_prompt(self, task: str, state: str) -> str:
        """生成思考阶段的提示"""
        history_ctx = self.task_memory.get_context()
        return self.THINK_PROMPT.format(
            task=task[:1000],
            state=state[:500],
            history=history_ctx[:500] if history_ctx else "无",
        )

    def generate_reflect_prompt(self, action: str, result: str, expected: str) -> str:
        """生成反思阶段的提示"""
        lessons = "; ".join(self.task_memory.lessons_learned[-5:])
        return self.REFLECT_PROMPT.format(
            action=action[:200],
            result=result[:500],
            expected=expected[:500],
            lessons=lessons[:500] if lessons else "无",
        )

    def generate_repair_prompt(self, failure: str, available_tools: List[str]) -> str:
        """生成修复阶段的提示"""
        return self.REPAIR_PROMPT.format(
            failure=failure[:500],
            failed_strategies="; ".join(self.task_memory.failed_strategies[-3:]),
            available_tools=", ".join(available_tools[:20]),
        )

    def record_reflection(self, entry: ReflectionEntry):
        """记录一次反射"""
        self.history.append(entry)
        self._turn_count += 1

        # 自动提取教训
        if entry.verdict == ReflectionVerdict.FAILURE:
            self.task_memory.record_attempt(
                entry.action, entry.result, success=False
            )
        elif entry.verdict == ReflectionVerdict.SUCCESS:
            self.task_memory.record_attempt(
                entry.action, entry.result, success=True
            )

        for lesson in entry.lessons:
            self.task_memory.record_lesson(lesson)

    def analyze_output(self, output: str, expected_pattern: str = "") -> ReflectionVerdict:
        """分析输出质量，自动判定结果

        设计原则：只判定"蒙多自身是否产出了有效结果"，
        不因为输出中讨论/修复/分析错误而误判为失败。
        """
        if not output or not output.strip():
            return ReflectionVerdict.FAILURE

        # 真正的失败特征：蒙多明确表示自己无法完成
        true_failure_phrases = [
            "蒙多无法完成", "蒙多失败了", "任务无法执行",
            "i cannot complete", "i'm unable to",
            "抱歉，我无法", "对不起，我做不到",
        ]
        output_lower = output.lower()
        if any(phrase in output_lower for phrase in true_failure_phrases):
            return ReflectionVerdict.FAILURE

        # 幻觉检测：蒙多在猜测而非确认
        hallucination_phrases = [
            "蒙多猜测", "蒙多假设", "如果蒙多没记错",
            "蒙多不确定这是否正确", "可能是蒙多弄错了",
        ]
        if any(phrase in output for phrase in hallucination_phrases):
            return ReflectionVerdict.HALLUCINATION

        # 有效输出特征：有实质内容（代码、文件路径、命令结果、分析结论）
        has_substance = (
            len(output.strip()) >= 50
            or "```" in output
            or "/" in output  # 文件路径
            or "def " in output
            or "class " in output
            or "import " in output
            or "已完成" in output
            or "已修复" in output
            or "done" in output_lower
            or "success" in output_lower
            or "完成" in output
        )

        if has_substance:
            return ReflectionVerdict.SUCCESS

        # 短回复但有明确结论也算成功
        if len(output.strip()) >= 20:
            return ReflectionVerdict.SUCCESS

        return ReflectionVerdict.PARTIAL

    def should_continue(self) -> bool:
        """判断是否应该继续执行

        v3.0.1: 大幅放宽限制 — 蒙多没做完不允许擅自停下
        """
        # 30 轮内必须继续（复杂任务需要足够空间）
        if self._turn_count >= 30:
            return False

        # 连续 5 次真正失败才停止（之前是 3 次，误判率太高）
        recent = self.history[-5:] if len(self.history) >= 5 else self.history
        failure_count = sum(1 for e in recent if e.verdict == ReflectionVerdict.FAILURE)
        if failure_count >= 5:
            return False

        return True

    def get_strategy_hint(self) -> str:
        """基于历史经验，给出策略提示"""
        if self.task_memory.failed_strategies:
            return f"避免重复: {self.task_memory.failed_strategies[-1][:100]}"
        if self.task_memory.successful_patterns:
            return f"复用成功模式: {self.task_memory.successful_patterns[-1][:100]}"
        return ""

    def get_reflection_summary(self) -> str:
        """生成反射总结"""
        if not self.history:
            return "尚无反射记录"

        total = len(self.history)
        success = sum(1 for e in self.history if e.verdict == ReflectionVerdict.SUCCESS)
        fail = sum(1 for e in self.history if e.verdict == ReflectionVerdict.FAILURE)

        parts = [
            f"反射次数: {total}",
            f"成功: {success}, 失败: {fail}",
        ]

        if self.task_memory.lessons_learned:
            parts.append(f"经验教训: {len(self.task_memory.lessons_learned)} 条")
            parts.append(f"最新: {self.task_memory.lessons_learned[-1][:100]}")

        return " | ".join(parts)

    def reset(self):
        """重置反射引擎"""
        self.history.clear()
        self.task_memory = TaskMemory()
        self._current_phase = Phase.THINK
        self._turn_count = 0


class AdaptiveStrategySelector:
    """自适应策略选择器 — 根据历史表现动态调整"""

    STRATEGIES = {
        "direct": "直接执行，不做额外处理",
        "decompose": "将任务分解为子任务，逐个完成",
        "explore_first": "先探索环境，再制定方案",
        "retry_with_variation": "重试但改变参数",
        "alternative_tool": "换一个工具尝试",
        "ask_clarification": "请求用户澄清",
    }

    def __init__(self):
        self.strategy_scores: Dict[str, float] = {k: 1.0 for k in self.STRATEGIES}
        self._decay_rate = 0.95

    def select_strategy(self, context: str, failed_strategies: List[str]) -> str:
        """根据上下文和历史选择最佳策略"""
        # 排除已失败的策略
        available = {
            k: v for k, v in self.strategy_scores.items()
            if k not in failed_strategies[-3:]
        }

        if not available:
            return "ask_clarification"

        # 基于分数选择（带探索）
        import random
        strategies = list(available.keys())
        scores = [available[s] for s in strategies]

        # Softmax 选择
        max_score = max(scores)
        exp_scores = [pow(2, s - max_score) for s in scores]
        total = sum(exp_scores)
        probs = [e / total for e in exp_scores]

        return random.choices(strategies, weights=probs, k=1)[0]

    def update_score(self, strategy: str, success: bool):
        """更新策略分数"""
        if strategy not in self.strategy_scores:
            return

        if success:
            self.strategy_scores[strategy] = min(5.0, self.strategy_scores[strategy] + 0.5)
        else:
            self.strategy_scores[strategy] = max(0.1, self.strategy_scores[strategy] - 0.3)

        # 衰减其他策略分数（保持竞争）
        for k in self.strategy_scores:
            if k != strategy:
                self.strategy_scores[k] *= self._decay_rate

    def get_ranking(self) -> List[Tuple[str, float]]:
        """获取策略排名"""
        return sorted(
            self.strategy_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )


# 全局单例
_reflection_engine: Optional[ReflectionEngine] = None
_strategy_selector: Optional[AdaptiveStrategySelector] = None


def reset_reflection_engine():
    """重置单例 — 用于测试隔离"""
    global _reflection_engine
    _reflection_engine = None


def get_reflection_engine() -> ReflectionEngine:
    global _reflection_engine
    if _reflection_engine is None:
        _reflection_engine = ReflectionEngine()
    return _reflection_engine


def reset_strategy_selector():
    """重置单例 — 用于测试隔离"""
    global _strategy_selector
    _strategy_selector = None


def get_strategy_selector() -> AdaptiveStrategySelector:
    global _strategy_selector
    if _strategy_selector is None:
        _strategy_selector = AdaptiveStrategySelector()
    return _strategy_selector
