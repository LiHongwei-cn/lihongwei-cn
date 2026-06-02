"""蒙多执行控制台 v27 — Hermes 活动流 + Rich 渲染 + 命令自动补全

v27 改进（vs v26）：
- slash 命令自动补全（借鉴 Hermes prompt_toolkit completer）
- 预算警告显示
- 压缩通知显示
- 错误分类显示（可重试 vs 致命）
"""

import sys
import shutil
import time as _time
from pathlib import Path
from typing import Optional, List

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.theme import Theme

# ═══════════════════════════════════════════════
# Catppuccin Mocha + 金色主题
# ═══════════════════════════════════════════════

MUNDO_THEME = Theme({
    "gold": "bold #d4a017",
    "gold.dim": "#b8860b",
    "success": "#98c379",
    "error": "#e06c75",
    "warning": "#e5c07b",
    "info": "#61afef",
    "cyan": "#56b6c2",
    "purple": "#c678dd",
    "muted": "#5c6370",
    "text": "#abb2bf",
    "subtext": "#9da5b4",
    "feed": "#636d83",
})

console = Console(theme=MUNDO_THEME, highlight=False, force_terminal=True)

_FEED = "┊"

TOOL_EMOJI = {
    "terminal": "💻",
    "read_file": "📖",
    "write_file": "✍️ ",
    "edit_file": "🔧",
    "search_files": "🔎",
    "web_search": "🔍",
    "list_directory": "📁",
}

TOOL_VERB = {
    "terminal": "$",
    "read_file": "read",
    "write_file": "write",
    "edit_file": "edit",
    "search_files": "grep",
    "web_search": "search",
    "list_directory": "ls",
}

# slash 命令列表（自动补全用）
SLASH_COMMANDS = [
    "/help", "/quit", "/exit", "/clear", "/status", "/reset",
    "/model", "/models", "/switch", "/providers", "/add", "/setup",
    "/remember", "/recall", "/forget", "/memories", "/memory",
    "/compact", "/context", "/effort", "/tools",
]


def _fmt_tok(n: int) -> str:
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
    return f"{int(m // 60)}h{m % 60}m"


def _trunc(s: str, n: int = 40) -> str:
    s = str(s)
    return (s[:n-3] + "...") if len(s) > n else s


def _path_short(p: str, n: int = 35) -> str:
    p = str(p)
    return ("..." + p[-(n-3):]) if len(p) > n else p


# ═══════════════════════════════════════════════
# Slash 命令自动补全器
# ═══════════════════════════════════════════════

class SlashCompleter:
    """prompt_toolkit 自动补全器 — 输入 / 时显示可用命令"""

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


# ═══════════════════════════════════════════════
# TaskConsole — Hermes 活动流模式
# ═══════════════════════════════════════════════

class TaskConsole:

    def __init__(self):
        self._model = ""
        self._stats = None
        self._is_running = False
        self._task_start = 0.0
        self._session_start = _time.time()
        self._was_streamed = False
        self._current_tool_start = 0.0
        self._last_tool_args = {}

    def init_screen(self, model_display: str, version: str = ""):
        self._model = model_display
        self._session_start = _time.time()

    def _build_status(self) -> Text:
        tok = self._stats.total_tokens if self._stats else 0
        model = self._model.split("/")[-1] if "/" in self._model else self._model
        t = Text()
        t.append("MUNDO", style="bold gold")
        t.append(" · ", style="muted")
        t.append(model, style="text")
        if tok > 0:
            t.append(" · ", style="muted")
            t.append(f"{_fmt_tok(tok)} tok", style="cyan")
        if self._is_running and self._task_start > 0:
            t.append(" · ", style="muted")
            t.append(f"⏱{_elapsed(self._task_start)}", style="gold.dim")
        return t

    def print_status(self):
        console.print(self._build_status())

    def update_live_status(self, stats=None):
        if stats:
            self._stats = stats

    # ═══════════════════════════════════════
    # 流式输出
    # ═══════════════════════════════════════

    def stream_start(self, turn: int):
        self._was_streamed = True
        sys.stdout.write("\n")
        sys.stdout.flush()

    def stream_text(self, text: str):
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
    # 输入 — prompt_toolkit + 自动补全
    # ═══════════════════════════════════════

    def read_input(self) -> str:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.styles import Style
        from prompt_toolkit.key_binding import KeyBindings

        self.print_status()

        hist_path = str(Path.home() / ".hermes" / "mundo-agent" / ".mundo_history")
        style = Style.from_dict({"prompt": "#d4a017 bold"})

        kb = KeyBindings()

        @kb.add("enter")
        def _(event):
            buf = event.current_buffer
            text = buf.text
            cursor = buf.cursor_position
            if cursor >= len(text.rstrip()):
                buf.text = text.rstrip()
                buf.validate_and_handle()
            else:
                buf.newline()

        @kb.add("escape", "enter")
        def _(event):
            buf = event.current_buffer
            buf.text = buf.text.rstrip()
            buf.validate_and_handle()

        completer = SlashCompleter()

        session = PromptSession(
            history=FileHistory(hist_path),
            style=style,
            key_bindings=kb,
            multiline=True,
            completer=completer,
            complete_while_typing=True,
        )
        try:
            return session.prompt("❯ ").strip()
        except (EOFError, KeyboardInterrupt):
            return ""

    # ═══════════════════════════════════════
    # 日志 — Hermes ┊ 活动流模式
    # ═══════════════════════════════════════

    def log_thinking(self, turn: int):
        self._task_start = _time.time()
        console.print(f"  [gold.dim]{_FEED}[/] [subtext]思考中...[/] [dim](Turn {turn})[/]")

    def log_task_accepted(self, task_text: str):
        preview = _trunc(task_text.replace("\n", " "), 60)
        console.print(f"\n  [success]{_FEED}[/] [dim]已接收[/] [subtext]{preview}[/]")

    def log_tool_start(self, tool_name: str, tool_args: dict):
        emoji = TOOL_EMOJI.get(tool_name, "⚡")
        info = self._fmt_tool_preview(tool_name, tool_args)
        console.print(f"  [feed]{_FEED}[/] {emoji} [dim]preparing[/] [text]{tool_name}[/] [dim]{info}[/]")
        self._current_tool_start = _time.time()
        if self._stats:
            self._stats._active_tools.append(tool_name)

    def log_tool_output(self, tool_name: str, output: str, is_error: bool = False):
        if not output:
            return
        lines = output.strip().split("\n")
        if len(lines) > 20:
            display = lines[:10] + [f"  ... ({len(lines) - 15} 行省略)"] + lines[-5:]
        else:
            display = lines
        for line in display:
            colored = self._color_line(line, tool_name, is_error)
            console.print(f"  [feed]{_FEED}[/] {colored}")

    def log_tool_done(self, tool_name: str, duration: float):
        emoji = TOOL_EMOJI.get(tool_name, "⚡")
        verb = TOOL_VERB.get(tool_name, tool_name)
        preview = self._fmt_tool_preview(tool_name, self._last_tool_args)
        dur = f"{duration:.1f}s"
        if duration > 0.1:
            if preview:
                console.print(f"  [feed]{_FEED}[/] {emoji} [text]{verb:9}[/] [subtext]{preview}[/]  [dim]{dur}[/]")
            else:
                console.print(f"  [feed]{_FEED}[/] {emoji} [text]{verb:9}[/] [dim]{dur}[/]")

    def log_response(self, text: str):
        if self._was_streamed:
            self._was_streamed = False
            return
        console.print()
        for line in text.split("\n"):
            console.print(f"  [text]{line}[/]")
        console.print()

    def log_error(self, error: str):
        console.print(f"\n  [error]{_FEED}[/] [error]{error}[/]\n")

    def log_budget_warning(self, budget):
        ratio = int(budget.usage_ratio * 100)
        console.print(f"  [warning]{_FEED}[/] [warning]上下文使用率 {ratio}%，建议 /compact[/]")

    def log_compress(self, old_count, new_count, old_tokens, new_tokens):
        saved = old_tokens - new_tokens
        console.print(f"  [info]{_FEED}[/] [info]自动压缩[/] {old_count}→{new_count} 条消息，节省 ~{_fmt_tok(saved)} tok")

    def log_done(self, stats):
        self._stats = stats
        tok = _fmt_tok(stats.total_tokens)
        tok_in = _fmt_tok(stats.prompt_tokens)
        tok_out = _fmt_tok(stats.completion_tokens)
        elapsed = stats.elapsed_str

        bar = "─" * 50
        console.print(f"\n  [gold.dim]{bar}[/]")

        t = Text()
        t.append(f"  ✓", style="success")
        t.append(f" · ⏱ {elapsed}", style="gold.dim")
        t.append(f" · {tok} tok", style="cyan")
        t.append(f" ({tok_in}→{tok_out})", style="dim")
        t.append(f" · T{stats.turns}", style="muted")
        if stats.tool_calls_count > 0:
            t.append(f" · {stats.tool_calls_count} tools", style="muted")
        if stats.retries_count > 0:
            t.append(f" · {stats.retries_count} retries", style="warning")
        if stats.errors_count > 0:
            t.append(f" · {stats.errors_count} errors", style="error")
        console.print(t)
        console.print(f"  [gold.dim]{bar}[/]\n")

        self._is_running = False
        self._task_start = 0.0

    def start_task(self):
        self._is_running = True
        self._task_start = _time.time()

    def stop_task(self):
        self._is_running = False

    def _update_stats(self, stats):
        self._stats = stats

    def cleanup(self):
        pass

    def _color_line(self, line: str, tool: str, is_error: bool = False) -> str:
        s = line.strip()
        if is_error or any(k in s.lower() for k in ["error", "err:", "错误", "failed", "fatal", "traceback"]):
            return f"[error]{line}[/]"
        if any(k in s.lower() for k in ["warn", "warning", "警告"]):
            return f"[warning]{line}[/]"
        if any(k in s for k in ["✓", "success", "ok", "完成", "done"]):
            return f"[success]{line}[/]"
        if tool == "terminal":
            return self._code_color(line)
        if "/" in s and " " not in s[:20]:
            return f"[info]{line}[/]"
        return f"[subtext]{line}[/]"

    def _code_color(self, line: str) -> str:
        s = line.strip()
        if s.startswith("$") or s.startswith("#"):
            return f"[success]{line}[/]"
        kw = ["def ", "class ", "import ", "from ", "if ", "elif ", "return ",
              "for ", "while ", "try:", "except", "with ", "async "]
        if any(s.startswith(k) or f" {k}" in s for k in kw):
            return f"[purple]{line}[/]"
        if s.startswith("//") or s.startswith("--"):
            return f"[dim]{line}[/]"
        if s and s[0].isdigit():
            return f"[cyan]{line}[/]"
        return f"[subtext]{line}[/]"

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
