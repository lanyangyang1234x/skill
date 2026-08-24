#!/usr/bin/env python3
"""Claim and verify disjoint translation/review batches without duplicate retries."""

from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path


FIELDS = (
    "batch_id",
    "source_start",
    "source_end",
    "source_id",
    "phase",
    "owner",
    "target_files",
    "status",
    "attempt",
    "output_sha256",
    "updated_at_utc",
    "notes",
)
STATUSES = {"pending", "in_progress", "drafted", "verified", "blocked"}
ACTIVE = {"in_progress"}
COMPLETED = {"drafted", "verified"}
PHASES = {"translation", "mathematics", "terminology", "layout"}


def digest_files(project: Path, files: list[str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(files):
        path = (project / relative).resolve()
        try:
            path.relative_to(project.resolve())
        except ValueError as exc:
            raise SystemExit(f"Target file escapes project: {relative}") from exc
        if not path.is_file():
            raise SystemExit(f"Target file not found: {relative}")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def read_rows(handle: object) -> list[dict[str, str]]:
    handle.seek(0)
    reader = csv.DictReader(handle, delimiter="\t")
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise SystemExit("Invalid batch checkpoint header")
    return list(reader)


def write_rows(handle: object, rows: list[dict[str, str]]) -> None:
    handle.seek(0)
    handle.truncate()
    writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    handle.flush()
    os.fsync(handle.fileno())


def open_locked(path: Path) -> object:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+", encoding="utf-8", newline="")
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    return handle


def latest(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        result[row["batch_id"]] = row
    return result


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_files(values: list[str]) -> list[str]:
    files = sorted({value.strip() for value in values if value.strip()})
    if not files:
        raise SystemExit("At least one --file is required")
    if any("\n" in value or "\t" in value for value in files):
        raise SystemExit("Target file names cannot contain tabs or newlines")
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--init", action="store_true")
    mode.add_argument("--claim", action="store_true")
    mode.add_argument("--complete", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--batch-id")
    parser.add_argument("--source-start", type=int)
    parser.add_argument("--source-end", type=int)
    parser.add_argument("--source-id", default="")
    parser.add_argument("--phase", choices=sorted(PHASES), default="translation")
    parser.add_argument("--owner", default="")
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--status", choices=sorted(COMPLETED | {"blocked"}))
    parser.add_argument("--notes", default="")
    parser.add_argument("--retry", action="store_true")
    args = parser.parse_args()

    ledger = args.ledger.expanduser().resolve()
    project = args.project_dir.expanduser().resolve()
    if args.init:
        if ledger.exists() and ledger.stat().st_size:
            raise SystemExit(f"Refusing to overwrite existing ledger: {ledger}")
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with ledger.open("w", encoding="utf-8", newline="") as handle:
            csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t", lineterminator="\n").writeheader()
        print(f"Initialized: {ledger}")
        return 0

    if not ledger.is_file():
        raise SystemExit(f"Ledger not found: {ledger}; run --init first")
    with open_locked(ledger) as handle:
        rows = read_rows(handle)
        current = latest(rows)

        if args.check:
            errors: list[str] = []
            positions = {id(row): index for index, row in enumerate(rows)}
            for batch_id, row in current.items():
                try:
                    start = int(row["source_start"])
                    end = int(row["source_end"])
                    attempt = int(row["attempt"])
                except ValueError:
                    errors.append(f"{batch_id}: invalid numeric checkpoint field")
                    continue
                if start < 1 or end < start:
                    errors.append(f"{batch_id}: invalid source range {start}-{end}")
                if attempt < 1:
                    errors.append(f"{batch_id}: attempt must be positive")
                if row["status"] not in STATUSES:
                    errors.append(f"{batch_id}: invalid status {row['status']!r}")
                if row["phase"] not in PHASES:
                    errors.append(f"{batch_id}: invalid phase {row['phase']!r}")
                files = parse_files(row["target_files"].split(";"))
                later_file_use = any(
                    later["status"] != "blocked"
                    and set(files) & set(parse_files(later["target_files"].split(";")))
                    for later in rows[positions[id(row)] + 1 :]
                )
                if row["status"] in COMPLETED and not later_file_use:
                    try:
                        actual = digest_files(project, files)
                    except SystemExit as exc:
                        errors.append(f"{batch_id}: {exc}")
                    else:
                        if actual != row["output_sha256"]:
                            errors.append(f"{batch_id}: target file hash changed")
            for batch_id, row in current.items():
                if row["status"] != "in_progress":
                    continue
                for other_id, other in current.items():
                    if other_id <= batch_id or other["status"] != "in_progress":
                        continue
                    if row["phase"] != other["phase"]:
                        continue
                    if int(row["source_start"]) <= int(other["source_end"]) and int(other["source_start"]) <= int(row["source_end"]):
                        errors.append(f"overlapping active source ranges: {batch_id} and {other_id}")
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print(f"Batch checkpoint audit passed: {len(current)} batches")
            return 0

        if not args.batch_id:
            raise SystemExit("--batch-id is required")
        prior = current.get(args.batch_id)

        if args.claim:
            if args.source_start is None or args.source_end is None:
                raise SystemExit("--source-start and --source-end are required")
            if args.source_start < 1 or args.source_end < args.source_start:
                raise SystemExit("Invalid source range")
            files = parse_files(args.file)
            if prior and (prior["status"] in ACTIVE or prior["status"] in COMPLETED):
                raise SystemExit(
                    f"Batch {args.batch_id} already has status {prior['status']}; duplicate dispatch refused"
                )
            if prior and prior["status"] == "blocked" and not args.retry:
                raise SystemExit(f"Batch {args.batch_id} is blocked; use --retry with a reason")
            for other_id, other in current.items():
                if other_id == args.batch_id or other["status"] == "blocked":
                    continue
                other_start = int(other["source_start"])
                other_end = int(other["source_end"])
                if (
                    args.phase == other["phase"]
                    and args.source_start <= other_end
                    and other_start <= args.source_end
                ):
                    raise SystemExit(
                        f"Source range overlaps existing {args.phase} batch {other_id}; dispatch refused"
                    )
                other_files = set(parse_files(other["target_files"].split(";")))
                if other["status"] in ACTIVE and set(files) & other_files:
                    raise SystemExit(
                        f"Target files overlap active batch {other_id}; dispatch refused"
                    )
            attempt = int(prior["attempt"]) + 1 if prior else 1
            rows.append(
                {
                    "batch_id": args.batch_id,
                    "source_start": str(args.source_start),
                    "source_end": str(args.source_end),
                    "source_id": args.source_id,
                    "phase": args.phase,
                    "owner": args.owner,
                    "target_files": ";".join(files),
                    "status": "in_progress",
                    "attempt": str(attempt),
                    "output_sha256": "",
                    "updated_at_utc": now(),
                    "notes": args.notes,
                }
            )
            write_rows(handle, rows)
            print(f"Claimed {args.batch_id} attempt {attempt}")
            return 0

        if not prior or prior["status"] != "in_progress":
            raise SystemExit(f"Batch {args.batch_id} has no active claim")
        if args.complete:
            if args.status not in COMPLETED | {"blocked"}:
                raise SystemExit("--status drafted, verified, or blocked is required")
            files = parse_files(prior["target_files"].split(";"))
            digest = "" if args.status == "blocked" else digest_files(project, files)
            rows.append(
                {
                    **prior,
                    "status": args.status,
                    "output_sha256": digest,
                    "updated_at_utc": now(),
                    "notes": args.notes,
                }
            )
            write_rows(handle, rows)
            print(f"Completed {args.batch_id}: {args.status}")
            return 0

    raise SystemExit("No operation selected")


if __name__ == "__main__":
    raise SystemExit(main())
