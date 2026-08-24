#!/usr/bin/env python3
"""Audit citation keys and chapter-local bibliography mechanics in a TeX graph."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


INPUT_RE = re.compile(r"\\(?:input|include)\s*\{([^}]+)\}")
CITE_RE = re.compile(
    r"\\(?P<command>(?:[A-Za-z]*cite)\*?)\s*(?:\[[^\]]*\]\s*){0,2}\{(?P<keys>[^}]*)\}"
)
BIBITEM_RE = re.compile(r"\\bibitem(?:\[[^\]]*\])?\s*\{([^}]+)\}")
BIB_HEADING_RE = re.compile(
    r"\\(?:part|chapter|section|subsection|subsubsection)\*?\s*\{参考文献\}"
)
TOC_BIB_RE = re.compile(r"\\addcontentsline\s*\{toc\}\s*\{[^}]+\}\s*\{参考文献\}")
HARDCODED_RE = re.compile(
    r"\b[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’.-]{2,}(?:\s+(?:and|和|与)\s+"
    r"[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’.-]{2,})?\s*\[(?:\d+[,-]?\s*)+\]"
)


def strip_comments(text: str) -> str:
    cleaned: list[str] = []
    for line in text.splitlines():
        index = 0
        while True:
            index = line.find("%", index)
            if index < 0:
                break
            backslashes = 0
            cursor = index - 1
            while cursor >= 0 and line[cursor] == "\\":
                backslashes += 1
                cursor -= 1
            if backslashes % 2 == 0:
                line = line[:index]
                break
            index += 1
        cleaned.append(line)
    return "\n".join(cleaned)


def tex_graph(project: Path, main_tex: str) -> list[Path]:
    root = project.resolve()
    start = (root / main_tex).resolve()
    if not start.is_file():
        raise SystemExit(f"Main TeX file not found: {start}")
    ordered: list[Path] = []
    visited: set[Path] = set()

    def visit(path: Path) -> None:
        path = path.resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise SystemExit(f"Refusing to audit TeX input outside project: {path}") from exc
        if path in visited:
            return
        if not path.is_file():
            raise SystemExit(f"Included TeX file not found: {path}")
        visited.add(path)
        ordered.append(path)
        text = strip_comments(path.read_text(encoding="utf-8"))
        for match in INPUT_RE.finditer(text):
            value = match.group(1).strip()
            child = path.parent / value
            if not child.suffix:
                child = child.with_suffix(".tex")
            visit(child)

    visit(start)
    return ordered


def audit(args: argparse.Namespace) -> tuple[dict[str, Any], list[str], list[str]]:
    project = args.project_dir.expanduser().resolve()
    files = tex_graph(project, args.main_tex)
    citation_keys: list[str] = []
    bibitem_keys: list[str] = []
    citation_commands = 0
    headings = 0
    toc_entries = 0
    hardcoded: list[str] = []

    for path in files:
        text = strip_comments(path.read_text(encoding="utf-8"))
        for match in CITE_RE.finditer(text):
            if match.group("command").lower().startswith("nocite"):
                continue
            citation_commands += 1
            citation_keys.extend(key.strip() for key in match.group("keys").split(",") if key.strip())
        bibitem_keys.extend(key.strip() for key in BIBITEM_RE.findall(text) if key.strip())
        headings += len(BIB_HEADING_RE.findall(text))
        toc_entries += len(TOC_BIB_RE.findall(text))
        for line_no, line in enumerate(text.splitlines(), start=1):
            if "\\cite" in line:
                continue
            for match in HARDCODED_RE.finditer(line):
                hardcoded.append(f"{path.relative_to(project)}:{line_no}: {match.group(0)}")

    cite_counts = Counter(citation_keys)
    bib_counts = Counter(bibitem_keys)
    missing = sorted(set(cite_counts) - set(bib_counts))
    unused = sorted(set(bib_counts) - set(cite_counts))
    duplicates = sorted(key for key, count in bib_counts.items() if count > 1)
    numeric_keys = sorted(key for key in bib_counts if key.isdigit())

    errors: list[str] = []
    warnings: list[str] = []
    if missing:
        errors.append("citation keys without bibitems: " + ", ".join(missing))
    if duplicates:
        errors.append("duplicate bibitem keys: " + ", ".join(duplicates))
    if args.fail_unused and unused:
        errors.append("unused bibitem keys: " + ", ".join(unused))
    elif unused:
        warnings.append("unused bibitem keys: " + ", ".join(unused))
    if numeric_keys:
        warnings.append("numeric-only bibliography keys reduce auditability: " + ", ".join(numeric_keys))
    if hardcoded:
        message = "possible author-name hard-coded citations: " + "; ".join(hardcoded)
        (errors if args.fail_hardcoded else warnings).append(message)
    if args.require_toc_bibliographies and headings != toc_entries:
        errors.append(
            f"bibliography heading/TOC mismatch: {headings} headings, {toc_entries} TOC entries"
        )

    report: dict[str, Any] = {
        "project": str(project),
        "main_tex": args.main_tex,
        "tex_files": [str(path.relative_to(project)) for path in files],
        "citation_commands": citation_commands,
        "citation_occurrences": len(citation_keys),
        "unique_citation_keys": len(cite_counts),
        "bibitems": len(bibitem_keys),
        "unique_bibitem_keys": len(bib_counts),
        "bibliography_headings": headings,
        "bibliography_toc_entries": toc_entries,
        "missing_keys": missing,
        "unused_keys": unused,
        "duplicate_bibitem_keys": duplicates,
        "numeric_only_keys": numeric_keys,
        "possible_hardcoded_citations": hardcoded,
        "errors": errors,
        "warnings": warnings,
    }
    return report, errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("main_tex")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--fail-unused", action="store_true")
    parser.add_argument("--fail-hardcoded", action="store_true")
    parser.add_argument("--require-toc-bibliographies", action="store_true")
    args = parser.parse_args()

    report, errors, warnings = audit(args)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print(
        "Bibliography audit: "
        f"{report['citation_commands']} cite commands, "
        f"{report['bibitems']} bibitems, "
        f"{report['bibliography_headings']} bibliography headings"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
