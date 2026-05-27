#!/usr/bin/env python3
"""Quality scoring engine for Mundo skills.

Scores a SKILL.md file on four dimensions (0–100 total):
  - Structure   (0–30): frontmatter, sections, examples
  - Completeness(0–25): description length, code blocks, tables
  - Documentation(0–25): comments, usage instructions, pitfalls
  - Freshness   (0–20): recency, active maintenance signals

Stdlib only — no pip install needed.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def _has_frontmatter(text: str) -> bool:
    return text.lstrip().startswith("---")


def _count_sections(text: str) -> int:
    return len(re.findall(r"^#{1,6}\s+", text, re.MULTILINE))


def _count_examples(text: str) -> int:
    return len(re.findall(r"```", text)) // 2


def _count_tables(text: str) -> int:
    return len(re.findall(r"^\|.+\|$", text, re.MULTILINE)) // 2


def _count_code_blocks(text: str) -> int:
    return len(re.findall(r"```", text)) // 2


def _has_comments(text: str) -> bool:
    return bool(re.search(r"(<!--.*?-->|#.*TODO|#.*NOTE|#.*FIXME)", text, re.DOTALL))


def _has_usage_section(text: str) -> bool:
    return bool(re.search(r"(?i)^#{1,6}\s*(usage|how\s+to|getting\s+started|quick\s+start)", text, re.MULTILINE))


def _has_pitfalls(text: str) -> bool:
    return bool(re.search(r"(?i)(pitfall|caveat|warning|caution|danger|注意|警告|坑)", text))


def _score_structure(text: str) -> tuple[int, list[str]]:
    score = 0
    details: list[str] = []

    if _has_frontmatter(text):
        score += 10
        details.append("✓ frontmatter present")
    else:
        details.append("✗ missing frontmatter")

    section_count = _count_sections(text)
    if section_count >= 3:
        score += 10
        details.append(f"✓ {section_count} sections")
    elif section_count >= 1:
        score += 5
        details.append(f"△ only {section_count} section(s)")
    else:
        details.append("✗ no sections")

    example_count = _count_examples(text)
    if example_count >= 2:
        score += 10
        details.append(f"✓ {example_count} examples")
    elif example_count >= 1:
        score += 5
        details.append(f"△ only {example_count} example(s)")
    else:
        details.append("✗ no examples")

    return score, details


def _score_completeness(text: str) -> tuple[int, list[str]]:
    score = 0
    details: list[str] = []

    desc_len = len(text.strip())
    if desc_len >= 500:
        score += 10
        details.append(f"✓ substantial content ({desc_len} chars)")
    elif desc_len >= 200:
        score += 5
        details.append(f"△ moderate content ({desc_len} chars)")
    else:
        details.append(f"✗ too short ({desc_len} chars)")

    code_count = _count_code_blocks(text)
    if code_count >= 3:
        score += 8
        details.append(f"✓ {code_count} code blocks")
    elif code_count >= 1:
        score += 4
        details.append(f"△ {code_count} code block(s)")
    else:
        details.append("✗ no code blocks")

    table_count = _count_tables(text)
    if table_count >= 1:
        score += 7
        details.append(f"✓ {table_count} table(s)")
    else:
        details.append("✗ no tables")

    return score, details


def _score_documentation(text: str) -> tuple[int, list[str]]:
    score = 0
    details: list[str] = []

    if _has_comments(text):
        score += 8
        details.append("✓ has comments/annotations")
    else:
        details.append("✗ no comments/annotations")

    if _has_usage_section(text):
        score += 9
        details.append("✓ usage section found")
    else:
        details.append("✗ no usage section")

    if _has_pitfalls(text):
        score += 8
        details.append("✓ pitfalls/warnings documented")
    else:
        details.append("✗ no pitfalls documented")

    return score, details


def _score_freshness(text: str) -> tuple[int, list[str]]:
    score = 0
    details: list[str] = []

    version_match = re.search(r"(?i)version[\"']?\s*[:=]\s*[\"']?(\d+\.\d+)", text)
    if version_match:
        score += 10
        details.append(f"✓ version declared: {version_match.group(1)}")
    else:
        details.append("✗ no version found")

    date_match = re.search(r"(?i)(updated?|date|last.?modified)[\"']?\s*[:=]\s*[\"']?(\d{4}[-/]\d{2})", text)
    if date_match:
        score += 10
        details.append(f"✓ dated: {date_match.group(2)}")
    else:
        details.append("✗ no date found")

    return score, details


def score_skill(file_path: str | Path) -> dict:
    """Score a SKILL.md file and return structured results."""
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {path}", "total": 0}

    text = path.read_text(encoding="utf-8")

    s_score, s_details = _score_structure(text)
    c_score, c_details = _score_completeness(text)
    d_score, d_details = _score_documentation(text)
    f_score, f_details = _score_freshness(text)

    total = s_score + c_score + d_score + f_score

    return {
        "file": str(path),
        "total": total,
        "breakdown": {
            "structure": {"score": s_score, "max": 30, "details": s_details},
            "completeness": {"score": c_score, "max": 25, "details": c_details},
            "documentation": {"score": d_score, "max": 25, "details": d_details},
            "freshness": {"score": f_score, "max": 20, "details": f_details},
        },
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python quality_scorer.py <path/to/SKILL.md>", file=sys.stderr)
        sys.exit(1)

    result = score_skill(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
