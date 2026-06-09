---
name: mundo-sync
description: 蒙多三合一同步协议 — 每次更新后强制执行
version: 1.4.2
---

# MUNDO 三合一同步协议

## 铁律

**每次修改蒙多代码后，必须执行三合一同步。不允许任何脱节。**

## 三个节点

| 节点 | 路径 | 角色 |
|------|------|------|
| 源码 | `~/Desktop/lihongwei-cn/mundo-agent/` | 开发编辑 |
| 安装版 | `~/.hermes/mundo-agent/` | 运行时 |
| Dock .app | `/Users/huangpeng/Applications/MUNDO.app/` | 程序坞启动器 |

## 同步方法

### 方法一：手动同步（推荐）

```bash
bash ~/Desktop/lihongwei-cn/mundo-agent/sync_mundo.sh
```

### 方法二：自动同步（已内置）

Dock 启动器和 MUNDO.command 已内置自动版本检测：
- 启动时对比源码版本和安装版版本
- 脱节则自动同步后启动
- **零人工干预**

## 同步范围（v1.4.2 完整清单）

每次同步的文件：

**核心模块（13个）：**
- `mundo.py` `core.py` `llm.py` `setup.py` `tools.py`
- `approval.py` `display.py` `memory.py` `memory_import.py`
- `models.py` `agents.py` `delegation.py` `cloud_sync.py`

**包结构模块（v1.4.2+）：**
- `mundo_agent/core/engine.py` — Agentic Loop
- `mundo_agent/core/task_decomposer.py` — 任务分解器
- `mundo_agent/core/budget.py` — Token 预算
- `mundo_agent/core/stats.py` — 执行统计
- `mundo_agent/core/compressor.py` — 上下文压缩
- `mundo_agent/memory/mundo_memory.py` — 四层记忆架构
- `mundo_agent/memory/manager.py` — 数据库连接池
- `mundo_agent/llm/client.py` — LLM 客户端
- `mundo_agent/tools/*.py` — 工具实现
- `mundo_agent/utils/*.py` — 工具函数

**基础设施模块（11个，v1.4.0+）：**
- `constants.py` — 统一常量管理
- `policy.py` — 结构化策略引擎
- `events.py` — 事件总线
- `timeline.py` — 执行轨迹
- `context_mapper.py` — 上下文分块映射
- `cache.py` — 多层缓存
- `sandbox.py` — 执行沙箱
- `mcp.py` — MCP 层
- `skills.py` — Skill 系统
- `plugins.py` — 插件系统
- `runtime_config.py` — 运行时配置

**配置文件（3个）：**
- `version.txt` `requirements.txt` `MUNDO.command`

**三处同步铁律（v1.4.0 教训）：**
新增 .py 模块时必须同步到三处，漏放仓库 = 程序坞启动器 ModuleNotFoundError：
1. `~/.hermes/mundo-agent/` — 运行时
2. `~/Desktop/lihongwei-cn/mundo-agent/` — 仓库
3. `~/Desktop/lihongwei-cn/global-specs/skills/mundo/references/` — 全球规范

## 更新流程（标准操作）

```
1. 编辑源码 ~/Desktop/lihongwei-cn/mundo-agent/xxx.py
2. 测试：cd ~/Desktop/lihongwei-cn/mundo-agent && python3 mundo.py
3. 同步：bash sync_mundo.sh
4. 验证：从 Dock 启动蒙多，确认版本号一致
```

## 故障排查

```bash
# 检查三节点版本是否一致
bash ~/Desktop/lihongwei-cn/mundo-agent/sync_mundo.sh --check

# 强制同步
bash ~/Desktop/lihongwei-cn/mundo-agent/sync_mundo.sh
```

## 工具能力

### 核心工具
- `terminal`: 执行 shell 命令
- `read_file` / `write_file` / `edit_file`: 文件操作
- `search_files`: 搜索文件内容
- `list_directory`: 列出目录内容
- `web_search`: 网络搜索

### 记忆系统
- `memory.py`: 记忆管理（remember, recall, forget, all_facts）
- `memory_import.py`: 记忆导入（import_existing_memory）

### 显示与输入系统
- `display.py`: 任务控制台（TaskConsole, SlashCompleter, read_input）

### 代理系统
- `delegation.py`: 代理管理（AgentManager, TaskDelegator, MundoClone）

### 配置系统
- `setup.py`: 配置管理（PROVIDERS, MUNDO_HOME, MUNDO_ENV）

### 云同步系统
- `cloud_sync.py`: 云同步（scan_local_skills, find_new_skills, auto_sync_new_skills）

## 工作流程

1. **接收任务**: 用户输入任务描述
2. **分析任务**: 判断任务复杂度和类型
3. **选择工具**: 根据任务选择合适的工具
4. **执行任务**: 调用工具执行任务
5. **返回结果**: 向用户报告执行结果

## 代码统计（v1.4.2）

- 核心模块: 29 个（13 核心 + 11 基础设施 + 5 扩展）
- 总代码行数: ~10000 行
- 支持 Provider: 28 个

### 基础设施（v1.4.0+）
- `policy.py`: 结构化策略引擎（15 条内置规则）
- `events.py`: 事件总线（25 种事件类型）
- `timeline.py`: 执行轨迹（SQLite 持久化）
- `context_mapper.py`: 上下文分块映射
- `cache.py`: 多层缓存（prefix + semantic + result）
- `sandbox.py`: 执行沙箱
- `mcp.py`: MCP 层
- `skills.py`: Skill 系统
- `plugins.py`: 插件系统
- `runtime_config.py`: 运行时配置
- `constants.py`: 统一常量管理
