"""结构化工作流引擎 — 从 Claude Code 7阶段模式提炼

将复杂任务分解为有序阶段，每个阶段有明确目标和完成标准。
支持自定义工作流模板。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class PhaseStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    SKIPPED = "skipped"


@dataclass
class Phase:
    name: str
    goal: str
    actions: List[str] = field(default_factory=list)
    status: PhaseStatus = PhaseStatus.PENDING
    output: str = ""
    auto: bool = False  # True = 自动执行，False = 需要用户确认


@dataclass
class WorkflowTemplate:
    name: str
    description: str
    phases: List[Phase]


# 预定义工作流模板
FEATURE_DEV = WorkflowTemplate(
    name="feature-dev",
    description="结构化功能开发（从 Claude Code 7阶段提炼）",
    phases=[
        Phase(
            name="Discovery",
            goal="理解要做什么",
            actions=["分析任务需求", "识别模糊点", "确认理解"],
        ),
        Phase(
            name="Exploration",
            goal="理解相关代码",
            actions=["搜索相关文件", "理解现有架构", "找到关键模式"],
            auto=True,
        ),
        Phase(
            name="Clarification",
            goal="消除所有歧义",
            actions=["列出所有问题", "等待用户回答", "确认边界条件"],
        ),
        Phase(
            name="Architecture",
            goal="设计方案",
            actions=["提出2-3种方案", "分析权衡", "推荐最佳方案"],
        ),
        Phase(
            name="Implementation",
            goal="实现功能",
            actions=["按方案编码", "遵循代码规范", "逐步推进"],
            auto=True,
        ),
        Phase(
            name="Review",
            goal="确保质量",
            actions=["检查bug", "验证规范", "测试边界条件"],
            auto=True,
        ),
        Phase(
            name="Summary",
            goal="总结完成",
            actions=["列出修改文件", "记录关键决策", "建议后续步骤"],
        ),
    ],
)

BUGFIX = WorkflowTemplate(
    name="bugfix",
    description="结构化Bug修复",
    phases=[
        Phase(
            name="Reproduce",
            goal="复现问题",
            actions=["描述错误现象", "找到触发条件", "确认可复现"],
        ),
        Phase(
            name="Diagnose",
            goal="定位根因",
            actions=["分析错误日志", "追踪调用链", "找到根因"],
            auto=True,
        ),
        Phase(
            name="Fix",
            goal="修复问题",
            actions=["编写修复代码", "确保不引入新问题"],
            auto=True,
        ),
        Phase(
            name="Verify",
            goal="验证修复",
            actions=["运行测试", "确认问题不再复现"],
            auto=True,
        ),
    ],
)

CODE_REVIEW = WorkflowTemplate(
    name="code-review",
    description="结构化代码审查",
    phases=[
        Phase(
            name="Overview",
            goal="整体了解",
            actions=["查看变更范围", "理解变更目的"],
            auto=True,
        ),
        Phase(
            name="Analysis",
            goal="深入分析",
            actions=["检查逻辑正确性", "检查边界条件", "检查性能"],
            auto=True,
        ),
        Phase(
            name="Report",
            goal="输出审查报告",
            actions=["列出问题", "按严重程度排序", "给出修复建议"],
        ),
    ],
)

TEMPLATES = {
    "feature-dev": FEATURE_DEV,
    "bugfix": BUGFIX,
    "code-review": CODE_REVIEW,
}


class WorkflowEngine:
    """工作流引擎"""

    def __init__(self):
        self._active: Optional[WorkflowTemplate] = None
        self._current_phase: int = 0

    def start(self, template_name: str) -> List[Phase]:
        """启动工作流"""
        template = TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"未知工作流模板: {template_name}")
        self._active = template
        self._current_phase = 0
        self._active.phases[0].status = PhaseStatus.ACTIVE
        return self._active.phases

    def complete_phase(self, output: str = "") -> Optional[Phase]:
        """完成当前阶段，进入下一阶段"""
        if not self._active:
            return None

        current = self._active.phases[self._current_phase]
        current.status = PhaseStatus.COMPLETED
        current.output = output

        self._current_phase += 1
        if self._current_phase >= len(self._active.phases):
            return None  # 工作流完成

        next_phase = self._active.phases[self._current_phase]
        next_phase.status = PhaseStatus.ACTIVE
        return next_phase

    def skip_phase(self, reason: str = "") -> Optional[Phase]:
        """跳过当前阶段"""
        if not self._active:
            return None
        current = self._active.phases[self._current_phase]
        current.status = PhaseStatus.SKIPPED
        current.output = f"[跳过] {reason}"
        self._current_phase += 1
        if self._current_phase >= len(self._active.phases):
            return None
        next_phase = self._active.phases[self._current_phase]
        next_phase.status = PhaseStatus.ACTIVE
        return next_phase

    def current(self) -> Optional[Phase]:
        """获取当前阶段"""
        if not self._active:
            return None
        return self._active.phases[self._current_phase]

    def progress(self) -> Dict[str, Any]:
        """获取进度"""
        if not self._active:
            return {"active": False}
        phases = self._active.phases
        completed = sum(1 for p in phases if p.status == PhaseStatus.COMPLETED)
        return {
            "active": True,
            "template": self._active.name,
            "current": self._current_phase,
            "total": len(phases),
            "completed": completed,
            "progress_pct": completed / len(phases) * 100 if phases else 0,
            "phases": [
                {"name": p.name, "status": p.status.value, "goal": p.goal}
                for p in phases
            ],
        }

    def is_done(self) -> bool:
        return (
            self._active is not None
            and all(p.status in (PhaseStatus.COMPLETED, PhaseStatus.SKIPPED)
                    for p in self._active.phases)
        )

    def reset(self):
        self._active = None
        self._current_phase = 0


def get_available_templates() -> Dict[str, str]:
    """获取所有可用模板"""
    return {name: t.description for name, t in TEMPLATES.items()}
