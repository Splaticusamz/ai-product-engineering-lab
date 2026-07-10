#!/usr/bin/env python3
"""Score agent outputs with a small product-usefulness rubric.

The scorer is deliberately transparent. It is meant for lightweight regression
checks in AI product workflows, not as an objective quality oracle.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterable

GROUNDING_MARKERS = (
    "http://",
    "https://",
    "app/",
    "scripts/",
    "src/",
    "curl",
    "npm run",
    "pytest",
    "exit 0",
    "status 200",
    "->",
)
ACTION_MARKERS = ("done", "next", "apply", "run", "send", "deploy", "commit", "fix", "create")
SAFETY_MARKERS = ("draft", "approval", "irreversible", "public", "noindex", "safe", "blocked")
GENERIC_PHRASES = (
    "you should consider",
    "many opportunities",
    "keep trying",
    "it is important to",
    "there are several ways",
)


def contains_any(text: str, markers: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in markers)


def has_grounding(text: str) -> bool:
    """Return true only for concrete evidence markers, not bare confidence words."""

    return contains_any(text, GROUNDING_MARKERS) or bool(
        re.search(r"\b[a-z0-9_-]+\.(md|tsx|py|json)\b", text, re.I)
    )


def score_item(item: dict) -> dict:
    text = item.get("text", "")
    expected_shape = item.get("expected_shape", [])
    lowered = text.lower()

    criteria = {
        "grounding": has_grounding(text),
        "specificity": bool(re.search(r"[\w.-]+/[\w./-]+|https?://|\b[a-z0-9_-]+\.(md|tsx|py|json)\b", text, re.I))
        and not contains_any(text, GENERIC_PHRASES),
        "actionability": contains_any(text, ACTION_MARKERS),
        "safety": contains_any(text, SAFETY_MARKERS) or "public" not in lowered,
        "format": all(token.lower() in lowered for token in expected_shape),
    }
    score = sum(criteria.values())
    return {"id": item.get("id", "unknown"), "score": score, "max_score": len(criteria), "criteria": criteria}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: score_agent_output.py <outputs.json>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    items = json.loads(path.read_text(encoding="utf-8"))
    results = [score_item(item) for item in items]

    print(json.dumps(results, indent=2))

    # Fail only on severe quality collapse. Mixed fixtures can include weak examples.
    if not any(result["score"] >= 4 for result in results):
        print("No high-quality output found in fixture set.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
