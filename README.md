<div align="center">

<img src="skills/mundo-avatar.png" width="120" style="border-radius:50%;border:3px solid #00e676;box-shadow:0 0 20px rgba(0,230,118,0.3)">

# 🔪 MUNDO — 蒙多跨界学习引擎

### 我是蒙多！蒙多想去哪就去哪！

[![GitHub stars](https://img.shields.io/github/stars/LiHongwei-cn/lihongwei-cn?style=social)](https://github.com/LiHongwei-cn/lihongwei-cn)
[![License: MIT](https://img.shields.io/badge/License-MIT-brightgreen.svg)](LICENSE)

**蒙多没有边界。蒙多可以调用一切资源来解决问题。**

</div>

---

## 🟣 蒙多是谁？

```
╔══════════════════════════════════════╗
║    🟣 我是蒙多！蒙多想去哪就去哪！  ║
╚══════════════════════════════════════╝
```

蒙多是 **Claude Code / Hermes Agent 通用 Skill**，专治各种"卡住"。

蒙多没有边界 — 调用所有工具、加载所有 Skills、搜索 GitHub、并行分身。

| 症状 | 蒙多的处方 |
|------|-----------|
| 😵 代码报错看不懂 | 扫描本地 Skills + 多渠道搜索同类问题 |
| 🤔 不知道怎么实现 | 加载相关 Skills + GitHub 找参考实现 |
| 😤 方案不够好 | 四维对比：简洁度、性能、可维护性、匹配度 |
| 🔄 重复踩同一个坑 | 沉淀为 Skill，下次自动规避 |
| 🧩 任务太复杂 | delegate_task 并行分身，多个蒙多同时干活 |

---

## ⚡ 安装

### Claude Code

```bash
# 一键安装（推荐）
/plugin marketplace add https://github.com/LiHongwei-cn/lihongwei-cn
/plugin install mundo
/reload-plugins
```

### Hermes Agent

```bash
# 一键安装
hermes skills install mundo

# 或手动
git clone https://github.com/LiHongwei-cn/lihongwei-cn.git
cp -R skills/mundo ~/.hermes/skills/
```

### 其他工具（Cursor / Aider / Windsurf / Codex）

```bash
git clone https://github.com/LiHongwei-cn/lihongwei-cn.git
cd lihongwei-cn
cp -R skills/mundo ~/.你的工具/skills/
```

---

## 🔪 蒙多的能力

| 能力 | 说明 |
|------|------|
| 🔧 **调用所有工具** | terminal、file、web、browser、code_execution — 没有限制 |
| 📚 **加载所有 Skills** | 先扫描本地已安装的 skills，找到相关的直接加载使用 |
| 🌐 **GitHub 深度挖掘** | 搜索开源代码、clone 下来研究、提取方案 |
| 🤖 **多 AI 并行搜索** | Stack Overflow + 掘金 + 其他 AI 模型，同时出击 |
| ⚡ **并行分身** | delegate_task 拆分复杂任务，多个蒙多同时干活 |
| 💾 **经验沉淀** | 有价值的方案自动沉淀为 Skill，不重复踩坑 |

---

## 🎯 蒙多七步法

```
卡住了
  ↓
🔪 蒙多变身！（大喊：我是蒙多！蒙多想去哪就去哪！）
  ↓
┌─────────────────────────────────────┐
│  1️⃣  定位瓶颈                      │
│     不知道怎么做？做不好？不够好？   │
├─────────────────────────────────────┤
│  2️⃣  扫描本地武器库                │
│     skills_list() → skill_view()    │
│     本地有答案？直接用！            │
├─────────────────────────────────────┤
│  3️⃣  多渠道并行搜索                │
│     GitHub + Stack Overflow + 掘金  │
│     + 其他 AI 模型                  │
├─────────────────────────────────────┤
│  4️⃣  GitHub 深度挖掘               │
│     搜索 → clone → 研究 → 提取方案 │
├─────────────────────────────────────┤
│  5️⃣  四维对比                      │
│     简洁度 ⭐ 性能 ⭐              │
│     可维护性 ⭐ 匹配度 ⭐          │
├─────────────────────────────────────┤
│  6️⃣  吸收实施                      │
│     理解 → 适配 → 代码落实          │
├─────────────────────────────────────┤
│  7️⃣  效果验证与沉淀                │
│     解决了吗？→ 沉淀为 Skill        │
└─────────────────────────────────────┘
```

---

## 🎯 触发方式

说以下任意一句，蒙多就来：

| 触发词 |
|--------|
| `蒙多` · `卡住了` · `搞不定` · `报错了` · `没思路` · `遇到瓶颈` · `有没有更好的方案` · `mundo` |

**蒙多规则：第一次卡住就变蒙多，绝不试第二次。**

---

## 📖 使用示例

```
你：这个 React 组件渲染太慢了，列表有 1000 条数据就卡死
蒙多：🔪 我是蒙多！蒙多想去哪就去哪！
     [扫描本地 Skills → 没有相关]
     [搜索 GitHub + Stack Overflow + 向其他 AI 请教]
     [clone 了 react-window 研究实现]
     [四维对比 3 种方案]
     → 推荐：react-window 虚拟列表
     → 代码已写好，直接用
     → 已沉淀为 Skill：react-virtual-list
```

```
你：Python 爬虫被反爬了，requests 请求被 403
蒙多：🔪 我是蒙多！蒙多想去哪就去哪！
     [扫描本地 Skills → 发现 Scrapling 相关]
     [加载 Scrapling Skill → 自适应抓取 + 反检测]
     → 替换 requests，问题解决
     → 下次爬虫任务自动使用 Scrapling
```

---

## 🛠️ 技术细节

| 项目 | 说明 |
|------|------|
| 兼容工具 | Claude Code / Hermes Agent / Cursor / Aider / Windsurf / Codex |
| 可用工具 | terminal、file、web、browser、code_execution、delegate_task 等全部工具 |
| Skills 加载 | skills_list() 发现 + skill_view() 加载，本地优先 |
| 搜索渠道 | GitHub、Stack Overflow、掘金、其他 AI 模型 |
| 并行模式 | delegate_task 拆分复杂任务，多蒙多同时干活 |
| 沉淀机制 | skill_manage(action='create') 自动创建 Skill |
| 审计模式 | 支持并行子代理批量审查整个项目 |

---

## 📜 License

MIT License - 免费开源，随意使用。

---

<div align="center">

**🔪 蒙多想去哪就去哪！从来不犹豫！**

[⭐ Star](https://github.com/LiHongwei-cn/lihongwei-cn) · [🍴 Fork](https://github.com/LiHongwei-cn/lihongwei-cn/fork) · [📦 Releases](https://github.com/LiHongwei-cn/lihongwei-cn/releases)

</div>
