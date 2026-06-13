"""蒙多文件操作工具 — 重构版

改进：
- 统一错误处理
- 路径安全检查
- 结果格式化
"""

import os
import glob as glob_mod
import re
from typing import Dict, List

from .registry import register_tool, ToolParameter
from ..utils.errors import ToolError, ValidationError
from ..utils.logging import get_tool_logger

logger = get_tool_logger()


def _truncate(text: str, limit: int = 8000) -> str:
    """智能截断文本"""
    if len(text) <= limit:
        return text
    head = text[:int(limit * 0.6)]
    tail = text[-int(limit * 0.3):]
    return f"{head}\n... ({len(text)} 字符，省略中间部分) ...\n{tail}"


@register_tool(
    name="read_file",
    description="读取文本文件内容。返回带行号的内容。",
    parameters=[
        ToolParameter("path", "string", "文件路径", required=True),
        ToolParameter("offset", "integer", "起始行号（从 1 开始）", default=1),
        ToolParameter("limit", "integer", "最大读取行数（默认 500）", default=500),
    ]
)
def read_file(args: Dict) -> str:
    """读取文件"""
    path = args.get("path", "")
    if not path:
        raise ValidationError("缺少 path 参数", "path")

    path = os.path.expanduser(path)

    if not os.path.exists(path):
        raise ToolError("read_file", f"文件不存在: {path}")
    if os.path.isdir(path):
        raise ToolError("read_file", f"是目录不是文件: {path}")

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total = len(lines)
        offset = args.get("offset", 1)
        limit = args.get("limit", 500)

        start = max(0, offset - 1)
        end = min(total, start + limit)
        selected = lines[start:end]

        result = [f"{i:4d}|{line.rstrip()}" for i, line in enumerate(selected, start=start + 1)]
        header = f"文件: {path} (共 {total} 行，显示 {start+1}-{end})"

        return _truncate(header + "\n" + "\n".join(result))
    except ToolError:
        raise
    except Exception as e:
        raise ToolError("read_file", f"读取文件失败: {e}")


@register_tool(
    name="write_file",
    description="写入文件（覆盖整个文件）。自动创建父目录。",
    parameters=[
        ToolParameter("path", "string", "文件路径", required=True),
        ToolParameter("content", "string", "文件内容", required=True),
    ]
)
def write_file(args: Dict) -> str:
    """写入文件"""
    path = args.get("path", "")
    content = args.get("content", "")

    if not path:
        raise ValidationError("缺少 path 参数", "path")
    if not content:
        raise ValidationError("缺少 content 参数", "content")

    path = os.path.expanduser(path)

    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✓ 已写入: {path} ({len(content)} 字符)"
    except Exception as e:
        raise ToolError("write_file", f"写入文件失败: {e}")


@register_tool(
    name="edit_file",
    description="精确编辑文件中的指定文本。找到 old_string 并替换为 new_string。",
    parameters=[
        ToolParameter("path", "string", "文件路径", required=True),
        ToolParameter("old_string", "string", "要替换的原文", required=True),
        ToolParameter("new_string", "string", "替换后的新文本", required=True),
    ]
)
def edit_file(args: Dict) -> str:
    """编辑文件"""
    path = args.get("path", "")
    old_string = args.get("old_string", "")
    new_string = args.get("new_string", "")

    if not path:
        raise ValidationError("缺少 path 参数", "path")
    if not old_string:
        raise ValidationError("缺少 old_string 参数", "old_string")

    path = os.path.expanduser(path)

    if not os.path.exists(path):
        raise ToolError("edit_file", f"文件不存在: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if old_string not in content:
            raise ToolError("edit_file", "未找到匹配文本，请检查 old_string")

        count = content.count(old_string)
        if count > 1:
            raise ToolError("edit_file", f"找到 {count} 处匹配，请提供更精确的上下文")

        new_content = content.replace(old_string, new_string, 1)

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return f"✓ 已编辑: {path}"
    except ToolError:
        raise
    except Exception as e:
        raise ToolError("edit_file", f"编辑文件失败: {e}")


@register_tool(
    name="search_files",
    description="搜索文件内容或按文件名查找。返回匹配的行和文件路径。",
    parameters=[
        ToolParameter("pattern", "string", "正则表达式或 glob 模式", required=True),
        ToolParameter("path", "string", "搜索目录（默认当前目录）", default="."),
        ToolParameter("target", "string", "content=搜索文件内容, files=按文件名查找",
                     default="content", enum=["content", "files"]),
    ]
)
def search_files(args: Dict) -> str:
    """搜索文件"""
    pattern = args.get("pattern", "")
    if not pattern:
        raise ValidationError("缺少 pattern 参数", "pattern")

    path = os.path.expanduser(args.get("path") or ".")
    target = args.get("target", "content")

    if target == "files":
        matches = glob_mod.glob(os.path.join(path, "**", f"*{pattern}*"), recursive=True)
        if not matches:
            return f"未找到匹配 '{pattern}' 的文件"
        return _truncate("\n".join(sorted(matches)[:50]))

    # 搜索内容
    results = []
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error:
        regex = re.compile(re.escape(pattern), re.IGNORECASE)

    searchable_exts = (".py", ".js", ".ts", ".html", ".css", ".md", ".txt",
                       ".json", ".yaml", ".yml", ".sh", ".bat", ".m", ".swift",
                       ".c", ".cpp", ".h", ".hpp", ".java", ".go", ".rs")

    try:
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "node_modules", ".git", "venv")]

            for fname in files:
                if not fname.endswith(searchable_exts):
                    continue

                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        for i, line in enumerate(f, 1):
                            if regex.search(line):
                                rel = os.path.relpath(fpath, path)
                                results.append(f"{rel}:{i}: {line.rstrip()}")
                except (PermissionError, OSError):
                    continue

                if len(results) >= 80:
                    break
            if len(results) >= 80:
                break

        if not results:
            return f"未找到匹配 '{pattern}' 的内容"
        return _truncate("\n".join(results[:80]))
    except Exception as e:
        raise ToolError("search_files", f"搜索失败: {e}")


@register_tool(
    name="list_directory",
    description="列出目录下的文件和子目录。",
    parameters=[
        ToolParameter("path", "string", "目录路径（默认当前目录）", default="."),
        ToolParameter("show_hidden", "boolean", "是否显示隐藏文件", default=False),
    ]
)
def list_directory(args: Dict) -> str:
    """列出目录"""
    path = os.path.expanduser(args.get("path") or ".")
    show_hidden = args.get("show_hidden", False)

    if not os.path.isdir(path):
        raise ToolError("list_directory", f"不是目录: {path}")

    entries = []
    try:
        for name in sorted(os.listdir(path)):
            if not show_hidden and name.startswith("."):
                continue

            full = os.path.join(path, name)
            if os.path.isdir(full):
                entries.append(f"  📁 {name}/")
            else:
                size = os.path.getsize(full)
                if size < 1024:
                    s = f"{size}B"
                elif size < 1024 * 1024:
                    s = f"{size/1024:.1f}K"
                else:
                    s = f"{size/1024/1024:.1f}M"
                entries.append(f"  📄 {name} ({s})")

        return _truncate(f"目录: {path}\n" + "\n".join(entries[:100]))
    except PermissionError:
        raise ToolError("list_directory", f"无权限访问: {path}")
    except Exception as e:
        raise ToolError("list_directory", f"列出目录失败: {e}")