"""Skill 云仓库主模块 — 分类管理、存储、查询 GitHub 上的高星 skill 项目"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict

from github_skill_crawler import run_crawler


# ── 常量 ──────────────────────────────────────────────────────────────────────

STORE_DIR = Path(__file__).parent / "skill_store"
CATEGORIES_FILE = STORE_DIR / "categories.json"
SKILLS_INDEX_FILE = STORE_DIR / "skills_index.json"
CRAWL_LOG_FILE = STORE_DIR / "crawl_log.json"


# ── Skill 分类定义 ────────────────────────────────────────────────────────────

DEFAULT_CATEGORIES = {
    "code-generation": {
        "name": "代码生成",
        "keywords": ["code", "generate", "codegen", "scaffold", "boilerplate"],
        "description": "自动生成代码、模板、脚手架",
    },
    "code-review": {
        "name": "代码审查",
        "keywords": ["review", "lint", "static-analysis", "quality"],
        "description": "代码审查、静态分析、质量检查",
    },
    "testing": {
        "name": "测试",
        "keywords": ["test", "tdd", "bdd", "coverage", "e2e", "unit-test"],
        "description": "单元测试、集成测试、E2E 测试",
    },
    "refactoring": {
        "name": "重构优化",
        "keywords": ["refactor", "clean", "optimize", "performance"],
        "description": "代码重构、性能优化、死代码清理",
    },
    "documentation": {
        "name": "文档生成",
        "keywords": ["doc", "readme", "markdown", "api-doc", "changelog"],
        "description": "文档生成、README、API 文档",
    },
    "security": {
        "name": "安全",
        "keywords": ["security", "audit", "vulnerability", "cve", "pentest"],
        "description": "安全审计、漏洞扫描、渗透测试",
    },
    "devops": {
        "name": "DevOps",
        "keywords": ["ci", "cd", "deploy", "docker", "kubernetes", "pipeline"],
        "description": "CI/CD、部署、容器化、流水线",
    },
    "agent-framework": {
        "name": "Agent 框架",
        "keywords": ["agent", "framework", "orchestration", "workflow", "multi-agent"],
        "description": "AI Agent 框架、工作流编排",
    },
    "prompt-engineering": {
        "name": "提示工程",
        "keywords": ["prompt", "chain-of-thought", "few-shot", "in-context"],
        "description": "提示词优化、思维链、少样本学习",
    },
    "mcp": {
        "name": "MCP 协议",
        "keywords": ["mcp", "model-context-protocol", "tool-use", "function-call"],
        "description": "MCP 服务器、工具调用、协议集成",
    },
    "other": {
        "name": "其他",
        "keywords": [],
        "description": "未分类的 skill 项目",
    },
}


# ── 数据操作 ──────────────────────────────────────────────────────────────────

def load_json(path: Path, default=None):
    """安全加载 JSON 文件"""
    if path.exists():
        return json.loads(path.read_text())
    return default if default is not None else {}


def save_json(path: Path, data) -> None:
    """保存数据到 JSON 文件"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def init_categories() -> dict:
    """初始化分类文件（首次运行）"""
    if not CATEGORIES_FILE.exists():
        save_json(CATEGORIES_FILE, DEFAULT_CATEGORIES)
        print(f"[云仓库] 分类文件已初始化: {CATEGORIES_FILE}")
    return load_json(CATEGORIES_FILE, DEFAULT_CATEGORIES)


# ── 分类逻辑 ──────────────────────────────────────────────────────────────────

def classify_skill(project: dict, categories: dict) -> str:
    """根据项目信息自动分类"""
    text = " ".join([
        project.get("name", ""),
        project.get("description", ""),
        " ".join(project.get("topics", [])),
    ]).lower()

    best_match = "other"
    best_score = 0

    for cat_id, cat_info in categories.items():
        if cat_id == "other":
            continue
        score = sum(1 for kw in cat_info["keywords"] if kw in text)
        if score > best_score:
            best_score = score
            best_match = cat_id

    return best_match


def classify_all_projects(projects: List[Dict], categories: Dict) -> Dict[str, List[Dict]]:
    """将所有项目分类到对应类别"""
    classified = {cat_id: [] for cat_id in categories}

    for project in projects:
        cat_id = classify_skill(project, categories)
        classified[cat_id].append(project)

    # 移除空分类
    return {k: v for k, v in classified.items() if v}


# ── 索引构建 ──────────────────────────────────────────────────────────────────

def build_skills_index(classified: dict, categories: dict) -> dict:
    """构建 skill 索引"""
    index = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_skills": sum(len(v) for v in classified.values()),
        "categories": {},
    }

    for cat_id, projects in classified.items():
        cat_info = categories.get(cat_id, {})
        index["categories"][cat_id] = {
            "name": cat_info.get("name", cat_id),
            "description": cat_info.get("description", ""),
            "count": len(projects),
            "top_projects": [
                {
                    "name": p["name"],
                    "url": p["url"],
                    "stars": p["stars"],
                    "description": p["description"][:100],
                }
                for p in projects[:5]
            ],
        }

    return index


# ── 持久化 ────────────────────────────────────────────────────────────────────

def save_classified_skills(classified: dict) -> None:
    """按分类保存 skill 数据"""
    for cat_id, projects in classified.items():
        cat_file = STORE_DIR / f"category_{cat_id}.json"
        save_json(cat_file, {
            "category": cat_id,
            "count": len(projects),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "projects": projects,
        })
    print(f"[云仓库] 已保存 {len(classified)} 个分类的 skill 数据")


def append_crawl_log(total: int, categories: int) -> None:
    """追加爬取日志"""
    logs = load_json(CRAWL_LOG_FILE, [])
    logs.append({
        "time": datetime.now(timezone.utc).isoformat(),
        "total_skills": total,
        "categories": categories,
    })
    # 只保留最近 50 条日志
    save_json(CRAWL_LOG_FILE, logs[-50:])


# ── 查询接口 ──────────────────────────────────────────────────────────────────

def list_categories() -> List[Dict]:
    """列出所有分类及其 skill 数量"""
    categories = load_json(CATEGORIES_FILE, DEFAULT_CATEGORIES)
    result = []
    for cat_id, info in categories.items():
        cat_file = STORE_DIR / f"category_{cat_id}.json"
        count = 0
        if cat_file.exists():
            data = load_json(cat_file, {})
            count = data.get("count", 0)
        result.append({
            "id": cat_id,
            "name": info["name"],
            "description": info["description"],
            "count": count,
        })
    return result


def search_skills(keyword: str) -> List[Dict]:
    """在所有分类中搜索 skill"""
    keyword = keyword.lower()
    results = []
    for cat_file in STORE_DIR.glob("category_*.json"):
        data = load_json(cat_file, {})
        for project in data.get("projects", []):
            text = " ".join([
                project.get("name", ""),
                project.get("description", ""),
            ]).lower()
            if keyword in text:
                results.append(project)
    results.sort(key=lambda x: x.get("stars", 0), reverse=True)
    return results


def get_top_skills(limit: int = 20) -> List[Dict]:
    """获取全站 star 最高的 skill"""
    all_skills = []
    for cat_file in STORE_DIR.glob("category_*.json"):
        data = load_json(cat_file, {})
        all_skills.extend(data.get("projects", []))
    all_skills.sort(key=lambda x: x.get("stars", 0), reverse=True)
    return all_skills[:limit]


# ── 主流程 ────────────────────────────────────────────────────────────────────

def sync_skills() -> dict:
    """完整同步流程：爬取 → 分类 → 存储 → 建索引"""
    print("[云仓库] 开始同步 skill 数据...")

    # 1. 初始化分类
    categories = init_categories()

    # 2. 爬取 GitHub
    projects = run_crawler()
    if not projects:
        print("[云仓库] 未获取到任何项目，跳过本次同步")
        return {"status": "empty", "total": 0}

    # 3. 分类
    classified = classify_all_projects(projects, categories)

    # 4. 存储
    save_classified_skills(classified)

    # 5. 建索引
    index = build_skills_index(classified, categories)
    save_json(SKILLS_INDEX_FILE, index)

    # 6. 记录日志
    append_crawl_log(index["total_skills"], len(classified))

    print(f"[云仓库] 同步完成: {index['total_skills']} 个 skill, {len(classified)} 个分类")
    return {
        "status": "ok",
        "total": index["total_skills"],
        "categories": len(classified),
    }


def get_status() -> dict:
    """获取云仓库当前状态"""
    index = load_json(SKILLS_INDEX_FILE, {})
    logs = load_json(CRAWL_LOG_FILE, [])
    return {
        "total_skills": index.get("total_skills", 0),
        "last_updated": index.get("updated_at", "从未更新"),
        "crawl_count": len(logs),
        "last_crawl": logs[-1]["time"] if logs else "从未爬取",
    }


# ── CLI 入口 ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python skill_cloud.py [sync|status|search|top]")
        print("  sync          — 同步 GitHub 高星 skill 项目")
        print("  status        — 查看云仓库状态")
        print("  search <词>   — 搜索 skill")
        print("  top [数量]     — 查看 star 最高的 skill")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "sync":
        result = sync_skills()
        print(f"\n同步结果: {result}")

    elif cmd == "status":
        status = get_status()
        print(f"\n云仓库状态:")
        print(f"  总 skill 数: {status['total_skills']}")
        print(f"  最后更新: {status['last_updated']}")
        print(f"  爬取次数: {status['crawl_count']}")

    elif cmd == "search":
        keyword = sys.argv[2] if len(sys.argv) > 2 else ""
        if not keyword:
            print("请提供搜索关键词")
            sys.exit(1)
        results = search_skills(keyword)
        print(f"\n搜索 '{keyword}' 结果 ({len(results)} 条):")
        for r in results[:10]:
            print(f"  [{r['stars']}★] {r['name']} — {r['description'][:60]}")

    elif cmd == "top":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        top = get_top_skills(limit)
        print(f"\nTop {limit} Skill 项目:")
        for i, r in enumerate(top, 1):
            print(f"  {i}. [{r['stars']}★] {r['name']} — {r['description'][:60]}")

    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)
