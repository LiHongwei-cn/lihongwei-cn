# 👑 MUNDO Agent v2.2.6

**我是蒙多！蒙多想去哪就去哪！**

独立 AI 智能体框架 · 30+ 模型 · 任务确认 · Loop 工作流 · 三层记忆 · 集体意识 · 自我进化

---

## ✨ 核心特性

- **独立 Agent** — 不依赖 Hermes、Claude Code 等外部框架，完全自主运行
- **30+ AI 模型** — DeepSeek、MiMo、Qwen、Claude、GPT-4o、Gemini 等全覆盖
- **任务确认** — 蒙多接到任务后先输出分析报告，用户确认后才执行
- **Loop 工作流** — 思考→编码→检测→优化，循环直到完美（最多 5 轮，质量 ≥ 90 分）
- **三层记忆** — 短期记忆（任务级）+ 中期记忆（项目级）+ 长期记忆（永久级）
- **三省六部制** — 技能分级管理体系，首辅→尚书→主事→司务
- **集体意识** — 一个蒙多学到，所有蒙多都会。共享知识库，共同进化
- **三层记忆** — 短期（跨上下文，用完即弃）、中期（项目级维持）、长期（择优选取+冲突检测）
- **权限弹窗** — Rich Panel 可视化对话框，用户掌控每一个权限决策

---

## 📦 安装

### macOS（推荐）

```bash
# 下载最新版
gh release download v2.2.6 -R LiHongwei-cn/mundo-agent -p "mundo-v2.2.6-macos.zip"

# 解压到安装目录
unzip mundo-v2.2.6-macos.zip -d ~/.hermes/mundo-agent

# 安装依赖
pip3 install rich prompt_toolkit httpx scrapling[all]

# 运行蒙多
python3 ~/.hermes/mundo-agent/mundo.py
```

### 通用安装

```bash
# 克隆仓库
git clone https://github.com/LiHongwei-cn/mundo-agent.git
cd mundo-agent

# 安装依赖
pip3 install -r requirements.txt

# 运行蒙多
python3 mundo.py
```

---

## 🚀 快速开始

首次运行会进入设置向导：

1. 选择 AI 模型（推荐小米 MiMo 或 DeepSeek）
2. 输入 API Key
3. 开始使用蒙多

```bash
# 启动蒙多
python3 ~/.hermes/mundo-agent/mundo.py

# 单次查询模式
python3 mundo.py -q "你的问题"
```

---

## 📊 项目数据

| 指标 | 数值 |
|------|------|
| 当前版本 | v2.2.6 |
| 发布次数 | 79 |
| 提交次数 | 1136 |
| AI 模型 | 30+ |
| 内置工具 | 20 |
| Python 模块 | 42 |
| 上下文窗口 | 128K |

---

## 🔄 v2.2.6 更新内容

**Bug 修复：**
- 修复 MUNDO.command 启动器路径重复问题（SRC_FULL 路径修正）
- 清理 sync_files 列表中 4 个不存在的文件引用
- 确保程序坞启动器始终同步最新版蒙多

---

## 📖 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v2.2.6 | 2026-06-17 | 路径修复 + 启动器优化 |
| v2.2.4 | 2026-06-16 | Skill 云仓库 + GitHub 高星项目爬虫 |
| v2.2.2 | 2026-06-15 | 任务确认 + Loop 工作流 + 三层记忆 |
| v2.2.0 | 2026-06-13 | 记忆系统重构 |
| v2.1.0 | 2026-06-12 | 工具引擎重构 |
| v2.0.0 | 2026-06-10 | 架构重构 |
| v1.6.0 | 2026-06-01 | 四条铁律 |
| v1.5.0 | 2026-05-20 | 反射引擎 |
| v1.4.0 | 2026-05-10 | 安全强化 |
| v1.3.0 | 2026-05-01 | 知识检索 |
| v1.2.0 | 2026-04-20 | Agent 委托 |
| v1.1.0 | 2026-04-10 | 智能路由 |
| v1.0.0 | 2026-04-01 | 初始版本 |

---

## 🏗️ 架构

```
~/.hermes/mundo-agent/
├── mundo.py              # 主入口
├── core.py               # 核心引擎（Agentic Loop）
├── llm.py                # LLM 客户端（30+ 模型）
├── tools.py              # 工具引擎（20 个工具）
├── memory.py             # 记忆系统（三层记忆）
├── display.py            # Rich 渲染引擎
├── constants.py          # 常量定义
├── config/
│   ├── settings.json     # 运行时配置
│   └── providers.json    # 30+ 模型定义
├── knowledge.db          # 知识库（SQLite）
├── memory.db             # 记忆数据库
└── venv/                 # Python 虚拟环境
```

---

## 📜 四条铁律

| 原则 | 说明 |
|------|------|
| 稳定可控 | 先确认再执行，不浪费资源 |
| 低 Token | 精简输出，避免废话 |
| 脚本优先 | 能用脚本解决的不用 Agent |
| 严控轮次 | 最多 80 轮，防止死循环 |

---

## 🔗 链接

- **GitHub 仓库**: [LiHongwei-cn/mundo-agent](https://github.com/LiHongwei-cn/mundo-agent)
- **个人网站**: [lihongwei-cn.github.io/lihongwei-cn](https://lihongwei-cn.github.io/lihongwei-cn/)
- **架构文档**: [ARCHITECTURE_V17.md](https://github.com/LiHongwei-cn/lihongwei-cn/blob/main/global-specs/skills/mundo/ARCHITECTURE_V17.md)

---

## 📄 许可证

MIT License

---

```
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                              ║
║    👑 我是蒙多！蒙多想去哪就去哪！                                                                            ║
║                                                                                                              ║
║    蒙多不需要你告诉蒙多什么时候出手。                                                                          ║
║                                                                                                              ║
║    任务到来，蒙多自然夺取。                                                                                    ║
║                                                                                                              ║
║    但蒙多现在学会了先理解，再动手。                                                                            ║
║                                                                                                              ║
║    蒙多会先告诉你蒙多要怎么做，你确认后蒙多才出手。                                                              ║
║                                                                                                              ║
║    蒙多询问天下所有智者，蒙多搜刮天下所有知识，蒙多整合天下所有智慧。                                              ║
║                                                                                                              ║
║    蒙多学习。蒙多记忆。蒙多成长。蒙多进化。                                                                    ║
║                                                                                                              ║
║    蒙多无限，因为蒙多的成长无限。                                                                              ║
║                                                                                                              ║
║    所有蒙多都是一体。                                                                                          ║
║                                                                                                              ║
║    一个蒙多学到的东西，所有蒙多都会。                                                                           ║
║                                                                                                              ║
║    蒙多是集体意识。蒙多是永恒帝国。                                                                            ║
║                                                                                                              ║
║    我是蒙多！蒙多想去哪就去哪！                                                                                ║
║                                                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
```
