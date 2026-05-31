"""蒙多云仓库同步 — 新 Skill 自动上传 + 每日质量筛选"""

import os
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

MUNDO_HOME = Path.home() / ".hermes" / "mundo-agent"
HERMES_SKILLS = Path.home() / ".hermes" / "skills"
CLOUD_REPO = Path.home() / "Desktop" / "lihongwei-cn" / "mundo-cloud"
SYNC_STATE = MUNDO_HOME / "sync_state.json"
UPLOAD_QUEUE = MUNDO_HOME / "upload_queue.json"


# ═══════════════════════════════════════════════
# 本地同步状态
# ═══════════════════════════════════════════════

def _load_state() -> Dict:
    if SYNC_STATE.exists():
        return json.loads(SYNC_STATE.read_text())
    return {"uploaded": {}, "last_daily": None}


def _save_state(state: Dict):
    MUNDO_HOME.mkdir(parents=True, exist_ok=True)
    SYNC_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


# ═══════════════════════════════════════════════
# 新 Skill 检测 & 排队
# ═══════════════════════════════════════════════

def scan_local_skills() -> List[Dict]:
    """扫描所有本地 Skill"""
    skills = []
    if not HERMES_SKILLS.exists():
        return skills
    for skill_md in HERMES_SKILLS.rglob("SKILL.md"):
        try:
            content = skill_md.read_text(encoding="utf-8")
            name = skill_md.parent.name
            size = len(content)
            h = _file_hash(skill_md)
            skills.append({
                "name": name,
                "path": str(skill_md),
                "hash": h,
                "size": size,
                "modified": skill_md.stat().st_mtime,
            })
        except Exception:
            continue
    return skills


def find_new_skills() -> List[Dict]:
    """找到未上传的新 Skill"""
    state = _load_state()
    uploaded = state.get("uploaded", {})
    all_skills = scan_local_skills()
    new_skills = []
    for s in all_skills:
        if s["name"] not in uploaded or uploaded[s["name"]] != s["hash"]:
            new_skills.append(s)
    return new_skills


def queue_upload(skill_name: str, skill_path: str):
    """将 Skill 加入上传队列"""
    queue = []
    if UPLOAD_QUEUE.exists():
        queue = json.loads(UPLOAD_QUEUE.read_text())

    entry = {
        "name": skill_name,
        "path": skill_path,
        "queued_at": datetime.now().isoformat(),
        "hash": _file_hash(Path(skill_path)),
    }

    # 去重
    queue = [e for e in queue if e["name"] != skill_name]
    queue.append(entry)

    MUNDO_HOME.mkdir(parents=True, exist_ok=True)
    UPLOAD_QUEUE.write_text(json.dumps(queue, indent=2, ensure_ascii=False))


# ═══════════════════════════════════════════════
# 上传到云仓库
# ═══════════════════════════════════════════════

def upload_skill_to_cloud(skill_name: str, skill_path: str) -> bool:
    """将单个 Skill 上传到 mundo-cloud/skills/"""
    if not CLOUD_REPO.exists():
        return False

    cloud_target = CLOUD_REPO / "skills" / skill_name / "SKILL.md"
    cloud_target.parent.mkdir(parents=True, exist_ok=True)

    src = Path(skill_path)
    if not src.exists():
        return False

    # 复制文件
    cloud_target.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    # 更新同步状态
    state = _load_state()
    state["uploaded"][skill_name] = _file_hash(src)
    _save_state(state)

    return True


def process_upload_queue() -> Dict:
    """处理上传队列。返回 {uploaded, failed, skipped}"""
    result = {"uploaded": 0, "failed": 0, "skipped": 0}

    if not UPLOAD_QUEUE.exists():
        return result

    queue = json.loads(UPLOAD_QUEUE.read_text())
    remaining = []

    for entry in queue:
        name = entry["name"]
        path = entry["path"]

        if not Path(path).exists():
            result["skipped"] += 1
            continue

        if upload_skill_to_cloud(name, path):
            result["uploaded"] += 1
        else:
            result["failed"] += 1
            remaining.append(entry)

    # 更新队列
    UPLOAD_QUEUE.write_text(json.dumps(remaining, indent=2, ensure_ascii=False))

    # git push 云仓库
    if result["uploaded"] > 0 and CLOUD_REPO.exists():
        try:
            subprocess.run(
                ["git", "add", "."],
                cwd=str(CLOUD_REPO), capture_output=True, timeout=10
            )
            subprocess.run(
                ["git", "commit", "-m", f"auto: 蒙多自动上传 {result['uploaded']} 个 Skill"],
                cwd=str(CLOUD_REPO), capture_output=True, timeout=10
            )
            subprocess.run(
                ["git", "push"],
                cwd=str(CLOUD_REPO), capture_output=True, timeout=30
            )
        except Exception:
            pass

    return result


def auto_sync_new_skills() -> int:
    """自动检测并同步新 Skill。返回新增数量。"""
    new_skills = find_new_skills()
    count = 0
    for s in new_skills:
        queue_upload(s["name"], s["path"])
        count += 1
    if count > 0:
        process_upload_queue()
    return count


# ═══════════════════════════════════════════════
# 每日质量筛选
# ═══════════════════════════════════════════════

def score_skill(content: str) -> int:
    """质量评分 0-100"""
    score = 0
    lines = content.splitlines()

    # 结构完整性 (30分)
    has_title = any(l.startswith("# ") for l in lines)
    has_desc = any(l.startswith("description:") for l in lines[:10])
    has_sections = sum(1 for l in lines if l.startswith("## ")) >= 2
    score += 10 if has_title else 0
    score += 10 if has_desc else 0
    score += 10 if has_sections else 0

    # 内容质量 (30分)
    content_lines = [l for l in lines if l.strip() and not l.startswith("#") and not l.startswith("---")]
    word_count = sum(len(l.split()) for l in content_lines)
    if word_count > 200:
        score += 15
    elif word_count > 50:
        score += 10
    elif word_count > 10:
        score += 5

    has_code = any("```" in l for l in lines)
    has_tables = any("|" in l and "---" in l for l in lines)
    score += 8 if has_code else 0
    score += 7 if has_tables else 0

    # 可读性 (20分)
    if len(lines) > 20:
        score += 10
    if len(lines) < 500:
        score += 5
    has_list = sum(1 for l in lines if l.strip().startswith(("- ", "* ", "1."))) > 3
    score += 5 if has_list else 0

    # 时效性 (20分)
    if "2026" in content or "2025" in content:
        score += 10
    if any(kw in content.lower() for kw in ["最新", "latest", "v2", "v3", "v4"]):
        score += 5
    if "deprecated" not in content.lower():
        score += 5

    return min(100, score)


def daily_quality_audit() -> Dict:
    """每日质量审计。返回审计结果。"""
    if not CLOUD_REPO.exists():
        return {"error": "云仓库不存在"}

    skills_dir = CLOUD_REPO / "skills"
    if not skills_dir.exists():
        return {"error": "skills 目录不存在"}

    results = {"total": 0, "high": 0, "medium": 0, "low": 0, "flagged": []}

    for skill_md in skills_dir.rglob("SKILL.md"):
        try:
            content = skill_md.read_text(encoding="utf-8")
            s = score_skill(content)
            results["total"] += 1

            name = skill_md.parent.name
            if s >= 70:
                results["high"] += 1
            elif s >= 40:
                results["medium"] += 1
            else:
                results["low"] += 1
                results["flagged"].append({"name": name, "score": s})
        except Exception:
            continue

    # 保存审计日志
    audit_log = MUNDO_HOME / "audit_log.json"
    audit_data = {
        "date": datetime.now().isoformat(),
        "results": results,
    }
    existing = []
    if audit_log.exists():
        existing = json.loads(audit_log.read_text())
    existing.append(audit_data)
    existing = existing[-30:]  # 保留最近30天
    audit_log.write_text(json.dumps(existing, indent=2, ensure_ascii=False))

    return results


# ═══════════════════════════════════════════════
# 云端拉取 — 安装时自动部署 skills + global-specs
# ═══════════════════════════════════════════════

REPO_URL = "https://github.com/LiHongwei-cn/lihongwei-cn.git"
REPO_LOCAL = MUNDO_HOME / "repo_cache"


def ensure_repo_cloned() -> Path:
    """确保云仓库克隆到本地。返回仓库路径。"""
    if REPO_LOCAL.exists():
        # 已有缓存，拉取最新
        try:
            subprocess.run(
                ["git", "pull", "--ff-only"],
                cwd=str(REPO_LOCAL), capture_output=True, timeout=30
            )
        except Exception:
            pass
        return REPO_LOCAL

    # 首次克隆（浅克隆，节省时间）
    try:
        subprocess.run(
            ["git", "clone", "--depth=1", REPO_URL, str(REPO_LOCAL)],
            capture_output=True, timeout=120, check=True
        )
    except Exception as e:
        raise RuntimeError(f"克隆云仓库失败: {e}")
    return REPO_LOCAL


def pull_cloud_skills() -> Dict:
    """从云仓库拉取所有 Skill 到本地 ~/.hermes/skills/"""
    result = {"pulled": 0, "skipped": 0, "failed": 0}

    repo = ensure_repo_cloned()
    cloud_skills = repo / "global-specs" / "skills"
    if not cloud_skills.exists():
        cloud_skills = repo / "mundo-cloud" / "skills"
    if not cloud_skills.exists():
        return {"error": "云仓库中未找到 skills 目录"}

    HERMES_SKILLS.mkdir(parents=True, exist_ok=True)

    for skill_dir in cloud_skills.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        name = skill_dir.name
        local_target = HERMES_SKILLS / name / "SKILL.md"
        local_target.parent.mkdir(parents=True, exist_ok=True)

        try:
            content = skill_md.read_text(encoding="utf-8")
            # 如果本地已存在且内容相同，跳过
            if local_target.exists():
                local_content = local_target.read_text(encoding="utf-8")
                if _file_hash(skill_md) == _file_hash(local_target):
                    result["skipped"] += 1
                    continue
            local_target.write_text(content, encoding="utf-8")
            result["pulled"] += 1
        except Exception:
            result["failed"] += 1

    return result


def pull_global_specs() -> Dict:
    """从云仓库拉取全局规范到本地"""
    result = {"pulled": 0, "skipped": 0}

    repo = ensure_repo_cloned()
    specs_dir = repo / "global-specs"
    if not specs_dir.exists():
        return {"error": "云仓库中未找到 global-specs 目录"}

    # 拉取 rules
    rules_src = specs_dir / "rules"
    rules_dst = Path.home() / ".hermes" / "rules"
    if rules_src.exists():
        rules_dst.mkdir(parents=True, exist_ok=True)
        for f in rules_src.glob("*.md"):
            dst = rules_dst / f.name
            if not dst.exists() or _file_hash(f) != _file_hash(dst):
                dst.write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
                result["pulled"] += 1
            else:
                result["skipped"] += 1

    # 拉取 SKILL.md（蒙多核心）
    mundo_skill = specs_dir / "skills" / "蒙多" / "SKILL.md"
    if mundo_skill.exists():
        mundo_dst = MUNDO_HOME / "SKILL.md"
        mundo_dst.write_text(mundo_skill.read_text(encoding="utf-8"), encoding="utf-8")
        result["pulled"] += 1

    return result


def initial_deploy() -> Dict:
    """首次部署：从云仓库拉取所有 skills + 全局规范"""
    result = {"skills": {}, "specs": {}, "repo_cloned": False}

    try:
        ensure_repo_cloned()
        result["repo_cloned"] = True
    except Exception as e:
        result["error"] = str(e)
        return result

    result["skills"] = pull_cloud_skills()
    result["specs"] = pull_global_specs()
    return result


# ═══════════════════════════════════════════════
# 自动更新 — 保留用户记忆，更新代码
# ═══════════════════════════════════════════════

import urllib.request

# 不会被覆盖的用户文件
PRESERVED_FILES = {
    "memory.db",        # 用户记忆数据库
    ".env",             # API Key
    ".setup_complete",  # 设置完成标记
    "repo_cache",       # 仓库缓存
    "sync_state.json",  # 同步状态
    "upload_queue.json", # 上传队列
    "audit_log.json",   # 审计日志
    "SKILL.md",         # 蒙多 Skill
    "memory",           # 记忆目录
    "config",           # 配置目录
    "static",           # 静态资源
    "templates",        # 模板
}

# 可更新的代码文件
UPDATABLE_FILES = [
    "mundo.py", "engine.py", "llm.py", "tools.py",
    "agents.py", "delegation.py", "approval.py",
    "cloud_sync.py", "setup.py", "models.py", "memory.py",
    "mundo.sh", "mundo.bat", "MUNDO.command",
    "install.sh", "install.ps1", "index.html",
]

RAW_BASE = "https://raw.githubusercontent.com/LiHongwei-cn/lihongwei-cn/main/mundo-agent"


def get_local_version() -> str:
    """获取本地版本号"""
    version_file = MUNDO_HOME / "version.txt"
    if version_file.exists():
        return version_file.read_text().strip()
    return "0.0.0"


def get_remote_version() -> str:
    """从 GitHub 获取最新版本号"""
    try:
        url = f"{RAW_BASE}/version.txt"
        req = urllib.request.Request(url, headers={"User-Agent": "mundo-agent"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode().strip()
    except Exception:
        return get_local_version()


def save_local_version(version: str):
    (MUNDO_HOME / "version.txt").write_text(version)


def check_update() -> Dict:
    """检查是否有更新。返回 {available, local, remote, changelog}"""
    local = get_local_version()
    remote = get_remote_version()

    if local == remote:
        return {"available": False, "local": local, "remote": remote}

    # 获取更新日志
    changelog = ""
    try:
        url = f"{RAW_BASE}/CHANGELOG.md"
        req = urllib.request.Request(url, headers={"User-Agent": "mundo-agent"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            changelog = resp.read().decode()[:500]
    except Exception:
        pass

    return {
        "available": True,
        "local": local,
        "remote": remote,
        "changelog": changelog,
    }


def perform_update() -> Dict:
    """执行更新。保留用户记忆和配置，更新代码文件。"""
    result = {"updated": [], "skipped": [], "failed": [], "preserved": []}

    # 备份用户文件
    backup_dir = MUNDO_HOME / ".backup"
    backup_dir.mkdir(exist_ok=True)
    for fname in PRESERVED_FILES:
        src = MUNDO_HOME / fname
        if src.exists():
            dst = backup_dir / fname
            if src.is_file():
                import shutil
                shutil.copy2(str(src), str(dst))
            elif src.is_dir():
                import shutil
                if dst.exists():
                    shutil.rmtree(str(dst))
                shutil.copytree(str(src), str(dst))
            result["preserved"].append(fname)

    # 下载并替换代码文件
    for fname in UPDATABLE_FILES:
        try:
            url = f"{RAW_BASE}/{fname}"
            req = urllib.request.Request(url, headers={"User-Agent": "mundo-agent"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read()

            target = MUNDO_HOME / fname
            # 写入临时文件再替换（原子操作）
            tmp = target.with_suffix(".tmp")
            tmp.write_bytes(content)
            tmp.replace(target)

            # 设置脚本可执行
            if fname.endswith((".sh", ".command")):
                os.chmod(str(target), 0o755)

            result["updated"].append(fname)
        except Exception as e:
            result["failed"].append(f"{fname}: {e}")

    # 恢复用户文件（确保不被覆盖）
    for fname in PRESERVED_FILES:
        src = backup_dir / fname
        dst = MUNDO_HOME / fname
        if src.exists() and not dst.exists():
            import shutil
            if src.is_file():
                shutil.copy2(str(src), str(dst))
            elif src.is_dir():
                shutil.copytree(str(src), str(dst))

    # 清理备份
    import shutil
    shutil.rmtree(str(backup_dir), ignore_errors=True)

    # 更新版本号
    remote_ver = get_remote_version()
    save_local_version(remote_ver)
    result["new_version"] = remote_ver

    return result
