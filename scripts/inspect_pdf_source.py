#!/usr/bin/env python3
"""Classify PDF pages for direct extraction versus OCR review."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


HYPHEN_RE = re.compile(r"\b([A-Za-z]{2,})-\n([a-z][A-Za-z]{1,})\b")


def image_coverage(page: object) -> float:
    page_area = float(page.rect.width * page.rect.height)  # type: ignore[attr-defined]
    if page_area <= 0:
        return 0.0
    covered = 0.0
    seen: set[tuple[float, float, float, float]] = set()
    for image in page.get_images(full=True):  # type: ignore[attr-defined]
        for rect in page.get_image_rects(image[0]):  # type: ignore[attr-defined]
            key = tuple(round(float(value), 2) for value in rect)
            if key in seen:
                continue
            seen.add(key)
            covered += max(0.0, float(rect.width * rect.height))
    return round(min(1.0, covered / page_area), 4)


def classify_page(text: str, coverage: float) -> tuple[str, str]:
    compact = "".join(text.split())
    char_count = len(compact)
    bad_count = text.count("\ufffd") + text.count("�")
    bad_ratio = bad_count / max(1, char_count)
    if char_count >= 80 and bad_ratio < 0.02:
        return "electronic", "usable embedded text"
    if char_count < 20 and coverage >= 0.55:
        return "ocr-candidate", "image-dominant page with little embedded text"
    if char_count < 20:
        return "ocr-candidate", "little or no usable embedded text"
    return "mixed-review", "partial or potentially garbled embedded text"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect PDF extraction and OCR needs")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != ".pdf":
        print(f"Source PDF not found: {source}", file=sys.stderr)
        return 2

    try:
        import fitz  # type: ignore
    except ImportError:
        print("PyMuPDF is required for source inspection", file=sys.stderr)
        return 1

    pages: list[dict[str, object]] = []
    counts = {"electronic": 0, "mixed-review": 0, "ocr-candidate": 0}
    with fitz.open(source) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text", sort=True)
            coverage = image_coverage(page)
            category, reason = classify_page(text, coverage)
            counts[category] += 1
            hyphens = ["-".join(match) for match in HYPHEN_RE.findall(text)]
            pages.append(
                {
                    "page": page_number,
                    "category": category,
                    "reason": reason,
                    "non_whitespace_characters": len("".join(text.split())),
                    "text_blocks": sum(1 for block in page.get_text("blocks") if block[6] == 0),
                    "image_coverage": coverage,
                    "linebreak_hyphen_candidates": hyphens[:25],
                }
            )

    total = max(1, len(pages))
    if counts["ocr-candidate"] / total >= 0.8:
        document_type = "scanned"
    elif counts["electronic"] / total >= 0.9:
        document_type = "electronic"
    else:
        document_type = "mixed"

    report = {
        "source": str(source),
        "document_type": document_type,
        "page_count": len(pages),
        "counts": counts,
        "pages": pages,
        "note": "OCR candidates still require visual confirmation; formulas are never trusted to prose OCR alone.",
    }
    content = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            print(f"Output already exists: {output}", file=sys.stderr)
            return 2
        output.write_text(content, encoding="utf-8")
        print(output)
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
