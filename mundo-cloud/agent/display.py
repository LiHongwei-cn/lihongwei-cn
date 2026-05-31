"""蒙多执行控制台 v6 — 彩色输出 + 金色条输入框 + 实时 token

布局：
  运行中：彩色日志直接滚动输出
  等待输入：
    ━━━━━━━━━ 金色条（含实时 token）━━━━━━━━━
    > 用户输入
    ━━━━━━━━━ 金色条 ━━━━━━━━━━━━━━━━━━━━━━━
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
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    CLEAR_LINE = "\033[2K\r"
    GOLD = "\033[38;5;178m"
    GOLD_BRIGHT = "\033[38;5;220m"
    GOLD_DIM = "\033[38;5;136m"
    IRON = "\033[38;5;243m"
    STEEL = "\033[38;5;248m"
    AMBER = "\033[38;5;136m"
    SUCCESS = "\033[38;5;65m"
    ERROR = "\033[38;5;203m"
    TOOL = "\033[38;5;111m"
    CYAN = "\033[38;5;87m"
    GREEN = "\033[38;5;82m"
    YELLOW = "\033[38;5;226m"
    RED = "\033[38;5;196m"
    BLUE = "\033[38;5;75m"
    PURPLE = "\033[38;5;141m"
    WHITE = "\033[38;5;255m"
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"


def _display_width(text: str) -> int:
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
        self._model_display = ""
        self._version = ""
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

    def _gold_bar(self, content: str = "") -> str:
        """金色条，可选中间嵌入内容"""
        bar_char = "━"
        if content:
            # 内容嵌入在条中间
            content_w = _display_width(content)
            # ANSI 码不算宽度
            side_w = (self._cols - content_w - 4) // 2
            if side_w < 5:
                side_w = 5
            left = bar_char * side_w
            right = bar_char * (self._cols - side_w - content_w - 4)
            return f"  {A.GOLD}{left}{A.RESET} {content} {A.GOLD}{right}{A.RESET}"
        else:
            return f"  {A.GOLD}{bar_char * (self._cols - 4)}{A.RESET}"

    # ── 初始化 ──

    def init_screen(self, model_display: str, version: str = ""):
        self._model_display = model_display
        self._version = version
        self._cols = shutil.get_terminal_size((80, 24)).columns

    # ── 输入区（带金色条）──

    def _build_token_display(self) -> str:
        """构建 token 显示文本"""
        if self._stats and self._stats.total_tokens > 0:
            tok = self._fmt_tok(self._stats.total_tokens)
            return f"{A.CYAN}{tok} tokens{A.RESET}"
        return f"{A.DIM}0 tokens{A.RESET}"

    def read_input(self) -> str:
        import termios
        import tty

        # 金色上条（含 token）
        token_str = self._build_token_display()
        self._w(f"\n{self._gold_bar(token_str)}\n")

        # 输入提示符
        self._w(f"  {A.GOLD_BRIGHT}>{A.RESET} ")

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
                    # 金色下条
                    self._w(f"\n{self._gold_bar()}\n")
                    self._w(A.SHOW_CURSOR)
                    return "".join(buf)

                if ch == b"\x03":
                    self._w(f"\n{self._gold_bar()}\n")
                    self._w(A.SHOW_CURSOR)
                    raise KeyboardInterrupt

                if ch == b"\x04":
                    if not buf:
                        self._w(f"\n{self._gold_bar()}\n")
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
        self._w(f"\r{A.CLEAR_LINE}  {A.GOLD_BRIGHT}>{A.RESET} {text}")
        if cur < len(text):
            before_w = _display_width(text[:cur])
            self._w(f"\033[{4 + before_w}G")
        self._w(A.SHOW_CURSOR)

    # ── 日志输出（彩色）──

    def log_thinking(self, turn: int):
        self._task_start = _time.time()
        self._stats = None
        self._w(f"\n  {A.AMBER}▸{A.RESET} {A.STEEL}思考中...{A.RESET} {A.DIM}(Turn {turn}){A.RESET}\n")

    def log_tool_start(self, tool_name: str, tool_args: dict):
        self._last_tool_start = _time.time()
        info = self._fmt_tool_info(tool_name, tool_args)
        # 工具名用蓝色，参数用灰色
        self._w(f"\n  {A.BLUE}▸{A.RESET} {A.BOLD}{A.TOOL}{tool_name}{A.RESET}  {A.DIM}{info}{A.RESET}\n")

    def log_tool_output(self, tool_name: str, output: str, is_error: bool = False):
        if is_error:
            color = A.ERROR
            mark = f"{A.RED}✗{A.RESET}"
        else:
            color = A.IRON
            mark = f"{A.GREEN}│{A.RESET}"
        if not output:
            self._w(f"  {mark} {A.DIM}(无输出){A.RESET}\n")
            return
        for line in self._fmt_tool_output(tool_name, output).split("\n"):
            # 根据内容高亮
            colored_line = self._colorize_line(line, tool_name)
            self._w(f"  {mark} {colored_line}\n")

    def log_tool_done(self, tool_name: str, duration: float):
        if duration > 0.5:
            self._w(f"  {A.SUCCESS}✓{A.RESET} {A.GREEN}{tool_name}{A.RESET} {A.DIM}({duration:.1f}s){A.RESET}\n")

    def log_delegation(self, agent_names: list, clone_count: int, total: int):
        self._w(f"\n  {A.CYAN}━━ 分发 ━━{A.RESET}\n")
        for name in set(agent_names):
            self._w(f"  {A.SUCCESS}  ▸ {name}{A.RESET}\n")
        if clone_count > 0:
            self._w(f"  {A.AMBER}  ▸ {clone_count} 个分身{A.RESET}\n")
        self._w(f"  {A.DIM}  共 {total} 个子任务{A.RESET}\n")

    def log_clones(self, count: int):
        for i in range(1, count + 1):
            self._w(f"  {A.GOLD}  👑 分身 #{i}{A.RESET}\n")

    def log_response(self, text: str):
        self._w(f"\n")
        for line in text.split("\n"):
            self._w(f"  {A.STEEL}{line}{A.RESET}\n")
        self._w("\n")

    def log_error(self, error: str):
        self._w(f"\n  {A.RED}✗{A.RESET} {A.ERROR}{error}{A.RESET}\n\n")

    def log_done(self, stats):
        self._stats = stats
        tok = self._fmt_tok(stats.total_tokens)
        tok_in = self._fmt_tok(stats.prompt_tokens)
        tok_out = self._fmt_tok(stats.completion_tokens)
        elapsed = stats.elapsed_str
        llm_pct = f"{stats.llm_time / max(stats.elapsed, 0.01) * 100:.0f}%"
        tool_pct = f"{stats.tool_time / max(stats.elapsed, 0.01) * 100:.0f}%"

        sep = A.GOLD + "━" * min(self._cols - 4, 50) + A.RESET
        self._w(f"\n  {sep}\n")
        self._w(
            f"  {A.GREEN}✓{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.AMBER}⏱ {elapsed}{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.CYAN}{tok} tokens{A.RESET}"
            f" {A.DIM}({tok_in}→{tok_out}){A.RESET}"
            f" {A.DIM}·{A.RESET} {A.IRON}T{stats.turns}{A.RESET}"
            f" {A.DIM}·{A.RESET} {A.IRON}LLM {llm_pct} Tools {tool_pct}{A.RESET}"
        )
        if stats.tool_calls_count > 0:
            self._w(f" {A.DIM}·{A.RESET} {A.IRON}{stats.tool_calls_count} tools{A.RESET}")
        self._w(f"\n  {sep}\n")

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

    # ── 语法高亮 ──

    def _colorize_line(self, line: str, tool_name: str) -> str:
        """给输出行添加语法高亮"""
        stripped = line.strip()

        # 错误/警告
        if any(kw in stripped.lower() for kw in ["error", "err:", "错误", "failed", "fatal", "traceback"]):
            return f"{A.ERROR}{line}{A.RESET}"
        if any(kw in stripped.lower() for kw in ["warn", "warning", "警告"]):
            return f"{A.YELLOW}{line}{A.RESET}"

        # 成功
        if any(kw in stripped for kw in ["✓", "success", "ok", "完成", "done"]):
            return f"{A.GREEN}{line}{A.RESET}"

        # terminal 输出：代码高亮
        if tool_name == "terminal":
            return self._colorize_code(line)

        # 文件路径
        if "/" in stripped and (" " not in stripped[:20]):
            return f"{A.BLUE}{line}{A.RESET}"

        return f"{A.IRON}{line}{A.RESET}"

    def _colorize_code(self, line: str) -> str:
        """简单代码语法高亮"""
        stripped = line.strip()

        # shell 提示符
        if stripped.startswith("$") or stripped.startswith("#"):
            return f"{A.GREEN}{line}{A.RESET}"

        # Python 关键字
        py_keywords = ["def ", "class ", "import ", "from ", "if ", "elif ", "else:",
                       "for ", "while ", "return ", "try:", "except", "with ", "as ",
                       "async ", "await ", "yield ", "raise ", "assert ", "pass", "break", "continue"]
        if any(stripped.startswith(kw) or f" {kw}" in stripped for kw in py_keywords):
            return f"{A.PURPLE}{line}{A.RESET}"

        # 字符串
        if '"""' in stripped or "'''" in stripped:
            return f"{A.GREEN}{line}{A.RESET}"

        # 注释
        if stripped.startswith("//") or stripped.startswith("#") or stripped.startswith("--"):
            return f"{A.DIM}{line}{A.RESET}"

        # 数字开头
        if stripped and stripped[0].isdigit():
            return f"{A.CYAN}{line}{A.RESET}"

        # 路径
        if "/" in stripped and not " " in stripped[:15]:
            return f"{A.BLUE}{line}{A.RESET}"

        return f"{A.IRON}{line}{A.RESET}"

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
        print(f"\n  {A.RED}✗{A.RESET} {A.DIM}·{A.RESET} {A.CYAN}{self._fmt_tok(stats.total_tokens)}{A.RESET} {A.ERROR}{error[:60]}{A.RESET}\n")
