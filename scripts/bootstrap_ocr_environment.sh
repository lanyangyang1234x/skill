#!/usr/bin/env bash
set -euo pipefail

codex_root="${CODEX_HOME:-$HOME/.codex}"
ocr_venv="${1:-$codex_root/venvs/pdf-to-chinese-tex-ocr}"

if [[ -z "$ocr_venv" || "$ocr_venv" == "/" || "$ocr_venv" == "$HOME" ]]; then
  printf 'Refusing unsafe virtual environment path: %s\n' "$ocr_venv" >&2
  exit 2
fi

python3 -m venv "$ocr_venv"
"$ocr_venv/bin/python" -m pip install --upgrade pip setuptools wheel
"$ocr_venv/bin/python" -m pip install \
  "paddlepaddle==3.3.1" \
  "paddleocr==3.7.0"
mkdir -p "$ocr_venv/.paddlex-cache"
PADDLE_PDX_CACHE_HOME="$ocr_venv/.paddlex-cache" "$ocr_venv/bin/python" -c \
  "import paddle, paddleocr; print('paddle=' + paddle.__version__ + '; paddleocr=' + paddleocr.__version__)"

printf 'OCR environment ready: %s\n' "$ocr_venv"
