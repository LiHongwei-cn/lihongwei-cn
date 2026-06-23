"""蒙多任务分析引擎 v3.0.0 — 帝皇的参谋部

用户输入进来后，先分析、分类、拆解，再执行。
不是直接把用户原文丢给 LLM，是先理解用户要什么。

能力：
1. 输入分类 — 自动识别任务类型（代码/分析/文档/调试/重构/问答）
2. 文档解析 — Markdown 结构化提取（标题/章节/代码块/列表/表格）
3. 需求提取 — 从文档中提取关键需求、约束、验收标准
4. 任务拆解 — 将复杂文档分解为可执行的子任务
5. 上下文关联 — 将文档结构注入执行上下文，支持按章节引用

设计哲学：
- 先理解再动手，不做无脑执行
- 文档结构是任务骨架，章节是执行单元
- 分类决定策略，策略决定效率
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════
# 任务类型
# ═══════════════════════════════════════════════

class TaskType(Enum):
    CODE_GENERATION = "code_generation"     # 写代码
    CODE_REVIEW = "code_review"             # 代码审查
    DEBUGGING = "debugging"                 # 调试修复
    REFACTORING = "refactoring"             # 重构优化
    ANALYSIS = "analysis"                   # 分析研究
    DOCUMENTATION = "documentation"         # 文档撰写
    CONFIGURATION = "configuration"         # 配置部署
    QUESTION = "question"                   # 问答咨询
    MULTI_STEP = "multi_step"              # 多步复合任务
    UNKNOWN = "unknown"


class TaskComplexity(Enum):
    TRIVIAL = "trivial"      # 一句话能搞定
    SIMPLE = "simple"        # 1-3 步
    MEDIUM = "medium"        # 4-10 步
    COMPLEX = "complex"      # 10+ 步，需要拆解


# ═══════════════════════════════════════════════
# 文档结构
# ═══════════════════════════════════════════════

@dataclass
class DocSection:
    """Markdown 文档的一个章节"""
    title: str
    level: int              # 1-6 对应 h1-h6
    content: str            # 纯文本内容（不含标题行）
    start_line: int
    end_line: int
    subsections: List['DocSection'] = field(default_factory=list)
    code_blocks: List[str] = field(default_factory=list)
    list_items: List[str] = field(default_factory=list)
    tables: List[List[List[str]]] = field(default_factory=list)

    @property
    def full_content(self) -> str:
        """包含子章节的完整内容"""
        parts = [self.content]
        for sub in self.subsections:
            parts.append(sub.full_content)
        return "\n".join(parts)

    def to_summary(self, max_depth: int = 2) -> str:
        """生成结构摘要"""
        lines = []
        indent = "  " * (self.level - 1)
        lines.append(f"{indent}{'#' * self.level} {self.title}")
        if self.content.strip():
            preview = self.content.strip()[:100]
            if len(self.content.strip()) > 100:
                preview += "..."
            lines.append(f"{indent}  {preview}")
        if max_depth > 0:
            for sub in self.subsections:
                lines.append(sub.to_summary(max_depth - 1))
        return "\n".join(lines)


@dataclass
class DocStructure:
    """文档整体结构"""
    title: str
    sections: List[DocSection]
    code_blocks: List[Tuple[str, str]]  # (language, code)
    metadata: Dict = field(default_factory=dict)

    def get_section(self, title_keyword: str) -> Optional[DocSection]:
        """按标题关键词查找章节"""
        keyword = title_keyword.lower()
        for section in self._all_sections():
            if keyword in section.title.lower():
                return section
        return None

    def get_sections_by_pattern(self, pattern: str) -> List[DocSection]:
        """按正则匹配标题"""
        regex = re.compile(pattern, re.IGNORECASE)
        return [s for s in self._all_sections() if regex.search(s.title)]

    def to_outline(self) -> str:
        """生成目录大纲"""
        lines = []
        for section in self.sections:
            lines.append(section.to_summary(max_depth=3))
        return "\n".join(lines)

    def _all_sections(self) -> List[DocSection]:
        """递归获取所有章节"""
        result = []
        for section in self.sections:
            result.append(section)
            result.extend(self._flatten_subsections(section))
        return result

    def _flatten_subsections(self, section: DocSection) -> List[DocSection]:
        result = []
        for sub in section.subsections:
            result.append(sub)
            result.extend(self._flatten_subsections(sub))
        return result


# ═══════════════════════════════════════════════
# 任务分析结果
# ═══════════════════════════════════════════════

@dataclass
class TaskAnalysis:
    """任务分析结果"""
    task_type: TaskType
    complexity: TaskComplexity
    summary: str                          # 一句话概括
    requirements: List[str]               # 提取的需求列表
    constraints: List[str]                # 约束条件
    acceptance_criteria: List[str]        # 验收标准
    subtasks: List[Dict[str, str]]        # 拆解的子任务
    doc_structure: Optional[DocStructure] # 文档结构（如果有）
    keywords: List[str]                   # 关键词
    suggested_tools: List[str]            # 建议使用的工具
    context_hints: List[str]              # 上下文提示

    def to_prompt_context(self) -> str:
        """转换为可注入 prompt 的上下文"""
        parts = []

        parts.append(f"[任务分析] 类型: {self.task_type.value} | 复杂度: {self.complexity.value}")
        parts.append(f"[任务摘要] {self.summary}")

        if self.requirements:
            parts.append("[需求清单]")
            for i, req in enumerate(self.requirements, 1):
                parts.append(f"  {i}. {req}")

        if self.constraints:
            parts.append("[约束条件]")
            for c in self.constraints:
                parts.append(f"  - {c}")

        if self.acceptance_criteria:
            parts.append("[验收标准]")
            for ac in self.acceptance_criteria:
                parts.append(f"  ✓ {ac}")

        if self.subtasks:
            parts.append("[执行计划]")
            for i, st in enumerate(self.subtasks, 1):
                parts.append(f"  步骤{i}: {st.get('name', '')} — {st.get('desc', '')}")

        if self.doc_structure:
            parts.append(f"[文档结构]\n{self.doc_structure.to_outline()}")

        if self.context_hints:
            parts.append("[执行提示]")
            for hint in self.context_hints:
                parts.append(f"  → {hint}")

        return "\n".join(parts)


# ═══════════════════════════════════════════════
# Markdown 解析器
# ═══════════════════════════════════════════════

class MarkdownParser:
    """Markdown 文档结构化解析"""

    def parse(self, text: str) -> DocStructure:
        """解析 Markdown 文档为结构化对象"""
        lines = text.split("\n")

        # 提取标题
        title = self._extract_title(lines)

        # 解析章节
        sections = self._parse_sections(lines)

        # 提取代码块
        code_blocks = self._extract_code_blocks(text)

        # 提取元数据（YAML front matter）
        metadata = self._extract_metadata(text)

        return DocStructure(
            title=title,
            sections=sections,
            code_blocks=code_blocks,
            metadata=metadata,
        )

    def _extract_title(self, lines: List[str]) -> str:
        """提取文档标题"""
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# ") and not stripped.startswith("## "):
                return stripped[2:].strip()
        return ""

    def _parse_sections(self, lines: List[str]) -> List[DocSection]:
        """解析章节结构"""
        sections = []
        current_section = None
        current_content = []
        current_start = 0

        for i, line in enumerate(lines):
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)

            if header_match:
                # 保存上一个章节
                if current_section:
                    current_section.content = "\n".join(current_content).strip()
                    current_section.end_line = i - 1
                    current_section.code_blocks = self._extract_code_blocks(
                        "\n".join(current_content)
                    )
                    current_section.list_items = self._extract_list_items(
                        "\n".join(current_content)
                    )

                level = len(header_match.group(1))
                title = header_match.group(2).strip()

                current_section = DocSection(
                    title=title,
                    level=level,
                    content="",
                    start_line=i,
                    end_line=i,
                )
                current_content = []
                current_start = i

                # 按层级插入
                if level == 1:
                    sections.append(current_section)
                else:
                    parent = self._find_parent(sections, level)
                    if parent:
                        parent.subsections.append(current_section)
                    else:
                        sections.append(current_section)
            else:
                current_content.append(line)

        # 最后一个章节
        if current_section:
            current_section.content = "\n".join(current_content).strip()
            current_section.end_line = len(lines) - 1
            current_section.code_blocks = self._extract_code_blocks(
                "\n".join(current_content)
            )
            current_section.list_items = self._extract_list_items(
                "\n".join(current_content)
            )

        return sections

    def _find_parent(self, sections: List[DocSection], level: int) -> Optional[DocSection]:
        """查找最近的父章节（level < 当前 level）"""
        # 从最后一个添加的章节往回找
        best = None
        for section in self._iter_all(sections):
            if section.level < level:
                if best is None or section.start_line > best.start_line:
                    best = section
        return best

    def _iter_all(self, sections: List[DocSection]):
        """按添加顺序遍历所有章节"""
        for s in sections:
            yield s
            yield from self._iter_all(s.subsections)

    def _extract_code_blocks(self, text: str) -> List[Tuple[str, str]]:
        """提取代码块"""
        blocks = []
        pattern = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)
        for match in pattern.finditer(text):
            lang = match.group(1) or "text"
            code = match.group(2).strip()
            blocks.append((lang, code))
        return blocks

    def _extract_list_items(self, text: str) -> List[str]:
        """提取列表项"""
        items = []
        for line in text.split("\n"):
            stripped = line.strip()
            if re.match(r'^[-*+]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
                item = re.sub(r'^[-*+\d.]\s+', '', stripped)
                items.append(item)
        return items

    def _extract_metadata(self, text: str) -> Dict:
        """提取 YAML front matter"""
        match = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
        if not match:
            return {}

        metadata = {}
        for line in match.group(1).split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                metadata[key.strip()] = value.strip()
        return metadata


# ═══════════════════════════════════════════════
# 任务分析器
# ═══════════════════════════════════════════════

class TaskAnalyzer:
    """任务分析器 — 理解用户要什么，再告诉蒙多怎么做"""

    # 任务类型关键词映射
    TYPE_KEYWORDS = {
        TaskType.CODE_GENERATION: [
            "写代码", "实现", "编写", "开发", "创建", "新建", "代码生成",
            "写一个", "写个", "做一个", "搞一个", "搭一个",
            "implement", "create", "build", "develop", "write",
        ],
        TaskType.CODE_REVIEW: [
            "审查", "review", "检查代码", "代码质量", "看看代码",
            "代码规范", "最佳实践", "有没有问题",
        ],
        TaskType.DEBUGGING: [
            "报错", "bug", "错误", "异常", "失败", "不工作", "不能用",
            "修复", "fix", "debug", "排查", "问题", "出错",
        ],
        TaskType.REFACTORING: [
            "重构", "优化", "改进", "简化", "提取", "拆分", "合并",
            "refactor", "optimize", "simplify", "clean",
        ],
        TaskType.ANALYSIS: [
            "分析", "研究", "对比", "评估", "调研", "总结",
            "为什么", "怎么回事", "原理", "机制",
            "analyze", "research", "compare", "evaluate",
        ],
        TaskType.DOCUMENTATION: [
            "文档", "说明", "readme", "注释", "教程", "指南",
            "写文档", "写说明", "整理文档",
            "document", "readme", "guide", "tutorial",
        ],
        TaskType.CONFIGURATION: [
            "配置", "部署", "安装", "设置", "环境", "docker",
            "ci/cd", "pipeline", "deploy", "config", "setup",
        ],
    }

    # 复杂度判断关键词
    COMPLEXITY_SIGNALS = {
        TaskComplexity.TRIVIAL: ["是什么", "多少", "告诉我", "查一下"],
        TaskComplexity.SIMPLE: ["修改", "更新", "替换", "添加", "删除"],
        TaskComplexity.MEDIUM: ["实现", "开发", "重构", "迁移"],
        TaskComplexity.COMPLEX: ["架构", "系统", "框架", "完整", "全流程", "端到端"],
    }

    def __init__(self):
        self._parser = MarkdownParser()

    def analyze(self, user_input: str) -> TaskAnalysis:
        """分析用户输入，返回结构化任务分析"""
        # 检测是否包含 Markdown 文档
        doc_structure = None
        is_document = self._is_markdown_document(user_input)

        if is_document:
            doc_structure = self._parser.parse(user_input)

        # 分类任务类型
        task_type = self._classify_type(user_input, doc_structure)

        # 判断复杂度
        complexity = self._estimate_complexity(user_input, doc_structure)

        # 提取需求
        requirements = self._extract_requirements(user_input, doc_structure)

        # 提取约束
        constraints = self._extract_constraints(user_input, doc_structure)

        # 提取验收标准
        acceptance_criteria = self._extract_acceptance_criteria(user_input, doc_structure)

        # 拆解子任务
        subtasks = self._decompose_tasks(user_input, task_type, doc_structure)

        # 提取关键词
        keywords = self._extract_keywords(user_input)

        # 推荐工具
        suggested_tools = self._suggest_tools(task_type, requirements)

        # 生成上下文提示
        context_hints = self._generate_hints(task_type, complexity, doc_structure)

        # 生成摘要
        summary = self._generate_summary(user_input, task_type, doc_structure)

        return TaskAnalysis(
            task_type=task_type,
            complexity=complexity,
            summary=summary,
            requirements=requirements,
            constraints=constraints,
            acceptance_criteria=acceptance_criteria,
            subtasks=subtasks,
            doc_structure=doc_structure,
            keywords=keywords,
            suggested_tools=suggested_tools,
            context_hints=context_hints,
        )

    def _is_markdown_document(self, text: str) -> bool:
        """判断是否是 Markdown 文档（而非简单对话）"""
        indicators = 0

        # 有标题
        if re.search(r'^#{1,6}\s+', text, re.MULTILINE):
            indicators += 2

        # 有代码块
        if re.search(r'```', text):
            indicators += 2

        # 有列表
        if re.search(r'^[-*+]\s+', text, re.MULTILINE):
            indicators += 1

        # 有表格
        if re.search(r'\|.*\|.*\|', text):
            indicators += 2

        # 有多段落（长度超过 500 字符）
        if len(text) > 500:
            indicators += 1

        # 有结构化标记
        if re.search(r'^>\s+', text, re.MULTILINE):  # 引用
            indicators += 1

        return indicators >= 3

    def _classify_type(self, text: str, doc: Optional[DocStructure]) -> TaskType:
        """分类任务类型"""
        text_lower = text.lower()
        scores: Dict[TaskType, int] = {t: 0 for t in TaskType}

        # 关键词匹配
        for task_type, keywords in self.TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    scores[task_type] += 1

        # 文档结构辅助判断
        if doc:
            for section in doc.sections:
                title_lower = section.title.lower()
                for task_type, keywords in self.TYPE_KEYWORDS.items():
                    for kw in keywords:
                        if kw in title_lower:
                            scores[task_type] += 2  # 标题权重更高

            # 有代码块 → 偏代码类
            if doc.code_blocks:
                scores[TaskType.CODE_GENERATION] += 2
                scores[TaskType.DEBUGGING] += 1

            # 有 "需求"/"要求"/"功能" 章节 → 偏开发
            req_sections = doc.get_sections_by_pattern(r"需求|要求|功能|feature|requirement")
            if req_sections:
                scores[TaskType.CODE_GENERATION] += 3

            # 有 "问题"/"错误"/"bug" 章节 → 偏调试
            bug_sections = doc.get_sections_by_pattern(r"问题|错误|bug|issue|error")
            if bug_sections:
                scores[TaskType.DEBUGGING] += 3

        # 取最高分
        best_type = max(scores, key=scores.get)
        if scores[best_type] == 0:
            return TaskType.QUESTION

        # 如果多个类型分数接近，可能是复合任务
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_scores) >= 2 and sorted_scores[0][1] - sorted_scores[1][1] <= 1:
            return TaskType.MULTI_STEP

        return best_type

    def _estimate_complexity(self, text: str,
                             doc: Optional[DocStructure]) -> TaskComplexity:
        """估算任务复杂度"""
        score = 0

        # 文本长度
        if len(text) > 2000:
            score += 3
        elif len(text) > 500:
            score += 2
        elif len(text) > 100:
            score += 1

        # 文档结构
        if doc:
            section_count = len(doc._all_sections())
            if section_count > 10:
                score += 3
            elif section_count > 5:
                score += 2
            elif section_count > 2:
                score += 1

            if doc.code_blocks:
                score += len(doc.code_blocks)

        # 复杂度关键词
        text_lower = text.lower()
        for complexity, keywords in self.COMPLEXITY_SIGNALS.items():
            for kw in keywords:
                if kw in text_lower:
                    score += {
                        TaskComplexity.TRIVIAL: 0,
                        TaskComplexity.SIMPLE: 1,
                        TaskComplexity.MEDIUM: 2,
                        TaskComplexity.COMPLEX: 3,
                    }[complexity]

        if score <= 1:
            return TaskComplexity.TRIVIAL
        elif score <= 4:
            return TaskComplexity.SIMPLE
        elif score <= 8:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.COMPLEX

    def _extract_requirements(self, text: str,
                              doc: Optional[DocStructure]) -> List[str]:
        """提取需求"""
        requirements = []

        # 从文档的需求章节提取
        if doc:
            for pattern in [r"需求", r"要求", r"功能", r"feature", r"requirement", r"目标"]:
                sections = doc.get_sections_by_pattern(pattern)
                for section in sections:
                    for item in section.list_items:
                        requirements.append(item)
                    if not section.list_items and section.content.strip():
                        # 按行拆分
                        for line in section.content.split("\n"):
                            line = line.strip()
                            if line and len(line) > 5:
                                requirements.append(line)

        # 从用户输入中提取 "需要"/"必须"/"应该" 后面的内容
        for match in re.finditer(r'(?:需要|必须|应该|要|shall|must|should)\s*[：:]\s*(.+?)(?:\n|$)', text):
            req = match.group(1).strip()
            if req and req not in requirements:
                requirements.append(req)

        # 从列表项提取
        for match in re.finditer(r'^[-*+]\s+(.+)$', text, re.MULTILINE):
            item = match.group(1).strip()
            if len(item) > 5 and item not in requirements:
                requirements.append(item)

        return requirements[:20]  # 限制数量

    def _extract_constraints(self, text: str,
                             doc: Optional[DocStructure]) -> List[str]:
        """提取约束条件"""
        constraints = []

        # 关键词匹配
        patterns = [
            r'(?:注意|约束|限制|不能|禁止|不要|不可以|避免)\s*[：:]\s*(.+?)(?:\n|$)',
            r'(?:constraint|limitation|must not|avoid)\s*[：:]\s*(.+?)(?:\n|$)',
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                constraints.append(match.group(1).strip())

        # 从文档的约束章节提取
        if doc:
            for section in doc.get_sections_by_pattern(r"约束|限制|注意|constraint|limitation"):
                for item in section.list_items:
                    if item not in constraints:
                        constraints.append(item)

        return constraints[:10]

    def _extract_acceptance_criteria(self, text: str,
                                     doc: Optional[DocStructure]) -> List[str]:
        """提取验收标准"""
        criteria = []

        # 从文档的验收/测试章节提取
        if doc:
            for section in doc.get_sections_by_pattern(r"验收|测试|标准|criteria|test|验证"):
                for item in section.list_items:
                    criteria.append(item)

        # 从 "确保"/"保证"/"验证" 提取
        for match in re.finditer(r'(?:确保|保证|验证|测试)\s*[：:]\s*(.+?)(?:\n|$)', text):
            criteria.append(match.group(1).strip())

        return criteria[:10]

    def _decompose_tasks(self, text: str, task_type: TaskType,
                         doc: Optional[DocStructure]) -> List[Dict[str, str]]:
        """拆解子任务"""
        subtasks = []

        if doc and len(doc.sections) > 1:
            # 有文档结构 → 按章节拆解
            for i, section in enumerate(doc.sections):
                if section.level == 1:
                    continue  # 跳过顶级标题

                subtask = {
                    "name": section.title,
                    "desc": section.content[:200] if section.content else section.title,
                    "section": section.title,
                    "order": str(i),
                }
                subtasks.append(subtask)
        else:
            # 无文档结构 → 按任务类型生成默认步骤
            default_steps = {
                TaskType.CODE_GENERATION: [
                    {"name": "分析需求", "desc": "理解用户要实现什么"},
                    {"name": "设计方案", "desc": "确定技术方案和架构"},
                    {"name": "编写代码", "desc": "实现核心功能"},
                    {"name": "测试验证", "desc": "运行测试确保正确"},
                ],
                TaskType.DEBUGGING: [
                    {"name": "复现问题", "desc": "确认错误现象"},
                    {"name": "定位原因", "desc": "找到根本原因"},
                    {"name": "修复代码", "desc": "实施修复"},
                    {"name": "验证修复", "desc": "确认问题解决"},
                ],
                TaskType.ANALYSIS: [
                    {"name": "收集信息", "desc": "读取相关文件和数据"},
                    {"name": "分析数据", "desc": "深入分析关键信息"},
                    {"name": "得出结论", "desc": "总结分析结果"},
                ],
                TaskType.DOCUMENTATION: [
                    {"name": "梳理内容", "desc": "确定文档结构"},
                    {"name": "撰写文档", "desc": "编写完整内容"},
                    {"name": "审校完善", "desc": "检查格式和准确性"},
                ],
            }
            subtasks = default_steps.get(task_type, [
                {"name": "理解任务", "desc": "分析用户需求"},
                {"name": "执行任务", "desc": "完成核心工作"},
                {"name": "输出结果", "desc": "汇报完成情况"},
            ])

        return subtasks[:15]  # 限制数量

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        keywords = set()

        # 英文关键词（驼峰/下划线命名）
        for match in re.finditer(r'[a-zA-Z_][a-zA-Z0-9_]{2,}', text):
            word = match.group()
            if len(word) > 3:
                keywords.add(word)

        # 中文关键词（2-4 字组合）
        for match in re.finditer(r'[一-鿿]{2,4}', text):
            word = match.group()
            if word not in {"一个", "这个", "那个", "什么", "怎么", "如何", "可以", "需要", "应该"}:
                keywords.add(word)

        return list(keywords)[:20]

    def _suggest_tools(self, task_type: TaskType,
                       requirements: List[str]) -> List[str]:
        """推荐工具"""
        tool_map = {
            TaskType.CODE_GENERATION: ["write_file", "read_file", "terminal"],
            TaskType.CODE_REVIEW: ["read_file", "search_files"],
            TaskType.DEBUGGING: ["read_file", "terminal", "search_files"],
            TaskType.REFACTORING: ["read_file", "write_file", "search_files"],
            TaskType.ANALYSIS: ["read_file", "search_files", "list_directory"],
            TaskType.DOCUMENTATION: ["write_file", "read_file"],
            TaskType.CONFIGURATION: ["terminal", "write_file"],
            TaskType.QUESTION: ["read_file", "search_files"],
        }
        return tool_map.get(task_type, ["read_file", "terminal"])

    def _generate_hints(self, task_type: TaskType,
                        complexity: TaskComplexity,
                        doc: Optional[DocStructure]) -> List[str]:
        """生成执行提示"""
        hints = []

        if complexity == TaskComplexity.COMPLEX:
            hints.append("任务复杂，建议分阶段执行，每阶段验证后再继续")

        if task_type == TaskType.CODE_GENERATION:
            hints.append("先读取相关文件了解现有代码结构，再动手写")
            hints.append("代码写完后自检：无死代码、无冗余注释、函数<50行")

        if task_type == TaskType.DEBUGGING:
            hints.append("先复现问题再修复，不要猜测原因")

        if task_type == TaskType.ANALYSIS:
            hints.append("收集足够信息后再下结论，避免基于不完整数据做判断")

        if doc:
            section_count = len(doc._all_sections())
            if section_count > 5:
                hints.append(f"文档有 {section_count} 个章节，按章节逐个处理")
            if doc.code_blocks:
                hints.append(f"文档包含 {len(doc.code_blocks)} 个代码块，注意参照实现")

        return hints[:5]

    def _generate_summary(self, text: str, task_type: TaskType,
                          doc: Optional[DocStructure]) -> str:
        """生成任务摘要"""
        if doc and doc.title:
            return f"[{task_type.value}] {doc.title}"

        # 取第一句有意义的话
        for line in text.split("\n"):
            line = line.strip()
            if line and len(line) > 5 and not line.startswith("#"):
                summary = line[:100]
                if len(line) > 100:
                    summary += "..."
                return f"[{task_type.value}] {summary}"

        return f"[{task_type.value}] 用户任务"


# ═══════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════

_analyzer: Optional[TaskAnalyzer] = None


def reset_task_analyzer():
    """重置单例 — 用于测试隔离"""
    global _analyzer
    _analyzer = None


def get_task_analyzer() -> TaskAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = TaskAnalyzer()
    return _analyzer
