"""多Agent并行协调器 — 从 Claude Code feature-dev 提炼

三种专用Agent角色，可并行执行：
- Explorer（探索者）：遍历代码库，理解架构，找到关键文件
- Architect（架构师）：设计实现方案，评估权衡
- Reviewer（审查员）：审查质量，找bug，检查规范

协调器负责分配任务、收集结果、整合输出。
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class AgentRole(Enum):
    EXPLORER = "explorer"
    ARCHITECT = "architect"
    REVIEWER = "reviewer"


@dataclass
class AgentTask:
    role: AgentRole
    prompt: str
    context: str = ""
    priority: int = 50


@dataclass
class AgentResult:
    role: AgentRole
    output: str
    key_files: List[str] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)
    elapsed: float = 0.0
    success: bool = True


ROLE_PROMPTS = {
    AgentRole.EXPLORER: (
        "你是代码探索者。深入遍历代码库，理解架构和控制流。"
        "找到与任务最相关的5-10个关键文件，解释它们的作用和关联。"
        "输出格式：1) 架构概述 2) 关键文件列表 3) 数据流/控制流"
    ),
    AgentRole.ARCHITECT: (
        "你是架构师。根据探索结果设计实现方案。"
        "提出2-3种方案，分析每种的优缺点，推荐最佳方案。"
        "输出格式：1) 方案对比 2) 推荐方案 3) 实现步骤 4) 风险点"
    ),
    AgentRole.REVIEWER: (
        "你是代码审查员。审查实现质量。"
        "检查：1) bug和逻辑错误 2) 代码规范 3) 边界条件 4) 性能问题"
        "输出格式：1) 严重问题 2) 改进建议 3) 优点"
    ),
}


class MultiAgentCoordinator:
    """多Agent并行协调器"""

    def __init__(self, executor: Callable[[str, str], str]):
        """executor(role_prompt, context) -> agent output"""
        self._executor = executor

    def run_parallel(
        self,
        tasks: List[AgentTask],
        max_workers: int = 3,
    ) -> List[AgentResult]:
        """并行执行多个Agent任务"""
        results = {}
        with ThreadPoolExecutor(max_workers=min(max_workers, len(tasks))) as pool:
            futures = {}
            for task in tasks:
                role_prompt = ROLE_PROMPTS.get(task.role, "")
                full_prompt = f"{role_prompt}\n\n任务：{task.prompt}"
                if task.context:
                    full_prompt += f"\n\n上下文：{task.context}"
                future = pool.submit(self._run_single, task.role, full_prompt, task.context)
                futures[future] = task

            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    results[task.role] = result
                except Exception as e:
                    results[task.role] = AgentResult(
                        role=task.role,
                        output=f"[Agent错误] {e}",
                        success=False,
                    )

        return [results.get(t.role, AgentResult(role=t.role, output="", success=False)) for t in tasks]

    def _run_single(self, role: AgentRole, prompt: str, context: str) -> AgentResult:
        import time
        start = time.time()
        try:
            output = self._executor(prompt, context)
            return AgentResult(
                role=role,
                output=output,
                elapsed=time.time() - start,
            )
        except Exception as e:
            return AgentResult(
                role=role,
                output=str(e),
                elapsed=time.time() - start,
                success=False,
            )

    def explore_and_design(self, task_description: str, codebase_context: str = "") -> Dict[str, str]:
        """标准工作流：先探索，再设计，最后审查"""
        # Phase 1: 并行探索
        explore_tasks = [
            AgentTask(
                role=AgentRole.EXPLORER,
                prompt=f"找到与以下任务相关的所有代码和文件：{task_description}",
                context=codebase_context,
            ),
        ]
        explore_results = self.run_parallel(explore_tasks)
        explore_output = explore_results[0].output if explore_results else ""

        # Phase 2: 架构设计（基于探索结果）
        design_tasks = [
            AgentTask(
                role=AgentRole.ARCHITECT,
                prompt=f"为以下任务设计实现方案：{task_description}",
                context=f"探索结果：\n{explore_output}",
            ),
        ]
        design_results = self.run_parallel(design_tasks)
        design_output = design_results[0].output if design_results else ""

        return {
            "exploration": explore_output,
            "architecture": design_output,
        }

    def full_review(self, code: str, task_description: str = "") -> Dict[str, str]:
        """完整审查：并行执行探索+架构+审查"""
        tasks = [
            AgentTask(
                role=AgentRole.EXPLORER,
                prompt=f"分析这段代码的结构和组织：{task_description}",
                context=code[:5000],
            ),
            AgentTask(
                role=AgentRole.ARCHITECT,
                prompt=f"评估这段代码的架构设计：{task_description}",
                context=code[:5000],
            ),
            AgentTask(
                role=AgentRole.REVIEWER,
                prompt=f"审查这段代码的质量：{task_description}",
                context=code[:5000],
            ),
        ]
        results = self.run_parallel(tasks)
        return {r.role.value: r.output for r in results}
