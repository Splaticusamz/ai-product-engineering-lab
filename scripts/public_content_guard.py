#!/usr/bin/env python3
"""Scan public repo artifacts for obvious private-content leaks.

The goal is not perfect secret detection. It is a lightweight pre-commit guard for
this lab: catch the kinds of material that should never be included in public AI
product-engineering notes, fixtures, or scripts.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
MAX_TEXT_BYTES = 1_000_000

EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".next",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
}

TEXT_SUFFIXES = {
    "",
    ".css",
    ".csv",
    ".env",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]
    guidance: str


RULES = (
    Rule(
        "private-key-block",
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        "Remove private key material and rotate the exposed key.",
    ),
    Rule(
        "github-token",
        re.compile(r"gh[pousr]_[A-Za-z0-9_]{30,}"),
        "Remove GitHub tokens from public artifacts and rotate the token.",
    ),
    Rule(
        "openai-key",
        re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{32,}"),
        "Remove model-provider API keys and rotate the credential.",
    ),
    Rule(
        "aws-access-key",
        re.compile(r"AKIA[0-9A-Z]{16}"),
        "Remove AWS access keys and rotate the IAM credential.",
    ),
    Rule(
        "slack-token",
        re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
        "Remove Slack tokens and rotate the app credential.",
    ),
    Rule(
        "discord-webhook",
        re.compile(r"https://discord(?:app)?\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+"),
        "Remove Discord webhook URLs and rotate the webhook.",
    ),
    Rule(
        "private-material-label",
        re.compile(
            r"\b(client secret|private client|job application|resume draft|discord transcript|do not publish)\b",
            re.IGNORECASE,
        ),
        "Public lab artifacts should not contain private client, application, or Discord material.",
    ),
)


SELF_ALLOWED_RULES = {"private-material-label"}


def tracked_files(root: Path) -> list[Path]:
    """Return git-tracked files when available; otherwise fall back to a tree walk."""

    try:
        output = subprocess.check_output(
            ["git", "ls-files"], cwd=root, text=True, stderr=subprocess.DEVNULL
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return [path for path in root.rglob("*") if path.is_file()]

    return [root / line for line in output.splitlines() if line.strip()]


def is_scannable(path: Path) -> bool:
    if any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts):
        return False
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return False
    try:
        return path.stat().st_size <= MAX_TEXT_BYTES
    except OSError:
        return False


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def scan(paths: Iterable[Path]) -> list[str]:
    findings: list[str] = []
    self_path = Path(__file__).resolve()
    for path in paths:
        if not is_scannable(path):
            continue
        text = read_text(path)
        if text is None:
            continue
        rel = path.relative_to(ROOT)
        for line_number, line in enumerate(text.splitlines(), start=1):
            for rule in RULES:
                if path.resolve() == self_path and rule.name in SELF_ALLOWED_RULES:
                    continue
                if rule.pattern.search(line):
                    findings.append(f"{rel}:{line_number}: {rule.name} — {rule.guidance}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan tracked public artifacts for obvious secrets and private-content labels."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional repo-relative paths to scan. Defaults to git-tracked files.",
    )
    args = parser.parse_args()

    paths = [ROOT / arg for arg in args.paths] if args.paths else tracked_files(ROOT)
    findings = scan(paths)

    if findings:
        print("Public content guard failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print(f"Public content guard passed for {len(paths)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
