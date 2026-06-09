"""蒙多常量 v1.4.2 — 所有魔法数字的家

一处定义，全局引用。消除硬编码散落。
"""

from pathlib import Path

# ═══════════════════════════════════════════════
# 路径 — 蒙多的疆域
# ═══════════════════════════════════════════════

MUNDO_HOME = Path.home() / ".hermes" / "mundo-agent"
VENV_DIR = MUNDO_HOME / "venv"
MEMORY_DB = MUNDO_HOME / "memory.db"
EVENTS_LOG = MUNDO_HOME / "events.jsonl"
TIMELINE_DB = MUNDO_HOME / "timeline.db"
HISTORY_FILE = MUNDO_HOME / ".mundo_history"
SETUP_FLAG = MUNDO_HOME / ".setup_complete"
ENV_FILE = MUNDO_HOME / ".env"
PASTE_DIR = MUNDO_HOME / "pastes"
SYNC_STATE = MUNDO_HOME / "sync_state.json"
UPLOAD_QUEUE = MUNDO_HOME / "upload_queue.json"
CONFIG_FILE = MUNDO_HOME / "config.json"

# ═══════════════════════════════════════════════
# 版本
# ═══════════════════════════════════════════════

VERSION = "1.5.1"

# ═══════════════════════════════════════════════
# Token 估算
# ═══════════════════════════════════════════════

CHAR_TO_TOKEN = 0.4  # 中英文混合约 2.5 字符/token

# ═══════════════════════════════════════════════
# 上下文窗口
# ═══════════════════════════════════════════════

CONTEXT_MAX_TOKENS = 128000
CONTEXT_COMPRESS_THRESHOLD = 0.7
CONTEXT_COMPRESS_TARGET = 0.5
CONTEXT_KEEP_RECENT = 8
CONTEXT_SYSTEM_RESERVE = 4000
CONTEXT_RESPONSE_RESERVE = 8000
CONTEXT_SAFETY_MARGIN = 2000

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
TOOL_MAX_OUTPUT = 500_000
TOOL_OUTPUT_PREVIEW_LINES = 5

# ═══════════════════════════════════════════════
# 记忆
# ═══════════════════════════════════════════════

MAX_CONTEXT_INJECT = 3000
MAX_FACTS_INJECT = 8
MAX_CONVERSATION_RESULTS = 5
MEMORY_MAX_FACTS = 100

# ═══════════════════════════════════════════════
# 稳定性
# ═══════════════════════════════════════════════

STUCK_THRESHOLD = 3
IDLE_TIMEOUT = 300
MAX_RETRY = 3
RETRY_DELAY = 2.0

# ═══════════════════════════════════════════════
# 帝皇决心 — 不完成不罢休
# ═══════════════════════════════════════════════

MAX_ITERATIONS = 200          # 最大迭代次数（复杂任务需要更多轮）
LONG_TASK_THRESHOLD = 50      # 长任务阈值（超过此值启用特殊处理）
TASK_ABANDON_TIMEOUT = 1800   # 任务放弃超时（30分钟无进展）
PROGRESS_CHECK_INTERVAL = 10  # 进度检查间隔（每10轮检查一次）
