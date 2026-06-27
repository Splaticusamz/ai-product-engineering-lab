#!/usr/bin/env python3
"""Validate that repository markdown files are non-empty and have headings.

This is intentionally lightweight. It catches obvious automation failures without
pretending to be a full content-quality judge.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
IGNORE_DIRS = {".git", "node_modules", ".next", "dist", "build"}


def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*.md"):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def main() -> int:
    failures: list[str] = []
    for path in iter_markdown_files():
        text = path.read_text(encoding="utf-8").strip()
        rel = path.relative_to(ROOT)
        if len(text) < 80:
            failures.append(f"{rel}: too short")
        if not any(line.startswith("#") for line in text.splitlines()):
            failures.append(f"{rel}: missing markdown heading")

    if failures:
        print("Markdown validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Validated {len(iter_markdown_files())} markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
