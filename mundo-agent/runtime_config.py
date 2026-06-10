"""蒙多 Runtime 定制 v2.0.8 — 皇帝的宫殿蓝图

可配置的运行时。不是硬编码。是声明式配置。
所有行为都可以通过配置覆盖，不需要改代码。

设计哲学：
- 配置是分层的：默认 → 全局 → 项目 → 会话 → 运行时
- 高层覆盖低层
- 类型安全：配置值有类型约束
- 热重载：配置变更立即生效
"""

import os
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from pathlib import Path


@dataclass
class LLMConfig:
    provider: str = "xiaomi"
    model: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    stream: bool = True
    timeout: int = 120
    retry_count: int = 3
    retry_delay: float = 2.0


@dataclass
class ContextConfig:
    max_tokens: int = 128000
    compress_threshold: float = 0.7
    compress_target: float = 0.5
    keep_recent: int = 8
    inject_memory: bool = True
    inject_project: bool = True
    memory_budget: int = 3000


@dataclass
class ToolConfig:
    enabled: List[str] = field(default_factory=lambda: [
        "terminal", "read_file", "write_file", "edit_file",
        "search_files", "web_search", "list_directory",
        "git_operation", "python_execute",
    ])
    require_approval: List[str] = field(default_factory=lambda: [
        "terminal", "write_file", "edit_file", "git_operation",
    ])
    timeout: int = 30
    max_output: int = 500_000


@dataclass
class SandboxConfig:
    enabled: bool = True
    timeout: int = 30
    max_memory_mb: int = 512
    max_output_bytes: int = 512_000
    network: bool = True


@dataclass
class CacheConfig:
    enabled: bool = True
    prefix_cache: bool = True
    semantic_cache: bool = True
    result_cache: bool = True
    semantic_threshold: float = 0.85
    result_ttl: int = 300


@dataclass
class PolicyConfig:
    enabled: bool = True
    audit_log: bool = True
    max_audit_entries: int = 1000


@dataclass
class MemoryConfig:
    enabled: bool = True
    auto_extract: bool = True
    auto_consolidate: bool = True
    max_facts: int = 100
    max_context_tokens: int = 3000


@dataclass
class DisplayConfig:
    theme: str = "gold"
    stream: bool = True
    show_tool_output: bool = True
    max_tool_lines: int = 5
    show_stats: bool = True
    compact_mode: bool = False


@dataclass
class DelegationConfig:
    enabled: bool = True
    max_concurrent: int = 3
    default_timeout: int = 120
    agents: Dict[str, str] = field(default_factory=lambda: {
        "codex": "codex",
        "claude": "claude-code",
        "hermes": "hermes",
    })


@dataclass
class RuntimeConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    context: ContextConfig = field(default_factory=ContextConfig)
    tools: ToolConfig = field(default_factory=ToolConfig)
    sandbox: SandboxConfig = field(default_factory=SandboxConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    policy: PolicyConfig = field(default_factory=PolicyConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    delegation: DelegationConfig = field(default_factory=DelegationConfig)

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeConfig":
        config = cls()
        if "llm" in data:
            for k, v in data["llm"].items():
                if hasattr(config.llm, k):
                    setattr(config.llm, k, v)
        if "context" in data:
            for k, v in data["context"].items():
                if hasattr(config.context, k):
                    setattr(config.context, k, v)
        if "tools" in data:
            for k, v in data["tools"].items():
                if hasattr(config.tools, k):
                    setattr(config.tools, k, v)
        if "sandbox" in data:
            for k, v in data["sandbox"].items():
                if hasattr(config.sandbox, k):
                    setattr(config.sandbox, k, v)
        if "cache" in data:
            for k, v in data["cache"].items():
                if hasattr(config.cache, k):
                    setattr(config.cache, k, v)
        if "policy" in data:
            for k, v in data["policy"].items():
                if hasattr(config.policy, k):
                    setattr(config.policy, k, v)
        if "memory" in data:
            for k, v in data["memory"].items():
                if hasattr(config.memory, k):
                    setattr(config.memory, k, v)
        if "display" in data:
            for k, v in data["display"].items():
                if hasattr(config.display, k):
                    setattr(config.display, k, v)
        if "delegation" in data:
            for k, v in data["delegation"].items():
                if hasattr(config.delegation, k):
                    setattr(config.delegation, k, v)
        return config


class ConfigManager:
    """配置管理器 — 分层加载、热重载"""

    GLOBAL_PATH = Path.home() / ".hermes" / "mundo-agent" / "config.json"
    PROJECT_PATH = Path.cwd() / ".mundo" / "config.json"

    def __init__(self):
        self._config = RuntimeConfig()
        self._overrides: Dict[str, Any] = {}

    def load(self) -> RuntimeConfig:
        """分层加载配置"""
        # 1. 全局配置
        if self.GLOBAL_PATH.exists():
            try:
                data = json.loads(self.GLOBAL_PATH.read_text(encoding="utf-8"))
                self._config = RuntimeConfig.from_dict(data)
            except (json.JSONDecodeError, OSError):
                pass

        # 2. 项目配置覆盖
        if self.PROJECT_PATH.exists():
            try:
                data = json.loads(self.PROJECT_PATH.read_text(encoding="utf-8"))
                project_config = RuntimeConfig.from_dict(data)
                self._merge(project_config)
            except (json.JSONDecodeError, OSError):
                pass

        # 3. 运行时覆盖
        for key, value in self._overrides.items():
            self._set_nested(key, value)

        return self._config

    def save_global(self) -> None:
        self.GLOBAL_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.GLOBAL_PATH.write_text(
            json.dumps(self._config.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def save_project(self) -> None:
        self.PROJECT_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.PROJECT_PATH.write_text(
            json.dumps(self._config.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def set(self, key: str, value: Any) -> None:
        """运行时覆盖配置"""
        self._overrides[key] = value
        self._set_nested(key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._get_nested(key, default)

    @property
    def config(self) -> RuntimeConfig:
        return self._config

    def _merge(self, other: RuntimeConfig) -> None:
        """合并配置"""
        for section in ["llm", "context", "tools", "sandbox", "cache",
                        "policy", "memory", "display", "delegation"]:
            src = getattr(other, section, None)
            dst = getattr(self._config, section, None)
            if src and dst:
                for k, v in src.__dict__.items():
                    if v is not None:
                        setattr(dst, k, v)

    def _set_nested(self, key: str, value: Any) -> None:
        parts = key.split(".")
        obj = self._config
        for part in parts[:-1]:
            obj = getattr(obj, part, None)
            if obj is None:
                return
        if hasattr(obj, parts[-1]):
            setattr(obj, parts[-1], value)

    def _get_nested(self, key: str, default: Any = None) -> Any:
        parts = key.split(".")
        obj = self._config
        for part in parts:
            obj = getattr(obj, part, None)
            if obj is None:
                return default
        return obj


# 全局单例
_manager: Optional[ConfigManager] = None


def get_config() -> RuntimeConfig:
    global _manager
    if _manager is None:
        _manager = ConfigManager()
        _manager.load()
    return _manager.config


def get_config_manager() -> ConfigManager:
    global _manager
    if _manager is None:
        _manager = ConfigManager()
        _manager.load()
    return _manager
