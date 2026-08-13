#!/usr/bin/env python3
"""Check that expected PDF image objects retain soft transparency masks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except ModuleNotFoundError as error:
    raise SystemExit("pypdf is required for PDF image-mask validation") from error


def parse_expectation(value: str) -> tuple[int, int, int]:
    try:
        page, size = value.split(":", 1)
        width, height = size.lower().split("x", 1)
        page_number, width_number, height_number = int(page), int(width), int(height)
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected PAGE:WIDTHxHEIGHT") from error
    if min(page_number, width_number, height_number) <= 0:
        raise argparse.ArgumentTypeError("page and dimensions must be positive")
    return page_number, width_number, height_number


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify soft masks for known transparent figure image sizes on PDF pages."
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument(
        "--expect",
        action="append",
        type=parse_expectation,
        required=True,
        metavar="PAGE:WIDTHxHEIGHT",
        help="Physical 1-based PDF page and expected image dimensions; repeat per figure.",
    )
    args = parser.parse_args()
    reader = PdfReader(str(args.pdf))
    failures = []
    for page_number, width, height in args.expect:
        if page_number > len(reader.pages):
            failures.append(f"page {page_number} is outside {len(reader.pages)} pages")
            continue
        resources = reader.pages[page_number - 1].get("/Resources").get_object()
        xobjects = resources.get("/XObject", {})
        matches = []
        for reference in xobjects.values():
            image = reference.get_object()
            if image.get("/Subtype") != "/Image":
                continue
            if image.get("/Width") == width and image.get("/Height") == height:
                matches.append(bool(image.get("/SMask")))
        if not matches:
            failures.append(f"page {page_number}: no {width}x{height} image object")
        elif not any(matches):
            failures.append(f"page {page_number}: {width}x{height} image has no /SMask")
        else:
            print(f"PASS page={page_number} size={width}x{height} smask=true")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
