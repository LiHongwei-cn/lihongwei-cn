"""
蒙多的MCP Client实践 - 2026-06-11
演示如何连接和使用MCP Server

MCP Client可以：
1. 连接到MCP Server
2. 列出可用的工具、资源、提示
3. 调用工具执行操作
4. 读取资源获取数据
5. 使用提示模板
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    """MCP客户端主函数"""
    
    # 配置服务器参数（连接到我们的demo server）
    server_params = StdioServerParameters(
        command="python",
        args=["examples/mcp_server_demo.py"]
    )
    
    # 连接到服务器
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()
            
            print("✅ 已连接到MCP Server\n")
            
            # ============ 列出可用能力 ============
            
            # 列出工具
            tools = await session.list_tools()
            print("🔧 可用工具:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # 列出资源
            resources = await session.list_resources()
            print("\n📁 可用资源:")
            for resource in resources.resources:
                print(f"  - {resource.uri}")
            
            # 列出提示
            prompts = await session.list_prompts()
            print("\n💡 可用提示:")
            for prompt in prompts.prompts:
                print(f"  - {prompt.name}: {prompt.description}")
            
            # ============ 调用工具 ============
            
            print("\n" + "="*50)
            print("🔧 调用工具示例")
            print("="*50)
            
            # 调用计算工具
            result = await session.call_tool("calculate", {"expression": "2 + 3 * 4"})
            print(f"\n计算 2 + 3 * 4:")
            print(f"  结果: {result.content[0].text}")
            
            # 调用时间工具
            result = await session.call_tool("get_current_time", {})
            print(f"\n获取当前时间:")
            print(f"  结果: {result.content[0].text}")
            
            # 调用文本分析工具
            result = await session.call_tool("analyze_text", {
                "text": "MCP is a protocol for AI agents. It standardizes tool interactions."
            })
            print(f"\n分析文本:")
            print(f"  结果: {result.content[0].text}")
            
            # ============ 读取资源 ============
            
            print("\n" + "="*50)
            print("📁 读取资源示例")
            print("="*50)
            
            # 读取应用配置
            content, mime = await session.read_resource("config://app")
            print(f"\n应用配置:")
            print(f"  {content}")
            
            # 读取MCP文档
            content, mime = await session.read_resource("docs://mcp/tools")
            print(f"\nMCP Tools文档:")
            print(f"  {content}")
            
            # ============ 使用提示 ============
            
            print("\n" + "="*50)
            print("💡 使用提示示例")
            print("="*50)
            
            # 获取代码审查提示
            prompt = await session.get_prompt("code_review", {
                "code": "def hello():\n    print('Hello, MCP!')",
                "language": "python"
            })
            print(f"\n代码审查提示:")
            print(f"  {prompt.messages[0].content}")
            
            print("\n✅ MCP客户端演示完成！")


if __name__ == "__main__":
    asyncio.run(main())
