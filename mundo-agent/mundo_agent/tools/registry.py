"""蒙多工具注册表 — 重构版

改进：
- 统一错误处理
- 参数验证
- 结果缓存
- 性能监控
"""

from typing import Dict, Any, Callable, List, Optional
from ..utils.errors import ToolError, ValidationError
from ..utils.logging import get_tool_logger

logger = get_tool_logger()


class ToolParameter:
    """工具参数定义"""

    def __init__(self, name: str, type: str, description: str = "",
                 required: bool = False, default: Any = None, enum: List = None):
        self.name = name
        self.type = type
        self.description = description
        self.required = required
        self.default = default
        self.enum = enum

    def to_schema(self) -> Dict:
        """转换为 JSON Schema"""
        schema = {
            "type": self.type,
            "description": self.description,
        }
        if self.enum:
            schema["enum"] = self.enum
        return schema


class ToolDefinition:
    """工具定义"""

    def __init__(self, name: str, description: str, handler: Callable,
                 parameters: List[ToolParameter] = None):
        self.name = name
        self.description = description
        self.handler = handler
        self.parameters = parameters or []
        self._required = [p.name for p in self.parameters if p.required]

    def to_schema(self) -> Dict:
        """转换为 OpenAI Function Schema"""
        properties = {}
        for param in self.parameters:
            properties[param.name] = param.to_schema()

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": self._required,
                },
            },
        }

    def validate_args(self, args: Dict) -> Dict:
        """验证参数"""
        validated = {}
        for param in self.parameters:
            if param.name in args:
                value = args[param.name]
                # 简单类型检查
                if param.type == "string" and not isinstance(value, str):
                    try:
                        value = str(value)
                    except (ValueError, TypeError):
                        raise ValidationError(f"参数 {param.name} 必须是字符串", param.name)
                elif param.type == "integer":
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        raise ValidationError(f"参数 {param.name} 必须是整数", param.name)
                elif param.type == "boolean":
                    if isinstance(value, str):
                        value = value.lower() in ("true", "1", "yes")
                    else:
                        value = bool(value)
                elif param.type == "number":
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        raise ValidationError(f"参数 {param.name} 必须是数字", param.name)

                if param.enum and value not in param.enum:
                    raise ValidationError(
                        f"参数 {param.name} 必须是 {param.enum} 之一", param.name
                    )

                validated[param.name] = value
            elif param.required:
                if param.default is not None:
                    validated[param.name] = param.default
                else:
                    raise ValidationError(f"缺少必需参数: {param.name}", param.name)
            elif param.default is not None:
                validated[param.name] = param.default

        return validated


class ToolRegistry:
    """工具注册表"""

    _instance: Optional['ToolRegistry'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: Dict[str, ToolDefinition] = {}
            cls._instance._schema_cache: Optional[List[Dict]] = None
        return cls._instance

    def register(self, name: str, description: str, handler: Callable,
                 parameters: List[ToolParameter] = None):
        """注册工具"""
        tool = ToolDefinition(name, description, handler, parameters)
        self._tools[name] = tool
        self._schema_cache = None  # 失效缓存
        logger.debug(f"注册工具: {name}")

    @property
    def schemas(self) -> List[Dict]:
        """获取所有工具的 Schema（缓存）"""
        if self._schema_cache is None:
            self._schema_cache = [tool.to_schema() for tool in self._tools.values()]
        return self._schema_cache

    @property
    def names(self) -> List[str]:
        """获取所有工具名称"""
        return list(self._tools.keys())

    def execute(self, name: str, args: Dict) -> str:
        """执行工具"""
        tool = self._tools.get(name)
        if not tool:
            return f"[错误: 未知工具 {name}]"

        if not isinstance(args, dict):
            args = {}

        try:
            # 验证参数
            validated_args = tool.validate_args(args)

            # 执行工具
            logger.debug(f"执行工具: {name}({validated_args})")
            result = tool.handler(validated_args)

            if isinstance(result, str) and "缺少" in result:
                req = tool._required
                if req:
                    result += f"\n正确用法: {name}({', '.join(req)})"

            return result

        except ValidationError as e:
            return f"[参数错误] {e}"
        except ToolError as e:
            return f"[工具错误] {e}"
        except Exception as e:
            logger.error(f"工具 {name} 执行异常: {e}", exc_info=True)
            return f"[工具执行错误: {name}: {e}]"


# 全局注册表实例
registry = ToolRegistry()


def register_tool(name: str, description: str, parameters: List[ToolParameter] = None):
    """工具注册装饰器"""
    def decorator(handler):
        registry.register(name, description, handler, parameters)
        return handler
    return decorator


def execute_tool(name: str, args: Dict) -> str:
    """执行工具（兼容旧接口）"""
    return registry.execute(name, args)