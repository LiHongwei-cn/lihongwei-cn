"""蒙多常量 v2.1.2 — 所有魔法数字的家

一处定义，全局引用。零硬编码散落。
版本号由版本管理系统自动管理。
"""

from pathlib import Path

# ═══════════════════════════════════════════════
# 路径
# ═══════════════════════════════════════════════

MUNDO_HOME = Path.home() / ".hermes" / "mundo-agent"
VENV_DIR = MUNDO_HOME / "venv"
MEMORY_DB = MUNDO_HOME / "memory.db"
EVENTS_LOG = MUNDO_HOME / "events.jsonl"
TIMELINE_DB = MUNDO_HOME / "timeline.db"
HISTORY_FILE = MUNDO_HOME / ".mundo_history"
SETUP_FLAG = MUNDO_HOME / ".setup_complete"
ENV_FILE = MUNDO_HOME / ".env"
CONFIG_FILE = MUNDO_HOME / "config.json"

# ═══════════════════════════════════════════════
# 版本 — 由版本管理系统自动管理
# ═══════════════════════════════════════════════

def _get_version():
    """从版本管理系统获取版本号"""
    try:
        from version_manager import get_current_version
        return get_current_version()
    except ImportError:
        # 如果版本管理系统不可用，返回默认版本
        return "v2.1.2"

VERSION = _get_version()

# ═══════════════════════════════════════════════
# 默认模型
# ═══════════════════════════════════════════════

DEFAULT_PROVIDER = "deepseek"
DEFAULT_MODEL = "deepseek-chat"

# ═══════════════════════════════════════════════
# Token 估算
# ═══════════════════════════════════════════════

CHAR_TO_TOKEN = 0.4

# ═══════════════════════════════════════════════
# 上下文窗口
# ═══════════════════════════════════════════════

CONTEXT_MAX_TOKENS = 128000
CONTEXT_COMPRESS_THRESHOLD = 0.7
CONTEXT_KEEP_RECENT = 8

# ═══════════════════════════════════════════════
# 预算
# ═══════════════════════════════════════════════

BUDGET_MAX_PROMPT = 500000
BUDGET_MAX_COMPLETION = 200000
BUDGET_WARN_THRESHOLD = 0.7

# ═══════════════════════════════════════════════
# LLM 超时
# ═══════════════════════════════════════════════

DNS_TIMEOUT = 8
READ_TIMEOUT_FIRST = 90
READ_TIMEOUT_RETRY = 180
STREAM_IDLE_TIMEOUT = 45
STREAM_MAX_WAIT = 300

# ═══════════════════════════════════════════════
# 工具
# ═══════════════════════════════════════════════

TOOL_TIMEOUT = 30
TOOL_MAX_OUTPUT = 8000

# ═══════════════════════════════════════════════
# 记忆
# ═══════════════════════════════════════════════

MAX_CONTEXT_INJECT = 3000
MAX_FACTS_INJECT = 8
MAX_CONVERSATION_RESULTS = 5

# ═══════════════════════════════════════════════
# 稳定性
# ═══════════════════════════════════════════════

STUCK_THRESHOLD = 5
MAX_RETRY = 3
RETRY_DELAY = 2.0

# ═══════════════════════════════════════════════
# 帝皇决心
# ═══════════════════════════════════════════════

MAX_ITERATIONS = 80
IDLE_TIMEOUT = 600
LONG_TASK_THRESHOLD = 30
TASK_ABANDON_TIMEOUT = 1800
PROGRESS_CHECK_INTERVAL = 10

# ═══════════════════════════════════════════════
# 反射引擎
# ═══════════════════════════════════════════════

REFLECTION_MAX_TURNS = 30
REFLECTION_SUCCESS_THRESHOLD = 0.6

# ═══════════════════════════════════════════════
# 安全强化
# ═══════════════════════════════════════════════

SECURITY_RATE_LIMIT_PER_MINUTE = 60
SECURITY_MAX_INPUT_LENGTH = 100000

# ═══════════════════════════════════════════════
# 知识检索
# ═══════════════════════════════════════════════

KNOWLEDGE_MAX_CONTEXT_CHARS = 3000
KNOWLEDGE_SEARCH_TOP_K = 5