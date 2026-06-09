"""蒙多小米/DeepSeek 夸克级适配 v1.0

小米 MiMo 特性：
- MiMo-V2.5-Pro: 1.02T参数，42B激活，1M上下文，MoE架构
- MiMo-V2.5: 310B参数，15B激活，原生多模态（视觉+音频）
- API 同时支持 OpenAI 兼容和 Anthropic 兼容协议
- 支持 function calling、流式输出
- 支持内置联网搜索工具（web_search type）
- 价格：按量计费，Token Plan Credits

DeepSeek 特性：
- V3 (deepseek-chat): 通用模型，65K上下文
- R1 (deepseek-reasoner): 推理模型，支持CoT
- Coder: 代码专用
- Context Caching: 缓存命中打1折
- Anthropic API 兼容端点
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


# ═══════════════════════════════════════════════
# 小米 MiMo 夸克级优化器
# ═══════════════════════════════════════════════

class XiaomiOptimizer:
    """小米 MiMo 专用优化器"""
    
    # MiMo 最佳实践
    BEST_PRACTICES = {
        "system_prompt": [
            "MiMo 遵循详细指令，system prompt 可以更完整",
            "支持角色扮演，在 system prompt 中定义角色",
            "中文指令效果更好",
            "明确指定输出格式",
        ],
        "function_calling": [
            "使用 OpenAI 兼容格式的 tools 参数",
            "支持并行 function calling",
            "工具描述用中文更佳",
            "支持内置 web_search 工具",
        ],
        "token_optimization": [
            "1M 上下文窗口，不需要频繁压缩",
            "长文本可直接传入，无需分段",
            "利用 Anthropic 兼容端点的 cache_control",
        ],
        "multimodal": [
            "支持图像理解（视觉编码器）",
            "支持音频理解（音频编码器）",
            "多模态推理能力强",
        ],
    }
    
    # MiMo 模型配置
    MODELS = {
        "mimo-v2.5-pro": {
            "name": "MiMo-V2.5-Pro",
            "params": "1.02T (42B active)",
            "context": 1000000,
            "strengths": ["推理", "代码", "Agent", "长文本"],
            "temperature": 0.7,
            "max_tokens": 4096,
        },
        "mimo-v2.5": {
            "name": "MiMo-V2.5",
            "params": "310B (15B active)",
            "context": 1000000,
            "strengths": ["多模态", "视觉", "音频", "Agent"],
            "temperature": 0.7,
            "max_tokens": 4096,
        },
        "mimo-v2-flash": {
            "name": "MiMo-V2-Flash",
            "params": "轻量级",
            "context": 128000,
            "strengths": ["快速响应", "日常任务"],
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    }
    
    @staticmethod
    def get_optimal_model(task_type: str) -> str:
        """根据任务类型选择最优 MiMo 模型"""
        task_lower = task_type.lower()
        
        # 多模态任务
        if any(kw in task_lower for kw in ['图片', '图像', '视频', '音频', '视觉', 'image', 'video']):
            return "mimo-v2.5"
        
        # 复杂推理/Agent任务
        if any(kw in task_lower for kw in ['推理', '复杂', 'Agent', '自主', 'reasoning']):
            return "mimo-v2.5-pro"
        
        # 快速任务
        if any(kw in task_lower for kw in ['快速', '简单', '查询', 'fast', 'quick']):
            return "mimo-v2-flash"
        
        # 默认
        return "mimo-v2.5-pro"
    
    @staticmethod
    def format_system_prompt(base_prompt: str, **kwargs) -> str:
        """为 MiMo 格式化 system prompt"""
        return base_prompt
    
    @staticmethod
    def get_tool_config() -> Dict:
        """获取 MiMo 工具配置"""
        return {
            "supports_parallel": True,
            "max_tools": 20,
            "description_lang": "zh",  # 中文描述效果更好
        }
    
    @staticmethod
    def get_web_search_tool() -> Dict:
        """获取 MiMo 内置搜索工具配置"""
        return {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "搜索互联网获取最新信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词"
                        }
                    },
                    "required": ["query"]
                }
            }
        }


# ═══════════════════════════════════════════════
# DeepSeek 夸克级优化器
# ═══════════════════════════════════════════════

class DeepSeekQuarkOptimizer:
    """DeepSeek 夸克级优化器 — 最大化利用 DeepSeek 特性"""
    
    # DeepSeek 最佳实践（夸克级）
    BEST_PRACTICES = {
        "system_prompt": [
            "保持简洁直接，避免冗长说明",
            "不要在 system prompt 中放时间戳或随机内容（影响缓存命中）",
            "明确指定输出格式",
            "利用 DeepSeek 的推理能力，不预设解题路径",
            "R1 模型不需要过多指令，让模型自己推理",
        ],
        "function_calling": [
            "使用 OpenAI 兼容格式",
            "工具描述精确简洁，300字符以内",
            "参数描述用一句话说清楚",
            "支持并行调用，但复杂任务建议串行",
            "工具返回结果控制在合理长度",
        ],
        "context_caching": [
            "保持 system prompt 稳定（缓存前缀）",
            "不要在 prompt 中放时间戳、请求ID等随机内容",
            "缓存命中可降 90% 成本",
            "监控 prompt_cache_hit_tokens 优化缓存策略",
            "首 token 延迟从 13s 降到 500ms",
        ],
        "token_optimization": [
            "精简工具描述，减少 prompt tokens",
            "使用流式输出减少首 token 延迟",
            "合理设置 max_tokens，避免浪费",
            "利用缓存折扣：cached tokens 成本仅为 1/10",
        ],
        "error_handling": [
            "429 限速：指数退避重试",
            "500 服务器错误：重试2次",
            "上下文溢出：压缩上下文后重试",
            "网络超时：增加超时时间",
        ],
    }
    
    # DeepSeek 模型配置
    MODELS = {
        "deepseek-chat": {
            "name": "DeepSeek V3",
            "context": 65536,
            "strengths": ["通用", "快速", "性价比"],
            "temperature": 0.7,
            "max_tokens": 4096,
            "cache_discount": 0.9,
        },
        "deepseek-reasoner": {
            "name": "DeepSeek R1",
            "context": 65536,
            "strengths": ["推理", "CoT", "数学", "逻辑"],
            "temperature": 0.6,
            "max_tokens": 8192,
            "cache_discount": 0.9,
        },
        "deepseek-coder": {
            "name": "DeepSeek Coder",
            "context": 65536,
            "strengths": ["代码", "编程", "调试"],
            "temperature": 0.3,
            "max_tokens": 4096,
            "cache_discount": 0.9,
        },
    }
    
    @staticmethod
    def get_optimal_model(task_type: str) -> str:
        """根据任务类型选择最优 DeepSeek 模型"""
        task_lower = task_type.lower()
        
        # 推理任务
        if any(kw in task_lower for kw in ['推理', '分析', 'debug', '复杂', '算法', '数学', '逻辑']):
            return "deepseek-reasoner"
        
        # 代码任务
        if any(kw in task_lower for kw in ['代码', 'code', '编程', '写', '实现', '开发', '函数']):
            return "deepseek-coder"
        
        # 通用任务
        return "deepseek-chat"
    
    @staticmethod
    def format_system_prompt(base_prompt: str, model: str = "deepseek-chat") -> str:
        """为 DeepSeek 格式化 system prompt"""
        if model == "deepseek-reasoner":
            # R1 最小化指令
            lines = base_prompt.split('\n')
            essential = [l for l in lines if any(kw in l for kw in ['你是', '工具', '完成'])]
            return '\n'.join(essential[:8])
        elif model == "deepseek-coder":
            # Coder 强调代码相关
            return f"你是代码专家。{base_prompt}"
        else:
            # V3 保持简洁
            return base_prompt
    
    @staticmethod
    def optimize_tool_schemas(schemas: List[Dict], max_desc_chars: int = 300) -> List[Dict]:
        """优化工具 schema，减少 token 消耗"""
        optimized = []
        for schema in schemas:
            s = dict(schema)
            func = s.get("function", {})
            
            # 截断过长的 description
            desc = func.get("description", "")
            if len(desc) > max_desc_chars:
                func["description"] = desc[:max_desc_chars-3] + "..."
            
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
    def get_cache_headers() -> Dict[str, str]:
        """获取缓存相关 headers"""
        return {
            "X-DeepSeek-Cache": "true",
        }
    
    @staticmethod
    def format_for_cache(messages: List[Dict]) -> List[Dict]:
        """格式化消息以最大化缓存命中"""
        formatted = []
        for msg in messages:
            m = dict(msg)
            
            # 移除可能影响缓存的动态内容
            if m.get("role") == "system":
                content = m.get("content", "")
                # 移除时间戳等动态内容
                import re
                content = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', '[时间]', content)
                content = re.sub(r'请求ID: \w+', '[请求ID]', content)
                m["content"] = content
            
            formatted.append(m)
        
        return formatted
    
    @staticmethod
    def extract_reasoning(response: Dict) -> Optional[str]:
        """提取 DeepSeek R1 的推理过程"""
        return response.get("reasoning_content")


# ═══════════════════════════════════════════════
# 统一优化器工厂
# ═══════════════════════════════════════════════

class ModelOptimizerFactory:
    """模型优化器工厂 — 根据 provider 自动选择优化器"""
    
    _optimizers = {
        "xiaomi": XiaomiOptimizer,
        "deepseek": DeepSeekQuarkOptimizer,
    }
    
    @classmethod
    def get_optimizer(cls, provider: str):
        """获取指定 provider 的优化器"""
        return cls._optimizers.get(provider)
    
    @classmethod
    def get_optimal_model(cls, provider: str, task_type: str) -> str:
        """获取最优模型"""
        optimizer = cls.get_optimizer(provider)
        if optimizer:
            return optimizer.get_optimal_model(task_type)
        return ""
    
    @classmethod
    def format_system_prompt(cls, provider: str, base_prompt: str, **kwargs) -> str:
        """格式化 system prompt"""
        optimizer = cls.get_optimizer(provider)
        if optimizer:
            return optimizer.format_system_prompt(base_prompt, **kwargs)
        return base_prompt
    
    @classmethod
    def optimize_tools(cls, provider: str, schemas: List[Dict]) -> List[Dict]:
        """优化工具 schema"""
        optimizer = cls.get_optimizer(provider)
        if optimizer and hasattr(optimizer, 'optimize_tool_schemas'):
            return optimizer.optimize_tool_schemas(schemas)
        return schemas


# ═══════════════════════════════════════════════
# 导出
# ═══════════════════════════════════════════════

__all__ = [
    'XiaomiOptimizer',
    'DeepSeekQuarkOptimizer',
    'ModelOptimizerFactory',
]
