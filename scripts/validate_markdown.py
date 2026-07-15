#!/usr/bin/env python3
"""Validate repository Markdown structure and local artifact links.

The checks stay intentionally small, but they distinguish document structure from
examples inside fenced code blocks and reject relative links that are missing or
escape the repository.
"""

from __future__ import annotations

import argparse
import re
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
IGNORE_DIRS = {".git", "node_modules", ".next", "dist", "build"}
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
INLINE_LINK_RE = re.compile(
    r"!?\[[^\]]*\]\(\s*(?:<([^>]+)>|((?:[^\s()]|\([^()]*\))+))"
)
REFERENCE_LINK_RE = re.compile(r"^ {0,3}\[[^\]]+\]:\s*(?:<([^>]+)>|([^\s]+))")


def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*.md"):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def numbered_structural_lines(text: str) -> tuple[list[tuple[int, str]], str | None]:
    """Return numbered lines outside fenced code and any unclosed opening fence."""

    lines: list[tuple[int, str]] = []
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
            lines.append((line_number, line))
            continue

        if match:
            marker, suffix = match.groups()
            if marker[0] == fence_char and len(marker) >= fence_length and not suffix.strip():
                fence_char = None
                fence_length = 0
                opening_fence = None

    return lines, opening_fence


def structural_lines(text: str) -> tuple[list[str], str | None]:
    """Return lines outside fenced code and any unclosed opening fence."""

    numbered_lines, opening_fence = numbered_structural_lines(text)
    return [line for _, line in numbered_lines], opening_fence


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


def validate_local_links(text: str, source_path: Path) -> list[str]:
    """Reject missing or repo-escaping relative links outside code fences."""

    failures: list[str] = []
    numbered_lines, _ = numbered_structural_lines(text)
    root = ROOT.resolve()

    for line_number, line in numbered_lines:
        matches = list(INLINE_LINK_RE.finditer(line))
        reference_match = REFERENCE_LINK_RE.match(line)
        if reference_match:
            matches.append(reference_match)

        for match in matches:
            target = next(group for group in match.groups() if group is not None)
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith(("#", "//", "/")) or not parsed.path:
                continue

            candidate = (source_path.parent / unquote(parsed.path)).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                failures.append(
                    f"line {line_number}: local link escapes repository: {target!r}"
                )
                continue

            if not candidate.exists():
                failures.append(
                    f"line {line_number}: local link target does not exist: {target!r}"
                )

    return failures


def validate_path(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return validate_text(text) + validate_local_links(text, path)


def validate_files(paths: list[Path]) -> list[str]:
    failures: list[str] = []
    for path in paths:
        rel = path.relative_to(ROOT)
        for message in validate_path(path):
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

    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        base = Path(tmp)
        target = base / "target.md"
        target.write_text("# Target\n\nA real target for relative-link validation.\n", encoding="utf-8")
        versioned_target = base / "target_(v2).md"
        versioned_target.write_text(
            "# Versioned target\n\nA target whose valid Markdown path contains parentheses.\n",
            encoding="utf-8",
        )

        valid = base / "valid-links.md"
        valid.write_text(
            "# Valid links\n\n"
            "This fixture links to real artifacts and ignores links shown only as examples.\n\n"
            "[real target](target.md)\n"
            "[versioned target](target_(v2).md)\n\n"
            "```markdown\n[example only](missing-example.md)\n```\n",
            encoding="utf-8",
        )
        broken = base / "broken-link.md"
        broken.write_text(
            "# Broken link\n\n"
            "This fixture is long enough and points to a local artifact that does not exist.\n\n"
            "[missing artifact](missing.md)\n",
            encoding="utf-8",
        )
        escaping = base / "escaping-link.md"
        escaping.write_text(
            "# Escaping link\n\n"
            "This fixture is long enough and points beyond the public repository boundary.\n\n"
            "[outside artifact](../../outside.md)\n",
            encoding="utf-8",
        )

        link_expectations = {
            "valid-links": (valid, []),
            "broken-link": (
                broken,
                ["line 5: local link target does not exist: 'missing.md'"],
            ),
            "escaping-link": (
                escaping,
                ["line 5: local link escapes repository: '../../outside.md'"],
            ),
        }
        for name, (path, expected) in link_expectations.items():
            actual = validate_path(path)
            if actual != expected:
                print(
                    f"Markdown validator self-test failed for {name}: "
                    f"expected {expected}, got {actual}"
                )
                return 1

    total_fixtures = len(fixtures) + len(link_expectations)
    print(
        f"Markdown validator self-test passed for {total_fixtures} fixtures, "
        "including fenced examples and local link targets."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate repository markdown structure.")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run focused fixtures for headings, code fences, and local links.",
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
