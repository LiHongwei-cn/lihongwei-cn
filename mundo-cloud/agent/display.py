"""蒙多执行控制台 v2 — 紧凑 banner + 金色条输入框 + 自动调整大小

布局（参考 Hermes Agent / Claude Code）：
  ┌─ 滚动日志区 ─────────────────────────────┐
  │ 蒙多的思考、工具调用、工具输出             │
  ├─ 底部固定区 ─────────────────────────────┤
  │ 📊 Tokens · ⏱ Elapsed · Turns · Tools     │  ← token 栏
  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │  ← 金色上条
  │ 👑 xiaomi/mimo-v2.5-pro · v24.2          │  ← 模型行
  │ > 用户输入，自动换行                       │  ← 输入区
  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │  ← 金色下条
  └──────────────────────────────────────────┘
"""

import sys
import os
import re
import shutil
import unicodedata


# ═══════════════════════════════════════════════
# ANSI 转义码
# ═══════════════════════════════════════════════

class A:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CLEAR_LINE = "\033[2K\r"
    SAVE_CURSOR = "\033[s"
    RESTORE_CURSOR = "\033[u"
    GOLD = "\033[38;5;178m"
    CRIMSON = "\033[38;5;131m"
    IRON = "\033[38;5;243m"
    STEEL = "\033[38;5;248m"
    AMBER = "\033[38;5;136m"
    SUCCESS = "\033[38;5;65m"
    ERROR = "\033[38;5;131m"
    TOOL = "\033[38;5;245m"
    CYAN = "\033[38;5;87m"
    WHITE = "\033[38;5;255m"
    BG_DARK = "\033[48;5;234m"
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"
    GOLD_DIM = "\033[38;5;136m"


# ═══════════════════════════════════════════════
# ANSI / 字符宽度工具函数
# ═══════════════════════════════════════════════

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")

def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)

def _display_width(text: str) -> int:
    """计算显示宽度（CJK 字符占 2 列）"""
    w = 0
    for ch in text:
        if ord(ch) < 32:
            continue
        eaw = unicodedata.east_asian_width(ch)
        w += 2 if eaw in ("W", "F") else 1
    return w

def _collected_width(text: str) -> int:
    """计算含 ANSI 码文本的显示宽度"""
    return _display_width(_strip_ansi(text))


# ═══════════════════════════════════════════════
# TaskConsole
# ═══════════════════════════════════════════════

class TaskConsole:
    """蒙多执行控制台 — 紧凑布局 + 金色条输入框 + 自动调整大小"""

    BOTTOM_LINES = 5  # token + gold_top + model + input + gold_bot

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

    # ─────────────────────────────────────────
    # 底层终端操作
    # ─────────────────────────────────────────

    def _write(self, text: str):
        sys.stdout.write(text)
        sys.stdout.flush()

    def _move_to(self, row: int, col: int = 1):
        self._write(f"\033[{row};{col}H")

    def _clear_from_cursor(self):
        self._write("\033[J")

    def _setup_scroll_region(self):
        scroll_bottom = self._rows - self.BOTTOM_LINES
        if scroll_bottom < 5:
            scroll_bottom = 5
        self._write(f"\033[1;{scroll_bottom}r")
        self._write(f"\033[{self._rows};1H")

    def _restore_scroll_region(self):
        self._write(f"\033[1;{self._rows}r")

    def _format_tokens(self, n: int) -> str:
        if n < 1000:
            return str(n)
        if n < 1000000:
            return f"{n / 1000:.1f}K"
        return f"{n / 1000000:.2f}M"

    # ─────────────────────────────────────────
    # 初始化
    # ─────────────────────────────────────────

    def init_screen(self, model_display: str, version: str = ""):
        self._model_display = model_display
        self._version = version
        self._cols = shutil.get_terminal_size((80, 24)).columns
        self._rows = shutil.get_terminal_size((80, 24)).lines
        self._write(A.SHOW_CURSOR)
        self._setup_scroll_region()
        self._draw_bottom()

    # ─────────────────────────────────────────
    # 底部区域绘制
    # ─────────────────────────────────────────

    def _gold_bar(self) -> str:
        return A.GOLD_DIM + "━" * self._cols + A.RESET

    def _input_lines_count(self, input_buffer: str) -> int:
        """计算输入文本占用的行数（含 CJK 宽字符）"""
        if not input_buffer:
            return 1
        prefix_width = 2  # "> "
        available = self._cols - prefix_width
        if available < 10:
            available = 10
        total_w = _display_width(input_buffer)
        lines = max(1, (total_w + available - 1) // available)
        return min(lines, 8)

    def _draw_bottom(self, input_buffer: str = "", cursor_pos: int = -1):
        """绘制底部固定区域"""
        scroll_bottom = self._rows - self.BOTTOM_LINES
        self._write(A.SAVE_CURSOR)

        # Token 统计栏
        self._move_to(scroll_bottom + 1)
        self._write(A.CLEAR_LINE)
        self._draw_token_bar(scroll_bottom + 1)

        # 金色上条
        self._move_to(scroll_bottom + 2)
        self._write(A.CLEAR_LINE + self._gold_bar())

        # 模型信息行
        self._move_to(scroll_bottom + 3)
        self._write(A.CLEAR_LINE)
        self._draw_model_line(scroll_bottom + 3)

        # 输入区域
        self._move_to(scroll_bottom + 4)
        self._write(A.CLEAR_LINE)
        if self._is_running:
            status = self._status_text or "蒙多接管中..."
            self._write(
                f"  {A.GOLD}▸{A.RESET}"
                f"  {self._status_color}{status}{A.RESET}"
            )
        else:
            self._write(f"  {A.GOLD_BOLD}> {A.RESET}{input_buffer}")
            if cursor_pos >= 0:
                prefix_w = 2
                before = input_buffer[:cursor_pos]
                before_w = _display_width(before)
                target_col = prefix_w + before_w + 1
                self._move_to(scroll_bottom + 4, target_col)
                self._write(A.SHOW_CURSOR)

        # 金色下条
        self._move_to(scroll_bottom + 5)
        self._write(A.CLEAR_LINE + self._gold_bar())

        self._write(A.RESTORE_CURSOR)

    def _draw_token_bar(self, row: int):
        self._move_to(row)
        self._write(A.CLEAR_LINE)
        if self._stats:
            tok = self._format_tokens(self._stats.total_tokens)
            tok_in = self._format_tokens(self._stats.prompt_tokens)
            tok_out = self._format_tokens(self._stats.completion_tokens)
            elapsed = self._stats.elapsed_str
            turns = self._stats.turns
            tools = self._stats.tool_calls_count
            self._write(
                f"  {A.CYAN}📊 {tok} tokens{A.RESET}"
                f"  {A.DIM}({tok_in}→{tok_out}){A.RESET}"
                f"  {A.AMBER}⏱ {elapsed}{A.RESET}"
                f"  {A.IRON}T{turns} · {tools} tools{A.RESET}"
            )
        else:
            self._write(f"  {A.DIM}等待任务...{A.RESET}")

    def _draw_model_line(self, row: int):
        self._move_to(row)
        self._write(A.CLEAR_LINE)
        if self._model_display:
            ver = f" · v{self._version}" if self._version else ""
            self._write(f"  {A.GOLD_BOLD}👑 {self._model_display}{ver}{A.RESET}")

    def _update_bottom(self, input_buffer: str = "", cursor_pos: int = -1):
        self._write(A.SAVE_CURSOR)
        self._draw_bottom(input_buffer, cursor_pos)
        self._write(A.RESTORE_CURSOR)

    # ─────────────────────────────────────────
    # 带金色条的多行输入（自动调整大小）
    # ─────────────────────────────────────────

    def read_input(self) -> str:
        """读取用户输入，带金色条框和自动换行支持"""
        import termios
        import tty

        buffer = []
        cursor = 0
        self._draw_bottom("", 0)

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = os.read(fd, 1)
                if not ch:
                    continue

                if ch == b"\r" or ch == b"\n":
                    self._write(A.HIDE_CURSOR)
                    self._write("\n")
                    return "".join(buffer)

                if ch == b"\x03":  # Ctrl+C
                    self._write(A.HIDE_CURSOR)
                    self._write(A.SHOW_CURSOR)
                    self._write("\n")
                    raise KeyboardInterrupt

                if ch == b"\x04":  # Ctrl+D
                    if not buffer:
                        self._write(A.HIDE_CURSOR)
                        self._write(A.SHOW_CURSOR)
                        return ""
                    continue

                if ch == b"\x7f" or ch == b"\x08":  # Backspace
                    if cursor > 0:
                        buffer.pop(cursor - 1)
                        cursor -= 1
                    self._draw_bottom("".join(buffer), cursor)
                    continue

                if ch == b"\x15":  # Ctrl+U
                    buffer = buffer[cursor:]
                    cursor = 0
                    self._draw_bottom("".join(buffer), cursor)
                    continue

                if ch == b"\x17":  # Ctrl+W
                    if cursor > 0:
                        i = cursor - 1
                        while i > 0 and buffer[i - 1] == " ":
                            i -= 1
                        while i > 0 and buffer[i - 1] != " ":
                            i -= 1
                        del buffer[i:cursor]
                        cursor = i
                    self._draw_bottom("".join(buffer), cursor)
                    continue

                if ch == b"\x1b":  # 箭头键
                    seq = os.read(fd, 2)
                    if seq == b"[C" and cursor < len(buffer):
                        cursor += 1
                        self._draw_bottom("".join(buffer), cursor)
                    elif seq == b"[D" and cursor > 0:
                        cursor -= 1
                        self._draw_bottom("".join(buffer), cursor)
                    continue

                # 普通字符（含 UTF-8 多字节）
                if ch[0] > 0x7f:
                    extra = 1
                    if ch[0] & 0xE0 == 0xC0:
                        extra = 1
                    elif ch[0] & 0xF0 == 0xE0:
                        extra = 2
                    elif ch[0] & 0xF8 == 0xF0:
                        extra = 3
                    ch += os.read(fd, extra)

                try:
                    decoded = ch.decode("utf-8")
                    buffer.insert(cursor, decoded)
                    cursor += 1
                except UnicodeDecodeError:
                    continue

                self._draw_bottom("".join(buffer), cursor)

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    # ─────────────────────────────────────────
    # 日志输出（滚动区域）
    # ─────────────────────────────────────────

    def log_thinking(self, turn: int):
        import time as _t
        self._resp_start = _t.time()
        self._status_text = f"思考中 (Turn {turn})..."
        self._status_color = A.AMBER
        self._write(f"\n  {A.AMBER}▸ 思考中... (Turn {turn}){A.RESET}\n")
        self._update_bottom()

    def log_tool_start(self, tool_name: str, tool_args: dict):
        self._status_text = f"▸ {tool_name}"
        self._status_color = A.TOOL
        info = self._format_tool_info(tool_name, tool_args)
        self._write(f"\n  {A.TOOL}▸ {A.BOLD}{tool_name}{A.RESET}  {A.DIM}{info}{A.RESET}\n")
        self._update_bottom()

    def log_tool_output(self, tool_name: str, output: str, is_error: bool = False):
        color = A.ERROR if is_error else A.IRON
        prefix = "✗" if is_error else "│"
        if not output:
            self._write(f"  {color}{prefix} {A.DIM}(无输出){A.RESET}\n")
            self._update_bottom()
            return
        formatted = self._format_tool_output(tool_name, output)
        for line in formatted.split("\n"):
            display_line = line[:self._cols - 6] if len(line) > self._cols - 6 else line
            self._write(f"  {color}{prefix} {display_line}{A.RESET}\n")
        self._update_bottom()

    def log_tool_done(self, tool_name: str, duration: float):
        if duration > 1.0:
            self._write(f"  {A.SUCCESS}✓ {tool_name} {A.DIM}({duration:.1f}s){A.RESET}\n")
        self._status_text = "思考中..."
        self._status_color = A.AMBER
        self._update_bottom()

    def log_delegation(self, agent_names: list, clone_count: int, total_subtasks: int):
        self._write(f"\n  {A.CYAN}━━ 任务分发 ━━{A.RESET}\n")
        for name in set(agent_names):
            self._write(f"  {A.SUCCESS}  ▸ 调用 {name}...{A.RESET}\n")
        if clone_count > 0:
            self._write(f"  {A.AMBER}  ▸ 蒙多分出 {clone_count} 个分身并行执行{A.RESET}\n")
        self._write(f"  {A.DIM}  共 {total_subtasks} 个子任务{A.RESET}\n")
        self._update_bottom()

    def log_clones(self, count: int):
        for i in range(1, count + 1):
            self._write(f"  {A.GOLD}  👑 分身 #{i} 已出动{A.RESET}\n")
        self._update_bottom()

    def log_response(self, text: str):
        self._write(f"\n{A.STEEL}")
        for line in text.split("\n"):
            self._write(f"  {line}\n")
        self._write(f"{A.RESET}\n")
        self._update_bottom()

    def log_error(self, error: str):
        self._write(f"\n  {A.ERROR}✗ {error}{A.RESET}\n\n")
        self._update_bottom()

    def log_done(self, stats):
        tok = self._format_tokens(stats.total_tokens)
        tok_in = self._format_tokens(stats.prompt_tokens)
        tok_out = self._format_tokens(stats.completion_tokens)
        elapsed = stats.elapsed_str
        llm_pct = f"{stats.llm_time / max(stats.elapsed, 0.01) * 100:.0f}%"
        tool_pct = f"{stats.tool_time / max(stats.elapsed, 0.01) * 100:.0f}%"

        import time as _t
        if self._resp_start > 0:
            latency = _t.time() - self._resp_start
            latency_pct = f"{latency / max(stats.elapsed, 0.01) * 100:.0f}%"
        else:
            latency_pct = "0%"

        sep = A.DIM + "─" * min(self._cols - 8, 60) + A.RESET
        self._write(f"\n  {sep}\n")
        self._write(
            f"  {A.SUCCESS}✓ 完成{A.RESET}"
            f"  {A.DIM}│{A.RESET}"
            f"  {A.AMBER}⏱ {elapsed}{A.RESET}"
            f"  {A.DIM}│{A.RESET}"
            f"  {A.CYAN}Tokens: {tok} ({tok_in}→{tok_out}){A.RESET}"
            f"  {A.DIM}│{A.RESET}"
            f"  {A.IRON}T{stats.turns} LLM {llm_pct} Tools {tool_pct} Overhead {latency_pct}{A.RESET}"
        )
        if stats.tool_calls_count > 0:
            self._write(f"  {A.DIM}│{A.RESET}  {A.IRON}{stats.tool_calls_count} tool calls{A.RESET}")
        self._write(f"\n  {sep}\n\n")

        self._is_running = False
        self._status_text = ""
        self._status_color = A.IRON
        self._update_bottom()

    # ─────────────────────────────────────────
    # 任务状态
    # ─────────────────────────────────────────

    def start_task(self):
        self._is_running = True
        self._status_text = "蒙多接管中..."
        self._status_color = A.GOLD
        self._update_bottom()

    def stop_task(self):
        self._is_running = False
        self._status_text = ""
        self._status_color = A.IRON
        self._update_bottom()

    def cleanup(self):
        self._restore_scroll_region()
        self._write(A.SHOW_CURSOR)
        self._write(A.RESET)

    # ─────────────────────────────────────────
    # 格式化辅助
    # ─────────────────────────────────────────

    def _format_tool_info(self, tool_name: str, tool_args: dict) -> str:
        if tool_name == "terminal":
            return tool_args.get("command", "")[:60]
        if tool_name in ("read_file", "write_file"):
            return tool_args.get("path", "")
        if tool_name == "search_files":
            return tool_args.get("pattern", "")
        if tool_name == "web_search":
            return tool_args.get("query", "")
        if tool_name == "list_directory":
            return tool_args.get("path", ".")
        return str(tool_args)[:60]

    def _format_tool_output(self, tool_name: str, output: str) -> str:
        max_lines = 30

        if tool_name == "terminal":
            lines = output.strip().split("\n")
            if len(lines) > max_lines:
                head = lines[:max_lines // 2]
                tail = lines[-5:]
                return "\n".join(head) + f"\n  ... ({len(lines) - max_lines + 5} 行已省略)\n" + "\n".join(tail)
            return output.strip()

        if tool_name == "write_file":
            return output.strip()

        if tool_name == "read_file":
            lines = output.strip().split("\n")
            if len(lines) > max_lines:
                return "\n".join(lines[:max_lines]) + f"\n  ... ({len(lines) - max_lines} 行已省略)"
            return output.strip()

        if tool_name == "search_files":
            lines = output.strip().split("\n")
            if len(lines) > 20:
                return "\n".join(lines[:20]) + f"\n  ... (共 {len(lines)} 条匹配)"
            return output.strip()

        if tool_name == "web_search":
            return output.strip()

        if tool_name == "list_directory":
            return output.strip()

        if len(output) > 2000:
            return output[:2000] + "\n  ... (已截断)"
        return output.strip()


# A 的别名引用（在类定义之后）
A = A  # noqa: F841


class StatusBar:
    """向后兼容的简单状态栏（供 -q 查询模式使用）"""

    def __init__(self):
        self._cols = shutil.get_terminal_size((80, 24)).columns

    @staticmethod
    def _format_tokens(n: int) -> str:
        if n < 1000:
            return str(n)
        if n < 1000000:
            return f"{n / 1000:.1f}K"
        return f"{n / 1000000:.2f}M"

    def show_thinking(self, model: str, turn: int, stats):
        sys.stdout.write(
            f"\r{A.CLEAR_LINE}  {A.AMBER}▸ 思考中 (Turn {turn})"
            f"  {A.DIM}│{A.RESET}  {A.CYAN}Tokens: {self._format_tokens(stats.total_tokens)}{A.RESET}"
            f"  {A.DIM}│{A.RESET}  {A.AMBER}⏱ {stats.elapsed_str}{A.RESET}  "
        )
        sys.stdout.flush()

    def show_tool_start(self, model: str, tool_name: str, tool_info: str, stats):
        sys.stdout.write(
            f"\r{A.CLEAR_LINE}  {A.TOOL}▸ {tool_name}: {tool_info[:30]}"
            f"  {A.DIM}│{A.RESET}  {A.CYAN}Tokens: {self._format_tokens(stats.total_tokens)}{A.RESET}  "
        )
        sys.stdout.flush()

    def show_done(self, model: str, stats):
        tok = self._format_tokens(stats.total_tokens)
        sys.stdout.write(A.CLEAR_LINE)
        print(f"\n  {A.SUCCESS}✓ 完成{A.RESET}  {A.DIM}│{A.RESET}  {A.AMBER}⏱ {stats.elapsed_str}{A.RESET}  {A.DIM}│{A.RESET}  {A.CYAN}Tokens: {tok}{A.RESET}\n")

    def show_error(self, model: str, error: str, stats):
        tok = self._format_tokens(stats.total_tokens)
        sys.stdout.write(A.CLEAR_LINE)
        print(f"\n  {A.ERROR}✗ 失败{A.RESET}  {A.DIM}│{A.RESET}  {A.CYAN}Tokens: {tok}{A.RESET}  {A.ERROR}{error[:60]}{A.RESET}\n")
