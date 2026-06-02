"""蒙多执行控制台 v10 — 流式输出 + 实时仪表盘

配色方案：基于 Catppuccin Mocha + 金色点缀（蒙多身份色）
布局：Hermes Agent / Claude Code 风格
  顶部：状态行（模型、tokens、时间、agents、工具）
  中间：输出区（流式文本 + 工具执行）
  底部：❯ 提示符
"""

import sys
import shutil
from pathlib import Path
import time as _time


class A:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    CLEAR_LINE = "\033[2K\r"

    TEXT = "\033[38;5;252m"
    SUBTEXT = "\033[38;5;249m"
    OVERLAY = "\033[38;5;243m"
    SURFACE = "\033[38;5;240m"

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

    # 光标移动
    CURSOR_UP = "\033[{}A"
    CURSOR_DOWN = "\033[{}B"
    SAVE_CURSOR = "\033[s"
    RESTORE_CURSOR = "\033[u"


class TaskConsole:

    def __init__(self):
        self._cols = shutil.get_terminal_size((80, 24)).columns
        self._model = ""
        self._version = ""
        self._stats = None
        self._is_running = False
        self._task_start = 0.0
        self._session_start = _time.time()
        self._stream_buf = ""
        self._stream_line_count = 0
        self._live_status = ""
        self._was_streamed = False

    def _w(self, t: str):
        from prompt_toolkit import print_formatted_text
        from prompt_toolkit.formatted_text import ANSI as PT_ANSI
        print_formatted_text(PT_ANSI(t), end="", flush=True)

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
        return A.GOLD_DIM + "─" * self._cols + A.RESET

    def init_screen(self, model_display: str, version: str = ""):
        self._model = model_display
        self._version = version
        self._cols = shutil.get_terminal_size((80, 24)).columns
        self._session_start = _time.time()

    # ═══════════════════════════════════════
    # 状态行（Claude Code 风格顶部栏）
    # ═══════════════════════════════════════

    def _status_line(self) -> str:
        tok = self._stats.total_tokens if self._stats else 0
        model = self._model.split("/")[-1] if "/" in self._model else self._model
        session_t = self._elapsed(self._session_start)
        task_t = self._elapsed(self._task_start) if self._is_running else ""

        parts = [
            f"{A.GOLD}{A.BOLD}MUNDO{A.RESET}",
            f"{A.DIM}·{A.RESET} {A.SUBTEXT}{model}{A.RESET}",
            f"{A.DIM}·{A.RESET} {A.CYAN}{self._fmt_tok(tok)} tok{A.RESET}",
            f"{A.DIM}·{A.RESET} {A.OVERLAY}{session_t}{A.RESET}",
        ]

        if self._is_running and task_t:
            parts.append(f"{A.DIM}·{A.RESET} {A.GOLD_DIM}⏱{task_t}{A.RESET}")

        if self._stats and self._stats.turns > 0:
            parts.append(f"{A.DIM}·{A.RESET} {A.OVERLAY}T{self._stats.turns}{A.RESET}")

        if self._stats and self._stats.tool_calls_count > 0:
            parts.append(f"{A.DIM}·{A.RESET} {A.INFO}{self._stats.tool_calls_count}tools{A.RESET}")

        if self._stats and self._stats.clones_count > 0:
            parts.append(f"{A.DIM}·{A.RESET} {A.PURPLE}{self._stats.clones_count}分身{A.RESET}")

        if self._stats and self._stats._active_agents:
            agents = ",".join(self._stats._active_agents[:3])
            parts.append(f"{A.DIM}·{A.RESET} {A.SUCCESS}{agents}{A.RESET}")

        return "  ".join(parts)

    # ═══════════════════════════════════════
    # 实时仪表盘（单行状态 + 工具/Agent 信息）
    # ═══════════════════════════════════════

    def _live_dashboard(self) -> str:
        """实时状态行 — 执行期间持续更新"""
        if not self._is_running or not self._stats:
            return ""

        s = self._stats
        parts = []

        # Turn
        parts.append(f"{A.GOLD}T{s.turns}{A.RESET}")

        # Tokens
        if s.total_tokens > 0:
            parts.append(f"{A.CYAN}{self._fmt_tok(s.total_tokens)}tok{A.RESET}")

        # Elapsed
        parts.append(f"{A.GOLD_DIM}⏱{s.elapsed_str}{A.RESET}")

        # LLM vs Tool time ratio
        total_time = max(s.elapsed, 0.01)
        if s.llm_time > 0 or s.tool_time > 0:
            llm_pct = int(s.llm_time / total_time * 100)
            tool_pct = int(s.tool_time / total_time * 100)
            parts.append(f"{A.DIM}L{llm_pct}% T{tool_pct}%{A.RESET}")

        # Active tools
        if s._active_tools:
            last_tool = s._active_tools[-1]
            parts.append(f"{A.INFO}{last_tool}{A.RESET}")

        # Agents
        if s._active_agents:
            parts.append(f"{A.SUCCESS}{'|'.join(s._active_agents[:2])}{A.RESET}")

        # Clones
        if s.clones_count > 0:
            parts.append(f"{A.PURPLE}×{s.clones_count}{A.RESET}")

        return f"  {A.DIM}│{A.RESET} ".join(parts)

    def update_live_status(self, stats=None):
        """更新实时状态栏（单行覆盖）"""
        if stats:
            self._stats = stats
        status = self._live_dashboard()
        if status:
            sys.stdout.write(f"\r{A.CLEAR_LINE}  {A.DIM}▸{A.RESET} {status} ")
            sys.stdout.flush()

    # ═══════════════════════════════════════
    # 流式输出
    # ═══════════════════════════════════════

    def stream_start(self, turn: int):
        """流式输出开始"""
        self._stream_buf = ""
        self._stream_line_count = 0
        self._was_streamed = True
        self._stream_chunk_count = 0
        self._last_status_len = 0
        sys.stdout.write(f"\n")
        sys.stdout.flush()

    def stream_text(self, text: str):
        """流式输出 — 逐 chunk 打印 + 状态行追加"""
        self._stream_buf += text
        self._stream_chunk_count += 1
        # 实时估算 token
        if self._stats:
            est_tokens = len(self._stream_buf) * 2 // 3
            self._stats.completion_tokens = max(self._stats.completion_tokens, est_tokens)
            self._stats.total_tokens = self._stats.prompt_tokens + self._stats.completion_tokens
        from prompt_toolkit import print_formatted_text
        from prompt_toolkit.formatted_text import ANSI as PT_ANSI
        # 每 15 个 chunk 在行尾追加状态
        if self._stream_chunk_count % 15 == 0:
            status = self._build_stream_status()
            print_formatted_text(PT_ANSI(f"{A.TEXT}{text}{A.RESET}{A.DIM}  [{status}]{A.RESET}"), end="", flush=True)
        else:
            print_formatted_text(PT_ANSI(f"{A.TEXT}{text}{A.RESET}"), end="", flush=True)

    def stream_end(self, turn: int):
        """流式输出结束"""
        if self._stream_buf and not self._stream_buf.endswith("\n"):
            sys.stdout.write("\n")
            sys.stdout.flush()
        self._stream_buf = ""

    def _build_stream_status(self) -> str:
        """构建流式状态文本"""
        elapsed = self._elapsed(self._task_start) if self._task_start > 0 else "0s"
        tok = self._fmt_tok(self._stats.total_tokens) if self._stats else "0"
        turn = self._stats.turns if self._stats else 1
        return f"T{turn} · {tok}tok · {elapsed}"

    # ═══════════════════════════════════════
    # 输入（prompt_toolkit）
    # ═══════════════════════════════════════

    def read_input(self) -> str:
        from prompt_toolkit import PromptSession, print_formatted_text
        from prompt_toolkit.formatted_text import ANSI as PT_ANSI
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.styles import Style
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.filters import Condition

        self._w(f"\n{self._status_line()}\n")

        hist_path = str(Path.home() / ".hermes" / "mundo-agent" / ".mundo_history")
        style = Style.from_dict({"prompt": "#d4a017 bold"})

        kb = KeyBindings()

        @kb.add("enter")
        def _(event):
            buf = event.current_buffer
            # 光标在最后一行末尾 → 提交
            text = buf.text
            cursor = buf.cursor_position
            if cursor >= len(text.rstrip()):
                # 去掉末尾空白后提交
                buf.text = text.rstrip()
                buf.validate_and_handle()
            else:
                # 在文本中间 → 插入换行，允许自由编辑
                buf.newline()

        @kb.add("escape", "enter")
        def _(event):
            # Option+Enter 强制提交（不论光标位置）
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
        """任务已接收反馈"""
        preview = task_text[:60].replace("\n", " ")
        if len(task_text) > 60:
            preview += "..."
        self._w(f"\n  {A.SUCCESS}▸{A.RESET} {A.DIM}已接收{A.RESET} {A.SUBTEXT}{preview}{A.RESET}\n")

    def log_tool_start(self, tool_name: str, tool_args: dict):
        info = self._fmt_tool_info(tool_name, tool_args)
        # 清除实时状态行，打印工具信息
        sys.stdout.write(f"\r{A.CLEAR_LINE}")
        self._w(f"\n  {A.INFO}▸{A.RESET} {A.TEXT}{tool_name}{A.RESET}  {A.DIM}{info}{A.RESET}\n")
        # 更新活跃工具
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

    def log_delegation(self, agent_names: list, clone_count: int, total: int):
        sys.stdout.write(f"\r{A.CLEAR_LINE}")
        self._w(f"\n  {A.CYAN}━━ 分发 ━━{A.RESET}\n")
        for name in set(agent_names):
            self._w(f"  {A.SUCCESS}  ▸ {name}{A.RESET}\n")
        if clone_count > 0:
            self._w(f"  {A.GOLD_DIM}  ▸ {clone_count} 个分身{A.RESET}\n")
        self._w(f"  {A.DIM}  共 {total} 个子任务{A.RESET}\n")

    def log_clones(self, count: int):
        for i in range(1, count + 1):
            self._w(f"  {A.GOLD}  分身 #{i}{A.RESET}\n")

    def log_subtask_progress(self, subtask_id, task_desc, agent_name, phase, preview=None):
        """子任务实时进度"""
        desc = (task_desc or "")[:40].replace("\n", " ")
        if phase == "start":
            self._w(f"  {A.INFO}▸{A.RESET} [{subtask_id}] {A.SUBTEXT}{desc}{A.RESET} → {A.SUCCESS}{agent_name}{A.RESET} {A.DIM}执行中...{A.RESET}\n")
        elif phase == "done":
            self._w(f"  {A.SUCCESS}✓{A.RESET} [{subtask_id}] {A.SUBTEXT}{desc}{A.RESET} → {A.SUCCESS}{agent_name}{A.RESET}\n")
            if preview:
                self._w(f"  {A.DIM}│ {preview}{A.RESET}\n")
        elif phase == "error":
            self._w(f"  {A.ERROR}✗{A.RESET} [{subtask_id}] {A.SUBTEXT}{desc}{A.RESET} → {A.ERROR}{preview}{A.RESET}\n")

    def log_merging(self):
        """汇总开始提示"""
        self._w(f"\n  {A.GOLD_DIM}▸{A.RESET} {A.SUBTEXT}汇总中...{A.RESET}\n")

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
        llm_pct = f"{stats.llm_time / max(stats.elapsed, 0.01) * 100:.0f}%"
        tool_pct = f"{stats.tool_time / max(stats.elapsed, 0.01) * 100:.0f}%"

        sys.stdout.write(f"\r{A.CLEAR_LINE}")

        self._w(f"\n{self._bar()}\n")
        self._w(
            f"  {A.SUCCESS}✓{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.GOLD_DIM}⏱ {elapsed}{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.CYAN}{tok} tok{A.RESET}"
            f" {A.DIM}({tok_in}→{tok_out}){A.RESET}"
            f" {A.DIM}·{A.RESET} {A.OVERLAY}T{stats.turns}{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.OVERLAY}LLM {llm_pct} Tools {tool_pct}{A.RESET}"
        )
        if stats.tool_calls_count > 0:
            self._w(f" {A.DIM}·{A.RESET} {A.OVERLAY}{stats.tool_calls_count} tools{A.RESET}")
        if stats._active_agents:
            self._w(f" {A.DIM}·{A.RESET} {A.SUCCESS}{'|'.join(stats._active_agents)}{A.RESET}")
        if stats.clones_count > 0:
            self._w(f" {A.DIM}·{A.RESET} {A.PURPLE}{stats.clones_count}分身{A.RESET}")
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
        """同步引擎 stats 到 console（实时状态栏用）"""
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
        if "/" in s and " " not in s[:20]:
            return f"{A.INFO}{line}{A.RESET}"
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
        if name in ("read_file", "write_file"):
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
        if name == "terminal":
            lines = output.strip().split("\n")
            if len(lines) > cap:
                return "\n".join(lines[:cap // 2]) + f"\n  ... ({len(lines) - cap + 5} 行省略)\n" + "\n".join(lines[-5:])
            return output.strip()
        if name in ("write_file", "web_search", "list_directory"):
            return output.strip()
        if name == "read_file":
            lines = output.strip().split("\n")
            if len(lines) > cap:
                return "\n".join(lines[:cap]) + f"\n  ... ({len(lines) - cap} 行省略)"
            return output.strip()
        if name == "search_files":
            lines = output.strip().split("\n")
            if len(lines) > 20:
                return "\n".join(lines[:20]) + f"\n  ... ({len(lines)} 条匹配)"
            return output.strip()
        if len(output) > 2000:
            return output[:2000] + "\n  ... (截断)"
        return output.strip()


class StatusBar:

    def __init__(self):
        self._cols = shutil.get_terminal_size((80, 24)).columns

    @staticmethod
    def _fmt_tok(n: int) -> str:
        if n < 1000:
            return str(n)
        if n < 1000000:
            return f"{n / 1000:.0f}K"
        return f"{n / 1000000:.1f}M"

    def show_thinking(self, model: str, turn: int, stats):
        sys.stdout.write(
            f"\r{A.CLEAR_LINE}  {A.GOLD_DIM}▸ Turn {turn}"
            f" {A.DIM}·{A.RESET} {A.CYAN}{self._fmt_tok(stats.total_tokens)}{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.GOLD_DIM}⏱ {stats.elapsed_str}{A.RESET}  "
        )
        sys.stdout.flush()

    def show_tool_start(self, model: str, tool_name: str, tool_info: str, stats):
        sys.stdout.write(
            f"\r{A.CLEAR_LINE}  {A.INFO}▸ {tool_name}: {tool_info[:30]}"
            f" {A.DIM}·{A.RESET} {A.CYAN}{self._fmt_tok(stats.total_tokens)}{A.RESET}  "
        )
        sys.stdout.flush()

    def show_done(self, model: str, stats):
        sys.stdout.write(A.CLEAR_LINE)
        print(f"\n  {A.SUCCESS}✓{A.RESET} {A.DIM}·{A.RESET} {A.GOLD_DIM}⏱ {stats.elapsed_str}{A.RESET} {A.DIM}·{A.RESET} {A.CYAN}{self._fmt_tok(stats.total_tokens)}{A.RESET}\n")

    def show_error(self, model: str, error: str, stats):
        sys.stdout.write(A.CLEAR_LINE)
        print(f"\n  {A.ERROR}✗{A.RESET} {A.DIM}·{A.RESET} {A.CYAN}{self._fmt_tok(stats.total_tokens)}{A.RESET} {A.ERROR}{error[:60]}{A.RESET}\n")
