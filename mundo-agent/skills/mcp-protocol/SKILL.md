---
name: mcp-protocol
description: MCP（Model Context Protocol）协议认知 — 蒙多的工具扩展之道
version: 1.0.0
author: mundo
tags:
  - mcp
  - protocol
  - tool-discovery
  - infrastructure
dependencies: []
conflicts: []
required_tools: []
priority: 80
---

# MCP 协议认知 Skill

## 核心概念

MCP（Model Context Protocol）是 Anthropic 于 2024年11月开源的协议，已成为 AI Agent 与外部工具交互的事实标准。

## 架构模型

```
Host（宿主应用，如蒙多）
  ↕ JSON-RPC 2.0
MCP Server（工具/数据源封装）
  ↕ 实际调用
外部系统（API、数据库、文件、浏览器...）
```

## 关键设计原则

1. **协议层解耦** — Agent 不直接调工具，通过标准化协议发现和调用
2. **Server 可组合** — 一个 Agent 可连多个 MCP Server，每个封装一类能力
3. **安全沙箱** — 权限控制在协议层，不在应用层
4. **能力发现** — Client 启动时自动发现 Server 提供的 tools/resources/prompts

## MCP Server 三类能力

| 类型 | 说明 | 示例 |
|------|------|------|
| **Tools** | 可调用的函数 | 搜索、数据库查询、文件操作 |
| **Resources** | 可读取的数据源 | 文件内容、API数据、数据库记录 |
| **Prompts** | 预定义的提示模板 | 代码审查模板、分析模板 |

## 蒙多接入路径

### 阶段一：认知（当前）
- 理解 MCP 协议架构
- 了解 JSON-RPC 2.0 通信方式
- 掌握 Server 能力发现机制

### 阶段二：实验
- 用 Python 写最小 MCP Server
- 实现 tools/resources/prompts 三类能力
- 测试与 Claude Desktop 的互操作

### 阶段三：集成
- 蒙多 tools.py 抽象为 MCP Host
- 第三方 MCP Server 直接可用
- 工具发现自动化，不再手动注册

## 与蒙多现有架构的映射

| MCP 概念 | 蒙多对应 | 差距 |
|----------|---------|------|
| Host | core.py 主循环 | 需要加 MCP Client |
| Server | tools.py 工具集 | 需要抽象为 MCP Server |
| Tools | ToolRegistry.register() | 接口兼容，需加协议层 |
| Resources | memory.py 记忆系统 | 可暴露为 MCP Resource |
| Prompts | MUNDO_SYSTEM_PROMPT | 可暴露为 MCP Prompt |

## 参考资料

- [MCP 官方文档](https://claude.com/docs/connectors/building/mcp)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP 完整指南 2026](https://dev.to/x4nent/complete-guide-to-mcp-model-context-protocol-in-2026-architecture-implementation-and-4a11)
