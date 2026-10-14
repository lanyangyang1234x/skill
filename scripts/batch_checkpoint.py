#!/usr/bin/env python3
"""Claim, checkpoint, promote, and audit disjoint translation/review batches."""

from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO


# Keep the TSV schema stable. New completed rows store a JSON file-to-hash map
# in output_sha256; existing aggregate SHA-256 rows remain readable.
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
PHASES = {"translation", "mathematics", "terminology", "language", "layout", "review"}
REVIEW_ROUND = re.compile(r"review:[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
SHA256 = re.compile(r"[0-9a-fA-F]{64}\Z")


def valid_phase(value: str) -> bool:
    return value in PHASES or REVIEW_ROUND.fullmatch(value) is not None


def phase_argument(value: str) -> str:
    if not valid_phase(value):
        raise argparse.ArgumentTypeError(
            "phase must be a standard phase or review:ROUND (ASCII letter/digit first, then letters/digits/_/./-)"
        )
    return value


def target_path(project: Path, relative: str) -> Path:
    path = (project / relative).resolve()
    try:
        path.relative_to(project.resolve())
    except ValueError as exc:
        raise SystemExit(f"Target file escapes project: {relative}") from exc
    if Path(relative).is_absolute():
        raise SystemExit(f"Target file must be relative to project: {relative}")
    return path


def file_keys(project: Path, files: list[str]) -> set[str]:
    """Compare actual project paths, including ./, .., and symlink aliases."""
    return {str(target_path(project, relative)) for relative in files}


def digest_files(project: Path, files: list[str]) -> str:
    """The original aggregate encoding, retained for old ledger verification."""
    digest = hashlib.sha256()
    for relative in sorted(files):
        path = target_path(project, relative)
        if not path.is_file():
            raise SystemExit(f"Target file not found: {relative}")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def digest_one(project: Path, relative: str) -> str:
    path = target_path(project, relative)
    if not path.is_file():
        raise SystemExit(f"Target file not found: {relative}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checkpoint_hashes(project: Path, files: list[str]) -> str:
    hashes = {relative: digest_one(project, relative) for relative in files}
    return json.dumps(hashes, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate hash key {key!r}")
        result[key] = value
    return result


def parse_hashes(value: str, files: list[str]) -> dict[str, str] | str:
    if SHA256.fullmatch(value):
        return value.lower()
    try:
        hashes = json.loads(value, object_pairs_hook=unique_json_object)
    except (ValueError, TypeError) as exc:
        raise SystemExit("Invalid output_sha256: expected SHA-256 or JSON per-file hashes") from exc
    if not isinstance(hashes, dict) or set(hashes) != set(files):
        raise SystemExit("Per-file hash keys must exactly match target_files")
    if any(not isinstance(value, str) or not SHA256.fullmatch(value) for value in hashes.values()):
        raise SystemExit("Invalid per-file SHA-256 value")
    return {relative: value.lower() for relative, value in hashes.items()}


def read_rows(handle: TextIO) -> list[dict[str, str]]:
    handle.seek(0)
    reader = csv.DictReader(handle, delimiter="\t", strict=True)
    try:
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise SystemExit("Invalid batch checkpoint header")
        rows = list(reader)
    except csv.Error as exc:
        raise SystemExit(f"Invalid batch checkpoint TSV: {exc}") from exc
    for index, row in enumerate(rows, start=2):
        if set(row) != set(FIELDS) or any(value is None for value in row.values()):
            raise SystemExit(f"Invalid batch checkpoint columns at row {index}")
    return rows


def write_rows(handle: TextIO, rows: list[dict[str, str]]) -> None:
    handle.seek(0)
    handle.truncate()
    writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    handle.flush()
    os.fsync(handle.fileno())


def open_locked(path: Path) -> TextIO:
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
    if any(any(char in value for char in ("\0", "\n", "\r", "\t", ";")) for value in files):
        raise SystemExit("Target file names cannot contain NUL, semicolons, tabs, or newlines")
    return files


def validate_rows(rows: list[dict[str, str]], project: Path) -> tuple[list[str], dict[int, dict[str, object]]]:
    """Validate before any int conversion or mutation; malformed rows never crash an audit."""
    errors: list[str] = []
    parsed: dict[int, dict[str, object]] = {}
    previous: dict[str, tuple[dict[str, str], dict[str, object]]] = {}
    for index, row in enumerate(rows):
        label = f"{row['batch_id'] or '<empty batch ID>'} (row {index + 2})"
        row_errors: list[str] = []
        try:
            start, end, attempt = (int(row[field]) for field in ("source_start", "source_end", "attempt"))
        except ValueError:
            row_errors.append("invalid numeric checkpoint field")
            start = end = attempt = 0
        else:
            if start < 1 or end < start:
                row_errors.append(f"invalid source range {start}-{end}")
            if attempt < 1:
                row_errors.append("attempt must be positive")
        if not row["batch_id"].strip():
            row_errors.append("batch_id must not be empty")
        if row["status"] not in STATUSES:
            row_errors.append(f"invalid status {row['status']!r}")
        if not valid_phase(row["phase"]):
            row_errors.append(f"invalid phase {row['phase']!r}")
        files: list[str] = []
        keys: set[str] = set()
        hashes: dict[str, str] | str | None = None
        try:
            files = parse_files(row["target_files"].split(";"))
            keys = file_keys(project, files)
            if len(keys) != len(files):
                row_errors.append("target_files contain aliases of the same file")
            if row["status"] in COMPLETED:
                hashes = parse_hashes(row["output_sha256"], files)
            elif row["output_sha256"]:
                row_errors.append("unfinished checkpoint must not have output hashes")
        except SystemExit as exc:
            row_errors.append(str(exc))
        if row_errors:
            errors.extend(f"{label}: {error}" for error in row_errors)
            continue
        info: dict[str, object] = {"start": start, "end": end, "attempt": attempt, "files": files, "keys": keys, "hashes": hashes}
        parsed[index] = info
        prior = previous.get(row["batch_id"])
        if prior:
            old, old_info = prior
            identity = (start, end, row["source_id"], row["phase"], keys)
            old_identity = (old_info["start"], old_info["end"], old["source_id"], old["phase"], old_info["keys"])
            if identity != old_identity:
                errors.append(f"{label}: batch identity changed across checkpoint history")
            transition = (old["status"], row["status"])
            if transition == ("blocked", "in_progress"):
                if attempt != old_info["attempt"] + 1:
                    errors.append(f"{label}: retry must increment attempt by one")
            elif transition in {("pending", "in_progress"), ("in_progress", "drafted"), ("in_progress", "verified"), ("in_progress", "blocked"), ("drafted", "verified")}:
                if attempt != old_info["attempt"]:
                    errors.append(f"{label}: attempt changed without a blocked retry")
            else:
                errors.append(f"{label}: invalid checkpoint transition {old['status']} -> {row['status']}")
        previous[row["batch_id"]] = (row, info)
    return errors, parsed


def hash_errors(project: Path, row: dict[str, str], info: dict[str, object], superseded: set[str] | None = None) -> list[str]:
    """Verify untouched files individually; an active claim never supersedes a hash."""
    superseded = superseded or set()
    files = info["files"]
    hashes = info["hashes"]
    errors: list[str] = []
    if isinstance(hashes, str):
        keys = info["keys"]
        if keys <= superseded:
            return errors
        try:
            actual = digest_files(project, files)
        except (SystemExit, OSError) as exc:
            errors.append(str(exc))
        else:
            if actual != hashes:
                suffix = "; partially superseded legacy aggregate needs a new checkpoint covering all target files" if keys & superseded else ""
                errors.append("target file hash changed" + suffix)
    else:
        for relative in files:
            if str(target_path(project, relative)) in superseded:
                continue
            try:
                actual = digest_one(project, relative)
            except (SystemExit, OSError) as exc:
                errors.append(str(exc))
            else:
                if actual != hashes[relative]:
                    errors.append(f"target file hash changed: {relative}")
    return errors


def audit(rows: list[dict[str, str]], project: Path, require_complete: bool, require_verified: bool) -> tuple[list[str], list[str]]:
    errors, parsed = validate_rows(rows, project)
    current = latest(rows)
    positions = {id(row): index for index, row in enumerate(rows)}
    # Walk every completed checkpoint, including historical ones. Each file's
    # responsibility moves only to a later completed checkpoint, never a claim.
    last_completed: dict[str, tuple[int, dict[str, str]]] = {}
    for index, row in enumerate(rows):
        if index in parsed and row["status"] in COMPLETED:
            for key in parsed[index]["keys"]:
                last_completed[key] = (index, row)
    for index, row in enumerate(rows):
        if index not in parsed or row["status"] not in COMPLETED:
            continue
        info = parsed[index]
        superseded = {key for key in info["keys"] if last_completed[key][0] > index}
        errors.extend(f"{row['batch_id']} (row {index + 2}): {error}" for error in hash_errors(project, row, info, superseded))
    active = [(batch_id, row, parsed[positions[id(row)]]) for batch_id, row in current.items() if row["status"] in ACTIVE and positions[id(row)] in parsed]
    for index, (batch_id, row, info) in enumerate(active):
        for other_id, other, other_info in active[index + 1:]:
            if row["phase"] == other["phase"] and info["start"] <= other_info["end"] and other_info["start"] <= info["end"]:
                errors.append(f"overlapping active source ranges: {batch_id} and {other_id}")
            if info["keys"] & other_info["keys"]:
                errors.append(f"overlapping active target files: {batch_id} and {other_id}")
    notices: list[str] = []
    for batch_id, row in current.items():
        if require_complete or require_verified:
            if row["status"] not in COMPLETED:
                errors.append(f"{batch_id}: release requires completion; status is {row['status']}")
        if require_verified and row["status"] == "drafted" and positions[id(row)] in parsed:
            position = positions[id(row)]
            info = parsed[position]
            responsible = [last_completed[key] for key in info["keys"]]
            if all(index > position and later["status"] == "verified" for index, later in responsible):
                batches = sorted({later["batch_id"] for _, later in responsible})
                notices.append(f"{batch_id}: drafted output superseded by verified batches: {', '.join(batches)}")
            else:
                errors.append(f"{batch_id}: release requires verified output for every target file")
    return errors, notices


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--init", action="store_true")
    mode.add_argument("--claim", action="store_true")
    mode.add_argument("--complete", action="store_true")
    mode.add_argument("--promote", action="store_true", help="Promote an unchanged drafted checkpoint to verified; --notes is required")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--batch-id")
    parser.add_argument("--source-start", type=int)
    parser.add_argument("--source-end", type=int)
    parser.add_argument("--source-id", default="")
    parser.add_argument("--phase", type=phase_argument, default="translation", metavar="PHASE",
                        help="Standard phase (" + ", ".join(sorted(PHASES)) + ") or a named review:ROUND")
    parser.add_argument("--owner", default="")
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--status", choices=sorted(COMPLETED | {"blocked"}))
    parser.add_argument("--notes", default="")
    parser.add_argument("--retry", action="store_true", help="Retry a blocked batch with identical identity and a reason in --notes")
    parser.add_argument("--require-complete", action="store_true", help="With --check, reject pending, in_progress, or blocked batches")
    parser.add_argument("--require-verified", action="store_true", help="With --check, also require each effective output responsibility to be verified")
    args = parser.parse_args()
    if (args.require_complete or args.require_verified) and not args.check:
        parser.error("--require-complete and --require-verified require --check")
    if args.retry and not args.claim:
        parser.error("--retry requires --claim")

    ledger = args.ledger.expanduser().resolve()
    project = args.project_dir.expanduser().resolve()
    if args.init:
        with open_locked(ledger) as handle:
            handle.seek(0, os.SEEK_END)
            if handle.tell():
                raise SystemExit(f"Refusing to overwrite existing ledger: {ledger}")
            write_rows(handle, [])
        print(f"Initialized: {ledger}")
        return 0
    if not ledger.is_file():
        raise SystemExit(f"Ledger not found: {ledger}; run --init first")
    with open_locked(ledger) as handle:
        rows = read_rows(handle)
        current = latest(rows)
        if args.check:
            errors, notices = audit(rows, project, args.require_complete, args.require_verified)
            for notice in notices:
                print(f"INFO: {notice}")
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print(f"Batch checkpoint audit passed: {len(current)} batches")
            return 0
        errors, parsed = validate_rows(rows, project)
        if errors:
            raise SystemExit("Invalid batch checkpoint ledger:\n" + "\n".join(errors))
        if not args.batch_id or not args.batch_id.strip():
            raise SystemExit("--batch-id is required")
        prior = current.get(args.batch_id)
        positions = {id(row): index for index, row in enumerate(rows)}

        if args.claim:
            if args.source_start is None or args.source_end is None:
                raise SystemExit("--source-start and --source-end are required")
            if args.source_start < 1 or args.source_end < args.source_start:
                raise SystemExit("Invalid source range")
            if args.phase.startswith("review:") and not args.notes.strip():
                raise SystemExit("Named review rounds require a concrete re-review reason in --notes")
            files = parse_files(args.file)
            keys = file_keys(project, files)
            if len(keys) != len(files):
                raise SystemExit("Target files contain aliases of the same file")
            if args.retry:
                if not prior or prior["status"] != "blocked":
                    raise SystemExit("--retry requires an existing blocked batch")
                if not args.notes.strip():
                    raise SystemExit("--retry requires a concrete reason in --notes")
                prior_info = parsed[positions[id(prior)]]
                identity = (args.source_start, args.source_end, args.source_id, args.phase, keys)
                prior_identity = (prior_info["start"], prior_info["end"], prior["source_id"], prior["phase"], prior_info["keys"])
                if identity != prior_identity:
                    raise SystemExit("Retry must keep the same batch ID, source range, source ID, phase, and target files")
            elif prior:
                if prior["status"] == "blocked":
                    raise SystemExit(f"Batch {args.batch_id} is blocked; use --retry with a reason")
                if prior["status"] != "pending":
                    raise SystemExit(f"Batch {args.batch_id} already has status {prior['status']}; duplicate dispatch refused")
                prior_info = parsed[positions[id(prior)]]
                if (args.source_start, args.source_end, args.source_id, args.phase, keys) != (prior_info["start"], prior_info["end"], prior["source_id"], prior["phase"], prior_info["keys"]):
                    raise SystemExit("Claim must preserve the pending batch identity")
            for other_id, other in current.items():
                if other_id == args.batch_id or other["status"] == "blocked":
                    continue
                other_info = parsed[positions[id(other)]]
                if args.phase == other["phase"] and args.source_start <= other_info["end"] and other_info["start"] <= args.source_end:
                    raise SystemExit(f"Source range overlaps existing {args.phase} batch {other_id}; dispatch refused")
                if other["status"] in ACTIVE and keys & other_info["keys"]:
                    raise SystemExit(f"Target files overlap active batch {other_id}; dispatch refused")
            attempt = int(prior["attempt"]) + (1 if args.retry else 0) if prior else 1
            rows.append({
                "batch_id": args.batch_id, "source_start": str(args.source_start), "source_end": str(args.source_end),
                "source_id": args.source_id, "phase": args.phase, "owner": args.owner, "target_files": ";".join(files),
                "status": "in_progress", "attempt": str(attempt), "output_sha256": "", "updated_at_utc": now(), "notes": args.notes,
            })
            write_rows(handle, rows)
            print(f"Claimed {args.batch_id} attempt {attempt}")
            return 0

        if args.promote:
            if not prior or prior["status"] != "drafted":
                raise SystemExit(f"Batch {args.batch_id} has no drafted checkpoint to promote")
            if not args.notes.strip():
                raise SystemExit("--promote requires verification evidence in --notes")
            errors = hash_errors(project, prior, parsed[positions[id(prior)]])
            if errors:
                raise SystemExit("Cannot promote changed output: " + "; ".join(errors))
            rows.append({**prior, "status": "verified", "updated_at_utc": now(), "notes": args.notes})
            write_rows(handle, rows)
            print(f"Promoted {args.batch_id}: verified (unchanged output)")
            return 0

        if not prior or prior["status"] != "in_progress":
            raise SystemExit(f"Batch {args.batch_id} has no active claim")
        if args.complete:
            if args.status not in COMPLETED | {"blocked"}:
                raise SystemExit("--status drafted, verified, or blocked is required")
            if args.status == "blocked" and not args.notes.strip():
                raise SystemExit("--status blocked requires a concrete reason in --notes")
            files = parsed[positions[id(prior)]]["files"]
            digest = "" if args.status == "blocked" else checkpoint_hashes(project, files)
            rows.append({**prior, "status": args.status, "output_sha256": digest, "updated_at_utc": now(), "notes": args.notes})
            write_rows(handle, rows)
            print(f"Completed {args.batch_id}: {args.status}")
            return 0
    raise SystemExit("No operation selected")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, UnicodeError) as exc:
        raise SystemExit(f"Batch checkpoint error: {exc}") from exc
