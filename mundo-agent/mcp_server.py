#!/usr/bin/env python3
"""MUNDO Agent MCP Server — 集成到 Cursor/Claude Code

通过 MCP 协议将 MUNDO Agent 暴露为工具服务器，
允许 Cursor、Claude Code 等客户端直接调用 MUNDO 的能力。

使用方式：
1. 在 Cursor 中添加 MCP 服务器配置
2. 通过 stdio 协议通信
3. 支持工具调用和资源访问
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加 MUNDO 到路径
MUNDO_DIR = Path(__file__).parent
sys.path.insert(0, str(MUNDO_DIR))

# MCP 协议常量
MCP_VERSION = "2024-11-05"
SERVER_NAME = "mundo-agent"
SERVER_VERSION = "2.0.9"


class MundoMCPServer:
    """MUNDO MCP 服务器"""

    def __init__(self):
        self.initialized = False
        self.mundo_engine = None
        self._init_mundo()

    def _init_mundo(self):
        """初始化 MUNDO 引擎"""
        try:
            from core import MundoEngine
            from setup import load_local_env, get_saved_provider, get_saved_model

            env = load_local_env()
            for k, v in env.items():
                os.environ.setdefault(k, v)

            provider = get_saved_provider() or "deepseek"
            model = get_saved_model()

            self.mundo_engine = MundoEngine(provider=provider, model=model)
        except Exception as e:
            print(f"Warning: Failed to initialize MUNDO engine: {e}", file=sys.stderr)
            self.mundo_engine = None

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理 MCP 请求"""
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")

        try:
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "tools/list":
                result = await self._handle_tools_list()
            elif method == "tools/call":
                result = await self._handle_tools_call(params)
            elif method == "resources/list":
                result = await self._handle_resources_list()
            elif method == "resources/read":
                result = await self._handle_resources_read(params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(e)}
            }

    async def _handle_initialize(self, params: Dict) -> Dict:
        """处理初始化请求"""
        self.initialized = True
        return {
            "protocolVersion": MCP_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False}
            },
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION
            }
        }

    async def _handle_tools_list(self) -> Dict:
        """返回可用工具列表"""
        tools = [
            {
                "name": "mundo_chat",
                "description": "Chat with MUNDO Agent. Send a message and get a response with tool execution.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The message to send to MUNDO"
                        },
                        "provider": {
                            "type": "string",
                            "description": "LLM provider (deepseek, openai, anthropic, etc.)",
                            "default": "deepseek"
                        }
                    },
                    "required": ["message"]
                }
            },
            {
                "name": "mundo_execute",
                "description": "Execute a task with MUNDO. MUNDO will plan, execute, and report results.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "The task to execute"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds",
                            "default": 90
                        }
                    },
                    "required": ["task"]
                }
            },
            {
                "name": "mundo_remember",
                "description": "Store a fact in MUNDO's memory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "The key to store the fact under"
                        },
                        "value": {
                            "type": "string",
                            "description": "The fact to remember"
                        }
                    },
                    "required": ["key", "value"]
                }
            },
            {
                "name": "mundo_recall",
                "description": "Retrieve a fact from MUNDO's memory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "The key to retrieve"
                        }
                    },
                    "required": ["key"]
                }
            },
            {
                "name": "mundo_status",
                "description": "Get MUNDO's current status and memory statistics",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
        return {"tools": tools}

    async def _handle_tools_call(self, params: Dict) -> Dict:
        """处理工具调用"""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if not self.mundo_engine:
            return {
                "content": [{"type": "text", "text": "MUNDO engine not initialized. Please check configuration."}],
                "isError": True
            }

        try:
            if tool_name == "mundo_chat":
                result = await self._tool_chat(arguments)
            elif tool_name == "mundo_execute":
                result = await self._tool_execute(arguments)
            elif tool_name == "mundo_remember":
                result = await self._tool_remember(arguments)
            elif tool_name == "mundo_recall":
                result = await self._tool_recall(arguments)
            elif tool_name == "mundo_status":
                result = await self._tool_status()
            else:
                result = f"Unknown tool: {tool_name}"

            return {
                "content": [{"type": "text", "text": result}],
                "isError": False
            }
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }

    async def _tool_chat(self, args: Dict) -> str:
        """聊天工具"""
        message = args.get("message", "")
        if not message:
            return "Error: message is required"

        # 在线程池中运行 MUNDO
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.mundo_engine.run, message)
        return result

    async def _tool_execute(self, args: Dict) -> str:
        """执行任务工具"""
        task = args.get("task", "")
        timeout = args.get("timeout", 90)

        if not task:
            return "Error: task is required"

        # 添加超时保护
        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self.mundo_engine.run, task),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            return f"Task timed out after {timeout} seconds"

    async def _tool_remember(self, args: Dict) -> str:
        """记忆工具"""
        key = args.get("key", "")
        value = args.get("value", "")

        if not key or not value:
            return "Error: key and value are required"

        # 使用 MUNDO 的记忆系统
        if hasattr(self.mundo_engine, 'memory') and self.mundo_engine.memory:
            self.mundo_engine.memory.save_fact(key, value)
            return f"Remembered: {key} = {value}"
        return "Memory system not available"

    async def _tool_recall(self, args: Dict) -> str:
        """回忆工具"""
        key = args.get("key", "")

        if not key:
            return "Error: key is required"

        if hasattr(self.mundo_engine, 'memory') and self.mundo_engine.memory:
            result = self.mundo_engine.memory.recall_fact(key)
            return result or f"No fact found for key: {key}"
        return "Memory system not available"

    async def _tool_status(self) -> str:
        """状态工具"""
        stats = {
            "version": SERVER_VERSION,
            "initialized": self.initialized,
            "engine_ready": self.mundo_engine is not None,
        }
        return json.dumps(stats, indent=2)

    async def _handle_resources_list(self) -> Dict:
        """返回可用资源列表"""
        return {
            "resources": [
                {
                    "uri": "mundo://status",
                    "name": "MUNDO Status",
                    "description": "Current status of MUNDO Agent",
                    "mimeType": "application/json"
                },
                {
                    "uri": "mundo://memory",
                    "name": "MUNDO Memory",
                    "description": "MUNDO's memory contents",
                    "mimeType": "application/json"
                }
            ]
        }

    async def _handle_resources_read(self, params: Dict) -> Dict:
        """读取资源"""
        uri = params.get("uri", "")

        if uri == "mundo://status":
            content = await self._tool_status()
        elif uri == "mundo://memory":
            content = "Memory access not implemented yet"
        else:
            content = f"Unknown resource: {uri}"

        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": content
                }
            ]
        }


async def main():
    """主函数 — 通过 stdio 处理 MCP 请求"""
    server = MundoMCPServer()

    # 读取 stdin 并处理请求
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        try:
            # 读取一行 JSON
            line = await reader.readline()
            if not line:
                break

            # 解析请求
            request = json.loads(line.decode().strip())

            # 处理请求
            response = await server.handle_request(request)

            # 发送响应
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            continue


if __name__ == "__main__":
    asyncio.run(main())
