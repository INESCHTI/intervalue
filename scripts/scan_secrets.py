"""Lightweight secret scanner for local commits.

This is not a replacement for enterprise secret scanning, but it catches the credential
shapes that have appeared in this project: GitHub tokens, OpenAI-style keys, SMTP/Gmail app
password assignments, private keys, and high-entropy app-password groups.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKIP_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    "dist",
    "playwright-report",
    "test-results",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{30,}")),
    ("OpenAI API key", re.compile(r"sk-[A-Za-z0-9_-]{32,}")),
    ("Private key", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----")),
    (
        "SMTP/Gmail password assignment",
        re.compile(
            r"(?i)\b(?:SMTP_PASSWORD|GMAIL_PASSWORD|APP_PASSWORD|API_KEY|SECRET_KEY|ACCESS_TOKEN|AUTH_TOKEN)\s*=\s*['\"]?[^'\"\s#]{12,}"
        ),
    ),
    (
        "Gmail app password groups",
        re.compile(r"\b[a-z]{4}\s+[a-z]{4}\s+[a-z]{4}\s+[a-z]{4}\b", re.IGNORECASE),
    ),
]
PLACEHOLDER_RE = re.compile(
    r"(?i)(changeme|change-me|replace-with|your-|example|dummy|placeholder|ollama|local)"
)
APP_PASSWORD_FILE_RE = re.compile(r"(^|[\\/])(\.env|.*\.env|.*\.local|.*\.secret|.*\.secrets)$", re.I)


def should_scan(path: Path) -> bool:
    if any(part in SKIP_PARTS for part in path.parts):
        return False
    if path.is_dir():
        return False
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf"}:
        return False
    return True


def scan_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    findings: list[str] = []
    for name, pattern in PATTERNS:
        if name == "Gmail app password groups" and not APP_PASSWORD_FILE_RE.search(str(path)):
            continue
        for match in pattern.finditer(text):
            snippet = match.group(0)
            line_start = text.rfind("\n", 0, match.start()) + 1
            if text[line_start:match.start()].lstrip().startswith("#"):
                continue
            if PLACEHOLDER_RE.search(snippet):
                continue
            line = text.count("\n", 0, match.start()) + 1
            findings.append(f"{path}:{line}: possible {name}")
    return findings


def main(argv: list[str]) -> int:
    paths = [Path(arg) for arg in argv] if argv else [Path(".")]
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(child for child in path.rglob("*") if should_scan(child))
        elif should_scan(path):
            files.append(path)

    findings = [finding for file in files for finding in scan_file(file)]
    if findings:
        print("Secret scan failed. Review or remove these values:")
        print("\n".join(findings))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
