#!/usr/bin/env bash
set -euo pipefail

project_dir=${1:?Usage: validate_chinese_template_project.sh PROJECT_DIR MAIN.tex}
main_tex=${2:?Usage: validate_chinese_template_project.sh PROJECT_DIR MAIN.tex}
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

for required in "$main_tex" compile.sh .latexmkrc terminology.tsv; do
  if [[ ! -e "$project_dir/$required" ]]; then
    printf 'Missing required Chinese Template resource: %s\n' "$required" >&2
    exit 1
  fi
done

main_path="$project_dir/$main_tex"

if ! grep -Fq '\documentclass[UTF8,12pt,fontset=fandol]{ctexart}' "$main_path"; then
  printf 'Chinese Template must keep the portable ctexart Fandol font setting.\n' >&2
  exit 1
fi

if grep -Eq '\\newcommand\{\\Translation(Editor|Tool)\}\{(译者姓名|使用模型或工具)\}' "$main_path"; then
  printf 'Chinese Template translator/tool metadata placeholders remain in: %s\n' "$project_dir/$main_tex" >&2
  exit 1
fi
if ! grep -Fq '\TranslationCreditLine' "$main_path"; then
  printf 'Chinese Template must keep a visible translation credit line.\n' >&2
  exit 1
fi

required_tokens=(
  '\titleformat{\section}[display]'
  '\newenvironment{exercises}'
  '\newenvironment{answers}'
  '\newenvironment{mybibliography}'
)
for token in "${required_tokens[@]}"; do
  if ! grep -Fq "$token" "$main_path"; then
    printf 'Required Chinese Template structure is missing: %s\n' "$token" >&2
    exit 1
  fi
done

sample_tokens=('你好，我是' 'Based on personal study and' 'Notes on Mathematical Studies' 'NOTES ON MATHEMATICAL STUDIES' '\\textsc{Yi Wang}')
for token in "${sample_tokens[@]}"; do
  if grep -Fq "$token" "$main_path"; then
    printf 'Chinese Template sample content remains in %s: %s\n' "$main_tex" "$token" >&2
    exit 1
  fi
done

python3 "$script_dir/terminology_ledger.py" "$project_dir/terminology.tsv" --check
python3 "$script_dir/terminology_ledger.py" "$project_dir/terminology.tsv" --audit "$project_dir"

if grep -REq --include='*.tex' '\\includegraphics|\\begin\{(tikzpicture|tikzcd)\}' "$project_dir"; then
  if [[ ! -s "$project_dir/figure-manifest.tsv" ]]; then
    printf 'Figure-bearing project is missing figure-manifest.tsv\n' >&2
    exit 1
  fi
fi
if [[ -s "$project_dir/figure-manifest.tsv" ]]; then
  python3 "$script_dir/figure_manifest_ledger.py" \
    "$project_dir/figure-manifest.tsv" --check --require-complete
fi

(
  cd "$project_dir"
  ./compile.sh "$main_tex"
)

pdf_name=${main_tex%.tex}.pdf
log_name=${main_tex%.tex}.log
if [[ ! -s "$project_dir/$pdf_name" ]]; then
  printf 'Expected PDF was not generated: %s\n' "$project_dir/$pdf_name" >&2
  exit 1
fi

if [[ -s "$project_dir/figure-manifest.tsv" ]]; then
  python3 "$script_dir/render_figure_page_contacts.py" \
    "$project_dir/$pdf_name" "$project_dir/figure-manifest.tsv" \
    --output-dir "$project_dir/work/figure-page-qa"
fi

if grep -Eqi '(^!|LaTeX Error|Package .* Error|Undefined control sequence|font .* not found|cannot find.*font|There were undefined references|Rerun to get cross-references right|Overfull)' "$project_dir/$log_name"; then
  printf 'Build completed, but the log contains warnings requiring review: %s\n' "$project_dir/$log_name" >&2
  exit 1
fi

for ext in aux log out toc synctex.gz fls fdb_latexmk xdv; do
  rm -f "$project_dir/${main_tex%.tex}.$ext"
done

printf 'Validated: %s\n' "$project_dir/$pdf_name"
