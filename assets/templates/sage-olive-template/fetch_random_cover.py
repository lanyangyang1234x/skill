#!/usr/bin/env python3
"""Fetch a random portrait landscape photograph from Wikimedia Commons."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


API_URL = "https://commons.wikimedia.org/w/api.php"
DEFAULT_CATEGORIES = (
    "Featured pictures of landscapes",
    "Featured pictures of mountains",
    "Featured pictures of waterfalls",
    "Featured pictures of lakes",
    "Featured pictures of coasts",
    "Featured pictures of watercourses",
    "Featured pictures of volcanoes",
)
USER_AGENT = "pdf-to-chinese-tex/2.1 (random Sage-Olive cover)"
DEFAULT_HISTORY = Path("~/.codex/pdf-to-chinese-tex-cover-history.json")


def request_json(parameters: dict[str, str]) -> dict[str, Any]:
    url = API_URL + "?" + urllib.parse.urlencode(parameters)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def clean_metadata_value(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("value", "")).strip()
    return str(value or "").strip()


def collect_candidates(category: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    continuation = ""
    for _ in range(6):
        parameters = {
            "action": "query",
            "generator": "categorymembers",
            "gcmtitle": f"Category:{category}",
            "gcmtype": "file",
            "gcmlimit": "500",
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": "1800",
            "format": "json",
            "formatversion": "2",
        }
        if continuation:
            parameters["gcmcontinue"] = continuation
        data = request_json(parameters)
        for page in data.get("query", {}).get("pages", []):
            image_info = (page.get("imageinfo") or [{}])[0]
            width = int(image_info.get("width") or 0)
            height = int(image_info.get("height") or 0)
            mime = str(image_info.get("mime") or "")
            metadata = image_info.get("extmetadata") or {}
            license_name = clean_metadata_value(metadata.get("LicenseShortName"))
            source_url = str(image_info.get("thumburl") or image_info.get("url") or "")
            if (
                width >= 1000
                and height >= 1400
                and height / max(1, width) >= 1.2
                and mime in {"image/jpeg", "image/png"}
                and license_name
                and source_url.startswith("https://")
            ):
                candidates.append(
                    {
                        "title": page.get("title"),
                        "width": width,
                        "height": height,
                        "mime": mime,
                        "download_url": source_url,
                        "description_url": image_info.get("descriptionurl"),
                        "author": clean_metadata_value(metadata.get("Artist")),
                        "credit": clean_metadata_value(metadata.get("Credit")),
                        "license": license_name,
                        "license_url": clean_metadata_value(metadata.get("LicenseUrl")),
                        "category": category,
                    }
                )
        continuation = str(data.get("continue", {}).get("gcmcontinue") or "")
        if not continuation:
            break
    return candidates


def source_id(candidate: dict[str, Any]) -> str:
    return str(candidate.get("description_url") or candidate.get("title") or "").strip()


def choose_candidate(categories: list[str], used_sources: set[str]) -> dict[str, Any]:
    shuffled = list(categories)
    secrets.SystemRandom().shuffle(shuffled)
    candidates: list[dict[str, Any]] = []
    scanned: list[str] = []
    for category in shuffled:
        scanned.append(category)
        candidates.extend(
            candidate
            for candidate in collect_candidates(category)
            if source_id(candidate) not in used_sources
        )
        # Avoid a nominally random one-image pool while keeping API traffic low.
        if len(candidates) >= 8:
            break
    if not candidates:
        raise RuntimeError(
            "No suitable portrait landscape found in Commons categories: "
            + ", ".join(scanned)
        )
    selected = secrets.choice(candidates)
    selected["candidate_pool_size"] = len(candidates)
    selected["categories_scanned"] = scanned
    return selected


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_history(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "entries": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("entries"), list):
        raise RuntimeError(f"Unsupported cover history format: {path}")
    return data


def register_history(
    history_path: Path,
    history: dict[str, Any],
    candidate: dict[str, Any],
    digest: str,
    project_dir: Path,
) -> None:
    entries = history["entries"]
    candidate_source = source_id(candidate)
    if any(
        entry.get("sha256") == digest
        or (candidate_source and entry.get("source_id") == candidate_source)
        for entry in entries
    ):
        return
    entries.append(
        {
            "source_id": candidate_source,
            "title": candidate.get("title"),
            "description_url": candidate.get("description_url"),
            "sha256": digest,
            "selected_at_utc": datetime.now(timezone.utc).isoformat(),
            "project_name": project_dir.name,
        }
    )
    history_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = history_path.with_name(f".{history_path.name}.tmp")
    temporary.write_text(
        json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(history_path)


def download(candidate: dict[str, Any], destination: Path) -> tuple[Path, Path]:
    extension = ".png" if candidate["mime"] == "image/png" else ".jpg"
    output = destination / f"selected-cover{extension}"
    temporary = destination / f".selected-cover-download{extension}"
    request = urllib.request.Request(candidate["download_url"], headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as handle:
        handle.write(response.read())
    if temporary.stat().st_size < 100_000:
        temporary.unlink(missing_ok=True)
        raise RuntimeError("Downloaded cover is unexpectedly small")
    return temporary, output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch a random online landscape cover")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument(
        "--category",
        action="append",
        help="Commons category to use; repeat to combine categories",
    )
    parser.add_argument("--force", action="store_true", help="Replace the current project's cover")
    parser.add_argument(
        "--history-file",
        type=Path,
        help="Cross-project cover history (default: PDF_TO_CHINESE_TEX_COVER_HISTORY or ~/.codex/pdf-to-chinese-tex-cover-history.json)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_dir = args.project_dir.expanduser().resolve()
    configured_history = args.history_file or Path(
        os.environ.get("PDF_TO_CHINESE_TEX_COVER_HISTORY", str(DEFAULT_HISTORY))
    )
    history_path = configured_history.expanduser().resolve()
    try:
        history = load_history(history_path)
    except Exception as exc:
        print(f"Unable to read cover history {history_path}: {exc}", file=sys.stderr)
        return 1
    used_sources = {str(entry.get("source_id") or "") for entry in history["entries"]}
    used_hashes = {str(entry.get("sha256") or "") for entry in history["entries"]}
    cover_dir = project_dir / "assets/cover"
    source_record = cover_dir / "cover-source.json"
    existing = [path for path in (cover_dir / "selected-cover.jpg", cover_dir / "selected-cover.png") if path.is_file()]
    if existing and not args.force:
        try:
            if not source_record.is_file():
                raise RuntimeError(f"existing cover has no source record: {source_record}")
            candidate = json.loads(source_record.read_text(encoding="utf-8"))
            digest = file_sha256(existing[0])
            register_history(history_path, history, candidate, digest, project_dir)
        except Exception as exc:
            print(f"Unable to register the existing cover in {history_path}: {exc}", file=sys.stderr)
            return 1
        print(f"Online cover already selected: {existing[0]}")
        print(f"Cover history: {history_path}")
        return 0

    cover_dir.mkdir(parents=True, exist_ok=True)
    try:
        for _ in range(6):
            candidate = choose_candidate(args.category or list(DEFAULT_CATEGORIES), used_sources)
            temporary, output = download(candidate, cover_dir)
            digest = file_sha256(temporary)
            if digest not in used_hashes:
                break
            temporary.unlink(missing_ok=True)
            used_sources.add(source_id(candidate))
        else:
            raise RuntimeError("Unable to find a cover not already present in the cover history")
        register_history(history_path, history, candidate, digest, project_dir)
        for old_cover in existing:
            old_cover.unlink()
        temporary.replace(output)
        candidate["local_file"] = output.name
        candidate["sha256"] = digest
        candidate["history_registered"] = True
        source_record.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:
        for temporary in cover_dir.glob(".selected-cover-download.*"):
            temporary.unlink(missing_ok=True)
        print(f"Unable to fetch a random online cover: {exc}", file=sys.stderr)
        return 1

    print(f"Selected online cover: {candidate['title']} -> {output}")
    print(f"Source record: {source_record}")
    print(f"Cover history: {history_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
