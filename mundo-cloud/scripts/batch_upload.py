#!/usr/bin/env python3
"""Batch upload all custom skills to Mundo cloud repository."""

import shutil, json, hashlib, re
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO / "skills"
REGISTRY_PATH = REPO / "sync" / "registry.json"

registry = json.loads(REGISTRY_PATH.read_text("utf-8"))
hermes = Path.home() / ".hermes" / "skills"
gs = Path.home() / "Desktop" / "lihongwei-cn" / "global-specs" / "skills"

skills_to_upload = {}

# Custom skills
for name in ["code-tidy", "homepage-layout", "neat-freak", "cross-platform-launcher", "matlab-ai-generator"]:
    src = hermes / name / "SKILL.md"
    if src.exists():
        skills_to_upload[name] = src

# Nature academic skills
for name in ["nature-writing", "nature-polishing", "nature-figure", "nature-citation",
             "nature-data", "nature-reader", "nature-response", "nature-paper2ppt", "nature-academic-search"]:
    src = gs / name / "SKILL.md"
    if src.exists():
        skills_to_upload[name] = src

uploaded = []
for name, src_path in skills_to_upload.items():
    dest_dir = SKILLS_DIR / name
    dest_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(src_path, dest_dir / "SKILL.md")

    for subdir in ["references", "templates"]:
        src_sub = src_path.parent / subdir
        if src_sub.is_dir():
            dest_sub = dest_dir / subdir
            if dest_sub.exists():
                shutil.rmtree(dest_sub)
            shutil.copytree(src_sub, dest_sub)

    content = (dest_dir / "SKILL.md").read_text("utf-8")
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    version = "1.0.0"
    author = "LiHongwei"
    if content.startswith("---"):
        fm_end = content.find("---", 3)
        if fm_end > 0:
            fm = content[3:fm_end]
            vm = re.search(r'version["\']?\s*[:=]\s*["\']?(\d+\.\d+)', fm)
            if vm:
                version = vm.group(1)
            am = re.search(r'author["\']?\s*[:=]\s*["\']?(.+?)$', fm, re.MULTILINE)
            if am:
                author = am.group(1).strip().strip('"\'')

    registry["skills"][name] = {
        "version": version,
        "score": 0,
        "author": author,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "path": f"skills/{name}/SKILL.md",
        "content_hash": content_hash,
    }
    registry["total_submissions"] = registry.get("total_submissions", 0) + 1
    uploaded.append(name)

REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", "utf-8")

print(f"Uploaded {len(uploaded)} skills:")
for name in uploaded:
    print(f"  - {name}")
print(f"Total skills in registry: {len(registry['skills'])}")
