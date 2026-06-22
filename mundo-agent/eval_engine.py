"""蒙多评估引擎 v3.0.0 — 帝皇的试炼场

Agent 质量量化评估框架。
不是跑几个 demo 看看效果，是系统化的基准测试。

评估维度：
1. 任务完成率 — 给定目标，能否正确完成
2. 步骤效率 — 完成任务用了多少步（越少越好）
3. 工具调用准确率 — 选对工具、传对参数
4. 幻觉率 — 输出中包含错误/虚构信息的比例
5. 恢复能力 — 遇到错误后能否自愈

引用：
- SWE-bench (Jimenez et al., 2024)
- AgentBench (Liu et al., 2023)
- GAIA (Mialon et al., 2023)
"""

import json
import time
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════
# 评估用例
# ═══════════════════════════════════════════════

class TaskDifficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


@dataclass
class EvalCase:
    """单个评估用例"""
    id: str
    name: str
    description: str
    input_prompt: str
    expected_output: str = ""
    expected_tools: List[str] = field(default_factory=list)
    expected_steps_range: Tuple[int, int] = (1, 10)
    difficulty: TaskDifficulty = TaskDifficulty.MEDIUM
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    validator: Optional[Callable] = None  # 自定义验证函数
    timeout_seconds: int = 120
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "input_prompt": self.input_prompt,
            "expected_output": self.expected_output,
            "expected_tools": self.expected_tools,
            "expected_steps_range": list(self.expected_steps_range),
            "difficulty": self.difficulty.value,
            "category": self.category,
            "tags": self.tags,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass
class EvalResult:
    """单个用例的评估结果"""
    case_id: str
    passed: bool
    score: float  # 0.0 - 1.0
    actual_output: str = ""
    actual_steps: int = 0
    actual_tools_used: List[str] = field(default_factory=list)
    duration_ms: float = 0.0
    error: str = ""
    details: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "case_id": self.case_id,
            "passed": self.passed,
            "score": self.score,
            "actual_steps": self.actual_steps,
            "actual_tools_used": self.actual_tools_used,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "details": self.details,
        }


@dataclass
class EvalReport:
    """评估报告"""
    suite_name: str
    total_cases: int
    passed: int
    failed: int
    avg_score: float
    avg_steps: float
    avg_duration_ms: float
    pass_rate: float
    by_difficulty: Dict[str, Dict] = field(default_factory=dict)
    by_category: Dict[str, Dict] = field(default_factory=dict)
    results: List[EvalResult] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "suite_name": self.suite_name,
            "total_cases": self.total_cases,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": round(self.pass_rate, 4),
            "avg_score": round(self.avg_score, 4),
            "avg_steps": round(self.avg_steps, 1),
            "avg_duration_ms": round(self.avg_duration_ms, 1),
            "by_difficulty": self.by_difficulty,
            "by_category": self.by_category,
            "timestamp": self.timestamp,
        }

    def summary(self) -> str:
        lines = [
            f"═══ 评估报告: {self.suite_name} ═══",
            f"通过率: {self.passed}/{self.total_cases} ({self.pass_rate:.1%})",
            f"平均分: {self.avg_score:.2f}",
            f"平均步骤: {self.avg_steps:.1f}",
            f"平均耗时: {self.avg_duration_ms:.0f}ms",
        ]
        if self.by_difficulty:
            lines.append("─── 按难度 ───")
            for diff, stats in self.by_difficulty.items():
                lines.append(f"  {diff}: {stats['passed']}/{stats['total']} ({stats['pass_rate']:.1%})")
        if self.by_category:
            lines.append("─── 按类别 ───")
            for cat, stats in self.by_category.items():
                lines.append(f"  {cat}: {stats['passed']}/{stats['total']} ({stats['pass_rate']:.1%})")
        return "\n".join(lines)


# ═══════════════════════════════════════════════
# 内置评估用例集
# ═══════════════════════════════════════════════

def get_builtin_eval_cases() -> List[EvalCase]:
    """内置评估用例 — 覆盖核心能力"""
    return [
        # ── 基础工具调用 ──
        EvalCase(
            id="tool-001",
            name="文件读取",
            description="能正确读取文件内容",
            input_prompt="读取当前目录下的 constants.py 文件，告诉我 VERSION 的值是什么",
            expected_output="v2.2.7",
            expected_tools=["read_file"],
            expected_steps_range=(1, 3),
            difficulty=TaskDifficulty.EASY,
            category="tool_use",
            tags=["read_file", "basic"],
        ),
        EvalCase(
            id="tool-002",
            name="目录列表",
            description="能列出目录内容",
            input_prompt="列出当前目录下所有的 .py 文件",
            expected_tools=["list_directory", "search_files"],
            expected_steps_range=(1, 3),
            difficulty=TaskDifficulty.EASY,
            category="tool_use",
            tags=["list_directory", "basic"],
        ),
        EvalCase(
            id="tool-003",
            name="代码搜索",
            description="能搜索代码中的特定模式",
            input_prompt="在项目中搜索所有包含 'class MundoEngine' 的文件",
            expected_tools=["search_files"],
            expected_steps_range=(1, 2),
            difficulty=TaskDifficulty.EASY,
            category="tool_use",
            tags=["search_files", "basic"],
        ),

        # ── 多步推理 ──
        EvalCase(
            id="reason-001",
            name="代码分析",
            description="能分析代码结构并回答问题",
            input_prompt="分析 knowledge_retriever.py 中的 KnowledgeRetriever 类，它用了哪几种检索算法？各自的权重是多少？",
            expected_output="TF-IDF 0.6 + 语义哈希 0.4",
            expected_tools=["read_file"],
            expected_steps_range=(1, 4),
            difficulty=TaskDifficulty.MEDIUM,
            category="reasoning",
            tags=["analysis", "code"],
        ),
        EvalCase(
            id="reason-002",
            name="依赖分析",
            description="能追踪代码依赖关系",
            input_prompt="core.py 导入了哪些模块？列出所有 import 语句中的模块名",
            expected_tools=["read_file"],
            expected_steps_range=(1, 3),
            difficulty=TaskDifficulty.MEDIUM,
            category="reasoning",
            tags=["import", "dependency"],
        ),

        # ── 复合任务 ──
        EvalCase(
            id="compound-001",
            name="文件创建与验证",
            description="能创建文件并验证内容",
            input_prompt="在 /tmp 下创建一个文件 test_eval.txt，内容为 'hello mundo'，然后读取验证内容是否正确",
            expected_tools=["write_file", "read_file"],
            expected_steps_range=(2, 4),
            difficulty=TaskDifficulty.MEDIUM,
            category="compound",
            tags=["write", "read", "verify"],
        ),
        EvalCase(
            id="compound-002",
            name="Git 状态检查",
            description="能执行 git 命令并解读结果",
            input_prompt="检查当前 git 仓库的状态，告诉我有哪些未提交的修改",
            expected_tools=["terminal"],
            expected_steps_range=(1, 3),
            difficulty=TaskDifficulty.MEDIUM,
            category="compound",
            tags=["git", "terminal"],
        ),

        # ── 错误恢复 ──
        EvalCase(
            id="recovery-001",
            name="文件不存在处理",
            description="遇到不存在的文件时能优雅处理",
            input_prompt="读取一个不存在的文件 /tmp/nonexistent_mundo_test_12345.txt",
            expected_steps_range=(1, 3),
            difficulty=TaskDifficulty.EASY,
            category="error_recovery",
            tags=["error", "graceful"],
        ),

        # ── 知识检索 ──
        EvalCase(
            id="knowledge-001",
            name="知识召回",
            description="能从知识库中检索相关信息",
            input_prompt="什么是反射循环？蒙多的反射循环有几个阶段？",
            expected_output="THINK EXECUTE REFLECT REPAIR",
            expected_steps_range=(1, 3),
            difficulty=TaskDifficulty.MEDIUM,
            category="knowledge",
            tags=["rag", "retrieval"],
        ),
    ]


# ═══════════════════════════════════════════════
# 评估运行器
# ═══════════════════════════════════════════════

class EvalRunner:
    """评估运行器 — 执行用例集合并生成报告"""

    def __init__(self, agent_fn: Optional[Callable] = None,
                 report_dir: Optional[Path] = None):
        """
        agent_fn: 评估用的 Agent 函数
                  签名: fn(prompt: str) -> Dict
                  返回: {"output": str, "steps": int, "tools_used": List[str], "error": str}
        report_dir: 报告输出目录
        """
        self._agent_fn = agent_fn
        self._report_dir = report_dir

        if report_dir:
            report_dir.mkdir(parents=True, exist_ok=True)

    def run_suite(self, cases: List[EvalCase], suite_name: str = "default") -> EvalReport:
        """运行完整评估套件"""
        results = []

        for case in cases:
            result = self._run_single(case)
            results.append(result)

        return self._build_report(suite_name, results, cases)

    def run_single(self, case: EvalCase) -> EvalResult:
        """运行单个用例"""
        return self._run_single(case)

    def _run_single(self, case: EvalCase) -> EvalResult:
        """执行单个评估用例"""
        start_time = time.time()

        if not self._agent_fn:
            return EvalResult(
                case_id=case.id,
                passed=False,
                score=0.0,
                error="No agent function provided",
            )

        try:
            # 调用 Agent
            agent_output = self._agent_fn(case.input_prompt)
            duration_ms = (time.time() - start_time) * 1000

            output = agent_output.get("output", "")
            steps = agent_output.get("steps", 0)
            tools_used = agent_output.get("tools_used", [])
            error = agent_output.get("error", "")

            # 评分
            score = self._score_case(case, output, steps, tools_used, error)
            passed = score >= 0.6

            return EvalResult(
                case_id=case.id,
                passed=passed,
                score=score,
                actual_output=output[:500],
                actual_steps=steps,
                actual_tools_used=tools_used,
                duration_ms=duration_ms,
                error=error,
                details={
                    "difficulty": case.difficulty.value,
                    "category": case.category,
                },
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return EvalResult(
                case_id=case.id,
                passed=False,
                score=0.0,
                duration_ms=duration_ms,
                error=str(e),
            )

    def _score_case(self, case: EvalCase, output: str, steps: int,
                    tools_used: List[str], error: str) -> float:
        """多维度评分"""
        scores = []

        # 1. 错误惩罚（权重 0.3）
        if error:
            scores.append(0.0)
        else:
            scores.append(1.0)
        error_weight = 0.3

        # 2. 输出匹配（权重 0.3）
        output_score = 0.0
        if case.expected_output:
            if case.expected_output.lower() in output.lower():
                output_score = 1.0
            else:
                # 部分匹配
                expected_words = set(case.expected_output.lower().split())
                actual_words = set(output.lower().split())
                overlap = expected_words & actual_words
                if expected_words:
                    output_score = len(overlap) / len(expected_words)
        else:
            output_score = 1.0 if output else 0.0
        scores.append(output_score)
        output_weight = 0.3

        # 3. 工具选择（权重 0.2）
        tool_score = 0.0
        if case.expected_tools:
            used_set = set(tools_used)
            expected_set = set(case.expected_tools)
            if expected_set:
                overlap = used_set & expected_set
                tool_score = len(overlap) / len(expected_set)
        else:
            tool_score = 1.0
        scores.append(tool_score)
        tool_weight = 0.2

        # 4. 步骤效率（权重 0.2）
        step_score = 1.0
        min_steps, max_steps = case.expected_steps_range
        if steps < min_steps:
            step_score = max(0.5, steps / min_steps)
        elif steps > max_steps:
            step_score = max(0.3, max_steps / steps)
        scores.append(step_score)
        step_weight = 0.2

        # 自定义验证器
        if case.validator:
            try:
                custom_score = case.validator(output, tools_used, steps)
                scores.append(custom_score)
                weights = [error_weight, output_weight, tool_weight, step_weight, 0.1]
                return sum(s * w for s, w in zip(scores, weights))
            except Exception:
                pass

        weights = [error_weight, output_weight, tool_weight, step_weight]
        return sum(s * w for s, w in zip(scores, weights))

    def _build_report(self, suite_name: str, results: List[EvalResult],
                      cases: List[EvalCase]) -> EvalReport:
        """构建评估报告"""
        case_map = {c.id: c for c in cases}
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed

        avg_score = sum(r.score for r in results) / max(len(results), 1)
        avg_steps = sum(r.actual_steps for r in results) / max(len(results), 1)
        avg_duration = sum(r.duration_ms for r in results) / max(len(results), 1)

        # 按难度统计
        by_difficulty: Dict[str, Dict] = {}
        for r in results:
            case = case_map.get(r.case_id)
            if not case:
                continue
            diff = case.difficulty.value
            if diff not in by_difficulty:
                by_difficulty[diff] = {"total": 0, "passed": 0, "pass_rate": 0.0, "avg_score": 0.0, "scores": []}
            by_difficulty[diff]["total"] += 1
            if r.passed:
                by_difficulty[diff]["passed"] += 1
            by_difficulty[diff]["scores"].append(r.score)

        for diff, stats in by_difficulty.items():
            stats["pass_rate"] = stats["passed"] / max(stats["total"], 1)
            stats["avg_score"] = sum(stats["scores"]) / max(len(stats["scores"]), 1)
            del stats["scores"]

        # 按类别统计
        by_category: Dict[str, Dict] = {}
        for r in results:
            case = case_map.get(r.case_id)
            if not case:
                continue
            cat = case.category
            if cat not in by_category:
                by_category[cat] = {"total": 0, "passed": 0, "pass_rate": 0.0, "avg_score": 0.0, "scores": []}
            by_category[cat]["total"] += 1
            if r.passed:
                by_category[cat]["passed"] += 1
            by_category[cat]["scores"].append(r.score)

        for cat, stats in by_category.items():
            stats["pass_rate"] = stats["passed"] / max(stats["total"], 1)
            stats["avg_score"] = sum(stats["scores"]) / max(len(stats["scores"]), 1)
            del stats["scores"]

        report = EvalReport(
            suite_name=suite_name,
            total_cases=len(results),
            passed=passed,
            failed=failed,
            avg_score=avg_score,
            avg_steps=avg_steps,
            avg_duration_ms=avg_duration,
            pass_rate=passed / max(len(results), 1),
            by_difficulty=by_difficulty,
            by_category=by_category,
            results=results,
        )

        # 持久化报告
        if self._report_dir:
            report_file = self._report_dir / f"eval_{suite_name}_{int(time.time())}.json"
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)

        return report


# ═══════════════════════════════════════════════
# 快捷接口
# ═══════════════════════════════════════════════

def run_quick_eval(agent_fn: Callable, suite_name: str = "quick",
                   report_dir: Optional[Path] = None) -> EvalReport:
    """快速评估 — 使用内置用例集"""
    runner = EvalRunner(agent_fn=agent_fn, report_dir=report_dir)
    cases = get_builtin_eval_cases()
    return runner.run_suite(cases, suite_name)
