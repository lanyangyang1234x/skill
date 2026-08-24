#!/usr/bin/env python3
"""Snapshot an authoritative source PDF and verify its identity later."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_pages(path: Path) -> int | None:
    try:
        result = subprocess.run(
            ["pdfinfo", str(path)],
            check=True,
            capture_output=True,
            text=True,
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


def create_manifest(args: argparse.Namespace) -> int:
    source = args.source.expanduser().resolve()
    project = args.project_dir.expanduser().resolve()
    output = project / args.output
    if not source.is_file():
        raise SystemExit(f"Source file not found: {source}")
    if output.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing manifest without --force: {output}")

    snapshot_rel: Path | None = None
    authoritative = source
    if not args.no_snapshot:
        snapshot_dir = project / "work/source"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        suffix = source.suffix.lower() or ".pdf"
        snapshot = snapshot_dir / f"authoritative-source{suffix}"
        if source != snapshot:
            shutil.copy2(source, snapshot)
        snapshot_rel = snapshot.relative_to(project)
        authoritative = snapshot

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "original_filename": source.name,
        "local_source_path": str(source),
        "snapshot_path": snapshot_rel.as_posix() if snapshot_rel else None,
        "sha256": sha256(authoritative),
        "size_bytes": authoritative.stat().st_size,
        "pdf_pages": pdf_pages(authoritative) if authoritative.suffix.lower() == ".pdf" else None,
        "release_policy": "local QA record; exclude the source snapshot and local path from public release archives",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Source manifest: {output}")
    print(f"Source SHA-256: {record['sha256']}")
    if snapshot_rel:
        print(f"Read-only audit snapshot: {project / snapshot_rel}")
    return 0


def check_manifest(args: argparse.Namespace) -> int:
    manifest = args.manifest.expanduser().resolve()
    if not manifest.is_file():
        raise SystemExit(f"Manifest not found: {manifest}")
    record = json.loads(manifest.read_text(encoding="utf-8"))
    if record.get("schema_version") != SCHEMA_VERSION:
        raise SystemExit(f"Unsupported source manifest schema: {record.get('schema_version')!r}")

    snapshot_value = record.get("snapshot_path")
    if snapshot_value:
        source = manifest.parent / snapshot_value
    else:
        source = Path(str(record.get("local_source_path", "")))
    if not source.is_file():
        raise SystemExit(f"Recorded authoritative source is unavailable: {source}")

    errors: list[str] = []
    actual_hash = sha256(source)
    if actual_hash != record.get("sha256"):
        errors.append(f"SHA-256 changed: expected {record.get('sha256')}, found {actual_hash}")
    if source.stat().st_size != record.get("size_bytes"):
        errors.append(
            f"size changed: expected {record.get('size_bytes')}, found {source.stat().st_size}"
        )
    expected_pages = record.get("pdf_pages")
    if expected_pages is not None:
        actual_pages = pdf_pages(source)
        if actual_pages != expected_pages:
            errors.append(f"page count changed: expected {expected_pages}, found {actual_pages}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Source manifest verified: {manifest}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="snapshot a source and write its manifest")
    create.add_argument("source", type=Path)
    create.add_argument("--project-dir", type=Path, required=True)
    create.add_argument("--output", default="source-manifest.json")
    create.add_argument("--no-snapshot", action="store_true")
    create.add_argument("--force", action="store_true")
    create.set_defaults(func=create_manifest)

    check = subparsers.add_parser("check", help="verify a recorded source snapshot")
    check.add_argument("manifest", type=Path)
    check.set_defaults(func=check_manifest)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
