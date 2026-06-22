"""任务分析引擎单元测试"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMarkdownParser:
    """MarkdownParser 测试"""

    def test_parse_headers(self):
        from task_analyzer import MarkdownParser
        parser = MarkdownParser()
        doc = parser.parse("# 标题\n\n## 章节1\n内容1\n## 章节2\n内容2")
        assert doc.title == "标题"
        # h1 作为顶级 section，h2 是它的 subsections
        assert len(doc.sections) == 1
        assert doc.sections[0].title == "标题"
        assert len(doc.sections[0].subsections) == 2
        assert doc.sections[0].subsections[0].title == "章节1"
        assert doc.sections[0].subsections[1].title == "章节2"

    def test_parse_nested_headers(self):
        from task_analyzer import MarkdownParser
        parser = MarkdownParser()
        doc = parser.parse("# H1\n## H2a\n### H3\n## H2b")
        assert doc.title == "H1"
        assert len(doc.sections) == 1
        h1 = doc.sections[0]
        assert len(h1.subsections) == 2  # H2a, H2b
        assert len(h1.subsections[0].subsections) == 1  # H3
        assert h1.subsections[0].subsections[0].title == "H3"

    def test_parse_code_blocks(self):
        from task_analyzer import MarkdownParser
        parser = MarkdownParser()
        doc = parser.parse("# Test\n\n```python\nprint('hello')\n```\n\n```js\nconsole.log('hi')\n```")
        assert len(doc.code_blocks) == 2
        assert doc.code_blocks[0][0] == "python"
        assert doc.code_blocks[1][0] == "js"

    def test_parse_list_items(self):
        from task_analyzer import MarkdownParser
        parser = MarkdownParser()
        doc = parser.parse("# Req\n\n- 需求一\n- 需求二\n- 需求三")
        section = doc.sections[0]
        assert len(section.list_items) == 3

    def test_parse_metadata(self):
        from task_analyzer import MarkdownParser
        parser = MarkdownParser()
        doc = parser.parse("---\ntitle: Test\nauthor: Mundo\n---\n\n# Content")
        assert doc.metadata["title"] == "Test"
        assert doc.metadata["author"] == "Mundo"

    def test_to_outline(self):
        from task_analyzer import MarkdownParser
        parser = MarkdownParser()
        doc = parser.parse("# Root\n## A\n### A1\n## B")
        outline = doc.to_outline()
        assert "Root" in outline
        assert "A" in outline
        assert "B" in outline

    def test_get_section(self):
        from task_analyzer import MarkdownParser
        parser = MarkdownParser()
        doc = parser.parse("# Doc\n## 需求分析\n内容\n## 代码实现\n代码")
        section = doc.get_section("需求")
        assert section is not None
        assert "需求" in section.title

    def test_empty_doc(self):
        from task_analyzer import MarkdownParser
        parser = MarkdownParser()
        doc = parser.parse("")
        assert doc.title == ""
        assert len(doc.sections) == 0


class TestTaskAnalyzer:
    """TaskAnalyzer 测试"""

    def test_classify_code_generation(self):
        from task_analyzer import TaskAnalyzer, TaskType
        analyzer = TaskAnalyzer()
        result = analyzer.analyze("帮我写一个 Python 脚本，实现文件批量重命名功能")
        assert result.task_type == TaskType.CODE_GENERATION

    def test_classify_debugging(self):
        from task_analyzer import TaskAnalyzer, TaskType
        analyzer = TaskAnalyzer()
        result = analyzer.analyze("这段代码报错了，TypeError: cannot read property of undefined，帮我修复")
        assert result.task_type == TaskType.DEBUGGING

    def test_classify_analysis(self):
        from task_analyzer import TaskAnalyzer, TaskType
        analyzer = TaskAnalyzer()
        result = analyzer.analyze("分析一下这个项目的架构，对比几种方案的优劣")
        assert result.task_type in (TaskType.ANALYSIS, TaskType.MULTI_STEP)

    def test_classify_documentation(self):
        from task_analyzer import TaskAnalyzer, TaskType
        analyzer = TaskAnalyzer()
        result = analyzer.analyze("帮我写一份 README 文档，包含安装说明和使用教程")
        assert result.task_type == TaskType.DOCUMENTATION

    def test_simple_question(self):
        from task_analyzer import TaskAnalyzer, TaskType
        analyzer = TaskAnalyzer()
        result = analyzer.analyze("Python 的 GIL 是什么")
        assert result.task_type in (TaskType.QUESTION, TaskType.ANALYSIS)

    def test_markdown_document_analysis(self):
        from task_analyzer import TaskAnalyzer, TaskType
        analyzer = TaskAnalyzer()
        doc = """# 用户管理系统

## 需求
- 用户注册和登录
- 权限管理
- 数据导出

## 技术要求
- 使用 Python FastAPI
- SQLite 数据库
- JWT 认证

## 验收标准
- 所有 API 端点正常响应
- 单元测试覆盖率 > 80%
"""
        result = analyzer.analyze(doc)
        assert result.doc_structure is not None
        assert len(result.requirements) > 0
        assert result.task_type == TaskType.CODE_GENERATION

    def test_analysis_has_requirements(self):
        from task_analyzer import TaskAnalyzer
        analyzer = TaskAnalyzer()
        result = analyzer.analyze("""
# 任务说明
- 需要实现用户登录功能
- 需要支持 JWT 认证
- 需要密码加密存储
""")
        assert len(result.requirements) > 0

    def test_analysis_has_subtasks(self):
        from task_analyzer import TaskAnalyzer
        analyzer = TaskAnalyzer()
        result = analyzer.analyze("""
# 项目重构
## 数据库层
重构数据库访问层
## API 层
重构 REST API
## 前端
重构前端组件
""")
        assert len(result.subtasks) > 0

    def test_to_prompt_context(self):
        from task_analyzer import TaskAnalyzer
        analyzer = TaskAnalyzer()
        result = analyzer.analyze("写一个排序算法")
        context = result.to_prompt_context()
        assert "[任务分析]" in context
        assert "[任务摘要]" in context

    def test_complexity_estimation(self):
        from task_analyzer import TaskAnalyzer, TaskComplexity
        analyzer = TaskAnalyzer()

        trivial = analyzer.analyze("这是什么")
        assert trivial.complexity in (TaskComplexity.TRIVIAL, TaskComplexity.SIMPLE)

        complex_task = analyzer.analyze("""
# 完整的微服务架构设计
## 服务拆分
## 数据库设计
## API 网关
## 消息队列
## 部署方案
## 监控告警
""")
        assert complex_task.complexity in (TaskComplexity.MEDIUM, TaskComplexity.COMPLEX)

    def test_suggest_tools(self):
        from task_analyzer import TaskAnalyzer
        analyzer = TaskAnalyzer()
        result = analyzer.analyze("写一个 Python 脚本，实现排序算法并生成测试用例")
        # MULTI_STEP 或 CODE_GENERATION 都会推荐 write_file
        assert len(result.suggested_tools) > 0

    def test_keywords_extraction(self):
        from task_analyzer import TaskAnalyzer
        analyzer = TaskAnalyzer()
        result = analyzer.analyze("实现一个 Python FastAPI 用户管理系统")
        assert len(result.keywords) > 0


class TestDocStructure:
    """DocStructure 测试"""

    def test_get_section_by_keyword(self):
        from task_analyzer import MarkdownParser
        parser = MarkdownParser()
        doc = parser.parse("# Project\n## Setup\npip install\n## Usage\nrun it")
        setup = doc.get_section("setup")
        assert setup is not None
        assert "pip" in setup.content

    def test_get_sections_by_pattern(self):
        from task_analyzer import MarkdownParser
        parser = MarkdownParser()
        doc = parser.parse("# Doc\n## 需求一\n## 需求二\n## 实现")
        reqs = doc.get_sections_by_pattern(r"需求")
        assert len(reqs) == 2

    def test_section_full_content(self):
        from task_analyzer import MarkdownParser
        parser = MarkdownParser()
        doc = parser.parse("# Root\n## A\n内容A\n### A1\n内容A1")
        section_a = doc.sections[0]
        full = section_a.full_content
        assert "内容A" in full
        assert "内容A1" in full
