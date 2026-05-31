---
name: homepage-layout
description: >
  网站首页布局自检与修复。每次新增/删除/修改项目页面后自动触发，
  确保仪表盘无横向滚动条、卡片不重叠、列数随项目数量自适应。
  MUST trigger when the user says: "主页布局", "首页排版", "check layout",
  "fix homepage", "检查页面", or after any project page add/remove/rename.
  Also triggered by any change to index.html or addition of new project directories.
  Also trigger when merging sub-projects into a parent (removing cards after consolidation).
---

# 首页布局自检

> 适用：`lihongwei-cn` GitHub Pages 主页 `index.html`

检查并修复主页布局，确保每项标准都达标。

## 检查清单

逐项验证，不达标的立即修复：

- [ ] **无横向滚动条**：`body { overflow-x: hidden }` 已设置
- [ ] **容器不溢出**：`.container` 使用 `max-width` 而非 `width`，且 `width: 100%`
- [ ] **仪表盘自适应**：`.dashboard` 使用 `grid-template-columns: repeat(auto-fit, minmax(240px, 1fr))`
- [ ] **卡片不重叠**：每个 `.card` 的 `.card-body { min-width: 0 }`，文本有 `overflow: hidden; text-overflow: ellipsis; white-space: nowrap`
- [ ] **分类区块等宽等高**：同一行的 `.cat-section` 高度一致，不会因内容多少而参差
- [ ] **响应式断点合理**：小屏（≤540px）下 `grid-template-columns: 1fr`
- [ ] **所有分类都有至少 1 个项目**：空分类应从 HTML 中移除
- [ ] **所有卡片链接可达**：`href` 指向存在的目录，且该目录包含 `index.html`

## 修复流程

1. 读 `index.html`，核对以上清单
2. CSS 问题直接改 `index.html`
3. 链接验证：检查每个 `href` 是否存在对应目录
4. 修改完成后 `git add` + `git commit` + `git push`

## 新增项目时的额外检查

当新增项目页面时，除了以上检查，还需：

1. 确认新项目归类到哪个 `.cat-section`
2. 若现有分类都不合适，新建分类区块
3. 在 `stats.json` 中添加新项目的初始计数
4. 各子页面添加 page counter（使用 `counterapi.dev`，命名空间 `lihongwei-cn/<project-id>`）
5. 子页面 footer 添加 GitHub 链接和 counter 显示

## 关键 CSS 约束

这些值不可随意改动，否则会造成布局问题：

```css
.container { max-width: 1100px; width: 100%; }
.dashboard { grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }
body { overflow-x: hidden; }
.card-body { min-width: 0; }
@media(max-width: 540px) { .dashboard { grid-template-columns: 1fr; } }
```
