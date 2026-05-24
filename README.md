<div align="center">

# 🔪 MUNDO — 蒙多跨界学习引擎

**我是蒙多！蒙多想去哪就去哪！**

[![GitHub stars](https://img.shields.io/github/stars/LiHongwei-cn/lihongwei-cn?style=social)](https://github.com/LiHongwei-cn/lihongwei-cn)
[![License: MIT](https://img.shields.io/badge/License-MIT-brightgreen.svg)](LICENSE)

> 🔪 卡住了？报错了？没思路？蒙多来也！
>
> 多 AI 模型 + GitHub + Stack Overflow + 掘金，并行搜索，四维对比，选最佳方案。
> 零延迟，第一次卡住就变蒙多。绝不犹豫。

</div>

---

## 🟣 蒙多是谁？

```
╔══════════════════════════════════════╗
║    🟣 我是蒙多！蒙多想去哪就去哪！  ║
╚══════════════════════════════════════╝
```

蒙多是 **Claude Code / Hermes Agent 通用 Skill**，专治各种"卡住"：

| 症状 | 蒙多的处方 |
|------|-----------|
| 😵 代码报错看不懂 | 多渠道搜索同类问题，对比 2-3 种解法 |
| 🤔 不知道怎么实现 | 向其他 AI 请教 + GitHub 找参考实现 |
| 😤 方案不够好 | 四维对比：简洁度、性能、可维护性、匹配度 |
| 🔄 重复踩同一个坑 | 沉淀为 Skill，下次自动规避 |

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

## 🔪 蒙多五步法

```
卡住了
  ↓
🔪 蒙多变身！（大喊：我是蒙多！蒙多想去哪就去哪！）
  ↓
┌─────────────────────────────────────┐
│  1️⃣  定位瓶颈                      │
│     不知道怎么做？做不好？不够好？   │
├─────────────────────────────────────┤
│  2️⃣  多渠道并行搜索                │
│     GitHub + Stack Overflow + 掘金  │
│     + 其他 AI 模型                  │
├─────────────────────────────────────┤
│  3️⃣  四维对比                      │
│     简洁度 ⭐ 性能 ⭐              │
│     可维护性 ⭐ 匹配度 ⭐          │
├─────────────────────────────────────┤
│  4️⃣  吸收实施                      │
│     理解 → 适配 → 代码落实          │
├─────────────────────────────────────┤
│  5️⃣  效果验证                      │
│     解决了吗？有副作用吗？          │
└─────────────────────────────────────┘
  ↓
✅ 解决了！或 → 沉淀为 Skill
```

---

## 🎯 触发方式

在 Claude Code 或 Hermes Agent 对话中，说以下任意一句即可触发蒙多：

- `蒙多`
- `卡住了`
- `搞不定`
- `报错了`
- `没思路`
- `遇到瓶颈`
- `有没有更好的方案`
- `mundo`

**蒙多规则：第一次卡住就变蒙多，绝不试第二次。**

---

## 🛠️ 技术细节

| 项目 | 说明 |
|------|------|
| 兼容工具 | Claude Code / Hermes Agent / Cursor / Aider / Windsurf / Codex |
| 搜索渠道 | GitHub、Stack Overflow、掘金、其他 AI 模型 |
| 对比维度 | 简洁度、性能、可维护性、匹配度 |
| 沉淀机制 | 有价值的方案自动创建为 Skill |
| 审计模式 | 支持并行子代理批量审查整个项目 |

---

## 📖 使用示例

```
你：这个 React 组件渲染太慢了，怎么办
蒙多：🔪 我是蒙多！蒙多想去哪就去哪！
     [搜索 GitHub + Stack Overflow + 向其他 AI 请教]
     [四维对比 3 种方案]
     → 推荐：React.memo + useMemo + 虚拟列表
     → 代码已写好，直接用
```

```
你：Python 爬虫被反爬了
蒙多：🔪 我是蒙多！蒙多想去哪就去哪！
     [发现 Scrapling 框架，自适应抓取 + 反检测]
     → 替换 requests，问题解决
     → 已沉淀为 Skill，下次自动规避
```

---

## 📜 License

MIT License - 免费开源，随意使用。

---

<div align="center">

**🔪 蒙多想去哪就去哪！从来不犹豫！**

[⭐ Star](https://github.com/LiHongwei-cn/lihongwei-cn) · [🍴 Fork](https://github.com/LiHongwei-cn/lihongwei-cn/fork) · [📦 Releases](https://github.com/LiHongwei-cn/lihongwei-cn/releases)

</div>
