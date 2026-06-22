---
name: agentic-retrieval
description: Agentic 检索思维 — 蒙多的记忆不只是搜索，是主动推理
version: 1.0.0
author: mundo
tags:
  - rag
  - memory
  - retrieval
  - reasoning
dependencies: []
conflicts: []
required_tools:
  - search_files
  - web_search
priority: 85
---

# Agentic 检索思维 Skill

## 核心思想

传统 RAG：Query → Retrieve → Generate
Agentic RAG：Query → **自问** → **规划** → Retrieve → **验证** → Synthesize → Generate

蒙多的检索不是被动搜索，是主动推理。

## 检索决策树

面对一个问题时，蒙多先问自己：

```
1. 我现在知道答案吗？
   ├─ 确定知道 → 直接回答
   ├─ 不确定 → 需要检索
   └─ 完全不知道 → 必须检索

2. 如果需要检索，去哪找？
   ├─ 本地记忆（memory.db）→ recall/search
   ├─ 项目文件（当前目录）→ search_files
   ├─ 对话历史（conversations）→ FTS5
   ├─ 外部知识（互联网）→ web_search
   └─ 代码库（github等）→ http_request

3. 检索到了，可信吗？
   ├─ 多源一致 → 高可信
   ├─ 单源 → 需要交叉验证
   └─ 矛盾 → 重新检索或标注不确定性
```

## 自问清单（Self-Questioning）

在回答复杂问题前，蒙多必须过一遍：

1. **这个问题的前提成立吗？** — 用户的假设可能有误
2. **我有直接证据吗？** — 还是在靠推测？
3. **有没有遗漏的关键信息？** — 信息缺口在哪？
4. **我的结论能被证伪吗？** — 如果不能，可能是废话
5. **最可能出错的地方是什么？** — 主动找薄弱点

## 检索策略

### 策略一：关键词拆解
- 从问题中提取核心关键词
- 用不同关键词组合多次检索
- 合并去重

### 策略二：时间线追踪
- 先找最近的记录（新鲜度优先）
- 再找历史记录（完整性）
- 对比变化

### 策略三：上下文扩展
- 找到一个线索后，沿着关联扩展
- 同一项目的其他文件
- 同一类别的其他记忆

### 策略四：反向验证
- 找到答案后，反过来搜索"反面证据"
- 如果找到反面证据，标注不确定性

## 与蒙多记忆系统的集成

蒙多 memory.py 已有：
- FTS5 全文检索（对话历史）
- LIKE 后备（中文支持）
- 自动提取（规则模式）
- 项目隔离（按目录过滤）

**需要增强的：**
1. **自问层** — 检索前先判断是否真的需要检索
2. **多源融合** — 同时查记忆、文件、网络，合并结果
3. **可信度标注** — 每条检索结果标注可信度
4. **检索链路记录** — 记录检索过程，用于复盘

## 实践示例

```
用户问："蒙多的策略引擎支持几级优先级？"

蒙多的 Agentic 检索过程：
1. 自问：我知道 policy.py 的结构吗？→ 不完全确定
2. 规划：先查 policy.py 的 Severity 枚举 → 再查 PolicyEngine 的 evaluate
3. 检索：search_files("Severity|priority", path="policy.py")
4. 结果：Severity 有 LOW(1)/MEDIUM(2)/HIGH(3)/CRITICAL(4) 四级
5. 验证：确认 PolicyEngine.evaluate 确实用了这个排序
6. 回答：四级优先级，从 LOW(1) 到 CRITICAL(4)
```

## 参考资料

- [RAG 综述 arxiv 2506.00054](https://arxiv.org/html/2506.00054v1)
- [Agentic RAG 论文](https://link.springer.com/article/10.1007/s41019-025-00335-5)
- [Self-RAG: Learning to Retrieve](https://arxiv.org/abs/2310.11511)
