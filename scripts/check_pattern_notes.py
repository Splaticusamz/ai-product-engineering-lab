#!/usr/bin/env python3
"""Validate reusable pattern notes for public-lab quality.

Pattern notes should be more than prose: each one needs a clear trigger, a
repeatable structure, and enough concrete detail that another builder can apply
it without reading the original project context.
"""

from __future__ import annotations

import re
import sys
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


def main() -> int:
    paths = [ROOT / arg for arg in sys.argv[1:]] if len(sys.argv) > 1 else pattern_files()
    paths = [path for path in paths if path.suffix == ".md" and "patterns" in path.parts]

    findings: list[Finding] = []
    for path in paths:
        findings.extend(validate_pattern(path))
    findings.extend(validate_collection(paths))

    if findings:
        print("Pattern note validation failed:")
        for finding in findings:
            print(f"- {finding.format()}")
        return 1

    print(f"Validated {len(paths)} pattern markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
