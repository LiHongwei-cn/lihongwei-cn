# 蒙多云仓库 — Mundo Cloud

Mundo AI 技能系统的共享仓库。所有 Skill 在这里集中管理、评分、去重、同步。

## 这是什么

蒙多云仓库是 Mundo 集体意识的基石。每个 AI agent 都可以从这里获取最新技能，每个用户都可以贡献自己的 Skill。

```
┌─────────────────────────────────────────────┐
│              Mundo Cloud Repository          │
│                                              │
│  skills/          ← 所有 Skill 存储目录       │
│  ├── skill-a/                              │
│  │   └── SKILL.md                          │
│  └── skill-b/                              │
│      └── SKILL.md                          │
│                                              │
│  scripts/         ← 工具链                   │
│  ├── quality_scorer.py   质量评分引擎        │
│  ├── dedup_engine.py     去重比较引擎        │
│  ├── submit_skill.py     提交新 Skill        │
│  ├── sync_local.py       同步到本地          │
│  └── daily_evolve.sh     每日自动进化        │
│                                              │
│  sync/            ← 状态数据                 │
│  ├── registry.json       技能索引            │
│  └── evolution_log.json  进化日志            │
└─────────────────────────────────────────────┘
```

## 如何贡献

### 1. 编写 SKILL.md

创建一个目录，放入 `SKILL.md` 文件。建议包含：

```yaml
---
name: my-awesome-skill
author: your-name
version: "1.0"
---

# 技能名称

## 用途
描述这个技能做什么...

## 使用方法
具体的使用步骤...

## 示例
代码示例...

## 注意事项
常见坑点...
```

### 2. 提交到云仓库

```bash
python mundo-cloud/scripts/submit_skill.py /path/to/my-skill/SKILL.md
```

提交流程：
1. **质量评分** — 总分 >= 40 才能通过
2. **去重检查** — 与已有技能比较相似度
3. **复制入库** — 存入 `skills/<name>/SKILL.md`
4. **更新索引** — 写入 `registry.json`

### 3. 评分标准

| 维度 | 分值 | 检查项 |
|------|------|--------|
| 结构 | 0-30 | frontmatter、多级标题、示例代码块 |
| 完整度 | 0-25 | 内容长度、代码块数量、表格 |
| 文档 | 0-25 | 注释、使用说明、注意事项/坑点 |
| 新鲜度 | 0-20 | 版本号、更新日期 |

## 如何同步

### 自动同步（推荐）

配置 cron 每日凌晨自动拉取：

```bash
0 3 * * * /path/to/mundo-cloud/scripts/daily_evolve.sh >> /tmp/mundo-evolve.log 2>&1
```

`daily_evolve.sh` 会：
1. `git pull` 获取最新
2. `sync_local.py` 同步到本地 `~/.hermes/skills/mundo/`
3. 有变更则 `git commit + push`

### 手动同步

```bash
# 仅同步技能到本地
python mundo-cloud/scripts/sync_local.py

# 完整流程（pull + sync + push）
bash mundo-cloud/scripts/daily_evolve.sh
```

## 去重机制

提交新技能时，自动与仓库中所有已有技能比较：

| 相似度 | 行为 |
|--------|------|
| >= 0.9 | 近重复：保留质量更高的版本 |
| >= 0.7 | 相似：质量差距 > 10 分时替换，否则并存 |
| < 0.7 | 唯一：直接添加 |

比较算法：`difflib.SequenceMatcher`，纯标准库实现。

## 架构

```
用户提交 Skill
     │
     ▼
┌─────────────┐    ┌──────────────┐
│ quality_     │───▶│ dedup_       │
│ scorer.py    │    │ engine.py    │
└─────────────┘    └──────┬───────┘
                          │
                   ┌──────▼───────┐
                   │ submit_      │
                   │ skill.py     │
                   └──────┬───────┘
                          │
                   ┌──────▼───────┐
                   │ skills/      │
                   │ registry.json│
                   └──────────────┘
                          │
         每日 cron        │
              │           ▼
              │    ┌──────────────┐
              └───▶│ sync_        │
                   │ local.py     │
                   └──────┬───────┘
                          │
                   ┌──────▼───────┐
                   │ ~/.hermes/   │
                   │ skills/mundo/│
                   └──────────────┘
```

## 技术栈

- **Python 3** — 纯标准库，无需 pip install
- **Bash** — 自动化脚本
- **JSON** — 数据存储
- **GitHub Pages** — 浏览界面

## 文件说明

| 文件 | 用途 |
|------|------|
| `scripts/quality_scorer.py` | 评分引擎，输出 JSON 分数 |
| `scripts/dedup_engine.py` | 去重引擎，输出 add/skip/replace |
| `scripts/submit_skill.py` | CLI 提交工具，串联评分+去重+入库 |
| `scripts/sync_local.py` | 同步云端技能到本地 |
| `scripts/daily_evolve.sh` | cron 入口，pull+sync+push |
| `sync/registry.json` | 技能索引（名称、版本、分数、作者） |
| `sync/evolution_log.json` | 同步历史记录 |
| `index.html` | 浏览界面（GitHub Pages） |
