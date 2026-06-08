"""蒙多 Skill 系统 v1.4.0 — 皇帝的武功秘籍

不是简单的文件加载。是结构化的技能注册、组合、继承。
Skill 有依赖、有前置条件、有元数据。

设计哲学：
- Skill 是可组合的能力单元
- 支持依赖链：A 依赖 B，B 自动加载
- 支持冲突检测：A 和 B 互斥时警告
- Skill 可以声明它需要的工具和权限
"""

import os
import json
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from pathlib import Path


@dataclass
class SkillMeta:
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)
    entry_point: str = "SKILL.md"
    source: str = ""  # 来源路径
    hash: str = ""    # 内容哈希，用于变更检测
    enabled: bool = True
    priority: int = 100
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "conflicts": self.conflicts,
            "required_tools": self.required_tools,
            "source": self.source,
            "enabled": self.enabled,
            "priority": self.priority,
        }


@dataclass
class Skill:
    meta: SkillMeta
    content: str = ""
    loaded: bool = False
    load_error: str = ""

    @property
    def is_ready(self) -> bool:
        return self.meta.enabled and self.loaded and not self.load_error


class SkillRegistry:
    """Skill 注册表 — 发现、加载、组合"""

    def __init__(self, search_paths: Optional[List[Path]] = None):
        self._skills: Dict[str, Skill] = {}
        self._search_paths = search_paths or self._default_paths()

    @staticmethod
    def _default_paths() -> List[Path]:
        home = Path.home()
        return [
            home / ".hermes" / "skills",
            home / ".hermes" / "mundo-agent" / "skills",
        ]

    def discover(self) -> List[SkillMeta]:
        """扫描所有搜索路径，发现可用 Skill"""
        discovered = []
        for base in self._search_paths:
            if not base.exists():
                continue
            for skill_dir in sorted(base.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    meta = self._parse_meta(skill_file, skill_dir)
                    if meta:
                        discovered.append(meta)
        return discovered

    def register(self, meta: SkillMeta, content: str = "") -> Skill:
        skill = Skill(meta=meta, content=content)
        skill.meta.hash = hashlib.md5(content.encode()).hexdigest()[:12]
        self._skills[meta.name] = skill
        return skill

    def load(self, name: str) -> bool:
        skill = self._skills.get(name)
        if not skill:
            return False

        # 检查依赖
        for dep in skill.meta.dependencies:
            if dep not in self._skills or not self._skills[dep].is_ready:
                skill.load_error = f"缺少依赖: {dep}"
                return False

        # 检查冲突
        for conflict in skill.meta.conflicts:
            if conflict in self._skills and self._skills[conflict].is_ready:
                skill.load_error = f"冲突: {conflict} 已加载"
                return False

        # 加载内容
        if not skill.content:
            source = Path(skill.meta.source) / skill.meta.entry_point
            if source.exists():
                skill.content = source.read_text(encoding="utf-8")
            else:
                skill.load_error = f"找不到入口文件: {source}"
                return False

        skill.loaded = True
        return True

    def load_all(self) -> Dict[str, bool]:
        results = {}
        for name in self._skills:
            results[name] = self.load(name)
        return results

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def get_content(self, name: str) -> str:
        skill = self._skills.get(name)
        return skill.content if skill and skill.is_ready else ""

    def list_skills(self, enabled_only: bool = True,
                    tag: str = "") -> List[SkillMeta]:
        skills = list(self._skills.values())
        if enabled_only:
            skills = [s for s in skills if s.meta.enabled]
        if tag:
            skills = [s for s in skills if tag in s.meta.tags]
        return [s.meta for s in skills]

    def enable(self, name: str) -> bool:
        skill = self._skills.get(name)
        if skill:
            skill.meta.enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        skill = self._skills.get(name)
        if skill:
            skill.meta.enabled = False
            skill.loaded = False
            return True
        return False

    def remove(self, name: str) -> bool:
        return self._skills.pop(name, None) is not None

    def resolve_dependencies(self, name: str) -> List[str]:
        """解析依赖链，返回加载顺序"""
        visited: Set[str] = set()
        order: List[str] = []

        def _visit(n: str):
            if n in visited:
                return
            visited.add(n)
            skill = self._skills.get(n)
            if skill:
                for dep in skill.meta.dependencies:
                    _visit(dep)
                order.append(n)

        _visit(name)
        return order

    def validate(self) -> List[str]:
        """验证所有 Skill 的完整性"""
        issues = []
        for name, skill in self._skills.items():
            if not skill.meta.description:
                issues.append(f"{name}: 缺少描述")
            for dep in skill.meta.dependencies:
                if dep not in self._skills:
                    issues.append(f"{name}: 依赖不存在 — {dep}")
            for conflict in skill.meta.conflicts:
                if conflict in self._skills and self._skills[conflict].meta.enabled:
                    issues.append(f"{name}: 与 {conflict} 冲突（两者都启用）")
        return issues

    def stats(self) -> Dict:
        total = len(self._skills)
        loaded = sum(1 for s in self._skills.values() if s.is_ready)
        errors = sum(1 for s in self._skills.values() if s.load_error)
        return {
            "total": total,
            "loaded": loaded,
            "errors": errors,
            "disabled": total - loaded - errors,
        }

    def _parse_meta(self, skill_file: Path, skill_dir: Path) -> Optional[SkillMeta]:
        """从 SKILL.md 解析元数据"""
        try:
            content = skill_file.read_text(encoding="utf-8")
            # 简单的 frontmatter 解析
            if content.startswith("---"):
                end = content.index("---", 3)
                frontmatter = content[3:end].strip()
                meta_dict = {}
                for line in frontmatter.split("\n"):
                    if ":" in line:
                        key, val = line.split(":", 1)
                        meta_dict[key.strip()] = val.strip()

                return SkillMeta(
                    name=meta_dict.get("name", skill_dir.name),
                    version=meta_dict.get("version", "1.0.0"),
                    description=meta_dict.get("description", ""),
                    author=meta_dict.get("author", ""),
                    tags=[t.strip() for t in meta_dict.get("tags", "").split(",") if t.strip()],
                    source=str(skill_dir),
                )
            return SkillMeta(
                name=skill_dir.name,
                source=str(skill_dir),
            )
        except Exception:
            return None


# 全局单例
_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry
