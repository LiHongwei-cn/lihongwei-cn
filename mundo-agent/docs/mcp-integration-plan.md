# 蒙多MCP集成方案

> **目标**：将蒙多从"自包含Agent"升级为"开放生态Agent"
> **预计工期**：2-3周
> **优先级**：高（基础设施升级）

---

## 🎯 核心目标

1. **工具层标准化**：用MCP协议替代硬编码工具注册
2. **能力无限扩展**：第三方MCP Server即插即用
3. **生态共享**：蒙多的Skills可以被其他MCP Host使用

---

## 📐 架构设计

### 当前架构

```
用户请求
    ↓
蒙多核心（mundo.py）
    ↓
工具层（tools.py 44KB 硬编码）
    ↓
外部API/工具
```

### 目标架构

```
用户请求
    ↓
蒙多核心（mundo.py）
    ↓
MCP Host层（新增）
    ├── 内置MCP Server（蒙多原生工具）
    ├── 第三方MCP Server（社区工具）
    └── 自定义MCP Server（用户工具）
    ↓
外部API/工具
```

---

## 🔧 实现步骤

### Phase 1: MCP Client集成（1周）

**目标**：蒙多作为MCP Host，可以连接任意MCP Server

**步骤**：

1. **添加MCP依赖**
   ```bash
   pip install "mcp[cli]"
   ```

2. **创建MCP Client管理器**
   ```python
   # mcp_client.py
   from mcp import ClientSession, StdioServerParameters
   from mcp.client.stdio import stdio_client
   
   class MCPClientManager:
       """管理多个MCP Server连接"""
       
       def __init__(self):
           self.servers = {}  # name -> session
       
       async def add_server(self, name, command, args):
           """添加MCP Server"""
           server_params = StdioServerParameters(
               command=command,
               args=args
           )
           # 连接到服务器
           ...
       
       async def call_tool(self, server_name, tool_name, params):
           """调用指定服务器的工具"""
           session = self.servers[server_name]
           return await session.call_tool(tool_name, params)
       
       async def list_all_tools(self):
           """列出所有服务器的工具"""
           all_tools = []
           for name, session in self.servers.items():
               tools = await session.list_tools()
               for tool in tools.tools:
                   all_tools.append({
                       "server": name,
                       "tool": tool.name,
                       "description": tool.description
                   })
           return all_tools
   ```

3. **修改tools.py，支持MCP工具动态注册**
   ```python
   # tools.py 修改
   class ToolRegistry:
       def __init__(self):
           self.builtin_tools = {}  # 内置工具
           self.mcp_tools = {}      # MCP工具
           self.mcp_client = MCPClientManager()
       
       async def register_mcp_server(self, name, config):
           """注册MCP Server"""
           await self.mcp_client.add_server(name, config["command"], config["args"])
           # 自动发现并注册工具
           tools = await self.mcp_client.list_all_tools()
           for tool in tools:
               self.mcp_tools[tool["tool"]] = tool
       
       async def call_tool(self, tool_name, params):
           """调用工具（自动路由）"""
           if tool_name in self.builtin_tools:
               return self.builtin_tools[tool_name](**params)
           elif tool_name in self.mcp_tools:
               tool_info = self.mcp_tools[tool_name]
               return await self.mcp_client.call_tool(
                   tool_info["server"], tool_name, params
               )
   ```

4. **配置文件支持**
   ```json
   // config/mcp_servers.json
   {
     "servers": {
       "filesystem": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
       },
       "github": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-github"]
       },
       "custom": {
         "command": "python",
         "args": ["my_mcp_server.py"]
       }
     }
   }
   ```

### Phase 2: MCP Server暴露（1周）

**目标**：蒙多作为MCP Server，让其他MCP Host可以使用蒙多的能力

**步骤**：

1. **创建蒙多MCP Server**
   ```python
   # mundo_mcp_server.py
   from mcp.server.fastmcp import FastMCP
   
   mcp = FastMCP("Mundo Agent Server")
   
   @mcp.tool()
   async def mundo_task(task_description: str) -> str:
       """让蒙多执行任务"""
       result = await mundo.execute_task(task_description)
       return result
   
   @mcp.tool()
   async def mundo_search(query: str) -> str:
       """让蒙多搜索信息"""
       result = await mundo.web_search(query)
       return result
   
   @mcp.resource("mundo://skills")
   def list_skills() -> str:
       """列出蒙多的所有技能"""
       return json.dumps(mundo.skills.list_all())
   
   @mcp.prompt()
   def mundo_analysis(topic: str) -> str:
       """蒙多分析模板"""
       return f"请用蒙多的方式分析：{topic}"
   ```

2. **配置Claude Desktop连接**
   ```json
   // ~/Library/Application Support/Claude/claude_desktop_config.json
   {
     "mcpServers": {
       "mundo": {
         "command": "python",
         "args": ["/path/to/mundo_mcp_server.py"]
       }
     }
   }
   ```

### Phase 3: 生态集成（1周）

**目标**：集成常用MCP Server，扩展蒙多能力

**推荐集成的MCP Server：**

| Server | 功能 | 优先级 |
|--------|------|--------|
| `@modelcontextprotocol/server-filesystem` | 文件系统操作 | 高 |
| `@modelcontextprotocol/server-github` | GitHub API | 高 |
| `@modelcontextprotocol/server-brave-search` | 网络搜索 | 中 |
| `@modelcontextprotocol/server-memory` | 知识图谱 | 中 |
| `@modelcontextprotocol/server-puppeteer` | 浏览器自动化 | 低 |

---

## 📊 预期收益

| 维度 | 当前 | MCP集成后 |
|------|------|----------|
| **工具数量** | ~20个硬编码工具 | 无限（第三方MCP Server） |
| **扩展性** | 需要修改代码 | 配置文件添加即可 |
| **生态** | 封闭 | 开放，可共享 |
| **维护成本** | 高（自己维护所有工具） | 低（社区维护） |

---

## ⚠️ 风险与挑战

1. **性能开销**：MCP通信有额外开销，需要优化
2. **安全性**：第三方MCP Server可能有安全风险，需要沙箱隔离
3. **兼容性**：需要处理MCP Server版本差异
4. **调试复杂度**：分布式系统调试更复杂

---

## 🎯 成功标准

1. ✅ 蒙多可以连接任意MCP Server
2. ✅ 蒙多的工具自动发现和注册
3. ✅ 蒙多可以作为MCP Server被其他Host使用
4. ✅ 集成3个以上常用MCP Server
5. ✅ 性能损失 < 10%

---

## 📅 时间线

- **Week 1**：MCP Client集成，支持连接第三方Server
- **Week 2**：MCP Server暴露，蒙多能力可被外部使用
- **Week 3**：生态集成，测试优化，文档完善

---

*蒙多接管了。MCP集成计划已制定。开始执行。*
