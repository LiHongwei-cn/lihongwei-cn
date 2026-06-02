"""蒙多执行控制台 v9 — 专业配色 + Claude Code 风格布局

配色方案：基于 Catppuccin Mocha + 金色点缀（蒙多身份色）
  背景：终端原生深色
  文本：柔和白 #cdd6f4
  暗淡：灰色 #6c7086
  金色：低饱和金 #f2c57c（蒙多标识色）
  绿色：柔和绿 #a6e3a1（成功）
  红色：柔和红 #f38ba8（错误）
  蓝色：柔和蓝 #89b4fa（信息/工具）
  紫色：柔和紫 #cba6f7（代码关键字）
  黄色：柔和黄 #f9e2af（警告）
  青色：柔和青 #94e2d5（数据）

布局：Claude Code 风格三段式
  顶部：状态行
  中间：输出区
  底部：❯ 提示符
"""

import sys
import os
import shutil
import unicodedata
import time as _time


class A:
    # ── 基础 ──
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CLEAR_LINE = "\033[2K\r"

    # ── Catppuccin Mocha 调色板 ──
    TEXT = "\033[38;5;252m"          # 柔和白
    SUBTEXT = "\033[38;5;249m"       # 浅灰
    OVERLAY = "\033[38;5;243m"       # 中灰
    SURFACE = "\033[38;5;240m"       # 深灰

    # ── 语义色（低饱和）──
    GOLD = "\033[38;5;221m"          # 蒙多标识色（温暖金）
    GOLD_DIM = "\033[38;5;180m"      # 暗金
    SUCCESS = "\033[38;5;150m"       # 柔和绿
    ERROR = "\033[38;5;210m"         # 柔和红
    WARNING = "\033[38;5;223m"       # 柔和黄
    INFO = "\033[38;5;111m"          # 柔和蓝
    CYAN = "\033[38;5;116m"          # 柔和青
    PURPLE = "\033[38;5;183m"        # 柔和紫

    # ── 工具 ──
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"


def _dw(text: str) -> int:
    w = 0
    for ch in text:
        if ord(ch) < 32:
            continue
        eaw = unicodedata.east_asian_width(ch)
        w += 2 if eaw in ("W", "F") else 1
    return w


class TaskConsole:

    def __init__(self):
        self._cols = shutil.get_terminal_size((80, 24)).columns
        self._model = ""
        self._version = ""
        self._stats = None
        self._is_running = False
        self._task_start = 0.0
        self._session_start = _time.time()

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
        return A.GOLD_DIM + "─" * self._cols + A.RESET

    # ── 初始化 ──

    def init_screen(self, model_display: str, version: str = ""):
        self._model = model_display
        self._version = version
        self._cols = shutil.get_terminal_size((80, 24)).columns
        self._session_start = _time.time()

    # ── 状态行 ──

    def _status_line(self) -> str:
        tok = self._stats.total_tokens if self._stats else 0
        model = self._model.split("/")[-1] if "/" in self._model else self._model
        session_t = self._elapsed(self._session_start)
        task_t = self._elapsed(self._task_start) if self._is_running else ""

        line = (
            f"  {A.GOLD}{A.BOLD}MUNDO{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.SUBTEXT}{model}{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.CYAN}{self._fmt_tok(tok)} tokens{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.OVERLAY}{session_t}{A.RESET}"
        )
        if self._is_running and task_t:
            line += f" {A.DIM}·{A.RESET} {A.GOLD_DIM}⏱ {task_t}{A.RESET}"
        return line

    # ── 输入 ──

    def read_input(self) -> str:
        import termios
        import tty

        self._w(f"\n{self._status_line()}\n")
        self._w(f"{A.GOLD}❯{A.RESET} ")

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
                    self._redraw(buf, cur)
                    continue

                if ch == b"\x15":
                    buf = buf[cur:]
                    cur = 0
                    self._redraw(buf, cur)
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
                    self._redraw(buf, cur)
                    continue

                if ch == b"\x1b":
                    seq = os.read(fd, 2)
                    if seq == b"[C" and cur < len(buf):
                        cur += 1
                    elif seq == b"[D" and cur > 0:
                        cur -= 1
                    self._redraw(buf, cur)
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

                self._redraw(buf, cur)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def _redraw(self, buf, cur):
        text = "".join(buf)
        cols = shutil.get_terminal_size((80, 24)).columns
        usable = max(cols - 3, 10)
        text_w = _dw(text)
        lines = max(1, (text_w + usable - 1) // usable) if text_w > 0 else 1
        # 回到输入起始行
        if lines > 1:
            self._w(f"\033[{lines - 1}A")
        self._w(f"\r\033[J")
        # 重绘
        self._w(f"{A.GOLD}❯{A.RESET} {text}")
        # 光标定位（重写后光标在文本末尾）
        if cur < len(text):
            bw = _dw(text[:cur])
            target_line = bw // usable if usable > 0 else 0
            total_lines = lines
            move_up = total_lines - 1 - target_line
            if move_up > 0:
                self._w(f"\033[{move_up}A")
            self._w(f"\r\033[{3 + (bw % usable)}G")
        self._w(A.SHOW_CURSOR)

    # ── 日志输出 ──

    def log_thinking(self, turn: int):
        self._task_start = _time.time()
        self._stats = None
        self._w(f"\n  {A.GOLD_DIM}▸{A.RESET} {A.SUBTEXT}思考中...{A.RESET} {A.DIM}(Turn {turn}){A.RESET}\n")

    def log_tool_start(self, tool_name: str, tool_args: dict):
        info = self._fmt_tool_info(tool_name, tool_args)
        self._w(f"\n  {A.INFO}▸{A.RESET} {A.TEXT}{tool_name}{A.RESET}  {A.DIM}{info}{A.RESET}\n")

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
        self._w(f"\n  {A.CYAN}━━ 分发 ━━{A.RESET}\n")
        for name in set(agent_names):
            self._w(f"  {A.SUCCESS}  ▸ {name}{A.RESET}\n")
        if clone_count > 0:
            self._w(f"  {A.GOLD_DIM}  ▸ {clone_count} 个分身{A.RESET}\n")
        self._w(f"  {A.DIM}  共 {total} 个子任务{A.RESET}\n")

    def log_clones(self, count: int):
        for i in range(1, count + 1):
            self._w(f"  {A.GOLD}  分身 #{i}{A.RESET}\n")

    def log_response(self, text: str):
        self._w("\n")
        for line in text.split("\n"):
            self._w(f"  {A.TEXT}{line}{A.RESET}\n")
        self._w("\n")

    def log_error(self, error: str):
        self._w(f"\n  {A.ERROR}✗{A.RESET} {A.ERROR}{error}{A.RESET}\n\n")

    def log_done(self, stats):
        self._stats = stats
        tok = self._fmt_tok(stats.total_tokens)
        tok_in = self._fmt_tok(stats.prompt_tokens)
        tok_out = self._fmt_tok(stats.completion_tokens)
        elapsed = stats.elapsed_str
        llm_pct = f"{stats.llm_time / max(stats.elapsed, 0.01) * 100:.0f}%"
        tool_pct = f"{stats.tool_time / max(stats.elapsed, 0.01) * 100:.0f}%"

        self._w(f"\n{self._bar()}\n")
        self._w(
            f"  {A.SUCCESS}✓{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.GOLD_DIM}⏱ {elapsed}{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.CYAN}{tok} tokens{A.RESET}"
            f" {A.DIM}({tok_in}→{tok_out}){A.RESET}"
            f" {A.DIM}·{A.RESET} {A.OVERLAY}T{stats.turns}{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.OVERLAY}LLM {llm_pct} Tools {tool_pct}{A.RESET}"
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
