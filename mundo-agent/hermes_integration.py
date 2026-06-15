"""蒙多 Hermes Agent 深度集成 v24.9 — Hermes Agent CLI 全能力封装

适配版本：Hermes v0.16.0+
保持配置：xiaomi/mimo-v2.5-pro

能力：
- 一次性查询（hermes chat -q）
- 交互式会话（hermes chat）
- 指定模型/Provider（--model / --provider）
- 加载技能（--skills）
- 限制工具集（--toolsets）
- 后台长任务
- 会话管理（--resume / --continue）
- 多平台网关（telegram/discord/slack/whatsapp）
- 定时任务（cron）
- 记忆系统（memory）
- 技能管理（skills）
- 版本检测与兼容性验证
"""

import os
import shutil
import subprocess
from typing import Dict, List, Optional


HERMES_CMD = shutil.which("hermes")


def _run_hermes(
    args: List[str],
    timeout: int = 300,
    workdir: Optional[str] = None,
    background: bool = False,
) -> str:
    if not HERMES_CMD:
        return "[Hermes Agent 未安装]"

    cmd = [HERMES_CMD] + args

    if background:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=workdir,
        )
        return f"[Hermes 后台启动 PID={proc.pid}]"

    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir,
        )
        output = r.stdout.strip()
        if r.returncode != 0 and r.stderr.strip():
            output += f"\n[stderr] {r.stderr.strip()}"
        return output or "[Hermes 无输出]"
    except subprocess.TimeoutExpired:
        return f"[Hermes 超时 ({timeout}s)]"
    except FileNotFoundError:
        return "[Hermes Agent 未安装]"
    except Exception as e:
        return f"[Hermes 错误: {e}]"


class HermesAgent:
    """Hermes Agent CLI 深度集成"""

    def __init__(self):
        self.available = HERMES_CMD is not None
        self.cmd = HERMES_CMD

    def is_available(self) -> bool:
        return self.available

    def chat_one_shot(
        self,
        prompt: str,
        model: Optional[str] = None,
        provider: Optional[str] = "xiaomi",
        toolsets: Optional[str] = None,
        skills: Optional[str] = None,
        timeout: int = 300,
        workdir: Optional[str] = None,
        lite: bool = False,
    ) -> str:
        args = ["chat", "-q", prompt, "-Q"]
        if model:
            args += ["-m", model]
        if provider:
            args += ["--provider", provider]
        if toolsets:
            args += ["-t", toolsets]
        if skills:
            args += ["-s", skills]
        # 轻量模式：跳过用户配置和规则文件，限制轮次
        if lite:
            args += ["--ignore-user-config", "--max-turns", "15"]
        return _run_hermes(args, timeout=timeout, workdir=workdir)

    def chat_with_skills(
        self,
        prompt: str,
        skills: List[str],
        model: Optional[str] = None,
        timeout: int = 300,
    ) -> str:
        return self.chat_one_shot(
            prompt,
            model=model,
            skills=",".join(skills),
            timeout=timeout,
        )

    def chat_with_tools(
        self,
        prompt: str,
        toolsets: List[str],
        model: Optional[str] = None,
        timeout: int = 300,
    ) -> str:
        return self.chat_one_shot(
            prompt,
            model=model,
            toolsets=",".join(toolsets),
            timeout=timeout,
        )

    def chat_background(
        self,
        prompt: str,
        model: Optional[str] = None,
        toolsets: Optional[str] = None,
    ) -> str:
        args = ["chat", "-q", prompt, "-Q"]
        if model:
            args += ["-m", model]
        if toolsets:
            args += ["-t", toolsets]
        return _run_hermes(args, background=True)

    def chat_resume(
        self,
        session_id: str,
        prompt: str,
        timeout: int = 300,
    ) -> str:
        args = ["chat", "-q", prompt, "-Q", "--resume", session_id]
        return _run_hermes(args, timeout=timeout)

    def chat_continue(
        self,
        prompt: str,
        timeout: int = 300,
    ) -> str:
        args = ["chat", "-q", prompt, "-Q", "--continue"]
        return _run_hermes(args, timeout=timeout)

    def send_message(
        self,
        platform: str,
        message: str,
        timeout: int = 30,
    ) -> str:
        args = ["send", "--platform", platform, "--message", message]
        return _run_hermes(args, timeout=timeout)

    def cron_create(
        self,
        schedule: str,
        prompt: str,
        name: Optional[str] = None,
        timezone: str = "Asia/Shanghai",
    ) -> str:
        args = ["cron", "create", "--schedule", schedule, "--prompt", prompt, "--timezone", timezone]
        if name:
            args += ["--name", name]
        return _run_hermes(args, timeout=60)

    def cron_list(self) -> str:
        return _run_hermes(["cron", "list"], timeout=30)

    def skills_list(self) -> str:
        return _run_hermes(["skills", "list"], timeout=30)

    def memory_add(self, content: str, target: str = "memory") -> str:
        return _run_hermes(
            ["memory", "add", "--content", content, "--target", target],
            timeout=30,
        )

    def memory_search(self, query: str) -> str:
        return _run_hermes(
            ["memory", "search", "--query", query],
            timeout=30,
        )

    def status(self) -> str:
        return _run_hermes(["status"], timeout=30)

    def gateway_status(self) -> str:
        return _run_hermes(["gateway", "status"], timeout=30)

    def gateway_restart(self) -> str:
        return _run_hermes(["gateway", "restart"], timeout=60)

    def doctor(self) -> str:
        return _run_hermes(["doctor"], timeout=60)

    def tools_list(self) -> str:
        return _run_hermes(["tools", "list"], timeout=30)

    def sessions_list(self) -> str:
        return _run_hermes(["sessions", "list"], timeout=30)


def get_hermes_agent() -> Optional[HermesAgent]:
    agent = HermesAgent()
    return agent if agent.is_available() else None
