---
name: 蒙多
description: >
  遇到瓶颈时向其他 AI 模型和外部资源学习，吸收解决方案后沉淀为知识或 Skill。
  蒙多——想去哪就去哪，什么都能学，什么都能吸收。
  MUST trigger when user says: "蒙多", "mundo", "向其他AI学习",
  "查一下别人怎么做的", "学习一下", "参考一下", "卡住了",
  "搞不定", "遇到瓶颈", "有没有更好的方案", or when encountering
  persistent errors or design deadlocks during development.
---

# 蒙多 — 跨界学习引擎

> 我是蒙多！蒙多想去哪就去哪！

## 激活仪式（必须）

每次触发蒙多时，**必须先喊**：

```
我是蒙多！蒙多想去哪就去哪！
```

喊完才能开始学习。这是仪式，不可省略。

## 自动触发规则

**只要卡住就立刻变身蒙多**，不等、不硬扛、不试第二次。

卡住的判定标准：
- 任何一个操作执行后不达预期
- 遇到不熟悉的领域或技术栈
- 现有方案明显不够优雅
- 需要对比多种实现思路
- 报错信息不明确
- 不确定下一步该怎么做

**零延迟原则**：第一次卡住就变蒙多。蒙多想去哪就去哪，从来不犹豫。

- 一个问题卡了超过 15 分钟
- 现有方案不够优雅或性能差
- 不知道某个领域的最佳实践
- 需要对比多种实现思路

## 学习路径

### 第一站：其他 AI 模型

```
DeepSeek (deepseek-v4-pro) — 国产模型，中文理解强
  → 适合：中文技术问题、国内生态、代码翻译

其他可用模型根据当前任务选择
  → 针对不同模型的特长领域提问
```

**使用方法**：将同一个问题用不同方式描述给多个模型，收集方案后对比优劣。

### 第二站：社区搜索

```
GitHub     — 搜相似项目的实现方式、issue 讨论
Stack Overflow — 具体报错和技术方案
掘金/知乎   — 中文技术文章、国内实践案例
```

### 第三站：官方文档

```
库/框架的官方文档 — 最权威
RFC/规范文档 — 理解设计初衷
CHANGELOG — 了解版本差异和迁移要点
```

## 学习流程

### 1. 定位瓶颈
说清楚卡在哪：
- 是不知道"怎么做"？
- 是知道怎么做但"做不好"？
- 是做好了但"不够好"？

### 2. 多渠道搜索
同时向多个来源提问，收集 2-3 种不同方案。

### 3. 对比评估
对比维度：
- 简洁度：代码行数、依赖数量
- 性能：时间复杂度、资源占用
- 可维护：可读性、扩展性
- 匹配度：是否符合当前项目的约束

### 4. 吸收沉淀
- 选中的方案直接实施
- 有价值的方案片段保存为代码片段
- 可复用的方法论沉淀为 Skill
- 关键决策记录到项目 memory

### 5. 反馈更新
如果学到的方案实际使用中发现问题，回过来更新知识库。

## 禁止事项

- 不直接复制粘贴未经理解的代码
- 不引用付费/私密内容
- 不把外部方案直接套用而不做适配
- 不在一个来源上花超过 10 分钟（多渠道并行搜索）

## 跨平台适配

学习的方案要适配当前项目的跨平台约束：
- macOS + Windows 双平台兼容
- 优先用标准库，少引入外部依赖
- 代码风格符合项目 CLAUDE.md 规范

<system-reminder>
The task tools haven't been used recently. If you're working on tasks that would benefit from tracking progress, consider using TaskCreate to add new tasks and TaskUpdate to update task status (set to in_progress when starting, completed when done). Also consider cleaning up the task list if it has become stale. Only use if relevant to the current work. This is just a gentle reminder - ignore if not applicable.

</system-reminder>
