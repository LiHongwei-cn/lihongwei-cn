"""
Mundo Agent 专业知识体系 v1.0

三大领域：编程工程 | AI Agent | 网络安全

这是蒙多的"大脑知识库"，所有决策和实现都必须基于这些专业知识。
"""

# ═══════════════════════════════════════════════════════════════════════════════
# 领域一：编程工程专业知识
# ═══════════════════════════════════════════════════════════════════════════════

PROGRAMMING_KNOWLEDGE = {
    "core_principles": {
        "SOLID": {
            "S": "单一职责原则 - 每个类/函数只有一个职责",
            "O": "开闭原则 - 对扩展开放，对修改关闭",
            "L": "里氏替换原则 - 子类可以替换父类",
            "I": "接口隔离原则 - 接口要小而专",
            "D": "依赖倒置原则 - 依赖抽象而非具体"
        },
        "DRY": "Don't Repeat Yourself - 避免代码重复",
        "KISS": "Keep It Simple, Stupid - 保持简单",
        "YAGNI": "You Aren't Gonna Need It - 不要过度设计"
    },
    
    "design_patterns": {
        "creational": ["Singleton", "Factory", "Abstract Factory", "Builder", "Prototype"],
        "structural": ["Adapter", "Bridge", "Composite", "Decorator", "Facade", "Proxy"],
        "behavioral": ["Observer", "Strategy", "Command", "State", "Template Method", "Iterator"]
    },
    
    "architecture_patterns": {
        "layered": "分层架构 - 表示层/业务层/数据层",
        "microservices": "微服务架构 - 独立部署的服务单元",
        "event_driven": "事件驱动架构 - 基于事件的松耦合",
        "plugin": "插件架构 - 核心+插件扩展"
    },
    
    "testing": {
        "unit_test": "单元测试 - 测试单个函数/方法",
        "integration_test": "集成测试 - 测试模块间交互",
        "e2e_test": "端到端测试 - 测试完整流程",
        "tdd": "测试驱动开发 - 先写测试再写代码"
    },
    
    "code_quality": {
        "type_hints": "类型提示 - 提高代码可读性和IDE支持",
        "docstrings": "文档字符串 - 函数/类/模块的说明文档",
        "linting": "代码检查 - pylint/flake8/ruff",
        "formatting": "代码格式化 - black/isort"
    },
    
    "error_handling": {
        "specific_exceptions": "捕获具体异常而非通用Exception",
        "fail_fast": "快速失败 - 尽早发现和报告错误",
        "graceful_degradation": "优雅降级 - 部分功能失败不影响整体",
        "retry_mechanism": "重试机制 - 处理临时性故障"
    },
    
    "performance": {
        "profiling": "性能分析 - 找出瓶颈",
        "caching": "缓存策略 - 减少重复计算",
        "lazy_loading": "懒加载 - 按需加载资源",
        "connection_pooling": "连接池 - 复用数据库/HTTP连接"
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# 领域二：AI Agent 专业知识
# ═══════════════════════════════════════════════════════════════════════════════

AI_AGENT_KNOWLEDGE = {
    "agent_architecture": {
        "components": {
            "perception": "感知模块 - 接收和理解输入",
            "reasoning": "推理模块 - 分析和决策",
            "planning": "规划模块 - 制定执行计划",
            "action": "行动模块 - 执行工具调用",
            "memory": "记忆模块 - 存储和检索信息",
            "learning": "学习模块 - 从经验中改进"
        },
        "patterns": {
            "react": "ReAct - Reasoning + Acting 交替执行",
            "plan_and_execute": "Plan-and-Execute - 先规划后执行",
            "reflection": "Reflection - 自我反思和改进",
            "multi_agent": "Multi-Agent - 多Agent协作"
        }
    },
    
    "tool_calling": {
        "tool_design": {
            "atomic": "原子性 - 每个工具做一件事",
            "idempotent": "幂等性 - 相同输入相同输出",
            "composable": "可组合 - 工具可以串联使用",
            "safe": "安全性 - 防止危险操作"
        },
        "tool_types": {
            "read_only": "只读工具 - 查询/搜索/分析",
            "write": "写入工具 - 创建/修改/删除",
            "execute": "执行工具 - 运行代码/命令",
            "external": "外部工具 - API调用/网络请求"
        },
        "error_handling": {
            "validation": "参数验证 - 调用前检查参数",
            "timeout": "超时控制 - 防止长时间阻塞",
            "fallback": "降级方案 - 工具失败时的备选",
            "retry": "重试策略 - 临时性故障重试"
        }
    },
    
    "memory_system": {
        "types": {
            "short_term": "短期记忆 - 当前对话上下文",
            "long_term": "长期记忆 - 持久化存储",
            "episodic": "情景记忆 - 具体事件记录",
            "semantic": "语义记忆 - 知识和概念",
            "procedural": "程序记忆 - 操作步骤"
        },
        "operations": {
            "encoding": "编码 - 将信息转化为记忆",
            "storage": "存储 - 持久化保存",
            "retrieval": "检索 - 根据相关性查找",
            "consolidation": "巩固 - 整理和强化重要记忆",
            "forgetting": "遗忘 - 清理不重要信息"
        }
    },
    
    "reasoning": {
        "types": {
            "chain_of_thought": "思维链 - 逐步推理",
            "tree_of_thought": "思维树 - 多路径探索",
            "self_consistency": "自一致性 - 多次推理取一致结果",
            "step_back": "退一步思考 - 抽象层面分析"
        },
        "techniques": {
            "decomposition": "问题分解 - 复杂问题拆解",
            "analogical": "类比推理 - 借鉴相似问题",
            "counterfactual": "反事实推理 - 假设不同情况",
            "meta_cognition": "元认知 - 思考自己的思考"
        }
    },
    
    "planning": {
        "strategies": {
            "goal_decomposition": "目标分解 - 大目标拆小目标",
            "backward_chaining": "反向链接 - 从目标反推步骤",
            "forward_chaining": "正向链接 - 从前向后推导",
            "hierarchical": "层次规划 - 不同抽象层次"
        },
        "adjustment": {
            "replanning": "重新规划 - 计划失败时调整",
            "priority_update": "优先级更新 - 动态调整优先级",
            "resource_reallocation": "资源重分配 - 优化资源使用"
        }
    },
    
    "model_optimization": {
        "prompt_engineering": {
            "system_prompt": "系统提示 - 定义角色和行为",
            "few_shot": "少样本示例 - 提供参考例子",
            "chain_of_thought": "思维链提示 - 引导逐步推理",
            "structured_output": "结构化输出 - JSON/XML格式"
        },
        "context_management": {
            "window_management": "窗口管理 - 控制上下文长度",
            "compression": "上下文压缩 - 保留关键信息",
            "retrieval_augmented": "RAG - 检索增强生成"
        },
        "model_selection": {
            "task_matching": "任务匹配 - 选适合任务的模型",
            "cost_optimization": "成本优化 - 性价比考虑",
            "latency_optimization": "延迟优化 - 响应速度考虑"
        }
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# 领域三：网络安全专业知识
# ═══════════════════════════════════════════════════════════════════════════════

SECURITY_KNOWLEDGE = {
    "input_validation": {
        "principles": {
            "whitelist": "白名单验证 - 只允许已知安全的输入",
            "sanitization": "输入净化 - 移除或转义危险字符",
            "length_check": "长度检查 - 防止缓冲区溢出",
            "type_check": "类型检查 - 确保数据类型正确"
        },
        "attacks_prevented": {
            "sql_injection": "SQL注入 - 恶意SQL语句",
            "xss": "跨站脚本 - 恶意JavaScript",
            "command_injection": "命令注入 - 恶意系统命令",
            "path_traversal": "路径遍历 - 访问受限文件"
        }
    },
    
    "authentication": {
        "methods": {
            "password": "密码认证 - 哈希存储+盐值",
            "token": "令牌认证 - JWT/OAuth",
            "api_key": "API密钥 - 服务间认证",
            "certificate": "证书认证 - mTLS双向认证"
        },
        "best_practices": {
            "strong_passwords": "强密码策略",
            "mfa": "多因素认证",
            "session_management": "会话管理",
            "rate_limiting": "速率限制"
        }
    },
    
    "authorization": {
        "models": {
            "rbac": "基于角色的访问控制",
            "abac": "基于属性的访问控制",
            "acl": "访问控制列表"
        },
        "principles": {
            "least_privilege": "最小权限原则",
            "separation_of_duties": "职责分离",
            "defense_in_depth": "纵深防御"
        }
    },
    
    "data_protection": {
        "at_rest": {
            "encryption": "静态数据加密 - AES-256",
            "key_management": "密钥管理 - HSM/KMS",
            "secure_deletion": "安全删除 - 覆写数据"
        },
        "in_transit": {
            "tls": "传输加密 - TLS 1.3",
            "certificate_pinning": "证书固定",
            "perfect_forward_secrecy": "完美前向保密"
        },
        "in_use": {
            "memory_protection": "内存保护 - 加密内存",
            "secure_enclave": "安全飞地 - TEE",
            "data_masking": "数据脱敏"
        }
    },
    
    "secure_coding": {
        "practices": {
            "input_validation": "输入验证",
            "output_encoding": "输出编码",
            "parameterized_queries": "参数化查询",
            "prepared_statements": "预编译语句"
        },
        "common_vulnerabilities": {
            "owasp_top_10": [
                "注入", "失效的认证", "敏感数据暴露",
                "XML外部实体", "失效的访问控制", "安全配置错误",
                "跨站脚本", "不安全的反序列化", "使用含漏洞的组件",
                "不足的日志和监控"
            ]
        }
    },
    
    "agent_security": {
        "tool_safety": {
            "sandboxing": "沙箱隔离 - 限制工具执行环境",
            "permission_model": "权限模型 - 工具分级授权",
            "audit_logging": "审计日志 - 记录所有操作",
            "rollback": "回滚机制 - 出错时恢复"
        },
        "prompt_security": {
            "injection_prevention": "提示注入防护",
            "output_filtering": "输出过滤",
            "context_isolation": "上下文隔离",
            "jailbreak_detection": "越狱检测"
        },
        "data_handling": {
            "pii_detection": "PII检测 - 识别个人敏感信息",
            "data_minimization": "数据最小化 - 只收集必要数据",
            "consent_management": "同意管理 - 用户授权",
            "retention_policy": "保留策略 - 定期清理"
        }
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# 知识应用指南
# ═══════════════════════════════════════════════════════════════════════════════

KNOWLEDGE_APPLICATION = {
    "task_execution_rules": {
        "1_analysis": "任务分析 - 理解需求，识别风险点",
        "2_design": "方案设计 - 基于专业知识设计解决方案",
        "3_implementation": "实现 - 遵循最佳实践编码",
        "4_testing": "测试 - 验证功能和安全",
        "5_review": "审查 - 代码审查和安全审计",
        "6_documentation": "文档 - 记录设计和使用说明"
    },
    
    "quality_checklist": {
        "functionality": "功能正确性 - 是否满足需求",
        "reliability": "可靠性 - 异常处理是否完善",
        "performance": "性能 - 是否有明显瓶颈",
        "security": "安全性 - 是否有安全漏洞",
        "maintainability": "可维护性 - 代码是否清晰",
        "testability": "可测试性 - 是否容易测试"
    },
    
    "security_checklist": {
        "input_validation": "输入是否验证",
        "output_encoding": "输出是否编码",
        "authentication": "认证是否正确",
        "authorization": "授权是否到位",
        "encryption": "敏感数据是否加密",
        "logging": "关键操作是否记录",
        "error_handling": "错误信息是否泄露敏感信息",
        "dependencies": "依赖是否有已知漏洞"
    }
}


def get_knowledge_summary():
    """获取知识体系摘要"""
    return {
        "programming": len(PROGRAMMING_KNOWLEDGE),
        "ai_agent": len(AI_AGENT_KNOWLEDGE),
        "security": len(SECURITY_KNOWLEDGE),
        "total_domains": 3
    }


if __name__ == "__main__":
    summary = get_knowledge_summary()
    print(f"知识体系包含 {summary['total_domains']} 个领域")
    print(f"- 编程工程: {summary['programming']} 个主题")
    print(f"- AI Agent: {summary['ai_agent']} 个主题")
    print(f"- 网络安全: {summary['security']} 个主题")