"""蒙多记忆导入 — 首次部署时自动读取已有 Agent 的记忆

扫描 Hermes Agent / Claude Code 的配置和记忆文件，
提取用户偏好、项目上下文、API Key，导入蒙多记忆系统。
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


G = "\033[38;5;178m"
R = "\033[0m"
D = "\033[2m"
OK = "\033[38;5;65m"
A = "\033[38;5;136m"

HERMES_HOME = Path.home() / ".hermes"
CLAUDE_HOME = Path.home() / ".claude"
MUNDO_HOME = HERMES_HOME / "mundo-agent"


def import_existing_memory(memory) -> Dict[str, int]:
    """导入已有 Agent 的记忆。返回统计。"""
    stats = {"keys_imported": 0, "facts_imported": 0, "source": ""}

    # 1. 导入 API Keys
    keys = _import_api_keys()
    stats["keys_imported"] = keys

    # 2. 读取 Claude Code CLAUDE.md
    claude_facts = _parse_claude_md()

    # 3. 读取 Hermes 配置
    hermes_facts = _parse_hermes_config()

    # 4. 合并去重写入记忆
    all_facts = claude_facts + hermes_facts
    seen = set()
    for content, category, importance in all_facts:
        # 简单去重
        key = content[:50].lower()
        if key in seen:
            continue
        seen.add(key)
        memory.remember(
            content=content,
            category=category,
            source="import",
            importance=importance,
        )
        stats["facts_imported"] += 1

    sources = []
    if claude_facts:
        sources.append("Claude Code")
    if hermes_facts:
        sources.append("Hermes Agent")
    stats["source"] = " + ".join(sources) if sources else "无"

    return stats


def _import_api_keys() -> int:
    """从 Hermes .env 导入 API Key 到 Mundo .env"""
    hermes_env = HERMES_HOME / ".env"
    mundo_env = MUNDO_HOME / ".env"

    if not hermes_env.exists():
        return 0

    # 读取已有的 Mundo env
    existing = {}
    try:
        if mundo_env.exists():
            for line in mundo_env.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    existing[k.strip()] = v.strip()
    except OSError:
        pass

    # 从 Hermes env 读取 API keys
    api_key_patterns = [
        "XIAOMI_API_KEY", "DEEPSEEK_API_KEY", "OPENROUTER_API_KEY",
        "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
        "GEMINI_API_KEY", "DASHSCOPE_API_KEY", "ZHIPU_API_KEY",
        "MOONSHOT_API_KEY", "MINIMAX_API_KEY", "BAIDU_API_KEY",
        "BYTEDANCE_API_KEY", "GROQ_API_KEY", "XAI_API_KEY",
        "COHERE_API_KEY", "HF_TOKEN", "MISTRAL_API_KEY",
        "TENCENT_API_KEY", "IFLYTEK_API_KEY", "SILICONFLOW_API_KEY",
    ]

    imported = 0
    new_keys = {}
    for line in hermes_env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        if k in api_key_patterns and v and k not in existing:
            new_keys[k] = v
            imported += 1

    if new_keys:
        MUNDO_HOME.mkdir(parents=True, exist_ok=True)
        all_keys = {**existing, **new_keys}
        lines = [f"{k}={v}" for k, v in all_keys.items()]
        mundo_env.write_text("\n".join(lines) + "\n")
        # 同步到环境变量
        for k, v in new_keys.items():
            os.environ[k] = v

    return imported


def _parse_claude_md() -> List[Tuple[str, str, int]]:
    """解析 Claude Code 的 CLAUDE.md，提取用户偏好和规则"""
    claude_md = CLAUDE_HOME / "CLAUDE.md"
    if not claude_md.exists():
        return []

    facts = []
    try:
        content = claude_md.read_text(encoding="utf-8")
    except Exception:
        return []

    # 提取身份信息
    if "黄鹏" in content or "LiHongwei" in content:
        facts.append(("用户身份：黄鹏（化名李宏伟），GitHub 用化名", "profile", 8))
    if "新能源汽车" in content:
        facts.append(("专业：新能源汽车工程", "profile", 7))
    if "MATLAB" in content:
        facts.append(("核心技能：MATLAB/Simulink 仿真", "profile", 7))

    # 提取偏好
    if "直接切入主题" in content or "不废话" in content:
        facts.append(("沟通风格：直接切入主题、不废话、简洁无冗余", "preference", 9))
    if "中文" in content and "交流" in content:
        facts.append(("语言偏好：中文交流，代码命名用英文", "preference", 8))

    # 提取项目信息
    repo_match = re.search(r"github\.com/([^/\"]+)/([^/\"]+)", content)
    if repo_match:
        facts.append((f"GitHub 仓库：{repo_match.group(0)}", "reference", 7))

    site_match = re.search(r"https?://([^\s\"]+\.github\.io/[^\s\"]+)", content)
    if site_match:
        facts.append((f"个人网站：{site_match.group(1)}", "reference", 6))

    # 提取代码规范
    if "R2016b" in content:
        facts.append(("MATLAB 兼容底线：R2016b（禁用 2017+ 函数）", "preference", 7))
    if "UTF-8" in content and "GBK" in content:
        facts.append((".m 文件编码：UTF-8（不用 GBK，macOS 会乱码）", "preference", 6))

    # 提取工具链
    tools = []
    if "CarSim" in content:
        tools.append("CarSim")
    if "Python" in content and "3.12" in content:
        tools.append("Python 3.12")
    if "微信小程序" in content:
        tools.append("微信小程序")
    if tools:
        facts.append((f"工具链：{', '.join(tools)}", "profile", 6))

    # 提取 Git 规范
    if "git commit" in content and "自动" in content:
        facts.append(("Git 行为：每次代码修改后自动 commit + push", "preference", 8))

    # 提取安全规则
    if "绝不硬编码密钥" in content or "硬编码" in content:
        facts.append(("安全规则：绝不硬编码密钥，从环境变量读取", "preference", 9))

    # 提取风格偏好
    if "emoji" in content and "不使用" in content:
        facts.append(("风格偏好：默认不使用 emoji", "preference", 5))
    if "总结" in content and "禁止" in content:
        facts.append(("风格偏好：禁止在结尾写总结性段落", "preference", 6))

    return facts


def _parse_hermes_config() -> List[Tuple[str, str, int]]:
    """解析 Hermes 配置，提取环境信息"""
    facts = []
    config_path = HERMES_HOME / "config.yaml"

    if not config_path.exists():
        return facts

    try:
        content = config_path.read_text(encoding="utf-8")
    except Exception:
        return facts

    # 提取默认模型
    model_match = re.search(r"default:\s*(.+)", content)
    if model_match:
        facts.append((f"Hermes 默认模型：{model_match.group(1).strip()}", "reference", 5))

    # 提取平台信息
    if "telegram" in content.lower():
        facts.append(("已配置 Telegram Bot 平台", "reference", 4))

    return facts
