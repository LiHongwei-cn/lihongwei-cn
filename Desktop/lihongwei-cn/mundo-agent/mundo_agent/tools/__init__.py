"""蒙多工具模块 — 自动注册所有工具"""

from .registry import registry, execute_tool, register_tool, ToolParameter

# 导入所有工具模块（触发装饰器注册）
from . import file_ops
from . import terminal
from . import git_ops
from . import web
from . import code

# 导出
__all__ = [
    'registry',
    'execute_tool',
    'register_tool',
    'ToolParameter',
]