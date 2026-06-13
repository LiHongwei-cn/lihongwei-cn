"""蒙多的模型能力矩阵 — 智能路由，最大限度发挥每个模型"""

from typing import Optional, List, Dict

# ═══════════════════════════════════════════════
# 模型能力标注
# ═══════════════════════════════════════════════
# 每个模型标注擅长领域（1-10 分）和最佳用途

MODEL_PROFILES = {
    # ─── 中国模型 ───
    "xiaomi/mimo-v2.5-pro": {
        "label": "小米 MiMo",
        "strengths": {"general": 8, "coding": 7, "reasoning": 7, "chinese": 9, "math": 7, "speed": 9},
        "best_for": ["日常对话", "中文任务", "快速查询", "代码生成"],
        "cost": "low",
        "context": "128K",
    },
    "deepseek/deepseek-chat": {
        "label": "DeepSeek V3",
        "strengths": {"general": 8, "coding": 9, "reasoning": 9, "chinese": 8, "math": 9, "speed": 7},
        "best_for": ["代码编写", "数学推理", "复杂逻辑", "算法"],
        "cost": "low",
        "context": "128K",
    },
    "deepseek/deepseek-reasoner": {
        "label": "DeepSeek R1",
        "strengths": {"general": 7, "coding": 8, "reasoning": 10, "chinese": 7, "math": 10, "speed": 4},
        "best_for": ["深度推理", "数学证明", "复杂分析", "学术研究"],
        "cost": "medium",
        "context": "64K",
    },
    "qwen/qwen-max": {
        "label": "通义千问 Max",
        "strengths": {"general": 8, "coding": 7, "reasoning": 8, "chinese": 10, "math": 8, "speed": 7},
        "best_for": ["中文写作", "翻译", "文档理解", "多语言"],
        "cost": "medium",
        "context": "32K",
    },
    "zhipu/glm-4-plus": {
        "label": "智谱 GLM-4",
        "strengths": {"general": 8, "coding": 7, "reasoning": 7, "chinese": 9, "math": 7, "speed": 8},
        "best_for": ["工具调用", "中文对话", "知识问答"],
        "cost": "medium",
        "context": "128K",
    },
    "moonshot/moonshot-v1-128k": {
        "label": "Kimi 128K",
        "strengths": {"general": 7, "coding": 6, "reasoning": 7, "chinese": 9, "math": 6, "speed": 7},
        "best_for": ["长文档理解", "论文阅读", "文档总结"],
        "cost": "medium",
        "context": "128K",
    },
    "minimax/MiniMax-Text-01": {
        "label": "MiniMax",
        "strengths": {"general": 7, "coding": 6, "reasoning": 7, "chinese": 8, "math": 6, "speed": 8},
        "best_for": ["长上下文", "多轮对话", "创意写作"],
        "cost": "low",
        "context": "256K",
    },
    "tencent/hunyuan-pro": {
        "label": "腾讯混元",
        "strengths": {"general": 7, "coding": 8, "reasoning": 7, "chinese": 8, "math": 7, "speed": 7},
        "best_for": ["代码生成", "技术文档"],
        "cost": "medium",
        "context": "32K",
    },

    # ─── 国际模型 ───
    "openai/gpt-4o": {
        "label": "GPT-4o",
        "strengths": {"general": 9, "coding": 9, "reasoning": 9, "chinese": 7, "math": 8, "speed": 7},
        "best_for": ["通用任务", "代码", "推理", "多模态"],
        "cost": "high",
        "context": "128K",
    },
    "anthropic/claude-sonnet-4-20250514": {
        "label": "Claude Sonnet 4",
        "strengths": {"general": 9, "coding": 10, "reasoning": 9, "chinese": 7, "math": 8, "speed": 7},
        "best_for": ["代码编写", "重构", "调试", "架构设计", "安全分析"],
        "cost": "high",
        "context": "200K",
    },
    "anthropic/claude-opus-4": {
        "label": "Claude Opus 4",
        "strengths": {"general": 10, "coding": 10, "reasoning": 10, "chinese": 8, "math": 9, "speed": 3},
        "best_for": ["最复杂任务", "深度推理", "学术写作", "架构决策"],
        "cost": "very_high",
        "context": "200K",
    },
    "google/gemini-2.5-pro": {
        "label": "Gemini 2.5 Pro",
        "strengths": {"general": 9, "coding": 9, "reasoning": 9, "chinese": 7, "math": 9, "speed": 7},
        "best_for": ["长上下文", "多模态", "代码", "数学"],
        "cost": "high",
        "context": "1000K",
    },
    "mistral/mistral-large-latest": {
        "label": "Mistral Large",
        "strengths": {"general": 8, "coding": 8, "reasoning": 8, "chinese": 5, "math": 7, "speed": 8},
        "best_for": ["欧洲语言", "代码", "工具调用"],
        "cost": "medium",
        "context": "128K",
    },
    "groq/llama-3.3-70b-versatile": {
        "label": "Groq Llama 70B",
        "strengths": {"general": 7, "coding": 7, "reasoning": 7, "chinese": 5, "math": 6, "speed": 10},
        "best_for": ["超快响应", "简单任务", "批量处理"],
        "cost": "very_low",
        "context": "128K",
    },
    "xai/grok-3": {
        "label": "Grok-3",
        "strengths": {"general": 8, "coding": 8, "reasoning": 8, "chinese": 6, "math": 8, "speed": 7},
        "best_for": ["通用任务", "实时信息", "创意"],
        "cost": "high",
        "context": "128K",
    },

    # ─── 聚合平台 ───
    "openrouter/anthropic/claude-sonnet-4": {
        "label": "OpenRouter Claude",
        "strengths": {"general": 9, "coding": 10, "reasoning": 9, "chinese": 7, "math": 8, "speed": 7},
        "best_for": ["代码编写", "推理", "通用"],
        "cost": "medium",
        "context": "200K",
    },
    "siliconflow/deepseek-ai/DeepSeek-V3": {
        "label": "硅基 DeepSeek",
        "strengths": {"general": 8, "coding": 9, "reasoning": 9, "chinese": 8, "math": 9, "speed": 8},
        "best_for": ["代码", "推理", "便宜快速"],
        "cost": "very_low",
        "context": "128K",
    },
}

# 任务类型到能力维度的映射
TASK_TYPE_MAP = {
    "代码": "coding",
    "code": "coding",
    "编程": "coding",
    "coding": "coding",
    "调试": "coding",
    "debug": "coding",
    "重构": "coding",
    "refactor": "coding",
    "测试": "coding",
    "test": "coding",
    "推理": "reasoning",
    "reasoning": "reasoning",
    "分析": "reasoning",
    "analysis": "reasoning",
    "数学": "math",
    "math": "math",
    "计算": "math",
    "中文": "chinese",
    "写作": "chinese",
    "翻译": "chinese",
    "文档": "chinese",
    "通用": "general",
    "general": "general",
    "chinese": "chinese",
    "日常": "general",
    "快速": "speed",
    "speed": "speed",
    "批量": "speed",
    "简单": "speed",
    "math": "math",
    "reasoning": "reasoning",
}

# 协同模式：不同任务类型分配不同模型
COLLAB_PRESETS = {
    "全栈开发": {
        "desc": "前端+后端+数据库，代码为主",
        "primary": "coding",
        "secondary": "reasoning",
        "tertiary": "general",
    },
    "学术研究": {
        "desc": "文献阅读+推理分析+写作",
        "primary": "reasoning",
        "secondary": "chinese",
        "tertiary": "general",
    },
    "日常助手": {
        "desc": "问答+搜索+快速响应",
        "primary": "general",
        "secondary": "speed",
        "tertiary": "chinese",
    },
    "数学建模": {
        "desc": "数学推理+代码实现+文档",
        "primary": "math",
        "secondary": "coding",
        "tertiary": "chinese",
    },
}


def get_best_model_for_task(available_models: List[str], task_type: str) -> Optional[str]:
    """根据任务类型，从可用模型中选最佳"""
    dimension = TASK_TYPE_MAP.get(task_type, "general")

    best_score = -1
    best_model = None

    for model_key in available_models:
        profile = MODEL_PROFILES.get(model_key)
        if not profile:
            continue
        score = profile["strengths"].get(dimension, 5)
        if score > best_score:
            best_score = score
            best_model = model_key

    return best_model


def get_model_profile(model_key: str) -> Optional[Dict]:
    """获取模型能力档案"""
    return MODEL_PROFILES.get(model_key)


def suggest_collab_models(available_models: List[str], preset: str = None) -> Dict:
    """为协同模式推荐模型分配"""
    if preset and preset in COLLAB_PRESETS:
        cfg = COLLAB_PRESETS[preset]
        primary = get_best_model_for_task(available_models, cfg["primary"])
        secondary = get_best_model_for_task(
            [m for m in available_models if m != primary], cfg["secondary"]
        )
        tertiary = get_best_model_for_task(
            [m for m in available_models if m not in (primary, secondary)], cfg["tertiary"]
        )
        return {
            "preset": preset,
            "primary": primary,
            "secondary": secondary,
            "tertiary": tertiary,
        }

    # 无预设：按能力排序分配
    sorted_models = sorted(
        available_models,
        key=lambda m: sum(MODEL_PROFILES.get(m, {}).get("strengths", {}).values()),
        reverse=True
    )
    return {
        "preset": "auto",
        "primary": sorted_models[0] if len(sorted_models) > 0 else None,
        "secondary": sorted_models[1] if len(sorted_models) > 1 else None,
        "tertiary": sorted_models[2] if len(sorted_models) > 2 else None,
    }


def format_model_strengths(model_key: str) -> str:
    """格式化模型能力为可读字符串"""
    profile = MODEL_PROFILES.get(model_key)
    if not profile:
        return "未知"
    s = profile["strengths"]
    parts = []
    names = {"coding": "编码", "reasoning": "推理", "math": "数学", "chinese": "中文", "general": "通用", "speed": "速度"}
    for k, v in sorted(s.items(), key=lambda x: -x[1]):
        if v >= 8:
            parts.append(f"{names.get(k, k)}{v}/10")
    return " · ".join(parts[:4])
