#!/usr/bin/env python3
"""Render final figure pages as centerline-overlay contact sheets."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

try:
    import fitz
except ModuleNotFoundError as error:
    raise SystemExit("PyMuPDF is required for figure-page contact sheets") from error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render verified figure-manifest pages with a centerline audit overlay."
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=144)
    return parser.parse_args()


def manifest_pages(path: Path) -> list[tuple[int, list[str]]]:
    pages: dict[int, list[str]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"figure_id", "target_pdf_page", "status"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise SystemExit(f"Invalid figure manifest header: {path}")
        for row in reader:
            if row["status"] != "verified":
                continue
            try:
                page = int(row["target_pdf_page"])
            except ValueError as error:
                raise SystemExit(
                    f"Invalid target_pdf_page for {row['figure_id']}: {row['target_pdf_page']}"
                ) from error
            pages.setdefault(page, []).append(row["figure_id"])
    if not pages:
        raise SystemExit(f"No verified figure pages in: {path}")
    return sorted(pages.items())


def fitted_rect(source: fitz.Rect, target: fitz.Rect) -> fitz.Rect:
    scale = min(target.width / source.width, target.height / source.height)
    width = source.width * scale
    height = source.height * scale
    x0 = target.x0 + (target.width - width) / 2
    y0 = target.y0 + (target.height - height) / 2
    return fitz.Rect(x0, y0, x0 + width, y0 + height)


def main() -> int:
    args = parse_args()
    if args.dpi < 72:
        raise SystemExit("--dpi must be at least 72")
    if not args.pdf.is_file():
        raise SystemExit(f"PDF not found: {args.pdf}")
    if not args.manifest.is_file():
        raise SystemExit(f"Manifest not found: {args.manifest}")

    entries = manifest_pages(args.manifest)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    source = fitz.open(args.pdf)
    invalid = [page for page, _ in entries if page < 1 or page > len(source)]
    if invalid:
        raise SystemExit(f"Manifest pages outside 1..{len(source)}: {invalid}")

    sheet = fitz.open()
    sheet_width, sheet_height = 1190.0, 1684.0
    margin, gap, label_height = 24.0, 18.0, 24.0
    tile_width = (sheet_width - 2 * margin - gap) / 2
    tile_height = (sheet_height - 2 * margin - gap) / 2

    for index, (page_number, figure_ids) in enumerate(entries):
        slot = index % 4
        if slot == 0:
            contact = sheet.new_page(width=sheet_width, height=sheet_height)
        column, row = slot % 2, slot // 2
        x0 = margin + column * (tile_width + gap)
        y0 = margin + row * (tile_height + gap)
        label = f"physical page {page_number}: {', '.join(figure_ids)}"
        contact.insert_text((x0, y0 + 15), label, fontsize=11, color=(0.15, 0.15, 0.15))
        target = fitz.Rect(x0, y0 + label_height, x0 + tile_width, y0 + tile_height)
        source_rect = source[page_number - 1].rect
        placed = fitted_rect(source_rect, target)
        contact.show_pdf_page(placed, source, page_number - 1, keep_proportion=True)
        center_x = (placed.x0 + placed.x1) / 2
        contact.draw_line(
            fitz.Point(center_x, placed.y0),
            fitz.Point(center_x, placed.y1),
            color=(0.9, 0.05, 0.12),
            width=0.8,
            stroke_opacity=0.42,
            dashes="[4 3]",
            overlay=True,
        )
        contact.draw_rect(placed, color=(0.55, 0.55, 0.55), width=0.4, overlay=True)

    contact_pdf = args.output_dir / "figure-page-contacts.pdf"
    sheet.save(contact_pdf, garbage=4, deflate=True)
    zoom = args.dpi / 72
    for number, page in enumerate(sheet, start=1):
        pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        pixmap.save(args.output_dir / f"contact-{number:02d}.png")

    print(
        f"Rendered {len(entries)} figure pages into {len(sheet)} contact sheets: {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
