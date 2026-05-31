"""蒙多执行控制台 v4 — 可靠的实时输出 + 底部状态栏

策略（参考 Hermes / Claude Code）：
  - 任务执行中：日志直接滚动输出，底部状态栏实时更新
  - 等待输入时：显示输入提示符
  - 不依赖复杂的 scroll region，用简单光标控制保证可靠性
"""

import sys
import os
import re
import shutil
import unicodedata
import time as _time


class A:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CLEAR_LINE = "\033[2K\r"
    GOLD = "\033[38;5;178m"
    IRON = "\033[38;5;243m"
    AMBER = "\033[38;5;136m"
    SUCCESS = "\033[38;5;65m"
    ERROR = "\033[38;5;131m"
    TOOL = "\033[38;5;245m"
    CYAN = "\033[38;5;87m"
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"


_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def _display_width(text: str) -> int:
    w = 0
    for ch in text:
        if ord(ch) < 32:
            continue
        eaw = unicodedata.east_asian_width(ch)
        w += 2 if eaw in ("W", "F") else 1
    return w


BOTTOM_LINES = 3


class TaskConsole:

    def __init__(self):
        self._cols = shutil.get_terminal_size((80, 24)).columns
        self._rows = shutil.get_terminal_size((80, 24)).lines
        self._model_display = ""
        self._version = ""
        self._status_text = ""
        self._status_color = A.AMBER
        self._stats = None
        self._is_running = False
        self._task_start = 0.0

    def _w(self, text: str):
        sys.stdout.write(text)
        sys.stdout.flush()

    def _fmt_tok(self, n: int) -> str:
        if n < 1000:
            return str(n)
        if n < 1000000:
            return f"{n / 1000:.1f}K"
        return f"{n / 1000000:.2f}M"

    def _elapsed(self) -> str:
        if self._task_start <= 0:
            return "0s"
        s = _time.time() - self._task_start
        if s < 60:
            return f"{s:.1f}s"
        return f"{int(s // 60)}m{s % 60:.0f}s"

    # ── 初始化 ──

    def init_screen(self, model_display: str, version: str = ""):
        self._model_display = model_display
        self._version = version
        self._cols = shutil.get_terminal_size((80, 24)).columns
        self._rows = shutil.get_terminal_size((80, 24)).lines
        self._w(A.SHOW_CURSOR)
        self._draw_status_bar()

    # ── 底部状态栏（单行，不干扰滚动输出）──

    def _draw_status_bar(self):
        """在当前光标位置绘制一行状态信息"""
        if self._is_running:
            elapsed = self._elapsed()
            tok_str = ""
            if self._stats and self._stats.total_tokens > 0:
                tok_str = f" {A.DIM}·{A.RESET} {A.CYAN}{self._fmt_tok(self._stats.total_tokens)} tokens{A.RESET}"
            status = self._status_text or "运行中"
            self._w(
                f"\r{A.CLEAR_LINE}"
                f"  {A.GOLD}MUNDO{A.RESET}"
                f" {A.DIM}·{A.RESET} {self._status_color}{status}{A.RESET}"
                f"{tok_str}"
                f" {A.DIM}·{A.RESET} {A.AMBER}⏱ {elapsed}{A.RESET}"
            )
        else:
            ver = f" v{self._version}" if self._version else ""
            self._w(
                f"\r{A.CLEAR_LINE}"
                f"  {A.GOLD}MUNDO{A.DIM}{ver}{A.RESET}"
                f" {A.DIM}·{A.RESET} {A.IRON}{self._model_display}{A.RESET}"
            )

    def _newline_after_status(self):
        """状态栏后换行，让后续输出在新行开始"""
        self._w("\n")

    # ── 输入（raw terminal）──

    def read_input(self) -> str:
        import termios
        import tty

        # 显示输入提示符
        ver = f" v{self._version}" if self._version else ""
        self._w(
            f"\r{A.CLEAR_LINE}"
            f"  {A.GOLD}MUNDO{A.DIM}{ver}{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.IRON}{self._model_display}{A.RESET}"
            f"\n{A.CLEAR_LINE}"
            f"  {A.GOLD}>{A.RESET} "
        )

        buf = []
        cur = 0

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = os.read(fd, 1)
                if not ch:
                    continue

                if ch in (b"\r", b"\n"):
                    self._w(A.SHOW_CURSOR + "\n")
                    return "".join(buf)

                if ch == b"\x03":
                    self._w(A.SHOW_CURSOR + "\n")
                    raise KeyboardInterrupt

                if ch == b"\x04":
                    if not buf:
                        self._w(A.SHOW_CURSOR)
                        return ""
                    continue

                if ch in (b"\x7f", b"\x08"):
                    if cur > 0:
                        buf.pop(cur - 1)
                        cur -= 1
                    self._redraw_input(buf, cur)
                    continue

                if ch == b"\x15":
                    buf = buf[cur:]
                    cur = 0
                    self._redraw_input(buf, cur)
                    continue

                if ch == b"\x17":
                    if cur > 0:
                        i = cur - 1
                        while i > 0 and buf[i - 1] == " ":
                            i -= 1
                        while i > 0 and buf[i - 1] != " ":
                            i -= 1
                        del buf[i:cur]
                        cur = i
                    self._redraw_input(buf, cur)
                    continue

                if ch == b"\x1b":
                    seq = os.read(fd, 2)
                    if seq == b"[C" and cur < len(buf):
                        cur += 1
                    elif seq == b"[D" and cur > 0:
                        cur -= 1
                    self._redraw_input(buf, cur)
                    continue

                if ch[0] > 0x7f:
                    if ch[0] & 0xE0 == 0xC0:
                        ch += os.read(fd, 1)
                    elif ch[0] & 0xF0 == 0xE0:
                        ch += os.read(fd, 2)
                    elif ch[0] & 0xF8 == 0xF0:
                        ch += os.read(fd, 3)

                try:
                    buf.insert(cur, ch.decode("utf-8"))
                    cur += 1
                except UnicodeDecodeError:
                    continue

                self._redraw_input(buf, cur)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def _redraw_input(self, buf, cur):
        text = "".join(buf)
        self._w(f"\r{A.CLEAR_LINE}  {A.GOLD}>{A.RESET} {text}")
        if cur < len(text):
            before_w = _display_width(text[:cur])
            self._w(f"\033[{4 + before_w}G")  # 回到光标位置
        self._w(A.SHOW_CURSOR)

    # ── 日志输出（实时滚动）──

    def log_thinking(self, turn: int):
        self._task_start = _time.time()
        self._status_text = f"思考 Turn {turn}"
        self._status_color = A.AMBER
        self._stats = None
        self._w(f"\n  {A.AMBER}▸ 思考中... (Turn {turn}){A.RESET}\n")
        self._draw_status_bar()

    def log_tool_start(self, tool_name: str, tool_args: dict):
        self._status_text = tool_name
        self._status_color = A.TOOL
        info = self._fmt_tool_info(tool_name, tool_args)
        self._w(f"\n  {A.TOOL}▸ {A.BOLD}{tool_name}{A.RESET}  {A.DIM}{info}{A.RESET}\n")
        self._draw_status_bar()

    def log_tool_output(self, tool_name: str, output: str, is_error: bool = False):
        color = A.ERROR if is_error else A.IRON
        mark = "✗" if is_error else "│"
        if not output:
            self._w(f"  {color}{mark} {A.DIM}(无输出){A.RESET}\n")
            self._draw_status_bar()
            return
        for line in self._fmt_tool_output(tool_name, output).split("\n"):
            display_line = line[:self._cols - 6] if len(line) > self._cols - 6 else line
            self._w(f"  {color}{mark} {display_line}{A.RESET}\n")
        self._draw_status_bar()

    def log_tool_done(self, tool_name: str, duration: float):
        if duration > 1.0:
            self._w(f"  {A.SUCCESS}✓ {tool_name} {A.DIM}({duration:.1f}s){A.RESET}\n")
        self._status_text = "思考中"
        self._status_color = A.AMBER
        self._draw_status_bar()

    def log_delegation(self, agent_names: list, clone_count: int, total: int):
        self._w(f"\n  {A.CYAN}━━ 任务分发 ━━{A.RESET}\n")
        for name in set(agent_names):
            self._w(f"  {A.SUCCESS}  ▸ 调用 {name}{A.RESET}\n")
        if clone_count > 0:
            self._w(f"  {A.AMBER}  ▸ {clone_count} 个蒙多分身并行{A.RESET}\n")
        self._w(f"  {A.DIM}  共 {total} 个子任务{A.RESET}\n")
        self._draw_status_bar()

    def log_clones(self, count: int):
        for i in range(1, count + 1):
            self._w(f"  {A.GOLD}  👑 分身 #{i} 已出动{A.RESET}\n")
        self._draw_status_bar()

    def log_response(self, text: str):
        self._w(f"\n{A.IRON}")
        for line in text.split("\n"):
            self._w(f"  {line}\n")
        self._w(f"{A.RESET}\n")

    def log_error(self, error: str):
        self._w(f"\n  {A.ERROR}✗ {error}{A.RESET}\n\n")

    def log_done(self, stats):
        self._stats = stats
        tok = self._fmt_tok(stats.total_tokens)
        tok_in = self._fmt_tok(stats.prompt_tokens)
        tok_out = self._fmt_tok(stats.completion_tokens)
        elapsed = stats.elapsed_str
        llm_pct = f"{stats.llm_time / max(stats.elapsed, 0.01) * 100:.0f}%"
        tool_pct = f"{stats.tool_time / max(stats.elapsed, 0.01) * 100:.0f}%"

        sep = A.DIM + "─" * min(self._cols - 4, 60) + A.RESET
        self._w(f"\n  {sep}\n")
        self._w(
            f"  {A.SUCCESS}✓ 完成{A.RESET}"
            f"  {A.DIM}│{A.RESET}"
            f"  {A.AMBER}⏱ {elapsed}{A.RESET}"
            f"  {A.DIM}│{A.RESET}"
            f"  {A.CYAN}Tokens: {tok} ({tok_in}→{tok_out}){A.RESET}"
            f"  {A.DIM}│{A.RESET}"
            f"  {A.IRON}T{stats.turns} LLM {llm_pct} Tools {tool_pct}{A.RESET}"
        )
        if stats.tool_calls_count > 0:
            self._w(f"  {A.DIM}│{A.RESET}  {A.IRON}{stats.tool_calls_count} 次工具调用{A.RESET}")
        self._w(f"\n  {sep}\n\n")

        self._is_running = False
        self._status_text = ""
        self._task_start = 0.0
        self._draw_status_bar()

    # ── 任务状态 ──

    def start_task(self):
        self._is_running = True
        self._task_start = _time.time()
        self._status_text = "蒙多接管"
        self._status_color = A.GOLD
        self._w("\n")
        self._draw_status_bar()
        self._w("\n")

    def stop_task(self):
        self._is_running = False
        self._status_text = ""

    def cleanup(self):
        self._w(A.SHOW_CURSOR + A.RESET)

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
    """兼容 -q 查询模式"""

    def __init__(self):
        self._cols = shutil.get_terminal_size((80, 24)).columns

    @staticmethod
    def _fmt_tok(n: int) -> str:
        if n < 1000:
            return str(n)
        if n < 1000000:
            return f"{n / 1000:.1f}K"
        return f"{n / 1000000:.2f}M"

    def show_thinking(self, model: str, turn: int, stats):
        sys.stdout.write(
            f"\r{A.CLEAR_LINE}  {A.AMBER}▸ Turn {turn}"
            f" {A.DIM}·{A.RESET} {A.CYAN}{self._fmt_tok(stats.total_tokens)}{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.AMBER}⏱ {stats.elapsed_str}{A.RESET}  "
        )
        sys.stdout.flush()

    def show_tool_start(self, model: str, tool_name: str, tool_info: str, stats):
        sys.stdout.write(
            f"\r{A.CLEAR_LINE}  {A.TOOL}▸ {tool_name}: {tool_info[:30]}"
            f" {A.DIM}·{A.RESET} {A.CYAN}{self._fmt_tok(stats.total_tokens)}{A.RESET}  "
        )
        sys.stdout.flush()

    def show_done(self, model: str, stats):
        sys.stdout.write(A.CLEAR_LINE)
        print(f"\n  {A.SUCCESS}✓{A.RESET} {A.DIM}·{A.RESET} {A.AMBER}⏱ {stats.elapsed_str}{A.RESET} {A.DIM}·{A.RESET} {A.CYAN}{self._fmt_tok(stats.total_tokens)}{A.RESET}\n")

    def show_error(self, model: str, error: str, stats):
        sys.stdout.write(A.CLEAR_LINE)
        print(f"\n  {A.ERROR}✗{A.RESET} {A.DIM}·{A.RESET} {A.CYAN}{self._fmt_tok(stats.total_tokens)}{A.RESET} {A.ERROR}{error[:60]}{A.RESET}\n")
