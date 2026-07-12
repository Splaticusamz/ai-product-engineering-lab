#!/usr/bin/env python3
"""Validate reusable pattern notes for public-lab quality.

Pattern notes should be more than prose: each one needs a clear trigger, a
repeatable structure, and enough concrete detail that another builder can apply
it without reading the original project context.
"""

from __future__ import annotations

import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS_DIR = ROOT / "patterns"
FORBIDDEN_PLACEHOLDERS = (
    "todo",
    "tbd",
    "lorem ipsum",
    "coming soon",
    "placeholder",
)
REUSABLE_STRUCTURE_HEADINGS = {
    "acceptance criteria",
    "anti-patterns",
    "cheap validators that pay off",
    "good default ux",
    "required fields",
    "review states",
}


@dataclass(frozen=True)
class Finding:
    path: Path
    message: str

    def format(self) -> str:
        return f"{self.path.relative_to(ROOT)}: {self.message}"


def markdown_headings(text: str) -> list[str]:
    headings: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            headings.append(match.group(1).strip())
    return headings


def first_nonblank_lines(text: str, limit: int = 5) -> list[str]:
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            lines.append(stripped)
        if len(lines) >= limit:
            break
    return lines


def slugify(value: str) -> str:
    """Return the filename-style slug used by pattern notes."""

    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return re.sub(r"-+", "-", slug)


def validate_pattern(path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    headings = markdown_headings(text)
    normalized_headings = {heading.lower() for heading in headings}
    intro = "\n".join(first_nonblank_lines(text))
    findings: list[Finding] = []

    if not headings or not text.lstrip().startswith("# "):
        findings.append(Finding(path, "must start with a top-level markdown heading"))
    else:
        title_slug = slugify(headings[0])
        file_slug = path.stem.lower()
        if title_slug != file_slug:
            findings.append(
                Finding(
                    path,
                    f"top-level heading slug {title_slug!r} should match filename slug {file_slug!r}",
                )
            )

    if not re.search(r"\buse (this|when)\b", intro, re.IGNORECASE):
        findings.append(Finding(path, "opening lines should state when to use the pattern"))

    if not (normalized_headings & REUSABLE_STRUCTURE_HEADINGS):
        expected = ", ".join(sorted(REUSABLE_STRUCTURE_HEADINGS))
        findings.append(Finding(path, f"missing reusable structure heading; expected one of: {expected}"))

    bullet_or_table_rows = [
        line
        for line in text.splitlines()
        if re.match(r"^\s*(- |\d+\. |\| .+ \|)", line)
    ]
    if len(bullet_or_table_rows) < 3:
        findings.append(Finding(path, "needs at least three concrete bullets, steps, or table rows"))

    for marker in FORBIDDEN_PLACEHOLDERS:
        if re.search(rf"\b{re.escape(marker)}\b", lowered):
            findings.append(Finding(path, f"contains placeholder marker: {marker!r}"))

    return findings


def pattern_files() -> list[Path]:
    if not PATTERNS_DIR.exists():
        return []
    return sorted(PATTERNS_DIR.glob("*.md"))


def top_level_title(path: Path) -> str | None:
    headings = markdown_headings(path.read_text(encoding="utf-8"))
    return headings[0] if headings else None


def validate_collection(paths: list[Path]) -> list[Finding]:
    """Catch cross-file drift that single-note checks cannot see."""

    findings: list[Finding] = []
    seen_titles: dict[str, Path] = {}
    for path in paths:
        title = top_level_title(path)
        if not title:
            continue
        title_key = slugify(title)
        previous = seen_titles.get(title_key)
        if previous is not None:
            findings.append(
                Finding(
                    path,
                    f"duplicates top-level heading from {previous.relative_to(ROOT)}",
                )
            )
        else:
            seen_titles[title_key] = path
    return findings


def validate_paths(paths: list[Path], collection_paths: list[Path] | None = None) -> list[Finding]:
    """Validate selected notes without losing collection-level checks.

    A targeted invocation still needs the full collection for duplicate-title
    detection. Otherwise a new note can pass alone and fail only in a later
    full-repository validation.
    """

    findings: list[Finding] = []
    for path in paths:
        findings.extend(validate_pattern(path))
    findings.extend(validate_collection(collection_paths or paths))
    return findings


def run_self_test() -> int:
    body = (
        "# Shared Pattern\n\n"
        "Use this when validating targeted pattern notes.\n\n"
        "## Acceptance criteria\n\n"
        "- Has a trigger.\n"
        "- Has concrete structure.\n"
        "- Has a collection-unique title.\n"
    )

    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        base = Path(tmp)
        first = base / "first" / "shared-pattern.md"
        second = base / "second" / "shared-pattern.md"
        first.parent.mkdir()
        second.parent.mkdir()
        first.write_text(body, encoding="utf-8")
        second.write_text(body, encoding="utf-8")

        findings = validate_paths([second], [first, second])

    duplicate_findings = [
        finding for finding in findings if "duplicates top-level heading" in finding.message
    ]
    if len(duplicate_findings) != 1:
        print(
            "Pattern note validator self-test failed: targeted validation did not "
            "detect the collection duplicate."
        )
        return 1

    print("Pattern note validator self-test passed: targeted validation checks collection uniqueness.")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if "--self-test" in args:
        if args != ["--self-test"]:
            print("--self-test cannot be combined with pattern paths.")
            return 2
        return run_self_test()

    paths = [ROOT / arg for arg in args] if args else pattern_files()
    paths = [path for path in paths if path.suffix == ".md" and "patterns" in path.parts]
    collection_paths = pattern_files() if args else paths
    findings = validate_paths(paths, collection_paths)

    if findings:
        print("Pattern note validation failed:")
        for finding in findings:
            print(f"- {finding.format()}")
        return 1

    print(f"Validated {len(paths)} pattern markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
