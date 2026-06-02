"""蒙多工具引擎 v26 — Hermes 注册表模式 + Claude Code 极简工具集

设计原则（融合 Hermes + Claude Code）：
- 注册表模式：工具自注册，零耦合
- 自动发现：import 时自动注册 schema
- 参数验证：每个 handler 自行验证必填参数
- 结果截断：统一在注册表层处理，不在各工具内部
"""

import os
import json
import re
import subprocess
import glob as glob_mod
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional

# ═══════════════════════════════════════════════
# Tool Registry — 借鉴 Hermes tools/registry.py
# ═══════════════════════════════════════════════

class ToolRegistry:
    """工具注册表 — 自动收集 schema + handler"""

    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._schemas: List[Dict] = []
        self._required: Dict[str, List[str]] = {}
        self._names: List[str] = []

    def register(self, name: str, description: str,
                 parameters: Dict, handler: Callable,
                 required: List[str] = None):
        self._handlers[name] = handler
        self._required[name] = required or []
        self._names.append(name)
        self._schemas.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        })

    @property
    def schemas(self) -> List[Dict]:
        return self._schemas

    @property
    def names(self) -> List[str]:
        return list(self._names)

    def execute(self, name: str, args: Dict) -> str:
        handler = self._handlers.get(name)
        if not handler:
            return f"[错误: 未知工具 {name}]"
        if not isinstance(args, dict):
            args = {}
        try:
            result = handler(args)
            if isinstance(result, str) and "缺少" in result:
                req = self._required.get(name, [])
                if req:
                    result += f"\n正确用法: {name}({', '.join(req)})"
            return result
        except Exception as e:
            return f"[工具执行错误: {name}: {e}]"


# 全局注册表实例
registry = ToolRegistry()

# 结果截断上限
MAX_OUTPUT_CHARS = 8000


def _truncate(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... (截断，共 {len(text)} 字符)"


# ═══════════════════════════════════════════════
# 工具实现 — Claude Code 风格极简
# ═══════════════════════════════════════════════

def _terminal(args: Dict) -> str:
    cmd = args.get("command", "")
    if not cmd:
        return "[错误: terminal 缺少 command 参数]"
    workdir = args.get("workdir") or os.getcwd()
    timeout = args.get("timeout", 120)
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=workdir,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        return _truncate(output or "(无输出)")
    except subprocess.TimeoutExpired:
        return f"[超时: 命令执行超过 {timeout} 秒]"
    except Exception as e:
        return f"[错误: {e}]"


def _read_file(args: Dict) -> str:
    path = args.get("path", "")
    if not path:
        return "[错误: read_file 缺少 path 参数]"
    path = os.path.expanduser(path)
    offset = args.get("offset", 1)
    limit = args.get("limit", 500)

    if not os.path.exists(path):
        return f"[错误: 文件不存在: {path}]"
    if os.path.isdir(path):
        return f"[错误: 是目录不是文件: {path}]"
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        total = len(lines)
        start = max(0, offset - 1)
        end = min(total, start + limit)
        selected = lines[start:end]
        result = [f"{i:4d}|{line.rstrip()}" for i, line in enumerate(selected, start=start + 1)]
        header = f"文件: {path} (共 {total} 行，显示 {start+1}-{end})"
        return _truncate(header + "\n" + "\n".join(result))
    except Exception as e:
        return f"[错误: {e}]"


def _write_file(args: Dict) -> str:
    path = args.get("path", "")
    if not path:
        return "[错误: write_file 缺少 path 参数]"
    content = args.get("content") or ""
    if not content:
        return "[错误: write_file 缺少 content 参数]"
    path = os.path.expanduser(path)
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✓ 已写入: {path} ({len(content)} 字符)"
    except Exception as e:
        return f"[错误: {e}]"


def _search_files(args: Dict) -> str:
    pattern = args.get("pattern", "")
    if not pattern:
        return "[错误: search_files 缺少 pattern 参数]"
    path = os.path.expanduser(args.get("path") or ".")
    target = args.get("target", "content")

    if target == "files":
        matches = glob_mod.glob(os.path.join(path, "**", f"*{pattern}*"), recursive=True)
        if not matches:
            return f"未找到匹配 '{pattern}' 的文件"
        return _truncate("\n".join(sorted(matches)[:50]))

    results = []
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error:
        regex = re.compile(re.escape(pattern), re.IGNORECASE)

    searchable_exts = (".py", ".js", ".ts", ".html", ".css", ".md", ".txt",
                       ".json", ".yaml", ".yml", ".sh", ".bat", ".m", ".swift",
                       ".c", ".cpp", ".h", ".hpp", ".java", ".go", ".rs")

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


def _web_search(args: Dict) -> str:
    query = args.get("query", "")
    if not query:
        return "[错误: web_search 缺少 query 参数]"
    limit = args.get("limit", 5)

    try:
        import urllib.parse
        import urllib.request
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        results = []
        links = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html)
        for href, title in links[:limit]:
            title = re.sub(r"<[^>]+>", "", title).strip()
            results.append(f"• {title}\n  {href}")
        return "\n\n".join(results) if results else "搜索未返回结果"
    except Exception as e:
        return f"搜索失败: {e}"


def _list_directory(args: Dict) -> str:
    path = os.path.expanduser(args.get("path") or ".")
    show_hidden = args.get("show_hidden", False)
    if not os.path.isdir(path):
        return f"[错误: 不是目录: {path}]"
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
        return f"[错误: 无权限访问: {path}]"


def _edit_file(args: Dict) -> str:
    """精确编辑文件（Claude Code Edit 工具风格）"""
    path = args.get("path", "")
    if not path:
        return "[错误: edit_file 缺少 path 参数]"
    old_string = args.get("old_string", "")
    new_string = args.get("new_string", "")
    if not old_string:
        return "[错误: edit_file 缺少 old_string 参数]"

    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return f"[错误: 文件不存在: {path}]"
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if old_string not in content:
            return f"[错误: 未找到匹配文本，请检查 old_string]"
        count = content.count(old_string)
        if count > 1:
            return f"[错误: 找到 {count} 处匹配，请提供更精确的上下文]"
        new_content = content.replace(old_string, new_string, 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"✓ 已编辑: {path}"
    except Exception as e:
        return f"[错误: {e}]"


# ═══════════════════════════════════════════════
# 自动注册所有工具
# ═══════════════════════════════════════════════

registry.register(
    name="terminal",
    description="执行 shell 命令。用于运行代码、安装包、git 操作、系统管理。返回 stdout/stderr。",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "要执行的 shell 命令"},
            "workdir": {"type": "string", "description": "工作目录（可选，默认当前目录）"},
            "timeout": {"type": "integer", "description": "超时秒数（默认 120）"},
        },
        "required": ["command"],
    },
    handler=_terminal,
    required=["command"],
)

registry.register(
    name="read_file",
    description="读取文本文件内容。返回带行号的内容。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "offset": {"type": "integer", "description": "起始行号（从 1 开始）"},
            "limit": {"type": "integer", "description": "最大读取行数（默认 500）"},
        },
        "required": ["path"],
    },
    handler=_read_file,
    required=["path"],
)

registry.register(
    name="write_file",
    description="写入文件（覆盖整个文件）。自动创建父目录。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "content": {"type": "string", "description": "文件内容"},
        },
        "required": ["path", "content"],
    },
    handler=_write_file,
    required=["path", "content"],
)

registry.register(
    name="edit_file",
    description="精确编辑文件中的指定文本。找到 old_string 并替换为 new_string。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "old_string": {"type": "string", "description": "要替换的原文"},
            "new_string": {"type": "string", "description": "替换后的新文本"},
        },
        "required": ["path", "old_string", "new_string"],
    },
    handler=_edit_file,
    required=["path", "old_string", "new_string"],
)

registry.register(
    name="search_files",
    description="搜索文件内容或按文件名查找。返回匹配的行和文件路径。",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "正则表达式或 glob 模式"},
            "path": {"type": "string", "description": "搜索目录（默认当前目录）"},
            "target": {
                "type": "string",
                "enum": ["content", "files"],
                "description": "content=搜索文件内容, files=按文件名查找",
            },
        },
        "required": ["pattern"],
    },
    handler=_search_files,
    required=["pattern"],
)

registry.register(
    name="web_search",
    description="搜索互联网。返回搜索结果列表（标题、URL、描述）。",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索查询"},
            "limit": {"type": "integer", "description": "结果数量（默认 5）"},
        },
        "required": ["query"],
    },
    handler=_web_search,
    required=["query"],
)

registry.register(
    name="list_directory",
    description="列出目录下的文件和子目录。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "目录路径（默认当前目录）"},
            "show_hidden": {"type": "boolean", "description": "是否显示隐藏文件"},
        },
    },
    handler=_list_directory,
)

# 向后兼容：旧代码引用的常量
TOOL_SCHEMAS = registry.schemas


def execute_tool(name: str, args: Dict) -> str:
    return registry.execute(name, args)
