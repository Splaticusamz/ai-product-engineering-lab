#!/usr/bin/env python3
"""Validate experiment notes for reusable public-lab structure.

The check is intentionally small: experiment READMEs should state a question,
hypothesis, and a reusable outcome surface so they read like reproducible product
engineering notes instead of loose progress logs.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS_DIR = ROOT / "experiments"
REQUIRED_HEADINGS = ("question", "hypothesis")
OUTCOME_HEADINGS = ("run", "takeaway", "contribution quality bar", "results")
FORBIDDEN_PLACEHOLDERS = (
    "todo",
    "tbd",
    "lorem ipsum",
    "coming soon",
    "placeholder",
)


@dataclass(frozen=True)
class Finding:
    path: Path
    message: str

    def format(self) -> str:
        return f"{self.path.relative_to(ROOT)}: {self.message}"


def markdown_headings(text: str) -> set[str]:
    headings: set[str] = set()
    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            headings.add(match.group(1).strip().lower())
    return headings


def validate_note(path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8")
    headings = markdown_headings(text)
    lowered = text.lower()
    findings: list[Finding] = []

    for heading in REQUIRED_HEADINGS:
        if heading not in headings:
            findings.append(Finding(path, f"missing required heading: {heading!r}"))

    if not any(heading in headings for heading in OUTCOME_HEADINGS):
        options = ", ".join(OUTCOME_HEADINGS)
        findings.append(Finding(path, f"missing outcome heading; expected one of: {options}"))

    for marker in FORBIDDEN_PLACEHOLDERS:
        if re.search(rf"\b{re.escape(marker)}\b", lowered):
            findings.append(Finding(path, f"contains placeholder marker: {marker!r}"))

    if "```bash" in text and "python" not in lowered and "npm" not in lowered and "curl" not in lowered:
        findings.append(Finding(path, "bash block does not include a runnable command family"))

    return findings


def experiment_readmes() -> list[Path]:
    if not EXPERIMENTS_DIR.exists():
        return []
    return sorted(EXPERIMENTS_DIR.glob("*/README.md"))


def main() -> int:
    paths = [ROOT / arg for arg in sys.argv[1:]] if len(sys.argv) > 1 else experiment_readmes()
    paths = [path for path in paths if path.name == "README.md" and "experiments" in path.parts]

    findings: list[Finding] = []
    for path in paths:
        findings.extend(validate_note(path))

    if findings:
        print("Experiment note validation failed:")
        for finding in findings:
            print(f"- {finding.format()}")
        return 1

    print(f"Validated {len(paths)} experiment README files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
