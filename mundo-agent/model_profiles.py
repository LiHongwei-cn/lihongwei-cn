"""蒙多全模型夸克级适配系统 v1.0

自动检测用户选择的AI模型，根据任务类型智能选择最优子模型。
用户只需输入API Key，蒙多自动完成所有适配。

支持的模型家族：
- 小米 MiMo: V2.5-Pro / V2.5 / Flash
- DeepSeek: V4-Pro / V4-Flash / R1
- OpenAI: GPT-5.5 / GPT-5.4 / o3 / o4-mini
- Anthropic: Claude Opus 4 / Sonnet 4 / Haiku 4.5
- Google: Gemini 2.5 Pro / Flash / Flash-Lite
- 阿里 Qwen: Qwen3 Max / Qwen3.5 / Qwen3 Coder
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class TaskType(Enum):
    """任务类型枚举"""
    GENERAL = "general"           # 通用对话
    CODING = "coding"             # 代码编写
    REASONING = "reasoning"       # 推理分析
    CREATIVE = "creative"         # 创意写作
    MULTIMODAL = "multimodal"     # 多模态（图像/视频/音频）
    LONG_CONTEXT = "long_context" # 长文本处理
    FAST = "fast"                 # 快速响应
    AGENT = "agent"               # Agent任务


@dataclass
class ModelSpec:
    """模型规格"""
    model_id: str
    name: str
    context_window: int
    strengths: List[str]
    price_input: float  # 每百万token价格
    price_output: float
    speed_tier: str     # fast/medium/slow
    capability_tier: str  # flagship/standard/economy
    supports_function_calling: bool = True
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_reasoning: bool = False
    supports_caching: bool = False
    cache_discount: float = 0.0


@dataclass
class ProviderConfig:
    """模型提供商配置"""
    provider_id: str
    name: str
    base_url: str
    anthropic_base_url: str = ""
    env_key: str = ""
    models: Dict[str, ModelSpec] = field(default_factory=dict)
    default_model: str = ""
    region: str = "cn"  # cn/international


# ═══════════════════════════════════════════════
# 模型数据库 — 2026年最新
# ═══════════════════════════════════════════════

PROVIDER_DATABASE: Dict[str, ProviderConfig] = {
    # ─── 小米 MiMo ───
    "xiaomi": ProviderConfig(
        provider_id="xiaomi",
        name="小米 MiMo",
        base_url="https://token-plan-cn.xiaomimimo.com/v1",
        anthropic_base_url="https://token-plan-cn.xiaomimimo.com/anthropic",
        env_key="XIAOMI_API_KEY",
        default_model="mimo-v2.5-pro",
        region="cn",
        models={
            "mimo-v2.5-pro": ModelSpec(
                model_id="mimo-v2.5-pro",
                name="MiMo-V2.5-Pro",
                context_window=1000000,
                strengths=["推理", "Agent", "代码", "长文本"],
                price_input=1.0,
                price_output=3.0,
                speed_tier="medium",
                capability_tier="flagship",
                supports_vision=True,
                supports_reasoning=True,
            ),
            "mimo-v2.5": ModelSpec(
                model_id="mimo-v2.5",
                name="MiMo-V2.5",
                context_window=1000000,
                strengths=["多模态", "视觉", "音频", "Agent"],
                price_input=0.14,
                price_output=0.28,
                speed_tier="medium",
                capability_tier="standard",
                supports_vision=True,
            ),
            "mimo-v2-flash": ModelSpec(
                model_id="mimo-v2-flash",
                name="MiMo-V2-Flash",
                context_window=128000,
                strengths=["快速", "日常", "轻量"],
                price_input=0.05,
                price_output=0.10,
                speed_tier="fast",
                capability_tier="economy",
            ),
        },
    ),
    
    # ─── DeepSeek ───
    "deepseek": ProviderConfig(
        provider_id="deepseek",
        name="DeepSeek",
        base_url="https://api.deepseek.com/v1",
        env_key="DEEPSEEK_API_KEY",
        default_model="deepseek-chat",
        region="cn",
        models={
            "deepseek-chat": ModelSpec(
                model_id="deepseek-chat",
                name="DeepSeek V3",
                context_window=65536,
                strengths=["通用", "快速", "性价比"],
                price_input=0.27,
                price_output=1.10,
                speed_tier="fast",
                capability_tier="standard",
                supports_caching=True,
                cache_discount=0.9,
            ),
            "deepseek-reasoner": ModelSpec(
                model_id="deepseek-reasoner",
                name="DeepSeek R1",
                context_window=65536,
                strengths=["推理", "CoT", "数学", "逻辑"],
                price_input=0.55,
                price_output=2.19,
                speed_tier="medium",
                capability_tier="flagship",
                supports_reasoning=True,
                supports_caching=True,
                cache_discount=0.9,
            ),
        },
    ),
    
    # ─── OpenAI ───
    "openai": ProviderConfig(
        provider_id="openai",
        name="OpenAI",
        base_url="https://api.openai.com/v1",
        env_key="OPENAI_API_KEY",
        default_model="gpt-5.4",
        region="international",
        models={
            "gpt-5.5": ModelSpec(
                model_id="gpt-5.5",
                name="GPT-5.5",
                context_window=1000000,
                strengths=["旗舰", "推理", "代码", "Agent"],
                price_input=5.0,
                price_output=30.0,
                speed_tier="slow",
                capability_tier="flagship",
                supports_vision=True,
                supports_reasoning=True,
            ),
            "gpt-5.4": ModelSpec(
                model_id="gpt-5.4",
                name="GPT-5.4",
                context_window=1000000,
                strengths=["通用", "性价比", "生产"],
                price_input=2.50,
                price_output=15.0,
                speed_tier="medium",
                capability_tier="standard",
                supports_vision=True,
            ),
            "gpt-5.4-mini": ModelSpec(
                model_id="gpt-5.4-mini",
                name="GPT-5.4 Mini",
                context_window=128000,
                strengths=["快速", "低成本", "轻量"],
                price_input=0.40,
                price_output=1.60,
                speed_tier="fast",
                capability_tier="economy",
            ),
            "o3": ModelSpec(
                model_id="o3",
                name="o3",
                context_window=200000,
                strengths=["推理", "数学", "分析", "复杂逻辑"],
                price_input=2.0,
                price_output=8.0,
                speed_tier="slow",
                capability_tier="flagship",
                supports_reasoning=True,
            ),
            "o4-mini": ModelSpec(
                model_id="o4-mini",
                name="o4-mini",
                context_window=128000,
                strengths=["推理", "性价比", "快速推理"],
                price_input=1.10,
                price_output=4.40,
                speed_tier="medium",
                capability_tier="standard",
                supports_reasoning=True,
            ),
        },
    ),
    
    # ─── Anthropic Claude ───
    "anthropic": ProviderConfig(
        provider_id="anthropic",
        name="Anthropic Claude",
        base_url="https://api.anthropic.com/v1",
        env_key="ANTHROPIC_API_KEY",
        default_model="claude-sonnet-4-20250514",
        region="international",
        models={
            "claude-opus-4-20250514": ModelSpec(
                model_id="claude-opus-4-20250514",
                name="Claude Opus 4",
                context_window=200000,
                strengths=["旗舰", "复杂分析", "创意", "长文本"],
                price_input=15.0,
                price_output=75.0,
                speed_tier="slow",
                capability_tier="flagship",
                supports_vision=True,
            ),
            "claude-sonnet-4-20250514": ModelSpec(
                model_id="claude-sonnet-4-20250514",
                name="Claude Sonnet 4",
                context_window=200000,
                strengths=["平衡", "代码", "Agent", "通用"],
                price_input=3.0,
                price_output=15.0,
                speed_tier="medium",
                capability_tier="standard",
                supports_vision=True,
            ),
            "claude-haiku-4-5": ModelSpec(
                model_id="claude-haiku-4-5",
                name="Claude Haiku 4.5",
                context_window=200000,
                strengths=["快速", "低成本", "轻量"],
                price_input=0.80,
                price_output=4.0,
                speed_tier="fast",
                capability_tier="economy",
            ),
        },
    ),
    
    # ─── Google Gemini ───
    "google": ProviderConfig(
        provider_id="google",
        name="Google Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        env_key="GOOGLE_API_KEY",
        default_model="gemini-2.5-flash",
        region="international",
        models={
            "gemini-2.5-pro": ModelSpec(
                model_id="gemini-2.5-pro",
                name="Gemini 2.5 Pro",
                context_window=1048576,
                strengths=["旗舰", "推理", "代码", "1M上下文"],
                price_input=1.25,
                price_output=10.0,
                speed_tier="medium",
                capability_tier="flagship",
                supports_vision=True,
                supports_reasoning=True,
            ),
            "gemini-2.5-flash": ModelSpec(
                model_id="gemini-2.5-flash",
                name="Gemini 2.5 Flash",
                context_window=1048576,
                strengths=["快速", "性价比", "1M上下文"],
                price_input=0.15,
                price_output=0.60,
                speed_tier="fast",
                capability_tier="standard",
                supports_vision=True,
            ),
            "gemini-2.5-flash-lite": ModelSpec(
                model_id="gemini-2.5-flash-lite",
                name="Gemini 2.5 Flash-Lite",
                context_window=1048576,
                strengths=["超快", "超低成本", "轻量"],
                price_input=0.075,
                price_output=0.30,
                speed_tier="fast",
                capability_tier="economy",
            ),
        },
    ),
    
    # ─── 阿里 Qwen ───
    "qwen": ProviderConfig(
        provider_id="qwen",
        name="阿里通义千问",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        env_key="DASHSCOPE_API_KEY",
        default_model="qwen-max",
        region="cn",
        models={
            "qwen-max": ModelSpec(
                model_id="qwen-max",
                name="Qwen3 Max",
                context_window=131072,
                strengths=["旗舰", "推理", "代码", "Agent"],
                price_input=2.4,
                price_output=9.6,
                speed_tier="medium",
                capability_tier="flagship",
                supports_vision=True,
            ),
            "qwen-plus": ModelSpec(
                model_id="qwen-plus",
                name="Qwen3.5 Plus",
                context_window=131072,
                strengths=["平衡", "通用", "性价比"],
                price_input=0.8,
                price_output=3.2,
                speed_tier="medium",
                capability_tier="standard",
            ),
            "qwen-turbo": ModelSpec(
                model_id="qwen-turbo",
                name="Qwen3 Turbo",
                context_window=131072,
                strengths=["快速", "低成本", "轻量"],
                price_input=0.3,
                price_output=1.2,
                speed_tier="fast",
                capability_tier="economy",
            ),
            "qwen-coder-plus": ModelSpec(
                model_id="qwen-coder-plus",
                name="Qwen3 Coder",
                context_window=131072,
                strengths=["代码", "编程", "调试"],
                price_input=2.0,
                price_output=8.0,
                speed_tier="medium",
                capability_tier="standard",
            ),
        },
    ),
}


# ═══════════════════════════════════════════════
# 智能模型选择器
# ═══════════════════════════════════════════════

class SmartModelSelector:
    """智能模型选择器 — 根据任务自动选择最优模型"""
    
    # 任务类型关键词映射
    TASK_KEYWORDS = {
        TaskType.CODING: [
            "代码", "code", "编程", "写", "实现", "开发", "函数", "class",
            "debug", "调试", "重构", "refactor", "python", "javascript",
        ],
        TaskType.REASONING: [
            "推理", "分析", "逻辑", "数学", "证明", "为什么", "原因",
            "复杂", "算法", "reasoning", "analyze", "math",
        ],
        TaskType.CREATIVE: [
            "写文章", "创作", "故事", "诗歌", "文案", "创意",
            "creative", "write", "story", "poem",
        ],
        TaskType.MULTIMODAL: [
            "图片", "图像", "视频", "音频", "视觉", "看",
            "image", "video", "audio", "picture", "photo",
        ],
        TaskType.LONG_CONTEXT: [
            "长文", "文档", "论文", "报告", "总结", "摘要",
            "全文", "整篇", "long", "document", "paper",
        ],
        TaskType.FAST: [
            "快速", "简单", "查询", "翻译", "计算",
            "fast", "quick", "simple", "translate",
        ],
        TaskType.AGENT: [
            "agent", "自主", "执行", "任务", "工具", "调用",
            "搜索", "爬取", "自动化",
        ],
    }
    
    @classmethod
    def detect_task_type(cls, task_description: str) -> TaskType:
        """检测任务类型"""
        task_lower = task_description.lower()
        
        # 计算每个任务类型的匹配分数
        scores = {}
        for task_type, keywords in cls.TASK_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in task_lower)
            if score > 0:
                scores[task_type] = score
        
        if not scores:
            return TaskType.GENERAL
        
        return max(scores, key=scores.get)
    
    @classmethod
    def select_model(
        cls,
        provider: str,
        task_type: TaskType,
        context_length: int = 0,
        budget: str = "balanced",  # low/balanced/high
    ) -> str:
        """根据任务类型选择最优模型"""
        provider_config = PROVIDER_DATABASE.get(provider)
        if not provider_config:
            return ""
        
        models = provider_config.models
        if not models:
            return ""
        
        # 根据任务类型筛选模型
        candidates = []
        for model_id, spec in models.items():
            score = 0
            
            # 任务类型匹配
            if task_type == TaskType.CODING and "代码" in spec.strengths:
                score += 10
            elif task_type == TaskType.REASONING and ("推理" in spec.strengths or spec.supports_reasoning):
                score += 10
            elif task_type == TaskType.MULTIMODAL and spec.supports_vision:
                score += 10
            elif task_type == TaskType.FAST and spec.speed_tier == "fast":
                score += 10
            elif task_type == TaskType.LONG_CONTEXT and spec.context_window >= 200000:
                score += 10
            elif task_type == TaskType.AGENT and "Agent" in spec.strengths:
                score += 10
            
            # 上下文长度匹配
            if context_length > 0 and spec.context_window >= context_length:
                score += 5
            
            # 预算匹配
            if budget == "low" and spec.capability_tier == "economy":
                score += 5
            elif budget == "balanced" and spec.capability_tier == "standard":
                score += 5
            elif budget == "high" and spec.capability_tier == "flagship":
                score += 5
            
            candidates.append((model_id, score, spec))
        
        # 按分数排序，选择最优
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # 默认使用provider的默认模型
        if candidates[0][1] == 0:
            return provider_config.default_model
        
        return candidates[0][0]
    
    @classmethod
    def get_model_info(cls, provider: str, model_id: str) -> Optional[ModelSpec]:
        """获取模型详细信息"""
        provider_config = PROVIDER_DATABASE.get(provider)
        if not provider_config:
            return None
        return provider_config.models.get(model_id)


# ═══════════════════════════════════════════════
# 自动适配器
# ═══════════════════════════════════════════════

class AutoAdapter:
    """自动适配器 — 根据模型特性自动优化"""
    
    @staticmethod
    def get_provider_config(provider: str) -> Optional[ProviderConfig]:
        """获取provider配置"""
        return PROVIDER_DATABASE.get(provider)
    
    @staticmethod
    def get_optimal_params(provider: str, model_id: str) -> Dict:
        """获取模型最优参数"""
        spec = SmartModelSelector.get_model_info(provider, model_id)
        if not spec:
            return {"temperature": 0.7, "max_tokens": 4096}
        
        # 根据模型特性设置参数
        params = {
            "temperature": 0.7,
            "max_tokens": 4096,
            "stream": spec.supports_streaming,
        }
        
        # 代码任务低温
        if "代码" in spec.strengths:
            params["temperature"] = 0.3
        
        # 推理任务中低温
        if spec.supports_reasoning:
            params["temperature"] = 0.6
            params["max_tokens"] = 8192
        
        return params
    
    @staticmethod
    def optimize_system_prompt(prompt: str, provider: str, model_id: str) -> str:
        """根据模型优化system prompt"""
        spec = SmartModelSelector.get_model_info(provider, model_id)
        if not spec:
            return prompt
        
        # 推理模型：精简指令
        if spec.supports_reasoning and provider == "deepseek":
            lines = prompt.split('\n')
            essential = [l for l in lines if any(kw in l for kw in ['你是', '工具', '完成'])]
            return '\n'.join(essential[:10])
        
        # 旗舰模型：保持完整
        if spec.capability_tier == "flagship":
            return prompt
        
        # 其他模型：适度精简
        return prompt
    
    @staticmethod
    def optimize_tool_schemas(schemas: List[Dict], provider: str, model_id: str) -> List[Dict]:
        """根据模型优化工具schema"""
        spec = SmartModelSelector.get_model_info(provider, model_id)
        if not spec:
            return schemas
        
        # 设置描述长度限制
        max_desc = 500
        if spec.capability_tier == "economy":
            max_desc = 200
        elif spec.capability_tier == "standard":
            max_desc = 300
        
        optimized = []
        for schema in schemas:
            s = dict(schema)
            func = s.get("function", {})
            
            # 截断过长描述
            desc = func.get("description", "")
            if len(desc) > max_desc:
                func["description"] = desc[:max_desc-3] + "..."
            
            # 精简参数描述
            params = func.get("parameters", {})
            properties = params.get("properties", {})
            for prop_name, prop_info in properties.items():
                if isinstance(prop_info, dict):
                    prop_desc = prop_info.get("description", "")
                    if len(prop_desc) > 80:
                        prop_info["description"] = prop_desc[:77] + "..."
            
            s["function"] = func
            optimized.append(s)
        
        return optimized
    
    @staticmethod
    def get_cache_headers(provider: str) -> Dict[str, str]:
        """获取缓存相关headers"""
        if provider == "deepseek":
            return {"X-DeepSeek-Cache": "true"}
        return {}


# ═══════════════════════════════════════════════
# 导出
# ═══════════════════════════════════════════════

__all__ = [
    'TaskType',
    'ModelSpec',
    'ProviderConfig',
    'PROVIDER_DATABASE',
    'SmartModelSelector',
    'AutoAdapter',
]
