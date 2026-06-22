"""评估引擎单元测试"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestEvalCase:
    """EvalCase 测试"""

    def test_creation(self):
        from eval_engine import EvalCase, TaskDifficulty
        case = EvalCase(
            id="test-001",
            name="test case",
            description="A test case",
            input_prompt="do something",
            expected_output="result",
            expected_tools=["tool_a"],
            difficulty=TaskDifficulty.EASY,
        )
        assert case.id == "test-001"
        assert case.difficulty == TaskDifficulty.EASY

    def test_to_dict(self):
        from eval_engine import EvalCase, TaskDifficulty
        case = EvalCase(
            id="t1", name="n", description="d", input_prompt="p",
            difficulty=TaskDifficulty.MEDIUM,
        )
        d = case.to_dict()
        assert d["id"] == "t1"
        assert d["difficulty"] == "medium"


class TestEvalResult:
    """EvalResult 测试"""

    def test_creation(self):
        from eval_engine import EvalResult
        result = EvalResult(
            case_id="t1", passed=True, score=0.9,
            actual_steps=3, actual_tools_used=["read_file"],
        )
        assert result.passed is True
        assert result.score == 0.9

    def test_to_dict(self):
        from eval_engine import EvalResult
        result = EvalResult(case_id="t1", passed=False, score=0.2, error="fail")
        d = result.to_dict()
        assert d["case_id"] == "t1"
        assert d["error"] == "fail"


class TestEvalRunner:
    """EvalRunner 测试"""

    def test_run_with_mock_agent(self):
        from eval_engine import EvalRunner, EvalCase, TaskDifficulty

        def mock_agent(prompt):
            return {
                "output": "v2.2.7",
                "steps": 2,
                "tools_used": ["read_file"],
                "error": "",
            }

        runner = EvalRunner(agent_fn=mock_agent)
        case = EvalCase(
            id="t1", name="test", description="d",
            input_prompt="read VERSION",
            expected_output="v2.2.7",
            expected_tools=["read_file"],
            expected_steps_range=(1, 5),
            difficulty=TaskDifficulty.EASY,
            category="tool_use",
        )

        result = runner.run_single(case)
        assert result.passed is True
        assert result.score > 0.5

    def test_run_suite(self):
        from eval_engine import EvalRunner, EvalCase, TaskDifficulty

        def mock_agent(prompt):
            return {"output": "ok", "steps": 1, "tools_used": ["terminal"], "error": ""}

        runner = EvalRunner(agent_fn=mock_agent)
        cases = [
            EvalCase(id=f"t{i}", name=f"t{i}", description="d", input_prompt="p",
                     difficulty=TaskDifficulty.EASY, category="basic")
            for i in range(5)
        ]

        report = runner.run_suite(cases, "test_suite")
        assert report.total_cases == 5
        assert report.passed + report.failed == 5
        assert report.pass_rate >= 0

    def test_no_agent_fn(self):
        from eval_engine import EvalRunner, EvalCase
        runner = EvalRunner(agent_fn=None)
        case = EvalCase(id="t1", name="n", description="d", input_prompt="p")
        result = runner.run_single(case)
        assert result.passed is False
        assert "No agent" in result.error

    def test_agent_exception(self):
        from eval_engine import EvalRunner, EvalCase

        def bad_agent(prompt):
            raise RuntimeError("agent crashed")

        runner = EvalRunner(agent_fn=bad_agent)
        case = EvalCase(id="t1", name="n", description="d", input_prompt="p")
        result = runner.run_single(case)
        assert result.passed is False
        assert "crashed" in result.error

    def test_report_summary(self):
        from eval_engine import EvalRunner, EvalCase, TaskDifficulty

        def mock_agent(prompt):
            return {"output": "v2.2.7", "steps": 2, "tools_used": ["read_file"], "error": ""}

        runner = EvalRunner(agent_fn=mock_agent)
        cases = [
            EvalCase(id="t1", name="n", description="d", input_prompt="p",
                     expected_output="v2.2.7", difficulty=TaskDifficulty.EASY, category="tool"),
        ]

        report = runner.run_suite(cases, "summary_test")
        summary = report.summary()
        assert "summary_test" in summary
        assert "通过率" in summary


class TestBuiltinCases:
    """内置评估用例测试"""

    def test_get_builtin_cases(self):
        from eval_engine import get_builtin_eval_cases
        cases = get_builtin_eval_cases()
        assert len(cases) > 0

    def test_cases_have_required_fields(self):
        from eval_engine import get_builtin_eval_cases
        for case in get_builtin_eval_cases():
            assert case.id
            assert case.name
            assert case.input_prompt
            assert case.difficulty
            assert case.category

    def test_cases_unique_ids(self):
        from eval_engine import get_builtin_eval_cases
        cases = get_builtin_eval_cases()
        ids = [c.id for c in cases]
        assert len(ids) == len(set(ids))
