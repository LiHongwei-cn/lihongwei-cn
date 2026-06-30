"""蒙多 MCP 服务端 v3.0.0 — 帝皇的使馆

让蒙多自身成为 MCP Server，外部工具/Agent 可通过标准 MCP 协议调用蒙多的能力。
与现有 MCPClient（连接外部服务器）互补，实现双向互操作。

协议：MCP 2024-11-05
传输：HTTP Streamable（兼容 stdio 未来扩展）
"""

import json
import time
import uuid
import threading
from dataclasses import dataclass, field
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Callable, Dict, List, Optional
from pathlib import Path


# ═══════════════════════════════════════════════
# MCP 工具定义
# ═══════════════════════════════════════════════

@dataclass
class MCPToolDef:
    """MCP 工具定义"""
    name: str
    description: str
    input_schema: Dict = field(default_factory=dict)
    handler: Optional[Callable] = None

    def to_mcp_schema(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


# ═══════════════════════════════════════════════
# MCP Server
# ═══════════════════════════════════════════════

class MCPServer:
    """MCP 服务端 — 让蒙多的能力通过标准协议对外暴露"""

    PROTOCOL_VERSION = "2024-11-05"
    SERVER_NAME = "mundo-agent"
    SERVER_VERSION = "3.0.0"

    def __init__(self, host: str = "127.0.0.1", port: int = 3100):
        self._host = host
        self._port = port
        self._tools: Dict[str, MCPToolDef] = {}
        self._resources: Dict[str, Dict] = {}
        self._prompts: Dict[str, Dict] = {}
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._request_count = 0
        self._start_time = 0.0

        # 注册内置工具
        self._register_builtin_tools()

    def register_tool(self, name: str, description: str,
                      input_schema: Dict, handler: Callable):
        """注册对外暴露的工具"""
        self._tools[name] = MCPToolDef(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler,
        )

    def register_resource(self, uri: str, name: str, description: str,
                          mime_type: str = "text/plain"):
        """注册资源"""
        self._resources[uri] = {
            "uri": uri,
            "name": name,
            "description": description,
            "mimeType": mime_type,
        }

    def register_prompt(self, name: str, description: str,
                        arguments: Optional[List[Dict]] = None):
        """注册提示词模板"""
        self._prompts[name] = {
            "name": name,
            "description": description,
            "arguments": arguments or [],
        }

    def list_tools(self) -> List[Dict]:
        """列出所有已注册工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self._tools.values()
        ]

    def start(self, background: bool = True):
        """启动 MCP Server"""
        if self._running:
            return

        handler = self._create_handler()
        self._server = HTTPServer((self._host, self._port), handler)
        self._running = True
        self._start_time = time.time()

        if background:
            self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
            self._thread.start()
        else:
            self._server.serve_forever()

    def stop(self):
        """停止 MCP Server"""
        if self._server:
            self._shutdown_server_safely()
            self._running = False

    def _shutdown_server_safely(self):
        try:
            self._server.shutdown()
        except Exception:
            pass

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def url(self) -> str:
        return f"http://{self._host}:{self._port}"

    def stats(self) -> Dict:
        return {
            "running": self._running,
            "url": self.url,
            "tools": len(self._tools),
            "resources": len(self._resources),
            "prompts": len(self._prompts),
            "requests": self._request_count,
            "uptime_seconds": time.time() - self._start_time if self._start_time else 0,
        }

    def _register_builtin_tools(self):
        """注册蒙多核心能力作为 MCP 工具"""

        # 代码分析工具
        self.register_tool(
            name="mundo_analyze_code",
            description="分析代码文件的结构、依赖和质量",
            input_schema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "要分析的文件路径"},
                    "analysis_type": {
                        "type": "string",
                        "enum": ["structure", "dependencies", "quality", "all"],
                        "default": "all",
                    },
                },
                "required": ["file_path"],
            },
            handler=self._tool_analyze_code,
        )

        # 知识检索工具
        self.register_tool(
            name="mundo_search_knowledge",
            description="从蒙多知识库中检索相关信息",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索查询"},
                    "top_k": {"type": "integer", "default": 5, "description": "返回结果数量"},
                    "category": {"type": "string", "default": "", "description": "限定类别"},
                },
                "required": ["query"],
            },
            handler=self._tool_search_knowledge,
        )

        # 记忆操作工具
        self.register_tool(
            name="mundo_memory",
            description="操作蒙多的三层记忆系统",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["remember", "recall", "stats"],
                        "description": "操作类型",
                    },
                    "content": {"type": "string", "description": "记忆内容（remember 时必填）"},
                    "query": {"type": "string", "description": "检索查询（recall 时必填）"},
                    "layer": {
                        "type": "string",
                        "enum": ["short", "mid", "long"],
                        "default": "short",
                    },
                },
                "required": ["action"],
            },
            handler=self._tool_memory,
        )

        # 任务规划工具
        self.register_tool(
            name="mundo_plan_task",
            description="使用蒙多的任务规划器分解复杂任务",
            input_schema={
                "type": "object",
                "properties": {
                    "task_description": {"type": "string", "description": "任务描述"},
                    "constraints": {"type": "string", "default": "", "description": "约束条件"},
                },
                "required": ["task_description"],
            },
            handler=self._tool_plan_task,
        )

    # ── 内置工具实现 ──

    def _tool_analyze_code(self, args: Dict) -> Dict:
        file_path = args.get("file_path", "")
        analysis_type = args.get("analysis_type", "all")

        try:
            from pathlib import Path as P
            p = P(file_path)
            if not p.exists():
                return {"error": f"文件不存在: {file_path}"}

            content = p.read_text(encoding="utf-8")
            lines = content.split("\n")

            result = {
                "file": file_path,
                "lines": len(lines),
                "chars": len(content),
            }

            if analysis_type in ("structure", "all"):
                classes = [l.strip() for l in lines if l.strip().startswith("class ")]
                functions = [l.strip() for l in lines if l.strip().startswith("def ")]
                result["structure"] = {
                    "classes": classes[:20],
                    "functions": functions[:30],
                }

            if analysis_type in ("dependencies", "all"):
                imports = [l.strip() for l in lines if l.strip().startswith(("import ", "from "))]
                result["dependencies"] = imports[:30]

            if analysis_type in ("quality", "all"):
                empty_lines = sum(1 for l in lines if not l.strip())
                comment_lines = sum(1 for l in lines if l.strip().startswith("#"))
                result["quality"] = {
                    "empty_lines": empty_lines,
                    "comment_lines": comment_lines,
                    "comment_ratio": round(comment_lines / max(len(lines), 1), 3),
                }

            return result
        except Exception as e:
            return {"error": str(e)}

    def _tool_search_knowledge(self, args: Dict) -> Dict:
        query = args.get("query", "")
        top_k = args.get("top_k", 5)
        category = args.get("category", "")

        try:
            from knowledge_retriever import get_knowledge_retriever
            retriever = get_knowledge_retriever()
            results = retriever.search(query, top_k=top_k, category=category)

            return {
                "query": query,
                "results": [
                    {
                        "content": r.chunk.content[:500],
                        "source": r.chunk.source,
                        "category": r.chunk.category,
                        "score": round(r.score, 4),
                    }
                    for r in results
                ],
                "total": len(results),
            }
        except Exception as e:
            return {"error": str(e)}

    def _tool_memory(self, args: Dict) -> Dict:
        action = args.get("action", "stats")

        try:
            from memory import MundoMemory
            from constants import MEMORY_DB
            memory = MundoMemory(MEMORY_DB)

            if action == "remember":
                content = args.get("content", "")
                layer = args.get("layer", "short")
                if layer == "short":
                    memory.store_short("mcp_input", content)
                elif layer == "mid":
                    memory.store_mid("mcp_input", content, "mcp")
                elif layer == "long":
                    memory.store_long("mcp_input", content, "mcp")
                return {"action": "remembered", "layer": layer}

            elif action == "recall":
                query = args.get("query", "")
                results = memory.recall(query)
                return {"action": "recall", "results": results[:10]}

            else:  # stats
                stats = memory.get_stats()
                return {"action": "stats", **stats}

        except Exception as e:
            return {"error": str(e)}

    def _tool_plan_task(self, args: Dict) -> Dict:
        task = args.get("task_description", "")

        try:
            from task_planner import TaskPlanner
            planner = TaskPlanner()
            plan = planner.generate_plan(task)
            return {"task": task, "plan": plan}
        except Exception as e:
            return {"error": str(e)}

    def _create_handler(self):
        """动态创建 HTTP 请求处理器"""
        server_ref = self

        class MCPHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # 静默日志

            def do_POST(self):
                server_ref._request_count += 1
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)

                try:
                    request = json.loads(body.decode("utf-8"))
                    response = server_ref._handle_jsonrpc(request)
                    self._send_json(200, response)
                except json.JSONDecodeError:
                    self._send_json(400, {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None})
                except Exception as e:
                    self._send_json(500, {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": None})

            def do_GET(self):
                if self.path == "/health":
                    self._send_json(200, {"status": "ok", "server": "mundo-mcp"})
                elif self.path == "/stats":
                    self._send_json(200, server_ref.stats())
                else:
                    self._send_json(404, {"error": "not found"})

            def _send_json(self, status: int, data: Dict):
                response = json.dumps(data, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response)

        return MCPHandler

    def _handle_jsonrpc(self, request: Dict) -> Dict:
        """处理 JSON-RPC 2.0 请求"""
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")

        handlers = {
            "initialize": self._rpc_initialize,
            "tools/list": self._rpc_tools_list,
            "tools/call": self._rpc_tools_call,
            "resources/list": self._rpc_resources_list,
            "resources/read": self._rpc_resources_read,
            "prompts/list": self._rpc_prompts_list,
            "prompts/get": self._rpc_prompts_get,
            "ping": self._rpc_ping,
        }

        handler = handlers.get(method)
        if not handler:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method not found: {method}"},
                "id": req_id,
            }

        try:
            result = handler(params)
            return {"jsonrpc": "2.0", "result": result, "id": req_id}
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
                "id": req_id,
            }

    def _rpc_initialize(self, params: Dict) -> Dict:
        return {
            "protocolVersion": self.PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
                "prompts": {"listChanged": False},
            },
            "serverInfo": {
                "name": self.SERVER_NAME,
                "version": self.SERVER_VERSION,
            },
        }

    def _rpc_tools_list(self, params: Dict) -> Dict:
        return {"tools": [t.to_mcp_schema() for t in self._tools.values()]}

    def _rpc_tools_call(self, params: Dict) -> Dict:
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        tool = self._tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        if not tool.handler:
            raise ValueError(f"Tool has no handler: {tool_name}")

        result = tool.handler(arguments)

        return {
            "content": [
                {"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}
            ]
        }

    def _rpc_resources_list(self, params: Dict) -> Dict:
        return {"resources": list(self._resources.values())}

    def _rpc_resources_read(self, params: Dict) -> Dict:
        uri = params.get("uri", "")
        resource = self._resources.get(uri)
        if not resource:
            raise ValueError(f"Resource not found: {uri}")
        return {"contents": [{"uri": uri, "text": resource.get("description", "")}]}

    def _rpc_prompts_list(self, params: Dict) -> Dict:
        return {"prompts": list(self._prompts.values())}

    def _rpc_prompts_get(self, params: Dict) -> Dict:
        name = params.get("name", "")
        prompt = self._prompts.get(name)
        if not prompt:
            raise ValueError(f"Prompt not found: {name}")
        return {"messages": [{"role": "user", "content": {"type": "text", "text": prompt.get("description", "")}}]}

    def _rpc_ping(self, params: Dict) -> Dict:
        return {"pong": True, "timestamp": time.time()}


# ═══════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════

_mcp_server: Optional[MCPServer] = None


def get_mcp_server(host: str = "127.0.0.1", port: int = 3100) -> MCPServer:
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer(host=host, port=port)
    return _mcp_server
