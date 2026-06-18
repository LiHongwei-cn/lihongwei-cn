"""MCP Server 单元测试"""

import pytest
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMCPServerCore:
    """MCPServer 核心功能测试"""

    def test_server_creation(self):
        from mcp_server import MCPServer
        server = MCPServer(host="127.0.0.1", port=0)
        assert server.is_running is False
        assert "tools" in server.stats()

    def test_register_tool(self):
        from mcp_server import MCPServer
        server = MCPServer(port=0)

        def handler(args):
            return {"result": "ok"}

        server.register_tool(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {}},
            handler=handler,
        )

        assert "test_tool" in server._tools

    def test_register_resource(self):
        from mcp_server import MCPServer
        server = MCPServer(port=0)
        server.register_resource(
            uri="file:///test",
            name="test_resource",
            description="A test resource",
        )
        assert "file:///test" in server._resources

    def test_register_prompt(self):
        from mcp_server import MCPServer
        server = MCPServer(port=0)
        server.register_prompt(
            name="test_prompt",
            description="A test prompt",
        )
        assert "test_prompt" in server._prompts

    def test_builtin_tools_registered(self):
        from mcp_server import MCPServer
        server = MCPServer(port=0)
        tool_names = list(server._tools.keys())
        assert "mundo_analyze_code" in tool_names
        assert "mundo_search_knowledge" in tool_names
        assert "mundo_memory" in tool_names
        assert "mundo_plan_task" in tool_names


class TestMCPServerProtocol:
    """MCP 协议层测试"""

    def test_initialize(self):
        from mcp_server import MCPServer
        server = MCPServer(port=0)

        result = server._handle_jsonrpc({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        })

        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 1
        assert "result" in result
        assert result["result"]["protocolVersion"] == "2024-11-05"
        assert "capabilities" in result["result"]
        assert "serverInfo" in result["result"]

    def test_tools_list(self):
        from mcp_server import MCPServer
        server = MCPServer(port=0)

        result = server._handle_jsonrpc({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        })

        tools = result["result"]["tools"]
        assert len(tools) > 0
        assert all("name" in t for t in tools)
        assert all("description" in t for t in tools)
        assert all("inputSchema" in t for t in tools)

    def test_tools_call(self):
        from mcp_server import MCPServer
        server = MCPServer(port=0)

        result = server._handle_jsonrpc({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "mundo_analyze_code",
                "arguments": {"file_path": str(Path(__file__).parent.parent / "constants.py")},
            },
        })

        assert "result" in result
        content = result["result"]["content"]
        assert len(content) > 0
        assert content[0]["type"] == "text"

    def test_tools_call_not_found(self):
        from mcp_server import MCPServer
        server = MCPServer(port=0)

        result = server._handle_jsonrpc({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "nonexistent_tool", "arguments": {}},
        })

        assert "error" in result
        assert result["error"]["code"] == -32603

    def test_unknown_method(self):
        from mcp_server import MCPServer
        server = MCPServer(port=0)

        result = server._handle_jsonrpc({
            "jsonrpc": "2.0",
            "id": 5,
            "method": "unknown/method",
            "params": {},
        })

        assert "error" in result
        assert result["error"]["code"] == -32601

    def test_ping(self):
        from mcp_server import MCPServer
        server = MCPServer(port=0)

        result = server._handle_jsonrpc({
            "jsonrpc": "2.0",
            "id": 6,
            "method": "ping",
            "params": {},
        })

        assert result["result"]["pong"] is True

    def test_resources_list(self):
        from mcp_server import MCPServer
        server = MCPServer(port=0)
        server.register_resource("test://uri", "test", "desc")

        result = server._handle_jsonrpc({
            "jsonrpc": "2.0",
            "id": 7,
            "method": "resources/list",
            "params": {},
        })

        resources = result["result"]["resources"]
        assert len(resources) > 0

    def test_prompts_list(self):
        from mcp_server import MCPServer
        server = MCPServer(port=0)
        server.register_prompt("test_prompt", "desc")

        result = server._handle_jsonrpc({
            "jsonrpc": "2.0",
            "id": 8,
            "method": "prompts/list",
            "params": {},
        })

        prompts = result["result"]["prompts"]
        assert len(prompts) > 0


class TestMCPServerHTTP:
    """HTTP 传输层测试"""

    def test_start_and_stop(self):
        from mcp_server import MCPServer
        server = MCPServer(host="127.0.0.1", port=13999)
        server.start(background=True)
        assert server.is_running is True

        stats = server.stats()
        assert stats["running"] is True
        assert "13999" in stats.get("url", "")

        server.stop()
        assert server.is_running is False

    def test_health_endpoint(self):
        from mcp_server import MCPServer
        server = MCPServer(host="127.0.0.1", port=14000)
        server.start(background=True)

        try:
            req = urllib.request.Request("http://127.0.0.1:14000/health")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                assert data["status"] == "ok"
        finally:
            server.stop()
