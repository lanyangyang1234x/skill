#!/usr/bin/env python3
"""Initialize, validate, and audit a mathematical terminology ledger."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


COLUMNS = [
    "source_term",
    "chosen_zh",
    "field_context",
    "evidence_type",
    "evidence_title",
    "evidence_url_or_citation",
    "first_source_location",
    "status",
    "notes",
]
STATUSES = {"verified", "provisional", "user-supplied"}
AUDIT_SUFFIXES = {".md", ".markdown", ".tex"}
SKIP_DIRECTORIES = {".git", "assets", "fonts", "work"}


def initialize(path: Path) -> int:
    if path.exists():
        print(f"Ledger already exists; refusing to overwrite: {path}", file=sys.stderr)
        return 2
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, delimiter="\t").writerow(COLUMNS)
    print(f"Initialized terminology ledger: {path}")
    return 0


def read_ledger(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.is_file():
        return [], [f"ledger not found: {path}"]
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != COLUMNS:
            return [], ["invalid ledger columns; expected: " + "\t".join(COLUMNS)]
        return list(reader), []


def validate_rows(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    choices: dict[str, set[str]] = {}
    seen_exact: dict[tuple[str, str], int] = {}
    for number, row in enumerate(rows, start=2):
        for field in (
            "source_term",
            "chosen_zh",
            "evidence_type",
            "evidence_url_or_citation",
            "first_source_location",
            "status",
        ):
            if not (row.get(field) or "").strip():
                errors.append(f"row {number}: missing {field}")
        status = (row.get("status") or "").strip()
        if status and status not in STATUSES:
            errors.append(f"row {number}: invalid status {status!r}")
        source_term = (row.get("source_term") or "").strip().casefold()
        chosen_zh = (row.get("chosen_zh") or "").strip()
        if source_term:
            choices.setdefault(source_term, set()).add(chosen_zh)
            key = (source_term, chosen_zh)
            if key in seen_exact:
                errors.append(
                    f"row {number}: duplicate entry for {source_term!r} / {chosen_zh!r} "
                    f"(first seen on row {seen_exact[key]})"
                )
            else:
                seen_exact[key] = number

    for source_term, translations in choices.items():
        if len(translations) > 1:
            errors.append(f"conflicting translations for {source_term}: {sorted(translations)}")
    return errors


def validate(path: Path) -> tuple[int, list[dict[str, str]]]:
    rows, errors = read_ledger(path)
    errors.extend(validate_rows(rows))
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors), file=sys.stderr)
        return 1, rows
    print(f"Valid terminology ledger: {len(rows)} entries")
    return 0, rows


def expand_documents(values: list[Path]) -> list[Path]:
    documents: set[Path] = set()
    for value in values:
        path = value.expanduser().resolve()
        if path.is_file() and path.suffix.lower() in AUDIT_SUFFIXES:
            documents.add(path)
        elif path.is_dir():
            for candidate in path.rglob("*"):
                if not candidate.is_file() or candidate.suffix.lower() not in AUDIT_SUFFIXES:
                    continue
                relative_parts = candidate.relative_to(path).parts[:-1]
                if any(part.startswith(".") or part in SKIP_DIRECTORIES for part in relative_parts):
                    continue
                documents.add(candidate.resolve())
        else:
            raise ValueError(f"audit input is not a Markdown/TeX file or directory: {path}")
    return sorted(documents)


def prose_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".md", ".markdown"}:
        text = re.sub(r"```.*?```|~~~.*?~~~", lambda match: "\n" * match.group(0).count("\n"), text, flags=re.S)
        text = re.sub(r"`[^`\n]*`", "", text)
        text = text.replace("**", "").replace("__", "").replace("*", "").replace("_", "")
    else:
        text = re.sub(r"(?m)(?<!\\)%.*$", "", text)
        style = re.compile(r"\\(?:textit|emph|textbf|textsf|textrm|mathrm|mathbf)\s*\{([^{}]*)\}")
        while style.search(text):
            text = style.sub(r"\1", text)
    return text


def term_pattern(term: str) -> re.Pattern[str]:
    escaped = re.escape(term.strip())
    return re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", re.IGNORECASE)


def accepted_bilingual_pattern(chosen_zh: str, source_term: str) -> re.Pattern[str]:
    return re.compile(
        re.escape(chosen_zh.strip())
        + r"\s*[（(]\s*"
        + re.escape(source_term.strip())
        + r"\s*[）)]",
        re.IGNORECASE,
    )


def audit_controls(notes: str) -> tuple[bool, bool, int, list[str]]:
    normalized = notes.casefold()
    match = re.search(r"audit-allow-source\s*=\s*(\d+)", normalized)
    forbidden_match = re.search(r"audit-forbid\s*=\s*([^;]+)", notes, re.IGNORECASE)
    forbidden = (
        [item.strip() for item in forbidden_match.group(1).split("|") if item.strip()]
        if forbidden_match
        else []
    )
    return (
        "audit-ignore" in normalized,
        "audit-allow-all" in normalized,
        int(match.group(1)) if match else 0,
        forbidden,
    )


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def audit(path: Path, rows: list[dict[str, str]], inputs: list[Path]) -> int:
    try:
        documents = expand_documents(inputs)
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if not documents:
        print("ERROR: no Markdown or TeX documents found for terminology audit", file=sys.stderr)
        return 2

    contents = [(document, prose_text(document)) for document in documents]
    findings: list[str] = []
    checked = 0
    for row in rows:
        source_term = row["source_term"].strip()
        chosen_zh = row["chosen_zh"].strip()
        ignore, allow_all_source, allowance, forbidden_terms = audit_controls(row.get("notes", ""))
        if ignore or not source_term or source_term.casefold() == chosen_zh.casefold():
            continue
        checked += 1
        if not allow_all_source:
            source_re = term_pattern(source_term)
            bilingual_re = accepted_bilingual_pattern(chosen_zh, source_term)
            accepted_remaining = 1
            raw_occurrences: list[tuple[Path, str, int]] = []
            for document, text in contents:
                accepted_spans: list[tuple[int, int]] = []
                for match in bilingual_re.finditer(text):
                    if accepted_remaining:
                        accepted_spans.append(match.span())
                        accepted_remaining -= 1
                for match in source_re.finditer(text):
                    if any(start <= match.start() and match.end() <= end for start, end in accepted_spans):
                        continue
                    raw_occurrences.append((document, text, match.start()))

            unexpected = raw_occurrences[allowance:]
            for document, text, offset in unexpected:
                findings.append(
                    f"{document}:{line_number(text, offset)}: source term {source_term!r} remains; "
                    f"use {chosen_zh!r} or document an audit allowance in notes"
                )

        for forbidden in forbidden_terms:
            if forbidden.casefold() == chosen_zh.casefold():
                continue
            forbidden_re = term_pattern(forbidden)
            for document, text in contents:
                for match in forbidden_re.finditer(text):
                    findings.append(
                        f"{document}:{line_number(text, match.start())}: forbidden alternate "
                        f"{forbidden!r} remains for {source_term!r}; use {chosen_zh!r}"
                    )

    if findings:
        print("\n".join(f"ERROR: {finding}" for finding in findings), file=sys.stderr)
        return 1
    print(
        f"Terminology audit passed: {checked} ledger terms across {len(documents)} documents "
        f"(ledger: {path})"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Initialize, validate, or audit an evidence-backed terminology ledger."
    )
    parser.add_argument("ledger", type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--init", action="store_true")
    action.add_argument("--check", action="store_true")
    action.add_argument("--audit", nargs="+", type=Path, metavar="DOCUMENT_OR_DIR")
    args = parser.parse_args()
    path = args.ledger.expanduser().resolve()
    if args.init:
        return initialize(path)
    status, rows = validate(path)
    if status or args.check:
        return status
    return audit(path, rows, args.audit)


if __name__ == "__main__":
    raise SystemExit(main())
