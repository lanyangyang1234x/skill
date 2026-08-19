#!/usr/bin/env python3
"""Validate transparent figure assets and create non-white-background previews."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ModuleNotFoundError:
    configured = os.environ.get("PDF_TO_CHINESE_TEX_IMAGE_PYTHON") or os.environ.get(
        "PDF_TO_CHINESE_TEX_OCR_PYTHON"
    )
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    fallbacks = (
        [Path(configured).expanduser()]
        if configured
        else [
            codex_home / "venvs/pdf-to-chinese-tex-image/bin/python",
            codex_home / "venvs/pdf-to-chinese-tex-ocr/bin/python",
        ]
    )
    for fallback in fallbacks:
        if fallback.is_file() and Path(sys.executable) != fallback:
            os.execv(str(fallback), [str(fallback), str(Path(__file__).resolve()), *sys.argv[1:]])
    raise SystemExit(
        "Pillow is unavailable. Set PDF_TO_CHINESE_TEX_IMAGE_PYTHON to a Python "
        "interpreter containing Pillow; an OCR/PaddleOCR installation is not required "
        "for image-only operations."
    )


def parse_rgb(value: str) -> tuple[int, int, int]:
    try:
        channels = tuple(int(channel.strip()) for channel in value.split(","))
    except ValueError as error:
        raise argparse.ArgumentTypeError("RGB must be written as R,G,B") from error
    if len(channels) != 3 or any(channel < 0 or channel > 255 for channel in channels):
        raise argparse.ArgumentTypeError("RGB channels must be integers from 0 to 255")
    return channels


def composite(image: Image.Image, background: tuple[int, int, int]) -> Image.Image:
    backdrop = Image.new("RGBA", image.size, (*background, 255))
    backdrop.alpha_composite(image)
    return backdrop.convert("RGB")


def edge_max_alpha(alpha: Image.Image) -> int:
    width, height = alpha.size
    edge = []
    edge.extend(alpha.crop((0, 0, width, 1)).tobytes())
    edge.extend(alpha.crop((0, height - 1, width, height)).tobytes())
    edge.extend(alpha.crop((0, 0, 1, height)).tobytes())
    edge.extend(alpha.crop((width - 1, 0, width, height)).tobytes())
    return max(edge, default=0)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check a PNG figure's alpha channel and generate contrasting previews."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--require-transparent", action="store_true")
    parser.add_argument("--require-clear-border", action="store_true")
    parser.add_argument("--require-trimmed", action="store_true")
    parser.add_argument("--max-margin", type=int, default=32)
    parser.add_argument("--preview-dir", type=Path)
    parser.add_argument(
        "--background",
        action="append",
        type=parse_rgb,
        dest="backgrounds",
        help="Preview background as R,G,B; may be repeated.",
    )
    args = parser.parse_args()

    if args.max_margin < 0:
        parser.error("--max-margin must be nonnegative")
    if not args.input.is_file():
        parser.error(f"input does not exist: {args.input}")

    image = Image.open(args.input)
    if image.mode != "RGBA":
        if args.require_transparent:
            raise SystemExit(f"FAIL {args.input}: mode is {image.mode}, expected RGBA")
        image = image.convert("RGBA")

    alpha = image.getchannel("A")
    extrema = alpha.getextrema()
    histogram = alpha.histogram()
    transparent = histogram[0]
    opaque = histogram[255]
    visible = alpha.getbbox()
    edge_max = edge_max_alpha(alpha)

    failures: list[str] = []
    if args.require_transparent and (extrema[0] != 0 or transparent == 0):
        failures.append("alpha channel has no fully transparent pixels")
    if args.require_clear_border and edge_max > 3:
        failures.append(f"outer border contains alpha {edge_max}, expected <= 3")
    if args.require_trimmed and visible is not None:
        left, top, right, bottom = visible
        margins = (left, top, image.width - right, image.height - bottom)
        if max(margins) > args.max_margin:
            failures.append(f"visible margins {margins} exceed {args.max_margin}px")
    if visible is None:
        failures.append("no visible content remains")

    print(f"asset: {args.input}")
    print(f"mode: {image.mode} size: {image.width}x{image.height}")
    print(f"alpha_extrema: {extrema} transparent_pixels: {transparent} opaque_pixels: {opaque}")
    print(f"visible_bbox: {visible} edge_max_alpha: {edge_max}")

    backgrounds = args.backgrounds or [(207, 226, 236), (242, 228, 210)]
    if args.preview_dir:
        args.preview_dir.mkdir(parents=True, exist_ok=True)
        stem = args.input.stem
        previews = [composite(image, background) for background in backgrounds]
        width = max(preview.width for preview in previews)
        height = max(preview.height for preview in previews)
        sheet = Image.new("RGB", (width * len(previews), height), (255, 255, 255))
        draw = ImageDraw.Draw(sheet)
        for index, preview in enumerate(previews):
            sheet.paste(preview, (index * width, 0))
            draw.text((index * width + 8, 8), ",".join(map(str, backgrounds[index])), fill=(220, 30, 30))
        output = args.preview_dir / f"{stem}-background-check.png"
        sheet.save(output, format="PNG")
        print(f"preview: {output}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        raise SystemExit(1)
    print("PASS")


if __name__ == "__main__":
    main()
