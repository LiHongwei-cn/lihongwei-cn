"""测试配置文件"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))


# ═══════════════════════════════════════════════
# 全局单例重置 — 确保每个测试独立运行
# ═══════════════════════════════════════════════

_SINGLETON_RESETS = [
    ("security_hardening", "reset_security"),
    ("policy", "reset_policy_engine"),
    ("reflection_engine", "reset_reflection_engine"),
    ("reflection_engine", "reset_strategy_selector"),
    ("intelligent_recovery", "reset_recovery"),
    ("intelligent_recovery", "reset_compressor"),
    ("knowledge_retriever", "reset_knowledge_retriever"),
    ("cache", "reset_cache_manager"),
    ("events", "reset_event_bus"),
    ("sandbox", "reset_sandbox"),
    ("plugins", "reset_plugin_loader"),
    ("skills", "reset_skill_registry"),
    ("task_analyzer", "reset_task_analyzer"),
    ("observability", "reset_logger"),
    ("observability", "reset_tracer"),
    ("observability", "reset_metrics"),
    ("runtime_config", "reset_config"),
    ("runtime_config", "reset_config_manager"),
    ("mcp_server", "reset_mcp_server"),
]


def _reset_all_singletons():
    """重置所有模块级全局单例 — 确保测试隔离"""
    for module_name, func_name in _SINGLETON_RESETS:
        try:
            mod = __import__(module_name)
            reset_fn = getattr(mod, func_name, None)
            if reset_fn:
                reset_fn()
        except Exception:
            pass  # 模块可能无法导入，跳过


@pytest.fixture(autouse=True)
def reset_singletons():
    """每个测试前自动重置所有全局单例"""
    _reset_all_singletons()
    yield


# ═══════════════════════════════════════════════

@pytest.fixture
def temp_dir(tmp_path):
    """创建临时目录"""
    return tmp_path


@pytest.fixture
def mock_env_vars(monkeypatch):
    """模拟环境变量"""
    monkeypatch.setenv("XIAOMI_API_KEY", "test_key_123")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test_key_456")


@pytest.fixture
def sample_messages():
    """示例消息列表"""
    return [
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮你的？"},
    ]


@pytest.fixture
def sample_tool_calls():
    """示例工具调用"""
    return [
        {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "terminal",
                "arguments": '{"command": "echo hello"}'
            }
        }
    ]


@pytest.fixture
def mock_llm_client():
    """模拟 LLM 客户端"""
    client = MagicMock()
    client.chat.return_value = {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "测试回复",
                "tool_calls": []
            }
        }],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
    }
    return client


@pytest.fixture
def db_path(tmp_path):
    """测试数据库路径"""
    return tmp_path / "test.db"