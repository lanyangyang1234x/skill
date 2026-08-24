#!/usr/bin/env python3
"""Record and verify immutable source/figure asset provenance.

The lock is a JSON document.  Recording an already-listed asset path is refused
unless the caller first creates a new run/asset path; this prevents a later crop
script from silently replacing a verified image.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "entries": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("entries"), list):
        raise SystemExit(f"Invalid figure lock: {path}")
    return data


def record(args: argparse.Namespace) -> None:
    lock = args.lock.expanduser().resolve()
    asset = args.asset.expanduser().resolve()
    source = args.source.expanduser().resolve()
    for path in (asset, source):
        if not path.is_file():
            raise SystemExit(f"Missing provenance file: {path}")
    data = load(lock)
    existing = [entry for entry in data["entries"] if entry["asset"] == str(asset)]
    if existing:
        raise SystemExit(
            f"Asset already locked: {asset}. Use a new run/versioned asset path; "
            "never replace a promoted asset in place."
        )
    entry = {
        "asset": str(asset),
        "asset_sha256": sha256(asset),
        "source": str(source),
        "source_sha256": sha256(source),
        "page": args.page,
        "dpi": args.dpi,
        "crop": args.crop,
        "method": args.method,
        "run_id": args.run_id,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    data["entries"].append(entry)
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Locked: {asset}")


def check(args: argparse.Namespace) -> None:
    lock = args.lock.expanduser().resolve()
    data = load(lock)
    failures: list[str] = []
    for entry in data["entries"]:
        asset = Path(entry["asset"])
        source = Path(entry["source"])
        if not asset.is_file():
            failures.append(f"missing asset: {asset}")
        elif sha256(asset) != entry["asset_sha256"]:
            failures.append(f"asset hash mismatch: {asset}")
        if not source.is_file():
            failures.append(f"missing source: {source}")
        elif sha256(source) != entry["source_sha256"]:
            failures.append(f"source hash mismatch: {source}")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        raise SystemExit(1)
    print(f"Figure asset lock verified: {lock} ({len(data['entries'])} entries)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Lock and verify figure asset provenance.")
    sub = parser.add_subparsers(dest="command", required=True)
    rec = sub.add_parser("record")
    rec.add_argument("lock", type=Path)
    rec.add_argument("asset", type=Path)
    rec.add_argument("source", type=Path)
    rec.add_argument("--page", required=True)
    rec.add_argument("--dpi", required=True)
    rec.add_argument("--crop", required=True)
    rec.add_argument("--method", required=True)
    rec.add_argument("--run-id", required=True)
    rec.set_defaults(func=record)
    chk = sub.add_parser("check")
    chk.add_argument("lock", type=Path)
    chk.set_defaults(func=check)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
