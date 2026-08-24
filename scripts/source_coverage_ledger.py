#!/usr/bin/env python3
"""Initialize and validate whole-source PDF page coverage ledgers."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Optional


FIELDS = [
    "pdf_page_start",
    "pdf_page_end",
    "source_id",
    "source_kind",
    "tex_file",
    "status",
    "notes",
]
STATUSES = {"pending", "drafted", "verified", "excluded"}


def initialize(path: Path) -> None:
    if path.exists() and path.stat().st_size:
        raise SystemExit(f"Refusing to overwrite nonempty ledger: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        csv.DictWriter(handle, fieldnames=FIELDS, dialect="excel-tab").writeheader()
    print(f"Initialized: {path}")


def validate(
    path: Path,
    first_page: Optional[int],
    last_page: Optional[int],
    max_verified_span: Optional[int],
) -> None:
    if not path.is_file():
        raise SystemExit(f"Ledger not found: {path}")
    if (first_page is None) != (last_page is None):
        raise SystemExit("--first-page and --last-page must be supplied together")
    if first_page is not None and first_page > last_page:
        raise SystemExit("--first-page must not exceed --last-page")

    errors: list[str] = []
    covered: set[int] = set()
    page_owners: dict[int, tuple[str, int]] = {}
    seen_ids: dict[str, int] = {}
    previous_start = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, dialect="excel-tab")
        if reader.fieldnames != FIELDS:
            raise SystemExit(
                "Unexpected ledger header. Expected: " + "\t".join(FIELDS)
            )
        rows = list(reader)

    if not rows:
        errors.append("ledger contains no source rows")

    for line_no, row in enumerate(rows, start=2):
        prefix = f"line {line_no}"
        try:
            start = int(row["pdf_page_start"])
            end = int(row["pdf_page_end"])
        except ValueError:
            errors.append(f"{prefix}: page bounds must be integers")
            continue
        if start < 1 or end < start:
            errors.append(f"{prefix}: invalid page range {start}-{end}")
        elif start < previous_start:
            errors.append(f"{prefix}: page ranges are out of source order")
        previous_start = max(previous_start, start)

        source_id = row["source_id"].strip()
        if not source_id:
            errors.append(f"{prefix}: source_id is required")
        elif source_id in seen_ids:
            errors.append(
                f"{prefix}: duplicate source_id {source_id!r} "
                f"(first seen on line {seen_ids[source_id]})"
            )
        else:
            seen_ids[source_id] = line_no

        if not row["source_kind"].strip():
            errors.append(f"{prefix}: source_kind is required")
        if not row["tex_file"].strip() and row["status"].strip() != "excluded":
            errors.append(f"{prefix}: tex_file is required unless status is excluded")

        status = row["status"].strip()
        if status not in STATUSES:
            errors.append(f"{prefix}: invalid status {status!r}")
        elif status in {"pending", "drafted"}:
            errors.append(f"{prefix}: incomplete status {status!r}")
        elif status == "excluded" and not row["notes"].strip():
            errors.append(f"{prefix}: excluded rows require an explanation in notes")
        elif (
            status == "verified"
            and max_verified_span is not None
            and end - start + 1 > max_verified_span
        ):
            errors.append(
                f"{prefix}: verified range {start}-{end} spans {end - start + 1} pages; "
                f"maximum allowed is {max_verified_span}"
            )

        if status in {"verified", "excluded"} and end >= start:
            for page in range(start, end + 1):
                if page in page_owners:
                    owner_id, owner_line = page_owners[page]
                    errors.append(
                        f"{prefix}: PDF page {page} overlaps {owner_id!r} "
                        f"from line {owner_line}"
                    )
                else:
                    page_owners[page] = (source_id or f"line-{line_no}", line_no)
                    covered.add(page)

    if first_page is not None:
        expected = set(range(first_page, last_page + 1))
        missing = sorted(expected - covered)
        outside = sorted(covered - expected)
        if missing:
            errors.append("uncovered PDF pages: " + compress_ranges(missing))
        if outside:
            errors.append("ledger pages outside expected range: " + compress_ranges(outside))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Coverage verified: {path} ({len(rows)} rows)")


def compress_ranges(values: list[int]) -> str:
    if not values:
        return ""
    ranges: list[str] = []
    start = previous = values[0]
    for value in values[1:]:
        if value == previous + 1:
            previous = value
            continue
        ranges.append(str(start) if start == previous else f"{start}-{previous}")
        start = previous = value
    ranges.append(str(start) if start == previous else f"{start}-{previous}")
    return ", ".join(ranges)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Initialize or validate a whole-source PDF coverage ledger."
    )
    parser.add_argument("ledger", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--init", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--first-page", type=int)
    parser.add_argument("--last-page", type=int)
    parser.add_argument(
        "--max-verified-span",
        type=int,
        help="reject overly coarse verified rows; book audits should normally use a chapter-sized limit",
    )
    args = parser.parse_args()

    if args.init:
        if (
            args.first_page is not None
            or args.last_page is not None
            or args.max_verified_span is not None
        ):
            parser.error("page-range arguments apply only to --check")
        initialize(args.ledger)
    else:
        if args.max_verified_span is not None and args.max_verified_span < 1:
            parser.error("--max-verified-span must be positive")
        validate(
            args.ledger,
            args.first_page,
            args.last_page,
            args.max_verified_span,
        )


if __name__ == "__main__":
    main()
