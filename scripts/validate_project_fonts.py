#!/usr/bin/env python3
"""Check actual PDF font embedding and optional LaTeX font diagnostics.

This does not establish whether font roles, glyph choices or typography match
the user's requested design. Those require separate source and visual checks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from inspect_build_log import font_log_findings


FONT_ROW = re.compile(
    r"^\s*(?P<name>\S+)\s+(?P<type>.+?)\s+(?P<encoding>\S+)\s+"
    r"(?P<embedded>yes|no)\s+(?P<subset>yes|no)\s+(?P<unicode>yes|no)\s+"
    r"(?P<object_id>\d+)\s+(?P<generation>\d+)\s*$",
    re.IGNORECASE,
)
HEADER = re.compile(r"^name\s+type\s+encoding\s+emb\s+sub\s+uni\s+object\s+ID\s*$")
LIMITATIONS = [
    "Embedding verifies that listed PDF font programs are included; it does not verify semantic font roles.",
    "Chinese body/theorem/emphasis fonts, math glyph choice, font licensing and original-figure fidelity require separate source and visual checks.",
    "Fonts used only as outlines or raster images are not listed by pdffonts; an empty listing is not accepted as a successful font check.",
]


def parse_pdffonts(text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse from the right-hand columns so types such as 'CID Type 0C (OT)' work."""
    fonts: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    header_seen = False
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        if HEADER.fullmatch(line.strip()):
            header_seen = True
            continue
        if re.fullmatch(r"\s*-+(?:\s+-+)*\s*", line):
            continue
        match = FONT_ROW.fullmatch(line)
        if not header_seen or match is None:
            findings.append({"category": "unrecognized_pdffonts_output", "line": line_no, "text": line})
            continue
        row = match.groupdict()
        fonts.append({
            "name": row["name"],
            "type": row["type"].strip(),
            "encoding": row["encoding"],
            "embedded": row["embedded"].lower() == "yes",
            "subset": row["subset"].lower() == "yes",
            "unicode_mapping": row["unicode"].lower() == "yes",
            "object_id": int(row["object_id"]),
            "generation": int(row["generation"]),
        })
    if not header_seen:
        findings.append({"category": "missing_pdffonts_header", "text": "pdffonts did not return its expected table header."})
    if not fonts:
        findings.append({"category": "no_fonts", "text": "No actual fonts were listed; fontless or image-only PDFs require separate review."})
    for font in fonts:
        if not font["embedded"]:
            findings.append({
                "category": "font_not_embedded",
                "font": font["name"],
                "object_id": font["object_id"],
                "text": f"PDF font {font['name']} is not embedded.",
            })
    return fonts, findings


def validate_project_fonts(pdf: Path, log: Path | None = None) -> dict[str, Any]:
    fonts: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    tool: dict[str, Any] = {"command": ["pdffonts", str(pdf.resolve())], "returncode": None, "stderr": ""}
    pdf_sha256 = None
    if not pdf.is_file():
        findings.append({"category": "pdf_not_found", "text": f"PDF not found: {pdf}"})
    else:
        pdf_sha256 = hashlib.sha256(pdf.read_bytes()).hexdigest()
        try:
            result = subprocess.run(tool["command"], capture_output=True, text=True, check=False, timeout=30)
            tool.update(returncode=result.returncode, stderr=result.stderr.strip())
            if result.returncode:
                findings.append({"category": "pdffonts_failed", "text": result.stderr.strip() or f"pdffonts exited with status {result.returncode}."})
            else:
                fonts, parsed_findings = parse_pdffonts(result.stdout)
                findings.extend(parsed_findings)
        except FileNotFoundError:
            findings.append({"category": "pdffonts_unavailable", "text": "pdffonts is required; install the Poppler tools and rerun this check."})
        except subprocess.TimeoutExpired:
            findings.append({"category": "pdffonts_timeout", "text": "pdffonts exceeded the 30-second timeout."})

    log_report: dict[str, Any] = {"checked": False, "path": str(log.resolve()) if log else None}
    if log is not None:
        if not log.is_file():
            findings.append({"category": "log_not_found", "text": f"LaTeX log not found: {log}"})
        else:
            log_report["checked"] = True
            for finding in font_log_findings(log.read_text(encoding="utf-8", errors="replace")):
                findings.append({"source": "latex_log", **finding})

    return {
        "status": "failed" if findings else "passed",
        "pdf": str(pdf.resolve()),
        "pdf_sha256": pdf_sha256,
        "total_font_count": len(fonts),
        "embedded_font_count": sum(font["embedded"] for font in fonts),
        "fonts": fonts,
        "log": log_report,
        "pdffonts": tool,
        "blocking_findings": findings,
        "limitations": LIMITATIONS + ([] if log_report["checked"] else ["LaTeX font diagnostics were not checked; supply --log to check missing glyphs and font substitutions."]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="The explicit PDF to inspect; no main-file discovery is performed.")
    parser.add_argument("--log", type=Path, help="Optional final LaTeX log to check for missing glyphs and font substitution.")
    parser.add_argument("--report", type=Path, help="Also save the JSON report at this path.")
    args = parser.parse_args(argv)
    report = validate_project_fonts(args.pdf, args.log)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
