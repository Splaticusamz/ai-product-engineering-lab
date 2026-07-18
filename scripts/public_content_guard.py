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


def candidate_files(root: Path) -> list[Path]:
    """Return tracked plus untracked public artifacts when git is available.

    A pre-commit guard that scans only tracked files can miss a newly generated
    note, fixture, or script before the first commit. Include untracked files that
    are not ignored so the guard covers the exact material likely to become public.
    """

    try:
        output = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return [path for path in root.rglob("*") if path.is_file()]

    return sorted({root / line for line in output.splitlines() if line.strip()})


def is_scannable(path: Path) -> bool:
    """Scan every publishable candidate instead of trusting filename suffixes.

    Generated credentials and exports often use uncommon extensions. Decode and
    size checks in ``scan`` fail closed when a candidate cannot be inspected.
    """

    if any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts):
        return False
    return True


def read_text(path: Path) -> tuple[str | None, bool]:
    """Read UTF-8 text and report decode failures instead of silently skipping them."""

    try:
        return path.read_text(encoding="utf-8"), False
    except UnicodeDecodeError:
        return None, True


def scan(paths: Iterable[Path]) -> list[str]:
    findings: list[str] = []
    self_path = Path(__file__).resolve()
    for path in paths:
        if not is_scannable(path):
            continue
        rel = path.relative_to(ROOT)
        try:
            size = path.stat().st_size
        except OSError as exc:
            findings.append(f"{rel}: unreadable-file — Could not inspect file metadata: {exc}")
            continue
        if size > MAX_TEXT_BYTES:
            findings.append(
                f"{rel}: oversized-text-file — File is {size} bytes; "
                f"review it manually or keep it below the {MAX_TEXT_BYTES}-byte scan limit."
            )
            continue
        text, decode_failed = read_text(path)
        if decode_failed:
            findings.append(
                f"{rel}: non-utf8-text-file — File uses invalid UTF-8; "
                "convert it to UTF-8 or inspect it manually before publishing."
            )
            continue
        assert text is not None
        for line_number, line in enumerate(text.splitlines(), start=1):
            for rule in RULES:
                if path.resolve() == self_path and rule.name in SELF_ALLOWED_RULES:
                    continue
                if rule.pattern.search(line):
                    findings.append(f"{rel}:{line_number}: {rule.name} — {rule.guidance}")
    return findings


def run_untracked_probe() -> int:
    """Verify untracked secret-bearing formats are scanned without false alarms.

    This guards against the most dangerous public-repo failure mode for this lab:
    an automation run creates a fresh note, config, or credential file that is never
    scanned because the guard only looked at tracked files or familiar source suffixes.
    """

    dotenv_probe = ROOT / ".env.local"
    private_key_probe = ROOT / ".public-content-guard-private-key.pem"
    token_probe = ROOT / ".public-content-guard-token.ini"
    arbitrary_suffix_probe = ROOT / ".public-content-guard-token.xml"
    safe_probe = ROOT / ".public-content-guard-safe.conf"
    oversized_probe = ROOT / ".public-content-guard-oversized.txt"
    invalid_utf8_probe = ROOT / ".public-content-guard-invalid-utf8.txt"
    probes = (
        dotenv_probe,
        private_key_probe,
        token_probe,
        arbitrary_suffix_probe,
        safe_probe,
        oversized_probe,
        invalid_utf8_probe,
    )
    existing = [str(path.relative_to(ROOT)) for path in probes if path.exists()]
    if existing:
        print(f"Self-test refused to overwrite existing probes: {', '.join(existing)}")
        return 1

    fake_token = "ghp_" + ("A" * 36)
    fake_openai_key = "sk-proj-" + ("A" * 40)
    dotenv_probe.write_text(
        "# temporary dotenv guard self-test file\n"
        f"OPENAI_API_KEY={fake_openai_key}\n",
        encoding="utf-8",
    )
    private_key_probe.write_text(
        "temporary PEM guard self-test file\n"
        "-----BEGIN " + "PRIVATE KEY-----\nnot-a-real-key\n-----END PRIVATE KEY-----\n",
        encoding="utf-8",
    )
    token_probe.write_text(
        "[credentials]\n"
        f"token={fake_token}\n",
        encoding="utf-8",
    )
    arbitrary_suffix_probe.write_text(
        "<credentials>\n"
        f"  <token>{fake_token}</token>\n"
        "</credentials>\n",
        encoding="utf-8",
    )
    safe_probe.write_text(
        "mode=development\n"
        "retries=2\n",
        encoding="utf-8",
    )
    oversized_probe.write_bytes(b"A" * (MAX_TEXT_BYTES + 1))
    invalid_utf8_probe.write_bytes(b"public note prefix\xff\xfepayload")

    try:
        paths = candidate_files(ROOT)
        findings = scan(paths)
    finally:
        for probe in probes:
            probe.unlink(missing_ok=True)

    probe_names = {str(path.relative_to(ROOT)) for path in probes}
    probe_findings = [
        finding for finding in findings if finding.split(":", maxsplit=1)[0] in probe_names
    ]
    expected = [
        ".env.local:2: openai-key — "
        "Remove model-provider API keys and rotate the credential.",
        ".public-content-guard-invalid-utf8.txt: non-utf8-text-file — "
        "File uses invalid UTF-8; convert it to UTF-8 or inspect it manually before publishing.",
        ".public-content-guard-oversized.txt: oversized-text-file — "
        f"File is {MAX_TEXT_BYTES + 1} bytes; review it manually or keep it below the "
        f"{MAX_TEXT_BYTES}-byte scan limit.",
        ".public-content-guard-private-key.pem:2: private-key-block — "
        "Remove private key material and rotate the exposed key.",
        ".public-content-guard-token.ini:2: github-token — "
        "Remove GitHub tokens from public artifacts and rotate the token.",
        ".public-content-guard-token.xml:2: github-token — "
        "Remove GitHub tokens from public artifacts and rotate the token.",
    ]
    if probe_findings != expected:
        print(
            "Public content guard self-test failed: "
            f"expected {expected}, got {probe_findings}"
        )
        return 1

    print(
        "Public content guard self-test passed: detected dotenv, PEM, INI, and arbitrary-suffix secrets, "
        "rejected oversized and invalid-UTF-8 text artifacts, ignored a safe config, "
        f"and scanned {len(paths)} candidate files."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan tracked and untracked public artifacts for obvious secrets and private-content labels."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional repo-relative paths to scan. Defaults to git-tracked plus untracked non-ignored files.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Verify untracked credential/config formats are scanned without flagging a safe fixture.",
    )
    args = parser.parse_args()

    if args.self_test:
        if args.paths:
            parser.error("--self-test cannot be combined with explicit paths")
        return run_untracked_probe()

    paths = [ROOT / arg for arg in args.paths] if args.paths else candidate_files(ROOT)
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
