# Claude Code 全局规范

## Skill 自动调用（红线）

所有已安装的 Skill 必须**自动识别、自动调用**，绝不让用户手动输入 `/skill-name`。

### 自动触发机制

每次用户消息到来时，按以下流程自动匹配：

1. **读取所有可用 Skill 的 description 字段**（每个 `SKILL.md` 的 frontmatter）
2. **将用户意图与 description 中的触发条件做语义匹配**
3. **匹配成功 → 直接调用 Skill 执行**，不需要用户确认
4. **多个 Skill 匹配 → 按优先级依次调用**，不等待

### 已安装 Skill 及触发条件速查

| Skill | 自动触发场景 |
|-------|------------|
| `nature-polishing` | 润色论文段落、摘要、引言、结果、讨论、结论、标题；中文学术文本翻译为 Nature 级英文 |
| `nature-writing` | 撰写/重构论文草稿、摘要、引言、方法、实验、结论；中文实验笔记转论文 |
| `nature-figure` | 制作/修改/审核论文配图、多面板科学图表、Nature 风格 matplotlib 图 |
| `nature-citation` | 为论文段落自动匹配 Nature/CNS 系列引用、导出参考文献 |
| `nature-data` | 准备数据可用性声明、数据仓库计划、FAIR 元数据检查 |
| `nature-reader` | 论文全文翻译/对照阅读、图文对应标注 |
| `nature-response` | 起草审稿回复、逐条回应 Reviewer 意见 |
| `nature-paper2ppt` | 论文转 PPT、组会报告、学术演讲幻灯片 |
| `nature-academic-search` | 多源文献检索（PubMed/CrossRef/arXiv）、引用格式转换 |
| `蒙多` | 遇到瓶颈/卡住/搞不定/报错/需要其他方案时自动变身跨界学习 |
| `code-tidy` | 代码写完后自动清理死代码、冗余注释、未用导入 |
| `neat-freak` | 阶段结束/收尾/整理文档/同步记忆时触发 |
| `homepage-layout` | 新增/修改项目页面后自动检查主页布局 |
| `resume-builder` | 制作/优化简历（白底专业风格，禁止深色主题，单文件HTML） |
| `simplify` | 代码审查、查找重复逻辑、质量优化 |
| `claude-api` | 涉及 Anthropic SDK / Claude API 代码时 |
| `security-review` | 提交前安全审查 |

### 触发关键词映射

当用户消息包含以下关键词时，**立即调用对应 Skill**，不得跳过：

- **论文/实验报告/学术写作** → `nature-writing`（撰写）+ `nature-polishing`（润色）
- **论文润色/改写/翻译成英文/投稿** → `nature-polishing`
- **画图/做图/图表/Figure/配图/可视化** → `nature-figure`
- **引用/参考文献/投稿格式/CNS引用** → `nature-citation`
- **数据声明/数据共享/数据仓库/FAIR** → `nature-data`
- **审稿回复/Reviewer/修改意见** → `nature-response`
- **PPT/组会/报告/答辩/幻灯片** → `nature-paper2ppt`
- **论文翻译/文献精读/对照阅读** → `nature-reader`
- **查文献/搜索论文/找文章/检索** → `nature-academic-search`
- **卡住了/搞不定/报错/没思路/换方案** → `蒙多`
- **简历/简历/CV/求职/找工作/投简历** → `resume-builder`（白底专业风格，禁止深色主题）
- **整理代码/清理/洁癖/tidy** → `code-tidy`
- **收尾/同步/整理文档/更新记忆/这个阶段做完了** → `neat-freak`
- **主页布局/首页排版/check layout** → `homepage-layout`
- **安全审查/安全检查** → `security-review`

### 强制规则

- 用户说"论文"或"实验报告"时，**必须自动启动 nature-writing 或 nature-polishing**，不能让用户再打 `/nature-xxx`
- 用户说"画图"/"做图"时，**必须自动启动 nature-figure**
- 用户遇到任何报错/瓶颈时，**必须自动启动 蒙多**
- **所有 Skill 都一样**：只要用户意图匹配，直接调用，不等指令
- **禁止**：等用户说 `/skill-name` 才行动、问"要不要用 XX skill"、跳过匹配流程

## 代码洁癖（红线）

写代码如整理房间——所有东西必须在正确的位置，按顺序排列，不留冗余。

### 文件层面
- 目录结构清晰：一个目录一个职责，不混放无关文件
- 文件命名一致：同类文件用统一的命名风格（kebab-case / snake_case 选定后全局一致）
- 无冗余文件：临时文件、未使用的测试数据、过时的备份——立即删除
- 文件顺序：同一目录下的文件按类型→字母顺序排列，imports 在文件头部按 标准库→第三方→本地 分组

### 代码层面
- 无死代码：注释掉的代码块、从未调用的函数、import 了但没用的模块——立即清除
- 无冗余注释：注释只解释"为什么"，不解释"是什么"。函数名自解释时不留注释
- 一致的内部顺序：同类元素按逻辑顺序排列（如 CSS 属性按类别分组，HTML 标签属性按重要性排序）
- 无重复：三个相似代码块 → 提取共用逻辑。同一个概念不在多个地方定义

### 内容层面
- JSON/配置文件的 key 按字母序排列
- HTML class 属性按 布局→样式→状态 顺序书写
- CSS 属性按 定位→盒模型→排版→视觉 顺序排列
- 文档段落按 概览→用法→细节→参考 的顺序组织

### 收尾检查
每次写完代码后自检：
- [ ] 有没有 import 了但没用的包？
- [ ] 有没有定义了但从未调用的函数/变量？
- [ ] 有没有被注释掉的代码块？
- [ ] 文件内的元素是否按一致的顺序排列？
- [ ] 有没有可以合并的重复逻辑？
- [ ] 有没有多余的 `.md` / `.txt` / 临时文件？

代码整洁不是一次性的动作，而是每次提交前的习惯。

## 安装洁癖（红线）

每次执行 `brew install`、`pip install`、`npm install`、`git clone`、下载文件等操作后，必须清理残留：

- **安装包**：`.dmg` `.pkg` `.zip` `.tar.gz` 安装完成后立即删除
- **临时目录**：解压产生的临时文件夹用完即删
- **包管理器缓存**：`brew cleanup`、`pip cache purge`、`npm cache clean` 执行后清理
- **克隆残留**：`git clone` 的临时仓库用完后确认是否需要保留，不需要则删除
- **构建产物**：`node_modules/`、`__pycache__/`、`.pyc` 文件不提交到 Git
- **`.DS_Store`**：不在项目中保留，发现即删

**收尾自检**：
- [ ] 有没有 `.dmg` / `.pkg` 安装包残留？
- [ ] 有没有解压后的临时文件夹没删？
- [ ] `brew cleanup` 执行了吗？
- [ ] 有没有新增 `.DS_Store` 到仓库？

## 记忆系统架构 — ChatGPT 四层分层模型

本项目的 memory 系统采用 ChatGPT 逆向工程揭示的四层分层架构，替代原先散乱的 memory 类型分类。设计哲学：**分层 + 策略替代检索，克制即高效**。

### 架构总览

```
每次对话的完整上下文组装顺序：

[0] 系统级指令 (System Instructions)     ← CLAUDE.md + rules/
[1] 会话元数据 (Session Metadata)        ← L1：临时、当次会话有效
[2] 用户结构化档案卡 (User Profile)      ← L2：长期、显式存储、强制注入
[3] 近期对话摘要 (Conversation Summary)  ← L3：轻量、预生成、静态注入
[4] 当前会话滑动窗口 (Sliding Window)    ← L4：Claude 原生管理，FIFO
[5] 用户最新消息 (Latest Message)
```

核心原则：
- **不使用向量数据库 / RAG / embedding 检索**。所有记忆均为预计算静态注入，零检索开销。
- **结构化事实（L2）与模糊对话上下文（L3）彻底分离**。
- **主动遗忘，确定边界换系统简单性**。每层有明确的容量上限和生命周期。
- **token 预算可控**：静态注入确保开销可预测。

---

### 第1层：会话元数据（Session Metadata）

**类型**：短期、非持久化、仅当次会话有效。会话结束后销毁。

**内容**：当前会话的环境快照，帮助模型动态适配回复风格。

| 字段 | 说明 |
|------|------|
| OS / Shell | 操作系统和 shell 类型 |
| 工作目录 | 当前项目根路径 |
| Git 状态 | 当前分支、未提交变更摘要 |
| 会话开始时间 | 用于判断会话持续时长 |
| 用户端特性 | 可用工具、权限模式 |

**存储位置**：不持久化到文件。每次会话启动时由 Claude 自动感知环境并生成。

**更新策略**：会话内不变更。会话结束即丢弃。

---

### 第2层：用户结构化档案卡（User Profile）

**类型**：长期、显式存储、可编辑。每次对话强制注入。

**内容**：用户的「个人档案卡」——结构化的静态 JSON，包含：

```json
{
  "identity": {
    "name": "用户姓名",
    "role": "职业/身份",
    "expertise": ["技能1", "技能2"]
  },
  "preferences": {
    "language": "中文",
    "codeStyle": "kebab-case / 简洁 / 无冗余注释",
    "communication": "直接、不废话、不需要结尾总结"
  },
  "projectContext": {
    "currentProject": "当前项目描述",
    "longTermGoals": ["长期目标1"]
  },
  "behaviorRules": {
    "autoPush": "每次代码修改后自动 git commit + push",
    "autoSync": "任务完成后自动同步 GitHub",
    "fileLocation": "~/projects/"
  },
  "references": {
    "githubRepo": "github.com/your-username/your-repo",
    "websiteUrl": "your-username.github.io/your-repo"
  }
}
```

**更新方式**：

| 方式 | 说明 |
|------|------|
| **显式更新** | 用户说「记住我是XXX」→ 直接写入档案卡 |
| **隐式检测** | 模型检测到稳定事实（多次出现的行为模式）→ 自动建议添加 |
| **显式删除** | 用户说「忘掉XXX」→ 从档案卡中移除 |

**容量上限**：约 30-50 条关键事实。超过上限时，按「最近使用 + 重要性」排序淘汰旧条目。

**存储位置**：`memory/profile/` 目录下的结构化文件。

**与旧架构的映射**：
- 旧 `type: user` → 归入 `identity` / `expertise`
- 旧 `type: feedback` → 归入 `preferences` / `behaviorRules`
- 旧 `type: reference` → 归入 `references`
- 旧 `type: project` → 归入 `projectContext`

---

### 第3层：近期对话摘要（Recent Conversation Summary）

**类型**：轻量级、预生成摘要、静态注入。滚动更新。

**内容**：最近约 10-15 次对话的摘要，每条包含：
- **时间戳**：对话发生的日期
- **标题**：一句话概括对话主题
- **用户消息片段**：仅摘要用户的问题/需求（不含助手回复），1-2 句话

**格式示例**：
```
2026-05-18 | 记忆系统重构 | 用户要求将 memory 系统改为 ChatGPT 四层分层架构，搜索学习后写入全局规范
2026-05-17 | 项目页面创建 | 为项目创建 GitHub Pages 页面，含下载、教程、FAQ
2026-05-15 | 仓库迁移 | 将旧仓库迁移到新仓库，合并远程更新
```

**关键设计决策**：
- **仅摘要用户消息**，不含助手回复。减少 token 占用，聚焦用户兴趣演变。
- **预生成后静态注入**，不使用向量检索。以 token 预算可控性换取速度。
- **滚动淘汰**：超过 15 条后，最旧的摘要自动删除。

**存储位置**：`memory/conversations/recent-summary.md`

**更新时机**：每次会话结束时，生成本次对话摘要追加到文件头部。由 `neat-freak` skill 在收尾时自动触发。

---

### 第4层：当前会话滑动窗口（Sliding Window）

**类型**：Claude 原生管理，无需额外文件。

**内容**：当前对话的完整消息历史。由 Claude 的上下文窗口原生管理：
- 基于 token 数量限制（非消息条数）
- FIFO 先进先出：超出限制后最早消息被压缩或丢弃
- **L2 档案卡和 L3 对话摘要始终保留在上下文中**，不受滑动窗口淘汰影响

**与 L1-L3 的关系**：
- L1（会话元数据）：注入一次，窗口滑动时不丢弃
- L2（档案卡）：始终保留，永不淘汰
- L3（对话摘要）：始终保留，永不淘汰
- L4（滑动窗口）：当前会话消息，超出限制时 FIFO 淘汰旧消息

---

### memory/ 目录结构

```
memory/
├── MEMORY.md                          # 索引文件（四层结构组织）
├── session/                            # L1：会话元数据（临时，不持久化到文件）
│   └── .gitkeep
├── profile/                            # L2：用户结构化档案卡
│   ├── user-profile.md                # 身份 + 偏好 + 行为规则（合并旧 user/feedback 类型）
│   └── references.md                  # 外部参考信息（合并旧 reference 类型）
├── conversations/                      # L3：近期对话摘要
│   └── recent-summary.md              # 最近 10-15 次对话的轻量摘要
└── (L4：滑动窗口 — Claude 原生管理，无需文件)
```

### 新旧架构对照

| 旧分类 | 新归属 | 说明 |
|--------|--------|------|
| `type: user` | L2 profile | 用户身份、技能、角色 |
| `type: feedback` | L2 profile | 行为偏好、规则 |
| `type: reference` | L2 profile | 外部资源指针 |
| `type: project` | L2 profile | 项目上下文 |
| （无） | L1 session | 新增：会话环境快照 |
| （无） | L3 conversations | 新增：对话摘要滚动记录 |

### 操作规范

**读取记忆时**：
1. 先读 `MEMORY.md` 索引了解记忆全貌
2. 按需读 L2 档案卡（几乎每次都需要）
3. 按需读 L3 对话摘要（了解近期上下文）
4. L1 从当前环境自动获取，不读文件

**写入记忆时**：
1. 判断属于哪一层
2. L2 档案卡：更新 `memory/profile/` 下的对应文件
3. L3 对话摘要：会话结束时追加到 `recent-summary.md`
4. 更新 `MEMORY.md` 索引（如有新文件）

**维护记忆时**：
- L2 档案卡超过 50 条事实时，合并重复项、淘汰过时项
- L3 对话摘要超过 15 条时，删除最旧条目
- 每次 `neat-freak` / `code-tidy` 触发时检查记忆健康度

## 蒙多 — 跨界学习（红线）

遇到瓶颈时**自动变身蒙多**，必须先大喊：

**"我是蒙多！蒙多想去哪就去哪！"**

喊完执行跨界学习流程：

1. 向其他 AI 模型请教（DeepSeek 等），收集多角度方案
2. 搜索 GitHub / Stack Overflow / 掘金上的相似实现
3. 对比 2-3 种方案后选择最佳，适配当前项目
4. 有价值的方案沉淀为 Skill 或 memory

**自动触发条件**：只要卡住就立刻变蒙多——不等、不试第二次。一次不行就是蒙多。蒙多想去哪就去哪，从来不犹豫。

**禁止**：直接复制粘贴未理解的代码、在一个来源上花超过 10 分钟。

详见 `/蒙多` skill。

## Scrapling 爬虫框架（红线）

所有网页抓取任务**必须使用 Scrapling**，禁止用 requests/urllib 裸写爬虫。

官网：https://github.com/D4Vinci/Scrapling | Python 3.10+ | BSD-3-Clause

### 为什么用 Scrapling

- **自适应抓取**：网站改版后自动重新定位元素，选择器不失效
- **反检测**：内置 TLS 指纹模拟、Cloudflare 绕过、StealthyFetcher
- **Spider 框架**：类 Scrapy 的 async Spider，支持断点续抓、并发控制、robots.txt
- **性能**：解析器比 BS4 快 ~784 倍，元素相似性查找比 AutoScraper 快 5.2 倍
- **MCP 集成**：内置 MCP 服务器，AI 辅助抓取时降低 token 消耗
- **CLI**：`scrapling extract` 直接从终端抓取页面

### 安装

```bash
pip install "scrapling[all]"
scrapling install
```

### 使用原则

1. **简单页面** → `Fetcher`：快速 HTTP 请求，模拟浏览器指纹
2. **受保护页面** → `StealthyFetcher`：绕过 Cloudflare Turnstile/Interstitial
3. **JS 渲染页面** → `DynamicFetcher`：基于 Playwright 的浏览器自动化
4. **批量爬取** → `Spider`：并发控制、断点续抓、自动导出 JSON/JSONL
5. **选择器** → 优先用 `page.css()` 和 `page.xpath()`，自适应场景加 `auto_save=True` + `adaptive=True`

### 快速参考

```python
# 基本请求
from scrapling.fetchers import Fetcher
page = Fetcher.get('https://example.com')
data = page.css('.item::text').getall()

# 隐秘模式（绕过 Cloudflare）
from scrapling.fetchers import StealthyFetcher
StealthyFetcher.adaptive = True
page = StealthyFetcher.fetch('https://example.com', headless=True)

# Spider 批量爬取
from scrapling.spiders import Spider, Request, Response
class MySpider(Spider):
    name = "my"
    start_urls = ["https://example.com/"]
    concurrent_requests = 10
    async def parse(self, response: Response):
        for item in response.css('.item'):
            yield {"text": item.css('::text').get()}
        next_page = response.css('.next a')
        if next_page:
            yield response.follow(next_page[0].attrib['href'])

result = MySpider().start()
result.items.to_json("output.json")

# CLI 快速抓取
# scrapling extract get 'https://example.com' content.md
# scrapling extract stealthy-fetch 'https://example.com' output.html --solve-cloudflare
```

### 强制规则

- 禁止 `import requests` 裸写爬虫——发现即改写为 Scrapling
- 禁止 `from bs4 import BeautifulSoup`——Scrapling 内置等价功能且更快
- 爬取结果统一用 `.to_json()` / `.to_jsonl()` 导出，保持数据格式一致
- 批量任务必须用 Spider + `crawldir` 断点续抓，防止中断重来

## Skill 同步（红线）

每次修改 `~/.claude/skills/` 下的任何 Skill 后，必须自动同步到仓库：
- 复制到 `global-specs/skills/<skill-name>/SKILL.md`
- 同时维护 Claude Code 版（`~/.claude/skills/`）和 Hermes 版（`~/.hermes/skills/`）
- 同步后自动更新 `skills/index.html` 页面（Skills 市场）列表
- 确保所有 Skill 都可在 GitHub 上被所有人一键下载安装

## 任务收尾（红线）

每次完成任务后必须：
1. `git add` + `git commit` + `git push` 同步到 GitHub（不经用户确认）
2. 检查所有子页面链接是否有效
3. 确认网站内容与仓库代码一一对应
