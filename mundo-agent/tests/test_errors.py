"""错误处理单元测试"""

import pytest
from mundo_agent.utils.errors import (
    MundoError, LLMError, ContextOverflowError, ToolError,
    MemoryError, ConfigError, AgentError, NetworkError,
    ValidationError, format_error, ERROR_CODES
)


class TestMundoError:
    """MundoError 测试"""

    def test_basic_creation(self):
        """测试基本创建"""
        error = MundoError("测试错误")
        assert str(error) == "测试错误"
        assert error.code == "UNKNOWN"
        assert error.details is None

    def test_with_code(self):
        """测试带错误码"""
        error = MundoError("测试错误", code="TEST_ERROR")
        assert error.code == "TEST_ERROR"

    def test_with_details(self):
        """测试带详情"""
        details = {"key": "value"}
        error = MundoError("测试错误", details=details)
        assert error.details == details


class TestLLMError:
    """LLMError 测试"""

    def test_basic_creation(self):
        """测试基本创建"""
        error = LLMError("LLM 错误")
        assert str(error) == "LLM 错误"
        assert error.code == "LLM_ERROR"
        assert error.status_code is None

    def test_with_status_code(self):
        """测试带状态码"""
        error = LLMError("API 错误", status_code=429)
        assert error.status_code == 429


class TestContextOverflowError:
    """ContextOverflowError 测试"""

    def test_basic_creation(self):
        """测试基本创建"""
        error = ContextOverflowError()
        assert "上下文过长" in str(error)
        assert error.code == "CONTEXT_OVERFLOW"
        assert error.token_count == 0

    def test_with_token_count(self):
        """测试带 token 数量"""
        error = ContextOverflowError(token_count=100000)
        assert error.token_count == 100000


class TestToolError:
    """ToolError 测试"""

    def test_basic_creation(self):
        """测试基本创建"""
        error = ToolError("terminal", "命令执行失败")
        assert "terminal" in str(error)
        assert "命令执行失败" in str(error)
        assert error.code == "TOOL_ERROR"
        assert error.tool_name == "terminal"

    def test_with_original_error(self):
        """测试带原始错误"""
        original = ValueError("原始错误")
        error = ToolError("test", "测试错误", original)
        assert error.original_error == original


class TestMemoryError:
    """MemoryError 测试"""

    def test_basic_creation(self):
        """测试基本创建"""
        error = MemoryError("数据库错误")
        assert str(error) == "数据库错误"
        assert error.code == "MEMORY_ERROR"
        assert error.operation == ""

    def test_with_operation(self):
        """测试带操作"""
        error = MemoryError("查询失败", operation="recall")
        assert error.operation == "recall"


class TestConfigError:
    """ConfigError 测试"""

    def test_basic_creation(self):
        """测试基本创建"""
        error = ConfigError("配置错误")
        assert str(error) == "配置错误"
        assert error.code == "CONFIG_ERROR"
        assert error.key is None

    def test_with_key(self):
        """测试带配置键"""
        error = ConfigError("缺少配置", key="API_KEY")
        assert error.key == "API_KEY"


class TestAgentError:
    """AgentError 测试"""

    def test_basic_creation(self):
        """测试基本创建"""
        error = AgentError("claude", "Agent 执行失败")
        assert "claude" in str(error)
        assert "Agent 执行失败" in str(error)
        assert error.code == "AGENT_ERROR"
        assert error.agent_name == "claude"


class TestNetworkError:
    """NetworkError 测试"""

    def test_basic_creation(self):
        """测试基本创建"""
        error = NetworkError("网络错误")
        assert str(error) == "网络错误"
        assert error.code == "NETWORK_ERROR"
        assert error.url is None
        assert error.status_code is None

    def test_with_url(self):
        """测试带 URL"""
        error = NetworkError("连接失败", url="https://api.example.com")
        assert error.url == "https://api.example.com"

    def test_with_status_code(self):
        """测试带状态码"""
        error = NetworkError("请求失败", status_code=500)
        assert error.status_code == 500


class TestValidationError:
    """ValidationError 测试"""

    def test_basic_creation(self):
        """测试基本创建"""
        error = ValidationError("参数无效")
        assert str(error) == "参数无效"
        assert error.code == "VALIDATION_ERROR"
        assert error.field is None

    def test_with_field(self):
        """测试带字段"""
        error = ValidationError("缺少必需参数", field="name")
        assert error.field == "name"


class TestFormatError:
    """format_error 函数测试"""

    def test_format_mundo_error(self):
        """测试格式化 MundoError"""
        error = LLMError("测试错误")
        formatted = format_error(error)
        assert "LLM 调用错误" in formatted
        assert "测试错误" in formatted

    def test_format_generic_error(self):
        """测试格式化普通错误"""
        error = ValueError("普通错误")
        formatted = format_error(error)
        assert "错误" in formatted
        assert "普通错误" in formatted


class TestErrorCodes:
    """ERROR_CODES 测试"""

    def test_all_codes_present(self):
        """测试所有错误码都存在"""
        expected_codes = [
            "UNKNOWN", "LLM_ERROR", "CONTEXT_OVERFLOW", "TOOL_ERROR",
            "MEMORY_ERROR", "CONFIG_ERROR", "AGENT_ERROR",
            "NETWORK_ERROR", "VALIDATION_ERROR"
        ]
        for code in expected_codes:
            assert code in ERROR_CODES

    def test_code_values(self):
        """测试错误码值"""
        assert ERROR_CODES["UNKNOWN"] == "未知错误"
        assert ERROR_CODES["LLM_ERROR"] == "LLM 调用错误"
        assert ERROR_CODES["TOOL_ERROR"] == "工具执行错误"