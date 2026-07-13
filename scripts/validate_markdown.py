#!/usr/bin/env python3
"""Validate basic repository markdown structure.

The checks stay intentionally small, but they distinguish document structure from
examples inside fenced code blocks so malformed generated notes cannot pass by
accident.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORE_DIRS = {".git", "node_modules", ".next", "dist", "build"}
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*.md"):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def structural_lines(text: str) -> tuple[list[str], str | None]:
    """Return lines outside fenced code and any unclosed opening fence."""

    lines: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    opening_fence: str | None = None

    for line_number, line in enumerate(text.splitlines(), start=1):
        match = FENCE_RE.match(line)
        if fence_char is None:
            if match:
                marker = match.group(1)
                fence_char = marker[0]
                fence_length = len(marker)
                opening_fence = f"line {line_number} ({marker})"
                continue
            lines.append(line)
            continue

        if match:
            marker, suffix = match.groups()
            if marker[0] == fence_char and len(marker) >= fence_length and not suffix.strip():
                fence_char = None
                fence_length = 0
                opening_fence = None

    return lines, opening_fence


def validate_text(text: str) -> list[str]:
    failures: list[str] = []
    stripped = text.strip()
    if len(stripped) < 80:
        failures.append("too short")

    lines, unclosed_fence = structural_lines(text)
    first_nonblank = next((line for line in lines if line.strip()), "")
    if not re.match(r"^#\s+\S", first_nonblank):
        failures.append("first nonblank line must be a top-level heading")

    top_level_headings = [line for line in lines if re.match(r"^#\s+\S", line)]
    if len(top_level_headings) != 1:
        failures.append(
            f"expected exactly one top-level heading outside code fences; found {len(top_level_headings)}"
        )

    if unclosed_fence:
        failures.append(f"unclosed code fence opened at {unclosed_fence}")

    return failures


def validate_files(paths: list[Path]) -> list[str]:
    failures: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        for message in validate_text(text):
            failures.append(f"{rel}: {message}")
    return failures


def run_self_test() -> int:
    fixtures = {
        "valid": (
            "# Valid note\n\n"
            "This reusable note has enough concrete text to exceed the minimum length safely.\n\n"
            "```text\n# Example output, not a document heading\n```\n",
            [],
        ),
        "code-heading-only": (
            "This generated note has no title, but includes enough body text to exceed the minimum.\n\n"
            "```text\n# Not a document heading\n```\n",
            [
                "first nonblank line must be a top-level heading",
                "expected exactly one top-level heading outside code fences; found 0",
            ],
        ),
        "duplicate-title": (
            "# First title\n\nThis note has enough explanatory content to exceed the minimum length.\n\n"
            "# Second title\n",
            ["expected exactly one top-level heading outside code fences; found 2"],
        ),
        "unclosed-fence": (
            "# Unclosed example\n\nThis note has enough explanatory content to exceed the minimum length.\n\n"
            "```python\nprint('still open')\n",
            ["unclosed code fence opened at line 5 (```)"],
        ),
    }

    for name, (text, expected) in fixtures.items():
        actual = validate_text(text)
        if actual != expected:
            print(
                f"Markdown validator self-test failed for {name}: "
                f"expected {expected}, got {actual}"
            )
            return 1

    print(f"Markdown validator self-test passed for {len(fixtures)} fixtures.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate repository markdown structure.")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run focused fixtures for heading and code-fence handling.",
    )
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    paths = iter_markdown_files()
    failures = validate_files(paths)
    if failures:
        print("Markdown validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Validated {len(paths)} markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
