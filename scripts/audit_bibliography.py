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
BIB_RANGE_RE = re.compile(r"\\begin\s*\{(thebibliography|mybibliography)\}")
DEFINITION_RE = re.compile(
    r"\\(?P<command>newcommand|renewcommand|providecommand|DeclareRobustCommand|"
    r"newenvironment|renewenvironment|provideenvironment)\*?\s*"
)
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


def outside_definitions(text: str) -> str:
    """Mask ordinary macro/environment definitions before counting uses.

    This is a static source check, not TeX expansion. In particular, the
    thebibliography inside a mybibliography definition is not another use.
    """
    masked = list(text)

    def skip_space(position: int) -> int:
        while position < len(text) and text[position].isspace():
            position += 1
        return position

    def group_end(position: int, opening: str, closing: str) -> int | None:
        if position >= len(text) or text[position] != opening:
            return None
        depth = 0
        for index in range(position, len(text)):
            backslashes = 0
            cursor = index - 1
            while cursor >= 0 and text[cursor] == "\\":
                backslashes += 1
                cursor -= 1
            if backslashes % 2:
                continue
            if text[index] == opening:
                depth += 1
            elif text[index] == closing:
                depth -= 1
                if depth == 0:
                    return index + 1
        return None

    for match in DEFINITION_RE.finditer(text):
        position = match.end()
        end = group_end(position, "{", "}")
        if end is None:
            name = re.match(r"\\[A-Za-z@]+", text[position:])
            if name is None:
                continue
            end = position + name.end()
        position = skip_space(end)
        while position < len(text) and text[position] == "[":
            end = group_end(position, "[", "]")
            if end is None:
                break
            position = skip_space(end)
        body_count = 2 if match.group("command").endswith("environment") else 1
        for _ in range(body_count):
            end = group_end(position, "{", "}")
            if end is None:
                break
            position = skip_space(end)
        else:
            for index in range(match.start(), position):
                if masked[index] != "\n":
                    masked[index] = " "
    return "".join(masked)


def tex_graph(project: Path, main_tex: str, *, ignore_definitions: bool = False) -> list[Path]:
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
        if ignore_definitions:
            text = outside_definitions(text)
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
    bibliography_ranges: list[str] = []
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
        bibliography_ranges.extend(BIB_RANGE_RE.findall(outside_definitions(text)))
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
    required_toc_entries = len(bibliography_ranges) if bibliography_ranges else headings
    toc_count_basis = "bibliography ranges" if bibliography_ranges else "explicit headings"
    if args.require_toc_bibliographies and required_toc_entries != toc_entries:
        errors.append(
            f"bibliography scope/TOC mismatch: {required_toc_entries} {toc_count_basis}, "
            f"{toc_entries} TOC entries ({headings} explicit headings)"
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
        "bibliography_ranges": len(bibliography_ranges),
        "bibliography_range_environments": bibliography_ranges,
        "bibliography_toc_entries": toc_entries,
        "required_bibliography_toc_entries": required_toc_entries,
        "bibliography_toc_count_basis": toc_count_basis,
        "missing_keys": missing,
        "unused_keys": unused,
        "duplicate_bibitem_keys": duplicates,
        "numeric_only_keys": numeric_keys,
        "possible_hardcoded_citations": hardcoded,
        "errors": errors,
        "warnings": warnings,
        "limitations": [
            "Static bibliography-range and TOC counts do not establish rendered "
            "PDF titles or link destinations; TeX macro execution is not expanded."
        ],
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
        f"{report['bibliography_ranges']} bibliography ranges, "
        f"{report['bibliography_headings']} explicit bibliography headings"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
