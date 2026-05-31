"""蒙多执行控制台 v3 — 极简 Hermes 风格

布局：
  ┌─ 滚动日志区 ─────────────────────────────┐
  │ 蒙多的思考、工具调用、工具输出             │
  ├─ 底部固定区 ─────────────────────────────┤
  │  MUNDO · model · tokens · ⏱ · turns       │  ← 状态行（平铺）
  │  ─────────────────────────────────────    │  ← 分隔线
  │  > 用户输入                                │  ← 输入行
  └──────────────────────────────────────────┘
"""

import sys
import os
import re
import shutil
import unicodedata


class A:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CLEAR_LINE = "\033[2K\r"
    SAVE_CURSOR = "\033[s"
    RESTORE_CURSOR = "\033[u"
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


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


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
    """极简 Hermes 风格控制台"""

    def __init__(self):
        self._cols = shutil.get_terminal_size((80, 24)).columns
        self._rows = shutil.get_terminal_size((80, 24)).lines
        self._model_display = ""
        self._version = ""
        self._status_text = ""
        self._status_color = A.AMBER
        self._stats = None
        self._is_running = False
        self._resp_start = 0.0

    def _write(self, text: str):
        sys.stdout.write(text)
        sys.stdout.flush()

    def _move_to(self, row: int, col: int = 1):
        self._write(f"\033[{row};{col}H")

    def _setup_scroll_region(self):
        scroll_bottom = self._rows - BOTTOM_LINES
        if scroll_bottom < 5:
            scroll_bottom = 5
        self._write(f"\033[1;{scroll_bottom}r")
        self._write(f"\033[{self._rows};1H")

    def _restore_scroll_region(self):
        self._write(f"\033[1;{self._rows}r")

    def _fmt_tok(self, n: int) -> str:
        if n < 1000:
            return str(n)
        if n < 1000000:
            return f"{n / 1000:.1f}K"
        return f"{n / 1000000:.2f}M"

    # ── 初始化 ──

    def init_screen(self, model_display: str, version: str = ""):
        self._model_display = model_display
        self._version = version
        self._cols = shutil.get_terminal_size((80, 24)).columns
        self._rows = shutil.get_terminal_size((80, 24)).lines
        self._write(A.SHOW_CURSOR)
        self._setup_scroll_region()
        self._draw_bottom()

    # ── 底部绘制（3 行：状态 + 分隔线 + 输入）──

    def _draw_bottom(self, input_buffer: str = "", cursor_pos: int = -1):
        sb = self._rows - BOTTOM_LINES
        self._write(A.SAVE_CURSOR)

        # 行 1：状态（平铺一行，无 emoji 图标）
        self._move_to(sb + 1)
        self._write(A.CLEAR_LINE)
        if self._is_running:
            status = self._status_text or "运行中"
            self._write(f"  {A.GOLD}MUNDO{A.RESET} {A.DIM}·{A.RESET} {self._status_color}{status}{A.RESET}")
            if self._stats:
                tok = self._fmt_tok(self._stats.total_tokens)
                self._write(f" {A.DIM}·{A.RESET} {A.CYAN}{tok} tokens{A.RESET} {A.DIM}·{A.RESET} {A.AMBER}⏱ {self._stats.elapsed_str}{A.RESET}")
        elif self._stats:
            tok = self._fmt_tok(self._stats.total_tokens)
            self._write(
                f"  {A.GOLD}MUNDO{A.RESET}"
                f" {A.DIM}·{A.RESET} {A.IRON}{self._model_display}{A.RESET}"
                f" {A.DIM}·{A.RESET} {A.CYAN}{tok} tokens{A.RESET}"
                f" {A.DIM}·{A.RESET} {A.AMBER}⏱ {self._stats.elapsed_str}{A.RESET}"
                f" {A.DIM}·{A.RESET} {A.IRON}T{self._stats.turns}{A.RESET}"
            )
        else:
            ver = f" v{self._version}" if self._version else ""
            self._write(f"  {A.GOLD}MUNDO{A.DIM}{ver}{A.RESET} {A.DIM}·{A.RESET} {A.IRON}{self._model_display}{A.RESET}")

        # 行 2：分隔线（dim，终端宽度）
        self._move_to(sb + 2)
        self._write(A.CLEAR_LINE + A.DIM + "─" * self._cols + A.RESET)

        # 行 3：输入
        self._move_to(sb + 3)
        self._write(A.CLEAR_LINE)
        if self._is_running:
            self._write(f"  {A.DIM}▸ 任务执行中，完成后处理下一条{A.RESET}")
        else:
            self._write(f"  {A.GOLD}>{A.RESET} {input_buffer}")
            if cursor_pos >= 0:
                before_w = _display_width(input_buffer[:cursor_pos])
                self._move_to(sb + 3, 4 + before_w)
                self._write(A.SHOW_CURSOR)

        self._write(A.RESTORE_CURSOR)

    def _update_bottom(self, input_buffer: str = "", cursor_pos: int = -1):
        self._write(A.SAVE_CURSOR)
        self._draw_bottom(input_buffer, cursor_pos)
        self._write(A.RESTORE_CURSOR)

    # ── 输入（raw terminal，自动换行）──

    def read_input(self) -> str:
        import termios
        import tty

        buf = []
        cur = 0
        self._draw_bottom("", 0)

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = os.read(fd, 1)
                if not ch:
                    continue

                if ch in (b"\r", b"\n"):
                    self._write(A.HIDE_CURSOR + "\n")
                    return "".join(buf)

                if ch == b"\x03":
                    self._write(A.SHOW_CURSOR + "\n")
                    raise KeyboardInterrupt

                if ch == b"\x04":
                    if not buf:
                        self._write(A.SHOW_CURSOR)
                        return ""
                    continue

                if ch in (b"\x7f", b"\x08"):
                    if cur > 0:
                        buf.pop(cur - 1)
                        cur -= 1
                    self._draw_bottom("".join(buf), cur)
                    continue

                if ch == b"\x15":
                    buf = buf[cur:]
                    cur = 0
                    self._draw_bottom("".join(buf), cur)
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
                    self._draw_bottom("".join(buf), cur)
                    continue

                if ch == b"\x1b":
                    seq = os.read(fd, 2)
                    if seq == b"[C" and cur < len(buf):
                        cur += 1
                    elif seq == b"[D" and cur > 0:
                        cur -= 1
                    self._draw_bottom("".join(buf), cur)
                    continue

                # UTF-8 多字节
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

                self._draw_bottom("".join(buf), cur)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    # ── 日志输出 ──

    def log_thinking(self, turn: int):
        import time as _t
        self._resp_start = _t.time()
        self._status_text = f"思考 Turn {turn}"
        self._status_color = A.AMBER
        self._write(f"\n  {A.AMBER}▸ 思考中... (Turn {turn}){A.RESET}\n")
        self._update_bottom()

    def log_tool_start(self, tool_name: str, tool_args: dict):
        self._status_text = tool_name
        self._status_color = A.TOOL
        info = self._fmt_tool_info(tool_name, tool_args)
        self._write(f"\n  {A.TOOL}▸ {tool_name}{A.RESET}  {A.DIM}{info}{A.RESET}\n")
        self._update_bottom()

    def log_tool_output(self, tool_name: str, output: str, is_error: bool = False):
        color = A.ERROR if is_error else A.IRON
        mark = "✗" if is_error else "│"
        if not output:
            self._write(f"  {color}{mark} {A.DIM}(无输出){A.RESET}\n")
            self._update_bottom()
            return
        for line in self._fmt_tool_output(tool_name, output).split("\n"):
            self._write(f"  {color}{mark} {line[:self._cols - 6]}{A.RESET}\n")
        self._update_bottom()

    def log_tool_done(self, tool_name: str, duration: float):
        if duration > 1.0:
            self._write(f"  {A.SUCCESS}✓ {tool_name} {A.DIM}({duration:.1f}s){A.RESET}\n")
        self._status_text = "思考中"
        self._status_color = A.AMBER
        self._update_bottom()

    def log_delegation(self, agent_names: list, clone_count: int, total: int):
        self._write(f"\n  {A.CYAN}━━ 分发 ━━{A.RESET}\n")
        for name in set(agent_names):
            self._write(f"  {A.SUCCESS}  ▸ {name}{A.RESET}\n")
        if clone_count > 0:
            self._write(f"  {A.AMBER}  ▸ {clone_count} 个分身{A.RESET}\n")
        self._write(f"  {A.DIM}  共 {total} 子任务{A.RESET}\n")
        self._update_bottom()

    def log_clones(self, count: int):
        for i in range(1, count + 1):
            self._write(f"  {A.GOLD}  分身 #{i}{A.RESET}\n")
        self._update_bottom()

    def log_response(self, text: str):
        self._write(f"\n{A.IRON}")
        for line in text.split("\n"):
            self._write(f"  {line}\n")
        self._write(f"{A.RESET}\n")
        self._update_bottom()

    def log_error(self, error: str):
        self._write(f"\n  {A.ERROR}✗ {error}{A.RESET}\n\n")
        self._update_bottom()

    def log_done(self, stats):
        tok = self._fmt_tok(stats.total_tokens)
        elapsed = stats.elapsed_str
        llm_pct = f"{stats.llm_time / max(stats.elapsed, 0.01) * 100:.0f}%"
        tool_pct = f"{stats.tool_time / max(stats.elapsed, 0.01) * 100:.0f}%"

        sep = A.DIM + "─" * min(self._cols - 8, 60) + A.RESET
        self._write(f"\n  {sep}\n")
        self._write(
            f"  {A.SUCCESS}✓{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.AMBER}⏱ {elapsed}{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.CYAN}{tok} tokens{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.IRON}T{stats.turns} LLM {llm_pct} Tools {tool_pct}{A.RESET}"
        )
        if stats.tool_calls_count > 0:
            self._write(f" {A.DIM}·{A.RESET} {A.IRON}{stats.tool_calls_count} tools{A.RESET}")
        self._write(f"\n  {sep}\n\n")

        self._is_running = False
        self._status_text = ""
        self._update_bottom()

    # ── 任务状态 ──

    def start_task(self):
        self._is_running = True
        self._status_text = "接管中"
        self._status_color = A.GOLD
        self._update_bottom()

    def stop_task(self):
        self._is_running = False
        self._status_text = ""
        self._update_bottom()

    def cleanup(self):
        self._restore_scroll_region()
        self._write(A.SHOW_CURSOR + A.RESET)

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
    """兼容 -q 查询模式的简单状态栏"""

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
