"""任务分解器 — 复杂任务自动拆解

当用户输入涉及多步骤、多文件、多模块时，自动拆解为子任务序列。
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class SubTask:
    """子任务"""
    id: int
    description: str
    dependencies: List[int] = field(default_factory=list)
    tools_hint: List[str] = field(default_factory=list)
    status: str = "pending"  # pending / in_progress / done / failed
    result: str = ""


@dataclass
class TaskPlan:
    """任务计划"""
    original_request: str
    subtasks: List[SubTask]
    is_complex: bool
    reasoning: str


# 复杂任务特征模式
COMPLEX_PATTERNS = [
    # 多文件操作
    (r"(?:所有|每个|多个|批量).*(?:文件|模块|组件|页面)", "multi_file"),
    # 多步骤流程
    (r"(?:先|首先).*(?:然后|接着|再).*(?:最后|最终)", "multi_step"),
    # 涉及多个系统
    (r"(?:前端|后端|数据库|API|测试|部署).*(?:前端|后端|数据库|API|测试|部署)", "multi_system"),
    # 创建完整功能
    (r"(?:创建|搭建|实现|开发).*(?:系统|平台|应用|功能|模块)", "full_feature"),
    # 重构/迁移
    (r"(?:重构|迁移|升级|改造|优化)", "refactor"),
    # 调试复杂问题
    (r"(?:排查|调试|诊断|定位).*(?:问题|bug|错误|故障)", "debug"),
    # 同步/部署
    (r"(?:同步|部署|发布|上线|推送)", "deploy"),
    # 多语言/多平台
    (r"(?:跨平台|多语言|Windows.*Mac|Mac.*Windows)", "cross_platform"),
]

# 简单任务特征（排除复杂任务）
SIMPLE_PATTERNS = [
    r"^/?[a-zA-Z_]+\s*$",  # 纯命令调用
    r"^(?:查看|看看|检查|显示|列出|查|看)\s*\S{0,10}$",  # 短查询
    r"^(?:help|status|quit|exit|clear|reset)$",  # 系统命令
    r"^.{1,8}$",  # 极短输入（中文 8 字以内）
]


def is_complex_task(user_input: str) -> bool:
    """判断是否为复杂任务"""
    text = user_input.strip()

    # 简单任务排除
    for pattern in SIMPLE_PATTERNS:
        if re.match(pattern, text, re.IGNORECASE):
            return False

    # 复杂任务匹配
    for pattern, _ in COMPLEX_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    # 长度启发式：超过100字的描述性输入可能是复杂任务
    if len(text) > 100:
        return True

    return False


def decompose_task(user_input: str) -> Optional[TaskPlan]:
    """分解复杂任务为子任务序列

    返回 TaskPlan 或 None（如果不是复杂任务）
    """
    if not is_complex_task(user_input):
        return None

    # 匹配复杂任务类型
    task_type = "general"
    for pattern, t in COMPLEX_PATTERNS:
        if re.search(pattern, user_input, re.IGNORECASE):
            task_type = t
            break

    subtasks = _generate_subtasks(user_input, task_type)
    if len(subtasks) < 2:
        return None

    reasoning = _generate_reasoning(task_type, len(subtasks))

    return TaskPlan(
        original_request=user_input,
        subtasks=subtasks,
        is_complex=True,
        reasoning=reasoning,
    )


def _generate_subtasks(user_input: str, task_type: str) -> List[SubTask]:
    """根据任务类型生成子任务"""
    text = user_input.lower()
    subtasks = []
    sid = 1

    if task_type == "multi_file":
        subtasks = [
            SubTask(sid, "分析需求，确定涉及的文件范围", tools_hint=["search_files", "list_directory"]),
            SubTask(sid + 1, "逐个处理每个文件", dependencies=[sid], tools_hint=["read_file", "edit_file"]),
            SubTask(sid + 2, "验证所有文件修改的一致性", dependencies=[sid + 1], tools_hint=["terminal"]),
        ]
    elif task_type == "multi_step":
        # 从输入中提取步骤
        steps = re.findall(r'(?:先|首先|然后|接着|再|最后|最终)\s*([^，。,.]{5,50})', user_input)
        if steps:
            for i, step in enumerate(steps[:5]):
                deps = [sid + i - 1] if i > 0 else []
                subtasks.append(SubTask(sid + i, step.strip(), dependencies=deps))
        else:
            subtasks = [
                SubTask(sid, "分析任务，确定执行步骤"),
                SubTask(sid + 1, "执行核心操作", dependencies=[sid]),
                SubTask(sid + 2, "验证结果", dependencies=[sid + 1]),
            ]
    elif task_type == "multi_system":
        subtasks = [
            SubTask(sid, "分析系统架构，确定改动范围", tools_hint=["search_files"]),
            SubTask(sid + 1, "实现后端/API 改动", dependencies=[sid], tools_hint=["terminal", "edit_file"]),
            SubTask(sid + 2, "实现前端/UI 改动", dependencies=[sid], tools_hint=["edit_file"]),
            SubTask(sid + 3, "集成测试，验证端到端功能", dependencies=[sid + 1, sid + 2], tools_hint=["terminal"]),
        ]
    elif task_type == "full_feature":
        subtasks = [
            SubTask(sid, "需求分析：明确功能范围和接口", tools_hint=["search_files"]),
            SubTask(sid + 1, "设计：确定数据结构和模块划分", dependencies=[sid]),
            SubTask(sid + 2, "实现核心逻辑", dependencies=[sid + 1], tools_hint=["write_file", "edit_file"]),
            SubTask(sid + 3, "实现辅助功能（错误处理、边界情况）", dependencies=[sid + 2]),
            SubTask(sid + 4, "测试和验证", dependencies=[sid + 2, sid + 3], tools_hint=["terminal"]),
        ]
    elif task_type == "refactor":
        subtasks = [
            SubTask(sid, "分析现有代码，理解结构", tools_hint=["search_files", "read_file"]),
            SubTask(sid + 1, "制定重构计划", dependencies=[sid]),
            SubTask(sid + 2, "执行重构（保持功能不变）", dependencies=[sid + 1], tools_hint=["edit_file"]),
            SubTask(sid + 3, "验证重构后功能正常", dependencies=[sid + 2], tools_hint=["terminal"]),
        ]
    elif task_type == "debug":
        subtasks = [
            SubTask(sid, "复现问题，收集错误信息", tools_hint=["terminal"]),
            SubTask(sid + 1, "定位根因", dependencies=[sid], tools_hint=["search_files", "read_file"]),
            SubTask(sid + 2, "修复问题", dependencies=[sid + 1], tools_hint=["edit_file"]),
            SubTask(sid + 3, "验证修复", dependencies=[sid + 2], tools_hint=["terminal"]),
        ]
    elif task_type == "deploy":
        subtasks = [
            SubTask(sid, "检查当前状态，确认变更内容", tools_hint=["terminal"]),
            SubTask(sid + 1, "执行部署/同步操作", dependencies=[sid], tools_hint=["terminal"]),
            SubTask(sid + 2, "验证部署结果", dependencies=[sid + 1], tools_hint=["terminal", "web_search"]),
        ]
    elif task_type == "cross_platform":
        subtasks = [
            SubTask(sid, "分析平台差异，确定兼容性要求"),
            SubTask(sid + 1, "实现跨平台逻辑", dependencies=[sid], tools_hint=["write_file"]),
            SubTask(sid + 2, "生成各平台启动脚本", dependencies=[sid + 1], tools_hint=["write_file"]),
            SubTask(sid + 3, "验证各平台兼容性", dependencies=[sid + 2], tools_hint=["terminal"]),
        ]
    else:
        # 通用分解
        subtasks = [
            SubTask(sid, "分析任务需求"),
            SubTask(sid + 1, "执行核心操作", dependencies=[sid]),
            SubTask(sid + 2, "验证结果", dependencies=[sid + 1]),
        ]

    return subtasks


def _generate_reasoning(task_type: str, subtask_count: int) -> str:
    """生成任务分解的推理说明"""
    type_names = {
        "multi_file": "多文件操作",
        "multi_step": "多步骤流程",
        "multi_system": "多系统协作",
        "full_feature": "完整功能开发",
        "refactor": "重构/迁移",
        "debug": "复杂调试",
        "deploy": "部署/同步",
        "cross_platform": "跨平台开发",
        "general": "综合任务",
    }
    name = type_names.get(task_type, "复杂任务")
    return f"检测到{name}，拆解为 {subtask_count} 个子任务。"


def format_task_plan(plan: TaskPlan) -> str:
    """格式化任务计划为可读文本"""
    lines = [f"[任务分解] {plan.reasoning}", ""]
    for st in plan.subtasks:
        deps = ""
        if st.dependencies:
            dep_ids = ", ".join(str(d) for d in st.dependencies)
            deps = f" (依赖: #{dep_ids})"
        tools = ""
        if st.tools_hint:
            tools = f" [{', '.join(st.tools_hint)}]"
        lines.append(f"  {st.id}. {st.description}{deps}{tools}")
    return "\n".join(lines)
