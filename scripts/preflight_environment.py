#!/usr/bin/env python3
"""Check the core and optional OCR environment for PDF conversion."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def module_version(module_name: str) -> tuple[bool, str]:
    try:
        module = __import__(module_name)
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    version = getattr(module, "__version__", None)
    if module_name == "fitz" and hasattr(module, "version"):
        version = module.version[0]
    return True, str(version or "available")


def probe_ocr_python(candidate: Path) -> tuple[bool, str]:
    if not candidate.is_file():
        return False, f"not found: {candidate}"
    probe_env = os.environ.copy()
    try:
        with tempfile.TemporaryDirectory(prefix="pdf-to-chinese-tex-paddlex-") as cache_dir:
            # PaddleOCR initializes PaddleX at import time and may otherwise
            # create ~/.paddlex. Keep this read-only probe sandbox-friendly.
            probe_env.setdefault("PADDLE_PDX_CACHE_HOME", cache_dir)
            result = subprocess.run(
                [
                    str(candidate),
                    "-c",
                    "import paddle, paddleocr; "
                    "print('paddle=' + paddle.__version__ + '; paddleocr=' + getattr(paddleocr, '__version__', 'available'))",
                ],
                capture_output=True,
                text=True,
                env=probe_env,
                timeout=60,
            )
    except subprocess.TimeoutExpired:
        return False, "OCR import probe timed out after 60 seconds"
    if result.returncode != 0:
        lines = (result.stderr or result.stdout).strip().splitlines()
        return False, lines[-1] if lines else "OCR import probe failed"
    return True, result.stdout.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check PDF-to-Chinese-TeX dependencies")
    parser.add_argument("--require-ocr", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fitz_ok, fitz_detail = module_version("fitz")
    commands = {name: shutil.which(name) for name in ("xelatex", "pdftoppm", "pdftotext")}
    configured = os.environ.get("PDF_TO_CHINESE_TEX_OCR_PYTHON")
    ocr_python = Path(configured).expanduser() if configured else Path.home() / ".codex/venvs/pdf-to-chinese-tex-ocr/bin/python"
    ocr_ok, ocr_detail = probe_ocr_python(ocr_python)

    report = {
        "python": {"ok": sys.version_info >= (3, 9), "version": sys.version.split()[0], "path": sys.executable},
        "pymupdf": {"ok": fitz_ok, "detail": fitz_detail},
        "xelatex": {"ok": bool(commands["xelatex"]), "path": commands["xelatex"]},
        "pdftoppm": {"ok": bool(commands["pdftoppm"]), "path": commands["pdftoppm"]},
        "pdftotext": {"ok": bool(commands["pdftotext"]), "path": commands["pdftotext"], "required": False},
        "ocr": {"ok": ocr_ok, "python": str(ocr_python), "detail": ocr_detail, "required": args.require_ocr},
    }
    core_ok = all(report[name]["ok"] for name in ("python", "pymupdf", "xelatex", "pdftoppm"))
    success = core_ok and (ocr_ok or not args.require_ocr)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for name, info in report.items():
            status = "OK" if info["ok"] else "MISSING"
            detail = info.get("detail") or info.get("version") or info.get("path") or ""
            print(f"{status:7} {name:10} {detail}")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
