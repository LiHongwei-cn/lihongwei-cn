#!/usr/bin/env python3
"""蒙多 v2.0.8 全面测试套件 — 测试所有模块的功能和稳定性

运行方式：
    cd mundo-agent
    python test_mundo.py          # 全量测试
    python test_mundo.py -v       # 详细输出
    python test_mundo.py tools    # 只测 tools
    python test_mundo.py llm      # 只测 llm
    python test_mundo.py core     # 只测 core
    python test_mundo.py approval # 只测 approval
    python test_mundo.py models   # 只测 models
"""

import os
import sys
import json
import time
import tempfile
import traceback
import subprocess
from pathlib import Path
from typing import List, Dict, Callable, Tuple, Optional

# ═══════════════════════════════════════════════
# 测试框架 — 极简
# ═══════════════════════════════════════════════

class TestResult:
    def __init__(self, name: str, passed: bool, detail: str = ""):
        self.name = name
        self.passed = passed
        self.detail = detail

    def __repr__(self):
        status = "✅" if self.passed else "❌"
        s = f"  {status} {self.name}"
        if self.detail and not self.passed:
            s += f"\n     ↳ {self.detail}"
        return s


class TestSuite:
    def __init__(self, name: str):
        self.name = name
        self.results: List[TestResult] = []
        self._current_test = ""

    def run(self, test_func: Callable, name: str = None):
        name = name or test_func.__name__
        self._current_test = name
        try:
            test_func()
            self.results.append(TestResult(name, True))
        except AssertionError as e:
            self.results.append(TestResult(name, False, str(e)))
        except Exception as e:
            self.results.append(TestResult(name, False, f"异常: {type(e).__name__}: {e}"))

    def assert_eq(self, actual, expected, msg=""):
        if actual != expected:
            raise AssertionError(f"{msg}期望 {expected!r}, 实际 {actual!r}")

    def assert_true(self, val, msg=""):
        if not val:
            raise AssertionError(f"{msg}期望 True, 实际 {val!r}")

    def assert_false(self, val, msg=""):
        if val:
            raise AssertionError(f"{msg}期望 False, 实际 {val!r}")

    def assert_in(self, needle, haystack, msg=""):
        if needle not in haystack:
            raise AssertionError(f"{msg}{needle!r} 不在 {haystack!r} 中")

    def assert_not_in(self, needle, haystack, msg=""):
        if needle in haystack:
            raise AssertionError(f"{msg}{needle!r} 不应在 {haystack!r} 中")

    def assert_isinstance(self, obj, cls, msg=""):
        if not isinstance(obj, cls):
            raise AssertionError(f"{msg}期望 {cls.__name__}, 实际 {type(obj).__name__}")

    def assert_gt(self, a, b, msg=""):
        if not (a > b):
            raise AssertionError(f"{msg}期望 {a} > {b}")

    def assert_gte(self, a, b, msg=""):
        if not (a >= b):
            raise AssertionError(f"{msg}期望 {a} >= {b}")

    def assert_lt(self, a, b, msg=""):
        if not (a < b):
            raise AssertionError(f"{msg}期望 {a} < {b}")

    def assert_contains(self, text, substring, msg=""):
        if substring not in text:
            raise AssertionError(f"{msg}'{substring}' 不在文本中")

    def summary(self) -> Tuple[int, int, str]:
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        lines = [f"\n{'='*50}", f"📊 {self.name}: {passed}/{total} 通过"]
        for r in self.results:
            lines.append(str(r))
        if passed < total:
            lines.append(f"\n⚠️ {total - passed} 个测试失败")
        else:
            lines.append(f"\n✅ 全部通过！")
        return passed, total, "\n".join(lines)


# ═══════════════════════════════════════════════
# 工具函数测试
# ═══════════════════════════════════════════════

def test_tools(suite: TestSuite):
    """测试 tools.py 所有工具"""

    # ─── ToolRegistry 基础 ───

    def test_registry_basics():
        from tools import ToolRegistry
        reg = ToolRegistry()
        reg.register("test_tool", "测试工具", {"type": "object", "properties": {}},
                      lambda args: "ok", required=[])
        suite.assert_eq(len(reg.names), 1)
        suite.assert_in("test_tool", reg.names)
        suite.assert_eq(len(reg.schemas), 1)
        suite.assert_eq(reg.schemas[0]["function"]["name"], "test_tool")

    def test_registry_execute():
        from tools import ToolRegistry
        reg = ToolRegistry()
        reg.register("echo", "回显", {"type": "object", "properties": {}},
                      lambda args: f"echo:{args.get('x', '')}")
        result = reg.execute("echo", {"x": "hello"})
        suite.assert_eq(result, "echo:hello")

    def test_registry_unknown_tool():
        from tools import ToolRegistry
        reg = ToolRegistry()
        result = reg.execute("nonexistent", {})
        suite.assert_in("未知工具", result)

    def test_registry_handler_exception():
        from tools import ToolRegistry
        reg = ToolRegistry()
        reg.register("boom", "爆炸", {"type": "object", "properties": {}},
                      lambda args: 1/0)
        result = reg.execute("boom", {})
        suite.assert_in("执行失败", result)

    def test_registry_non_dict_args():
        from tools import ToolRegistry
        reg = ToolRegistry()
        reg.register("test", "t", {"type": "object", "properties": {}},
                      lambda args: f"type:{type(args).__name__}")
        result = reg.execute("test", "not_a_dict")
        suite.assert_in("dict", result)

    def test_global_registry_has_all_tools():
        from tools import registry
        expected = ["terminal", "read_file", "write_file", "edit_file",
                    "search_files", "web_search", "list_directory",
                    "git_operation", "python_execute", "http_request",
                    "json_process", "code_analysis"]
        for name in expected:
            suite.assert_in(name, registry.names, f"缺少工具 {name}: ")
        suite.assert_gte(len(registry.names), 12)

    def test_global_registry_schemas_valid():
        from tools import registry
        for schema in registry.schemas:
            suite.assert_eq(schema["type"], "function")
            func = schema["function"]
            suite.assert_true("name" in func)
            suite.assert_true("description" in func)
            suite.assert_true("parameters" in func)

    # ─── _truncate ───

    def test_truncate_short():
        from tools import _truncate
        result = _truncate("hello")
        suite.assert_eq(result, "hello")

    def test_truncate_long():
        from tools import _truncate
        long_text = "a" * 10000
        result = _truncate(long_text, limit=100)
        suite.assert_lt(len(result), 200)
        suite.assert_in("省略中间部分", result)

    def test_truncate_zero_limit():
        from tools import _truncate
        long_text = "a" * 300
        result = _truncate(long_text, limit=0)
        suite.assert_in("...", result)

    # ─── terminal ───

    def test_terminal_basic():
        from tools import registry
        result = registry.execute("terminal", {"command": "echo hello_mundo"})
        suite.assert_in("hello_mundo", result)

    def test_terminal_missing_command():
        from tools import registry
        result = registry.execute("terminal", {})
        suite.assert_in("错误", result)
        suite.assert_in("command", result)

    def test_terminal_stderr():
        from tools import registry
        result = registry.execute("terminal", {"command": "echo err >&2"})
        suite.assert_in("stderr", result)

    def test_terminal_exit_code():
        from tools import registry
        result = registry.execute("terminal", {"command": "exit 1"})
        suite.assert_in("exit code: 1", result)

    def test_terminal_command_not_found():
        from tools import registry
        result = registry.execute("terminal", {"command": "nonexistent_cmd_xyz"})
        suite.assert_in("命令未找到", result)

    def test_terminal_workdir():
        from tools import registry
        result = registry.execute("terminal", {"command": "pwd", "workdir": "/tmp"})
        suite.assert_in("/tmp", result)

    # ─── read_file ───

    def test_read_file_basic():
        from tools import registry
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("line1\nline2\nline3")
            path = f.name
        try:
            result = registry.execute("read_file", {"path": path})
            suite.assert_in("line1", result)
            suite.assert_in("line2", result)
            suite.assert_in("line3", result)
            suite.assert_in("共 3 行", result)
        finally:
            os.unlink(path)

    def test_read_file_offset_limit():
        from tools import registry
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            for i in range(20):
                f.write(f"line{i+1}\n")
            path = f.name
        try:
            result = registry.execute("read_file", {"path": path, "offset": 5, "limit": 3})
            suite.assert_in("line5", result)
            suite.assert_in("line7", result)
            suite.assert_not_in("line1\n", result)
        finally:
            os.unlink(path)

    def test_read_file_missing_path():
        from tools import registry
        result = registry.execute("read_file", {})
        suite.assert_in("错误", result)

    def test_read_file_not_found():
        from tools import registry
        result = registry.execute("read_file", {"path": "/nonexistent/file.txt"})
        suite.assert_in("文件不存在", result)

    def test_read_file_is_directory():
        from tools import registry
        result = registry.execute("read_file", {"path": "/tmp"})
        suite.assert_in("是目录不是文件", result)

    # ─── write_file ───

    def test_write_file_basic():
        from tools import registry
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "test.txt")
            result = registry.execute("write_file", {"path": path, "content": "hello mundo"})
            suite.assert_in("✓", result)
            with open(path) as f:
                suite.assert_eq(f.read(), "hello mundo")

    def test_write_file_creates_dirs():
        from tools import registry
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "sub", "dir", "file.txt")
            result = registry.execute("write_file", {"path": path, "content": "deep"})
            suite.assert_in("✓", result)
            suite.assert_true(os.path.exists(path))

    def test_write_file_missing_path():
        from tools import registry
        result = registry.execute("write_file", {"content": "x"})
        suite.assert_in("错误", result)

    def test_write_file_missing_content():
        from tools import registry
        result = registry.execute("write_file", {"path": "/tmp/test_write_empty"})
        suite.assert_in("错误", result)

    # ─── edit_file ───

    def test_edit_file_basic():
        from tools import registry
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello world")
            path = f.name
        try:
            result = registry.execute("edit_file", {
                "path": path, "old_string": "world", "new_string": "mundo"
            })
            suite.assert_in("✓", result)
            with open(path) as f:
                suite.assert_eq(f.read(), "hello mundo")
        finally:
            os.unlink(path)

    def test_edit_file_not_found_string():
        from tools import registry
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello world")
            path = f.name
        try:
            result = registry.execute("edit_file", {
                "path": path, "old_string": "not_exist", "new_string": "x"
            })
            suite.assert_in("未找到", result)
        finally:
            os.unlink(path)

    def test_edit_file_missing_params():
        from tools import registry
        result = registry.execute("edit_file", {"path": "/tmp/x"})
        suite.assert_in("错误", result)

    # ─── list_directory ───

    def test_list_directory_basic():
        from tools import registry
        result = registry.execute("list_directory", {"path": "/tmp"})
        suite.assert_in("目录:", result)

    def test_list_directory_not_exist():
        from tools import registry
        result = registry.execute("list_directory", {"path": "/nonexistent_dir"})
        suite.assert_in("不是目录", result)

    # ─── search_files ───

    def test_search_files_content():
        from tools import registry
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "test.py"), "w") as f:
                f.write("def hello_mundo():\n    pass\n")
            result = registry.execute("search_files", {
                "pattern": "hello_mundo", "path": d, "target": "content"
            })
            suite.assert_in("hello_mundo", result)

    def test_search_files_by_name():
        from tools import registry
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "unique_xyz.py"), "w") as f:
                f.write("x = 1\n")
            result = registry.execute("search_files", {
                "pattern": "unique_xyz", "path": d, "target": "files"
            })
            suite.assert_in("unique_xyz", result)

    def test_search_files_no_match():
        from tools import registry
        with tempfile.TemporaryDirectory() as d:
            result = registry.execute("search_files", {
                "pattern": "zzz_nonexistent", "path": d, "target": "content"
            })
            suite.assert_in("未找到", result)

    def test_search_files_missing_pattern():
        from tools import registry
        result = registry.execute("search_files", {})
        suite.assert_in("错误", result)

    # ─── git_operation ───

    def test_git_status():
        from tools import registry
        result = registry.execute("git_operation", {
            "operation": "status",
            "workdir": os.path.dirname(os.path.abspath(__file__))
        })
        # 应该能执行（不管输出内容）
        suite.assert_true(len(result) > 0, "git status 应有输出: ")

    def test_git_log():
        from tools import registry
        result = registry.execute("git_operation", {
            "operation": "log",
            "workdir": os.path.dirname(os.path.abspath(__file__))
        })
        suite.assert_true(len(result) > 0, "git log 应有输出: ")

    def test_git_current_branch():
        from tools import registry
        result = registry.execute("git_operation", {
            "operation": "current_branch",
            "workdir": os.path.dirname(os.path.abspath(__file__))
        })
        suite.assert_true(len(result) > 0, "git current_branch 应有输出: ")

    def test_git_missing_operation():
        from tools import registry
        result = registry.execute("git_operation", {})
        suite.assert_in("错误", result)

    def test_git_unknown_operation():
        from tools import registry
        result = registry.execute("git_operation", {"operation": "fake_op"})
        suite.assert_in("错误", result)

    # ─── python_execute ───

    def test_python_execute_basic():
        from tools import registry
        result = registry.execute("python_execute", {"code": "print(2+3)"})
        suite.assert_in("5", result)

    def test_python_execute_import():
        from tools import registry
        result = registry.execute("python_execute", {"code": "import json; print(json.dumps({'a':1}))"})
        suite.assert_in('"a"', result)

    def test_python_execute_error():
        from tools import registry
        result = registry.execute("python_execute", {"code": "1/0"})
        suite.assert_in("stderr", result)

    def test_python_execute_missing_code():
        from tools import registry
        result = registry.execute("python_execute", {})
        suite.assert_in("错误", result)

    # ─── json_process ───

    def test_json_parse():
        from tools import registry
        result = registry.execute("json_process", {"data": '{"a": 1, "b": 2}'})
        suite.assert_in('"a"', result)

    def test_json_keys():
        from tools import registry
        result = registry.execute("json_process", {"data": '{"x": 1, "y": 2}', "operation": "keys"})
        suite.assert_in("x", result)
        suite.assert_in("y", result)

    def test_json_path():
        from tools import registry
        result = registry.execute("json_process", {
            "data": '{"a": {"b": {"c": 42}}}', "operation": "path", "path": "a.b.c"
        })
        suite.assert_in("42", result)

    def test_json_validate():
        from tools import registry
        result = registry.execute("json_process", {"data": "[1,2,3]", "operation": "validate"})
        suite.assert_in("有效", result)

    # ─── 运行所有工具测试 ───

    suite.run(test_registry_basics, "ToolRegistry 基础")
    suite.run(test_registry_execute, "ToolRegistry 执行")
    suite.run(test_registry_unknown_tool, "ToolRegistry 未知工具")
    suite.run(test_registry_handler_exception, "ToolRegistry 异常处理")
    suite.run(test_registry_non_dict_args, "ToolRegistry 非字典参数")
    suite.run(test_global_registry_has_all_tools, "全局注册表完整性")
    suite.run(test_global_registry_schemas_valid, "全局注册表 Schema")
    suite.run(test_truncate_short, "truncate 短文本")
    suite.run(test_truncate_long, "truncate 长文本")
    suite.run(test_truncate_zero_limit, "truncate 零限制")
    suite.run(test_terminal_basic, "terminal 基础")
    suite.run(test_terminal_missing_command, "terminal 缺少命令")
    suite.run(test_terminal_stderr, "terminal stderr")
    suite.run(test_terminal_exit_code, "terminal 退出码")
    suite.run(test_terminal_command_not_found, "terminal 命令不存在")
    suite.run(test_terminal_workdir, "terminal 工作目录")
    suite.run(test_read_file_basic, "read_file 基础")
    suite.run(test_read_file_offset_limit, "read_file 行范围")
    suite.run(test_read_file_missing_path, "read_file 缺少路径")
    suite.run(test_read_file_not_found, "read_file 文件不存在")
    suite.run(test_read_file_is_directory, "read_file 目录")
    suite.run(test_write_file_basic, "write_file 基础")
    suite.run(test_write_file_creates_dirs, "write_file 创建目录")
    suite.run(test_write_file_missing_path, "write_file 缺少路径")
    suite.run(test_write_file_missing_content, "write_file 缺少内容")
    suite.run(test_edit_file_basic, "edit_file 基础")
    suite.run(test_edit_file_not_found_string, "edit_file 未找到字符串")
    suite.run(test_edit_file_missing_params, "edit_file 缺少参数")
    suite.run(test_list_directory_basic, "list_directory 基础")
    suite.run(test_list_directory_not_exist, "list_directory 不存在")
    suite.run(test_search_files_content, "search_files 内容搜索")
    suite.run(test_search_files_by_name, "search_files 文件名搜索")
    suite.run(test_search_files_no_match, "search_files 无匹配")
    suite.run(test_search_files_missing_pattern, "search_files 缺少模式")
    suite.run(test_git_status, "git status")
    suite.run(test_git_log, "git log")
    suite.run(test_git_current_branch, "git current_branch")
    suite.run(test_git_missing_operation, "git 缺少操作")
    suite.run(test_git_unknown_operation, "git 未知操作")
    suite.run(test_python_execute_basic, "python_execute 基础")
    suite.run(test_python_execute_import, "python_execute import")
    suite.run(test_python_execute_error, "python_execute 错误")
    suite.run(test_python_execute_missing_code, "python_execute 缺少代码")
    suite.run(test_json_parse, "json parse")
    suite.run(test_json_keys, "json keys")
    suite.run(test_json_path, "json path")
    suite.run(test_json_validate, "json validate")


# ═══════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    suite = TestSuite("蒙多 Agent v2.0.8 测试")
    test_tools(suite)
    passed, total, summary = suite.summary()
    print(summary)
    sys.exit(0 if passed == total else 1)