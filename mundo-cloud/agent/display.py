"""蒙多执行控制台 — 实时滚动日志 + 底部 Token 栏 + 状态行

布局（ANSI 控制）：
  ┌─ 执行日志区（滚动）──────────────────────┐
  │ 蒙多的思考、工具调用、工具输出实时显示     │
  ├──────────────────────────────────────────┤
  │ 📊 Tokens: 12.5K (in:8.2K out:4.3K) ... │  ← 固定底部 token 栏
  │ 👑 xiaomi/mimo-v2.5-pro │ ⚔️ 思考中...   │  ← 状态行
  │ 👑 _                                        │  ← 输入行
  └──────────────────────────────────────────┘
"""

import sys
import os
import shutil
from datetime import datetime


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
    BRIGHT_RED = "\033[38;5;203m"
    BG_DARK = "\033[48;5;234m"


class TaskConsole:
    """蒙多执行控制台 — 类似 Hermes/Claude Code 的实时输出"""

    # 底部固定区域行数：separator + token_bar + status_line + input_line = 4
    BOTTOM_LINES = 4

    def __init__(self):
        self._cols = shutil.get_terminal_size((80, 24)).columns
        self._rows = shutil.get_terminal_size((80, 24)).lines
        self._log_lines = 0
        self._status_text = ""
        self._status_color = A.AMBER
        self._model_display = ""
        self._stats = None
        self._is_running = False
        self._input_callback = None
        self._new_user_input = None
        self._separator = A.IRON + "─" * self._cols + A.RESET

    def _write(self, text: str):
        sys.stdout.write(text)
        sys.stdout.flush()

    def _format_tokens(self, n: int) -> str:
        if n < 1000:
            return str(n)
        if n < 1000000:
            return f"{n / 1000:.1f}K"
        return f"{n / 1000000:.2f}M"

    def _move_to(self, row: int, col: int = 1):
        self._write(f"\033[{row};{col}H")

    def _clear_from_cursor(self):
        self._write("\033[J")

    def _setup_scroll_region(self):
        """设置滚动区域为屏幕顶部到 (总行数 - BOTTOM_LINES)"""
        scroll_bottom = self._rows - self.BOTTOM_LINES
        if scroll_bottom < 5:
            scroll_bottom = 5
        self._write(f"\033[1;{scroll_bottom}r")
        self._write(f"\033[{self._rows};1H")

    def _restore_scroll_region(self):
        self._write(f"\033[1;{self._rows}r")

    def init_screen(self, model_display: str):
        """初始化屏幕布局"""
        self._model_display = model_display
        self._cols = shutil.get_terminal_size((80, 24)).columns
        self._rows = shutil.get_terminal_size((80, 24)).lines
        self._setup_scroll_region()
        self._draw_bottom()
        self._write(f"\033[{self._rows};3H")

    def _draw_bottom(self):
        """绘制底部固定区域（token 栏 + 状态行 + 输入行）"""
        scroll_bottom = self._rows - self.BOTTOM_LINES

        # 保存光标位置
        self._write(A.SAVE_CURSOR)

        # 分隔线
        self._move_to(scroll_bottom + 1)
        self._write(A.CLEAR_LINE + self._separator)

        # Token 栏
        self._draw_token_bar()

        # 状态行
        self._draw_status_line()

        # 输入行
        self._draw_input_line()

        # 恢复光标
        self._write(A.RESTORE_CURSOR)

    def _draw_token_bar(self):
        """绘制 token 统计栏"""
        scroll_bottom = self._rows - self.BOTTOM_LINES
        self._move_to(scroll_bottom + 2)
        self._write(A.CLEAR_LINE)

        if self._stats:
            tok = self._format_tokens(self._stats.total_tokens)
            tok_in = self._format_tokens(self._stats.prompt_tokens)
            tok_out = self._format_tokens(self._stats.completion_tokens)
            elapsed = self._stats.elapsed_str
            turns = self._stats.turns
            tools = self._stats.tool_calls_count

            bar = (
                f"  {A.CYAN}📊 Tokens: {tok}{A.RESET}"
                f"  {A.DIM}(in:{tok_in} out:{tok_out}){A.RESET}"
                f"  {A.AMBER}⏱ {elapsed}{A.RESET}"
                f"  {A.IRON}Turn {turns}  Tools {tools}{A.RESET}"
            )
            self._write(bar)
        else:
            self._write(f"  {A.DIM}📊 等待任务...{A.RESET}")

    def _draw_status_line(self):
        """绘制状态行"""
        scroll_bottom = self._rows - self.BOTTOM_LINES
        self._move_to(scroll_bottom + 3)
        self._write(A.CLEAR_LINE)

        if self._model_display:
            status = self._status_text or ("等待指令..." if not self._is_running else "运行中...")
            self._write(
                f"  {A.GOLD}👑 {self._model_display}{A.RESET}"
                f"  {A.DIM}│{A.RESET}"
                f"  {self._status_color}{status}{A.RESET}"
            )

    def _draw_input_line(self):
        """绘制输入行"""
        scroll_bottom = self._rows - self.BOTTOM_LINES
        self._move_to(scroll_bottom + 4)
        self._write(A.CLEAR_LINE)
        if self._is_running:
            self._write(f"  {A.GOLD}👑 {A.DIM}(任务执行中，输入新指令将在当前任务完成后处理){A.RESET}")
        else:
            self._write(f"  {A.GOLD}👑 {A.RESET}")

    def _update_bottom(self):
        """刷新底部区域（不移动滚动区光标）"""
        self._write(A.SAVE_CURSOR)
        self._draw_token_bar()
        self._draw_status_line()
        self._draw_input_line()
        self._write(A.RESTORE_CURSOR)

    # ───────────────────────────────────────────
    # 日志输出（滚动区域）
    # ───────────────────────────────────────────

    def log_thinking(self, turn: int):
        """显示蒙多思考中"""
        self._status_text = f"⚔️  思考中 (Turn {turn})..."
        self._status_color = A.AMBER
        self._write(f"\n  {A.AMBER}⚔️  蒙多思考中... (Turn {turn}){A.RESET}\n")
        self._update_bottom()

    def log_tool_start(self, tool_name: str, tool_args: dict):
        """显示工具调用开始"""
        self._status_text = f"▸ {tool_name}"
        self._status_color = A.TOOL

        # 格式化工具信息
        info = self._format_tool_info(tool_name, tool_args)
        self._write(f"\n  {A.TOOL}▸ {A.BOLD}{tool_name}{A.RESET}  {A.DIM}{info}{A.RESET}\n")
        self._update_bottom()

    def log_tool_output(self, tool_name: str, output: str, is_error: bool = False):
        """显示工具执行输出（核心 — 实时滚动输出）"""
        color = A.ERROR if is_error else A.IRON
        prefix = "✗" if is_error else "│"

        if not output:
            self._write(f"  {color}{prefix} {A.DIM}(无输出){A.RESET}\n")
            self._update_bottom()
            return

        # 根据工具类型格式化输出
        formatted = self._format_tool_output(tool_name, output)
        for line in formatted.split("\n"):
            # 截断过长的行
            display_line = line[:self._cols - 6] if len(line) > self._cols - 6 else line
            self._write(f"  {color}{prefix} {display_line}{A.RESET}\n")

        self._update_bottom()

    def log_tool_done(self, tool_name: str, duration: float):
        """显示工具执行完成"""
        if duration > 1.0:
            self._write(f"  {A.SUCCESS}✓ {tool_name} {A.DIM}({duration:.1f}s){A.RESET}\n")
        self._status_text = "⚔️  思考中..."
        self._status_color = A.AMBER
        self._update_bottom()

    def log_delegation(self, agent_names: list, clone_count: int, total_subtasks: int):
        """显示 Agent 调度信息"""
        self._write(f"\n  {A.CYAN}━━ 任务分发 ━━{A.RESET}\n")
        for name in set(agent_names):
            self._write(f"  {A.SUCCESS}  ▸ 调用 {name}...{A.RESET}\n")
        if clone_count > 0:
            self._write(f"  {A.AMBER}  ▸ 蒙多分出 {clone_count} 个分身并行执行{A.RESET}\n")
        self._write(f"  {A.DIM}  共 {total_subtasks} 个子任务{A.RESET}\n")
        self._update_bottom()

    def log_clones(self, count: int):
        """显示蒙多分身启动"""
        for i in range(1, count + 1):
            self._write(f"  {A.GOLD}  👑 分身 #{i} 已出动{A.RESET}\n")
        self._update_bottom()

    def log_response(self, text: str):
        """显示蒙多的最终回复"""
        self._write(f"\n{A.STEEL}")
        for line in text.split("\n"):
            self._write(f"  {line}\n")
        self._write(f"{A.RESET}\n")
        self._update_bottom()

    def log_error(self, error: str):
        """显示错误"""
        self._write(f"\n  {A.ERROR}✗ 错误: {error}{A.RESET}\n\n")
        self._update_bottom()

    def log_done(self, stats):
        """显示任务完成统计"""
        tok = self._format_tokens(stats.total_tokens)
        tok_in = self._format_tokens(stats.prompt_tokens)
        tok_out = self._format_tokens(stats.completion_tokens)
        elapsed = stats.elapsed_str
        llm_pct = f"{stats.llm_time / max(stats.elapsed, 0.01) * 100:.0f}%"
        tool_pct = f"{stats.tool_time / max(stats.elapsed, 0.01) * 100:.0f}%"

        sep = A.DIM + "─" * min(self._cols - 8, 60) + A.RESET
        self._write(f"\n  {sep}\n")
        self._write(
            f"  {A.SUCCESS}✓ 完成{A.RESET}"
            f"  {A.DIM}│{A.RESET}"
            f"  {A.AMBER}⏱ {elapsed}{A.RESET}"
            f"  {A.DIM}│{A.RESET}"
            f"  {A.CYAN}Tokens: {tok} ({tok_in}→{tok_out}){A.RESET}"
            f"  {A.DIM}│{A.RESET}"
            f"  {A.IRON}Turn {stats.turns}  LLM {llm_pct}  Tools {tool_pct}{A.RESET}"
        )
        if stats.tool_calls_count > 0:
            self._write(f"  {A.DIM}│{A.RESET}  {A.IRON}工具调用 {stats.tool_calls_count} 次{A.RESET}")
        self._write(f"\n  {sep}\n\n")

        self._is_running = False
        self._status_text = "等待指令..."
        self._status_color = A.IRON
        self._update_bottom()

    # ───────────────────────────────────────────
    # 格式化辅助
    # ───────────────────────────────────────────

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
        """根据工具类型格式化输出，限制行数避免刷屏"""
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

        # 默认：截断
        if len(output) > 2000:
            return output[:2000] + "\n  ... (已截断)"
        return output.strip()

    def start_task(self):
        """标记任务开始"""
        self._is_running = True
        self._status_text = "⚔️  蒙多接管..."
        self._status_color = A.GOLD
        self._update_bottom()

    def stop_task(self):
        """标记任务结束"""
        self._is_running = False
        self._status_text = "等待指令..."
        self._status_color = A.IRON
        self._update_bottom()

    def cleanup(self):
        """恢复终端状态"""
        self._restore_scroll_region()
        self._write(A.RESET)


class StatusBar:
    """向后兼容的简单状态栏（供 -q 查询模式使用）"""

    @staticmethod
    def _format_tokens(n: int) -> str:
        if n < 1000:
            return str(n)
        if n < 1000000:
            return f"{n / 1000:.1f}K"
        return f"{n / 1000000:.2f}M"

    def show_thinking(self, model: str, turn: int, stats):
        sys.stdout.write(
            f"\r{A.CLEAR_LINE}  {A.AMBER}⚔️  思考中 (Turn {turn})"
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
