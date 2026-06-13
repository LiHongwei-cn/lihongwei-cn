"""测试配置文件"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))


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