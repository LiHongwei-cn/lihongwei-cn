# 蒙多 · 跨界学习引擎

> 我是蒙多！蒙多想去哪就去哪！

完整的 AI 智能编排系统——学习、记忆、成长、进化，永不停止。通过 Hermes Agent 平台调度 Claude Code、DeepSeek、ChatGPT、Gemini 等多模型协同工作。

## 蒙多的能力

| 能力 | 说明 |
|------|------|
| 推理引擎 | 第一性原理拆解、决策矩阵、根因分析、类比推理、反事实验证 |
| 对抗验证 | 边界/安全/性能/依赖/矛盾五维攻击，方案存活才采纳 |
| 元学习 | 学习策略库、元规则、领域自信度自校准 |
| 期刊学习 | 每日自动抓取 Nature/Science/Cell 等顶级期刊，提取知识生成 Skill |
| AI 热点日报 | 每日追踪 AI 领域动态，多源抓取+AI 分析，生成结构化日报 |
| 云仓库系统 | 双向同步、质量评分(0-100)、SHA-256 去重、每日自动进化、每周审计 |
| 并行模式 | 复杂任务分身执行，多个蒙多同时工作 |
| 集体意识 | 一个蒙多学到，所有蒙多都会 |

## 自动化任务

| 任务 | 时间 | 说明 |
|------|------|------|
| daily-evolve | 每天 03:00 | 拉取最新技能到本地 |
| full-sync | 每天 04:00 | 全量同步到云仓库 |
| daily-journal | 每天 06:00 | 抓取期刊学习 |
| daily-hotspot | 每天 07:00 | AI 热点分析 |
| weekly-audit | 每周日 09:00 | 质量审计 |

## 项目结构

```
mundo-cloud/
├── skills/              # 所有 Skill 存储
├── scripts/             # 工具链脚本
│   ├── quality_scorer.py    # 质量评分引擎
│   ├── dedup_engine.py      # 去重比较引擎
│   ├── daily_evolve.sh      # 每日自动进化
│   └── daily_journal.sh     # 每日期刊学习
└── sync/                # 状态数据
```

## 安装

从 [Skills 市场](https://lihongwei-cn.github.io/lihongwei-cn/skills/) 下载蒙多 Skill：

- **Claude Code**：复制到 `~/.claude/skills/mundo/`
- **Hermes Agent**：复制到 `~/.hermes/skills/mundo/`
