"""蒙多执行控制台 v26 — Hermes KawaiiSpinner 风格 + Catppuccin 配色

改进（vs v25）：
- 借鉴 Hermes KawaiiSpinner 动画反馈
- 状态栏信息更精简，不重复
- 流式输出不再插入状态文本（避免打断阅读）
- 工具输出格式化统一
"""

import sys
import shutil
import time as _time
from pathlib import Path
from typing import Optional


class A:
    """Catppuccin Mocha + 金色点缀"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CLEAR_LINE = "\033[2K\r"

    TEXT = "\033[38;5;252m"
    SUBTEXT = "\033[38;5;249m"
    OVERLAY = "\033[38;5;243m"

    GOLD = "\033[38;5;221m"
    GOLD_DIM = "\033[38;5;180m"
    SUCCESS = "\033[38;5;150m"
    ERROR = "\033[38;5;210m"
    WARNING = "\033[38;5;223m"
    INFO = "\033[38;5;111m"
    CYAN = "\033[38;5;116m"
    PURPLE = "\033[38;5;183m"

    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"


# 借鉴 Hermes KawaiiSpinner — 执行中的动画脸
_SPINNER_FACES = ["◐", "◓", "◑", "◒"]
_SPINNER_VERBS = ["思考中", "运转中", "处理中", "分析中"]


class TaskConsole:

    def __init__(self):
        self._cols = shutil.get_terminal_size((80, 24)).columns
        self._model = ""
        self._stats = None
        self._is_running = False
        self._task_start = 0.0
        self._session_start = _time.time()
        self._was_streamed = False
        self._spinner_idx = 0

    def _w(self, t: str):
        sys.stdout.write(t)
        sys.stdout.flush()

    def _fmt_tok(self, n: int) -> str:
        if n < 1000:
            return str(n)
        if n < 1000000:
            return f"{n / 1000:.0f}K"
        return f"{n / 1000000:.1f}M"

    def _elapsed(self, start: float) -> str:
        if start <= 0:
            return "—"
        s = _time.time() - start
        if s < 60:
            return f"{int(s)}s"
        m = int(s // 60)
        if m < 60:
            return f"{m}m{int(s % 60)}s"
        return f"{int(m // 60)}h{m % 60}m"

    def _bar(self) -> str:
        return A.GOLD_DIM + "─" * min(self._cols, 60) + A.RESET

    def _spinner_face(self) -> str:
        face = _SPINNER_FACES[self._spinner_idx % len(_SPINNER_FACES)]
        self._spinner_idx += 1
        return face

    def init_screen(self, model_display: str, version: str = ""):
        self._model = model_display
        self._cols = shutil.get_terminal_size((80, 24)).columns
        self._session_start = _time.time()

    # ═══════════════════════════════════════
    # 状态行（精简版）
    # ═══════════════════════════════════════

    def _status_line(self) -> str:
        tok = self._stats.total_tokens if self._stats else 0
        model = self._model.split("/")[-1] if "/" in self._model else self._model
        parts = [
            f"{A.GOLD}{A.BOLD}MUNDO{A.RESET}",
            f"{A.DIM}·{A.RESET} {A.SUBTEXT}{model}{A.RESET}",
        ]
        if tok > 0:
            parts.append(f"{A.DIM}·{A.RESET} {A.CYAN}{self._fmt_tok(tok)} tok{A.RESET}")
        if self._is_running and self._task_start > 0:
            parts.append(f"{A.DIM}·{A.RESET} {A.GOLD_DIM}⏱{self._elapsed(self._task_start)}{A.RESET}")
        return "  ".join(parts)

    def _live_indicator(self) -> str:
        """单行实时指示器 — KawaiiSpinner 风格"""
        if not self._is_running or not self._stats:
            return ""
        s = self._stats
        face = self._spinner_face()
        parts = [f"{A.GOLD}{face}{A.RESET}"]
        if s.total_tokens > 0:
            parts.append(f"{A.CYAN}{self._fmt_tok(s.total_tokens)}tok{A.RESET}")
        parts.append(f"{A.GOLD_DIM}⏱{s.elapsed_str}{A.RESET}")
        if s._active_tools:
            parts.append(f"{A.INFO}{s._active_tools[-1]}{A.RESET}")
        return " │ ".join(parts)

    def update_live_status(self, stats=None):
        if stats:
            self._stats = stats
        indicator = self._live_indicator()
        if indicator:
            sys.stdout.write(f"\r{A.CLEAR_LINE}  {A.DIM}▸{A.RESET} {indicator} ")
            sys.stdout.flush()

    # ═══════════════════════════════════════
    # 流式输出 — 不插入状态文本，保持阅读流畅
    # ═══════════════════════════════════════

    def stream_start(self, turn: int):
        self._was_streamed = True
        sys.stdout.write(f"\n")
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
    # 输入（prompt_toolkit）
    # ═══════════════════════════════════════

    def read_input(self) -> str:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.formatted_text import ANSI as PT_ANSI
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.styles import Style
        from prompt_toolkit.key_binding import KeyBindings

        self._w(f"\n{self._status_line()}\n")

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

        session = PromptSession(
            history=FileHistory(hist_path),
            style=style,
            key_bindings=kb,
            multiline=True,
        )
        try:
            return session.prompt(
                PT_ANSI(f"{A.GOLD}❯{A.RESET} "),
                wrap_lines=True,
            ).strip()
        except (EOFError, KeyboardInterrupt):
            return ""

    # ═══════════════════════════════════════
    # 日志输出
    # ═══════════════════════════════════════

    def log_thinking(self, turn: int):
        self._task_start = _time.time()
        self._w(f"\n  {A.GOLD_DIM}▸{A.RESET} {A.SUBTEXT}思考中...{A.RESET} {A.DIM}(Turn {turn}){A.RESET}\n")

    def log_task_accepted(self, task_text: str):
        preview = task_text[:60].replace("\n", " ")
        if len(task_text) > 60:
            preview += "..."
        self._w(f"\n  {A.SUCCESS}▸{A.RESET} {A.DIM}已接收{A.RESET} {A.SUBTEXT}{preview}{A.RESET}\n")

    def log_tool_start(self, tool_name: str, tool_args: dict):
        info = self._fmt_tool_info(tool_name, tool_args)
        sys.stdout.write(f"\r{A.CLEAR_LINE}")
        self._w(f"\n  {A.INFO}▸{A.RESET} {A.TEXT}{tool_name}{A.RESET}  {A.DIM}{info}{A.RESET}\n")
        if self._stats:
            self._stats._active_tools.append(tool_name)

    def log_tool_output(self, tool_name: str, output: str, is_error: bool = False):
        mark = f"{A.ERROR}✗{A.RESET}" if is_error else f"{A.DIM}│{A.RESET}"
        if not output:
            self._w(f"  {mark} {A.DIM}(无输出){A.RESET}\n")
            return
        for line in self._fmt_tool_output(tool_name, output).split("\n"):
            self._w(f"  {mark} {self._color(line, tool_name)}\n")

    def log_tool_done(self, tool_name: str, duration: float):
        if duration > 0.5:
            self._w(f"  {A.SUCCESS}✓{A.RESET} {A.SUBTEXT}{tool_name}{A.RESET} {A.DIM}({duration:.1f}s){A.RESET}\n")

    def log_response(self, text: str):
        if self._was_streamed:
            self._was_streamed = False
            return
        self._w("\n")
        for line in text.split("\n"):
            self._w(f"  {A.TEXT}{line}{A.RESET}\n")
        self._w("\n")

    def log_error(self, error: str):
        sys.stdout.write(f"\r{A.CLEAR_LINE}")
        self._w(f"\n  {A.ERROR}✗{A.RESET} {A.ERROR}{error}{A.RESET}\n\n")

    def log_done(self, stats):
        self._stats = stats
        tok = self._fmt_tok(stats.total_tokens)
        tok_in = self._fmt_tok(stats.prompt_tokens)
        tok_out = self._fmt_tok(stats.completion_tokens)
        elapsed = stats.elapsed_str

        sys.stdout.write(f"\r{A.CLEAR_LINE}")
        self._w(f"\n{self._bar()}\n")
        self._w(
            f"  {A.SUCCESS}✓{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.GOLD_DIM}⏱ {elapsed}{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.CYAN}{tok} tok{A.RESET}"
            f" {A.DIM}({tok_in}→{tok_out}){A.RESET}"
            f" {A.DIM}·{A.RESET} {A.OVERLAY}T{stats.turns}{A.RESET}"
        )
        if stats.tool_calls_count > 0:
            self._w(f" {A.DIM}·{A.RESET} {A.OVERLAY}{stats.tool_calls_count} tools{A.RESET}")
        self._w(f"\n{self._bar()}\n")

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
        self._w(A.SHOW_CURSOR + A.RESET)

    # ── 颜色 ──

    def _color(self, line: str, tool: str) -> str:
        s = line.strip()
        if any(k in s.lower() for k in ["error", "err:", "错误", "failed", "fatal", "traceback"]):
            return f"{A.ERROR}{line}{A.RESET}"
        if any(k in s.lower() for k in ["warn", "warning", "警告"]):
            return f"{A.WARNING}{line}{A.RESET}"
        if any(k in s for k in ["✓", "success", "ok", "完成", "done"]):
            return f"{A.SUCCESS}{line}{A.RESET}"
        if tool == "terminal":
            return self._code_color(line)
        return f"{A.SUBTEXT}{line}{A.RESET}"

    def _code_color(self, line: str) -> str:
        s = line.strip()
        if s.startswith("$") or s.startswith("#"):
            return f"{A.SUCCESS}{line}{A.RESET}"
        kw = ["def ", "class ", "import ", "from ", "if ", "elif ", "return ",
              "for ", "while ", "try:", "except", "with ", "async "]
        if any(s.startswith(k) or f" {k}" in s for k in kw):
            return f"{A.PURPLE}{line}{A.RESET}"
        if s.startswith("//") or s.startswith("--"):
            return f"{A.DIM}{line}{A.RESET}"
        if s and s[0].isdigit():
            return f"{A.CYAN}{line}{A.RESET}"
        return f"{A.SUBTEXT}{line}{A.RESET}"

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

    def _fmt_tool_output(self, name: str, output: str) -> str:
        cap = 30
        lines = output.strip().split("\n")
        if len(lines) > cap:
            return "\n".join(lines[:cap // 2]) + f"\n  ... ({len(lines) - cap + 5} 行省略)\n" + "\n".join(lines[-5:])
        return output.strip()
