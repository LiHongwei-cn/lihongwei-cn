# 👑 MUNDO Agent v2.2.7

**我是蒙多！蒙多想去哪就去哪！**

独立 AI 智能体框架 · 30+ 模型 · 向量检索 · 评估框架 · MCP 互操作 · 可观测性 · 任务分析

---

## ✨ 核心特性

- **30+ AI 模型** — DeepSeek、MiMo、Qwen、Claude、GPT-5.5、Gemini 等全覆盖
- **反射循环引擎** — THINK → EXECUTE → REFLECT → REPAIR 四阶段，引用 Reflexion/ReAct 论文
- **三层记忆系统** — 短期（会话级）、中期（项目级 30 天衰减）、长期（永久级 + 冲突检测）
- **混合检索 RAG** — ChromaDB 向量 + BM25 + 语义哈希三路融合，自动降级
- **任务分析引擎** — 自动分类任务类型、解析 Markdown 文档、提取需求/约束/验收标准
- **MCP 互操作** — Client + Server 双向协议，蒙多能力通过标准 MCP 对外暴露
- **评估框架** — 多维度量化（任务完成率、步骤效率、工具准确率），内置评估用例
- **可观测性** — 结构化日志、分布式追踪（OpenTelemetry 兼容）、指标采集
- **安全强化** — 五层纵深防御（输入验证/输出过滤/权限边界/审计追踪/注入防护）
- **智能错误恢复** — 错误分类 + 自适应恢复策略 + 断路器熔断

---

## 📦 安装

### macOS

```bash
# 下载最新版
gh release download v2.2.7 -R LiHongwei-cn/mundo-agent -p "mundo-v2.2.7-macos.zip"

# 解压到安装目录
unzip mundo-v2.2.7-macos.zip -d ~/.hermes/mundo-agent

# 运行
python3 ~/.hermes/mundo-agent/mundo.py
```

### Docker

```bash
docker-compose up -d
```

### 从源码安装

```bash
git clone https://github.com/LiHongwei-cn/mundo-agent.git
cd mundo-agent
pip install -r requirements.txt
python3 setup.py
python3 mundo.py
```

---

## 🏗️ 架构

```
┌─────────────────────────────────────────────────┐
│                   MundoEngine                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ 反射循环  │ │ 任务分析  │ │   任务规划器      │ │
│  │THINK→    │ │分类/解析  │ │  分析→拆分→推荐   │ │
│  │EXECUTE→  │ │需求提取   │ │                  │ │
│  │REFLECT→  │ │子任务拆解 │ │                  │ │
│  │REPAIR    │ │          │ │                  │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ 三层记忆  │ │ 混合检索  │ │   多模型适配      │ │
│  │短/中/长期 │ │BM25+向量 │ │ DeepSeek/Claude/ │ │
│  │ SQLite   │ │ ChromaDB │ │ GPT/Gemini/Qwen  │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ 安全强化  │ │ 智能恢复  │ │   可观测性        │ │
│  │5层纵深   │ │错误分类   │ │ 日志/追踪/指标    │ │
│  │防御      │ │自适应恢复 │ │                  │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ 策略引擎  │ │ 工具注册  │ │   MCP 互操作      │ │
│  │全局/项目/ │ │零耦合    │ │ Client + Server  │ │
│  │会话继承   │ │自注册    │ │ 双向协议          │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## 📁 目录结构

```
mundo-agent/
├── core.py                 # 核心引擎 MundoEngine
├── reflection_engine.py    # 反射循环引擎
├── memory.py               # 三层记忆系统
├── knowledge_retriever.py  # 混合检索 RAG
├── vector_store.py         # ChromaDB 向量存储
├── task_analyzer.py        # 任务分析引擎
├── llm.py                  # LLM 客户端 + 断路器
├── model_adapter.py        # 模型适配层
├── model_profiles.py       # 模型画像 + 智能选择
├── task_planner.py         # 任务规划器
├── tools.py                # 工具注册表
├── delegation.py           # 多 Agent 委托
├── workflow.py             # 工作流引擎
├── policy.py               # 策略引擎
├── security_hardening.py   # 安全强化层
├── intelligent_recovery.py # 智能错误恢复
├── mcp.py                  # MCP 客户端
├── mcp_server.py           # MCP 服务端
├── eval_engine.py          # 评估框架
├── observability.py        # 可观测性
├── prompt_assembler.py     # 提示词组装器
├── constants.py            # 全局常量
├── Dockerfile              # 容器化
├── docker-compose.yml      # 编排
├── .github/workflows/      # CI/CD
└── tests/                  # 测试套件（169 用例）
```

---

## 🧪 测试

```bash
pytest tests/ -v --cov=. --cov-report=term-missing
```

169 个单元测试覆盖所有核心模块。

---

## 🔌 MCP Server

```bash
# 启动 MCP Server
python3 -c "
from mcp_server import get_mcp_server
server = get_mcp_server(port=3100)
server.start(background=False)
"

# 外部调用
curl -X POST http://127.0.0.1:3100 -H 'Content-Type: application/json' -d '{
  \"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"tools/call\",
  \"params\": {\"name\": \"mundo_search_knowledge\", \"arguments\": {\"query\": \"反射循环\"}}
}'
```

---

## 📚 引用论文

- Reflexion: Language Agents with Verbal Reinforcement Learning (Shinn et al., 2023)
- ReAct: Synergizing Reasoning and Acting in Language Models (Yao et al., 2022)
- Dense Passage Retrieval for Open-Domain Question Answering (Karpukhin et al., 2020)
- Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks (Lewis et al., 2020)
- SWE-bench: Can Language Models Resolve Real-World GitHub Issues? (Jimenez et al., 2024)

---

## 📝 版本历史

### v2.2.7 (2026-06-18)
- 向量检索：ChromaDB + BM25 + 语义哈希三路融合
- 任务分析引擎：自动分类、Markdown 解析、需求提取、子任务拆解
- MCP Server：蒙多能力通过标准协议对外暴露
- 评估框架：多维度量化 + 内置评估用例
- 可观测性：结构化日志 + 分布式追踪 + 指标采集
- 工程化：Docker + CI/CD + 169 单元测试
- 修复：工具参数 JSON 解析失败问题（repair_json 增强）

### v2.2.6 (2026-06-17)
- 三层记忆架构 + 权限弹窗
- 冲突解决机制

---

MIT License
