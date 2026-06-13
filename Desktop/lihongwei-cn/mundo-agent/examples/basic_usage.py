#!/usr/bin/env python3
"""
MUNDO Agent 基本使用示例

本示例展示如何使用重构后的 MUNDO Agent 模块。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def example_tool_registry():
    """示例：使用工具注册表"""
    from mundo_agent.tools import registry, register_tool, ToolParameter

    # 注册自定义工具
    @register_tool(
        name="greet",
        description="打招呼",
        parameters=[
            ToolParameter("name", "string", "名字", required=True),
        ]
    )
    def greet(args):
        name = args.get("name", "World")
        return f"Hello, {name}!"

    # 使用工具
    result = registry.execute("greet", {"name": "MUNDO"})
    print(f"工具结果: {result}")

    # 列出所有工具
    print(f"已注册工具: {registry.names}")


def example_budget_control():
    """示例：使用预算控制"""
    from mundo_agent.core.budget import IterationBudget

    # 创建预算
    budget = IterationBudget(
        max_prompt_tokens=100000,
        max_completion_tokens=50000,
        max_turns=10,
        warn_threshold=0.8
    )

    # 模拟使用
    for i in range(5):
        budget.update(prompt_tokens=10000, completion_tokens=5000)
        print(f"轮次 {i+1}: 使用率 {budget.usage_ratio:.1%}, 剩余 {budget.remaining} tokens")

        if budget.should_warn:
            print("⚠️ 预算警告！")
            budget.mark_warned()

        if budget.exhausted:
            print("❌ 预算耗尽！")
            break


def example_memory_system():
    """示例：使用记忆系统"""
    from mundo_agent.memory import MundoMemory
    import tempfile

    # 使用临时数据库
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        memory = MundoMemory(db_path)

        # 记住事实
        memory.remember_fact("name", "MUNDO Agent")
        memory.remember_fact("version", "1.3.0")

        # 记住偏好
        memory.remember_preference("theme", "dark")
        memory.remember_preference("language", "zh-CN")

        # 回忆
        result = memory.recall("name")
        print(f"回忆结果: {result}")

        # 获取用户画像
        profile = memory.get_profile()
        print(f"用户画像: {profile}")

        # 获取统计
        stats = memory.get_stats()
        print(f"记忆统计: {stats['total_memories']} 条记忆")


def example_error_handling():
    """示例：错误处理"""
    from mundo_agent.utils.errors import (
        ToolError, MemoryError, format_error
    )

    # 捕获和格式化错误
    try:
        raise ToolError("terminal", "命令执行超时")
    except ToolError as e:
        print(f"捕获错误: {format_error(e)}")

    try:
        raise MemoryError("数据库连接失败", operation="init")
    except MemoryError as e:
        print(f"捕获错误: {format_error(e)}")


def example_context_compressor():
    """示例：上下文压缩"""
    from mundo_agent.core.compressor import ContextCompressor, CompressionConfig

    # 创建压缩器
    config = CompressionConfig(
        max_messages_before_compress=3,
        target_tokens=100,
        keep_recent_messages=2
    )
    compressor = ContextCompressor(config)

    # 创建测试消息
    messages = [
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "消息1" * 50},
        {"role": "assistant", "content": "回复1" * 50},
        {"role": "user", "content": "消息2"},
        {"role": "assistant", "content": "回复2"},
    ]

    # 估算 token
    tokens = compressor.estimate_tokens(messages)
    print(f"估算 token: {tokens}")

    # 压缩
    compressed = compressor.compress(messages)
    print(f"压缩前: {len(messages)} 条消息")
    print(f"压缩后: {len(compressed)} 条消息")


def main():
    """运行所有示例"""
    print("=" * 60)
    print("MUNDO Agent 重构示例")
    print("=" * 60)
    print()

    print("1. 工具注册表")
    print("-" * 40)
    example_tool_registry()
    print()

    print("2. 预算控制")
    print("-" * 40)
    example_budget_control()
    print()

    print("3. 记忆系统")
    print("-" * 40)
    example_memory_system()
    print()

    print("4. 错误处理")
    print("-" * 40)
    example_error_handling()
    print()

    print("5. 上下文压缩")
    print("-" * 40)
    example_context_compressor()
    print()

    print("=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()