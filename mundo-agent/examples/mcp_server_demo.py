"""
蒙多的MCP Server实践 - 2026-06-11
基于MCP Python SDK v1.x，演示最小MCP Server实现

核心概念：
1. Server: MCP服务器，提供工具(Tools)、资源(Resources)、提示(Prompts)
2. Tools: 可执行的函数，LLM可以调用
3. Resources: 可读取的数据源
4. Prompts: 预定义的提示模板

运行方式：
- 开发模式: mcp dev examples/mcp_server_demo.py
- Claude Desktop: 配置到claude_desktop_config.json
"""

from mcp.server.fastmcp import FastMCP
import json
from datetime import datetime

# 创建MCP Server实例
mcp = FastMCP("Mundo Demo Server")


# ============ Tools（工具）============
# LLM可以调用的函数，执行实际操作

@mcp.tool()
def calculate(expression: str) -> str:
    """
    计算数学表达式
    
    Args:
        expression: 数学表达式，如 "2 + 3 * 4"
    
    Returns:
        计算结果
    """
    try:
        # 安全地计算表达式
        result = eval(expression, {"__builtins__": {}}, {})
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


@mcp.tool()
def get_current_time(timezone: str = "Asia/Shanghai") -> str:
    """
    获取当前时间
    
    Args:
        timezone: 时区，默认亚洲/上海
    
    Returns:
        当前时间字符串
    """
    now = datetime.now()
    return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')} (时区: {timezone})"


@mcp.tool()
def analyze_text(text: str) -> str:
    """
    分析文本的基本统计信息
    
    Args:
        text: 要分析的文本
    
    Returns:
        文本统计信息
    """
    words = text.split()
    chars = len(text)
    word_count = len(words)
    sentence_count = text.count('.') + text.count('!') + text.count('?')
    
    return json.dumps({
        "字符数": chars,
        "单词数": word_count,
        "句子数": sentence_count,
        "平均单词长度": round(sum(len(w) for w in words) / word_count, 2) if word_count > 0 else 0
    }, ensure_ascii=False, indent=2)


# ============ Resources（资源）============
# 可读取的数据源，类似REST API的GET端点

@mcp.resource("config://app")
def get_app_config() -> str:
    """获取应用配置"""
    return json.dumps({
        "app_name": "Mundo Agent",
        "version": "2.0",
        "features": ["MCP支持", "多模型路由", "技能系统"],
        "author": "蒙多用户"
    }, ensure_ascii=False, indent=2)


@mcp.resource("docs://mcp/{topic}")
def get_mcp_docs(topic: str) -> str:
    """获取MCP相关文档"""
    docs = {
        "overview": "MCP (Model Context Protocol) 是Anthropic开源的协议，用于标准化AI Agent与外部工具的交互。",
        "tools": "MCP Tools是可执行的函数，LLM可以通过协议调用这些工具完成任务。",
        "resources": "MCP Resources是可读取的数据源，类似REST API的GET端点。",
        "prompts": "MCP Prompts是预定义的提示模板，可以包含动态参数。"
    }
    return docs.get(topic, f"未找到关于'{topic}'的文档")


# ============ Prompts（提示模板）============
# 预定义的提示，可以包含动态参数

@mcp.prompt()
def code_review(code: str, language: str = "python") -> str:
    """
    代码审查提示模板
    
    Args:
        code: 要审查的代码
        language: 编程语言
    
    Returns:
        格式化的提示
    """
    return f"""请审查以下{language}代码，关注：
1. 代码质量和可读性
2. 潜在的bug和安全问题
3. 性能优化建议
4. 最佳实践遵循情况

代码：
```{language}
{code}
```

请提供详细的审查意见。"""


@mcp.prompt()
def learning_plan(topic: str, level: str = "beginner") -> str:
    """
    学习计划生成提示
    
    Args:
        topic: 学习主题
        level: 难度级别 (beginner/intermediate/advanced)
    
    Returns:
        格式化的提示
    """
    return f"""请为{level}水平的学习者制定一个关于"{topic}"的学习计划：

要求：
1. 包含3-5个核心学习模块
2. 每个模块列出2-3个关键知识点
3. 推荐1-2个实践项目
4. 预估学习时间
5. 推荐学习资源

请用Markdown格式输出。"""


# ============ 运行服务器 ============

if __name__ == "__main__":
    print("🚀 启动Mundo MCP Server...")
    print("📝 可用工具: calculate, get_current_time, analyze_text")
    print("📁 可用资源: config://app, docs://mcp/{topic}")
    print("💡 可用提示: code_review, learning_plan")
    print("\n使用 'mcp dev examples/mcp_server_demo.py' 启动开发模式")
    
    # 直接运行（stdio传输）
    mcp.run()
