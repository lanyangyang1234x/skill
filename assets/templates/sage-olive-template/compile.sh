#!/usr/bin/env bash
set -euo pipefail

main="${1:-template.tex}"

if [[ ! -f "$main" ]]; then
  printf 'Missing main TeX file: %s\n' "$main" >&2
  exit 1
fi

main="$(basename "$main")"
if [[ ! -f "$main" ]]; then
  printf 'Run this script from the project directory containing: %s\n' "$main" >&2
  exit 1
fi

for required in sage-math.sty portable-math-fonts.sty fonts/manifest.json fetch_random_cover.py; do
  if [[ ! -e "$required" ]]; then
    printf 'Missing template dependency: %s\n' "$required" >&2
    exit 1
  fi
done

if [[ ! -s assets/cover/selected-cover.jpg && ! -s assets/cover/selected-cover.png ]]; then
  python3 fetch_random_cover.py
fi

export TFMFONTS="./fonts/math//:${TFMFONTS:-}"

xelatex -interaction=nonstopmode -halt-on-error "$main"
if [[ -s "${main%.tex}.idx" ]]; then
  makeindex -q "${main%.tex}.idx"
fi
xelatex -interaction=nonstopmode -halt-on-error "$main"
xelatex -interaction=nonstopmode -halt-on-error "$main"

base="${main%.tex}"
for ext in aux log out toc synctex.gz fls fdb_latexmk xdv; do
  rm -f "${base}.${ext}"
done

printf 'Built %s\n' "${base}.pdf"
