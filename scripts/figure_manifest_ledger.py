#!/usr/bin/env python3
"""Initialize and validate figure manifests for mathematical PDF projects."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


FIELDS = [
    "figure_id",
    "source_pdf_page",
    "source_anchor",
    "source_bounds",
    "included_content",
    "excluded_neighbors",
    "method",
    "output_asset_or_tex",
    "source_width_ratio",
    "target_tex_width",
    "background_mode",
    "source_labels",
    "translated_labels",
    "target_pdf_page",
    "status",
    "notes",
]
STATUSES = {"pending", "drafted", "verified", "excluded"}
BACKGROUND_MODES = {"transparent", "exact-flat", "not-applicable"}


def initialize(path: Path) -> None:
    if path.exists() and path.stat().st_size:
        raise SystemExit(f"Refusing to overwrite nonempty manifest: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        csv.DictWriter(handle, fieldnames=FIELDS, dialect="excel-tab").writeheader()
    print(f"Initialized: {path}")


def positive_int(value: str) -> bool:
    try:
        return int(value) > 0
    except ValueError:
        return False


def output_path(manifest: Path, value: str) -> Path:
    relative = value.split("#", 1)[0].strip()
    return (manifest.parent / relative).resolve()


def validate(path: Path, require_complete: bool) -> None:
    if not path.is_file():
        raise SystemExit(f"Figure manifest not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, dialect="excel-tab")
        if reader.fieldnames != FIELDS:
            raise SystemExit("Unexpected figure manifest header. Expected: " + "\t".join(FIELDS))
        rows = list(reader)

    errors: list[str] = []
    seen_ids: dict[str, int] = {}
    if not rows:
        errors.append("manifest contains no figure rows")

    for line_no, row in enumerate(rows, start=2):
        prefix = f"line {line_no}"
        figure_id = row["figure_id"].strip()
        if not figure_id:
            errors.append(f"{prefix}: figure_id is required")
        elif figure_id in seen_ids:
            errors.append(
                f"{prefix}: duplicate figure_id {figure_id!r} "
                f"(first seen on line {seen_ids[figure_id]})"
            )
        else:
            seen_ids[figure_id] = line_no

        if not positive_int(row["source_pdf_page"].strip()):
            errors.append(f"{prefix}: source_pdf_page must be a positive integer")
        status = row["status"].strip()
        for field in (
            "source_anchor",
            "source_bounds",
            "included_content",
            "excluded_neighbors",
            "source_labels",
        ):
            if not row[field].strip():
                errors.append(f"{prefix}: {field} is required; use 'none' when applicable")

        if status not in STATUSES:
            errors.append(f"{prefix}: invalid status {status!r}")
        elif require_complete and status in {"pending", "drafted"}:
            errors.append(f"{prefix}: incomplete status {status!r}")
        elif status == "verified" and not positive_int(row["target_pdf_page"].strip()):
            errors.append(f"{prefix}: verified figures require a positive target_pdf_page")
        elif status == "excluded" and not row["notes"].strip():
            errors.append(f"{prefix}: excluded figures require an explanation in notes")

        if status != "excluded":
            for field in (
                "method",
                "output_asset_or_tex",
                "target_tex_width",
                "translated_labels",
            ):
                if not row[field].strip():
                    errors.append(f"{prefix}: {field} is required; use 'none' when applicable")
            try:
                ratio = float(row["source_width_ratio"])
                if not 0 < ratio <= 1:
                    raise ValueError
            except ValueError:
                errors.append(f"{prefix}: source_width_ratio must be a number in (0, 1]")

            background = row["background_mode"].strip()
            if background not in BACKGROUND_MODES:
                errors.append(f"{prefix}: invalid background_mode {background!r}")

        if status != "excluded" and row["output_asset_or_tex"].strip():
            output = output_path(path, row["output_asset_or_tex"])
            if not output.is_file():
                errors.append(f"{prefix}: output asset/TeX file not found: {output}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Figure manifest verified: {path} ({len(rows)} rows)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize or validate a figure manifest.")
    parser.add_argument("manifest", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--init", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    path = args.manifest.expanduser().resolve()
    if args.init:
        if args.require_complete:
            parser.error("--require-complete applies only to --check")
        initialize(path)
    else:
        validate(path, args.require_complete)


if __name__ == "__main__":
    main()
