# MUNDO v17 架构设计 — 任务确认 + Loop 工作流 + 三层记忆

## 核心改变

### 1. 任务确认流程（Task Confirmation Flow）

**原则**：先理解，再执行。用户确认后才动手。

```
用户输入任务
    ↓
蒙多阅读并识别任务
    ↓
蒙多输出完整任务文本：
  - 任务目标
  - 实现流程（步骤 1,2,3...）
  - 技术细节（使用的技术/方法/工具）
  - 预期输出
  - 潜在风险
  - 时间估算
    ↓
用户审阅任务文本
    ↓
┌─────────────────────────────────────┐
│  用户确认？                          │
│  ├─ 是 → 开始执行                    │
│  └─ 否 → 用户提出修改意见            │
│          ↓                          │
│          蒙多修改任务文本             │
│          ↓                          │
│          再次用户确认（循环）         │
└─────────────────────────────────────┘
```

### 2. Loop 工作流（Think-Code-Test-Optimize）

**原则**：思考 → 写代码 → 检测 → 优化，循环直到满足质量标准。

```
┌──────────────────────────────────────────────────┐
│                   LOOP 开始                       │
│                                                    │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐       │
│  │  思考   │ →  │ 写代码  │ →  │  检测   │       │
│  │ Think   │    │  Code   │    │  Test   │       │
│  └─────────┘    └─────────┘    └─────────┘       │
│       ↑                              │            │
│       │         ┌─────────┐          │            │
│       │         │  优化   │ ←────────┘            │
│       │         │Optimize │   (有问题)             │
│       │         └─────────┘                       │
│       │              │                            │
│       │              └────────────┐               │
│       │                           ↓               │
│       └───────────────────────────┘               │
│               (继续循环)                           │
│                                                    │
│  退出条件：                                        │
│  - 所有测试通过                                    │
│  - 质量评分达标                                    │
│  - 用户满意                                        │
└──────────────────────────────────────────────────┘
```

### 3. 三层记忆系统（Human-Like Memory）

**原则**：像人类大脑一样记忆，分层管理，动态调整。

```
┌─────────────────────────────────────────────────────────────┐
│                      蒙多的记忆系统                          │
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  短期记忆   │    │  中期记忆   │    │  长期记忆   │     │
│  │   Short     │ →  │   Medium    │ →  │    Long     │     │
│  │  (任务级)   │    │  (项目级)   │    │  (永久级)   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                  │                  │              │
│         ↓                  ↓                  ↓              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ 任务上下文  │    │ 项目上下文  │    │ 用户画像    │     │
│  │ 当前变量    │    │ 技术栈偏好  │    │ 身份信息    │     │
│  │ 临时发现    │    │ 常用模式    │    │ 长期偏好    │     │
│  │ 中间结果    │    │ 历史方案    │    │ 行为规则    │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                  │                  │              │
│         ↓                  ↓                  ↓              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ 任务结束    │    │  30 天过期  │    │  永久保留   │     │
│  │ 可遗忘      │    │  动态调整   │    │  不断完善   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 详细设计

### 一、任务确认流程

#### 1.1 任务识别阶段

蒙多接收用户输入后，执行以下分析：

```python
def analyze_task(user_input):
    """
    分析用户任务，生成结构化任务描述
    """
    task_analysis = {
        "goal": "任务的最终目标",
        "context": "任务背景和约束",
        "steps": [
            {
                "step": 1,
                "action": "具体动作",
                "method": "使用的技术/方法",
                "output": "预期产出"
            }
        ],
        "tech_stack": ["技术1", "技术2"],
        "risks": ["风险1", "风险2"],
        "time_estimate": "预估时间",
        "dependencies": ["依赖1", "依赖2"]
    }
    return task_analysis
```

#### 1.2 任务文本输出格式

```markdown
## 📋 任务分析报告

### 🎯 任务目标
[清晰描述最终要达成的目标]

### 📝 实现流程

**步骤 1：[步骤名称]**
- 动作：[具体做什么]
- 方法：[使用什么技术/方法]
- 输出：[预期产出]

**步骤 2：[步骤名称]**
- 动作：[具体做什么]
- 方法：[使用什么技术/方法]
- 输出：[预期产出]

...

### 🔧 技术细节

| 技术/工具 | 用途 | 版本/说明 |
|-----------|------|-----------|
| [技术1]   | [用途] | [说明]  |
| [技术2]   | [用途] | [说明]  |

### ⚠️ 潜在风险

1. [风险1] - [应对措施]
2. [风险2] - [应对措施]

### 📊 预期输出

- [输出1]：[描述]
- [输出2]：[描述]

### ⏱️ 时间估算

- 预计完成时间：[时间]
- 关键路径：[步骤]

---

**请确认以上任务分析是否准确？**
- 输入 **确认** 开始执行
- 输入 **修改意见** 蒙多将根据您的反馈调整
```

#### 1.3 用户确认循环

```python
def task_confirmation_loop():
    """
    任务确认循环，直到用户满意
    """
    while True:
        task_text = generate_task_analysis()
        display_task_text(task_text)

        user_response = get_user_input()

        if user_response == "确认":
            return task_text  # 用户确认，返回任务文本
        else:
            # 用户提出修改意见
            modifications = parse_modifications(user_response)
            task_text = apply_modifications(task_text, modifications)
            # 继续循环，再次展示修改后的任务文本
```

---

### 二、Loop 工作流

#### 2.1 思考阶段（Think）

```python
def think_phase(task, context):
    """
    思考阶段：分析问题，制定方案
    """
    analysis = {
        "problem_understanding": "深入理解问题本质",
        "approach_options": [
            {
                "name": "方案A",
                "pros": ["优点1", "优点2"],
                "cons": ["缺点1", "缺点2"],
                "complexity": "低/中/高"
            }
        ],
        "selected_approach": "选择的方案",
        "implementation_plan": ["步骤1", "步骤2"],
        "potential_issues": ["可能的问题1", "可能的问题2"]
    }
    return analysis
```

#### 2.2 编码阶段（Code）

```python
def code_phase(implementation_plan):
    """
    编码阶段：根据计划编写代码
    """
    code_result = {
        "files_created": ["file1.py", "file2.py"],
        "files_modified": ["existing_file.py"],
        "code_snippets": {
            "file1.py": "核心代码片段"
        },
        "implementation_notes": "实现说明"
    }
    return code_result
```

#### 2.3 检测阶段（Test）

```python
def test_phase(code_result):
    """
    检测阶段：验证代码正确性
    """
    test_result = {
        "unit_tests": {
            "passed": 10,
            "failed": 2,
            "coverage": "85%"
        },
        "integration_tests": {
            "passed": 5,
            "failed": 0
        },
        "issues_found": [
            {
                "file": "file1.py",
                "line": 42,
                "issue": "空指针异常",
                "severity": "高"
            }
        ],
        "quality_score": 78  # 0-100
    }
    return test_result
```

#### 2.4 优化阶段（Optimize）

```python
def optimize_phase(test_result):
    """
    优化阶段：修复问题，提升质量
    """
    optimization = {
        "fixes_applied": [
            {
                "issue": "空指针异常",
                "fix": "添加空值检查",
                "file": "file1.py"
            }
        ],
        "improvements": [
            {
                "aspect": "性能",
                "before": "O(n²)",
                "after": "O(n log n)"
            }
        ],
        "new_quality_score": 92
    }
    return optimization
```

#### 2.5 Loop 控制

```python
def workflow_loop(task):
    """
    主工作流循环
    """
    max_iterations = 5
    quality_threshold = 90
    context = load_context()

    for iteration in range(max_iterations):
        # 思考
        think_result = think_phase(task, context)

        # 编码
        code_result = code_phase(think_result["implementation_plan"])

        # 检测
        test_result = test_phase(code_result)

        # 检查是否达标
        if test_result["quality_score"] >= quality_threshold:
            if test_result["issues_found"]:
                # 还有问题，继续优化
                optimize_result = optimize_phase(test_result)
                context.update(optimize_result)
                continue
            else:
                # 达标，退出循环
                return {
                    "status": "success",
                    "iteration": iteration + 1,
                    "result": code_result
                }

        # 未达标，优化后继续
        optimize_result = optimize_phase(test_result)
        context.update(optimize_result)

    # 达到最大迭代次数
    return {
        "status": "max_iterations_reached",
        "iteration": max_iterations,
        "result": code_result
    }
```

---

### 三、三层记忆系统

#### 3.1 短期记忆（Short-Term Memory）

**特点**：
- 任务级别，任务结束后可遗忘
- 存储在内存中，快速访问
- 包含当前任务的上下文、变量、中间结果

**存储位置**：`memory/short-term/` 目录，每个任务一个文件

**数据结构**：

```json
{
  "task_id": "task_20260615_001",
  "created_at": "2026-06-15T10:00:00Z",
  "task_summary": "修复 React 组件渲染问题",
  "context": {
    "user_request": "这个组件渲染太慢了",
    "current_file": "src/components/DataTable.tsx",
    "error_messages": ["Warning: Cannot update a component during render"]
  },
  "variables": {
    "performance_metrics": {
      "before": "320ms",
      "target": "<50ms"
    },
    "optimization_attempts": 0
  },
  "intermediate_results": [
    {
      "step": 1,
      "action": "性能分析",
      "result": "发现不必要的重渲染",
      "timestamp": "2026-06-15T10:05:00Z"
    }
  ],
  "temporary_findings": [
    "React.memo 可以减少 80% 的重渲染",
    "useCallback 需要配合 useMemo 使用"
  ],
  "expires_at": "task_end"
}
```

**遗忘机制**：
- 任务完成 → 标记为可遗忘
- 重要发现 → 提取到中期记忆
- 24 小时后自动清理

#### 3.2 中期记忆（Medium-Term Memory）

**特点**：
- 项目级别，保留时间较长（30 天）
- 存储在文件系统中
- 包含技术栈偏好、常用模式、历史方案
- 动态调整，根据使用频率和效果更新

**存储位置**：`memory/medium-term/` 目录

**数据结构**：

```json
{
  "memory_id": "mt_20260615_001",
  "created_at": "2026-06-15",
  "last_accessed": "2026-06-15",
  "access_count": 5,
  "category": "technical_pattern",
  "tags": ["react", "performance", "optimization"],
  "content": {
    "pattern": "使用 React.memo + useCallback 优化列表渲染",
    "description": "当列表项包含复杂组件时，使用 React.memo 包裹，配合 useCallback 缓存事件处理函数",
    "example_code": "const ListItem = React.memo(({ item, onClick }) => {\n  const handleClick = useCallback(() => onClick(item.id), [item.id, onClick]);\n  return <div onClick={handleClick}>{item.name}</div>;\n});",
    "use_cases": ["大列表渲染", "频繁更新的组件", "复杂计算的组件"],
    "effectiveness": {
      "success_rate": 0.85,
      "average_improvement": "60%"
    }
  },
  "related_memories": ["mt_20260610_002", "mt_20260608_001"],
  "expires_at": "2026-07-15",
  "decay_rate": 0.1
}
```

**动态调整机制**：

```python
def adjust_medium_term_memory(memory, new_experience):
    """
    根据新经验调整中期记忆
    """
    # 更新访问次数
    memory["access_count"] += 1
    memory["last_accessed"] = current_timestamp()

    # 根据效果调整权重
    if new_experience["success"]:
        memory["content"]["effectiveness"]["success_rate"] = (
            memory["content"]["effectiveness"]["success_rate"] * 0.9 +
            1.0 * 0.1
        )
    else:
        memory["content"]["effectiveness"]["success_rate"] = (
            memory["content"]["effectiveness"]["success_rate"] * 0.9 +
            0.0 * 0.1
        )

    # 高频使用 → 延长过期时间
    if memory["access_count"] > 10:
        memory["expires_at"] = extend_expiry(memory["expires_at"], days=30)

    # 低效果 → 缩短过期时间
    if memory["content"]["effectiveness"]["success_rate"] < 0.3:
        memory["expires_at"] = shorten_expiry(memory["expires_at"], days=7)

    return memory
```

**遗忘机制**：
- 30 天过期，自动归档
- 低效果记忆加速衰减
- 高频使用记忆延长保留

#### 3.3 长期记忆（Long-Term Memory）

**特点**：
- 永久级别，不断完善的用户画像
- 存储在文件系统中，定期备份
- 包含用户身份、偏好、行为规则、长期目标
- 通过交互不断丰富和修正

**存储位置**：`memory/long-term/` 目录

**数据结构**：

```json
{
  "memory_id": "lt_user_profile",
  "created_at": "2026-05-18",
  "last_updated": "2026-06-15",
  "version": 3,
  "content": {
    "identity": {
      "name": "李洪伟",
      "role": "新能源汽车工程师",
      "expertise": ["MATLAB/Simulink", "车辆动力学", "电机控制"],
      "education": "硕士",
      "location": "中国"
    },
    "preferences": {
      "language": {
        "communication": "中文",
        "code": "英文命名"
      },
      "code_style": {
        "naming": "kebab-case",
        "comments": "简洁无冗余",
        "patterns": ["不可变数据", "函数式编程"]
      },
      "communication": {
        "style": "直接",
        "detail_level": "中等",
        "summary_required": false
      },
      "tools": {
        "os": "macOS",
        "editor": "VS Code",
        "terminal": "zsh"
      }
    },
    "behavior_rules": {
      "auto_push": true,
      "auto_sync": true,
      "file_location": "~/Desktop/lihongwei-cn/",
      "cross_platform": true,
      "open_source": true,
      "no_hardcoded_secrets": true
    },
    "project_context": {
      "current_focus": "新能源汽车仿真工具包",
      "long_term_goals": [
        "建设开源仿真工具包",
        "通过 GitHub Pages 分享教程",
        "降低控制策略开发门槛"
      ],
      "tech_stack": {
        "primary": ["MATLAB R2016b", "Python 3.12", "FastAPI"],
        "secondary": ["HTML/CSS", "微信小程序"],
        "tools": ["Git", "GitHub Pages", "Telegram Bot"]
      }
    },
    "interaction_history": {
      "total_sessions": 45,
      "common_tasks": ["代码开发", "Bug 修复", "文档编写"],
      "preferred_workflow": "先确认再执行",
      "feedback_style": "直接指出问题"
    }
  },
  "confidence_scores": {
    "identity": 0.95,
    "preferences": 0.90,
    "behavior_rules": 0.85,
    "project_context": 0.80
  },
  "update_log": [
    {
      "date": "2026-06-15",
      "field": "preferences.communication.style",
      "old_value": "不详",
      "new_value": "直接",
      "source": "用户反馈"
    }
  ]
}
```

**完善机制**：

```python
def update_long_term_memory(current_profile, new_observation):
    """
    通过新观察完善用户画像
    """
    # 识别需要更新的字段
    fields_to_update = identify_updates(current_profile, new_observation)

    for field in fields_to_update:
        # 计算置信度
        new_confidence = calculate_confidence(
            current_confidence=current_profile["confidence_scores"][field],
            observation_reliability=new_observation["reliability"],
            observation_count=new_observation["count"]
        )

        # 更新置信度
        current_profile["confidence_scores"][field] = new_confidence

        # 如果置信度足够高，更新内容
        if new_confidence > 0.7:
            old_value = get_nested_value(current_profile["content"], field)
            new_value = new_observation["value"]

            # 更新内容
            set_nested_value(current_profile["content"], field, new_value)

            # 记录更新日志
            current_profile["update_log"].append({
                "date": current_date(),
                "field": field,
                "old_value": old_value,
                "new_value": new_value,
                "source": new_observation["source"]
            })

    # 更新版本和时间戳
    current_profile["version"] += 1
    current_profile["last_updated"] = current_date()

    return current_profile
```

**遗忘机制**：
- 永不自动删除
- 低置信度字段标记为"待验证"
- 用户显式要求删除时才移除
- 定期备份到云端

---

### 四、记忆流转机制

#### 4.1 记忆升级路径

```
短期记忆 → 中期记忆 → 长期记忆
    ↓           ↓           ↓
  任务结束    30天过期    永久保留
    ↓           ↓           ↓
  可遗忘      动态调整    不断完善
```

#### 4.2 记忆提取规则

```python
def extract_memories(short_term_memory, task_result):
    """
    从短期记忆中提取有价值的信息到中期/长期记忆
    """
    # 提取技术模式到中期记忆
    if task_result["technical_pattern_discovered"]:
        create_medium_term_memory({
            "category": "technical_pattern",
            "content": task_result["technical_pattern"],
            "tags": task_result["tags"],
            "effectiveness": task_result["effectiveness"]
        })

    # 提取用户偏好到长期记忆
    if task_result["user_preference_observed"]:
        update_long_term_memory(
            field="preferences",
            new_value=task_result["user_preference"],
            source="task_interaction"
        )

    # 提取行为规则到长期记忆
    if task_result["behavior_rule_inferred"]:
        update_long_term_memory(
            field="behavior_rules",
            new_value=task_result["behavior_rule"],
            source="inferred_from_behavior"
        )
```

#### 4.3 记忆检索机制

```python
def retrieve_memories(task_context):
    """
    根据任务上下文检索相关记忆
    """
    memories = {
        "short_term": [],
        "medium_term": [],
        "long_term": []
    }

    # 检索短期记忆（当前任务相关）
    memories["short_term"] = search_short_term(
        keywords=task_context["keywords"],
        files=task_context["related_files"]
    )

    # 检索中期记忆（技术模式相关）
    memories["medium_term"] = search_medium_term(
        tags=task_context["tech_tags"],
        category=task_context["task_type"],
        min_effectiveness=0.6
    )

    # 检索长期记忆（用户偏好相关）
    memories["long_term"] = search_long_term(
        fields=["preferences", "behavior_rules", "project_context"]
    )

    return memories
```

---

### 五、实现计划

#### 5.1 阶段一：任务确认流程（1-2 天）

- [ ] 修改 SKILL.md，添加任务确认流程
- [ ] 实现任务分析函数
- [ ] 设计任务文本输出格式
- [ ] 实现用户确认循环

#### 5.2 阶段二：Loop 工作流（2-3 天）

- [ ] 设计工作流状态机
- [ ] 实现思考阶段
- [ ] 实现阶段
- [ ] 实现检测阶段
- [ ] 实现优化阶段
- [ ] 实现循环控制

#### 5.3 阶段三：三层记忆系统（3-5 天）

- [ ] 设计记忆数据结构
- [ ] 实现短期记忆
- [ ] 实现中期记忆
- [ ] 实现长期记忆
- [ ] 实现记忆流转机制
- [ ] 实现记忆检索机制

#### 5.4 阶段四：集成测试（1-2 天）

- [ ] 端到端测试
- [ ] 性能优化
- [ ] 文档更新

---

## 技术参考

### 已搜索的最佳实践

1. **任务确认流程**
   - LangChain 的 Human-in-the-loop 模式
   - AutoGPT 的任务确认机制
   - CrewAI 的任务委派确认

2. **Loop 工作流**
   - ReAct (Reasoning + Acting) 模式
   - Plan-and-Execute 架构
   - Reflexion 自我反思机制

3. **记忆系统**
   - MemGPT 的分层记忆架构
   - LangChain Memory 模块
   - Mem0 的统一记忆管理
   - 人类认知科学的记忆模型

---

*文档版本：v17.0.0*
*最后更新：2026-06-15*
*作者：蒙多架构组*
