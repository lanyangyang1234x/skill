#!/usr/bin/env python3
"""Check only the dependencies needed for the requested PDF/TeX task.

The default check is deliberately non-invasive: it verifies Python and does
not import PyMuPDF or probe/install an OCR environment. Ask for the capabilities
that the current stage actually needs with ``--need-pdf``, ``--need-render``,
``--need-compile`` or ``--require-ocr``.
"""

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
        if module_name == "fitz":
            try:
                module = __import__("pymupdf")
            except Exception:
                module = __import__("fitz")
        else:
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
    parser.add_argument(
        "--need-pdf",
        action="store_true",
        help="Require PyMuPDF for PDF inspection/extraction",
    )
    parser.add_argument(
        "--need-render",
        action="store_true",
        help="Require pdftoppm for page rendering/crops",
    )
    parser.add_argument(
        "--need-compile",
        action="store_true",
        help="Require XeLaTeX for compilation",
    )
    parser.add_argument(
        "--require-ocr",
        action="store_true",
        help="Require the explicitly configured/bootstrapped OCR environment (opt-in)",
    )
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    need_pdf = args.need_pdf or args.require_ocr
    need_render = args.need_render or args.require_ocr
    need_compile = args.need_compile

    if need_pdf:
        fitz_ok, fitz_detail = module_version("fitz")
    else:
        fitz_ok, fitz_detail = None, "not checked (PDF inspection not requested)"

    commands = {name: shutil.which(name) for name in ("xelatex", "pdftoppm", "pdftotext")}
    if args.require_ocr:
        configured = os.environ.get("PDF_TO_CHINESE_TEX_OCR_PYTHON")
        codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
        ocr_python = (
            Path(configured).expanduser()
            if configured
            else codex_home / "venvs/pdf-to-chinese-tex-ocr/bin/python"
        )
        ocr_ok, ocr_detail = probe_ocr_python(ocr_python)
    else:
        ocr_python = None
        ocr_ok, ocr_detail = None, "not checked (OCR is opt-in)"

    report = {
        "python": {"ok": sys.version_info >= (3, 9), "version": sys.version.split()[0], "path": sys.executable},
        "pymupdf": {"ok": fitz_ok, "detail": fitz_detail, "required": need_pdf, "skipped": not need_pdf},
        "xelatex": {
            "ok": bool(commands["xelatex"]) if need_compile else None,
            "path": commands["xelatex"],
            "required": need_compile,
            "skipped": not need_compile,
        },
        "pdftoppm": {
            "ok": bool(commands["pdftoppm"]) if need_render else None,
            "path": commands["pdftoppm"],
            "required": need_render,
            "skipped": not need_render,
        },
        "pdftotext": {
            "ok": bool(commands["pdftotext"]),
            "path": commands["pdftotext"],
            "required": False,
            "skipped": True,
        },
        "ocr": {
            "ok": ocr_ok,
            "python": str(ocr_python) if ocr_python else None,
            "detail": ocr_detail,
            "required": args.require_ocr,
            "skipped": not args.require_ocr,
        },
    }
    required_checks = [report["python"]["ok"]]
    if need_pdf:
        required_checks.append(bool(fitz_ok))
    if need_render:
        required_checks.append(bool(commands["pdftoppm"]))
    if need_compile:
        required_checks.append(bool(commands["xelatex"]))
    if args.require_ocr:
        required_checks.append(bool(ocr_ok))
    success = all(required_checks)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for name, info in report.items():
            if info.get("skipped"):
                status = "SKIP"
            else:
                status = "OK" if info["ok"] else "MISSING"
            detail = info.get("detail") or info.get("version") or info.get("path") or ""
            print(f"{status:7} {name:10} {detail}")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
