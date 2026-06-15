"""Skill 云仓库 — 分类、存储、查询"""

import json
from datetime import datetime, timezone
from pathlib import Path

from github_skill_crawler import run_crawler

STORE = Path(__file__).parent / "skill_store"
CATS_FILE = STORE / "categories.json"
INDEX_FILE = STORE / "skills_index.json"
LOG_FILE = STORE / "crawl_log.json"

CATEGORIES = {
    "code-generation": {"name": "代码生成", "kw": ["code", "generate", "codegen", "scaffold"]},
    "code-review":     {"name": "代码审查", "kw": ["review", "lint", "static-analysis"]},
    "testing":         {"name": "测试",     "kw": ["test", "tdd", "bdd", "coverage", "e2e"]},
    "refactoring":     {"name": "重构优化", "kw": ["refactor", "clean", "optimize"]},
    "documentation":   {"name": "文档生成", "kw": ["doc", "readme", "markdown", "changelog"]},
    "security":        {"name": "安全",     "kw": ["security", "audit", "vulnerability"]},
    "devops":          {"name": "DevOps",   "kw": ["ci", "cd", "deploy", "docker", "k8s"]},
    "agent-framework": {"name": "Agent框架", "kw": ["agent", "framework", "orchestration"]},
    "prompt":          {"name": "提示工程", "kw": ["prompt", "chain-of-thought", "few-shot"]},
    "mcp":             {"name": "MCP协议",  "kw": ["mcp", "model-context-protocol", "tool-use"]},
    "other":           {"name": "其他",     "kw": []},
}


def _load(path, default=None):
    return json.loads(path.read_text()) if path.exists() else (default if default is not None else {})


def _save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def classify(project: dict) -> str:
    text = f"{project.get('name','')} {project.get('description','')} {' '.join(project.get('topics',[]))}".lower()
    best, score = "other", 0
    for cid, info in CATEGORIES.items():
        if cid == "other":
            continue
        s = sum(1 for kw in info["kw"] if kw in text)
        if s > score:
            best, score = cid, s
    return best


def sync_skills() -> dict:
    """爬取 → 分类 → 存储"""
    if not CATS_FILE.exists():
        _save(CATS_FILE, CATEGORIES)

    projects = run_crawler()
    if not projects:
        return {"status": "empty", "total": 0}

    # 分类
    buckets = {}
    for p in projects:
        buckets.setdefault(classify(p), []).append(p)

    # 存储分类文件
    now = datetime.now(timezone.utc).isoformat()
    for cid, items in buckets.items():
        _save(STORE / f"category_{cid}.json", {"category": cid, "count": len(items), "updated_at": now, "projects": items})

    # 索引
    index = {"updated_at": now, "total_skills": len(projects), "categories": {}}
    for cid, items in buckets.items():
        index["categories"][cid] = {
            "name": CATEGORIES[cid]["name"],
            "count": len(items),
            "top": [{"name": p["name"], "url": p["url"], "stars": p["stars"]} for p in items[:5]],
        }
    _save(INDEX_FILE, index)

    # 日志
    logs = _load(LOG_FILE, [])
    logs.append({"time": now, "total": len(projects), "cats": len(buckets)})
    _save(LOG_FILE, logs[-50:])

    print(f"[云仓库] 同步完成: {len(projects)} skill, {len(buckets)} 分类")
    return {"status": "ok", "total": len(projects), "categories": len(buckets)}


def search(keyword: str) -> List[Dict]:
    kw = keyword.lower()
    results = []
    for f in STORE.glob("category_*.json"):
        for p in _load(f, {}).get("projects", []):
            if kw in f"{p.get('name','')} {p.get('description','')}".lower():
                results.append(p)
    return sorted(results, key=lambda x: x.get("stars", 0), reverse=True)


def top(limit: int = 20) -> List[Dict]:
    all_s = []
    for f in STORE.glob("category_*.json"):
        all_s.extend(_load(f, {}).get("projects", []))
    return sorted(all_s, key=lambda x: x.get("stars", 0), reverse=True)[:limit]


def status() -> dict:
    idx = _load(INDEX_FILE, {})
    logs = _load(LOG_FILE, [])
    return {"total": idx.get("total_skills", 0), "updated": idx.get("updated_at", "从未"), "crawls": len(logs)}


if __name__ == "__main__":
    import sys
    cmds = {"sync": lambda: print(sync_skills()), "status": lambda: print(status())}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(f"用法: python skill_cloud.py [{'|'.join(cmds)}]")
        sys.exit(0 if len(sys.argv) < 2 else 1)
    cmds[sys.argv[1]]()
