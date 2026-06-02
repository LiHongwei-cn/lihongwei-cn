#!/usr/bin/env python3
"""
MUNDO Agent v24.3 — THE EMPEROR
独立 AI Agent：LLM 直连 + 工具调用 + Agentic Loop + 权限审批 + 云仓库同步
核心架构借鉴 Claude Code / Hermes Agent / Codex
"""

import os
import sys
import queue
from pathlib import Path
from typing import Optional
import uuid

sys.path.insert(0, str(Path(__file__).parent))

from engine import MundoEngine, TaskStats
from llm import get_available_providers
from setup import PROVIDERS
from tools import TOOL_SCHEMAS, execute_tool as raw_execute_tool
from setup import (
    is_setup_done, run_setup, load_local_env, save_local_env,
    get_saved_provider, get_saved_model, add_provider_interactive,
    MUNDO_ENV,
)
from approval import approve_tool_call
from cloud_sync import auto_sync_new_skills, process_upload_queue, daily_quality_audit
from agents import AgentManager
from delegation import TaskDelegator
from display import TaskConsole, StatusBar

MUNDO_HOME = Path.home() / ".hermes" / "mundo-agent"
MUNDO_MEMORY_DB = MUNDO_HOME / "memory.db"
VERSION = "24.4.0"


# ═══════════════════════════════════════════════
# Colors
# ═══════════════════════════════════════════════

class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CLEAR_LINE = "\033[2K\r"
    GOLD = "\033[38;5;178m"
    CRIMSON = "\033[38;5;131m"
    IRON = "\033[38;5;243m"
    STEEL = "\033[38;5;248m"
    AMBER = "\033[38;5;136m"
    SUCCESS = "\033[38;5;65m"
    ERROR = "\033[38;5;131m"
    TOOL = "\033[38;5;245m"
    CYAN = "\033[38;5;87m"


# ═══════════════════════════════════════════════
# Memory
# ═══════════════════════════════════════════════

from memory import MundoMemoryV2 as Memory


# ═══════════════════════════════════════════════
# ═══════════════════════════════════════════════
# 像素风 Banner（蒙多皇帝形象）
# ═══════════════════════════════════════════════

_BANNER_ART = r"""
  {g}           M  U  N  D  O{r}
  {d}            THE EMPEROR{r}
  {d}            v{v}{r}
""".strip()

BANNER = _BANNER_ART.format(
    g=C.GOLD, d=C.DIM, r=C.RESET, v=VERSION
)


def safe_execute_tool(name: str, args: dict) -> str:
    if not approve_tool_call(name, args):
        return "[用户拒绝执行此操作]"
    return raw_execute_tool(name, args)


class MundoCLI:
    def __init__(self, provider: str = None, model: str = None):
        self.memory = Memory()
        self.console = TaskConsole()
        self._pending_inputs = queue.Queue()
        self._input_thread = None
        self._engine_busy = False
        self.session_id = uuid.uuid4().hex[:12]

        # 首次设置检查
        if not is_setup_done() and not provider:
            print(f"\n  {C.AMBER}检测到首次启动，进入设置向导...{C.RESET}\n")
            provider, model = run_setup()

        # 加载本地 .env
        env = load_local_env()
        for k, v in env.items():
            os.environ.setdefault(k, v)

        self.provider = provider or get_saved_provider() or self._detect_provider()
        self.model = model or get_saved_model()
        self.engine: Optional[MundoEngine] = None
        self._effort = "auto"
        self._init_engine()

        # 首次启动：导入已有 Agent 记忆
        self._import_memory_if_first_run()

        # 启动时自动同步新 Skill
        self._auto_sync_background()

        # 启动时检查更新
        self._check_update_background()

    def _detect_provider(self) -> str:
        available = get_available_providers()
        for p in ("xiaomi", "deepseek", "openrouter"):
            if p in available:
                return p
        if available:
            return available[0]
        print(f"{C.ERROR}错误: 没有可用的 API key。运行 /setup 重新设置。{C.RESET}")
        sys.exit(1)

    def _model_display(self) -> str:
        return self.model or PROVIDERS.get(self.provider, {}).get("model", "unknown")

    def _init_engine(self):
        self.engine = MundoEngine(provider=self.provider, model=self.model)
        model_disp = f"{self.provider}/{self._model_display()}"

        # 检测本地 Agent
        self.agent_mgr = AgentManager()
        self.delegator = TaskDelegator(self.engine.client, self.agent_mgr)

        # 注入安全工具执行和分发器
        import engine as eng
        eng.execute_tool = safe_execute_tool
        self.engine.delegator = self.delegator

        # Agent 调度回调 → console
        def _on_delegate(agent_names, clone_count, subtasks):
            self.console.log_delegation(agent_names, clone_count, len(subtasks))

        def _on_clones(clone_count):
            self.console.log_clones(clone_count)

        self.engine.on_delegate = _on_delegate
        self.engine.on_clones = _on_clones
        self.engine._memory_ref = self.memory
        self.engine._session_id = self.session_id

        self.engine.on_turn_start = lambda turn, stats: self.console.log_thinking(turn)

        # 工具调用开始 → console 显示工具名和参数
        def _on_tool_start(tool_name, tool_args, stats, phase, result_preview=None, duration=0):
            if phase == "start":
                self.console.log_tool_start(tool_name, tool_args)
            elif phase == "done":
                self.console.log_tool_done(tool_name, duration)

        self.engine.on_tool_call = _on_tool_start

        # 工具输出 → console 实时显示执行结果
        def _on_tool_output(tool_name, output, is_error):
            self.console.log_tool_output(tool_name, output, is_error)

        self.engine.on_tool_output = _on_tool_output

        self.engine.on_turn_end = lambda *a: None

        def _on_done(text, stats):
            if "失败" in text or "错误" in text:
                self.console.log_error(text[:100])
            self.console.log_done(stats)

        self.engine.on_task_done = _on_done

    def _auto_sync_background(self):
        try:
            from pathlib import Path as P
            skills_dir = P.home() / ".hermes" / "skills"
            if not skills_dir.exists() or not any(skills_dir.iterdir()):
                print(f"  {C.DIM}☁ 首次部署：从云仓库拉取 Skills 和全局规范...{C.RESET}")
                from cloud_sync import initial_deploy
                result = initial_deploy()
                s = result.get("skills", {})
                p = result.get("specs", {})
                pulled = s.get("pulled", 0) + p.get("pulled", 0)
                if pulled > 0:
                    print(f"  {C.SUCCESS}  ✓ 已部署 {pulled} 个文件到本地{C.RESET}")
            else:
                count = auto_sync_new_skills()
                if count > 0:
                    print(f"  {C.DIM}☁ 已同步 {count} 个新 Skill 到云仓库{C.RESET}")
        except Exception:
            pass

    def _import_memory_if_first_run(self):
        """首次启动时自动导入已有 Agent 的记忆"""
        import_flag = MUNDO_HOME / ".memory_imported"
        if import_flag.exists():
            return

        try:
            from memory_import import import_existing_memory
            stats = import_existing_memory(self.memory)

            if stats["facts_imported"] > 0 or stats["keys_imported"] > 0:
                print(f"\n  {C.GOLD}━━ 记忆导入 ━━{C.RESET}")
                print(f"  {C.SUCCESS}✓ 已从 {stats['source']} 导入：{C.RESET}")
                if stats["keys_imported"] > 0:
                    print(f"    {C.DIM}API Key: {stats['keys_imported']} 个{C.RESET}")
                if stats["facts_imported"] > 0:
                    print(f"    {C.DIM}记忆/偏好: {stats['facts_imported']} 条{C.RESET}")
                print(f"  {C.DIM}蒙多已继承你的偏好，直接开始使用。{C.RESET}\n")

            # 标记导入完成（无论是否有数据都标记，避免重复扫描）
            import_flag.write_text("done")
        except Exception:
            pass

    def show_banner(self):
        print(BANNER)
        model_disp = f"{self.provider}/{self._model_display()}"
        self.console.init_screen(model_disp, VERSION)
        agents = self.agent_mgr.list_available()
        if agents:
            names = ", ".join(a["name"] for a in agents)
            print(f"\n  {C.DIM}Agents: {names}{C.RESET}")
        print()

    def show_help(self):
        print(f"""
{C.GOLD}{C.BOLD}蒙多命令手册{C.RESET}

{C.AMBER}基础{C.RESET}
  {C.STEEL}/help{C.RESET}            此手册
  {C.STEEL}/quit{C.RESET}            退出
  {C.STEEL}/clear{C.RESET}           清屏
  {C.STEEL}/status{C.RESET}          蒙多状态
  {C.STEEL}/reset{C.RESET}           重置对话上下文

{C.AMBER}模型{C.RESET}
  {C.STEEL}/model{C.RESET}           查看当前模型
  {C.STEEL}/models{C.RESET}          已配置模型 + 能力矩阵
  {C.STEEL}/switch P{C.RESET}        切换 provider
  {C.STEEL}/providers{C.RESET}       全量 28 个模型
  {C.STEEL}/add{C.RESET}             添加新 AI 模型

{C.AMBER}上下文管理（借鉴 Claude Code）{C.RESET}
  {C.STEEL}/compact{C.RESET}         压缩上下文（省 token）
  {C.STEEL}/context{C.RESET}         上下文窗口使用率
  {C.STEEL}/btw <问题>{C.RESET}      旁问（不消耗上下文）
  {C.STEEL}/effort{C.RESET}          推理深度（low/medium/high/max）

{C.AMBER}记忆{C.RESET}
  {C.STEEL}/remember K V{C.RESET}    记住事实
  {C.STEEL}/recall K{C.RESET}        回忆事实（支持相关性检索）
  {C.STEEL}/forget K{C.RESET}        遗忘事实
  {C.STEEL}/memories{C.RESET}        列出所有记忆
  {C.STEEL}/memory{C.RESET}          记忆系统状态 + 自动合并
  {C.STEEL}/import{C.RESET}          从已有 Agent 导入记忆

{C.AMBER}云仓库{C.RESET}
  {C.STEEL}/sync{C.RESET}            同步新 Skill 到云仓库
  {C.STEEL}/pull{C.RESET}            从云仓库拉取 Skills + 全局规范
  {C.STEEL}/update{C.RESET}          检查并更新蒙多（保留记忆）
  {C.STEEL}/audit{C.RESET}           运行质量审计
  {C.STEEL}/skills{C.RESET}          列出本地 Skill
  {C.STEEL}/agents{C.RESET}          检测本地 Agent

{C.AMBER}工具{C.RESET}
  {C.STEEL}/tools{C.RESET}           列出所有工具
  {C.STEEL}/setup{C.RESET}           重新运行设置向导

{C.AMBER}直接执行{C.RESET}
  {C.STEEL}!command{C.RESET}          直接执行 shell 命令

{C.CYAN}直接输入任何文本，蒙多开始执行任务。{C.RESET}
{C.DIM}  输入区支持自动换行，金色条框标识输入区域。{C.RESET}
""")

    def show_status(self):
        stats = self.memory.get_stats()
        s = self.engine.stats
        print(f"""
{C.GOLD}{C.BOLD}═══ 蒙多帝国状态 ═══{C.RESET}
{C.AMBER}Provider{C.RESET}:  {self.provider}
{C.AMBER}Model{C.RESET}:     {self._model_display()}
{C.AMBER}Effort{C.RESET}:    {self._effort}
{C.AMBER}Memory{C.RESET}:    {stats['total_memories']} 条记忆 ({stats['total_tokens']} 字符)
{C.AMBER}Profile{C.RESET}:   {stats['profile_keys']} 项画像
{C.AMBER}Tokens{C.RESET}:    {s.total_tokens} (本次会话)
{C.AMBER}Tools{C.RESET}:     {len(TOOL_SCHEMAS)} 个可用
""")

    # ─────────────────────────────────────────
    # 新命令（借鉴 Claude Code / Hermes Agent / Codex）
    # ─────────────────────────────────────────

    def cmd_compact(self):
        """压缩上下文 — 借鉴 Claude Code /compact"""
        if not self.engine.messages:
            print(f"  {C.IRON}没有对话上下文需要压缩{C.RESET}")
            return

        msg_count = len(self.engine.messages)
        total_chars = sum(len(m.get("content", "")) for m in self.engine.messages)

        # 保留 system prompt + 最近 4 轮对话
        system_msg = self.engine.messages[0] if self.engine.messages[0]["role"] == "system" else None
        recent = self.engine.messages[-8:] if len(self.engine.messages) > 8 else self.engine.messages[1:]

        # 生成摘要
        summary_parts = []
        for msg in self.engine.messages[1:-8] if len(self.engine.messages) > 9 else []:
            role = msg["role"]
            content = msg.get("content", "")[:100]
            if content:
                summary_parts.append(f"[{role}] {content}")

        summary = " | ".join(summary_parts[-10:]) if summary_parts else "(早期对话已省略)"

        # 重建上下文
        new_messages = []
        if system_msg:
            new_messages.append(system_msg)
        new_messages.append({
            "role": "system",
            "content": f"[上下文压缩摘要] {summary[:500]}"
        })
        new_messages.extend(recent)

        self.engine.messages = new_messages
        new_chars = sum(len(m.get("content", "")) for m in self.engine.messages)

        print(f"  {C.SUCCESS}✓ 上下文已压缩{C.RESET}")
        print(f"  {C.DIM}  {msg_count} 条消息 → {len(self.engine.messages)} 条消息{C.RESET}")
        print(f"  {C.DIM}  {total_chars} 字符 → {new_chars} 字符{C.RESET}")

    def cmd_context(self):
        """显示上下文窗口使用率 — 借鉴 Claude Code /context"""
        if not self.engine.messages:
            print(f"  {C.IRON}没有对话上下文{C.RESET}")
            return

        msg_count = len(self.engine.messages)
        total_chars = sum(len(m.get("content", "")) for m in self.engine.messages)
        est_tokens = total_chars // 3  # 粗略估算 1 token ≈ 3 字符

        # 假设上下文窗口 128K tokens
        context_limit = 128000
        usage_pct = (est_tokens / context_limit) * 100

        # 可视化条
        bar_width = 40
        filled = int(bar_width * usage_pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        # 颜色：绿 < 70%，黄 70-85%，红 > 85%
        if usage_pct < 70:
            bar_color = C.SUCCESS
            status = "健康"
        elif usage_pct < 85:
            bar_color = C.AMBER
            status = "偏高，建议 /compact"
        else:
            bar_color = C.ERROR
            status = "危险，强烈建议 /compact"

        print(f"\n  {C.GOLD}上下文窗口{C.RESET}")
        print(f"  {bar_color}{bar}{A.RESET} {usage_pct:.0f}%")
        print(f"  {C.DIM}消息: {msg_count} 条 · 字符: {total_chars:,} · 估算 tokens: {est_tokens:,} / {context_limit:,}{C.RESET}")
        print(f"  {bar_color}状态: {status}{C.RESET}")

        # 消息类型分布
        role_counts = {}
        for msg in self.engine.messages:
            role = msg["role"]
            role_counts[role] = role_counts.get(role, 0) + 1
        print(f"  {C.DIM}分布: {role_counts}{C.RESET}\n")

    def cmd_btw(self, query: str):
        """旁问（不消耗上下文）— 借鉴 Claude Code /btw"""
        if not query:
            print(f"  {C.ERROR}用法: /btw <问题>{C.RESET}")
            return

        print(f"  {C.DIM}(旁问模式 — 不计入上下文){C.RESET}")
        try:
            # 直接调用 LLM，不存入 messages
            temp_messages = [
                {"role": "system", "content": "你是蒙多。简洁回答用户问题，不超过 200 字。"},
                {"role": "user", "content": query},
            ]
            result = self.engine.client.chat(
                messages=temp_messages,
                temperature=0.7,
                max_tokens=512,
            )
            from llm import LLMClient
            response = LLMClient.extract_response(result)
            text = response.get("content", "(无回复)")
            print(f"\n  {C.STEEL}{text}{C.RESET}\n")
        except Exception as e:
            print(f"  {C.ERROR}旁问失败: {e}{C.RESET}")

    def cmd_effort(self, level: str = ""):
        """设置推理深度 — 借鉴 Claude Code /effort"""
        valid = ("low", "medium", "high", "max", "auto")
        if not level:
            print(f"  {C.AMBER}当前推理深度: {self._effort}{C.RESET}")
            print(f"  {C.DIM}可选: {', '.join(valid)}{C.RESET}")
            print(f"  {C.DIM}low=快速省token · medium=平衡 · high=深度推理 · max=全力以赴{C.RESET}")
            return
        level = level.lower()
        if level not in valid:
            print(f"  {C.ERROR}无效级别: {level}. 可选: {', '.join(valid)}{C.RESET}")
            return
        self._effort = level
        token_map = {"low": 1024, "medium": 2048, "high": 4096, "max": 8192, "auto": 4096}
        self.engine.max_tokens_override = token_map.get(level, 4096)
        print(f"  {C.SUCCESS}✓ 推理深度: {level}{C.RESET}")

    def cmd_import(self):
        """手动触发记忆导入"""
        import_flag = MUNDO_HOME / ".memory_imported"
        if import_flag.exists():
            import_flag.unlink()

        self._import_memory_if_first_run()

    # ─────────────────────────────────────────
    # 原有命令
    # ─────────────────────────────────────────

    def cmd_remember(self, args):
        if len(args) < 2:
            print(f"{C.ERROR}用法: /remember <key> <value>{C.RESET}")
            return
        key, value = args[0], " ".join(args[1:])
        self.memory.remember_fact(key, value)
        print(f"{C.SUCCESS}✓ 已记住: {key}{C.RESET}")

    def cmd_recall(self, args):
        if not args:
            print(f"{C.ERROR}用法: /recall <key>{C.RESET}")
            return
        value = self.memory.recall_key(args[0])
        if not value:
            results = self.memory.recall(args[0], max_items=3)
            if results:
                print(f"  {C.CYAN}{results}{C.RESET}")
            else:
                print(f"{C.IRON}蒙多不记得 '{args[0]}'{C.RESET}")
        else:
            print(f"  {C.CYAN}{value}{C.RESET}")

    def cmd_forget(self, args):
        if not args:
            print(f"{C.ERROR}用法: /forget <key>{C.RESET}")
            return
        self.memory.forget(args[0])
        print(f"{C.SUCCESS}✓ 已遗忘: {args[0]}{C.RESET}")

    def cmd_memories(self):
        facts = self.memory.all_facts(limit=30)
        if not facts:
            print(f"{C.IRON}蒙多还没有记忆{C.RESET}")
            return
        for content, cat, imp in facts:
            stars = "★" * min(imp, 5)
            print(f"  {C.GOLD}{stars}{C.RESET} [{C.DIM}{cat}{C.RESET}] {content[:80]}")

    def cmd_memory_stats(self):
        stats = self.memory.get_stats()
        print(f"\n  {C.GOLD}{C.BOLD}蒙多记忆系统 v2{C.RESET}")
        print(f"  {C.AMBER}总记忆{C.RESET}:     {stats['total_memories']} 条")
        print(f"  {C.AMBER}总字符{C.RESET}:     {stats['total_tokens']}")
        print(f"  {C.AMBER}对话记录{C.RESET}:   {stats['conversations']} 条")
        print(f"  {C.AMBER}用户画像{C.RESET}:   {stats['profile_keys']} 项")
        cat = stats.get('by_category', {})
        if cat:
            print(f"\n  {C.DIM}分类:{C.RESET}")
            for c, n in cat.items():
                print(f"    {c}: {n}")
        self.memory.consolidate()
        print(f"\n  {C.DIM}三层架构: 热记忆(当前对话) → 温记忆(近期摘要) → 冷记忆(持久事实){C.RESET}")
        print(f"  {C.DIM}注入预算: {2000} 字符/次 | 自动提取: 对话后自动提取事实{C.RESET}\n")

    def cmd_model(self):
        print(f"  {C.AMBER}Provider{C.RESET}: {self.provider}")
        print(f"  {C.AMBER}Model{C.RESET}:    {self._model_display()}")
        print(f"  {C.AMBER}Effort{C.RESET}:   {self._effort}")

    def cmd_switch(self, args):
        if not args:
            print(f"{C.ERROR}用法: /switch <provider>{C.RESET}")
            return
        prov = args[0]
        if prov not in PROVIDERS:
            print(f"{C.ERROR}未知 provider: {prov}. 可选: {list(PROVIDERS.keys())}{C.RESET}")
            return
        available = get_available_providers()
        if prov not in available:
            print(f"{C.ERROR}{prov} 没有 API key. 用 /add 添加。{C.RESET}")
            return
        self.provider = prov
        self.model = None
        self._init_engine()
        print(f"{C.SUCCESS}✓ 已切换到 {prov} ({PROVIDERS[prov]['default_model']}){C.RESET}")

    def cmd_providers(self):
        available = get_available_providers()
        from setup import PROVIDERS as ALL_PROV, DISPLAY_ORDER
        groups = {}
        for key in DISPLAY_ORDER:
            p = ALL_PROV[key]
            g = p["group"]
            if g not in groups:
                groups[g] = []
            groups[g].append((key, p))
        print(f"\n{C.GOLD}全量 AI 模型 ({len(ALL_PROV)} 个){C.RESET}")
        for group_name, items in groups.items():
            print(f"\n  {C.AMBER}━━ {group_name} ━━{C.RESET}")
            for key, p in items:
                status = "✓" if key in available else "✗"
                color = C.SUCCESS if key in available else C.DIM
                print(f"    {color}{status} {key:16} {p['model']:35} {C.DIM}{p['desc']}{C.RESET}")
        print()

    def cmd_add(self):
        name, model = add_provider_interactive()
        if name:
            self.provider = name
            self.model = model
            self._init_engine()

    def cmd_sync(self):
        print(f"  {C.IRON}同步新 Skill 到云仓库...{C.RESET}")
        result = process_upload_queue()
        print(f"  {C.SUCCESS}✓ 上传: {result['uploaded']}{C.RESET}  {C.IRON}跳过: {result['skipped']}{C.RESET}  {C.ERROR}失败: {result['failed']}{C.RESET}")

    def cmd_pull(self):
        print(f"  {C.IRON}从云仓库拉取 Skills 和全局规范...{C.RESET}")
        from cloud_sync import initial_deploy
        result = initial_deploy()
        s = result.get("skills", {})
        p = result.get("specs", {})
        print(f"  {C.SUCCESS}✓ Skills: 拉取 {s.get('pulled', 0)} / 跳过 {s.get('skipped', 0)}{C.RESET}")
        print(f"  {C.SUCCESS}✓ 规范: 拉取 {p.get('pulled', 0)} / 跳过 {p.get('skipped', 0)}{C.RESET}")

    def cmd_update(self):
        from cloud_sync import check_update, perform_update, get_local_version
        local = get_local_version()
        print(f"  {C.IRON}检查更新... (当前版本: v{local}){C.RESET}")
        info = check_update()
        if not info["available"]:
            print(f"  {C.SUCCESS}✓ 已是最新版本 v{local}{C.RESET}")
            return
        print(f"  {C.AMBER}发现新版本: v{info['local']} → v{info['remote']}{C.RESET}")
        if info.get("changelog"):
            print(f"  {C.DIM}{info['changelog'][:200]}{C.RESET}")
        answer = input(f"  {C.GOLD}确认更新？[Y/n]：{C.RESET}").strip().lower()
        if answer == "n":
            print(f"  {C.DIM}已取消{C.RESET}")
            return
        print(f"  {C.IRON}更新中...（记忆和配置将完整保留）{C.RESET}")
        result = perform_update()
        print(f"\n  {C.SUCCESS}✓ 更新完成: v{result.get('new_version', '?')}{C.RESET}")
        print(f"  {C.DIM}  更新: {len(result['updated'])} 个文件{C.RESET}")
        print(f"  {C.DIM}  保留: {', '.join(result['preserved'][:5])}{C.RESET}")
        if result["failed"]:
            print(f"  {C.ERROR}  失败: {len(result['failed'])} 个{C.RESET}")
        print(f"  {C.AMBER}  重启蒙多以加载新版本。{C.RESET}\n")

    def _check_update_background(self):
        try:
            from cloud_sync import check_update
            info = check_update()
            if info["available"]:
                print(f"  {C.AMBER}发现新版本 v{info['remote']}（当前 v{info['local']}）。输入 /update 更新。{C.RESET}")
        except Exception:
            pass

    def cmd_audit(self):
        print(f"  {C.IRON}运行质量审计...{C.RESET}")
        result = daily_quality_audit()
        if "error" in result:
            print(f"  {C.ERROR}{result['error']}{C.RESET}")
            return
        print(f"\n  {C.GOLD}审计结果{C.RESET}")
        print(f"  总计: {result['total']}  高质量: {result['high']}  中等: {result['medium']}  低质量: {result['low']}")
        if result["flagged"]:
            print(f"\n  {C.ERROR}需整改:{C.RESET}")
            for f in result["flagged"][:10]:
                print(f"    {f['name']}: {f['score']}分")

    def cmd_agents(self):
        agents = self.agent_mgr.list_available()
        print(f"\n  {C.GOLD}检测到的 Agent{C.RESET}")
        if not agents:
            print(f"  {C.IRON}未检测到外部 Agent。蒙多将用分身模式并行执行复杂任务。{C.RESET}")
            print(f"  {C.DIM}安装 Hermes Agent / Claude Code / Codex 后自动检测。{C.RESET}\n")
            return
        for a in agents:
            print(f"\n  {C.SUCCESS}✓ {a['name']}{C.RESET}  {C.DIM}{a['version']}{C.RESET}")
            print(f"    {C.IRON}擅长: {', '.join(a['strengths'][:3])}{C.RESET}")
        print(f"\n  {C.DIM}蒙多会根据任务类型自动选择最佳 Agent{C.RESET}\n")

    def cmd_models(self):
        from models import MODEL_PROFILES, format_model_strengths
        from setup import load_local_env
        env = load_local_env()
        print(f"\n  {C.GOLD}已配置的模型 + 能力矩阵{C.RESET}\n")
        configured = []
        for key, cfg in PROVIDERS.items():
            if env.get(cfg["env_key"]):
                model_key = f"{key}/{cfg['model']}"
                strengths = format_model_strengths(model_key)
                current = " ← 当前" if key == self.provider else ""
                print(f"  {C.SUCCESS}✓ {cfg['label']:20}{C.RESET} {cfg['model']:35} {C.DIM}{strengths}{C.RESET}{C.AMBER}{current}{C.RESET}")
                configured.append(key)
        if not configured:
            print(f"  {C.IRON}未配置任何模型。运行 /setup 设置。{C.RESET}")
        else:
            print(f"\n  {C.DIM}蒙多会根据任务类型自动选择最佳模型。/switch 手动切换。{C.RESET}")
            print(f"  {C.DIM}编码任务 → DeepSeek/Claude  |  日常对话 → MiMo  |  推理 → DeepSeek R1{C.RESET}\n")

    def cmd_skills(self):
        from cloud_sync import scan_local_skills
        skills = scan_local_skills()
        print(f"\n  {C.GOLD}本地 Skill ({len(skills)} 个){C.RESET}\n")
        for s in sorted(skills, key=lambda x: x["name"])[:30]:
            print(f"  {C.STEEL}{s['name']:30}{C.RESET} {s['size']}字节")
        if len(skills) > 30:
            print(f"  {C.DIM}... 还有 {len(skills) - 30} 个{C.RESET}")
        print()

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
            "/sync": lambda: self.cmd_sync(),
            "/pull": lambda: self.cmd_pull(),
            "/update": lambda: self.cmd_update(),
            "/audit": lambda: self.cmd_audit(),
            "/skills": lambda: self.cmd_skills(),
            "/agents": lambda: self.cmd_agents(),
            "/models": lambda: self.cmd_models(),
            "/compact": lambda: self.cmd_compact(),
            "/context": lambda: self.cmd_context(),
            "/btw": lambda: self.cmd_btw(raw_arg),
            "/effort": lambda: self.cmd_effort(args[0] if args else ""),
            "/import": lambda: self.cmd_import(),
        }
        if cmd in handlers:
            handlers[cmd]()
            return True
        print(f"{C.ERROR}未知命令: {cmd}. 输入 /help 查看帮助。{C.RESET}")
        return True

    def _show_tools(self):
        print(f"\n{C.GOLD}{C.BOLD}蒙多的武器库{C.RESET}\n")
        for t in TOOL_SCHEMAS:
            fn = t["function"]
            print(f"  {C.AMBER}{fn['name']:20}{C.RESET} {fn['description'][:60]}")
        print()

    def _rerun_setup(self):
        from setup import MUNDO_SETUP_FLAG
        if MUNDO_SETUP_FLAG.exists():
            MUNDO_SETUP_FLAG.unlink()
        provider, model = run_setup()
        self.provider = provider
        self.model = model
        self._init_engine()
        print(f"{C.SUCCESS}✓ 设置已更新{C.RESET}")

    def _reset(self):
        self.engine.reset()
        print(f"{C.SUCCESS}✓ 对话上下文已重置{C.RESET}")

    def _exit(self):
        self.console.cleanup()
        print(f"\n  {C.GOLD}蒙多退朝。下次再战。{C.RESET}")
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
                    print(f"\n{C.IRON}  (Ctrl+C) 输入 /quit 退出{C.RESET}")
                except EOFError:
                    self._exit()

    def _execute_task(self, line: str):
        """执行任务"""
        # 智能记忆注入
        extra = self.memory.get_context_budget(line)

        # 对话结束后自动提取事实
        if self.engine.messages:
            self.memory.extract_from_conversation(self.engine.messages, self.engine.client)
            self.memory.compress_conversation(self.engine.messages, self.session_id)

        # 标记引擎忙
        self._engine_busy = True
        self.console.start_task()

        try:
            response = self.engine.run(line, extra_context=extra)
            self.console.log_response(response)
        except Exception as e:
            self.console.log_error(str(e))
        finally:
            self._engine_busy = False
            self.console.stop_task()

            # 生成会话摘要（借鉴 claude-mem）
            try:
                self.memory.generate_session_summary(
                    self.session_id, self.engine.client
                )
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
        print(response)
        return

    if not args.no_banner:
        cli.show_banner()

    cli.run()


if __name__ == "__main__":
    main()
