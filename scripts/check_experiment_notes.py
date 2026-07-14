#!/usr/bin/env python3
"""Validate experiment notes for reusable public-lab structure.

The check is intentionally small: experiment READMEs should state a question,
hypothesis, and a reusable outcome surface so they read like reproducible product
engineering notes instead of loose progress logs.
"""

from __future__ import annotations

import re
import sys
import tempfile
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
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


@dataclass(frozen=True)
class Finding:
    path: Path
    message: str

    def format(self) -> str:
        return f"{self.path.relative_to(ROOT)}: {self.message}"


def lines_outside_fences(text: str) -> list[str]:
    """Return document lines without headings from fenced examples."""

    lines: list[str] = []
    fence_char: str | None = None
    fence_length = 0

    for line in text.splitlines():
        match = FENCE_RE.match(line)
        if fence_char is None:
            if match:
                marker = match.group(1)
                fence_char = marker[0]
                fence_length = len(marker)
                continue
            lines.append(line)
            continue

        if match:
            marker, suffix = match.groups()
            if marker[0] == fence_char and len(marker) >= fence_length and not suffix.strip():
                fence_char = None
                fence_length = 0

    return lines


def markdown_headings(lines: list[str]) -> set[str]:
    headings: set[str] = set()
    for line in lines:
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            headings.add(match.group(1).strip().lower())
    return headings


def validate_note(path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8")
    headings = markdown_headings(lines_outside_fences(text))
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


def run_self_test() -> int:
    fixtures = {
        "fenced-structure-only": (
            "# Fenced Structure Only\n\n"
            "This note puts required experiment structure only inside an example.\n\n"
            "```markdown\n"
            "## Question\n"
            "## Hypothesis\n"
            "## Results\n"
            "```\n",
            [
                "missing required heading: 'question'",
                "missing required heading: 'hypothesis'",
                "missing outcome heading; expected one of: run, takeaway, contribution quality bar, results",
            ],
        ),
        "valid-with-fenced-examples": (
            "# Valid Experiment\n\n"
            "## Question\n\nCan this validator distinguish examples from document structure?\n\n"
            "## Hypothesis\n\nOnly headings outside fences should satisfy required sections.\n\n"
            "## Results\n\nThe focused fixture defines the expected behavior.\n\n"
            "```markdown\n## Question\n## Hypothesis\n## Results\n```\n",
            [],
        ),
    }

    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        base = Path(tmp)
        for name, (text, expected) in fixtures.items():
            path = base / name / "README.md"
            path.parent.mkdir()
            path.write_text(text, encoding="utf-8")
            actual = [finding.message for finding in validate_note(path)]
            if actual != expected:
                print(
                    f"Experiment note validator self-test failed for {name}: "
                    f"expected {expected}, got {actual}"
                )
                return 1

    print(
        "Experiment note validator self-test passed: fenced-only headings rejected "
        f"and valid structure accepted across {len(fixtures)} fixtures."
    )
    return 0


def experiment_readmes() -> list[Path]:
    if not EXPERIMENTS_DIR.exists():
        return []
    return sorted(EXPERIMENTS_DIR.glob("*/README.md"))


def main() -> int:
    args = sys.argv[1:]
    if "--self-test" in args:
        if args != ["--self-test"]:
            print("--self-test cannot be combined with experiment paths.")
            return 2
        return run_self_test()

    paths = [ROOT / arg for arg in args] if args else experiment_readmes()
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
