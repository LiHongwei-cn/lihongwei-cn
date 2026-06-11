"""蒙多性能优化模块 — 学习 Hermes/Claude 精华

优化策略：
1. 懒加载 — 减少启动时间
2. 缓存 — 系统提示词、工具 schema
3. 并行工具执行 — 独立工具并发执行
"""

import os
import sys
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed

# ═══════════════════════════════════════════════
# 缓存层
# ═══════════════════════════════════════════════

class CacheManager:
    """缓存管理器 — 避免重复计算"""

    def __init__(self):
        self._system_prompt_cache = None
        self._system_prompt_hash = None
        self._tool_schemas_cache = None
        self._tool_schemas_hash = None
        self._message_cache = {}

    def get_system_prompt(self, provider: str, model: str, build_fn) -> str:
        """缓存系统提示词"""
        cache_key = f"{provider}:{model}"
        current_hash = hashlib.md5(cache_key.encode()).hexdigest()

        if self._system_prompt_cache and self._system_prompt_hash == current_hash:
            return self._system_prompt_cache

        self._system_prompt_cache = build_fn()
        self._system_prompt_hash = current_hash
        return self._system_prompt_cache

    def get_tool_schemas(self, registry) -> List[Dict]:
        """缓存工具 schema"""
        schemas = registry.schemas
        current_hash = hashlib.md5(str(len(schemas)).encode()).hexdigest()

        if self._tool_schemas_cache and self._tool_schemas_hash == current_hash:
            return self._tool_schemas_cache

        self._tool_schemas_cache = schemas
        self._tool_schemas_hash = current_hash
        return self._tool_schemas_cache

    def clear(self):
        """清除所有缓存"""
        self._system_prompt_cache = None
        self._tool_schemas_cache = None
        self._message_cache.clear()


# ═══════════════════════════════════════════════
# 并行工具执行器
# ═══════════════════════════════════════════════

# 可以并行执行的工具（只读操作）
PARALLEL_SAFE_TOOLS = {
    "read_file", "search_files", "web_search", "web_extract",
    "list_directory", "file_info",
}

# 必须串行执行的工具（有副作用）
SERIAL_TOOLS = {
    "write_file", "patch", "terminal", "execute_code",
    "browser_navigate", "browser_click", "browser_type",
}


def can_parallelize(tool_calls: List[Dict]) -> bool:
    """判断工具调用是否可以并行"""
    if len(tool_calls) <= 1:
        return False
    # 所有工具都必须是安全的只读操作
    return all(
        tc.get("function", {}).get("name") in PARALLEL_SAFE_TOOLS
        for tc in tool_calls
    )


def execute_tools_parallel(tool_calls: List[Dict], execute_fn, max_workers: int = 3) -> List[str]:
    """并行执行工具调用"""
    results: List[str] = [""] * len(tool_calls)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(execute_fn, tc["function"]["name"], tc["function"]["arguments"]): i
            for i, tc in enumerate(tool_calls)
        }

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result() or ""
            except Exception as e:
                results[idx] = f"[工具执行错误: {e}]"

    return results


# ═══════════════════════════════════════════════
# 消息压缩器
# ═══════════════════════════════════════════════

class MessageCompressor:
    """智能消息压缩 — 保留关键信息，减少 token"""

    # 工具输出最大长度
    MAX_TOOL_OUTPUT = 2000
    # 保留最近 N 轮对话
    KEEP_RECENT_TURNS = 8

    @staticmethod
    def compress_tool_output(output: str) -> str:
        """压缩工具输出"""
        if len(output) <= MessageCompressor.MAX_TOOL_OUTPUT:
            return output
        # 保留头尾，中间用省略号
        half = MessageCompressor.MAX_TOOL_OUTPUT // 2
        return output[:half] + f"\n... [省略 {len(output) - MessageCompressor.MAX_TOOL_OUTPUT} 字符] ...\n" + output[-half:]

    @staticmethod
    def compress_messages(messages: List[Dict], keep_recent: int = None) -> List[Dict]:
        """压缩消息历史，保留系统消息和最近N轮"""
        if keep_recent is None:
            keep_recent = MessageCompressor.KEEP_RECENT_TURNS

        if len(messages) <= keep_recent * 2 + 1:
            return messages

        # 保留系统消息
        system_msgs = [m for m in messages if m["role"] == "system"]
        # 保留最近的消息
        recent_msgs = messages[-(keep_recent * 2):]

        return system_msgs + recent_msgs


# ═══════════════════════════════════════════════
# 快速响应检测
# ═══════════════════════════════════════════════

# 简单问题，不需要工具调用
SIMPLE_PATTERNS = [
    "什么是", "解释", "定义", "意思",
    "what is", "explain", "define",
]


def is_simple_query(query: str) -> bool:
    """判断是否为简单查询（不需要工具调用）"""
    query_lower = query.lower()
    # 短问题通常是简单的
    if len(query) < 50:
        return any(pattern in query_lower for pattern in SIMPLE_PATTERNS)
    return False


def get_fast_response_config() -> Dict:
    """获取快速响应配置"""
    return {
        "max_tokens": 500,
        "reasoning_effort": "low",
        "skip_tools": True,
    }


# ═══════════════════════════════════════════════
# 优化集成入口
# ═══════════════════════════════════════════════

# 全局缓存实例
_cache = CacheManager()


def get_cache() -> CacheManager:
    return _cache


def optimize_engine(engine):
    """优化引擎配置"""
    # 启用流式输出
    engine._use_streaming = True
    # 设置更小的工具输出限制
    return engine
