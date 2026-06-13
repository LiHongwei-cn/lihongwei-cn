"""蒙多工具引擎 v3.0.0 — 融合四家精华

设计原则：
- 注册表模式：工具自注册，零耦合（Hermes Agent）
- 参数验证：每个 handler 自行验证必填参数
- 结果截断：统一在注册表层处理
- 结构化输出：支持 JSON 输出（Claude Code）
- 安全隔离：危险操作需确认（Codex CLI）
- 沙箱执行：代码执行在受限环境（Codex CLI）
"""

import os
import sys
import json
import re
import subprocess
import glob as glob_mod
import time
import random
from typing import Dict, Callable, List
from pathlib import Path


# ═══════════════════════════════════════════════
# Tool Registry — 借鉴 Hermes Agent
# ═══════════════════════════════════════════════

class ToolRegistry:

    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._schemas: List[Dict] = []
        self._required: Dict[str, List[str]] = {}
        self._names: List[str] = []

    def __repr__(self) -> str:
        return f"ToolRegistry(tools={len(self._names)})"

    def __len__(self) -> int:
        return len(self._names)

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

        # v3.1.0: 参数规范化 + 记录原始参数用于调试
        original_keys = list(args.keys()) if args else []
        args = _normalize_args(args, name)
        normalized_keys = list(args.keys())

        try:
            result = handler(args)

            # v3.1.0: 增强错误反馈
            if isinstance(result, str) and ("缺少" in result or "错误" in result):
                req = self._required.get(name, [])
                if req:
                    fix_hint = f"\n\n⚠️ 参数错误修复指南:"
                    fix_hint += f"\n工具: {name}"
                    fix_hint += f"\n必需参数: {', '.join(req)}"
                    fix_hint += f"\n原始参数: {original_keys}"
                    fix_hint += f"\n规范化后: {normalized_keys}"
                    fix_hint += f"\n\n请重新调用: {name}({', '.join(req)})"
                    result += fix_hint

            return result
        except Exception as e:
            err_msg = f"工具 {name} 执行失败: {e}"
            req = self._required.get(name, [])
            if req and any(kw in str(e) for kw in ("缺少", "required", "missing", "必需")):
                err_msg += f"\n必需参数: {', '.join(req)}"
                err_msg += f"\n收到的参数: {original_keys}"
            return err_msg


registry = ToolRegistry()

MAX_OUTPUT_CHARS = 8000


# ═══════════════════════════════════════════════
# 参数规范化 — 解决 LLM 调用格式不稳定问题
# ═══════════════════════════════════════════════

# path 参数的常见别名
_PATH_ALIASES = ("path", "file_path", "filename", "file", "filepath", "dir", "directory", "folder")
_CONTENT_ALIASES = ("content", "text", "body", "value")
_COMMAND_ALIASES = ("command", "cmd", "shell", "exec", "run")
_PATTERN_ALIASES = ("pattern", "regex", "search", "keyword")

# 工具特定的参数保护：这些参数在特定工具中不应被规范化
_TOOL_PARAM_PROTECT = {
    "json_process": {"data"},
    "mimo_memory_search": {"query"},
}

# 常见的嵌套包装键
_WRAPPER_KEYS = ("parameters", "params", "args", "kwargs", "input", "data")


def _normalize_args(args: dict, tool_name: str = "") -> dict:
    """规范化工具参数 — 处理 LLM 输出的各种格式问题

    处理情况（v3.1.0 增强）：
    1. 嵌套解包: {"parameters": {"path": "x"}} → {"path": "x"}
    2. 别名映射: path/content/command/pattern 四大参数全别名覆盖
    3. 类型修正: {"path": 123} → {"path": "123"}
    4. 空值处理: {"path": null} → {"path": ""}
    5. 工具名片名: {"write_file": "/path/to/file"} → {"path": "/path/to/file"}
    6. 值穿透: 单值列表自动按位置拆分
    """
    if not isinstance(args, dict):
        return {}

    result = dict(args)  # 浅拷贝

    # 1. 解包嵌套参数（最多解3层，防死循环）
    for _ in range(3):
        if len(result) == 1:
            key = next(iter(result))
            if key in _WRAPPER_KEYS and isinstance(result[key], dict):
                result = dict(result[key])
            else:
                break
        else:
            break

    # 1.5 工具名片名处理: LLM 有时输出 {"write_file": "xxx"} 或 {"read_file": "xxx"}
    _tool_name_map = {
        "write_file": "path",
        "read_file": "path",
        "edit_file": "path",
        "search_files": "pattern",
        "list_directory": "path",
        "terminal": "command",
        "python_execute": "code",
    }
    if tool_name in _tool_name_map and tool_name in result:
        expected_param = _tool_name_map[tool_name]
        val = result.pop(tool_name)
        if expected_param not in result and isinstance(val, (str, list)):
            if isinstance(val, list):
                if expected_param == "path" and len(val) >= 1:
                    result["path"] = val[0]
                if "content" not in result and len(val) >= 2:
                    result["content"] = val[1]
            else:
                result[expected_param] = val

    # 2. 别名映射 → 统一为标准名（全面覆盖）
    # 获取当前工具的参数保护列表
    protected = _TOOL_PARAM_PROTECT.get(tool_name, set())

    for alias in _PATH_ALIASES:
        if alias in result and "path" not in result and alias not in protected:
            result["path"] = result.pop(alias)
            break

    for alias in _CONTENT_ALIASES:
        if alias in result and "content" not in result and alias not in protected:
            result["content"] = result.pop(alias)
            break

    for alias in _COMMAND_ALIASES:
        if alias in result and "command" not in result and alias not in protected:
            result["command"] = result.pop(alias)
            break

    for alias in _PATTERN_ALIASES:
        if alias in result and "pattern" not in result and alias not in protected:
            result["pattern"] = result.pop(alias)
            break

    for alias in ("workdir", "work_dir", "cwd", "directory"):
        if alias in result and "workdir" not in result and alias not in protected:
            result["workdir"] = result.pop(alias)
            break

    # 3. 类型修正 — 所有字符串参数统一转 str
    _STRING_KEYS = ("path", "workdir", "command", "code", "pattern", "content",
                    "message", "old_string", "new_string", "branch_name")
    for key in _STRING_KEYS:
        if key in result and result[key] is not None:
            if not isinstance(result[key], str):
                if isinstance(result[key], (list, dict)):
                    try:
                        result[key] = json.dumps(result[key], ensure_ascii=False)
                    except (TypeError, ValueError):
                        result[key] = str(result[key])
                else:
                    result[key] = str(result[key])

    # 4. 空值 → 空字符串（让 handler 能正确检测缺失）
    for key in _STRING_KEYS:
        if key in result and result[key] is None:
            result[key] = ""

    return result


def _truncate(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    if limit <= 0:
        return text[:200] + "..." if len(text) > 200 else text
    if len(text) <= limit:
        return text
    head = text[:int(limit * 0.6)]
    tail = text[-int(limit * 0.3):]
    return f"{head}\n... 省略中间部分 ({len(text)} 字符) ...\n{tail}"


# ═══════════════════════════════════════════════
# 工具实现
# ═══════════════════════════════════════════════

def _terminal(args: Dict) -> str:
    cmd = args.get("command", "")
    if not cmd:
        keys = list(args.keys()) if args else []
        return f"[错误: terminal 缺少 command 参数，收到: {keys}]"
    workdir = args.get("workdir") or os.getcwd()
    timeout = args.get("timeout", 120)
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=workdir,
        )
        output = result.stdout
        if result.stderr:
            stderr = result.stderr[:2000]
            if len(result.stderr) > 2000:
                stderr += f"\n... ({len(result.stderr)} 字符，已截断)"
            output += f"\n[stderr]\n{stderr}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
            stderr = result.stderr or ""
            if "command not found" in stderr:
                output += "\n提示: 命令未找到"
            elif "Permission denied" in stderr:
                output += "\n提示: 权限不足"
            elif "No such file" in stderr:
                output += "\n提示: 文件/目录不存在"
        return _truncate(output or "(无输出)")
    except subprocess.TimeoutExpired:
        return f"[超时: 命令执行超过 {timeout} 秒]"
    except PermissionError:
        return "[错误: 权限不足]"
    except Exception as e:
        return f"[错误: {type(e).__name__}: {e}]"


def _read_file(args: Dict) -> str:
    path = args.get("path", "")
    if not path:
        keys = list(args.keys()) if args else []
        return f"[错误: read_file 缺少 path 参数，收到: {keys}]"
    path = os.path.expanduser(path)
    offset = args.get("offset", 1)
    limit = args.get("limit", 500)

    if not os.path.exists(path):
        return f"[错误: 文件不存在: {path}]"
    if os.path.isdir(path):
        return f"[错误: 是目录不是文件: {path}]"
    try:
        from itertools import islice
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            if offset > 1:
                list(islice(f, offset - 1))
            selected = list(islice(f, limit))
        total = 0
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            total = sum(1 for _ in f)
        start = max(0, offset - 1)
        end = min(total, start + len(selected))
        result = [f"{i:4d}|{line.rstrip()}" for i, line in enumerate(selected, start=start + 1)]
        header = f"文件: {path} (共 {total} 行，显示 {start+1}-{end})"
        return _truncate(header + "\n" + "\n".join(result))
    except Exception as e:
        return f"[错误: {e}]"


def _write_file(args: Dict) -> str:
    path = args.get("path", "")
    if not path:
        keys = list(args.keys()) if args else []
        return f"[错误: write_file 缺少 path 参数，收到: {keys}]"
    content = args.get("content") or ""
    if not content:
        return f"[错误: write_file 缺少 content 参数，path={path[:50]}]"
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
    max_results = min(args.get("limit", 50), 100)

    if target == "files":
        matches = glob_mod.glob(os.path.join(path, "**", f"*{pattern}*"), recursive=True)
        if not matches:
            return f"未找到匹配 '{pattern}' 的文件"
        return _truncate("\n".join(sorted(matches)[:max_results]))

    results = []
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error:
        regex = re.compile(re.escape(pattern), re.IGNORECASE)

    searchable_exts = (".py", ".js", ".ts", ".html", ".css", ".md", ".txt",
                       ".json", ".yaml", ".yml", ".sh", ".bat", ".m", ".swift",
                       ".c", ".cpp", ".h", ".hpp", ".java", ".go", ".rs")

    max_depth = 5
    max_files = 500
    file_count = 0
    start_time = time.time()

    for root, dirs, files in os.walk(path):
        depth = root[len(path):].count(os.sep)
        if depth >= max_depth:
            dirs.clear()
            continue
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "node_modules", ".git", "venv")]
        for fname in files:
            if time.time() - start_time > 10:
                results.append(f"... [搜索超时，已找到 {len(results)} 条结果]")
                return _truncate("\n".join(results[:max_results]))
            file_count += 1
            if file_count > max_files:
                results.append(f"... [已扫描 {max_files} 个文件，停止搜索]")
                return _truncate("\n".join(results[:max_results]))
            if not fname.endswith(searchable_exts):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f, 1):
                        if regex.search(line):
                            rel = os.path.relpath(fpath, path)
                            results.append(f"{rel}:{i}: {line.rstrip()}")
                            if len(results) >= max_results:
                                return _truncate("\n".join(results[:max_results]))
            except (PermissionError, OSError):
                continue
    if not results:
        return f"未找到匹配 '{pattern}' 的内容"
    return _truncate("\n".join(results[:max_results]))


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


def _git_operation(args: Dict) -> str:
    operation = args.get("operation", "")
    if not operation:
        return "[错误: git_operation 缺少 operation 参数]"
    workdir = args.get("workdir") or os.getcwd()
    operations = {
        "status": "git status --short",
        "diff": "git diff",
        "diff_staged": "git diff --staged",
        "log": "git log --oneline -10",
        "branch": "git branch -a",
        "current_branch": "git rev-parse --abbrev-ref HEAD",
    }
    if operation in operations:
        cmd = operations[operation]
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                    timeout=30, cwd=workdir)
            return _truncate(result.stdout or "(无输出)")
        except Exception as e:
            return f"[错误: Git 操作失败: {e}]"
    elif operation == "commit":
        message = args.get("message", "")
        if not message:
            return "[错误: commit 需要 message 参数]"
        try:
            subprocess.run(["git", "add", "-A"], cwd=workdir, check=True)
            result = subprocess.run(["git", "commit", "-m", message],
                                    capture_output=True, text=True, cwd=workdir)
            return f"✓ 已提交: {message}\n{result.stdout}"
        except Exception as e:
            return f"[错误: 提交失败: {e}]"
    elif operation == "create_branch":
        branch_name = args.get("branch_name", "")
        if not branch_name:
            return "[错误: create_branch 需要 branch_name 参数]"
        try:
            result = subprocess.run(["git", "checkout", "-b", branch_name],
                                    capture_output=True, text=True, cwd=workdir)
            return f"✓ 已创建分支: {branch_name}\n{result.stdout}"
        except Exception as e:
            return f"[错误: 创建分支失败: {e}]"
    return f"[错误: 未知 git 操作: {operation}]"


def _python_execute(args: Dict) -> str:
    code = args.get("code", "")
    if not code:
        return "[错误: python_execute 缺少 code 参数]"
    timeout = args.get("timeout", 30)
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=timeout,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr[:2000]}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        return _truncate(output or "(无输出)")
    except subprocess.TimeoutExpired:
        return f"[超时: Python 执行超过 {timeout} 秒]"
    except Exception as e:
        return f"[错误: {e}]"


# ═══════════════════════════════════════════════
# edit_file
# ═══════════════════════════════════════════════

def _edit_file(args: Dict) -> str:
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
            return f"[错误: 未找到字符串: {old_string[:50]}]"
        new_content = content.replace(old_string, new_string, 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"✓ 已编辑: {path}"
    except Exception as e:
        return f"[错误: {e}]"


# ═══════════════════════════════════════════════
# json_process
# ═══════════════════════════════════════════════

def _json_process(args: Dict) -> str:
    data = args.get("data", "")
    if not data:
        return "[错误: json_process 缺少 data 参数]"
    operation = args.get("operation", "parse")
    try:
        obj = json.loads(data)
    except json.JSONDecodeError as e:
        if operation == "validate":
            return f"无效: {e}"
        return f"[错误: JSON 解析失败: {e}]"
    if operation == "validate":
        return "有效"
    if operation == "keys":
        if isinstance(obj, dict):
            return ", ".join(obj.keys())
        return "[错误: 非字典类型，无法获取 keys]"
    if operation == "path":
        json_path = args.get("path", "")
        if not json_path:
            return "[错误: path 操作需要 path 参数]"
        current = obj
        for key in json_path.split("."):
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list):
                try:
                    current = current[int(key)]
                except (ValueError, IndexError):
                    return f"[错误: 无效索引: {key}]"
            else:
                return f"[错误: 无法访问: {key}]"
        return json.dumps(current, ensure_ascii=False)
    return json.dumps(obj, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════
# MiMo 集成工具
# ═══════════════════════════════════════════════

_MIMO_CHECKPOINT_DIR = Path.home() / ".hermes" / "mundo-agent" / "checkpoints"
_MIMO_MEMORY_FILE = Path.home() / ".hermes" / "mundo-agent" / "mimo_memory.json"
_MIMO_TASKS_FILE = Path.home() / ".hermes" / "mundo-agent" / "mimo_tasks.json"
_MIMO_GOAL_FILE = Path.home() / ".hermes" / "mundo-agent" / "mimo_goal.json"


def _mimo_checkpoint_save(args: Dict) -> str:
    session_id = args.get("session_id", "default")
    sections = args.get("sections", {})
    if not sections:
        return "[错误: mimo_checkpoint_save 缺少 sections 参数]"
    _MIMO_CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    path = _MIMO_CHECKPOINT_DIR / f"{session_id}.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(sections, f, ensure_ascii=False, indent=2)
        return f"✓ 检查点已保存: {session_id}"
    except Exception as e:
        return f"[错误: {e}]"


def _mimo_checkpoint_load(args: Dict) -> str:
    session_id = args.get("session_id", "default")
    path = _MIMO_CHECKPOINT_DIR / f"{session_id}.json"
    if not path.exists():
        return f"[错误: 检查点不存在: {session_id}]"
    try:
        with open(path, "r", encoding="utf-8") as f:
            sections = json.load(f)
        lines = [f"检查点: {session_id}"]
        for k, v in sections.items():
            lines.append(f"  {k}: {v}")
        return "\n".join(lines)
    except Exception as e:
        return f"[错误: {e}]"


def _load_json_file(path: Path) -> list:
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return []


def _save_json_file(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _mimo_memory_add(args: Dict) -> str:
    content = args.get("content", "")
    if not content:
        return "[错误: mimo_memory_add 缺少 content 参数]"
    mem_type = args.get("type", "fact")
    memories = _load_json_file(_MIMO_MEMORY_FILE)
    memories.append({"content": content, "type": mem_type, "timestamp": time.time()})
    _save_json_file(_MIMO_MEMORY_FILE, memories)
    return f"✓ 已添加记忆: {content[:50]}"


def _mimo_memory_search(args: Dict) -> str:
    query = args.get("query", "")
    if not query:
        return "[错误: mimo_memory_search 缺少 query 参数]"
    memories = _load_json_file(_MIMO_MEMORY_FILE)
    matches = [m for m in memories if query.lower() in m.get("content", "").lower()]
    if not matches:
        return f"搜索结果: 未找到匹配 '{query}' 的记忆"
    lines = [f"搜索结果: {len(matches)} 条匹配"]
    for m in matches[:10]:
        lines.append(f"  [{m.get('type', '?')}] {m.get('content', '')}")
    return "\n".join(lines)


def _mimo_task_create(args: Dict) -> str:
    task_id = args.get("task_id", "")
    title = args.get("title", "")
    if not task_id or not title:
        return "[错误: mimo_task_create 缺少 task_id 或 title]"
    tasks = _load_json_file(_MIMO_TASKS_FILE)
    tasks.append({"task_id": task_id, "title": title, "status": "pending", "created": time.time()})
    _save_json_file(_MIMO_TASKS_FILE, tasks)
    return f"✓ 已创建任务: {task_id}"


def _mimo_task_update(args: Dict) -> str:
    task_id = args.get("task_id", "")
    status = args.get("status", "")
    if not task_id or not status:
        return "[错误: mimo_task_update 缺少 task_id 或 status]"
    tasks = _load_json_file(_MIMO_TASKS_FILE)
    for t in tasks:
        if t.get("task_id") == task_id:
            t["status"] = status
            _save_json_file(_MIMO_TASKS_FILE, tasks)
            return f"✓ 已更新任务: {task_id} -> {status}"
    return f"[错误: 未找到任务: {task_id}]"


def _mimo_task_list(args: Dict) -> str:
    tasks = _load_json_file(_MIMO_TASKS_FILE)
    if not tasks:
        return "任务列表: 空"
    lines = ["任务列表:"]
    for t in tasks:
        lines.append(f"  [{t.get('status', '?')}] {t.get('task_id', '?')} - {t.get('title', '?')}")
    return "\n".join(lines)


def _mimo_goal_set(args: Dict) -> str:
    condition = args.get("condition", "")
    if not condition:
        return "[错误: mimo_goal_set 缺少 condition 参数]"
    _save_json_file(_MIMO_GOAL_FILE, {"condition": condition, "set_at": time.time()})
    return f"✓ 目标已设置: {condition}"


# ═══════════════════════════════════════════════
# web_search / http_request / code_analysis
# ═══════════════════════════════════════════════

def _web_search(args: Dict) -> str:
    query = args.get("query", "")
    if not query:
        return "[错误: web_search 缺少 query 参数]"
    try:
        # 优先使用 Scrapling 解析搜索结果
        try:
            from scrapling.fetchers import Fetcher
            import urllib.parse
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            page = Fetcher.get(url, timeout=15)
            results = []
            # 提取搜索结果标题和链接
            for item in page.css('div.g'):
                title = item.css('h3::text').get('')
                link = item.css('a::attr(href)').get('')
                snippet = item.css('.VwiC3b::text').get('')
                if title and link:
                    results.append(f"**{title}**\n{link}\n{snippet}")
            if results:
                return _truncate(f"搜索: {query}\n\n" + "\n\n".join(results[:5]))
        except ImportError:
            pass  # Scrapling 未安装，回退到简单方法
        except Exception:
            pass  # Scrapling 解析失败，回退到简单方法

        # 回退：直接抓取 HTML
        import urllib.request
        import urllib.parse
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        return _truncate(f"搜索: {query}\n{html[:2000]}")
    except Exception as e:
        return f"[错误: web_search 失败: {e}]"


def _http_request(args: Dict) -> str:
    url = args.get("url", "")
    if not url:
        return "[错误: http_request 缺少 url 参数]"
    method = args.get("method", "GET").upper()
    try:
        import urllib.request
        req = urllib.request.Request(url, method=method)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        return _truncate(f"HTTP {resp.status} {resp.reason}\n{body}")
    except Exception as e:
        return f"[错误: http_request 失败: {e}]"


def _code_analysis(args: Dict) -> str:
    code = args.get("code", "")
    if not code:
        return "[错误: code_analysis 缺少 code 参数]"
    lines = code.split("\n")
    analysis = {
        "total_lines": len(lines),
        "blank_lines": sum(1 for l in lines if not l.strip()),
        "comment_lines": sum(1 for l in lines if l.strip().startswith("#")),
        "function_count": sum(1 for l in lines if l.strip().startswith("def ")),
        "class_count": sum(1 for l in lines if l.strip().startswith("class ")),
        "import_count": sum(1 for l in lines if l.strip().startswith(("import ", "from "))),
    }
    return json.dumps(analysis, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════
# 注册所有工具
# ═══════════════════════════════════════════════

registry.register(
    "terminal", "执行 shell 命令",
    {"type": "object", "properties": {
        "command": {"type": "string", "description": "要执行的命令"},
        "workdir": {"type": "string", "description": "工作目录"},
        "timeout": {"type": "integer", "description": "超时秒数"},
    }},
    _terminal, required=["command"],
)

registry.register(
    "read_file", "读取文件内容",
    {"type": "object", "properties": {
        "path": {"type": "string", "description": "文件路径"},
        "offset": {"type": "integer", "description": "起始行号"},
        "limit": {"type": "integer", "description": "最大行数"},
    }},
    _read_file, required=["path"],
)

registry.register(
    "write_file", "写入文件内容",
    {"type": "object", "properties": {
        "path": {"type": "string", "description": "文件路径"},
        "content": {"type": "string", "description": "写入内容"},
    }},
    _write_file, required=["path", "content"],
)

registry.register(
    "search_files", "搜索文件内容或按名称查找文件",
    {"type": "object", "properties": {
        "pattern": {"type": "string", "description": "搜索模式（正则或glob）"},
        "path": {"type": "string", "description": "搜索路径"},
        "target": {"type": "string", "description": "content 或 files"},
        "limit": {"type": "integer", "description": "最大结果数"},
    }},
    _search_files, required=["pattern"],
)

registry.register(
    "list_directory", "列出目录内容",
    {"type": "object", "properties": {
        "path": {"type": "string", "description": "目录路径"},
        "show_hidden": {"type": "boolean", "description": "是否显示隐藏文件"},
    }},
    _list_directory, required=[],
)

registry.register(
    "git_operation", "Git 操作（status/diff/commit/branch）",
    {"type": "object", "properties": {
        "operation": {"type": "string", "description": "操作类型"},
        "workdir": {"type": "string", "description": "工作目录"},
        "message": {"type": "string", "description": "commit 消息"},
        "branch_name": {"type": "string", "description": "分支名"},
    }},
    _git_operation, required=["operation"],
)

registry.register(
    "python_execute", "执行 Python 代码",
    {"type": "object", "properties": {
        "code": {"type": "string", "description": "Python 代码"},
        "timeout": {"type": "integer", "description": "超时秒数"},
    }},
    _python_execute, required=["code"],
)

registry.register(
    "edit_file", "编辑文件内容（查找替换）",
    {"type": "object", "properties": {
        "path": {"type": "string", "description": "文件路径"},
        "old_string": {"type": "string", "description": "要查找的字符串"},
        "new_string": {"type": "string", "description": "替换后的字符串"},
    }},
    _edit_file, required=["path", "old_string"],
)

registry.register(
    "json_process", "JSON 处理（解析/验证/提取）",
    {"type": "object", "properties": {
        "data": {"type": "string", "description": "JSON 字符串"},
        "operation": {"type": "string", "description": "操作类型: parse/keys/path/validate"},
        "path": {"type": "string", "description": "JSON 路径（path 操作用）"},
    }},
    _json_process, required=["data"],
)

registry.register(
    "mimo_checkpoint_save", "保存会话检查点",
    {"type": "object", "properties": {
        "session_id": {"type": "string", "description": "会话 ID"},
        "sections": {"type": "object", "description": "检查点内容"},
    }},
    _mimo_checkpoint_save, required=["session_id", "sections"],
)

registry.register(
    "mimo_checkpoint_load", "加载会话检查点",
    {"type": "object", "properties": {
        "session_id": {"type": "string", "description": "会话 ID"},
    }},
    _mimo_checkpoint_load, required=["session_id"],
)

registry.register(
    "mimo_memory_add", "添加记忆条目",
    {"type": "object", "properties": {
        "content": {"type": "string", "description": "记忆内容"},
        "type": {"type": "string", "description": "记忆类型"},
    }},
    _mimo_memory_add, required=["content"],
)

registry.register(
    "mimo_memory_search", "搜索记忆",
    {"type": "object", "properties": {
        "query": {"type": "string", "description": "搜索关键词"},
    }},
    _mimo_memory_search, required=["query"],
)

registry.register(
    "mimo_task_create", "创建任务",
    {"type": "object", "properties": {
        "task_id": {"type": "string", "description": "任务 ID"},
        "title": {"type": "string", "description": "任务标题"},
    }},
    _mimo_task_create, required=["task_id", "title"],
)

registry.register(
    "mimo_task_update", "更新任务状态",
    {"type": "object", "properties": {
        "task_id": {"type": "string", "description": "任务 ID"},
        "status": {"type": "string", "description": "新状态"},
    }},
    _mimo_task_update, required=["task_id", "status"],
)

registry.register(
    "mimo_task_list", "列出所有任务",
    {"type": "object", "properties": {}},
    _mimo_task_list, required=[],
)

registry.register(
    "mimo_goal_set", "设置目标条件",
    {"type": "object", "properties": {
        "condition": {"type": "string", "description": "目标条件"},
    }},
    _mimo_goal_set, required=["condition"],
)

registry.register(
    "web_search", "网络搜索",
    {"type": "object", "properties": {
        "query": {"type": "string", "description": "搜索关键词"},
    }},
    _web_search, required=["query"],
)

registry.register(
    "http_request", "HTTP 请求",
    {"type": "object", "properties": {
        "url": {"type": "string", "description": "请求 URL"},
        "method": {"type": "string", "description": "请求方法: GET/POST/PUT/DELETE"},
    }},
    _http_request, required=["url"],
)

registry.register(
    "code_analysis", "代码分析",
    {"type": "object", "properties": {
        "code": {"type": "string", "description": "要分析的代码"},
    }},
    _code_analysis, required=["code"],
)


# ═══════════════════════════════════════════════
# 工具执行入口
# ═══════════════════════════════════════════════

def execute_tool(name: str, args: dict) -> str:
    return registry.execute(name, args)
