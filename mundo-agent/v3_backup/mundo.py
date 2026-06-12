#!/usr/bin/env python3
import warnings
warnings.filterwarnings("ignore", message="urllib3 v2 only")
"""
MUNDO Agent v2.1.1 — THE EMPEROR
独立 AI Agent：LLM 直连 + 工具调用 + Agentic Loop + 权限审批
融合 Hermes Agent + Claude Code 精华架构
Rich 渲染所有输出，prompt_toolkit 只管输入
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
import uuid

MUNDO_HOME = Path.home() / ".hermes" / "mundo-agent"
VENV_DIR = MUNDO_HOME / "venv"

def ensure_venv():
    """确保在虚拟环境中运行，如果不在则自动激活并重启"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return True  # 已在虚拟环境中
    
    venv_python = VENV_DIR / "bin" / "python3"
    if not venv_python.exists():
        print("首次运行，正在安装虚拟环境...")
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], 
                      capture_output=True, check=True)
        # 安装依赖
        requirements = MUNDO_HOME / "requirements.txt"
        if requirements.exists():
            subprocess.run([str(venv_python), "-m", "pip", "install", "-r", str(requirements)], 
                          capture_output=True, check=True)
    
    # 在虚拟环境中重新启动自己
    os.execv(str(venv_python), [str(venv_python)] + sys.argv)

# 确保在虚拟环境中运行
ensure_venv()

sys.path.insert(0, str(Path(__file__).parent))

from core import MundoEngine
from llm import get_available_providers
from setup import PROVIDERS
from tools import registry as tool_registry, execute_tool as raw_execute_tool
from setup import (
    is_setup_done, run_setup, load_local_env,
    get_saved_provider, get_saved_model, add_provider_interactive,
)
from approval import approve_tool_call
from display import TaskConsole, console

from constants import VERSION


def safe_execute_tool(name: str, args: dict) -> str:
    if not approve_tool_call(name, args):
        return "[用户拒绝执行此操作]"
    return raw_execute_tool(name, args)


class MundoCLI:
    def __repr__(self) -> str:
        return f"MundoCLI(session={self.session_id})"

    def __init__(self, provider: str = None, model: str = None):
        self.memory = None
        self.console = TaskConsole()
        self.session_id = uuid.uuid4().hex[:12]

        if not is_setup_done() and not provider:
            console.print("\n  [gold.dim]检测到首次启动，进入设置向导...[/]\n")
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
        console.print("[error]错误: 没有可用的 API key。运行 /setup 设置。[/]")
        sys.exit(1)

    def _model_display(self) -> str:
        return self.model or PROVIDERS.get(self.provider, {}).get("model", "unknown")

    def _init_engine(self):
        self.engine = MundoEngine(provider=self.provider, model=self.model)

        import core as eng
        eng.execute_tool = safe_execute_tool

        self.engine.on_stream_start = lambda turn: self.console.stream_start(turn)
        self.engine.on_stream_text = lambda text: self.console.stream_text(text)
        self.engine.on_stream_end = lambda turn: self.console.stream_end(turn)

        self.engine.on_turn_start = lambda turn, stats: (
            self.console.log_thinking(turn),
            self.console._update_stats(stats),
        )
        self.engine.on_turn_end = lambda turn, stats, *a: self.console._update_stats(stats)

        def _on_tool_start(tool_name, tool_args, stats):
            self.console.log_tool_start(tool_name, tool_args)
            self.console._last_tool_args = tool_args  # 存储用于完成时显示
            self.console.update_live_status(stats)
        self.engine.on_tool_call = _on_tool_start

        def _on_tool_output(tool_name, output, is_error):
            self.console.log_tool_output(tool_name, output, is_error)
        self.engine.on_tool_output = _on_tool_output

        def _on_done(text, stats):
            # 不在这里显示完成栏，由 _execute_task 在显示回复后调用
            pass
        self.engine.on_task_done = _on_done

        # v27: 预算警告 + 自动压缩通知
        self.engine.on_budget_warn = lambda budget: self.console.log_budget_warning(budget)
        self.engine.on_compress = lambda *a: self.console.log_compress(*a)

        # v2.1.1: 实时 token 统计 + 缓存命中率
        self.engine.on_llm_stats = lambda prompt, completion, cached, ctx: self.console.log_llm_stats(prompt, completion, cached, ctx)

    def _init_memory(self):
        try:
            from memory import MundoMemory
            self.memory = MundoMemory()
        except Exception:
            self.memory = None

    def _check_latest_version(self) -> str:
        """从GitHub获取最新版本号"""
        try:
            import urllib.request
            url = "https://raw.githubusercontent.com/LiHongwei-cn/lihongwei-cn/main/mundo-agent/version.txt"
            req = urllib.request.Request(url, headers={"User-Agent": "mundo-agent"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.read().decode().strip()
        except Exception:
            return VERSION

    def show_banner(self):
        model_disp = self._model_display()
        self.console.init_screen(f"{self.provider}/{model_disp}", VERSION)
        console.print(f"\n[gold]  MUNDO[/] [dim]v{VERSION} · {model_disp}[/]")

        # 启动时检查版本更新
        latest = self._check_latest_version()
        if latest != VERSION:
            console.print(f"\n  [yellow]⚠ 发现新版本: v{latest}[/]")
            console.print(f"  [dim]当前版本: v{VERSION}[/]")
            console.print(f"  [dim]运行 /update 自动更新，或手动执行:[/]")
            console.print(f"  [dim]  cp ~/Desktop/lihongwei-cn/mundo-agent/*.py ~/.hermes/mundo-agent/[/]\n")

    def show_help(self):
        help_text = """
[bold gold]蒙多命令手册[/]

[gold.dim]基础[/]
  [subtext]/help[/]            此手册
  [subtext]/quit[/]            退出
  [subtext]/clear[/]           清屏
  [subtext]/status[/]          蒙多状态
  [subtext]/reset[/]           重置对话上下文

[gold.dim]模型[/]
  [subtext]/model[/]           查看当前模型
  [subtext]/models[/]          已配置模型列表
  [subtext]/switch P[/]        切换 provider
  [subtext]/providers[/]       全量模型列表
  [subtext]/add[/]             添加新 AI 模型

[gold.dim]上下文管理[/]
  [subtext]/compact[/]         压缩上下文（省 token）
  [subtext]/context[/]         上下文窗口使用率
  [subtext]/effort[/]          推理深度（low/medium/high/max）

[gold.dim]输入技巧[/]
  [dim]Enter            提交输入[/]
  [dim]Option+Enter     换行编辑[/]
  [dim]输入 / + Tab     自动补全命令[/]
  [dim]!command         直接执行 shell 命令[/]

[gold.dim]记忆（六套架构）[/]
  [subtext]/remember K V[/]    记住事实
  [subtext]/recall K[/]        回忆事实
  [subtext]/forget K[/]        遗忘事实
  [subtext]/memories[/]        列出所有记忆
  [subtext]/memory[/]          记忆系统状态
  [subtext]/search Q[/]        搜索历史对话
  [subtext]/projects[/]        列出项目上下文

[gold.dim]工具[/]
  [subtext]/tools[/]           列出所有工具
  [subtext]/setup[/]           重新运行设置向导
  [subtext]/update[/]          检查并更新到最新版本

[cyan]直接输入任何文本，蒙多开始执行任务。[/]
"""
        console.print(help_text)

    def show_status(self):
        stats = self.memory.get_stats() if self.memory else {"total_memories": 0, "total_tokens": 0, "profile_keys": 0, "projects": 0, "by_category": {}}
        s = self.engine.stats
        b = self.engine.budget
        cat = stats.get('by_category', {})
        console.print(f"""
[bold gold]═══ 蒙多帝国状态 ═══[/]
[gold.dim]Provider[/]:  {self.provider}
[gold.dim]Model[/]:     {self._model_display()}
[gold.dim]Effort[/]:    {self._effort}
[gold.dim]Tokens[/]:    {s.total_tokens} (本次会话)
[gold.dim]Budget[/]:    {b.prompt_tokens_used:,}/{b.max_prompt_tokens:,} prompt ({int(b.usage_ratio*100)}%)
[gold.dim]Turns[/]:     {b.turns_used}{'/∞' if b.max_turns == 0 else f'/{b.max_turns}'}
[gold.dim]Tools[/]:     {len(tool_registry.schemas)} 个可用
[gold.dim]Errors[/]:    {s.errors_count} 错误 · {s.retries_count} 重试

[bold gold]═══ 六套记忆 ═══[/]
[gold.dim]自动 Memory[/]:  {cat.get('fact', 0) + cat.get('preference', 0) + cat.get('constraint', 0) + cat.get('rule', 0)} 条
[gold.dim]对话搜索[/]:    {stats['conversations']} 条对话
[gold.dim]Code Memory[/]:  {cat.get('code_pattern', 0)} 条代码模式
[gold.dim]Agent Memory[/]: {cat.get('agent_result', 0)} 条执行记录
[gold.dim]Projects[/]:     {stats['projects']} 个项目
[gold.dim]总记忆[/]:       {stats['total_memories']} 条 ({stats['total_tokens']} 字符)
""")

    # ─────────────────────────────────────────
    # 上下文管理（借鉴 Claude Code）
    # ─────────────────────────────────────────

    def cmd_compact(self):
        if not self.engine.messages:
            console.print("  [dim]没有对话上下文需要压缩[/]")
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
        console.print(f"  [success]✓ 上下文已压缩[/]")
        console.print(f"  [dim]  {msg_count} 条消息 → {len(self.engine.messages)} 条消息[/]")
        console.print(f"  [dim]  {total_chars} 字符 → {new_chars} 字符[/]")

    def cmd_context(self):
        if not self.engine.messages:
            console.print("  [dim]没有对话上下文[/]")
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
            bar_color, status = "success", "健康"
        elif usage_pct < 85:
            bar_color, status = "gold.dim", "偏高，建议 /compact"
        else:
            bar_color, status = "error", "危险，强烈建议 /compact"
        console.print(f"\n  [gold]上下文窗口[/]")
        console.print(f"  [{bar_color}]{bar}[/] {usage_pct:.0f}%")
        console.print(f"  [dim]消息: {msg_count} 条 · 字符: {total_chars:,} · 估算 tokens: {est_tokens:,} / {context_limit:,}[/]")
        console.print(f"  [{bar_color}]状态: {status}[/]\n")

    def cmd_effort(self, level: str = ""):
        valid = ("low", "medium", "high", "max", "auto")
        if not level:
            console.print(f"  [gold.dim]当前推理深度: {self._effort}[/]")
            console.print(f"  [dim]可选: {', '.join(valid)}[/]")
            return
        level = level.lower()
        if level not in valid:
            console.print(f"  [error]无效级别: {level}[/]")
            return
        self._effort = level
        token_map = {"low": 1024, "medium": 2048, "high": 4096, "max": 8192, "auto": 4096}
        self.engine.max_tokens_override = token_map.get(level, 4096)
        console.print(f"  [success]✓ 推理深度: {level}[/]")

    # ─────────────────────────────────────────
    # 记忆命令
    # ─────────────────────────────────────────

    def cmd_remember(self, args):
        if len(args) < 2:
            console.print("[error]用法: /remember <key> <value>[/]")
            return
        key, value = args[0], " ".join(args[1:])
        if self.memory:
            self.memory.remember_fact(key, value)
        console.print(f"[success]✓ 已记住: {key}[/]")

    def cmd_recall(self, args):
        if not args:
            console.print("[error]用法: /recall <key>[/]")
            return
        if self.memory:
            value = self.memory.recall_key(args[0])
            if not value:
                results = self.memory.recall(args[0], max_items=3)
                console.print(f"  [cyan]{results}[/]" if results else f"[dim]蒙多不记得 '{args[0]}'[/]")
            else:
                console.print(f"  [cyan]{value}[/]")

    def cmd_forget(self, args):
        if not args:
            console.print("[error]用法: /forget <key>[/]")
            return
        if self.memory:
            self.memory.forget(args[0])
        console.print(f"[success]✓ 已遗忘: {args[0]}[/]")

    def cmd_memories(self):
        if not self.memory:
            console.print("[dim]记忆系统未初始化[/]")
            return
        facts = self.memory.all_facts(limit=30)
        if not facts:
            console.print("[dim]蒙多还没有记忆[/]")
            return
        for content, cat, imp in facts:
            stars = "★" * min(imp, 5)
            console.print(f"  [gold]{stars}[/] [[dim]{cat}[/]] {content[:80]}")

    def cmd_memory_stats(self):
        if not self.memory:
            console.print("[dim]记忆系统未初始化[/]")
            return
        stats = self.memory.get_stats()
        cat = stats.get('by_category', {})
        console.print(f"\n  [bold gold]蒙多六套记忆系统[/]")
        console.print(f"  [gold.dim]1. 自动 Memory[/]:   {cat.get('fact', 0) + cat.get('preference', 0) + cat.get('constraint', 0) + cat.get('rule', 0)} 条 (从对话自动提取)")
        console.print(f"  [gold.dim]2. 对话搜索[/]:     {stats['conversations']} 条对话 (FTS5 全文搜索)")
        console.print(f"  [gold.dim]3. Code Memory[/]:   {cat.get('code_pattern', 0)} 条代码模式")
        console.print(f"  [gold.dim]4. Agent Memory[/]:  {cat.get('agent_result', 0)} 条执行记录")
        console.print(f"  [gold.dim]5. Projects[/]:      {stats['projects']} 个项目上下文")
        console.print(f"  [gold.dim]6. 自我整理[/]:     自动去重+淘汰过时")
        console.print(f"  [gold.dim]用户画像[/]:       {stats['profile_keys']} 项")
        console.print(f"  [gold.dim]总记忆[/]:         {stats['total_memories']} 条 ({stats['total_tokens']} 字符)")
        cat = stats.get('by_category', {})
        if cat:
            console.print(f"\n  [dim]分类:[/]")
            for c, n in cat.items():
                console.print(f"    {c}: {n}")
        if self.memory:
            result = self.memory.consolidate()
            if result["duplicates_removed"] or result["expired_removed"]:
                console.print(f"\n  [info]自我整理: 去重 {result['duplicates_removed']} 条，淘汰 {result['expired_removed']} 条[/]")
        console.print(f"\n  [dim]注入预算: {3000} 字符/次 | 项目隔离: 按工作目录[/]\n")

    def cmd_search(self, args):
        if not self.memory:
            console.print("[dim]记忆系统未初始化[/]")
            return
        if not args:
            console.print("[error]用法: /search <关键词>[/]")
            return
        query = " ".join(args)
        results = self.memory.search_conversations(query, limit=5)
        if not results:
            console.print(f"  [dim]未找到与 '{query}' 相关的对话[/]")
            return
        console.print(f"\n  [gold]搜索结果: '{query}'[/]")
        for r in results:
            console.print(f"  [gold.dim]{r['date']}[/] [{r['messages']}条] {r['title'][:60]}")

    def cmd_projects(self):
        if not self.memory:
            console.print("[dim]记忆系统未初始化[/]")
            return
        projects = self.memory.get_all_projects()
        if not projects:
            console.print("  [dim]还没有项目上下文[/]")
            return
        console.print(f"\n  [gold]项目上下文[/]")
        for p in projects:
            console.print(f"  [gold.dim]{p['path']}[/]")
            if p['name']:
                console.print(f"    名称: {p['name']}")
            if p['tech']:
                console.print(f"    技术栈: {p['tech']}")
            console.print(f"    最近: {p['seen']}")

    def cmd_update(self):
        """自动更新蒙多到最新版本"""
        import shutil
        console.print("\n  [gold]检查更新...[/]")

        latest = self._check_latest_version()
        if latest == VERSION:
            console.print(f"  [success]✓ 已是最新版本 v{VERSION}[/]\n")
            return

        console.print(f"  [yellow]发现新版本: v{latest}[/]")
        console.print(f"  [dim]当前版本: v{VERSION}[/]\n")

        # 检查仓库目录是否存在
        repo_dir = Path.home() / "Desktop" / "lihongwei-cn" / "mundo-agent"
        if not repo_dir.exists():
            console.print(f"  [error]✗ 仓库目录不存在: {repo_dir}[/]")
            console.print(f"  [dim]请手动克隆仓库后重试[/]\n")
            return

        console.print(f"  [gold]正在从仓库同步...[/]")

        # 需要同步的文件列表
        sync_files = [
            "mundo.py", "constants.py", "core.py", "llm.py",
            "delegation.py", "hermes_integration.py", "claude_integration.py",
            "codex_integration.py", "tools.py", "display.py", "setup.py",
            "approval.py", "memory.py", "hooks.py", "cache.py",
            "context_discipline.py", "context_mapper.py", "dispatch.py",
            "events.py", "failover.py", "cloud_sync.py", "engine.py",
            "agents.py", "version.txt"
        ]

        synced = 0
        for fname in sync_files:
            src = repo_dir / fname
            dst = MUNDO_HOME / fname
            if src.exists():
                try:
                    shutil.copy2(str(src), str(dst))
                    synced += 1
                except Exception as e:
                    console.print(f"  [error]✗ 同步失败 {fname}: {e}[/]")

        console.print(f"\n  [success]✓ 同步完成: {synced}/{len(sync_files)} 个文件[/]")
        console.print(f"  [gold]请重启蒙多以使用新版本 v{latest}[/]\n")

    # ─────────────────────────────────────────
    # 模型命令
    # ─────────────────────────────────────────

    def cmd_model(self):
        console.print(f"  [gold.dim]Provider[/]: {self.provider}")
        console.print(f"  [gold.dim]Model[/]:    {self._model_display()}")
        console.print(f"  [gold.dim]Effort[/]:   {self._effort}")

    def cmd_switch(self, args):
        if not args:
            console.print("[error]用法: /switch <provider>[/]")
            return
        prov = args[0]
        if prov not in PROVIDERS:
            console.print(f"[error]未知 provider: {prov}[/]")
            return
        available = get_available_providers()
        if prov not in available:
            console.print(f"[error]{prov} 没有 API key. 用 /add 添加。[/]")
            return
        self.provider = prov
        self.model = None
        self._init_engine()
        console.print(f"[success]✓ 已切换到 {prov} ({PROVIDERS[prov]['model']})[/]")

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
        console.print(f"\n[gold]全量 AI 模型 ({len(PROVIDERS)} 个)[/]")
        for group_name, items in groups.items():
            console.print(f"\n  [gold.dim]━━ {group_name} ━━[/]")
            for key, p in items:
                status = "✓" if key in available else "✗"
                color = "success" if key in available else "dim"
                console.print(f"    [{color}]{status} {key:16} {p['model']:35} [dim]{p['desc']}[/][/]")
        console.print()

    def cmd_add(self):
        name, model = add_provider_interactive()
        if name:
            self.provider = name
            self.model = model
            self._init_engine()

    def cmd_models(self):
        from setup import load_local_env
        env = load_local_env()
        console.print(f"\n  [gold]已配置的模型[/]\n")
        configured = []
        for key, cfg in PROVIDERS.items():
            if env.get(cfg["env_key"]):
                current = " ← 当前" if key == self.provider else ""
                console.print(f"  [success]✓ {cfg['label']:20}[/] {cfg['model']:35}[gold.dim]{current}[/]")
                configured.append(key)
        if not configured:
            console.print(f"  [dim]未配置任何模型。运行 /setup 设置。[/]")
        console.print()

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
            "/search": lambda: self.cmd_search(args),
            "/projects": lambda: self.cmd_projects(),
            "/update": lambda: self.cmd_update(),
        }
        if cmd in handlers:
            handlers[cmd]()
            return True
        console.print(f"[error]未知命令: {cmd}. 输入 /help 查看帮助。[/]")
        return True

    def _show_tools(self):
        console.print(f"\n[bold gold]蒙多的武器库[/]\n")
        for t in tool_registry.schemas:
            fn = t["function"]
            console.print(f"  [gold.dim]{fn['name']:20}[/] {fn['description'][:60]}")
        console.print()

    def _rerun_setup(self):
        from setup import MUNDO_SETUP_FLAG
        if MUNDO_SETUP_FLAG.exists():
            MUNDO_SETUP_FLAG.unlink()
        provider, model = run_setup()
        self.provider = provider
        self.model = model
        self._init_engine()
        console.print("[success]✓ 设置已更新[/]")

    def _reset(self):
        self.engine.reset()
        console.print("[success]✓ 对话上下文已重置[/]")

    def _exit(self):
        self.console.cleanup()
        console.print(f"\n  [gold]蒙多退朝。下次再战。[/]")
        sys.exit(0)

    def run(self):
        """主循环 — 不使用 patch_stdout，Rich 处理所有输出"""
        while True:
            try:
                line = self.console.read_input().strip()
                if not line:
                    continue
                if self.process_command(line):
                    continue
                self._execute_task(line)
            except KeyboardInterrupt:
                console.print(f"\n[dim]  (Ctrl+C) 输入 /quit 退出[/]")
            except EOFError:
                self._exit()

    def _execute_task(self, line: str):
        project = os.getcwd()
        extra = self.memory.get_context_budget(line, project=project) if self.memory else ""

        self.console.log_task_accepted(line)
        self.console.start_task()

        full_text = TaskConsole.expand_paste_refs(line)
        response = ""
        try:
            response = self.engine.run(full_text, extra_context=extra)
            if response and response.strip() and not self.console._was_streamed:
                self.console.log_response(response)
            self.console._was_streamed = False
        except Exception as e:
            self.console.log_error(str(e))
        finally:
            self.console.stop_task()
            self.console.log_done(self.engine.stats)

            if self.memory:
                try:
                    # 先保存对话（含完整响应）
                    self.memory.save_conversation(
                        conv_id=self.session_id,
                        title=line[:100],
                        summary=response[:200] if response else "",
                        messages=self.engine.messages,
                        project=project
                    )
                    # 再提取记忆
                    self.memory.auto_extract(line, response, project=project)
                    # 更新会话摘要
                    self.memory.generate_session_summary(self.session_id, self.engine.messages)
                except Exception as e:
                    print(f"[memory] 记忆操作失败: {e}", file=sys.stderr)


def main():
    os.system("clear")
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
