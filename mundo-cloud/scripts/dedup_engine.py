#!/usr/bin/env python3
"""Deduplication + comparison engine for Mundo skills.

Fast path: SHA-256 hash match → immediate skip.
Slow path: SequenceMatcher comparison against existing skills.

  - similarity >= 0.9 → near-duplicate (skip or replace if better)
  - similarity >= 0.7 → similar (warn, compare quality)
  - similarity <  0.7 → unique (add)

Stdlib only — uses difflib.SequenceMatcher.
"""

from __future__ import annotations

import hashlib
import json
import sys
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quality_scorer import score_skill

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
REGISTRY_PATH = Path(__file__).resolve().parent.parent / "sync" / "registry.json"
NEAR_DUPLICATE_THRESHOLD = 0.9
SIMILAR_THRESHOLD = 0.7


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_skill(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _find_existing_skills() -> list[Path]:
    return sorted(SKILLS_DIR.rglob("SKILL.md"))


def _load_registry_hashes() -> dict[str, str]:
    """Load stored content hashes from registry.json."""
    if not REGISTRY_PATH.exists():
        return {}
    try:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    hashes: dict[str, str] = {}
    for name, info in registry.get("skills", {}).items():
        h = info.get("content_hash")
        if h:
            hashes[name] = h
    return hashes


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def check_duplicate(candidate_path: str | Path) -> dict:
    """Check if candidate skill is a duplicate of an existing skill.

    Returns dict with:
      - action: "add" | "skip" | "replace"
      - reason: human-readable explanation
      - similarity: float (best match)
      - matched_skill: path of closest match (if any)
    """
    candidate = Path(candidate_path)
    if not candidate.exists():
        return {"action": "skip", "reason": f"File not found: {candidate}", "similarity": 0.0}

    candidate_text = _read_skill(candidate)
    candidate_hash = _content_hash(candidate_text)
    candidate_score = score_skill(candidate)

    # --- Fast path: SHA-256 hash match ---
    registry_hashes = _load_registry_hashes()
    for name, stored_hash in registry_hashes.items():
        if stored_hash == candidate_hash:
            return {
                "action": "skip",
                "reason": f"Exact content hash match with existing skill '{name}'",
                "similarity": 1.0,
                "matched_skill": name,
                "candidate_score": candidate_score["total"],
                "hash_match": True,
            }

    # --- Slow path: SequenceMatcher comparison ---
    existing = _find_existing_skills()

    if not existing:
        return {
            "action": "add",
            "reason": "No existing skills — this is the first one",
            "similarity": 0.0,
            "matched_skill": None,
            "candidate_score": candidate_score["total"],
        }

    # Cache existing skill texts to avoid re-reading in scoring step
    cached_texts: dict[Path, str] = {}
    best_sim = 0.0
    best_match: Path | None = None

    for skill_path in existing:
        skill_text = _read_skill(skill_path)
        cached_texts[skill_path] = skill_text
        sim = _similarity(candidate_text, skill_text)
        if sim > best_sim:
            best_sim = sim
            best_match = skill_path

    result: dict = {
        "similarity": round(best_sim, 4),
        "matched_skill": str(best_match) if best_match else None,
        "candidate_score": candidate_score["total"],
    }

    if best_sim >= NEAR_DUPLICATE_THRESHOLD:
        existing_score = score_skill(best_match)["total"] if best_match else 0
        result["existing_score"] = existing_score
        if candidate_score["total"] > existing_score:
            result["action"] = "replace"
            result["reason"] = (
                f"Near-duplicate (sim={best_sim:.2f}) but candidate scores higher "
                f"({candidate_score['total']} > {existing_score})"
            )
        else:
            result["action"] = "skip"
            result["reason"] = (
                f"Near-duplicate (sim={best_sim:.2f}) and existing skill is equal or better "
                f"({existing_score} >= {candidate_score['total']})"
            )
    elif best_sim >= SIMILAR_THRESHOLD:
        existing_score = score_skill(best_match)["total"] if best_match else 0
        result["existing_score"] = existing_score
        if candidate_score["total"] > existing_score + 10:
            result["action"] = "replace"
            result["reason"] = (
                f"Similar skill exists (sim={best_sim:.2f}) but candidate is significantly better "
                f"({candidate_score['total']} vs {existing_score})"
            )
        else:
            result["action"] = "add"
            result["reason"] = (
                f"Similar skill exists (sim={best_sim:.2f}) but candidate is sufficiently different"
            )
    else:
        result["action"] = "add"
        result["reason"] = f"Unique skill (best similarity={best_sim:.2f} < {SIMILAR_THRESHOLD})"

    return result


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print("Usage: python dedup_engine.py <path/to/SKILL.md>", file=sys.stderr)
        print("Check if a skill duplicates existing skills in the cloud repo.", file=sys.stderr)
        sys.exit(1)

    result = check_duplicate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
