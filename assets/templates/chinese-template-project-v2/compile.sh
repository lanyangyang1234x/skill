#!/usr/bin/env bash
set -euo pipefail

main_tex=${1:-template.tex}

xelatex -interaction=nonstopmode -halt-on-error "$main_tex"
xelatex -interaction=nonstopmode -halt-on-error "$main_tex"
xelatex -interaction=nonstopmode -halt-on-error "$main_tex"

printf 'Built: %s\n' "${main_tex%.tex}.pdf"
