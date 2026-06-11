"""蒙多插件系统 v2.1.0 — 皇帝的百官

可扩展的插件架构。不是简单的 import。是生命周期管理。
插件有钩子、有依赖、有优先级。

设计哲学：
- 插件是可替换的扩展点
- 生命周期：加载 → 初始化 → 运行 → 卸载
- 钩子机制：在关键节点插入自定义逻辑
- 依赖注入：插件声明它需要什么，框架提供
"""

import os
import sys
import json
import importlib
import importlib.util
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from pathlib import Path
from enum import Enum, auto


class HookPoint(Enum):
    BEFORE_TURN = auto()
    AFTER_TURN = auto()
    BEFORE_TOOL = auto()
    AFTER_TOOL = auto()
    BEFORE_LLM = auto()
    AFTER_LLM = auto()
    ON_ERROR = auto()
    ON_COMPRESS = auto()
    ON_MEMORY = auto()
    ON_DELEGATE = auto()
    ON_STARTUP = auto()
    ON_SHUTDOWN = auto()


@dataclass
class PluginMeta:
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    entry_point: str = "plugin.py"
    dependencies: List[str] = field(default_factory=list)
    hooks: List[str] = field(default_factory=list)
    priority: int = 100
    enabled: bool = True
    source: str = ""


@dataclass
class Plugin:
    meta: PluginMeta
    module: Any = None
    loaded: bool = False
    error: str = ""
    _hooks: Dict[str, List[Callable]] = field(default_factory=dict)


class PluginLoader:
    """插件加载器 — 发现、加载、管理"""

    def __init__(self, plugin_dirs: Optional[List[Path]] = None):
        self._plugins: Dict[str, Plugin] = {}
        self._hooks: Dict[HookPoint, List[tuple]] = {}
        self._plugin_dirs = plugin_dirs or [
            Path.home() / ".hermes" / "mundo-agent" / "plugins",
        ]

    def discover(self) -> List[PluginMeta]:
        discovered = []
        for base in self._plugin_dirs:
            if not base.exists():
                continue
            for item in sorted(base.iterdir()):
                if not item.is_dir():
                    continue
                meta_file = item / "plugin.json"
                if meta_file.exists():
                    meta = self._parse_meta(meta_file, item)
                    if meta:
                        discovered.append(meta)
                elif (item / "plugin.py").exists():
                    discovered.append(PluginMeta(
                        name=item.name,
                        source=str(item),
                    ))
        return discovered

    def register(self, meta: PluginMeta) -> Plugin:
        plugin = Plugin(meta=meta)
        self._plugins[meta.name] = plugin
        return plugin

    def load(self, name: str) -> bool:
        plugin = self._plugins.get(name)
        if not plugin:
            return False

        if not plugin.meta.enabled:
            return False

        # 检查依赖
        for dep in plugin.meta.dependencies:
            if dep not in self._plugins or not self._plugins[dep].loaded:
                plugin.error = f"缺少依赖: {dep}"
                return False

        # 加载模块
        source = Path(plugin.meta.source) / plugin.meta.entry_point
        if not source.exists():
            plugin.error = f"入口文件不存在: {source}"
            return False

        try:
            spec = importlib.util.spec_from_file_location(
                f"mundo_plugin_{name}", str(source)
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"mundo_plugin_{name}"] = module
            spec.loader.exec_module(module)

            plugin.module = module
            plugin.loaded = True

            # 注册钩子
            self._register_hooks(plugin)

            return True

        except Exception as e:
            plugin.error = str(e)
            return False

    def load_all(self) -> Dict[str, bool]:
        results = {}
        for name in sorted(self._plugins, key=lambda n: self._plugins[n].meta.priority):
            results[name] = self.load(name)
        return results

    def unload(self, name: str) -> bool:
        plugin = self._plugins.get(name)
        if not plugin or not plugin.loaded:
            return False

        # 清理钩子
        for point in self._hooks:
            self._hooks[point] = [
                (h, p) for h, p in self._hooks[point] if p != name
            ]

        # 调用插件的清理函数
        if plugin.module and hasattr(plugin.module, "on_unload"):
            try:
                plugin.module.on_unload()
            except Exception:
                pass

        plugin.loaded = False
        plugin.module = None
        return True

    def hook(self, point: HookPoint, handler: Callable,
             plugin_name: str = "", priority: int = 100) -> str:
        """注册钩子"""
        import uuid
        hook_id = uuid.uuid4().hex[:8]
        if point not in self._hooks:
            self._hooks[point] = []
        self._hooks[point].append((handler, plugin_name, priority))
        self._hooks[point].sort(key=lambda x: x[2], reverse=True)
        return hook_id

    def trigger(self, point: HookPoint, context: Dict = None) -> List[Any]:
        """触发钩子，返回所有结果"""
        results = []
        for handler, plugin_name, _ in self._hooks.get(point, []):
            try:
                result = handler(context or {})
                results.append(result)
            except Exception as e:
                results.append({"error": str(e), "plugin": plugin_name})
        return results

    def _register_hooks(self, plugin: Plugin) -> None:
        module = plugin.module
        hook_map = {
            "before_turn": HookPoint.BEFORE_TURN,
            "after_turn": HookPoint.AFTER_TURN,
            "before_tool": HookPoint.BEFORE_TOOL,
            "after_tool": HookPoint.AFTER_TOOL,
            "before_llm": HookPoint.BEFORE_LLM,
            "after_llm": HookPoint.AFTER_LLM,
            "on_error": HookPoint.ON_ERROR,
            "on_startup": HookPoint.ON_STARTUP,
            "on_shutdown": HookPoint.ON_SHUTDOWN,
        }
        for attr_name, point in hook_map.items():
            if hasattr(module, attr_name):
                self.hook(point, getattr(module, attr_name), plugin.meta.name)

    def list_plugins(self, enabled_only: bool = True) -> List[PluginMeta]:
        plugins = list(self._plugins.values())
        if enabled_only:
            plugins = [p for p in plugins if p.meta.enabled]
        return [p.meta for p in plugins]

    def stats(self) -> Dict:
        total = len(self._plugins)
        loaded = sum(1 for p in self._plugins.values() if p.loaded)
        hooks = sum(len(v) for v in self._hooks.values())
        return {
            "total": total,
            "loaded": loaded,
            "hooks": hooks,
        }

    def _parse_meta(self, meta_file: Path, plugin_dir: Path) -> Optional[PluginMeta]:
        try:
            data = json.loads(meta_file.read_text(encoding="utf-8"))
            return PluginMeta(
                name=data.get("name", plugin_dir.name),
                version=data.get("version", "1.0.0"),
                description=data.get("description", ""),
                author=data.get("author", ""),
                entry_point=data.get("entry_point", "plugin.py"),
                dependencies=data.get("dependencies", []),
                hooks=data.get("hooks", []),
                priority=data.get("priority", 100),
                source=str(plugin_dir),
            )
        except Exception:
            return None


# 向后兼容别名
PluginManager = PluginLoader


# 全局单例
_loader: Optional[PluginLoader] = None


def get_plugin_loader() -> PluginLoader:
    global _loader
    if _loader is None:
        _loader = PluginLoader()
    return _loader
