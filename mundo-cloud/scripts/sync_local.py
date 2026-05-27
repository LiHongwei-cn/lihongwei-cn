#!/usr/bin/env python3
"""Sync cloud skills to local Mundo installation.

Reads registry.json, compares with local ~/.hermes/skills/mundo/,
downloads new/updated skills, logs changes to evolution_log.json.

Stdlib only.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "sync" / "registry.json"
EVOLUTION_LOG = REPO_ROOT / "sync" / "evolution_log.json"
LOCAL_SKILLS_DIR = Path.home() / ".hermes" / "skills" / "mundo"


def _load_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _get_local_versions() -> dict[str, str]:
    """Read local skill versions from LOCAL_SKILLS_DIR/<name>/version.txt."""
    versions: dict[str, str] = {}
    if not LOCAL_SKILLS_DIR.exists():
        return versions
    for skill_dir in LOCAL_SKILLS_DIR.iterdir():
        if skill_dir.is_dir():
            version_file = skill_dir / "version.txt"
            if version_file.exists():
                versions[skill_dir.name] = version_file.read_text().strip()
    return versions


def _write_local_version(skill_name: str, version: str) -> None:
    skill_dir = LOCAL_SKILLS_DIR / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "version.txt").write_text(version + "\n", encoding="utf-8")


def _log_evolution(entry: dict) -> None:
    log = _load_json(EVOLUTION_LOG)
    if "entries" not in log:
        log["entries"] = []
    log["entries"].insert(0, entry)
    # Keep last 200 entries
    log["entries"] = log["entries"][:200]
    _save_json(EVOLUTION_LOG, log)


def sync_local() -> dict:
    """Sync cloud skills to local Mundo installation.

    Returns a summary of actions taken.
    """
    registry = _load_json(REGISTRY_PATH)
    if not registry.get("skills"):
        return {"status": "empty", "message": "No skills in registry", "synced": 0}

    local_versions = _get_local_versions()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    synced: list[dict] = []
    skipped: list[str] = []
    errors: list[dict] = []

    for skill_name, skill_info in registry["skills"].items():
        cloud_version = skill_info.get("version", "0.0")
        local_version = local_versions.get(skill_name, "0.0")

        if cloud_version <= local_version:
            skipped.append(skill_name)
            continue

        # Copy skill from cloud to local
        cloud_skill_path = REPO_ROOT / skill_info.get("path", f"skills/{skill_name}/SKILL.md")
        if not cloud_skill_path.exists():
            errors.append({"skill": skill_name, "error": f"Cloud file missing: {cloud_skill_path}"})
            continue

        try:
            local_dest = LOCAL_SKILLS_DIR / skill_name / "SKILL.md"
            local_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cloud_skill_path, local_dest)
            _write_local_version(skill_name, cloud_version)

            synced.append({
                "skill": skill_name,
                "from_version": local_version,
                "to_version": cloud_version,
                "score": skill_info.get("score", 0),
            })
        except Exception as e:
            errors.append({"skill": skill_name, "error": str(e)})

    # Update registry
    registry["last_sync"] = now
    registry["total_evolved"] = registry.get("total_evolved", 0) + len(synced)
    _save_json(REGISTRY_PATH, registry)

    # Log evolution
    if synced:
        _log_evolution({
            "timestamp": now,
            "action": "sync",
            "synced_count": len(synced),
            "skills": synced,
        })

    return {
        "status": "ok",
        "timestamp": now,
        "synced": len(synced),
        "skipped": len(skipped),
        "errors": len(errors),
        "details": {
            "synced": synced,
            "skipped": skipped,
            "errors": errors,
        },
    }


def main() -> None:
    result = sync_local()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
