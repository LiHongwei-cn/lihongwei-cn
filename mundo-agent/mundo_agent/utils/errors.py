"""蒙多自定义异常 — 统一错误处理"""

from typing import Optional, Any


class MundoError(Exception):
    """MUNDO Agent 基础异常"""
    def __init__(self, message: str, code: str = "UNKNOWN", details: Any = None):
        super().__init__(message)
        self.code = code
        self.details = details


class LLMError(MundoError):
    """LLM 调用相关错误"""
    def __init__(self, message: str, code: str = "LLM_ERROR", status_code: Optional[int] = None):
        super().__init__(message, code)
        self.status_code = status_code


class ContextOverflowError(LLMError):
    """上下文溢出错误"""
    def __init__(self, message: str = "上下文过长", token_count: int = 0):
        super().__init__(message, "CONTEXT_OVERFLOW")
        self.token_count = token_count


class ToolError(MundoError):
    """工具执行错误"""
    def __init__(self, tool_name: str, message: str, original_error: Optional[Exception] = None):
        super().__init__(f"工具 {tool_name} 执行失败: {message}", "TOOL_ERROR")
        self.tool_name = tool_name
        self.original_error = original_error


class MemoryError(MundoError):
    """记忆系统错误"""
    def __init__(self, message: str, operation: str = ""):
        super().__init__(message, "MEMORY_ERROR")
        self.operation = operation


class ConfigError(MundoError):
    """配置错误"""
    def __init__(self, message: str, key: Optional[str] = None):
        super().__init__(message, "CONFIG_ERROR")
        self.key = key


class AgentError(MundoError):
    """Agent 执行错误"""
    def __init__(self, agent_name: str, message: str):
        super().__init__(f"[{agent_name}] {message}", "AGENT_ERROR")
        self.agent_name = agent_name


class NetworkError(MundoError):
    """网络请求错误"""
    def __init__(self, message: str, url: Optional[str] = None, status_code: Optional[int] = None):
        super().__init__(message, "NETWORK_ERROR")
        self.url = url
        self.status_code = status_code


class ValidationError(MundoError):
    """参数验证错误"""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field


# 错误码映射
ERROR_CODES = {
    "UNKNOWN": "未知错误",
    "LLM_ERROR": "LLM 调用错误",
    "CONTEXT_OVERFLOW": "上下文溢出",
    "TOOL_ERROR": "工具执行错误",
    "MEMORY_ERROR": "记忆系统错误",
    "CONFIG_ERROR": "配置错误",
    "AGENT_ERROR": "Agent 执行错误",
    "NETWORK_ERROR": "网络错误",
    "VALIDATION_ERROR": "参数验证错误",
}


def format_error(error: Exception) -> str:
    """格式化错误信息"""
    if isinstance(error, MundoError):
        code_desc = ERROR_CODES.get(error.code, error.code)
        return f"[{code_desc}] {error}"
    return f"[错误] {error}"