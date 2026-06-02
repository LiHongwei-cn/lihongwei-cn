"""蒙多的工具引擎 — terminal / file / web / search"""

import os
import json
import subprocess
import glob as glob_mod
from pathlib import Path
from typing import Dict, Any, Callable


# ═══════════════════════════════════════════════
# Tool Schema — OpenAI function calling 格式
# ═══════════════════════════════════════════════

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "terminal",
            "description": "执行 shell 命令。用于运行代码、安装包、git 操作、系统管理。返回 stdout/stderr。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的 shell 命令",
                    },
                    "workdir": {
                        "type": "string",
                        "description": "工作目录（可选，默认当前目录）",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "超时秒数（默认 120）",
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取文本文件内容。返回带行号的内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "offset": {"type": "integer", "description": "起始行号（从 1 开始）"},
                    "limit": {"type": "integer", "description": "最大读取行数（默认 500）"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "写入文件（覆盖整个文件）。自动创建父目录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "文件内容"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "搜索文件内容或按文件名查找。返回匹配的行和文件路径。",
            "parameters": {
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
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索互联网。返回搜索结果列表（标题、URL、描述）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索查询"},
                    "limit": {"type": "integer", "description": "结果数量（默认 5）"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "列出目录下的文件和子目录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "目录路径（默认当前目录）"},
                    "show_hidden": {"type": "boolean", "description": "是否显示隐藏文件"},
                },
            },
        },
    },
]


# ═══════════════════════════════════════════════
# Tool Execution — 实际执行
# ═══════════════════════════════════════════════

def _run_terminal(args: Dict) -> str:
    cmd = args.get("command", "")
    if not cmd:
        return "[错误: terminal 缺少 command 参数]"
    workdir = args.get("workdir") or os.getcwd()
    timeout = args.get("timeout", 120)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        return output[:8000] or "(无输出)"
    except subprocess.TimeoutExpired:
        return f"[超时: 命令执行超过 {timeout} 秒]"
    except Exception as e:
        return f"[错误: {e}]"


def _run_read_file(args: Dict) -> str:
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

        result = []
        for i, line in enumerate(selected, start=start + 1):
            result.append(f"{i:4d}|{line.rstrip()}")

        header = f"文件: {path} (共 {total} 行，显示 {start+1}-{end})"
        return header + "\n" + "\n".join(result)
    except Exception as e:
        return f"[错误: {e}]"


def _run_write_file(args: Dict) -> str:
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


def _run_search_files(args: Dict) -> str:
    import re

    pattern = args.get("pattern", "")
    if not pattern:
        return "[错误: search_files 缺少 pattern 参数]"
    path = os.path.expanduser(args.get("path") or ".")
    target = args.get("target", "content")

    if target == "files":
        matches = glob_mod.glob(os.path.join(path, "**", f"*{pattern}*"), recursive=True)
        if not matches:
            return f"未找到匹配 '{pattern}' 的文件"
        return "\n".join(sorted(matches)[:50])

    # content search
    results = []
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error:
        regex = re.compile(re.escape(pattern), re.IGNORECASE)

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__" and d != "node_modules"]
        for fname in files:
            if not fname.endswith((".py", ".js", ".ts", ".html", ".css", ".md", ".txt", ".json", ".yaml", ".yml", ".sh", ".bat", ".m", ".swift")):
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
    return "\n".join(results[:80])


def _run_web_search(args: Dict) -> str:
    query = args.get("query", "")
    if not query:
        return "[错误: web_search 缺少 query 参数]"
    limit = args.get("limit", 5)

    # 使用 Hermes 的 web_search 如果可用，否则用 DuckDuckGo
    try:
        # 尝试 DuckDuckGo HTML 搜索
        import urllib.parse
        import urllib.request

        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # 简单提取结果
        results = []
        import re
        links = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html)
        for href, title in links[:limit]:
            title = re.sub(r"<[^>]+>", "", title).strip()
            results.append(f"• {title}\n  {href}")

        if results:
            return "\n\n".join(results)
        return "搜索未返回结果"
    except Exception as e:
        return f"搜索失败: {e}"


def _run_list_directory(args: Dict) -> str:
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
        return f"目录: {path}\n" + "\n".join(entries[:100])
    except PermissionError:
        return f"[错误: 无权限访问: {path}]"


# ═══════════════════════════════════════════════
# Tool Dispatch
# ═══════════════════════════════════════════════

TOOL_HANDLERS: Dict[str, Callable] = {
    "terminal": _run_terminal,
    "read_file": _run_read_file,
    "write_file": _run_write_file,
    "search_files": _run_search_files,
    "web_search": _run_web_search,
    "list_directory": _run_list_directory,
}


def execute_tool(name: str, args: Dict) -> str:
    """执行工具调用，返回结果字符串"""
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return f"[错误: 未知工具: {name}]"
    try:
        return handler(args)
    except Exception as e:
        return f"[工具执行错误: {name}: {e}]"
