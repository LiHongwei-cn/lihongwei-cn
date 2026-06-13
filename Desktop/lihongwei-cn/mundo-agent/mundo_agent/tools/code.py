"""蒙多代码工具 — 重构版

改进：
- 安全沙箱
- 更好的错误处理
- 性能分析
"""

import os
import re
import json
import subprocess
import tempfile
from typing import Dict, List

from .registry import register_tool, ToolParameter
from ..utils.errors import ToolError, ValidationError
from ..utils.logging import get_tool_logger

logger = get_tool_logger()

# 危险代码模式
DANGEROUS_PATTERNS = [
    "os.system",
    "subprocess",
    "shutil.rmtree",
    "os.remove",
    "open('/etc",
    "open('/proc",
    "open('/sys",
    "import ctypes",
    "exec(",
    "eval(",
    "__import__",
    "globals()",
    "locals()",
]


def _is_dangerous_code(code: str) -> bool:
    """检查代码是否危险"""
    for pattern in DANGEROUS_PATTERNS:
        if pattern in code:
            return True
    return False


@register_tool(
    name="python_execute",
    description="安全执行 Python 代码。支持代码执行、数据分析、算法测试等。",
    parameters=[
        ToolParameter("code", "string", "要执行的 Python 代码", required=True),
        ToolParameter("timeout", "integer", "超时秒数（默认 30）", default=30),
        ToolParameter("workdir", "string", "工作目录（默认当前目录）"),
    ]
)
def python_execute(args: Dict) -> str:
    """执行 Python 代码"""
    code = args.get("code", "")
    if not code:
        raise ValidationError("缺少 code 参数", "code")

    # 安全检查
    if _is_dangerous_code(code):
        raise ToolError("python_execute", "代码包含危险操作，拒绝执行")

    timeout = args.get("timeout", 30)
    workdir = args.get("workdir") or os.getcwd()

    temp_path = None
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, dir=workdir
        ) as f:
            f.write(code)
            temp_path = f.name

        logger.debug(f"执行 Python 代码: {temp_path}")

        # 执行代码
        result = subprocess.run(
            ["python3", temp_path],
            capture_output=True, text=True,
            timeout=timeout, cwd=workdir,
        )

        output = result.stdout

        if result.stderr:
            output += f"\n[stderr]\n{result.stderr[:2000]}"

        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"

        return output or "(无输出)"

    except subprocess.TimeoutExpired:
        raise ToolError("python_execute", f"代码执行超过 {timeout} 秒")
    except Exception as e:
        raise ToolError("python_execute", f"执行失败: {e}")
    finally:
        # 清理临时文件
        if temp_path:
            try:
                os.unlink(temp_path)
            except Exception:
                pass


@register_tool(
    name="json_process",
    description="JSON 数据处理工具。支持解析、查询、验证等操作。",
    parameters=[
        ToolParameter("data", "string", "JSON 数据（字符串或对象）", required=True),
        ToolParameter("operation", "string", "操作类型（默认 parse）", default="parse",
                     enum=["parse", "keys", "path", "validate"]),
        ToolParameter("path", "string", "JSON 路径（path 操作需要，如 'a.b.c'）"),
    ]
)
def json_process(args: Dict) -> str:
    """处理 JSON 数据"""
    data = args.get("data", "")
    operation = args.get("operation", "parse")

    if not data:
        raise ValidationError("缺少 data 参数", "data")

    try:
        # 解析 JSON
        if isinstance(data, str):
            json_data = json.loads(data)
        else:
            json_data = data

        # 执行操作
        if operation == "parse":
            return json.dumps(json_data, indent=2, ensure_ascii=False)[:5000]

        elif operation == "keys":
            if isinstance(json_data, dict):
                return "Keys: " + ", ".join(json_data.keys())
            elif isinstance(json_data, list):
                return f"Array with {len(json_data)} items"
            else:
                return f"Type: {type(json_data).__name__}"

        elif operation == "path":
            path = args.get("path", "")
            if not path:
                raise ValidationError("path 操作需要 path 参数", "path")

            keys = path.split(".")
            current = json_data

            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key)
                elif isinstance(current, list):
                    try:
                        current = current[int(key)]
                    except (ValueError, IndexError):
                        raise ToolError("json_process", f"无法访问数组索引: {key}")
                else:
                    raise ToolError("json_process", f"无法访问: {key}")

            return json.dumps(current, indent=2, ensure_ascii=False)[:5000]

        elif operation == "validate":
            if isinstance(json_data, dict):
                return f"✓ 有效的 JSON 对象，包含 {len(json_data)} 个键"
            elif isinstance(json_data, list):
                return f"✓ 有效的 JSON 数组，包含 {len(json_data)} 个元素"
            else:
                return f"✓ 有效的 JSON，类型: {type(json_data).__name__}"

        else:
            raise ToolError("json_process", f"未知 JSON 操作: {operation}")

    except json.JSONDecodeError as e:
        raise ToolError("json_process", f"JSON 解析失败: {e}")
    except ToolError:
        raise
    except Exception as e:
        raise ToolError("json_process", f"JSON 处理失败: {e}")


@register_tool(
    name="code_analysis",
    description="代码分析工具。支持复杂度分析、依赖分析、安全扫描。",
    parameters=[
        ToolParameter("path", "string", "代码文件路径", required=True),
        ToolParameter("type", "string", "分析类型（默认 complexity）", default="complexity",
                     enum=["complexity", "dependencies", "security"]),
    ]
)
def code_analysis(args: Dict) -> str:
    """分析代码"""
    path = args.get("path", "")
    if not path:
        raise ValidationError("缺少 path 参数", "path")

    analysis_type = args.get("type", "complexity")
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        raise ToolError("code_analysis", f"文件不存在: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # 复杂度分析
        if analysis_type == "complexity":
            return _analyze_complexity(path, content)

        # 依赖分析
        elif analysis_type == "dependencies":
            return _analyze_dependencies(path, content)

        # 安全扫描
        elif analysis_type == "security":
            return _analyze_security(path, content)

        else:
            raise ToolError("code_analysis", f"未知分析类型: {analysis_type}")

    except ToolError:
        raise
    except Exception as e:
        raise ToolError("code_analysis", f"代码分析失败: {e}")


def _analyze_complexity(path: str, content: str) -> str:
    """分析代码复杂度"""
    lines = content.split('\n')
    total_lines = len(lines)
    code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
    comment_lines = len([l for l in lines if l.strip().startswith('#')])
    blank_lines = len([l for l in lines if not l.strip()])

    # 计算圈复杂度（简化版）
    complexity_keywords = [
        'if', 'elif', 'else', 'for', 'while', 'try', 'except',
        'finally', 'with', 'and', 'or'
    ]
    complexity = 1
    for line in lines:
        for keyword in complexity_keywords:
            if keyword in line:
                complexity += 1

    result = [
        f"代码分析: {path}",
        "=" * 50,
        f"总行数: {total_lines}",
        f"代码行数: {code_lines}",
        f"注释行数: {comment_lines}",
        f"空行数: {blank_lines}",
        f"代码比例: {code_lines/total_lines*100:.1f}%",
        f"注释比例: {comment_lines/total_lines*100:.1f}%",
        "",
        "复杂度分析:",
        f"  圈复杂度: {complexity}",
        f"  复杂度等级: {'低' if complexity < 10 else '中' if complexity < 20 else '高'}",
    ]

    # 函数/类统计
    functions = re.findall(r'def\s+(\w+)\s*\(', content)
    classes = re.findall(r'class\s+(\w+)\s*[\(:]', content)

    result.extend([
        "",
        "结构统计:",
        f"  函数数量: {len(functions)}",
        f"  类数量: {len(classes)}",
    ])

    if functions:
        result.append(f"  函数列表: {', '.join(functions[:10])}")
    if classes:
        result.append(f"  类列表: {', '.join(classes[:10])}")

    return "\n".join(result)


def _analyze_dependencies(path: str, content: str) -> str:
    """分析代码依赖"""
    imports = re.findall(r'^(?:from|import)\s+(\w+)', content, re.MULTILINE)
    unique_imports = sorted(set(imports))

    result = [
        f"依赖分析: {path}",
        "=" * 50,
        f"导入语句: {len(imports)}",
        f"唯一依赖: {len(unique_imports)}",
        "",
        "依赖列表:",
    ]

    for imp in unique_imports[:20]:
        result.append(f"  • {imp}")

    return "\n".join(result)


def _analyze_security(path: str, content: str) -> str:
    """安全扫描"""
    security_patterns = {
        "硬编码密码": r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']',
        "API 密钥": r'(?i)(api[_-]?key|apikey)\s*=\s*["\'][^"\']+["\']',
        "SQL 注入": r'(?i)(execute|cursor)\s*\(\s*["\'].*%s',
        "命令注入": r'os\.system|subprocess\.call|subprocess\.run',
        "文件操作": r'open\s*\(\s*["\'](?:/etc|/proc|/sys)',
        "危险函数": r'exec\s*\(|eval\s*\(',
    }

    issues = []
    for pattern_name, pattern in security_patterns.items():
        matches = re.findall(pattern, content)
        if matches:
            issues.append(f"⚠️ {pattern_name}: {len(matches)} 处")

    result = [
        f"安全扫描: {path}",
        "=" * 50,
    ]

    if issues:
        result.append("发现潜在安全问题:")
        result.extend(issues)
    else:
        result.append("✓ 未发现明显安全问题")

    return "\n".join(result)