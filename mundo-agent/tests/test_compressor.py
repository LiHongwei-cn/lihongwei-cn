"""上下文压缩器单元测试"""

import pytest
from mundo_agent.core.compressor import ContextCompressor, CompressionConfig


class TestCompressionConfig:
    """CompressionConfig 测试"""

    def test_default_values(self):
        """测试默认值"""
        config = CompressionConfig()
        assert config.char_to_token_ratio == 0.4
        assert config.max_messages_before_compress == 8
        assert config.target_tokens == 60000
        assert config.warn_threshold_tokens == 70000
        assert config.keep_recent_messages == 8
        assert config.max_summary_length == 600
        assert config.max_tool_content_length == 500


class TestContextCompressor:
    """ContextCompressor 测试"""

    def test_estimate_tokens_empty(self):
        """测试空消息的 token 估算"""
        compressor = ContextCompressor()
        assert compressor.estimate_tokens([]) == 0

    def test_estimate_tokens_basic(self):
        """测试基本 token 估算"""
        compressor = ContextCompressor()
        messages = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮你的？"},
        ]
        # 中文约 2.5 字符/token，所以 10 字符 ≈ 4 tokens
        tokens = compressor.estimate_tokens(messages)
        assert tokens > 0
        assert tokens < 100

    def test_estimate_tokens_with_tool_calls(self):
        """测试带 tool_calls 的 token 估算"""
        compressor = ContextCompressor()
        messages = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "function": {
                        "name": "terminal",
                        "arguments": '{"command": "echo hello"}'
                    }
                }]
            }
        ]
        tokens = compressor.estimate_tokens(messages)
        assert tokens > 0

    def test_should_compress_below_threshold(self):
        """测试低于阈值时不压缩"""
        config = CompressionConfig(warn_threshold_tokens=1000)
        compressor = ContextCompressor(config)

        messages = [
            {"role": "user", "content": "你好"},
        ]
        assert compressor.should_compress(messages) is False

    def test_should_compress_above_threshold(self):
        """测试高于阈值时压缩"""
        config = CompressionConfig(warn_threshold_tokens=10)
        compressor = ContextCompressor(config)

        # 创建足够大的消息
        messages = [
            {"role": "user", "content": "这是一条很长的消息" * 100},
        ]
        assert compressor.should_compress(messages) is True

    def test_compress_short_messages(self):
        """测试压缩短消息（不压缩）"""
        compressor = ContextCompressor()

        messages = [
            {"role": "system", "content": "系统提示"},
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！"},
        ]

        result = compressor.compress(messages)
        assert len(result) == len(messages)

    def test_compress_preserves_system_message(self):
        """测试压缩保留 system 消息"""
        config = CompressionConfig(
            max_messages_before_compress=2,
            target_tokens=10
        )
        compressor = ContextCompressor(config)

        messages = [
            {"role": "system", "content": "系统提示"},
            {"role": "user", "content": "消息1" * 100},
            {"role": "assistant", "content": "回复1" * 100},
            {"role": "user", "content": "消息2" * 100},
            {"role": "assistant", "content": "回复2" * 100},
        ]

        result = compressor.compress(messages)
        # 应该保留 system 消息
        assert result[0]["role"] == "system"

    def test_compress_preserves_recent_messages(self):
        """测试压缩保留最近的消息"""
        config = CompressionConfig(
            max_messages_before_compress=2,
            target_tokens=10,
            keep_recent_messages=2
        )
        compressor = ContextCompressor(config)

        messages = [
            {"role": "system", "content": "系统提示"},
            {"role": "user", "content": "旧消息1" * 100},
            {"role": "assistant", "content": "旧回复1" * 100},
            {"role": "user", "content": "新消息2"},
            {"role": "assistant", "content": "新回复2"},
        ]

        result = compressor.compress(messages)
        # 应该保留最近的消息
        assert any(m.get("content") == "新消息2" for m in result)
        assert any(m.get("content") == "新回复2" for m in result)

    def test_compress_tool_messages(self):
        """测试压缩 tool 消息"""
        config = CompressionConfig(
            max_messages_before_compress=2,
            target_tokens=10,
            max_tool_content_length=50
        )
        compressor = ContextCompressor(config)

        long_content = "很长的工具输出" * 100
        messages = [
            {"role": "system", "content": "系统提示"},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "test", "arguments": "{}"}}]
            },
            {
                "role": "tool",
                "tool_call_id": "123",
                "content": long_content
            },
            {"role": "user", "content": "新消息"},
        ]

        result = compressor.compress(messages)
        # tool 消息应该被压缩
        tool_msgs = [m for m in result if m["role"] == "tool"]
        if tool_msgs:
            assert len(tool_msgs[0]["content"]) < len(long_content)