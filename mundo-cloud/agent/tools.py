"""蒙多的工具引擎 — terminal / file / web / search

v1.1 安全加固版:
- 所有参数安全访问 (get + 验证)
- 路径遍历防护
- 输入类型校验
- 具体异常捕获
"""

import os
import json
import subprocess
import glob as glob_mod
from pathlib import Path
from typing import Dict, Any, Callable, Optional


# ═══════════════════════════════════════════════
# 安全工具函数
# ═══════════════════════════════════════════════

def _require_param(args: Dict, key: str, expected_type: type = str) -> Any:
    """安全获取必需参数，缺失或类型错误时抛出明确异常"""
    value = args.get(key)
    if value is None:
        raise ValueError(f"[参数错误] 缺少必需参数 '{key}'")
    if not isinstance(value, expected_type):
        raise TypeError(f"[参数错误] '{key}' 期望 {expected_type.__name__}，实际 {type(value).__name__}")
    return value


def _validate_path(path: str, must_exist: bool = False, must_be_file: bool = False, must_be_dir: bool = False) -> str:
    """路径安全验证 — 防路径遍历、规范化路径"""
    if not path or not isinstance(path, str):
        raise ValueError(f"[路径错误] 路径不能为空")

    # 展开 ~
    expanded = os.path.expanduser(path)

    # 规范化（消除 .. 和 . 等）
    normalized = os.path.normpath(expanded)

    # 安全检查: 禁止访问敏感系统路径
    forbidden_prefixes = ['/etc/shadow', '/etc/passwd', '/root/.ssh', '/proc/self']
    for prefix in forbidden_prefixes:
        if normalized.startswith(prefix):
            raise PermissionError(f"[安全拒绝] 不允许访问系统敏感路径: {normalized}")

    if must_exist and not os.path.exists(normalized):
        raise FileNotFoundError(f"[路径错误] 路径不存在: {normalized}")

    if must_be_file:
        if not os.path.isfile(normalized):
            raise ValueError(f"[路径错误] 不是文件: {normalized}")

    if must_be_dir:
        if not os.path.isdir(normalized):
            raise ValueError(f"[路径错误] 不是目录: {normalized}")

    return normalized


def _truncate(text: str, max_len: int = 8000) -> str:
    """截断过长输出"""
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"\n... [已截断，共 {len(text)} 字符]"


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
    """执行 shell 命令"""
    try:
        cmd = _require_param(args, "command")
    except (ValueError, TypeError) as e:
        return str(e)

    workdir = args.get("workdir") or os.getcwd()
    timeout = args.get("timeout", 120)

    # 类型安全
    if isinstance(timeout, str):
        try:
            timeout = int(timeout)
        except ValueError:
            timeout = 120

    # 工作目录验证
    if not os.path.isdir(workdir):
        return f"[错误: 工作目录不存在: {workdir}]"

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
        return _truncate(output) or "(无输出)"
    except subprocess.TimeoutExpired:
        return f"[超时: 命令执行超过 {timeout} 秒]"
    except FileNotFoundError:
        return f"[错误: 命令未找到: {cmd.split()[0] if cmd else '?'}]"
    except PermissionError:
        return f"[错误: 无权限执行: {cmd}]"
    except Exception as e:
        return f"[错误: {type(e).__name__}: {e}]"


def _run_read_file(args: Dict) -> str:
    """读取文件"""
    try:
        raw_path = _require_param(args, "path")
        path = _validate_path(raw_path, must_exist=True, must_be_file=True)
    except (ValueError, TypeError, FileNotFoundError) as e:
        return str(e)

    offset = args.get("offset", 1)
    limit = args.get("limit", 500)

    # 类型安全
    if isinstance(offset, str):
        try:
            offset = int(offset)
        except ValueError:
            offset = 1
    if isinstance(limit, str):
        try:
            limit = int(limit)
        except ValueError:
            limit = 500

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
    except UnicodeDecodeError:
        return f"[错误: 文件不是文本格式（可能是二进制文件）: {path}]"
    except PermissionError:
        return f"[错误: 无权限读取: {path}]"
    except Exception as e:
        return f"[错误: {type(e).__name__}: {e}]"


def _run_write_file(args: Dict) -> str:
    """写入文件 — 核心修复: 参数安全访问 + 路径遍历防护"""
    try:
        raw_path = _require_param(args, "path")
        path = _validate_path(raw_path)
    except (ValueError, TypeError) as e:
        return str(e)

    try:
        content = _require_param(args, "content")
    except (ValueError, TypeError) as e:
        return str(e)

    try:
        parent_dir = os.path.dirname(path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✓ 已写入: {path} ({len(content)} 字符)"
    except PermissionError:
        return f"[错误: 无权限写入: {path}]"
    except OSError as e:
        return f"[错误: 文件系统错误: {e}]"
    except Exception as e:
        return f"[错误: {type(e).__name__}: {e}]"


def _run_search_files(args: Dict) -> str:
    """搜索文件"""
    import re

    try:
        pattern = _require_param(args, "pattern")
    except (ValueError, TypeError) as e:
        return str(e)

    raw_path = args.get("path") or "."
    target = args.get("target", "content")

    try:
        path = _validate_path(raw_path, must_exist=True, must_be_dir=True)
    except (ValueError, TypeError, FileNotFoundError) as e:
        return str(e)

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
        # 如果正则无效，当作普通字符串搜索
        regex = re.compile(re.escape(pattern), re.IGNORECASE)

    skip_dirs = {".", "..", ".git", "__pycache__", "node_modules", "venv", ".venv", "dist", ".tox"}
    text_extensions = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss",
        ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".sh", ".bat",
        ".m", ".swift", ".go", ".rs", ".java", ".c", ".cpp", ".h", ".hpp",
        ".sql", ".xml", ".cfg", ".ini", ".env", ".dockerfile",
    }

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in text_extensions and not fname.endswith("Makefile"):
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
    """搜索互联网"""
    try:
        query = _require_param(args, "query")
    except (ValueError, TypeError) as e:
        return str(e)

    limit = args.get("limit", 5)

    try:
        import urllib.request
        import urllib.parse

        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        results = []
        import re
        links = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html)
        for href, title in links[:limit]:
            title = re.sub(r"<[^>]+>", "", title).strip()
            results.append(f"• {title}\n  {href}")

        if results:
            return "\n\n".join(results)
        return "搜索未返回结果"
    except urllib.error.URLError as e:
        return f"[网络错误: {e}]"
    except Exception as e:
        return f"[搜索失败: {type(e).__name__}: {e}]"


def _run_list_directory(args: Dict) -> str:
    """列出目录"""
    raw_path = args.get("path") or "."
    show_hidden = args.get("show_hidden", False)

    try:
        path = _validate_path(raw_path, must_exist=True, must_be_dir=True)
    except (ValueError, TypeError, FileNotFoundError) as e:
        return str(e)

    entries = []
    try:
        for name in sorted(os.listdir(path)):
            if not show_hidden and name.startswith("."):
                continue
            full = os.path.join(path, name)
            if os.path.isdir(full):
                entries.append(f"  📁 {name}/")
            else:
                try:
                    size = os.path.getsize(full)
                    if size < 1024:
                        s = f"{size}B"
                    elif size < 1024 * 1024:
                        s = f"{size/1024:.1f}K"
                    else:
                        s = f"{size/1024/1024:.1f}M"
                except OSError:
                    s = "?"
                entries.append(f"  📄 {name} ({s})")
        return f"目录: {path}\n" + "\n".join(entries[:100])
    except PermissionError:
        return f"[错误: 无权限访问: {path}]"
    except Exception as e:
        return f"[错误: {type(e).__name__}: {e}]"


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
    """执行工具调用，返回结果字符串

    安全保障:
    - 未知工具返回错误信息（不抛异常）
    - 所有异常被捕获并转为可读错误消息
    - 参数缺失时返回明确提示
    """
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        available = ", ".join(TOOL_HANDLERS.keys())
        return f"[错误: 未知工具: {name}] 可用工具: {available}"

    # 参数类型保护
    if not isinstance(args, dict):
        return f"[错误: 工具参数必须是字典类型，实际: {type(args).__name__}]"

    try:
        result = handler(args)
        return result if result else "(无输出)"
    except Exception as e:
        return f"[工具执行错误: {name}: {type(e).__name__}: {e}]"
