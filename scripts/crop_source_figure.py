#!/usr/bin/env python3
"""Crop a high-resolution PDF render and prepare a figure-only PNG."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops
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


def dominant_near_white(image: Image.Image) -> int:
    """Return the dominant light channel value for a monochrome page scan."""
    histogram = image.convert("L").histogram()
    candidates = range(220, 256)
    return max(candidates, key=lambda value: histogram[value])


def parse_rgb(value: str) -> tuple[int, int, int]:
    try:
        channels = tuple(int(channel.strip()) for channel in value.split(","))
    except ValueError as error:
        raise argparse.ArgumentTypeError("RGB must be written as R,G,B") from error
    if len(channels) != 3 or any(channel < 0 or channel > 255 for channel in channels):
        raise argparse.ArgumentTypeError("RGB channels must be integers from 0 to 255")
    return channels


def visible_alpha(image: Image.Image, low: int, high: int) -> Image.Image:
    """Build an antialiased foreground alpha mask from a near-white background."""
    luminance = image.convert("RGB").convert("L")
    span = high - low
    return luminance.point(
        lambda value: 255
        if value <= low
        else 0
        if value >= high
        else round((high - value) * 255 / span)
    )


def trim_to_visible(image: Image.Image, padding: int, background: tuple[int, int, int]) -> Image.Image:
    if image.mode == "RGBA":
        box = image.getchannel("A").getbbox()
    else:
        backdrop = Image.new("RGB", image.size, background)
        box = ImageChops.difference(image.convert("RGB"), backdrop).getbbox()
    if box is None:
        raise SystemExit("No visible figure content remains after background processing")
    left, top, right, bottom = box
    return image.crop(
        (
            max(0, left - padding),
            max(0, top - padding),
            min(image.width, right + padding),
            min(image.height, bottom + padding),
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Crop a figure-only region from a high-resolution PDF page render, "
            "optionally remove its near-white background, and trim unused canvas."
        )
    )
    parser.add_argument("input", type=Path, help="Rendered source page image")
    parser.add_argument("output", type=Path, help="Lossless PNG output")
    parser.add_argument("left", type=int)
    parser.add_argument("top", type=int)
    parser.add_argument("right", type=int)
    parser.add_argument("bottom", type=int)
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Allow replacing an existing output. Use only for an explicitly "
            "versioned, unverified run; never use this on a promoted release asset."
        ),
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=540,
        help="DPI metadata for the cropped PNG (default: 540)",
    )
    background = parser.add_mutually_exclusive_group()
    background.add_argument(
        "--transparent-background",
        action="store_true",
        help="Map the near-white page background to antialiased transparency",
    )
    background.add_argument(
        "--background-rgb",
        type=parse_rgb,
        metavar="R,G,B",
        help="Flatten the near-white page background to this document background color",
    )
    parser.add_argument(
        "--trim-visible",
        action="store_true",
        help="Crop unused canvas to visible content bounds after background processing",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=8,
        help="Pixels retained around visible content with --trim-visible (default: 8)",
    )
    parser.add_argument(
        "--threshold-low",
        type=int,
        default=235,
        help="Pixels at or below this luminance remain fully opaque (default: 235)",
    )
    parser.add_argument(
        "--threshold-high",
        type=int,
        default=250,
        help="Pixels at or above this luminance become background (default: 250)",
    )
    parser.add_argument(
        "--white-point",
        type=int,
        help=(
            "Near-white RGB value to map to 255. By default, infer the "
            "dominant value from the cropped monochrome image."
        ),
    )
    args = parser.parse_args()

    if not (args.left < args.right and args.top < args.bottom):
        parser.error("crop coordinates must satisfy left < right and top < bottom")
    if not 1 <= args.dpi <= 2400:
        parser.error("--dpi must be between 1 and 2400")
    if args.padding < 0:
        parser.error("--padding must be nonnegative")
    if not 0 <= args.threshold_low < args.threshold_high <= 255:
        parser.error("thresholds must satisfy 0 <= low < high <= 255")

    image = Image.open(args.input).convert("RGB")
    width, height = image.size
    if not (
        0 <= args.left < args.right <= width
        and 0 <= args.top < args.bottom <= height
    ):
        parser.error(f"crop box exceeds image bounds {width}x{height}")

    crop = image.crop((args.left, args.top, args.right, args.bottom))
    white_point = args.white_point or dominant_near_white(crop)
    if not 220 <= white_point <= 255:
        parser.error("--white-point must be between 220 and 255")

    # Preserve black strokes and the antialiasing ramp while mapping the
    # scanned page's nominal background to the target document's RGB 255.
    table = [
        min(255, round(value * 255 / white_point))
        for value in range(256)
    ]
    crop = crop.point(table * 3)

    alpha = visible_alpha(crop, args.threshold_low, args.threshold_high)
    output_background = (255, 255, 255)
    if args.transparent_background:
        crop = crop.convert("RGBA")
        crop.putalpha(ImageChops.darker(crop.getchannel("A"), alpha))
    elif args.background_rgb is not None:
        output_background = args.background_rgb
        foreground = crop.convert("RGBA")
        foreground.putalpha(alpha)
        backdrop = Image.new("RGBA", crop.size, (*args.background_rgb, 255))
        crop = Image.alpha_composite(backdrop, foreground).convert("RGB")

    if args.trim_visible:
        crop = trim_to_visible(crop, args.padding, output_background)

    if args.output.exists() and not args.force:
        raise SystemExit(
            f"Refusing to overwrite existing crop: {args.output}. "
            "Write to a new run directory or pass --force only for an explicit "
            "versioned regeneration."
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    crop.save(args.output, format="PNG", dpi=(args.dpi, args.dpi), optimize=True)


if __name__ == "__main__":
    main()
