"""蒙多执行控制台 v1.2.6 — 极简艺术家

设计原则：
- 少即是多。每一像素都有存在的理由
- 金色是唯一强调色，其余全是灰
- 没有边框、没有装饰、没有噪音
- 状态栏一行，输入栏一个提示符，完成栏一行
- 工具输出精简，不展示垃圾
- 完成后必须有清晰的内容总结
"""

import sys
import time as _time
from pathlib import Path
from typing import Optional, List

from rich.console import Console
from rich.theme import Theme

# ═══════════════════════════════════════════════
# 极简色系 — 金 + 灰
# ═══════════════════════════════════════════════

MUNDO_THEME = Theme({
    "gold": "bold #d4a017",
    "gold.dim": "#a08030",
    "ok": "#7ec699",
    "err": "#f07178",
    "warn": "#f0c674",
    "hi": "#6a9ee5",
    "dim": "#555555",
    "muted": "#444444",
    "text": "#cccccc",
    "sub": "#888888",
})

console = Console(theme=MUNDO_THEME, highlight=False, force_terminal=True)

TOOL_EMOJI = {
    "terminal": ">", "read_file": "r", "write_file": "w",
    "edit_file": "e", "search_files": "f", "web_search": "s",
    "list_directory": "l", "git_operation": "g", "python_execute": "py",
    "http_request": "h", "json_process": "j", "code_analysis": "a",
}

TOOL_VERB = {
    "terminal": "$", "read_file": "read", "write_file": "write",
    "edit_file": "edit", "search_files": "grep", "web_search": "search",
    "list_directory": "ls", "git_operation": "git", "python_execute": "exec",
    "http_request": "http", "json_process": "json", "code_analysis": "analyze",
}

SLASH_COMMANDS = [
    "/help", "/quit", "/exit", "/clear", "/status", "/reset",
    "/model", "/models", "/switch", "/providers", "/add", "/setup",
    "/remember", "/recall", "/forget", "/memories", "/memory",
    "/compact", "/context", "/effort", "/tools",
    "/search", "/projects",
]


def _fmt_tok(n: int) -> str:
    if n < 0:
        return "—"
    if n < 1000:
        return str(n)
    if n < 1000000:
        return f"{n / 1000:.0f}K"
    return f"{n / 1000000:.1f}M"


def _elapsed(start: float) -> str:
    if start <= 0:
        return "—"
    s = _time.time() - start
    if s < 60:
        return f"{int(s)}s"
    m = int(s // 60)
    if m < 60:
        return f"{m}m{int(s % 60)}s"
    h = int(m // 60)
    return f"{h}h{m % 60}m"


def _trunc(s: str, n: int = 40) -> str:
    s = str(s)
    return (s[:n-3] + "...") if len(s) > n else s


def _path_short(p: str, n: int = 35) -> str:
    p = str(p)
    return ("..." + p[-(n-3):]) if len(p) > n else p


def _bar(percent: Optional[int], w: int = 8) -> str:
    if percent is None:
        return "·" * w
    filled = max(0, min(w, round(w * percent / 100)))
    return "█" * filled + "·" * (w - filled)


# ═══════════════════════════════════════════════
# Slash 命令自动补全器
# ═══════════════════════════════════════════════

class SlashCompleter:
    def __repr__(self) -> str:
        return f"SlashCompleter(commands={len(self.commands)})"

    def __init__(self, commands: List[str] = None):
        self.commands = commands or SLASH_COMMANDS

    def get_completions(self, document, complete_event):
        from prompt_toolkit.completion import Completion
        text = document.text_before_cursor
        if not text.startswith("/"):
            return
        for cmd in self.commands:
            if cmd.startswith(text):
                yield Completion(cmd, start_position=-len(text))

    async def get_completions_async(self, document, complete_event):
        for c in self.get_completions(document, complete_event):
            yield c


# ═══════════════════════════════════════════════
# TaskConsole — 极简
# ═══════════════════════════════════════════════

class TaskConsole:

    def __repr__(self) -> str:
        return f"TaskConsole(model={self._model})"

    def __init__(self):
        self._model = ""
        self._stats = None
        self._is_running = False
        self._task_start = 0.0
        self._session_start = _time.time()
        self._was_streamed = False
        self._current_tool_start = 0.0
        self._last_tool_args = {}
        self._context_tokens = 0
        self._context_limit = 128000
        self._cached_tokens = 0
        self._total_prompt_tokens = 0
        self._tools_used: List[str] = []

    def init_screen(self, model_display: str, version: str = ""):
        self._model = model_display
        self._session_start = _time.time()

    # ═══════════════════════════════════════
    # 状态栏 — 一行极简
    # ═══════════════════════════════════════

    def _build_status_bar(self) -> str:
        model = self._model.split("/")[-1] if "/" in self._model else self._model
        if len(model) > 20:
            model = model[:17] + "..."

        session_elapsed = _elapsed(self._session_start)

        parts = [f"[gold]{model}[/]"]

        # 缓存命中率 — 核心指标
        if self._total_prompt_tokens > 0:
            cache_rate = round(self._cached_tokens / self._total_prompt_tokens * 100)
            cache_color = "ok" if cache_rate >= 50 else "warn" if cache_rate >= 20 else "dim"
            parts.append(f"[{cache_color}]{cache_rate}% cache[/]")
        else:
            parts.append(f"[dim]--% cache[/]")

        # 上下文使用率 — 用进度条
        percent = round(self._context_tokens / self._context_limit * 100) if self._context_limit > 0 else 0
        percent = max(0, min(100, percent))
        bar = _bar(percent, 8)
        parts.append(f"[dim]{bar}[/] [dim]{percent}%[/]")

        parts.append(f"[dim]{session_elapsed}[/]")

        if self._is_running and self._task_start > 0:
            parts.append(f"[gold.dim]{_elapsed(self._task_start)}[/]")

        return " · ".join(parts)

    def print_status(self):
        console.print(f"\n  [dim]{self._build_status_bar()}[/]")

    def update_live_status(self, stats=None):
        if stats:
            self._stats = stats

    def update_context_tokens(self, tokens: int, limit: int = 0):
        self._context_tokens = tokens
        if limit > 0:
            self._context_limit = limit

    def update_cache_stats(self, cached_tokens: int, total_prompt_tokens: int):
        self._cached_tokens = cached_tokens
        self._total_prompt_tokens = total_prompt_tokens

    # ═══════════════════════════════════════
    # 流式输出
    # ═══════════════════════════════════════

    def stream_start(self, turn: int):
        self._was_streamed = False  # 每轮重置，只在实际收到内容时设 True
        sys.stdout.write("\n")
        sys.stdout.flush()

    def stream_text(self, text: str):
        self._was_streamed = True  # 确实有内容流出才标记
        if self._stats:
            self._stats.completion_tokens = max(
                self._stats.completion_tokens, len(text) * 2 // 3
            )
            self._stats.total_tokens = self._stats.prompt_tokens + self._stats.completion_tokens
        sys.stdout.write(text)
        sys.stdout.flush()

    def stream_end(self, turn: int):
        sys.stdout.write("\n")
        sys.stdout.flush()

    # ═══════════════════════════════════════
    # 粘贴折叠 — 蒙多洁癖版
    # ═══════════════════════════════════════

    _paste_counter = 0

    @staticmethod
    def expand_paste_refs(text: str) -> str:
        """提交前展开占位符为原始内容"""
        import re
        ref_re = re.compile(r'\[Pasted text #\d+: \d+ lines → (.+?)\]')
        if "[Pasted text #" not in text:
            return text

        def _load(match):
            path = Path(match.group(1))
            try:
                return path.read_text(encoding="utf-8")
            except Exception:
                return match.group(0)

        return ref_re.sub(_load, text)

    # ═══════════════════════════════════════
    # 输入 — 一个提示符
    # ═══════════════════════════════════════

    def read_input(self) -> str:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.styles import Style
        from prompt_toolkit.key_binding import KeyBindings

        hist_path = str(Path.home() / ".hermes" / "mundo-agent" / ".mundo_history")
        style = Style.from_dict({"prompt": "#d4a017 bold"})

        kb = KeyBindings()
        stored = {"text": "", "label": ""}
        navigating = [False]

        @kb.add("enter")
        def _(event):
            buf = event.current_buffer
            if stored["text"] and buf.text.strip() == stored["label"]:
                result = stored["text"]
            else:
                result = buf.text.rstrip()
            event.app.exit(result=result)

        @kb.add("escape", "enter")
        def _(event):
            event.current_buffer.newline()

        @kb.add("up")
        def _(event):
            navigating[0] = True
            event.current_buffer.history_backward()
            navigating[0] = False

        @kb.add("down")
        def _(event):
            navigating[0] = True
            event.current_buffer.history_forward()
            navigating[0] = False

        session = PromptSession(
            history=FileHistory(hist_path),
            style=style,
            key_bindings=kb,
            multiline=True,
            completer=SlashCompleter(),
            complete_while_typing=True,
            prompt_continuation="",
        )

        buf = session.app.current_buffer
        collapsing = [False]

        def _on_change(_buf):
            if collapsing[0] or navigating[0]:
                return
            text = _buf.text
            if text.count('\n') < 1 and len(text) <= 200:
                stored["text"] = ""
                stored["label"] = ""
                return
            collapsing[0] = True
            path, label = self._save_paste(text)
            stored["text"] = text
            stored["label"] = label
            _buf.text = label
            _buf.cursor_position = len(label)
            collapsing[0] = False

        buf.on_text_changed += _on_change

        try:
            from prompt_toolkit.formatted_text import HTML
            result = session.prompt(HTML("<ansiyellow><b> ❯ </b></ansiyellow>"))
            return (result or "").strip()
        except (EOFError, KeyboardInterrupt):
            return ""

    def _save_paste(self, text: str) -> tuple:
        """保存粘贴内容到文件，返回 (文件路径, 显示标签)"""
        TaskConsole._paste_counter += 1
        paste_dir = Path.home() / ".hermes" / "mundo-agent" / "pastes"
        paste_dir.mkdir(parents=True, exist_ok=True)
        n = TaskConsole._paste_counter
        ts = _time.strftime('%H:%M:%S')
        paste_file = paste_dir / f"paste_{n}_{ts}.txt"
        paste_file.write_text(text, encoding="utf-8")
        lines = text.count('\n') + 1
        kb = len(text) / 1024
        label = f"[{n}: {lines}行 {kb:.1f}KB → {paste_file}]"
        console.print(f"  [dim]📎 {lines}行 {kb:.1f}KB[/]")
        return (str(paste_file), label)

    # ═══════════════════════════════════════
    # 日志 — 极简活动流
    # ═══════════════════════════════════════

    def log_thinking(self, turn: int):
        self._task_start = _time.time()
        self._tools_used = []
        console.print(f"  [dim]. . .[/]")

    def log_task_accepted(self, task_text: str):
        preview = _trunc(task_text.replace("\n", " "), 60)
        console.print(f"  [gold]{preview}[/]")

    def log_tool_start(self, tool_name: str, tool_args: dict):
        tag = TOOL_EMOJI.get(tool_name, "?")
        info = self._fmt_tool_preview(tool_name, tool_args)
        if tool_name not in self._tools_used:
            self._tools_used.append(tool_name)
        console.print(f"  [dim]{tag} {tool_name}[/] [dim]{info}[/]")
        self._current_tool_start = _time.time()

    def log_tool_output(self, tool_name: str, output: str, is_error: bool = False):
        if not output:
            return
        lines = output.strip().split("\n")
        # 工具输出精简：最多 5 行
        if len(lines) > 5:
            display = lines[:3] + [f"  +{len(lines) - 4} lines"] + lines[-1:]
        else:
            display = lines
        for line in display:
            colored = self._color_line(line, tool_name, is_error)
            console.print(f"  [dim]│[/] {colored}")

    def log_tool_done(self, tool_name: str, duration: float):
        tag = TOOL_EMOJI.get(tool_name, "?")
        dur = f"{duration:.1f}s"
        console.print(f"  [dim]{tag} done {dur}[/]")

    def log_response(self, text: str):
        """显示回复内容 — 流式和非流式都走这里"""
        if not text or not text.strip():
            return
        console.print()
        for line in text.strip().split("\n"):
            console.print(f"  [text]{line}[/]")

    def log_error(self, error: str):
        console.print(f"\n  [err]{error}[/]")

    def log_budget_warning(self, budget):
        ratio = int(budget.usage_ratio * 100)
        console.print(f"  [warn]context {ratio}% — /compact[/]")

    def log_compress(self, old_count, new_count, old_tokens, new_tokens):
        saved = old_tokens - new_tokens
        console.print(f"  [dim]compressed {old_count}→{new_count}, saved ~{_fmt_tok(saved)} tok[/]")

    def log_done(self, stats):
        """完成 — 一行极简统计"""
        self._stats = stats
        elapsed = stats.elapsed_str
        tok = _fmt_tok(stats.total_tokens)
        turns = stats.turns
        tools_count = stats.tool_calls_count

        parts = [f"[dim]{elapsed}[/]"]
        if tok and tok != "0":
            parts.append(f"[dim]{tok}[/]")
        if turns > 1:
            parts.append(f"[dim]T{turns}[/]")
        if tools_count > 0:
            parts.append(f"[dim]{tools_count} tools[/]")
        if stats.errors_count > 0:
            parts.append(f"[err]{stats.errors_count} err[/]")

        console.print(f"\n  [gold]✓[/] [dim]{' · '.join(parts)}[/]")

        self._is_running = False
        self._task_start = 0.0

    def log_llm_stats(self, prompt_tokens: int, completion_tokens: int,
                      cached_tokens: int = 0, total_context: int = 0):
        # 累积缓存统计（跨多轮）
        self._cached_tokens += cached_tokens
        self._total_prompt_tokens += prompt_tokens
        if total_context > 0:
            self.update_context_tokens(total_context)

    # ── 任务状态 ──

    def start_task(self):
        self._is_running = True
        self._task_start = _time.time()
        # 重置缓存统计（每次任务独立计算）
        self._cached_tokens = 0
        self._total_prompt_tokens = 0

    def stop_task(self):
        self._is_running = False

    def _update_stats(self, stats):
        self._stats = stats

    def cleanup(self):
        pass

    # ── 颜色映射 ──

    def _color_line(self, line: str, tool: str, is_error: bool = False) -> str:
        s = line.strip()
        if is_error or any(k in s.lower() for k in ["error", "err:", "错误", "failed", "fatal", "traceback"]):
            return f"[err]{line}[/]"
        if any(k in s.lower() for k in ["warn", "warning", "警告"]):
            return f"[warn]{line}[/]"
        if any(k in s for k in ["✓", "success", "ok", "完成", "done"]):
            return f"[ok]{line}[/]"
        if tool == "terminal":
            return self._code_color(line)
        return f"[sub]{line}[/]"

    def _code_color(self, line: str) -> str:
        s = line.strip()
        if s.startswith("$") or s.startswith("#"):
            return f"[ok]{line}[/]"
        kw = ["def ", "class ", "import ", "from ", "if ", "elif ", "return ",
              "for ", "while ", "try:", "except", "with ", "async "]
        if any(s.startswith(k) or f" {k}" in s for k in kw):
            return f"[hi]{line}[/]"
        return f"[sub]{line}[/]"

    def _fmt_tool_preview(self, name: str, args: dict) -> str:
        if name == "terminal":
            return _trunc(args.get("command", ""), 42)
        if name in ("read_file", "write_file", "edit_file"):
            return _path_short(args.get("path", ""))
        if name == "search_files":
            return _trunc(args.get("pattern", ""), 35)
        if name == "web_search":
            return _trunc(args.get("query", ""), 42)
        if name == "list_directory":
            return _path_short(args.get("path", "."))
        return ""
