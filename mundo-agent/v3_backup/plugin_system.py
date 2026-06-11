"""插件系统 — 从 Claude Code plugin 架构提炼

每个插件是一个目录，包含 plugin.json 清单 + 可选组件：
  plugin-name/
  ├── plugin.json        # 清单（name/version/description/components）
  ├── commands/          # 斜杠命令（.md 文件）
  ├── agents/            # 子Agent定义（.md 文件）
  ├── skills/            # 技能（SKILL.md）
  └── hooks/             # 钩子配置（hooks.json）

自动发现：扫描目录，解析清单，注册组件。
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PluginManifest:
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    components: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Plugin:
    manifest: PluginManifest
    path: Path
    commands: Dict[str, str] = field(default_factory=dict)       # name -> content
    agents: Dict[str, str] = field(default_factory=dict)         # name -> content
    skills: Dict[str, str] = field(default_factory=dict)         # name -> SKILL.md content
    hooks: Dict[str, Any] = field(default_factory=dict)          # event -> [hook configs]
    enabled: bool = True


class PluginManager:
    """插件管理器 — 自动发现 + 加载 + 注册"""

    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._search_paths: List[Path] = []

    def add_search_path(self, path: str):
        p = Path(path).expanduser()
        if p.is_dir() and p not in self._search_paths:
            self._search_paths.append(p)

    def discover(self) -> List[str]:
        """扫描所有搜索路径，发现并加载插件"""
        found = []
        for search_path in self._search_paths:
            if not search_path.is_dir():
                continue
            for entry in sorted(search_path.iterdir()):
                if not entry.is_dir():
                    continue
                manifest_path = entry / "plugin.json"
                if manifest_path.exists():
                    plugin = self._load_plugin(entry)
                    if plugin:
                        self._plugins[plugin.manifest.name] = plugin
                        found.append(plugin.manifest.name)
        return found

    def _load_plugin(self, plugin_dir: Path) -> Optional[Plugin]:
        """加载单个插件"""
        manifest_path = plugin_dir / "plugin.json"
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        manifest = PluginManifest(
            name=data.get("name", plugin_dir.name),
            version=data.get("version", "0.1.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            components=data.get("components", {}),
        )

        plugin = Plugin(manifest=manifest, path=plugin_dir)

        # 加载 commands/
        commands_dir = plugin_dir / "commands"
        if commands_dir.is_dir():
            for f in sorted(commands_dir.glob("*.md")):
                plugin.commands[f.stem] = f.read_text(encoding="utf-8")

        # 加载 agents/
        agents_dir = plugin_dir / "agents"
        if agents_dir.is_dir():
            for f in sorted(agents_dir.glob("*.md")):
                plugin.agents[f.stem] = f.read_text(encoding="utf-8")

        # 加载 skills/
        skills_dir = plugin_dir / "skills"
        if skills_dir.is_dir():
            for skill_dir in sorted(skills_dir.iterdir()):
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    plugin.skills[skill_dir.name] = skill_md.read_text(encoding="utf-8")

        # 加载 hooks/
        hooks_json = plugin_dir / "hooks" / "hooks.json"
        if hooks_json.exists():
            try:
                with open(hooks_json, "r", encoding="utf-8") as f:
                    plugin.hooks = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        return plugin

    def get(self, name: str) -> Optional[Plugin]:
        return self._plugins.get(name)

    def list_plugins(self) -> List[Dict[str, str]]:
        return [
            {
                "name": p.manifest.name,
                "version": p.manifest.version,
                "description": p.manifest.description,
                "commands": len(p.commands),
                "agents": len(p.agents),
                "skills": len(p.skills),
                "enabled": p.enabled,
            }
            for p in self._plugins.values()
        ]

    def enable(self, name: str) -> bool:
        p = self._plugins.get(name)
        if p:
            p.enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        p = self._plugins.get(name)
        if p:
            p.enabled = False
            return True
        return False

    def get_all_commands(self) -> Dict[str, str]:
        """获取所有已启用插件的命令"""
        cmds = {}
        for p in self._plugins.values():
            if p.enabled:
                for name, content in p.commands.items():
                    cmds[f"{p.manifest.name}:{name}"] = content
        return cmds

    def get_all_skills(self) -> Dict[str, str]:
        """获取所有已启用插件的技能"""
        skills = {}
        for p in self._plugins.values():
            if p.enabled:
                for name, content in p.skills.items():
                    skills[name] = content
        return skills

    def get_all_agents(self) -> Dict[str, str]:
        """获取所有已启用插件的Agent"""
        agents = {}
        for p in self._plugins.values():
            if p.enabled:
                for name, content in p.agents.items():
                    agents[f"{p.manifest.name}:{name}"] = content
        return agents

    def get_all_hooks(self) -> Dict[str, list]:
        """获取所有已启用插件的钩子"""
        merged = {}
        for p in self._plugins.values():
            if p.enabled:
                for event, hooks in p.hooks.items():
                    merged.setdefault(event, []).extend(hooks)
        return merged

    def stats(self) -> Dict[str, int]:
        total = len(self._plugins)
        enabled = sum(1 for p in self._plugins.values() if p.enabled)
        cmds = sum(len(p.commands) for p in self._plugins.values() if p.enabled)
        agents = sum(len(p.agents) for p in self._plugins.values() if p.enabled)
        skills = sum(len(p.skills) for p in self._plugins.values() if p.enabled)
        return {
            "total_plugins": total,
            "enabled_plugins": enabled,
            "total_commands": cmds,
            "total_agents": agents,
            "total_skills": skills,
        }
