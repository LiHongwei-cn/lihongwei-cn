"""工具注册表单元测试"""

import pytest
from mundo_agent.tools.registry import (
    ToolRegistry, ToolDefinition, ToolParameter,
    registry, execute_tool
)
from mundo_agent.utils.errors import ValidationError, ToolError


class TestToolParameter:
    """ToolParameter 测试"""

    def test_basic_creation(self):
        """测试基本创建"""
        param = ToolParameter("name", "string", "名称", required=True)
        assert param.name == "name"
        assert param.type == "string"
        assert param.description == "名称"
        assert param.required is True
        assert param.default is None
        assert param.enum is None

    def test_to_schema(self):
        """测试转换为 Schema"""
        param = ToolParameter("count", "integer", "数量", required=True)
        schema = param.to_schema()
        assert schema["type"] == "integer"
        assert schema["description"] == "数量"

    def test_to_schema_with_enum(self):
        """测试带枚举的 Schema"""
        param = ToolParameter("mode", "string", "模式", enum=["fast", "slow"])
        schema = param.to_schema()
        assert schema["enum"] == ["fast", "slow"]


class TestToolDefinition:
    """ToolDefinition 测试"""

    def test_basic_creation(self):
        """测试基本创建"""
        def handler(args):
            return "ok"

        tool = ToolDefinition(
            "test_tool",
            "测试工具",
            handler,
            [ToolParameter("input", "string", "输入", required=True)]
        )

        assert tool.name == "test_tool"
        assert tool.description == "测试工具"
        assert tool._required == ["input"]

    def test_to_schema(self):
        """测试转换为 Schema"""
        def handler(args):
            return "ok"

        tool = ToolDefinition(
            "test_tool",
            "测试工具",
            handler,
            [
                ToolParameter("input", "string", "输入", required=True),
                ToolParameter("count", "integer", "数量", default=10),
            ]
        )

        schema = tool.to_schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "test_tool"
        assert "input" in schema["function"]["parameters"]["required"]
        assert "count" not in schema["function"]["parameters"]["required"]

    def test_validate_args_success(self):
        """测试参数验证成功"""
        def handler(args):
            return "ok"

        tool = ToolDefinition(
            "test_tool",
            "测试工具",
            handler,
            [
                ToolParameter("name", "string", "名称", required=True),
                ToolParameter("count", "integer", "数量", default=10),
            ]
        )

        validated = tool.validate_args({"name": "test", "count": "5"})
        assert validated["name"] == "test"
        assert validated["count"] == 5

    def test_validate_args_missing_required(self):
        """测试缺少必需参数"""
        def handler(args):
            return "ok"

        tool = ToolDefinition(
            "test_tool",
            "测试工具",
            handler,
            [ToolParameter("name", "string", "名称", required=True)]
        )

        with pytest.raises(ValidationError) as exc_info:
            tool.validate_args({})
        assert "name" in str(exc_info.value)

    def test_validate_args_type_conversion(self):
        """测试类型转换"""
        def handler(args):
            return "ok"

        tool = ToolDefinition(
            "test_tool",
            "测试工具",
            handler,
            [
                ToolParameter("count", "integer", "数量"),
                ToolParameter("flag", "boolean", "标志"),
            ]
        )

        validated = tool.validate_args({"count": "42", "flag": "true"})
        assert validated["count"] == 42
        assert validated["flag"] is True

    def test_validate_args_enum(self):
        """测试枚举验证"""
        def handler(args):
            return "ok"

        tool = ToolDefinition(
            "test_tool",
            "测试工具",
            handler,
            [ToolParameter("mode", "string", "模式", enum=["fast", "slow"])]
        )

        validated = tool.validate_args({"mode": "fast"})
        assert validated["mode"] == "fast"

        with pytest.raises(ValidationError):
            tool.validate_args({"mode": "invalid"})


class TestToolRegistry:
    """ToolRegistry 测试"""

    def setup_method(self):
        """每个测试前重置单例"""
        ToolRegistry._instance = None

    def test_register_tool(self):
        """测试注册工具"""
        registry = ToolRegistry()

        def handler(args):
            return "ok"

        registry.register("test", "测试", handler)
        assert "test" in registry.names
        assert len(registry.schemas) == 1

    def test_execute_tool_success(self):
        """测试执行工具成功"""
        registry = ToolRegistry()

        def handler(args):
            return f"hello {args.get('name', 'world')}"

        registry.register("test", "测试", handler,
                         [ToolParameter("name", "string", "名称")])

        result = registry.execute("test", {"name": "mundo"})
        assert result == "hello mundo"

    def test_execute_tool_unknown(self):
        """测试执行未知工具"""
        registry = ToolRegistry()
        result = registry.execute("unknown", {})
        assert "未知工具" in result

    def test_execute_tool_validation_error(self):
        """测试参数验证错误"""
        registry = ToolRegistry()

        def handler(args):
            return "ok"

        registry.register("test", "测试", handler,
                         [ToolParameter("name", "string", "名称", required=True)])

        result = registry.execute("test", {})
        assert "参数错误" in result

    def test_execute_tool_handler_error(self):
        """测试处理器错误"""
        registry = ToolRegistry()

        def handler(args):
            raise ValueError("测试错误")

        registry.register("test", "测试", handler)

        result = registry.execute("test", {})
        assert "工具执行错误" in result

    def test_schemas_property(self):
        """测试 schemas 属性"""
        registry = ToolRegistry()

        def handler(args):
            return "ok"

        registry.register("test1", "测试1", handler)
        registry.register("test2", "测试2", handler)

        schemas = registry.schemas
        assert len(schemas) == 2
        assert all(s["type"] == "function" for s in schemas)


class TestExecuteToolFunction:
    """execute_tool 函数测试"""

    def test_execute_tool(self):
        """测试 execute_tool 函数"""
        # 注意：这里使用全局 registry，可能需要清理
        result = execute_tool("read_file", {"path": "/nonexistent"})
        assert "错误" in result or "不存在" in result