#!/usr/bin/env python3
"""Fetch a random portrait landscape photograph from Wikimedia Commons."""

from __future__ import annotations

import argparse
import json
import secrets
import sys
import urllib.parse
import urllib.request
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
USER_AGENT = "pdf-to-chinese-tex/2.0 (random Sage-Olive cover)"


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


def choose_candidate(categories: list[str]) -> dict[str, Any]:
    shuffled = list(categories)
    secrets.SystemRandom().shuffle(shuffled)
    candidates: list[dict[str, Any]] = []
    scanned: list[str] = []
    for category in shuffled:
        scanned.append(category)
        candidates.extend(collect_candidates(category))
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_dir = args.project_dir.expanduser().resolve()
    cover_dir = project_dir / "assets/cover"
    source_record = cover_dir / "cover-source.json"
    existing = [path for path in (cover_dir / "selected-cover.jpg", cover_dir / "selected-cover.png") if path.is_file()]
    if existing and not args.force:
        print(f"Online cover already selected: {existing[0]}")
        return 0

    cover_dir.mkdir(parents=True, exist_ok=True)
    try:
        candidate = choose_candidate(args.category or list(DEFAULT_CATEGORIES))
        temporary, output = download(candidate, cover_dir)
        for old_cover in existing:
            old_cover.unlink()
        temporary.replace(output)
        candidate["local_file"] = output.name
        source_record.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:
        for temporary in cover_dir.glob(".selected-cover-download.*"):
            temporary.unlink(missing_ok=True)
        print(f"Unable to fetch a random online cover: {exc}", file=sys.stderr)
        return 1

    print(f"Selected online cover: {candidate['title']} -> {output}")
    print(f"Source record: {source_record}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
