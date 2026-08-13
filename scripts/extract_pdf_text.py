#!/usr/bin/env python3
"""Extract page-marked text or layout-aware JSON from a PDF scaffold."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def page_text_from_blocks(page: Any) -> str:
    blocks = page.get_text("blocks", sort=True)
    text_blocks = [
        (float(block[1]), float(block[0]), str(block[4]).rstrip())
        for block in blocks
        if len(block) >= 7 and int(block[6]) == 0 and str(block[4]).strip()
    ]
    text_blocks.sort(key=lambda item: (round(item[0], 1), round(item[1], 1)))
    return "\n\n".join(text for _, _, text in text_blocks)


def extract_text_with_pymupdf(source: Path) -> str:
    import fitz  # type: ignore

    parts: list[str] = []
    with fitz.open(source) as document:
        for page_number, page in enumerate(document, start=1):
            parts.append(f"--- Page {page_number} ---\n{page_text_from_blocks(page)}")
    return "\n\n".join(parts) + "\n"


def sanitize_json(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"binary_bytes": len(value)}
    if isinstance(value, dict):
        return {str(key): sanitize_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize_json(item) for item in value]
    return value


def extract_json_with_pymupdf(source: Path, format_name: str) -> str:
    import fitz  # type: ignore

    pages: list[dict[str, Any]] = []
    with fitz.open(source) as document:
        for page_number, page in enumerate(document, start=1):
            page_info: dict[str, Any] = {
                "page": page_number,
                "width": round(float(page.rect.width), 3),
                "height": round(float(page.rect.height), 3),
                "rotation": int(page.rotation),
            }
            if format_name == "blocks-json":
                page_info["blocks"] = [
                    {
                        "bbox": [round(float(v), 3) for v in block[:4]],
                        "text": str(block[4]).rstrip(),
                        "block_number": int(block[5]),
                        "block_type": int(block[6]),
                    }
                    for block in page.get_text("blocks", sort=True)
                ]
            else:
                page_info["layout"] = sanitize_json(page.get_text("dict", sort=True))
            pages.append(page_info)
    return json.dumps({"source": str(source), "pages": pages}, ensure_ascii=False, indent=2) + "\n"


def mark_pages(pages: list[str]) -> str:
    while pages and not pages[-1].strip():
        pages.pop()
    return "\n\n".join(
        f"--- Page {page_number} ---\n{page.rstrip()}"
        for page_number, page in enumerate(pages, start=1)
    ) + "\n"


def extract_with_pdftotext(source: Path) -> str:
    executable = shutil.which("pdftotext")
    if executable is None:
        raise RuntimeError("Neither PyMuPDF nor pdftotext is available")
    result = subprocess.run(
        [executable, "-layout", str(source), "-"],
        check=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    return mark_pages(result.stdout.split("\f"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract a PDF scaffold; verify formulas and reading order against rendered pages."
    )
    parser.add_argument("source", type=Path, help="Source PDF")
    parser.add_argument("--output", type=Path, help="Output text or JSON file")
    parser.add_argument(
        "--format",
        choices=("text", "blocks-json", "dict-json"),
        default="text",
        help="Text scaffold or layout-aware PyMuPDF JSON",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    default_suffix = ".txt" if args.format == "text" else ".json"
    output = (args.output or source.with_suffix(default_suffix)).expanduser().resolve()

    if not source.is_file() or source.suffix.lower() != ".pdf":
        print(f"Source PDF not found: {source}", file=sys.stderr)
        return 2
    if output.exists() and not args.force:
        print(f"Output already exists; pass --force to overwrite: {output}", file=sys.stderr)
        return 2

    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        if args.format == "text":
            try:
                content = extract_text_with_pymupdf(source)
            except ImportError:
                content = extract_with_pdftotext(source)
        else:
            content = extract_json_with_pymupdf(source, args.format)
    except (ImportError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Extraction failed: {exc}", file=sys.stderr)
        return 1

    output.write_text(content, encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
