"""蒙多执行控制台 v26.1 — 全 Rich 渲染（Hermes Agent 同源架构）

根治 ANSI 乱码：Rich 处理所有格式化输出，prompt_toolkit 只管输入。
不再混用 raw ANSI + patch_stdout。
"""

import sys
import shutil
import time as _time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.style import Style as RichStyle
from rich.theme import Theme
from rich.live import Live
from rich.spinner import Spinner

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
})

# Rich Console — 全局唯一渲染器
console = Console(theme=MUNDO_THEME, highlight=False, force_terminal=True)


# ═══════════════════════════════════════════════
# Spinner 动画（Hermes KawaiiSpinner 风格）
# ═══════════════════════════════════════════════

_SPINNER_FACES = ["◐", "◓", "◑", "◒"]


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


# ═══════════════════════════════════════════════
# TaskConsole — 所有输出通过 Rich
# ═══════════════════════════════════════════════

class TaskConsole:

    def __init__(self):
        self._model = ""
        self._stats = None
        self._is_running = False
        self._task_start = 0.0
        self._session_start = _time.time()
        self._was_streamed = False
        self._spinner_idx = 0

    def init_screen(self, model_display: str, version: str = ""):
        self._model = model_display
        self._session_start = _time.time()

    # ═══════════════════════════════════════
    # 状态行 — Rich Text
    # ═══════════════════════════════════════

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

        if self._stats and self._stats.turns > 0:
            t.append(" · ", style="muted")
            t.append(f"T{self._stats.turns}", style="muted")

        if self._stats and self._stats.tool_calls_count > 0:
            t.append(" · ", style="muted")
            t.append(f"{self._stats.tool_calls_count} tools", style="info")

        return t

    def print_status(self):
        console.print(self._build_status())

    def update_live_status(self, stats=None):
        if stats:
            self._stats = stats

    # ═══════════════════════════════════════
    # 流式输出 — 直接写 sys.stdout，不经 Rich
    # ═══════════════════════════════════════

    def stream_start(self, turn: int):
        self._was_streamed = True
        sys.stdout.write("\n")
        sys.stdout.flush()

    def stream_text(self, text: str):
        if self._stats:
            self._stats.completion_tokens = max(
                self._stats.completion_tokens,
                len(text) * 2 // 3
            )
            self._stats.total_tokens = self._stats.prompt_tokens + self._stats.completion_tokens
        sys.stdout.write(text)
        sys.stdout.flush()

    def stream_end(self, turn: int):
        sys.stdout.write("\n")
        sys.stdout.flush()

    # ═══════════════════════════════════════
    # 输入 — prompt_toolkit（只管输入，不管渲染）
    # ═══════════════════════════════════════

    def read_input(self) -> str:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.styles import Style
        from prompt_toolkit.key_binding import KeyBindings

        # 状态行通过 Rich 打印（在 prompt 之前）
        self.print_status()

        hist_path = str(Path.home() / ".hermes" / "mundo-agent" / ".mundo_history")
        # prompt_toolkit 只负责输入框样式
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

        session = PromptSession(
            history=FileHistory(hist_path),
            style=style,
            key_bindings=kb,
            multiline=True,
        )
        try:
            # prompt_toolkit 用原生 prompt 字符串，不用 PT_ANSI
            return session.prompt("❯ ").strip()
        except (EOFError, KeyboardInterrupt):
            return ""

    # ═══════════════════════════════════════
    # 日志输出 — 全部通过 Rich
    # ═══════════════════════════════════════

    def log_thinking(self, turn: int):
        self._task_start = _time.time()
        console.print(f"  [gold.dim]▸[/] [subtext]思考中...[/] [dim](Turn {turn})[/]")

    def log_task_accepted(self, task_text: str):
        preview = task_text[:60].replace("\n", " ")
        if len(task_text) > 60:
            preview += "..."
        console.print(f"\n  [success]▸[/] [dim]已接收[/] [subtext]{preview}[/]")

    def log_tool_start(self, tool_name: str, tool_args: dict):
        info = self._fmt_tool_info(tool_name, tool_args)
        console.print(f"\n  [info]▸[/] [text]{tool_name}[/]  [dim]{info}[/]")
        if self._stats:
            self._stats._active_tools.append(tool_name)

    def log_tool_output(self, tool_name: str, output: str, is_error: bool = False):
        if not output:
            console.print(f"  [dim]│[/] [dim](无输出)[/]")
            return
        mark = "[error]✗[/]" if is_error else "[dim]│[/]"
        lines = output.strip().split("\n")
        if len(lines) > 30:
            display = lines[:15] + [f"  ... ({len(lines) - 20} 行省略)"] + lines[-5:]
        else:
            display = lines
        for line in display:
            colored = self._color_line(line, tool_name, is_error)
            console.print(f"  {mark} {colored}")

    def log_tool_done(self, tool_name: str, duration: float):
        if duration > 0.5:
            console.print(f"  [success]✓[/] [subtext]{tool_name}[/] [dim]({duration:.1f}s)[/]")

    def log_response(self, text: str):
        if self._was_streamed:
            self._was_streamed = False
            return
        console.print()
        console.print(f"  [text]{text}[/]")
        console.print()

    def log_error(self, error: str):
        console.print(f"\n  [error]✗[/] [error]{error}[/]\n")

    def log_done(self, stats):
        self._stats = stats
        tok = _fmt_tok(stats.total_tokens)
        tok_in = _fmt_tok(stats.prompt_tokens)
        tok_out = _fmt_tok(stats.completion_tokens)
        elapsed = stats.elapsed_str

        bar = "─" * 50
        console.print(f"\n[gold.dim]{bar}[/]")

        t = Text()
        t.append("  ✓", style="success")
        t.append(f" · ⏱ {elapsed}", style="gold.dim")
        t.append(f" · {tok} tok", style="cyan")
        t.append(f" ({tok_in}→{tok_out})", style="dim")
        t.append(f" · T{stats.turns}", style="muted")
        if stats.tool_calls_count > 0:
            t.append(f" · {stats.tool_calls_count} tools", style="muted")
        console.print(t)

        console.print(f"[gold.dim]{bar}[/]")

        self._is_running = False
        self._task_start = 0.0

    # ── 任务状态 ──

    def start_task(self):
        self._is_running = True
        self._task_start = _time.time()

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

    # ── 格式化 ──

    def _fmt_tool_info(self, name: str, args: dict) -> str:
        if name == "terminal":
            return args.get("command", "")[:60]
        if name in ("read_file", "write_file", "edit_file"):
            return args.get("path", "")
        if name == "search_files":
            return args.get("pattern", "")
        if name == "web_search":
            return args.get("query", "")
        if name == "list_directory":
            return args.get("path", ".")
        return str(args)[:60]
