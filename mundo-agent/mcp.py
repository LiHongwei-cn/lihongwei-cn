"""蒙多 MCP 层 v2.0.8 — 皇帝的外交使团

Model Context Protocol 支持。让蒙多能连接外部工具服务器。
不是简单的 HTTP 调用。是结构化的工具发现、能力协商、生命周期管理。

设计哲学：
- 工具服务器是可替换的能力提供者
- 能力协商：服务器声明它能做什么，客户端按需使用
- 生命周期：连接 → 发现 → 调用 → 断开
- 错误隔离：一个服务器挂了不影响其他
"""

import json
import time
import uuid
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from pathlib import Path


@dataclass
class MCPServer:
    name: str
    url: str
    transport: str = "http"  # http / stdio
    capabilities: List[str] = field(default_factory=list)
    tools: List[Dict] = field(default_factory=list)
    connected: bool = False
    last_ping: float = 0
    error_count: int = 0
    metadata: Dict = field(default_factory=dict)


@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: Dict = field(default_factory=dict)
    server_name: str = ""

    def to_schema(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }


class MCPClient:
    """MCP 客户端 — 连接外部工具服务器"""

    def __init__(self):
        self._servers: Dict[str, MCPServer] = {}
        self._tools: Dict[str, MCPTool] = {}
        self._timeout = 30

    def add_server(self, name: str, url: str, transport: str = "http") -> MCPServer:
        server = MCPServer(name=name, url=url, transport=transport)
        self._servers[name] = server
        return server

    def remove_server(self, name: str) -> bool:
        server = self._servers.pop(name, None)
        if server:
            self._tools = {k: v for k, v in self._tools.items() if v.server_name != name}
            return True
        return False

    def connect(self, name: str) -> bool:
        server = self._servers.get(name)
        if not server:
            return False

        try:
            # 初始化握手
            response = self._send(server, "initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "mundo-agent", "version": "2.0.8"},
            })

            if response and "capabilities" in response:
                server.capabilities = list(response["capabilities"].keys())
                server.connected = True

                # 发现工具
                if "tools" in response.get("capabilities", {}):
                    self._discover_tools(server)

                return True
        except Exception as e:
            server.error_count += 1

        return False

    def connect_all(self) -> Dict[str, bool]:
        return {name: self.connect(name) for name in self._servers}

    def disconnect(self, name: str) -> None:
        server = self._servers.get(name)
        if server:
            server.connected = False
            self._tools = {k: v for k, v in self._tools.items() if v.server_name != name}

    def call_tool(self, tool_name: str, arguments: Dict) -> Optional[str]:
        tool = self._tools.get(tool_name)
        if not tool:
            return None

        server = self._servers.get(tool.server_name)
        if not server or not server.connected:
            return None

        try:
            response = self._send(server, "tools/call", {
                "name": tool.name,
                "arguments": arguments,
            })
            if response and "content" in response:
                parts = response["content"]
                return "".join(p.get("text", "") for p in parts if p.get("type") == "text")
        except Exception as e:
            server.error_count += 1

        return None

    def list_tools(self, server_name: str = "") -> List[MCPTool]:
        if server_name:
            return [t for t in self._tools.values() if t.server_name == server_name]
        return list(self._tools.values())

    def get_tool_schemas(self) -> List[Dict]:
        return [t.to_schema() for t in self._tools.values()]

    def is_mcp_tool(self, tool_name: str) -> bool:
        return tool_name in self._tools

    def servers(self) -> List[MCPServer]:
        return list(self._servers.values())

    def stats(self) -> Dict:
        connected = sum(1 for s in self._servers.values() if s.connected)
        return {
            "servers": len(self._servers),
            "connected": connected,
            "tools": len(self._tools),
        }

    def _discover_tools(self, server: MCPServer) -> None:
        try:
            response = self._send(server, "tools/list", {})
            if response and "tools" in response:
                for t in response["tools"]:
                    mcp_tool = MCPTool(
                        name=f"{server.name}__{t['name']}",
                        description=t.get("description", ""),
                        input_schema=t.get("inputSchema", {}),
                        server_name=server.name,
                    )
                    self._tools[mcp_tool.name] = mcp_tool
                    server.tools.append(t)
        except Exception:
            pass

    def _send(self, server: MCPServer, method: str, params: Dict) -> Optional[Dict]:
        if server.transport == "http":
            return self._send_http(server, method, params)
        return None

    def _send_http(self, server: MCPServer, method: str, params: Dict) -> Optional[Dict]:
        request_id = uuid.uuid4().hex[:8]
        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }).encode()

        req = urllib.request.Request(
            server.url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode())
                server.last_ping = time.time()
                if "result" in data:
                    return data["result"]
                if "error" in data:
                    server.error_count += 1
        except (urllib.error.URLError, TimeoutError, OSError):
            server.error_count += 1

        return None


# 全局单例
_mcp: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    global _mcp
    if _mcp is None:
        _mcp = MCPClient()
    return _mcp
