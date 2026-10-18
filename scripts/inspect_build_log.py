#!/usr/bin/env python3
"""Turn a final LaTeX log and PDF into a durable validation report."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


FAIL_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"^!",
        r"LaTeX Error",
        r"Package .* Error",
        r"Undefined control sequence",
        r"There were undefined references",
        r"There were undefined citations",
        r"Citation .* undefined",
        r"Reference .* undefined",
        r"multiply defined",
        r"destination with the same identifier",
        r"Overfull \\[hv]box",
        r"Rerun to get cross-references right",
    )
]


# NFSS/fontspec diagnostics often wrap the font name and the actual failure
# across several lines. Keep those checks shared with validate_project_fonts.
FONT_PATTERNS = [
    ("missing_glyph", re.compile(r"Missing character[^\n]*", re.IGNORECASE)),
    (
        "font_not_found",
        re.compile(
            r"\bfont\b.{0,250}?\b(?:cannot be found|not found|not loadable|could not be loaded)\b"
            r"|\bcannot find[^\n]{0,160}\bfont\b"
            r"|\b(?:could not|couldn't|cannot|can't)\s+load\s+(?:requested\s+)?font\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "font_substitution",
        re.compile(
            r"\bFont shape\b.{0,300}?\b(?:undefined|not available)\b"
            r"|\bSome font shapes were not available\b"
            r"|\b(?:Font|Size) substitutions?\b"
            r"|\bdefaults substituted\b"
            r"|\bUnknown CJK family\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
]


def font_log_findings(text: str) -> list[dict[str, Any]]:
    """Return source-located font failures, including wrapped diagnostics."""
    lines = text.splitlines()
    findings: dict[tuple[int, str], dict[str, Any]] = {}
    for category, pattern in FONT_PATTERNS:
        for match in pattern.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            end_line = text.count("\n", 0, match.end()) + 1
            findings[(line_no, category)] = {
                "line": line_no,
                "end_line": end_line,
                "category": category,
                "text": " ".join(line.strip() for line in lines[line_no - 1:end_line]),
            }
    return sorted(findings.values(), key=lambda finding: (finding["line"], finding["category"]))


def inspect_log(text: str) -> list[dict[str, Any]]:
    findings = font_log_findings(text)
    font_lines = {finding["line"] for finding in findings}
    for line_no, line in enumerate(text.splitlines(), start=1):
        if line_no not in font_lines and any(pattern.search(line) for pattern in FAIL_PATTERNS):
            findings.append({"line": line_no, "text": line.strip()})
    return sorted(findings, key=lambda finding: finding["line"])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def page_count(pdf: Path) -> int | None:
    try:
        result = subprocess.run(
            ["pdfinfo", str(pdf)], check=True, capture_output=True, text=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    if not args.log.is_file():
        raise SystemExit(f"LaTeX log not found: {args.log}")
    if not args.pdf.is_file():
        raise SystemExit(f"PDF not found: {args.pdf}")

    findings = inspect_log(args.log.read_text(encoding="utf-8", errors="replace"))

    report = {
        "status": "failed" if findings else "passed",
        "pdf": str(args.pdf.resolve()),
        "pdf_pages": page_count(args.pdf),
        "pdf_size_bytes": args.pdf.stat().st_size,
        "pdf_sha256": sha256(args.pdf),
        "log": str(args.log.resolve()),
        "blocking_findings": findings,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if findings:
        for finding in findings:
            print(f"ERROR: log line {finding['line']}: {finding['text']}", file=sys.stderr)
        print(f"Validation report: {args.report}", file=sys.stderr)
        return 1
    print(
        f"Build log audit passed: {report['pdf_pages']} pages, "
        f"SHA-256 {report['pdf_sha256']}"
    )
    print(f"Validation report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
