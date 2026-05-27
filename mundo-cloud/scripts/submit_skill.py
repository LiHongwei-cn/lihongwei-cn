#!/usr/bin/env python3
"""Submit a new skill to the Mundo cloud repository.

Usage:
  python submit_skill.py /path/to/SKILL.md

Workflow:
  1. Run quality scorer — reject if score < 40
  2. Run dedup check — skip/replace as needed
  3. Copy to skills/<name>/SKILL.md
  4. Update registry.json (with content hash)

Stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dedup_engine import check_duplicate
from quality_scorer import score_skill

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
REGISTRY_PATH = REPO_ROOT / "sync" / "registry.json"
MIN_QUALITY_SCORE = 40


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_version(version_str: str) -> list[int]:
    """Parse a version string into a list of int parts."""
    return [int(x) for x in re.split(r"\.", version_str) if x.isdigit()]


def _bump_version(existing_version: str) -> str:
    """Bump the minor version using proper semantic versioning."""
    parts = _parse_version(existing_version)
    if len(parts) < 2:
        parts = [0, 0]
    parts[1] += 1
    return ".".join(str(p) for p in parts[:2])


def _load_registry() -> dict:
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {
        "version": "1.0",
        "skills": {},
        "last_sync": None,
        "total_submissions": 0,
        "total_evolved": 0,
    }


def _save_registry(registry: dict) -> None:
    REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _extract_skill_name(skill_path: Path) -> str:
    """Derive a directory name from the SKILL.md frontmatter or filename."""
    text = skill_path.read_text(encoding="utf-8")

    if text.lstrip().startswith("---"):
        fm_end = text.find("---", 3)
        if fm_end > 0:
            fm = text[3:fm_end]
            name_match = re.search(r"name:\s*[\"']?(.+?)[\"']?\s*$", fm, re.MULTILINE)
            if name_match:
                return re.sub(r"[^a-z0-9_-]", "-", name_match.group(1).strip().lower())

    return skill_path.parent.name.lower().replace(" ", "-")


def _get_author(skill_path: Path) -> str:
    """Extract author from frontmatter or default to 'unknown'."""
    text = skill_path.read_text(encoding="utf-8")
    if text.lstrip().startswith("---"):
        fm_end = text.find("---", 3)
        if fm_end > 0:
            fm = text[3:fm_end]
            author_match = re.search(r"author:\s*[\"']?(.+?)[\"']?\s*$", fm, re.MULTILINE)
            if author_match:
                return author_match.group(1).strip()
    return "unknown"


def submit_skill(skill_path: str | Path) -> dict:
    """Submit a skill to the cloud repository.

    Returns a result dict with action taken and details.
    """
    path = Path(skill_path).resolve()
    result: dict = {"file": str(path), "steps": []}

    # Step 1: Quality check
    quality = score_skill(path)
    result["quality"] = quality
    result["steps"].append(f"Quality score: {quality['total']}/100")

    if quality["total"] < MIN_QUALITY_SCORE:
        result["action"] = "rejected"
        result["reason"] = f"Quality score {quality['total']} below minimum {MIN_QUALITY_SCORE}"
        return result

    # Step 2: Dedup check
    dedup = check_duplicate(path)
    result["dedup"] = dedup
    result["steps"].append(f"Dedup action: {dedup['action']} — {dedup['reason']}")

    if dedup["action"] == "skip":
        result["action"] = "skipped"
        result["reason"] = dedup["reason"]
        return result

    # Step 3: Copy skill to repository
    skill_name = _extract_skill_name(path)
    dest_dir = SKILLS_DIR / skill_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / "SKILL.md"
    shutil.copy2(path, dest_file)
    result["steps"].append(f"Copied to {dest_file.relative_to(REPO_ROOT)}")

    # Integrity verification after copy
    source_text = path.read_text(encoding="utf-8")
    dest_text = dest_file.read_text(encoding="utf-8")
    source_hash = _content_hash(source_text)
    dest_hash = _content_hash(dest_text)
    if source_hash != dest_hash:
        dest_file.unlink(missing_ok=True)
        result["action"] = "error"
        result["reason"] = "Integrity check failed: source and destination hashes differ after copy"
        return result
    result["steps"].append(f"Integrity verified: {dest_hash[:16]}…")

    # Step 4: Update registry
    registry = _load_registry()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    author = _get_author(path)

    existing_version = registry["skills"].get(skill_name, {}).get("version", "0.0")
    new_version = _bump_version(existing_version)

    registry["skills"][skill_name] = {
        "version": new_version,
        "score": quality["total"],
        "author": author,
        "date": now,
        "path": f"skills/{skill_name}/SKILL.md",
        "content_hash": source_hash,
    }
    registry["total_submissions"] = registry.get("total_submissions", 0) + 1
    _save_registry(registry)
    result["steps"].append(f"Registry updated: {skill_name} v{new_version}")

    result["action"] = "added" if dedup["action"] == "add" else "replaced"
    result["reason"] = dedup["reason"]
    result["skill_name"] = skill_name
    result["version"] = new_version
    result["content_hash"] = source_hash

    return result


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print("Usage: python submit_skill.py <path/to/SKILL.md>", file=sys.stderr)
        print("Submit a skill to the Mundo cloud repository.", file=sys.stderr)
        sys.exit(1)

    result = submit_skill(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result["action"] in ("added", "replaced"):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
