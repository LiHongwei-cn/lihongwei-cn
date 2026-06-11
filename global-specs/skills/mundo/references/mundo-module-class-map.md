# 蒙多模块类名映射表

快速参考：测试或导入蒙多模块时使用正确的类名。

## 核心模块

| 模块 | 实际类名 | 导入示例 |
|------|---------|---------|
| `core.py` | `MundoEngine` | `from core import MundoEngine` |
| `tools.py` | `ToolRegistry` | `from tools import ToolRegistry, TOOL_SCHEMAS` |
| `policy.py` | `PolicyEngine` | `from policy import PolicyEngine, BUILTIN_RULES` |
| `sandbox.py` | `Sandbox`, `SandboxConfig` | `from sandbox import Sandbox, SandboxConfig` |
| `events.py` | `EventBus`, `EventType` | `from events import EventBus, EventType, get_event_bus` |
| `memory.py` | `MundoMemory` (别名 `MemoryManager`) | `from memory import MundoMemory` 或 `from memory import MemoryManager` |
| `approval.py` | 无主类 | `from approval import DANGEROUS_PATTERNS, SENSITIVE_PATHS` |

## 扩展模块

| 模块 | 实际类名 | 导入示例 |
|------|---------|---------|
| `model_adapter.py` | `ModelAdapter`, `ModelProfile` | `from model_adapter import ModelAdapter, MODEL_PROFILES` |
| `agents.py` | `AgentManager`, `MundoClone` (别名 `DelegationManager`) | `from agents import AgentManager, AGENT_REGISTRY` 或 `from delegation import DelegationManager` |
| `quark_optimizer.py` | `DeepSeekQuarkOptimizer` | `from quark_optimizer import DeepSeekQuarkOptimizer, ModelOptimizerFactory` |

## 核心组件（core.py 内部）

| 组件 | 导入方式 |
|------|---------|
| LLM客户端 | `from core import LLMClient` |
| 上下文映射 | `from core import ContextMapper` |
| 消息压缩 | `from core import MessageCompressor` |
| 任务规划 | `from core import TaskPlanner` |
| 统计追踪 | `from core import TaskStats` |
| 模型选择 | `from core import SmartModelSelector` |
| 工具防护 | `from core import ToolGuardController` |

## 常见陷阱

1. **事件发布需要 EventType 枚举**：`bus.publish(EventType.SESSION_START, data)` ✅
   - 错误：`bus.publish('session_start', data)` ✗（会报 `'str' object has no attribute 'name'`）

2. **ModelAdapter 需要参数**：`ModelAdapter('deepseek-chat')` ✅
   - 错误：`ModelAdapter()` ✗（会报 `missing 1 required positional argument: 'model_id'`）

3. **Sandbox 需要配置参数**：`Sandbox(SandboxConfig())` ✅
   - 错误：`Sandbox()` ✗（会报 `missing 1 required positional argument: 'config'`）
