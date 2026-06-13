# 📖 每日学习笔记 — 2026-06-09

> **主题：AI Agent 生态现状 — 基础设施、框架大战、MCP协议**
> **与蒙多项目的关联度：★★★★★**

---

## 🔥 今日核心发现

### 1. MCP（Model Context Protocol）已成为事实标准

**来源：** dev.to / Claude.ai 官方文档 / neuralcoretech

Anthropic 在 2024年11月开源 MCP，**仅18个月就成为 AI Agent 与外部工具交互的事实标准**。

**核心架构：**
```
Client（宿主应用）
  ↕ JSON-RPC 2.0
MCP Server（工具/数据源封装）
  ↕ 实际调用
外部系统（API、数据库、文件、浏览器...）
```

**关键设计原则：**
- **协议层解耦**：Agent 不直接调工具，而是通过标准化协议发现和调用
- **Server 可组合**：一个 Agent 可以连多个 MCP Server，每个 Server 封装一类能力
- **安全沙箱**：权限控制在协议层，不在应用层

**对蒙多的启发：**
蒙多的 `tools.py`（41KB）目前是硬编码工具集。如果接入 MCP：
- 工具发现自动化（不需要手动注册）
- 第三方 MCP Server 直接可用
- 蒙多变成 MCP Host，能力无限扩展

---

### 2. 2026年 Agent 框架六国大战

**来源：** qubittool.com（2026-06-07 发布）

| 框架 | 开发商 | 核心特点 | MCP支持 | 适用场景 |
|------|--------|---------|---------|---------|
| **LangGraph** | LangChain | 图状态机、细粒度控制 | ✅ | 复杂工作流 |
| **CrewAI** | CrewAI Inc | 角色扮演、团队协作 | ✅ | 多Agent协作 |
| **AG2** | 原AutoGen | 对话式多Agent | ⚠️ | 研究/实验 |
| **Claude Agent SDK** | Anthropic | 与Claude深度集成 | ✅✅ | Claude生态 |
| **Strands Agents** | AWS | 企业级、云原生 | ✅ | AWS生态 |
| **OpenAI Agents SDK** | OpenAI | 轻量、与GPT集成 | ✅ | OpenAI生态 |

**关键趋势：**
- **MCP 成为必选项**：不支持 MCP 的框架在掉队
- **多Agent编排成为标配**：单Agent不够用了
- **可观测性**：Agent 的思考链路需要可追踪

**蒙多的定位分析：**
蒙多是自研编排系统，不依赖任何框架。优势是完全可控，劣势是维护成本高。
**建议**：保持核心自研，但考虑接入 MCP 作为工具层标准。

---

### 3. RAG 技术最新演进

**来源：** arxiv.org / Springer / ResearchGate（2025-2026 综述）

**RAG 不再只是"检索+生成"了。最新架构：**

```
传统 RAG: Query → Retrieve → Generate
                ↓
进阶 RAG: Query → Rewrite → Retrieve → Rerank → Compress → Generate
                ↓
Agentic RAG: Query → Plan → [Retrieve | Search | Calculate] → Synthesize → Validate → Generate
```

**关键进展：**
- **Agentic RAG**：Agent 自己决定什么时候检索、检索什么、怎么组合
- **Graph RAG**：用知识图谱替代纯向量检索，关系推理更强
- **Self-RAG**：模型自己判断"我需不需要检索"，减少无意义检索
- **多模态 RAG**：不只检索文本，还检索图片、表格、代码

**对蒙多的启发：**
蒙多的记忆系统（memory.py）目前是双层架构（事实+摘要）。可以升级：
- 加入向量检索（不只是关键词匹配）
- 用 Agentic RAG 的思路：让蒙多自己判断何时需要深度检索
- 记忆压缩：长对话自动提炼关键信息

---

## 🧠 深度思考：「Agent的Node.js时刻」与蒙多

你昨天读的文章核心观点：

> "我们需要的不是更多 Agent Demo，而是 Agent Infrastructure。"

**作者认为缺失的基础设施层：**
1. **可迁移性** — Agent 不能绑死在一个平台
2. **可组合性** — Agent 能力应该像 npm 包一样可插拔
3. **可观测性** — Agent 的决策过程必须可追踪
4. **可定制性** — 不同场景需要不同的 Agent 行为

**蒙多现在做到了哪些？**

| 缺失层 | 蒙多现状 | 差距 |
|--------|---------|------|
| 可迁移性 | ✅ 本地优先，跨平台脚本 | 接近，缺少容器化 |
| 可组合性 | ⚠️ Skills系统（基础） | 缺少标准化协议（MCP？） |
| 可观测性 | ⚠️ events.jsonl | 缺少结构化 trace |
| 可定制性 | ✅ 策略引擎可组合 | 已做得不错 |

**蒙多其实已经在往正确的方向走。** 关键下一步：
1. 接入 MCP 协议 → 工具层标准化
2. 结构化 trace → 每次推理链路可回放
3. Skills 打包标准 → 可分享、可复用

---

## 📝 今日学习清单

- [x] 了解 MCP 协议架构与生态现状
- [x] 对比 2026 六大 Agent 框架
- [x] 理解 RAG 技术最新演进（Agentic RAG / Graph RAG）
- [x] 将技术趋势与蒙多项目做关联分析
- [ ] **实践任务**：研究 MCP Python SDK，画出蒙多接入方案草图
- [ ] **阅读延伸**：读完「Agent需要它的Node.js时刻」全文

---

## 🎯 明日学习方向

1. **MCP 实践**：用 Python 写一个最小 MCP Server，理解协议细节
2. **LangGraph 源码**：读它的状态图设计，和蒙多的策略引擎对比
3. **Agentic RAG 论文**：精读 arxiv 2506.00054，提取可落地的思路

---

## 📚 参考资料

- [MCP 完整指南 2026](https://dev.to/x4nent/complete-guide-to-mcp-model-context-protocol-in-2026-architecture-implementation-and-4a11)
- [2026 AI Agent 框架对比](https://qubittool.com/blog/ai-agent-framework-comparison-2026)
- [RAG 综述 arxiv](https://arxiv.org/html/2506.00054v1)
- [MIT AI Agent Index 2025](https://aiagentindex.mit.edu/data/2025-AI-Agent-Index.pdf)
- [Strands Agents (AWS)](https://strandsagents.com/)

---

*蒙多学习了。蒙多记录了。蒙多变强了。*
