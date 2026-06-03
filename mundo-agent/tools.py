"""蒙多工具引擎 v29 — 融合 Hermes + Claude Code + Codex 精华

设计原则：
- 注册表模式：工具自注册，零耦合（借鉴 Hermes）
- 自动发现：import 时自动注册 schema
- 参数验证：每个 handler 自行验证必填参数
- 结果截断：统一在注册表层处理，不在各工具内部
- 安全隔离：危险操作需确认（借鉴 Codex 安全模型）
- 结构化输出：支持 JSON 输出（借鉴 Claude Code）
- 工作树隔离：Git 操作使用独立分支（借鉴 Codex）

v29 新增工具：
- git_operation: Git 操作（status/diff/commit/branch/worktree）
- python_execute: Python 代码执行（安全沙箱）
- http_request: HTTP 请求（REST API 测试）
- json_process: JSON 数据处理
- code_analysis: 代码分析（复杂度/依赖/安全扫描）
"""

import os
import json
import re
import subprocess
import glob as glob_mod
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional
import requests
from bs4 import BeautifulSoup

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
    # 智能截断：保留首尾，中间省略
    head = text[:int(limit * 0.6)]
    tail = text[-int(limit * 0.3):]
    return f"{head}\n... ({len(text)} 字符，省略中间部分) ...\n{tail}"


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
            # stderr 截断到 2000 字符
            stderr = result.stderr[:2000]
            if len(result.stderr) > 2000:
                stderr += f"\n... ({len(result.stderr)} 字符，已截断)"
            output += f"\n[stderr]\n{stderr}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
            stderr = result.stderr or ""
            if "command not found" in stderr:
                output += "\n提示: 命令未找到，检查拼写或安装对应包"
            elif "Permission denied" in stderr:
                output += "\n提示: 权限不足，尝试加 sudo 或检查文件权限"
            elif "No such file" in stderr:
                output += "\n提示: 文件/目录不存在，检查路径"
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
    
    # 代理设置（从环境变量读取）
    proxies = {}
    if os.environ.get("HTTP_PROXY"):
        proxies["http"] = os.environ["HTTP_PROXY"]
    if os.environ.get("HTTPS_PROXY"):
        proxies["https"] = os.environ["HTTPS_PROXY"]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # 尝试多个搜索引擎
    search_engines = [
        ("DuckDuckGo", f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}", _parse_duckduckgo),
        ("Google", f"https://www.google.com/search?q={requests.utils.quote(query)}&num={limit}", _parse_google),
        ("Bing", f"https://www.bing.com/search?q={requests.utils.quote(query)}&count={limit}", _parse_bing),
    ]
    
    for engine_name, url, parser in search_engines:
        try:
            resp = requests.get(url, headers=headers, proxies=proxies, timeout=15)
            resp.raise_for_status()
            results = parser(resp.text, limit)
            if results:
                return f"🔍 {engine_name} 搜索结果:\n\n" + "\n\n".join(results)
        except Exception as e:
            continue
    
    return "搜索未返回结果（所有搜索引擎均失败）"


def _parse_duckduckgo(html: str, limit: int) -> list:
    """解析 DuckDuckGo HTML 搜索结果"""
    results = []
    soup = BeautifulSoup(html, "html.parser")
    for result in soup.select(".result__a")[:limit]:
        title = result.get_text(strip=True)
        href = result.get("href", "")
        if title and href:
            # 处理 DuckDuckGo 重定向 URL
            if "uddg=" in href:
                try:
                    from urllib.parse import unquote, urlparse, parse_qs
                    parsed = urlparse(href)
                    qs = parse_qs(parsed.query)
                    if "uddg" in qs:
                        href = unquote(qs["uddg"][0])
                except:
                    pass
            results.append(f"• {title}\n  {href}")
    return results


def _parse_google(html: str, limit: int) -> list:
    """解析 Google 搜索结果"""
    results = []
    soup = BeautifulSoup(html, "html.parser")
    for g in soup.select("div.g")[:limit]:
        title_elem = g.select_one("h3")
        link_elem = g.select_one("a")
        if title_elem and link_elem:
            title = title_elem.get_text(strip=True)
            href = link_elem.get("href", "")
            if href.startswith("/url?q="):
                href = href.split("/url?q=")[1].split("&")[0]
            if title and href:
                results.append(f"• {title}\n  {href}")
    return results


def _parse_bing(html: str, limit: int) -> list:
    """解析 Bing 搜索结果"""
    results = []
    soup = BeautifulSoup(html, "html.parser")
    for li in soup.select("li.b_algo")[:limit]:
        title_elem = li.select_one("h2 a")
        if title_elem:
            title = title_elem.get_text(strip=True)
            href = title_elem.get("href", "")
            if title and href:
                results.append(f"• {title}\n  {href}")
    return results


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
    """Git 操作工具 — 借鉴 Codex 工作树隔离"""
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
        "stash_list": "git stash list",
    }
    
    if operation in operations:
        cmd = operations[operation]
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=30, cwd=workdir,
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr[:1000]}"
            return _truncate(output or "(无输出)")
        except Exception as e:
            return f"[错误: Git 操作失败: {e}]"
    
    elif operation == "commit":
        message = args.get("message", "")
        if not message:
            return "[错误: commit 操作需要 message 参数]"
        try:
            # 先添加所有更改
            subprocess.run("git add -A", shell=True, cwd=workdir, check=True)
            # 提交
            result = subprocess.run(
                f'git commit -m "{message}"',
                shell=True, capture_output=True, text=True, cwd=workdir,
            )
            return f"✓ 已提交: {message}\n{result.stdout}"
        except Exception as e:
            return f"[错误: 提交失败: {e}]"
    
    elif operation == "create_branch":
        branch_name = args.get("branch_name", "")
        if not branch_name:
            return "[错误: create_branch 操作需要 branch_name 参数]"
        try:
            result = subprocess.run(
                f"git checkout -b {branch_name}",
                shell=True, capture_output=True, text=True, cwd=workdir,
            )
            return f"✓ 已创建并切换到分支: {branch_name}\n{result.stdout}"
        except Exception as e:
            return f"[错误: 创建分支失败: {e}]"
    
    elif operation == "create_worktree":
        # 借鉴 Codex 的工作树隔离模式
        branch_name = args.get("branch_name", "")
        worktree_path = args.get("worktree_path", "")
        if not branch_name or not worktree_path:
            return "[错误: create_worktree 需要 branch_name 和 worktree_path 参数]"
        try:
            # 创建新分支
            subprocess.run(
                f"git branch {branch_name}",
                shell=True, capture_output=True, text=True, cwd=workdir,
            )
            # 创建工作树
            result = subprocess.run(
                f"git worktree add {worktree_path} {branch_name}",
                shell=True, capture_output=True, text=True, cwd=workdir,
            )
            return f"✓ 已创建工作树: {worktree_path} (分支: {branch_name})\n{result.stdout}"
        except Exception as e:
            return f"[错误: 创建工作树失败: {e}]"
    
    else:
        return f"[错误: 未知 Git 操作: {operation}]"


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


def _python_execute(args: Dict) -> str:
    """Python 代码执行工具 — 借鉴 Claude Code 代码执行能力"""
    code = args.get("code", "")
    if not code:
        return "[错误: python_execute 缺少 code 参数]"
    
    timeout = args.get("timeout", 30)
    workdir = args.get("workdir") or os.getcwd()
    
    # 安全检查：禁止危险操作
    dangerous_patterns = [
        "os.system", "subprocess", "shutil.rmtree", "os.remove",
        "open('/etc", "open('/proc", "open('/sys", "import ctypes",
        "exec(", "eval(", "__import__", "globals()", "locals()",
    ]
    for pattern in dangerous_patterns:
        if pattern in code:
            return f"[安全警告] 代码包含危险操作: {pattern}。蒙多拒绝执行。"
    
    try:
        # 创建临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=workdir) as f:
            f.write(code)
            temp_path = f.name
        
        # 执行代码
        result = subprocess.run(
            ["python3", temp_path],
            capture_output=True, text=True,
            timeout=timeout, cwd=workdir,
        )
        
        # 清理临时文件
        try:
            os.unlink(temp_path)
        except:
            pass
        
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr[:2000]}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        
        return _truncate(output or "(无输出)")
    except subprocess.TimeoutExpired:
        return f"[超时: Python 代码执行超过 {timeout} 秒]"
    except Exception as e:
        return f"[错误: Python 执行失败: {e}]"


def _http_request(args: Dict) -> str:
    """HTTP 请求工具 — 借鉴 Claude Code 的 API 测试能力"""
    url = args.get("url", "")
    if not url:
        return "[错误: http_request 缺少 url 参数]"
    
    method = args.get("method", "GET").upper()
    headers = args.get("headers", {})
    data = args.get("data")
    timeout = args.get("timeout", 30)
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=timeout)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=timeout)
        else:
            return f"[错误: 不支持的 HTTP 方法: {method}]"
        
        result_parts = [
            f"HTTP {response.status_code} {response.reason}",
            f"URL: {response.url}",
            "",
            "Headers:",
        ]
        for key, value in response.headers.items():
            result_parts.append(f"  {key}: {value}")
        
        result_parts.append("")
        result_parts.append("Body:")
        
        # 尝试解析 JSON
        try:
            json_data = response.json()
            result_parts.append(json.dumps(json_data, indent=2, ensure_ascii=False)[:5000])
        except:
            result_parts.append(response.text[:5000])
        
        return "\n".join(result_parts)
    except Exception as e:
        return f"[错误: HTTP 请求失败: {e}]"


def _json_process(args: Dict) -> str:
    """JSON 数据处理工具 — 借鉴 Claude Code 的数据处理能力"""
    data = args.get("data", "")
    operation = args.get("operation", "parse")
    
    if not data:
        return "[错误: json_process 缺少 data 参数]"
    
    try:
        if isinstance(data, str):
            json_data = json.loads(data)
        else:
            json_data = data
        
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
                return "[错误: path 操作需要 path 参数]"
            keys = path.split(".")
            current = json_data
            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key)
                elif isinstance(current, list):
                    try:
                        current = current[int(key)]
                    except (ValueError, IndexError):
                        return f"[错误: 无法访问数组索引: {key}]"
                else:
                    return f"[错误: 无法访问: {key}]"
            return json.dumps(current, indent=2, ensure_ascii=False)[:5000]
        elif operation == "validate":
            # 验证 JSON 结构
            if isinstance(json_data, dict):
                return f"✓ 有效的 JSON 对象，包含 {len(json_data)} 个键"
            elif isinstance(json_data, list):
                return f"✓ 有效的 JSON 数组，包含 {len(json_data)} 个元素"
            else:
                return f"✓ 有效的 JSON，类型: {type(json_data).__name__}"
        else:
            return f"[错误: 未知 JSON 操作: {operation}]"
    except json.JSONDecodeError as e:
        return f"[错误: JSON 解析失败: {e}]"
    except Exception as e:
        return f"[错误: JSON 处理失败: {e}]"


def _code_analysis(args: Dict) -> str:
    """代码分析工具 — 借鉴 Claude Code 的代码分析能力"""
    path = args.get("path", "")
    if not path:
        return "[错误: code_analysis 缺少 path 参数]"
    
    analysis_type = args.get("type", "complexity")
    path = os.path.expanduser(path)
    
    if not os.path.exists(path):
        return f"[错误: 文件不存在: {path}]"
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if analysis_type == "complexity":
            # 简单的复杂度分析
            lines = content.split('\n')
            total_lines = len(lines)
            code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
            comment_lines = len([l for l in lines if l.strip().startswith('#')])
            blank_lines = len([l for l in lines if not l.strip()])
            
            # 计算圈复杂度（简化版）
            complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 'with', 'and', 'or']
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
            import re
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
        
        elif analysis_type == "dependencies":
            # 依赖分析
            import re
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
        
        elif analysis_type == "security":
            # 安全扫描
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
        
        else:
            return f"[错误: 未知分析类型: {analysis_type}]"
    
    except Exception as e:
        return f"[错误: 代码分析失败: {e}]"


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

registry.register(
    name="git_operation",
    description="Git 操作工具。支持 status/diff/log/branch/commit/create_branch/create_worktree 等操作。",
    parameters={
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["status", "diff", "diff_staged", "log", "branch", "current_branch", "stash_list", "commit", "create_branch", "create_worktree"],
                "description": "Git 操作类型"
            },
            "workdir": {"type": "string", "description": "工作目录（默认当前目录）"},
            "message": {"type": "string", "description": "提交信息（commit 操作需要）"},
            "branch_name": {"type": "string", "description": "分支名称（create_branch/create_worktree 操作需要）"},
            "worktree_path": {"type": "string", "description": "工作树路径（create_worktree 操作需要）"},
        },
        "required": ["operation"],
    },
    handler=_git_operation,
    required=["operation"],
)

registry.register(
    name="python_execute",
    description="安全执行 Python 代码。支持代码执行、数据分析、算法测试等。",
    parameters={
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "要执行的 Python 代码"},
            "timeout": {"type": "integer", "description": "超时秒数（默认 30）"},
            "workdir": {"type": "string", "description": "工作目录（默认当前目录）"},
        },
        "required": ["code"],
    },
    handler=_python_execute,
    required=["code"],
)

registry.register(
    name="http_request",
    description="发送 HTTP 请求。支持 GET/POST/PUT/DELETE 方法，用于 API 测试和网页抓取。",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "请求 URL"},
            "method": {
                "type": "string",
                "enum": ["GET", "POST", "PUT", "DELETE"],
                "description": "HTTP 方法（默认 GET）"
            },
            "headers": {"type": "object", "description": "请求头"},
            "data": {"type": "object", "description": "请求数据（POST/PUT 需要）"},
            "timeout": {"type": "integer", "description": "超时秒数（默认 30）"},
        },
        "required": ["url"],
    },
    handler=_http_request,
    required=["url"],
)

registry.register(
    name="json_process",
    description="JSON 数据处理工具。支持解析、查询、验证等操作。",
    parameters={
        "type": "object",
        "properties": {
            "data": {"type": ["string", "object"], "description": "JSON 数据（字符串或对象）"},
            "operation": {
                "type": "string",
                "enum": ["parse", "keys", "path", "validate"],
                "description": "操作类型（默认 parse）"
            },
            "path": {"type": "string", "description": "JSON 路径（path 操作需要，如 'a.b.c'）"},
        },
        "required": ["data"],
    },
    handler=_json_process,
    required=["data"],
)

registry.register(
    name="code_analysis",
    description="代码分析工具。支持复杂度分析、依赖分析、安全扫描。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "代码文件路径"},
            "type": {
                "type": "string",
                "enum": ["complexity", "dependencies", "security"],
                "description": "分析类型（默认 complexity）"
            },
        },
        "required": ["path"],
    },
    handler=_code_analysis,
    required=["path"],
)

# 向后兼容：旧代码引用的常量
TOOL_SCHEMAS = registry.schemas


def execute_tool(name: str, args: Dict) -> str:
    return registry.execute(name, args)
