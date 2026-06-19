---
name: skill-store-index
description: "Skill 云仓库索引。包含所有可用的 skill 分类和快速查找指南。"
category: meta
tags: [index, catalog, skills]
---

# Skill 云仓库索引

## 目录结构

```
skill-store/
├── skills/
│   ├── ppt/           # PPT 制作工具
│   │   └── SKILL.md
│   ├── web-ui/        # Web UI 设计
│   │   └── SKILL.md
│   ├── resume/        # 简历制作
│   │   └── SKILL.md
│   └── design/        # 设计资源
│       └── SKILL.md
├── data/              # GitHub Trending 爬取数据
│   └── YYYY-MM-DD.json
├── scripts/           # 爬取脚本
│   └── scrape-trending.py
└── index.html         # 网页展示
```

## 快速查找

### 我要制作 PPT
→ 加载 `skill-store/skills/ppt/SKILL.md`

推荐方案：
- **技术分享**：Slidev + seriph 主题
- **学术答辩**：LaTeX Beamer + metropolis
- **快速演示**：Marp + VS Code
- **AI 辅助**：Gamma.app

### 我要做 Web 前端
→ 加载 `skill-store/skills/web-ui/SKILL.md`

推荐方案：
- **现代 Web 应用**：React + Tailwind + shadcn/ui + Framer Motion
- **Landing Page**：Next.js + Tailwind + Aceternity UI
- **Dashboard**：React + Tailwind + shadcn/ui + Recharts

### 我要制作简历
→ 加载 `skill-store/skills/resume/SKILL.md`

推荐方案：
- **开源最强**：Reactive Resume
- **技术岗位**：LaTeX (Deedy Resume 或 Awesome CV)
- **快速制作**：JSON Resume + elegant 主题
- **在线工具**：FlowCV 或 Novoresume

### 我需要设计资源
→ 加载 `skill-store/skills/design/SKILL.md`

包含：
- 色彩系统（深色/浅色主题）
- 字体搭配方案
- 图标库推荐
- 设计工具
- 灵感来源

---

## 调用方式

### 蒙多调用
```
skill_view(name='skill-store-index')
```

### Claude Code 调用
在 CLAUDE.md 中引用：
```markdown
## Skill 云仓库
- 位置：~/Desktop/lihongwei-cn/skill-store/skills/
- 索引：skill-store/skills/SKILL.md
- 分类：ppt, web-ui, resume, design
```

---

## 更新日志

- 2026-06-19：创建初始版本，包含 PPT/Web UI/简历/设计 四个分类