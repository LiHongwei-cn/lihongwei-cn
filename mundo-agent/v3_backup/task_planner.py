"""蒙多任务规划与多模型协调系统 v1.0

核心能力：
1. 任务规划：根据用户任务生成完整的规范化执行流程文档
2. 分身协调：多个分身并行执行，各自选择最优模型
3. 多模型交叉：跨AI模型家族的最优模型组合
4. 评级系统：基于测试和反馈的模型评级

最新模型信息（2026年6月）：
- DeepSeek: V4-Pro / V4-Flash / R1（V3系列7月24日退役）
- 小米 MiMo: V2.5-Pro / V2.5 / Flash（V2系列6月30日退役）
- OpenAI: GPT-5.5 / GPT-5.4 / GPT-5.4-mini
- Anthropic: Claude Opus 4 / Sonnet 4 / Haiku 4.5
- Google: Gemini 2.5 Pro / Flash / Flash-Lite
- 阿里 Qwen: Qwen3 Max / Plus / Turbo / Coder
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


# ═══════════════════════════════════════════════
# 最新模型数据库（2026年6月）
# ═══════════════════════════════════════════════

LATEST_MODELS = {
    "deepseek": {
        "name": "DeepSeek",
        "models": {
            "deepseek-v4-pro": {
                "name": "DeepSeek V4 Pro",
                "context": 1000000,
                "max_output": 384000,
                "price_input": 1.74,
                "price_output": 3.48,
                "cache_discount": 0.9,
                "strengths": ["旗舰", "推理", "代码", "Agent", "长文本"],
                "tier": "flagship",
                "speed": "medium",
                "released": "2026-04-23",
                "retires": None,
            },
            "deepseek-v4-flash": {
                "name": "DeepSeek V4 Flash",
                "context": 1000000,
                "max_output": 384000,
                "price_input": 0.14,
                "price_output": 0.28,
                "cache_discount": 0.9,
                "strengths": ["快速", "性价比", "通用", "长文本"],
                "tier": "standard",
                "speed": "fast",
                "released": "2026-04-23",
                "retires": None,
            },
            "deepseek-r1": {
                "name": "DeepSeek R1",
                "context": 65536,
                "max_output": 8192,
                "price_input": 0.55,
                "price_output": 2.19,
                "cache_discount": 0.9,
                "strengths": ["推理", "CoT", "数学", "逻辑", "分析"],
                "tier": "flagship",
                "speed": "slow",
                "released": "2025-01-20",
                "retires": None,
            },
        },
        "default": "deepseek-v4-flash",
    },
    "xiaomi": {
        "name": "小米 MiMo",
        "models": {
            "mimo-v2.5-pro": {
                "name": "MiMo-V2.5-Pro",
                "context": 1000000,
                "max_output": 128000,
                "price_input": 1.0,
                "price_output": 3.0,
                "cache_discount": 0.8,
                "strengths": ["旗舰", "推理", "Agent", "代码", "长文本"],
                "tier": "flagship",
                "speed": "medium",
                "released": "2026-04-22",
                "retires": None,
            },
            "mimo-v2.5": {
                "name": "MiMo-V2.5",
                "context": 1000000,
                "max_output": 128000,
                "price_input": 0.14,
                "price_output": 0.28,
                "cache_discount": 0.8,
                "strengths": ["多模态", "视觉", "音频", "Agent", "性价比"],
                "tier": "standard",
                "speed": "medium",
                "released": "2026-04-22",
                "retires": None,
            },
            "mimo-v2-flash": {
                "name": "MiMo-V2-Flash",
                "context": 128000,
                "max_output": 32000,
                "price_input": 0.05,
                "price_output": 0.10,
                "cache_discount": 0.8,
                "strengths": ["快速", "轻量", "日常"],
                "tier": "economy",
                "speed": "fast",
                "released": "2026-03-18",
                "retires": None,
            },
        },
        "default": "mimo-v2.5",
    },
    "openai": {
        "name": "OpenAI",
        "models": {
            "gpt-5.5": {
                "name": "GPT-5.5",
                "context": 1000000,
                "max_output": 32000,
                "price_input": 5.0,
                "price_output": 30.0,
                "cache_discount": 0.5,
                "strengths": ["旗舰", "推理", "代码", "Agent", "研究"],
                "tier": "flagship",
                "speed": "medium",
                "released": "2026-04-23",
                "retires": None,
            },
            "gpt-5.4": {
                "name": "GPT-5.4",
                "context": 1000000,
                "max_output": 32000,
                "price_input": 2.50,
                "price_output": 15.0,
                "cache_discount": 0.5,
                "strengths": ["通用", "生产", "性价比"],
                "tier": "standard",
                "speed": "medium",
                "released": "2026-03-01",
                "retires": None,
            },
            "gpt-5.4-mini": {
                "name": "GPT-5.4 Mini",
                "context": 128000,
                "max_output": 16000,
                "price_input": 0.40,
                "price_output": 1.60,
                "cache_discount": 0.5,
                "strengths": ["快速", "低成本", "轻量"],
                "tier": "economy",
                "speed": "fast",
                "released": "2026-03-01",
                "retires": None,
            },
        },
        "default": "gpt-5.4",
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "models": {
            "claude-opus-4": {
                "name": "Claude Opus 4",
                "context": 200000,
                "max_output": 32000,
                "price_input": 15.0,
                "price_output": 75.0,
                "cache_discount": 0.9,
                "strengths": ["旗舰", "复杂分析", "创意", "长文本", "安全"],
                "tier": "flagship",
                "speed": "slow",
                "released": "2025-05-22",
                "retires": None,
            },
            "claude-sonnet-4": {
                "name": "Claude Sonnet 4",
                "context": 200000,
                "max_output": 32000,
                "price_input": 3.0,
                "price_output": 15.0,
                "cache_discount": 0.9,
                "strengths": ["平衡", "代码", "Agent", "通用"],
                "tier": "standard",
                "speed": "medium",
                "released": "2025-05-22",
                "retires": None,
            },
            "claude-haiku-4.5": {
                "name": "Claude Haiku 4.5",
                "context": 200000,
                "max_output": 16000,
                "price_input": 0.80,
                "price_output": 4.0,
                "cache_discount": 0.9,
                "strengths": ["快速", "低成本", "轻量"],
                "tier": "economy",
                "speed": "fast",
                "released": "2025-03-01",
                "retires": None,
            },
        },
        "default": "claude-sonnet-4",
    },
    "google": {
        "name": "Google Gemini",
        "models": {
            "gemini-2.5-pro": {
                "name": "Gemini 2.5 Pro",
                "context": 1048576,
                "max_output": 65536,
                "price_input": 1.25,
                "price_output": 10.0,
                "cache_discount": 0.75,
                "strengths": ["旗舰", "推理", "代码", "1M上下文", "多模态"],
                "tier": "flagship",
                "speed": "medium",
                "released": "2025-03-01",
                "retires": None,
            },
            "gemini-2.5-flash": {
                "name": "Gemini 2.5 Flash",
                "context": 1048576,
                "max_output": 65536,
                "price_input": 0.15,
                "price_output": 0.60,
                "cache_discount": 0.75,
                "strengths": ["快速", "性价比", "1M上下文", "多模态"],
                "tier": "standard",
                "speed": "fast",
                "released": "2025-03-01",
                "retires": None,
            },
        },
        "default": "gemini-2.5-flash",
    },
    "qwen": {
        "name": "阿里 Qwen",
        "models": {
            "qwen-max": {
                "name": "Qwen3 Max",
                "context": 131072,
                "max_output": 32000,
                "price_input": 2.4,
                "price_output": 9.6,
                "cache_discount": 0.5,
                "strengths": ["旗舰", "推理", "代码", "Agent"],
                "tier": "flagship",
                "speed": "medium",
                "released": "2026-01-01",
                "retires": None,
            },
            "qwen-plus": {
                "name": "Qwen3.5 Plus",
                "context": 131072,
                "max_output": 32000,
                "price_input": 0.8,
                "price_output": 3.2,
                "cache_discount": 0.5,
                "strengths": ["平衡", "通用", "性价比"],
                "tier": "standard",
                "speed": "medium",
                "released": "2026-02-01",
                "retires": None,
            },
            "qwen-coder": {
                "name": "Qwen3 Coder",
                "context": 131072,
                "max_output": 32000,
                "price_input": 2.0,
                "price_output": 8.0,
                "cache_discount": 0.5,
                "strengths": ["代码", "编程", "调试", "重构"],
                "tier": "standard",
                "speed": "medium",
                "released": "2026-03-01",
                "retires": None,
            },
        },
        "default": "qwen-plus",
    },
}


# ═══════════════════════════════════════════════
# 模型评级系统
# ═══════════════════════════════════════════════

@dataclass
class ModelRating:
    """模型评级"""
    model_id: str
    provider: str
    overall_score: float = 0.0  # 综合评分 0-100
    coding_score: float = 0.0   # 代码能力
    reasoning_score: float = 0.0  # 推理能力
    creative_score: float = 0.0   # 创意能力
    speed_score: float = 0.0      # 速度评分
    cost_score: float = 0.0       # 性价比评分
    reliability_score: float = 0.0  # 可靠性评分
    user_feedback: float = 0.0    # 用户反馈评分
    last_updated: str = ""


# 预设评级（基于基准测试和用户反馈）
MODEL_RATINGS: Dict[str, ModelRating] = {
    # DeepSeek
    "deepseek-v4-pro": ModelRating(
        model_id="deepseek-v4-pro", provider="deepseek",
        overall_score=92, coding_score=95, reasoning_score=93,
        creative_score=85, speed_score=75, cost_score=90,
        reliability_score=90, user_feedback=91,
    ),
    "deepseek-v4-flash": ModelRating(
        model_id="deepseek-v4-flash", provider="deepseek",
        overall_score=85, coding_score=88, reasoning_score=82,
        creative_score=80, speed_score=95, cost_score=98,
        reliability_score=88, user_feedback=87,
    ),
    "deepseek-r1": ModelRating(
        model_id="deepseek-r1", provider="deepseek",
        overall_score=90, coding_score=85, reasoning_score=96,
        creative_score=78, speed_score=60, cost_score=85,
        reliability_score=88, user_feedback=89,
    ),
    
    # 小米 MiMo
    "mimo-v2.5-pro": ModelRating(
        model_id="mimo-v2.5-pro", provider="xiaomi",
        overall_score=91, coding_score=93, reasoning_score=92,
        creative_score=82, speed_score=72, cost_score=88,
        reliability_score=85, user_feedback=88,
    ),
    "mimo-v2.5": ModelRating(
        model_id="mimo-v2.5", provider="xiaomi",
        overall_score=86, coding_score=85, reasoning_score=84,
        creative_score=83, speed_score=78, cost_score=95,
        reliability_score=85, user_feedback=86,
    ),
    "mimo-v2-flash": ModelRating(
        model_id="mimo-v2-flash", provider="xiaomi",
        overall_score=78, coding_score=75, reasoning_score=72,
        creative_score=70, speed_score=92, cost_score=98,
        reliability_score=82, user_feedback=78,
    ),
    
    # OpenAI
    "gpt-5.5": ModelRating(
        model_id="gpt-5.5", provider="openai",
        overall_score=95, coding_score=96, reasoning_score=95,
        creative_score=92, speed_score=70, cost_score=60,
        reliability_score=95, user_feedback=94,
    ),
    "gpt-5.4": ModelRating(
        model_id="gpt-5.4", provider="openai",
        overall_score=88, coding_score=90, reasoning_score=88,
        creative_score=87, speed_score=78, cost_score=75,
        reliability_score=92, user_feedback=88,
    ),
    "gpt-5.4-mini": ModelRating(
        model_id="gpt-5.4-mini", provider="openai",
        overall_score=80, coding_score=82, reasoning_score=78,
        creative_score=76, speed_score=90, cost_score=90,
        reliability_score=88, user_feedback=80,
    ),
    
    # Anthropic
    "claude-opus-4": ModelRating(
        model_id="claude-opus-4", provider="anthropic",
        overall_score=94, coding_score=94, reasoning_score=93,
        creative_score=95, speed_score=60, cost_score=55,
        reliability_score=95, user_feedback=93,
    ),
    "claude-sonnet-4": ModelRating(
        model_id="claude-sonnet-4", provider="anthropic",
        overall_score=89, coding_score=91, reasoning_score=88,
        creative_score=90, speed_score=75, cost_score=80,
        reliability_score=92, user_feedback=89,
    ),
    "claude-haiku-4.5": ModelRating(
        model_id="claude-haiku-4.5", provider="anthropic",
        overall_score=82, coding_score=83, reasoning_score=80,
        creative_score=80, speed_score=92, cost_score=92,
        reliability_score=90, user_feedback=82,
    ),
    
    # Google
    "gemini-2.5-pro": ModelRating(
        model_id="gemini-2.5-pro", provider="google",
        overall_score=91, coding_score=92, reasoning_score=93,
        creative_score=85, speed_score=75, cost_score=85,
        reliability_score=88, user_feedback=90,
    ),
    "gemini-2.5-flash": ModelRating(
        model_id="gemini-2.5-flash", provider="google",
        overall_score=84, coding_score=85, reasoning_score=83,
        creative_score=80, speed_score=92, cost_score=95,
        reliability_score=86, user_feedback=84,
    ),
    
    # Qwen
    "qwen-max": ModelRating(
        model_id="qwen-max", provider="qwen",
        overall_score=88, coding_score=89, reasoning_score=88,
        creative_score=85, speed_score=75, cost_score=82,
        reliability_score=85, user_feedback=87,
    ),
    "qwen-plus": ModelRating(
        model_id="qwen-plus", provider="qwen",
        overall_score=82, coding_score=83, reasoning_score=81,
        creative_score=80, speed_score=82, cost_score=90,
        reliability_score=83, user_feedback=82,
    ),
    "qwen-coder": ModelRating(
        model_id="qwen-coder", provider="qwen",
        overall_score=86, coding_score=90, reasoning_score=84,
        creative_score=78, speed_score=78, cost_score=85,
        reliability_score=84, user_feedback=85,
    ),
}


# ═══════════════════════════════════════════════
# 任务规划器
# ═══════════════════════════════════════════════

class TaskPlanner:
    """任务规划器 — 生成规范化执行流程文档"""
    
    @staticmethod
    def generate_plan(task_description: str, provider: str = None) -> Dict:
        """根据任务描述生成完整的执行计划"""
        
        # 分析任务类型
        task_type = TaskPlanner._analyze_task_type(task_description)
        
        # 生成执行步骤
        steps = TaskPlanner._generate_steps(task_description, task_type)
        
        # 生成分身计划
        clones = TaskPlanner._generate_clone_plan(steps, provider)
        
        return {
            "task": task_description,
            "task_type": task_type,
            "steps": steps,
            "clones": clones,
            "estimated_time": TaskPlanner._estimate_time(steps),
            "estimated_tokens": TaskPlanner._estimate_tokens(steps),
        }
    
    @staticmethod
    def _analyze_task_type(task: str) -> str:
        """分析任务类型"""
        task_lower = task.lower()
        
        if any(kw in task_lower for kw in ['代码', 'code', '编程', '函数', 'class', 'python', 'javascript']):
            return "coding"
        elif any(kw in task_lower for kw in ['推理', '分析', '逻辑', '数学', '证明']):
            return "reasoning"
        elif any(kw in task_lower for kw in ['图片', '图像', '视频', '视觉']):
            return "multimodal"
        elif any(kw in task_lower for kw in ['写文章', '创作', '故事', '文案']):
            return "creative"
        elif any(kw in task_lower for kw in ['长文', '文档', '论文', '报告']):
            return "long_context"
        else:
            return "general"
    
    @staticmethod
    def _generate_steps(task: str, task_type: str) -> List[Dict]:
        """生成执行步骤"""
        steps = []
        
        if task_type == "coding":
            steps = [
                {"id": 1, "name": "需求分析", "desc": "理解任务需求，明确输入输出", "model_tier": "standard"},
                {"id": 2, "name": "架构设计", "desc": "设计代码结构和接口", "model_tier": "flagship"},
                {"id": 3, "name": "核心实现", "desc": "编写核心代码逻辑", "model_tier": "flagship"},
                {"id": 4, "name": "测试验证", "desc": "编写测试用例并验证", "model_tier": "standard"},
                {"id": 5, "name": "优化完善", "desc": "代码优化和文档编写", "model_tier": "standard"},
            ]
        elif task_type == "reasoning":
            steps = [
                {"id": 1, "name": "问题理解", "desc": "明确问题和约束条件", "model_tier": "standard"},
                {"id": 2, "name": "信息收集", "desc": "收集相关数据和背景", "model_tier": "standard"},
                {"id": 3, "name": "深度分析", "desc": "多角度分析问题", "model_tier": "flagship"},
                {"id": 4, "name": "推理验证", "desc": "验证推理过程和结论", "model_tier": "flagship"},
                {"id": 5, "name": "结果总结", "desc": "整理分析结果和建议", "model_tier": "standard"},
            ]
        elif task_type == "creative":
            steps = [
                {"id": 1, "name": "主题研究", "desc": "了解创作主题和风格", "model_tier": "standard"},
                {"id": 2, "name": "大纲构思", "desc": "构建内容框架", "model_tier": "flagship"},
                {"id": 3, "name": "内容创作", "desc": "撰写核心内容", "model_tier": "flagship"},
                {"id": 4, "name": "润色优化", "desc": "优化语言和表达", "model_tier": "standard"},
            ]
        else:
            steps = [
                {"id": 1, "name": "任务理解", "desc": "理解任务需求", "model_tier": "standard"},
                {"id": 2, "name": "信息收集", "desc": "收集相关信息", "model_tier": "standard"},
                {"id": 3, "name": "核心处理", "desc": "执行核心任务", "model_tier": "flagship"},
                {"id": 4, "name": "结果整理", "desc": "整理输出结果", "model_tier": "standard"},
            ]
        
        return steps
    
    @staticmethod
    def _generate_clone_plan(steps: List[Dict], provider: str = None) -> List[Dict]:
        """生成分身计划"""
        clones = []
        for step in steps:
            clone = {
                "step_id": step["id"],
                "step_name": step["name"],
                "model_tier": step["model_tier"],
                "recommended_models": TaskPlanner._get_recommended_models(
                    step["model_tier"], provider
                ),
            }
            clones.append(clone)
        return clones
    
    @staticmethod
    def _get_recommended_models(tier: str, provider: str = None) -> List[str]:
        """获取推荐模型列表"""
        recommendations = []
        
        for p, config in LATEST_MODELS.items():
            if provider and p != provider:
                continue
            for model_id, model_info in config["models"].items():
                if model_info["tier"] == tier:
                    rating = MODEL_RATINGS.get(model_id)
                    score = rating.overall_score if rating else 50
                    recommendations.append((model_id, score))
        
        # 按评分排序
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in recommendations[:3]]
    
    @staticmethod
    def _estimate_time(steps: List[Dict]) -> str:
        """估算执行时间"""
        total_minutes = len(steps) * 2  # 每步约2分钟
        if total_minutes < 60:
            return f"{total_minutes}分钟"
        else:
            return f"{total_minutes // 60}小时{total_minutes % 60}分钟"
    
    @staticmethod
    def _estimate_tokens(steps: List[Dict]) -> int:
        """估算token消耗"""
        base_tokens = 1000
        per_step = 2000
        return base_tokens + len(steps) * per_step
    
    @staticmethod
    def format_plan_document(plan: Dict) -> str:
        """格式化执行计划文档"""
        doc = f"""# 任务执行计划

## 任务描述
{plan['task']}

## 任务类型
{plan['task_type']}

## 执行步骤

"""
        for step in plan['steps']:
            doc += f"""### 步骤 {step['id']}: {step['name']}
- 描述: {step['desc']}
- 模型级别: {step['model_tier']}

"""
        
        doc += f"""## 分身计划

"""
        for clone in plan['clones']:
            doc += f"""### 分身 {clone['step_id']}: {clone['step_name']}
- 模型级别: {clone['model_tier']}
- 推荐模型: {', '.join(clone['recommended_models'][:3])}

"""
        
        doc += f"""## 预估资源
- 预计时间: {plan['estimated_time']}
- 预计Token: {plan['estimated_tokens']}

## 确认
请确认以上执行计划，或提出修改意见。
"""
        
        return doc


# ═══════════════════════════════════════════════
# 多模型协调器
# ═══════════════════════════════════════════════

class MultiModelCoordinator:
    """多模型协调器 — 跨AI模型家族的最优模型组合"""
    
    @staticmethod
    def select_best_model(
        task_type: str,
        providers: List[str] = None,
        budget: str = "balanced",
    ) -> Tuple[str, str]:
        """选择最优模型（跨所有provider）"""
        if providers is None:
            providers = list(LATEST_MODELS.keys())
        
        candidates = []
        
        for provider in providers:
            config = LATEST_MODELS.get(provider)
            if not config:
                continue
            
            for model_id, model_info in config["models"].items():
                rating = MODEL_RATINGS.get(model_id)
                if not rating:
                    continue
                
                # 根据任务类型计算匹配分数
                score = MultiModelCoordinator._calculate_score(
                    task_type, model_info, rating, budget
                )
                
                candidates.append((provider, model_id, score))
        
        # 按分数排序
        candidates.sort(key=lambda x: x[2], reverse=True)
        
        if candidates:
            best = candidates[0]
            return best[0], best[1]
        
        return "deepseek", "deepseek-v4-flash"
    
    @staticmethod
    def _calculate_score(
        task_type: str,
        model_info: Dict,
        rating: ModelRating,
        budget: str,
    ) -> float:
        """计算模型匹配分数"""
        score = rating.overall_score
        
        # 任务类型匹配
        if task_type == "coding":
            score = rating.coding_score
        elif task_type == "reasoning":
            score = rating.reasoning_score
        elif task_type == "creative":
            score = rating.creative_score
        elif task_type == "fast":
            score = rating.speed_score
        
        # 预算调整
        if budget == "low":
            score = score * 0.5 + rating.cost_score * 0.5
        elif budget == "balanced":
            score = score * 0.7 + rating.cost_score * 0.3
        # high: 保持原分数
        
        return score
    
    @staticmethod
    def get_optimal_combination(
        steps: List[Dict],
        providers: List[str] = None,
    ) -> List[Dict]:
        """为每个步骤获取最优模型组合"""
        combination = []
        
        for step in steps:
            task_type = step.get("task_type", "general")
            tier = step.get("model_tier", "standard")
            
            # 选择最优模型
            provider, model_id = MultiModelCoordinator.select_best_model(
                task_type, providers
            )
            
            combination.append({
                "step_id": step["id"],
                "step_name": step["name"],
                "provider": provider,
                "model_id": model_id,
                "model_name": LATEST_MODELS[provider]["models"][model_id]["name"],
            })
        
        return combination


# ═══════════════════════════════════════════════
# 导出
# ═══════════════════════════════════════════════

__all__ = [
    'LATEST_MODELS',
    'MODEL_RATINGS',
    'ModelRating',
    'TaskPlanner',
    'MultiModelCoordinator',
]
