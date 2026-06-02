#!/usr/bin/env python3
"""
MUNDO Agent v26.0 — THE EMPEROR
独立 AI Agent：LLM 直连 + 工具调用 + Agentic Loop + 权限审批
融合 Hermes Agent + Claude Code 精华架构
"""

import os
import sys
import queue
from pathlib import Path
from typing import Optional
import uuid

sys.path.insert(0, str(Path(__file__).parent))

from core import MundoEngine, TaskStats
from llm import get_available_providers
from setup import PROVIDERS
from tools import registry as tool_registry, execute_tool as raw_execute_tool
from setup import (
    is_setup_done, run_setup, load_local_env,
    get_saved_provider, get_saved_model, add_provider_interactive, MUNDO_ENV,
)
from approval import approve_tool_call
from delegation import TaskDelegator, AgentManager
from display import TaskConsole, A

MUNDO_HOME = Path.home() / ".hermes" / "mundo-agent"
VERSION = "26.0.0"


def safe_execute_tool(name: str, args: dict) -> str:
    if not approve_tool_call(name, args):
        return "[用户拒绝执行此操作]"
    return raw_execute_tool(name, args)


class MundoCLI:
    def __init__(self, provider: str = None, model: str = None):
        self.memory = None
        self.console = TaskConsole()
        self._pending_inputs = queue.Queue()
        self._engine_busy = False
        self.session_id = uuid.uuid4().hex[:12]

        if not is_setup_done() and not provider:
            print(f"\n  {A.GOLD_DIM}检测到首次启动，进入设置向导...{A.RESET}\n")
            provider, model = run_setup()

        env = load_local_env()
        for k, v in env.items():
            os.environ.setdefault(k, v)

        self.provider = provider or get_saved_provider() or self._detect_provider()
        self.model = model or get_saved_model()
        self.engine: Optional[MundoEngine] = None
        self._effort = "auto"
        self._init_engine()
        self._init_memory()

    def _detect_provider(self) -> str:
        available = get_available_providers()
        for p in ("xiaomi", "deepseek", "openrouter"):
            if p in available:
                return p
        if available:
            return available[0]
        print(f"{A.ERROR}错误: 没有可用的 API key。运行 /setup 设置。{A.RESET}")
        sys.exit(1)

    def _model_display(self) -> str:
        return self.model or PROVIDERS.get(self.provider, {}).get("model", "unknown")

    def _init_engine(self):
        self.engine = MundoEngine(provider=self.provider, model=self.model)
        self.agent_mgr = AgentManager()
        self.delegator = TaskDelegator(self.engine.client, self.agent_mgr)

        # 注入安全工具执行
        import core as eng
        eng.execute_tool = safe_execute_tool
        self.engine.delegator = self.delegator

        # 委托回调
        def _on_subtask_progress(subtask_id, task_desc, agent_name, phase, preview):
            pass  # 简化版不显示子任务进度
        self.delegator.on_subtask_progress = _on_subtask_progress

        # 流式输出回调
        self.engine.on_stream_start = lambda turn: self.console.stream_start(turn)
        self.engine.on_stream_text = lambda text: self.console.stream_text(text)
        self.engine.on_stream_end = lambda turn: self.console.stream_end(turn)

        # stats 同步
        self.engine.on_turn_start = lambda turn, stats: (
            self.console.log_thinking(turn),
            self.console._update_stats(stats),
        )
        self.engine.on_turn_end = lambda turn, stats, *a: self.console._update_stats(stats)

        # 工具回调
        def _on_tool_start(tool_name, tool_args, stats):
            self.console.log_tool_start(tool_name, tool_args)
            self.console.update_live_status(stats)
        self.engine.on_tool_call = _on_tool_start

        def _on_tool_output(tool_name, output, is_error):
            self.console.log_tool_output(tool_name, output, is_error)
        self.engine.on_tool_output = _on_tool_output

        def _on_done(text, stats):
            self.console.log_done(stats)
        self.engine.on_task_done = _on_done

    def _init_memory(self):
        try:
            from memory import MundoMemory
            self.memory = MundoMemory()
        except Exception:
            self.memory = None

    def show_banner(self):
        banner = f"""
  {A.GOLD}           M  U  N  D  O{A.RESET}
  {A.DIM}            THE EMPEROR{A.RESET}
  {A.DIM}            v{VERSION}{A.RESET}"""
        print(banner)
        model_disp = f"{self.provider}/{self._model_display()}"
        self.console.init_screen(model_disp, VERSION)
        agents = self.agent_mgr.list_available()
        if agents:
            names = ", ".join(a["name"] for a in agents)
            print(f"\n  {A.DIM}Agents: {names}{A.RESET}")
        print()

    def show_help(self):
        print(f"""
{A.GOLD}{A.BOLD}蒙多命令手册{A.RESET}

{A.GOLD_DIM}基础{A.RESET}
  {A.SUBTEXT}/help{A.RESET}            此手册
  {A.SUBTEXT}/quit{A.RESET}            退出
  {A.SUBTEXT}/clear{A.RESET}           清屏
  {A.SUBTEXT}/status{A.RESET}          蒙多状态
  {A.SUBTEXT}/reset{A.RESET}           重置对话上下文

{A.GOLD_DIM}模型{A.RESET}
  {A.SUBTEXT}/model{A.RESET}           查看当前模型
  {A.SUBTEXT}/models{A.RESET}          已配置模型列表
  {A.SUBTEXT}/switch P{A.RESET}        切换 provider
  {A.SUBTEXT}/providers{A.RESET}       全量模型列表
  {A.SUBTEXT}/add{A.RESET}             添加新 AI 模型

{A.GOLD_DIM}上下文管理{A.RESET}
  {A.SUBTEXT}/compact{A.RESET}         压缩上下文（省 token）
  {A.SUBTEXT}/context{A.RESET}         上下文窗口使用率
  {A.SUBTEXT}/effort{A.RESET}          推理深度（low/medium/high/max）

{A.GOLD_DIM}记忆{A.RESET}
  {A.SUBTEXT}/remember K V{A.RESET}    记住事实
  {A.SUBTEXT}/recall K{A.RESET}        回忆事实
  {A.SUBTEXT}/forget K{A.RESET}        遗忘事实
  {A.SUBTEXT}/memories{A.RESET}        列出所有记忆
  {A.SUBTEXT}/memory{A.RESET}          记忆系统状态

{A.GOLD_DIM}工具{A.RESET}
  {A.SUBTEXT}/tools{A.RESET}           列出所有工具
  {A.SUBTEXT}/setup{A.RESET}           重新运行设置向导
  {A.SUBTEXT}!command{A.RESET}          直接执行 shell 命令

{A.CYAN}直接输入任何文本，蒙多开始执行任务。{A.RESET}
""")

    def show_status(self):
        stats = self.memory.get_stats() if self.memory else {"total_memories": 0, "total_tokens": 0, "profile_keys": 0}
        s = self.engine.stats
        print(f"""
{A.GOLD}{A.BOLD}═══ 蒙多帝国状态 ═══{A.RESET}
{A.GOLD_DIM}Provider{A.RESET}:  {self.provider}
{A.GOLD_DIM}Model{A.RESET}:     {self._model_display()}
{A.GOLD_DIM}Effort{A.RESET}:    {self._effort}
{A.GOLD_DIM}Memory{A.RESET}:    {stats['total_memories']} 条记忆 ({stats['total_tokens']} 字符)
{A.GOLD_DIM}Profile{A.RESET}:   {stats['profile_keys']} 项画像
{A.GOLD_DIM}Tokens{A.RESET}:    {s.total_tokens} (本次会话)
{A.GOLD_DIM}Tools{A.RESET}:     {len(tool_registry.schemas)} 个可用
""")

    # ─────────────────────────────────────────
    # 上下文管理命令（借鉴 Claude Code）
    # ─────────────────────────────────────────

    def cmd_compact(self):
        if not self.engine.messages:
            print(f"  {A.DIM}没有对话上下文需要压缩{A.RESET}")
            return
        msg_count = len(self.engine.messages)
        total_chars = sum(len(m.get("content") or "") for m in self.engine.messages)
        system_msg = self.engine.messages[0] if self.engine.messages[0]["role"] == "system" else None
        recent = self.engine.messages[-8:] if len(self.engine.messages) > 8 else self.engine.messages[1:]
        summary_parts = []
        for msg in self.engine.messages[1:-8] if len(self.engine.messages) > 9 else []:
            content = (msg.get("content") or "")[:100]
            if content:
                summary_parts.append(content)
        summary = " | ".join(summary_parts[-10:]) if summary_parts else "(早期对话已省略)"
        new_messages = []
        if system_msg:
            new_messages.append(system_msg)
        new_messages.append({"role": "system", "content": f"[上下文压缩摘要] {summary[:500]}"})
        new_messages.extend(recent)
        self.engine.messages = new_messages
        new_chars = sum(len(m.get("content") or "") for m in self.engine.messages)
        print(f"  {A.SUCCESS}✓ 上下文已压缩{A.RESET}")
        print(f"  {A.DIM}  {msg_count} 条消息 → {len(self.engine.messages)} 条消息{A.RESET}")
        print(f"  {A.DIM}  {total_chars} 字符 → {new_chars} 字符{A.RESET}")

    def cmd_context(self):
        if not self.engine.messages:
            print(f"  {A.DIM}没有对话上下文{A.RESET}")
            return
        msg_count = len(self.engine.messages)
        total_chars = sum(len(m.get("content") or "") for m in self.engine.messages)
        est_tokens = total_chars // 3
        context_limit = 128000
        usage_pct = (est_tokens / context_limit) * 100
        bar_width = 40
        filled = int(bar_width * usage_pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        if usage_pct < 70:
            bar_color, status = A.SUCCESS, "健康"
        elif usage_pct < 85:
            bar_color, status = A.GOLD_DIM, "偏高，建议 /compact"
        else:
            bar_color, status = A.ERROR, "危险，强烈建议 /compact"
        print(f"\n  {A.GOLD}上下文窗口{A.RESET}")
        print(f"  {bar_color}{bar}{A.RESET} {usage_pct:.0f}%")
        print(f"  {A.DIM}消息: {msg_count} 条 · 字符: {total_chars:,} · 估算 tokens: {est_tokens:,} / {context_limit:,}{A.RESET}")
        print(f"  {bar_color}状态: {status}{A.RESET}\n")

    def cmd_effort(self, level: str = ""):
        valid = ("low", "medium", "high", "max", "auto")
        if not level:
            print(f"  {A.GOLD_DIM}当前推理深度: {self._effort}{A.RESET}")
            print(f"  {A.DIM}可选: {', '.join(valid)}{A.RESET}")
            return
        level = level.lower()
        if level not in valid:
            print(f"  {A.ERROR}无效级别: {level}{A.RESET}")
            return
        self._effort = level
        token_map = {"low": 1024, "medium": 2048, "high": 4096, "max": 8192, "auto": 4096}
        self.engine.max_tokens_override = token_map.get(level, 4096)
        print(f"  {A.SUCCESS}✓ 推理深度: {level}{A.RESET}")

    # ─────────────────────────────────────────
    # 记忆命令
    # ─────────────────────────────────────────

    def cmd_remember(self, args):
        if len(args) < 2:
            print(f"{A.ERROR}用法: /remember <key> <value>{A.RESET}")
            return
        key, value = args[0], " ".join(args[1:])
        if self.memory:
            self.memory.remember_fact(key, value)
        print(f"{A.SUCCESS}✓ 已记住: {key}{A.RESET}")

    def cmd_recall(self, args):
        if not args:
            print(f"{A.ERROR}用法: /recall <key>{A.RESET}")
            return
        if self.memory:
            value = self.memory.recall_key(args[0])
            if not value:
                results = self.memory.recall(args[0], max_items=3)
                print(f"  {A.CYAN}{results}{A.RESET}" if results else f"{A.DIM}蒙多不记得 '{args[0]}'{A.RESET}")
            else:
                print(f"  {A.CYAN}{value}{A.RESET}")

    def cmd_forget(self, args):
        if not args:
            print(f"{A.ERROR}用法: /forget <key>{A.RESET}")
            return
        if self.memory:
            self.memory.forget(args[0])
        print(f"{A.SUCCESS}✓ 已遗忘: {args[0]}{A.RESET}")

    def cmd_memories(self):
        if not self.memory:
            print(f"{A.DIM}记忆系统未初始化{A.RESET}")
            return
        facts = self.memory.all_facts(limit=30)
        if not facts:
            print(f"{A.DIM}蒙多还没有记忆{A.RESET}")
            return
        for content, cat, imp in facts:
            stars = "★" * min(imp, 5)
            print(f"  {A.GOLD}{stars}{A.RESET} [{A.DIM}{cat}{A.RESET}] {content[:80]}")

    def cmd_memory_stats(self):
        if not self.memory:
            print(f"{A.DIM}记忆系统未初始化{A.RESET}")
            return
        stats = self.memory.get_stats()
        print(f"\n  {A.GOLD}{A.BOLD}蒙多记忆系统{A.RESET}")
        print(f"  {A.GOLD_DIM}总记忆{A.RESET}:     {stats['total_memories']} 条")
        print(f"  {A.GOLD_DIM}总字符{A.RESET}:     {stats['total_tokens']}")
        print(f"  {A.GOLD_DIM}对话记录{A.RESET}:   {stats['conversations']} 条")
        print(f"  {A.GOLD_DIM}用户画像{A.RESET}:   {stats['profile_keys']} 项")
        cat = stats.get('by_category', {})
        if cat:
            print(f"\n  {A.DIM}分类:{A.RESET}")
            for c, n in cat.items():
                print(f"    {c}: {n}")
        if self.memory:
            self.memory.consolidate()
        print(f"\n  {A.DIM}双层架构: 事实(持久) + 摘要(近期) | 注入预算: {2000} 字符/次{A.RESET}\n")

    # ─────────────────────────────────────────
    # 模型命令
    # ─────────────────────────────────────────

    def cmd_model(self):
        print(f"  {A.GOLD_DIM}Provider{A.RESET}: {self.provider}")
        print(f"  {A.GOLD_DIM}Model{A.RESET}:    {self._model_display()}")
        print(f"  {A.GOLD_DIM}Effort{A.RESET}:   {self._effort}")

    def cmd_switch(self, args):
        if not args:
            print(f"{A.ERROR}用法: /switch <provider>{A.RESET}")
            return
        prov = args[0]
        if prov not in PROVIDERS:
            print(f"{A.ERROR}未知 provider: {prov}{A.RESET}")
            return
        available = get_available_providers()
        if prov not in available:
            print(f"{A.ERROR}{prov} 没有 API key. 用 /add 添加。{A.RESET}")
            return
        self.provider = prov
        self.model = None
        self._init_engine()
        print(f"{A.SUCCESS}✓ 已切换到 {prov} ({PROVIDERS[prov]['model']}){A.RESET}")

    def cmd_providers(self):
        available = get_available_providers()
        from setup import DISPLAY_ORDER
        groups = {}
        for key in DISPLAY_ORDER:
            p = PROVIDERS[key]
            g = p["group"]
            if g not in groups:
                groups[g] = []
            groups[g].append((key, p))
        print(f"\n{A.GOLD}全量 AI 模型 ({len(PROVIDERS)} 个){A.RESET}")
        for group_name, items in groups.items():
            print(f"\n  {A.GOLD_DIM}━━ {group_name} ━━{A.RESET}")
            for key, p in items:
                status = "✓" if key in available else "✗"
                color = A.SUCCESS if key in available else A.DIM
                print(f"    {color}{status} {key:16} {p['model']:35} {A.DIM}{p['desc']}{A.RESET}")
        print()

    def cmd_add(self):
        name, model = add_provider_interactive()
        if name:
            self.provider = name
            self.model = model
            self._init_engine()

    def cmd_models(self):
        from setup import load_local_env
        env = load_local_env()
        print(f"\n  {A.GOLD}已配置的模型{A.RESET}\n")
        configured = []
        for key, cfg in PROVIDERS.items():
            if env.get(cfg["env_key"]):
                current = " ← 当前" if key == self.provider else ""
                print(f"  {A.SUCCESS}✓ {cfg['label']:20}{A.RESET} {cfg['model']:35}{A.GOLD_DIM}{current}{A.RESET}")
                configured.append(key)
        if not configured:
            print(f"  {A.DIM}未配置任何模型。运行 /setup 设置。{A.RESET}")
        print()

    # ─────────────────────────────────────────
    # 命令分发
    # ─────────────────────────────────────────

    def process_command(self, line: str) -> bool:
        if line.startswith("!"):
            os.system(line[1:])
            return True
        if not line.startswith("/"):
            return False

        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()
        args = (parts[1] if len(parts) > 1 else "").split()
        raw_arg = parts[1] if len(parts) > 1 else ""

        handlers = {
            "/help": lambda: self.show_help(),
            "/quit": lambda: self._exit(),
            "/exit": lambda: self._exit(),
            "/q": lambda: self._exit(),
            "/clear": lambda: os.system("clear"),
            "/status": lambda: self.show_status(),
            "/reset": lambda: self._reset(),
            "/tools": lambda: self._show_tools(),
            "/model": lambda: self.cmd_model(),
            "/switch": lambda: self.cmd_switch(args),
            "/providers": lambda: self.cmd_providers(),
            "/add": lambda: self.cmd_add(),
            "/setup": lambda: self._rerun_setup(),
            "/remember": lambda: self.cmd_remember(args),
            "/recall": lambda: self.cmd_recall(args),
            "/forget": lambda: self.cmd_forget(args),
            "/memories": lambda: self.cmd_memories(),
            "/memory": lambda: self.cmd_memory_stats(),
            "/compact": lambda: self.cmd_compact(),
            "/context": lambda: self.cmd_context(),
            "/effort": lambda: self.cmd_effort(args[0] if args else ""),
            "/models": lambda: self.cmd_models(),
        }
        if cmd in handlers:
            handlers[cmd]()
            return True
        print(f"{A.ERROR}未知命令: {cmd}. 输入 /help 查看帮助。{A.RESET}")
        return True

    def _show_tools(self):
        print(f"\n{A.GOLD}{A.BOLD}蒙多的武器库{A.RESET}\n")
        for t in tool_registry.schemas:
            fn = t["function"]
            print(f"  {A.GOLD_DIM}{fn['name']:20}{A.RESET} {fn['description'][:60]}")
        print()

    def _rerun_setup(self):
        from setup import MUNDO_SETUP_FLAG
        if MUNDO_SETUP_FLAG.exists():
            MUNDO_SETUP_FLAG.unlink()
        provider, model = run_setup()
        self.provider = provider
        self.model = model
        self._init_engine()
        print(f"{A.SUCCESS}✓ 设置已更新{A.RESET}")

    def _reset(self):
        self.engine.reset()
        print(f"{A.SUCCESS}✓ 对话上下文已重置{A.RESET}")

    def _exit(self):
        self.console.cleanup()
        print(f"\n  {A.GOLD}蒙多退朝。下次再战。{A.RESET}")
        sys.exit(0)

    def run(self):
        from prompt_toolkit.patch_stdout import patch_stdout
        with patch_stdout():
            while True:
                try:
                    while not self._pending_inputs.empty():
                        self._pending_inputs.get_nowait()
                    line = self.console.read_input().strip()
                    if not line:
                        continue
                    if self.process_command(line):
                        continue
                    self._execute_task(line)
                except KeyboardInterrupt:
                    print(f"\n{A.DIM}  (Ctrl+C) 输入 /quit 退出{A.RESET}")
                except EOFError:
                    self._exit()

    def _execute_task(self, line: str):
        extra = self.memory.get_context_budget(line) if self.memory else ""

        if self.engine.messages and self.memory:
            try:
                self.memory.compress_conversation(self.engine.messages, self.session_id)
            except Exception:
                pass

        self.console.log_task_accepted(line)
        self._engine_busy = True
        self.console.start_task()

        try:
            response = self.engine.run(line, extra_context=extra)
            if not self.console._was_streamed:
                self.console.log_response(response)
            else:
                self.console._was_streamed = False
        except Exception as e:
            self.console.log_error(str(e))
        finally:
            self._engine_busy = False
            self.console.stop_task()

            if self.memory:
                try:
                    self.memory.generate_session_summary(self.session_id, self.engine.messages)
                except Exception:
                    pass


def main():
    import argparse
    parser = argparse.ArgumentParser(description="MUNDO Agent — THE EMPEROR")
    parser.add_argument("-q", "--query", help="单次查询模式")
    parser.add_argument("-p", "--provider", help="LLM provider")
    parser.add_argument("-m", "--model", help="模型名称")
    parser.add_argument("-v", "--version", action="store_true")
    parser.add_argument("--no-banner", action="store_true")
    args = parser.parse_args()

    if args.version:
        print(f"MUNDO Agent v{VERSION}")
        return

    cli = MundoCLI(provider=args.provider, model=args.model)

    if args.query:
        response = cli.engine.run(args.query)
        if not cli.console._was_streamed:
            print(response)
        else:
            cli.console._was_streamed = False
        return

    if not args.no_banner:
        cli.show_banner()
    cli.run()


if __name__ == "__main__":
    main()
