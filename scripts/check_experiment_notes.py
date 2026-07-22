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
SHELL_FENCE_LANGUAGES = {"bash", "sh", "shell", "zsh"}
RUNNABLE_SHELL_COMMAND_RE = re.compile(
    r"^\s*(?:\$\s*)?(?:[A-Za-z_][A-Za-z0-9_]*=\S+\s+)*"
    r"(?:python(?:3(?:\.\d+)?)?|pytest|uv|pip3?|npm|npx|pnpm|yarn|bun|node|deno|"
    r"curl|wget|git|gh|make|docker|podman|go|cargo|rustc|java|mvn|gradle|dotnet|"
    r"ruby|bundle|php|composer|bash|sh|zsh)\b",
    re.IGNORECASE,
)


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


def shell_blocks(text: str) -> list[tuple[int, list[str]]]:
    """Return opening line numbers and bodies for common fenced shell examples."""

    blocks: list[tuple[int, list[str]]] = []
    fence_char: str | None = None
    fence_length = 0
    opening_line = 0
    is_shell = False
    body: list[str] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        match = FENCE_RE.match(line)
        if fence_char is None:
            if not match:
                continue
            marker, suffix = match.groups()
            fence_char = marker[0]
            fence_length = len(marker)
            opening_line = line_number
            language = suffix.strip().split(maxsplit=1)[0].lower() if suffix.strip() else ""
            is_shell = language in SHELL_FENCE_LANGUAGES
            body = []
            continue

        if match:
            marker, suffix = match.groups()
            if marker[0] == fence_char and len(marker) >= fence_length and not suffix.strip():
                if is_shell:
                    blocks.append((opening_line, body))
                fence_char = None
                fence_length = 0
                opening_line = 0
                is_shell = False
                body = []
                continue

        if is_shell:
            body.append(line)

    return blocks


def has_runnable_shell_command(lines: list[str]) -> bool:
    """Reject empty/comment-only blocks and prose that only names a tool elsewhere."""

    return any(
        RUNNABLE_SHELL_COMMAND_RE.match(line)
        for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    )


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

    for opening_line, lines in shell_blocks(text):
        if not has_runnable_shell_command(lines):
            findings.append(
                Finding(
                    path,
                    f"shell block opened at line {opening_line} does not include a runnable command family",
                )
            )

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
            "```markdown\n## Question\n## Hypothesis\n## Results\n```\n\n"
            "```bash\npython3 scripts/check_experiment_notes.py --self-test\n```\n",
            [],
        ),
        "comment-only-bash": (
            "# Comment-only Bash Block\n\n"
            "## Question\n\nCan a Python experiment note pass with a non-runnable shell example?\n\n"
            "## Hypothesis\n\nThe validator should reject comment-only Bash blocks.\n\n"
            "## Results\n\nThe fixture keeps command-family words outside the fenced block.\n\n"
            "```bash\n# install dependencies before running the example\n```\n",
            ["shell block opened at line 15 does not include a runnable command family"],
        ),
        "comment-only-sh": (
            "# Comment-only Sh Block\n\n"
            "## Question\n\nCan an experiment pass with a non-runnable sh example?\n\n"
            "## Hypothesis\n\nThe validator should inspect common shell fence aliases.\n\n"
            "## Results\n\nThe fixture demonstrates parity between Bash and sh fences.\n\n"
            "```sh\n# no runnable command\n```\n",
            ["shell block opened at line 15 does not include a runnable command family"],
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
        "Experiment note validator self-test passed: fenced-only headings and comment-only shell blocks rejected "
        f"while valid structure was accepted across {len(fixtures)} fixtures."
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
