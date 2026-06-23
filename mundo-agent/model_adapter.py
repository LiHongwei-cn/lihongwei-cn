"""蒙多模型适配层 v3.2.0 — 运行时模型适配

职责：单模型运行时行为调整（token 限制、温度、payload 优化、流式支持）。
不要放模型选择逻辑 → 去 model_profiles.py。
不要放 provider 注册数据 → 去 setup.py PROVIDERS。
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ModelProfile:
    """模型画像 — 每个模型的脾气和习惯"""
    name: str
    provider: str
    model_id: str
    context_window: int = 128000
    supports_function_calling: bool = True
    supports_streaming: bool = True
    supports_reasoning: bool = False
    supports_vision: bool = False
    supports_json_mode: bool = False
    
    # Token 效率优化
    system_prompt_style: str = "concise"  # concise / detailed / minimal
    tool_description_style: str = "compact"  # compact / verbose
    max_tool_description_chars: int = 500
    
    # 行为特征
    temperature_default: float = 0.7
    max_tokens_default: int = 4096
    prefers_parallel_tools: bool = True
    
    # 成本优化
    supports_context_caching: bool = False
    cache_discount: float = 0.0  # 缓存命中折扣


# ═══════════════════════════════════════════════
# 模型画像库 — 每个模型的详细档案
# ═══════════════════════════════════════════════

MODEL_PROFILES: Dict[str, ModelProfile] = {
    # ─── DeepSeek 系列 ───
    "deepseek-chat": ModelProfile(
        name="DeepSeek V3",
        provider="deepseek",
        model_id="deepseek-chat",
        context_window=65536,
        supports_function_calling=True,
        supports_streaming=True,
        supports_json_mode=True,
        system_prompt_style="concise",
        tool_description_style="compact",
        max_tool_description_chars=300,
        temperature_default=0.7,
        max_tokens_default=4096,
        prefers_parallel_tools=True,
        supports_context_caching=True,
        cache_discount=0.9,  # 缓存命中打1折
    ),
    "deepseek-reasoner": ModelProfile(
        name="DeepSeek R1",
        provider="deepseek",
        model_id="deepseek-reasoner",
        context_window=65536,
        supports_function_calling=True,
        supports_streaming=True,
        supports_reasoning=True,
        supports_json_mode=True,
        system_prompt_style="minimal",  # R1 不需要过多指令
        tool_description_style="compact",
        max_tool_description_chars=200,
        temperature_default=0.6,  # R1 推荐较低温度
        max_tokens_default=8192,  # 推理任务需要更多输出
        prefers_parallel_tools=False,  # R1 串行推理更稳定
        supports_context_caching=True,
        cache_discount=0.9,
    ),
    "deepseek-coder": ModelProfile(
        name="DeepSeek Coder",
        provider="deepseek",
        model_id="deepseek-coder",
        context_window=65536,
        supports_function_calling=True,
        supports_streaming=True,
        supports_json_mode=True,
        system_prompt_style="concise",
        tool_description_style="compact",
        max_tool_description_chars=300,
        temperature_default=0.3,  # 代码任务低温更精确
        max_tokens_default=4096,
        prefers_parallel_tools=True,
        supports_context_caching=True,
        cache_discount=0.9,
    ),
    
    # ─── OpenAI 系列 ───
    "gpt-4o": ModelProfile(
        name="GPT-4o",
        provider="openai",
        model_id="gpt-4o",
        context_window=128000,
        supports_function_calling=True,
        supports_streaming=True,
        supports_json_mode=True,
        supports_vision=True,
        system_prompt_style="detailed",  # GPT-4o 遵循详细指令
        tool_description_style="verbose",
        max_tool_description_chars=800,
        temperature_default=0.7,
        max_tokens_default=4096,
        prefers_parallel_tools=True,
    ),
    "o3": ModelProfile(
        name="o3",
        provider="openai",
        model_id="o3",
        context_window=200000,
        supports_function_calling=True,
        supports_streaming=True,
        supports_reasoning=True,
        supports_json_mode=True,
        system_prompt_style="minimal",  # 推理模型不需要过多指令
        tool_description_style="compact",
        max_tool_description_chars=300,
        temperature_default=1.0,
        max_tokens_default=16384,
        prefers_parallel_tools=False,
    ),
    
    # ─── Anthropic Claude 系列 ───
    "claude-opus-4-20250514": ModelProfile(
        name="Claude Opus 4",
        provider="anthropic",
        model_id="claude-opus-4-20250514",
        context_window=200000,
        supports_function_calling=True,
        supports_streaming=True,
        supports_vision=True,
        system_prompt_style="detailed",
        tool_description_style="verbose",
        max_tool_description_chars=1000,
        temperature_default=0.7,
        max_tokens_default=4096,
        prefers_parallel_tools=True,
    ),
    "claude-sonnet-4-20250514": ModelProfile(
        name="Claude Sonnet 4",
        provider="anthropic",
        model_id="claude-sonnet-4-20250514",
        context_window=200000,
        supports_function_calling=True,
        supports_streaming=True,
        supports_vision=True,
        system_prompt_style="detailed",
        tool_description_style="verbose",
        max_tool_description_chars=800,
        temperature_default=0.7,
        max_tokens_default=4096,
        prefers_parallel_tools=True,
    ),
    
    # ─── Google Gemini 系列 ───
    "gemini-2.5-pro": ModelProfile(
        name="Gemini 2.5 Pro",
        provider="google",
        model_id="gemini-2.5-pro",
        context_window=1048576,  # 1M tokens!
        supports_function_calling=True,
        supports_streaming=True,
        supports_reasoning=True,
        supports_vision=True,
        supports_json_mode=True,
        system_prompt_style="detailed",
        tool_description_style="verbose",
        max_tool_description_chars=1000,
        temperature_default=0.7,
        max_tokens_default=8192,
        prefers_parallel_tools=True,
    ),
    
    # ─── 国产模型 ───
    "qwen-max": ModelProfile(
        name="通义千问 Max",
        provider="qwen",
        model_id="qwen-max",
        context_window=32000,
        supports_function_calling=True,
        supports_streaming=True,
        system_prompt_style="concise",
        tool_description_style="compact",
        max_tool_description_chars=400,
        temperature_default=0.7,
        max_tokens_default=4096,
        prefers_parallel_tools=True,
    ),
    "glm-4": ModelProfile(
        name="智谱 GLM-4",
        provider="zhipu",
        model_id="glm-4",
        context_window=128000,
        supports_function_calling=True,
        supports_streaming=True,
        system_prompt_style="concise",
        tool_description_style="compact",
        max_tool_description_chars=400,
        temperature_default=0.7,
        max_tokens_default=4096,
        prefers_parallel_tools=True,
    ),
    "kimi": ModelProfile(
        name="月之暗面 Kimi",
        provider="moonshot",
        model_id="moonshot-v1-128k",
        context_window=128000,
        supports_function_calling=True,
        supports_streaming=True,
        system_prompt_style="concise",
        tool_description_style="compact",
        max_tool_description_chars=400,
        temperature_default=0.7,
        max_tokens_default=4096,
        prefers_parallel_tools=True,
    ),
}


# ═══════════════════════════════════════════════
# 模型适配器
# ═══════════════════════════════════════════════

class ModelAdapter:
    """模型适配器 — 根据模型特性自动调整行为"""
    
    def __init__(self, model_id: str):
        self.profile = MODEL_PROFILES.get(model_id)
        if not self.profile:
            # 默认画像：未知模型用保守策略
            self.profile = ModelProfile(
                name=model_id,
                provider="unknown",
                model_id=model_id,
            )
    
    @property
    def name(self) -> str:
        return self.profile.name
    
    @property
    def is_deepseek(self) -> bool:
        return self.profile.provider == "deepseek"
    
    @property
    def is_reasoning_model(self) -> bool:
        return self.profile.supports_reasoning
    
    @property
    def supports_caching(self) -> bool:
        return self.profile.supports_context_caching
    
    # ─── System Prompt 优化 ───
    
    def optimize_system_prompt(self, base_prompt: str) -> str:
        """根据模型特性优化 system prompt"""
        style = self.profile.system_prompt_style
        
        if style == "minimal":
            # 推理模型：最小化指令，让模型自己推理
            return self._minimal_prompt(base_prompt)
        elif style == "concise":
            # 通用模型：精简但完整
            return self._concise_prompt(base_prompt)
        else:
            # 详细模型：完整指令
            return base_prompt
    
    def _minimal_prompt(self, prompt: str) -> str:
        """最小化 prompt — 适合推理模型"""
        # 保留核心指令，移除重复说明
        lines = prompt.split('\n')
        essential = []
        for line in lines:
            # 保留关键行
            if any(kw in line for kw in ['你是', '工具', '完成', '帝皇']):
                essential.append(line)
        return '\n'.join(essential[:10])  # 最多10行
    
    def _concise_prompt(self, prompt: str) -> str:
        """精简 prompt — 适合 DeepSeek V3"""
        # 移除冗余说明，保留核心
        return prompt
    
    # ─── Tool Schema 优化 ───
    
    def optimize_tool_schemas(self, schemas: List[Dict]) -> List[Dict]:
        """根据模型特性优化工具 schema"""
        max_chars = self.profile.max_tool_description_chars
        optimized = []
        
        for schema in schemas:
            s = dict(schema)
            func = s.get("function", {})
            
            # 截断过长的 description
            desc = func.get("description", "")
            if len(desc) > max_chars:
                func["description"] = desc[:max_chars-3] + "..."
            
            # 精简参数描述
            params = func.get("parameters", {})
            properties = params.get("properties", {})
            for prop_name, prop_info in properties.items():
                prop_desc = prop_info.get("description", "")
                if len(prop_desc) > 100:
                    prop_info["description"] = prop_desc[:97] + "..."
            
            s["function"] = func
            optimized.append(s)
        
        return optimized
    
    # ─── 调用参数优化 ───
    
    def get_call_params(self) -> Dict[str, Any]:
        """获取最优调用参数"""
        return {
            "temperature": self.profile.temperature_default,
            "max_tokens": self.profile.max_tokens_default,
            "stream": self.profile.supports_streaming,
        }
    
    def should_use_parallel_tools(self) -> bool:
        """是否应该并行调用工具"""
        return self.profile.prefers_parallel_tools
    
    # ─── Context Caching 优化 ───
    
    def get_cache_headers(self) -> Dict[str, str]:
        """获取缓存相关 headers"""
        if not self.profile.supports_context_caching:
            return {}
        
        if self.is_deepseek:
            return {"X-DeepSeek-Cache": "true"}
        
        return {}
    
    # ─── 错误处理策略 ───
    
    def get_retry_strategy(self, error_code: int) -> Dict[str, Any]:
        """根据错误码获取重试策略"""
        if error_code == 429:  # 限速
            return {"should_retry": True, "delay": 5, "max_retries": 3}
        elif error_code >= 500:  # 服务器错误
            return {"should_retry": True, "delay": 2, "max_retries": 2}
        elif error_code == 400:  # 请求错误
            return {"should_retry": False}
        elif error_code == 401:  # 认证错误
            return {"should_retry": False}
        else:
            return {"should_retry": True, "delay": 1, "max_retries": 1}
    
    # ─── 输出处理 ───
    
    def extract_response(self, response: Dict) -> Dict:
        """提取模型响应内容，处理不同模型的格式差异"""
        result = {
            "content": "",
            "reasoning": "",
            "tool_calls": [],
            "usage": {},
        }
        
        # 处理 reasoning_content（DeepSeek R1 特有）
        if "reasoning_content" in response:
            result["reasoning"] = response["reasoning_content"]
        
        # 处理 content
        if "content" in response:
            result["content"] = response["content"] or ""
        
        # 处理 tool_calls
        if "tool_calls" in response:
            result["tool_calls"] = response["tool_calls"]
        
        return result


# ═══════════════════════════════════════════════
# DeepSeek 专用优化器
# ═══════════════════════════════════════════════

class DeepSeekOptimizer:
    """DeepSeek 专用优化 — 最大化利用 DeepSeek 特性"""
    
    # DeepSeek 最佳实践
    BEST_PRACTICES = {
        "system_prompt": [
            "使用简洁直接的指令，避免冗长说明",
            "明确指定输出格式（JSON/Markdown/纯文本）",
            "对于代码任务，指定语言和风格",
            "利用 DeepSeek 的推理能力，不预设解题路径",
        ],
        "function_calling": [
            "工具描述要精确简洁，300字符以内",
            "参数描述用一句话说清楚",
            "支持并行调用，但复杂任务建议串行",
            "工具返回结果控制在合理长度",
        ],
        "token_optimization": [
            "利用 Context Caching：保持 system prompt 稳定",
            "缓存命中可降 90% 成本",
            "精简工具描述，减少 prompt tokens",
            "使用流式输出减少首 token 延迟",
        ],
        "error_handling": [
            "429 限速：指数退避重试",
            "500 服务器错误：重试2次",
            "上下文溢出：压缩上下文后重试",
            "网络超时：增加超时时间",
        ],
    }
    
    @staticmethod
    def get_optimal_model(task_type: str) -> str:
        """根据任务类型选择最优 DeepSeek 模型"""
        task_lower = task_type.lower()
        
        # 推理任务
        if any(kw in task_lower for kw in ['推理', '分析', 'debug', '复杂', '算法', '数学']):
            return "deepseek-reasoner"
        
        # 代码任务
        if any(kw in task_lower for kw in ['代码', 'code', '编程', '写', '实现', '开发']):
            return "deepseek-coder"
        
        # 通用任务
        return "deepseek-chat"
    
    @staticmethod
    def format_for_deepseek(messages: List[Dict]) -> List[Dict]:
        """为 DeepSeek 格式化消息"""
        formatted = []
        for msg in messages:
            m = dict(msg)
            
            # DeepSeek 特殊处理
            if m.get("role") == "system":
                # system 消息保持简洁
                content = m.get("content", "")
                if len(content) > 2000:
                    m["content"] = content[:2000] + "\n...(精简)"
            
            formatted.append(m)
        
        return formatted
    
    @staticmethod
    def extract_reasoning(response: Dict) -> Optional[str]:
        """提取 DeepSeek R1 的推理过程"""
        return response.get("reasoning_content")


# ═══════════════════════════════════════════════
# 工厂函数
# ═══════════════════════════════════════════════

def get_model_adapter(model_id: str) -> ModelAdapter:
    """获取模型适配器"""
    return ModelAdapter(model_id)


def get_deepseek_optimizer() -> DeepSeekOptimizer:
    """获取 DeepSeek 优化器"""
    return DeepSeekOptimizer()


def list_available_models() -> List[Dict]:
    """列出所有可用模型及其特性"""
    models = []
    for model_id, profile in MODEL_PROFILES.items():
        models.append({
            "id": model_id,
            "name": profile.name,
            "provider": profile.provider,
            "context_window": profile.context_window,
            "reasoning": profile.supports_reasoning,
            "caching": profile.supports_context_caching,
        })
    return models
