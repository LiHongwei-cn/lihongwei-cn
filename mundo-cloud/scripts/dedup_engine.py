#!/usr/bin/env python3
"""Deduplication + comparison engine for Mundo skills.

Compares a candidate SKILL.md against all existing skills in skills/:
  - similarity >= 0.9 → near-duplicate (skip or replace if better)
  - similarity >= 0.7 → similar (warn, compare quality)
  - similarity <  0.7 → unique (add)

Stdlib only — uses difflib.SequenceMatcher.
"""

from __future__ import annotations

import json
import sys
from difflib import SequenceMatcher
from pathlib import Path

# Resolve sibling import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from quality_scorer import score_skill

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
NEAR_DUPLICATE_THRESHOLD = 0.9
SIMILAR_THRESHOLD = 0.7


def _read_skill(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _find_existing_skills() -> list[Path]:
    """Find all SKILL.md files under skills/."""
    return sorted(SKILLS_DIR.rglob("SKILL.md"))


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
    candidate_score = score_skill(candidate)
    existing = _find_existing_skills()

    if not existing:
        return {
            "action": "add",
            "reason": "No existing skills — this is the first one",
            "similarity": 0.0,
            "matched_skill": None,
            "candidate_score": candidate_score["total"],
        }

    best_sim = 0.0
    best_match: Path | None = None
    best_match_text = ""

    for skill_path in existing:
        skill_text = _read_skill(skill_path)
        sim = _similarity(candidate_text, skill_text)
        if sim > best_sim:
            best_sim = sim
            best_match = skill_path
            best_match_text = skill_text

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
    if len(sys.argv) < 2:
        print("Usage: python dedup_engine.py <path/to/SKILL.md>", file=sys.stderr)
        sys.exit(1)

    result = check_duplicate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
