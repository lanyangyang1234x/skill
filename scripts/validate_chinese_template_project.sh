#!/usr/bin/env bash
set -euo pipefail

if (( $# < 2 )); then
  printf 'Usage: validate_chinese_template_project.sh PROJECT_DIR MAIN.tex [--keep-aux] [--allow-anonymous]\n' >&2
  exit 2
fi
project_dir=$1
main_tex=$2
shift 2
keep_aux=0
allow_anonymous=0
while (( $# )); do
  case "$1" in
    --keep-aux) keep_aux=1 ;;
    --allow-anonymous) allow_anonymous=1 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; exit 2 ;;
  esac
  shift
done
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

for required in "$main_tex" compile.sh .latexmkrc terminology.tsv portable-math-fonts.sty fonts/manifest.json; do
  if [[ ! -e "$project_dir/$required" ]]; then
    printf 'Missing required Chinese Template Project v2 resource: %s\n' "$required" >&2
    exit 1
  fi
done

main_path="$project_dir/$main_tex"

if ! grep -Fq '\documentclass[UTF8,12pt,fontset=none]{ctexart}' "$main_path"; then
  printf 'Chinese Template Project v2 must keep the portable ctexart 12pt fontset=none setting.\n' >&2
  exit 1
fi

python3 "$script_dir/validate_font_bundle.py" "$project_dir" --main "$main_tex"

if grep -Eq '\\(newcommand|renewcommand|providecommand)\{\\Translation(Editor|Tool)\}\{[[:space:]]*(译者姓名|使用模型或工具|工具/模型显示名|模型名称)[[:space:]]*\}' "$main_path"; then
  printf 'Chinese Template Project v2 translator/tool metadata placeholders remain in: %s\n' "$project_dir/$main_tex" >&2
  exit 1
fi
if (( ! allow_anonymous )); then
  for field in TranslationEditor TranslationTool; do
    if ! grep -Eq "\\\\(newcommand|renewcommand|providecommand)\\{\\\\${field}\\}\\{[[:space:]]*[^}[:space:]]" "$main_path"; then
      printf 'Missing or empty translator/tool metadata: \\%s. Use --allow-anonymous only for the user\047s chosen anonymous credit.\n' "$field" >&2
      exit 1
    fi
  done
  if ! grep -Fq '\TranslationCreditLine' "$main_path"; then
    printf 'Chinese Template Project v2 must keep a translation credit line unless the user chose anonymous credit and --allow-anonymous was supplied.\n' >&2
    exit 1
  fi
fi

required_tokens=(
  '\titleformat{\section}[display]'
  '\newenvironment{exercises}'
  '\newenvironment{answers}'
)
for token in "${required_tokens[@]}"; do
  if ! grep -Fq "$token" "$main_path"; then
    printf 'Required Chinese Template Project v2 structure is missing: %s\n' "$token" >&2
    exit 1
  fi
done

# Project v2 does not define a custom bibliography environment. The existing
# bibliography audit checks actual thebibliography/mybibliography ranges;
# sources without a bibliography do not need an invented environment.

sample_tokens=('你好，我是' 'Based on personal study and' 'Notes on Mathematical Studies' 'NOTES ON MATHEMATICAL STUDIES' '\\textsc{Yi Wang}')
for token in "${sample_tokens[@]}"; do
  if grep -Fq "$token" "$main_path"; then
    printf 'Chinese Template Project v2 sample content remains in %s: %s\n' "$main_tex" "$token" >&2
    exit 1
  fi
done

python3 "$script_dir/terminology_ledger.py" "$project_dir/terminology.tsv" --check
python3 "$script_dir/terminology_ledger.py" "$project_dir/terminology.tsv" --audit "$project_dir"

validation_dir="$project_dir/work/validation"
mkdir -p "$validation_dir"
python3 "$script_dir/audit_bibliography.py" "$project_dir" "$main_tex" \
  --require-toc-bibliographies \
  --report "$validation_dir/bibliography-report.json"
if [[ -s "$project_dir/source-manifest.json" ]]; then
  python3 "$script_dir/source_manifest.py" check "$project_dir/source-manifest.json"
fi

has_figures=0
if python3 "$script_dir/project_figure_usage.py" "$project_dir" "$main_tex"; then
  has_figures=1
else
  figure_usage_status=$?
  if (( figure_usage_status != 1 )); then
    exit "$figure_usage_status"
  fi
fi
manifest_has_rows=0
if [[ -s "$project_dir/figure-manifest.tsv" ]] \
    && awk 'NR > 1 && NF { found = 1; exit } END { exit !found }' "$project_dir/figure-manifest.tsv"; then
  manifest_has_rows=1
fi
if (( has_figures && ! manifest_has_rows )); then
  printf 'Detected figure/diagram usage requires figure-manifest.tsv with recorded rows; a missing or header-only manifest is insufficient.\n' >&2
  exit 1
fi
validate_figures=$((has_figures || manifest_has_rows))
if (( validate_figures )); then
  python3 "$script_dir/figure_manifest_ledger.py" \
    "$project_dir/figure-manifest.tsv" --check --require-complete
fi

(
  cd "$project_dir"
  export TFMFONTS="./fonts/math//:${TFMFONTS:-}"
  # Precompile the body before indexing. These fixed passes do not establish
  # pagination convergence; inspect the derived files and continue if needed.
  xelatex -interaction=nonstopmode -halt-on-error "$main_tex"
  xelatex -interaction=nonstopmode -halt-on-error "$main_tex"
  if [[ -s "${main_tex%.tex}.idx" ]]; then
    makeindex -q "${main_tex%.tex}.idx"
  fi
  xelatex -interaction=nonstopmode -halt-on-error "$main_tex"
  xelatex -interaction=nonstopmode -halt-on-error "$main_tex"
)

pdf_name=${main_tex%.tex}.pdf
log_name=${main_tex%.tex}.log
if [[ ! -s "$project_dir/$pdf_name" ]]; then
  printf 'Expected PDF was not generated: %s\n' "$project_dir/$pdf_name" >&2
  exit 1
fi

if (( validate_figures )); then
  python3 "$script_dir/render_figure_page_contacts.py" \
    "$project_dir/$pdf_name" "$project_dir/figure-manifest.tsv" \
    --output-dir "$project_dir/work/figure-page-qa"
fi

python3 "$script_dir/validate_project_fonts.py" "$project_dir/$pdf_name" \
  --log "$project_dir/$log_name" --report "$validation_dir/font-validation.json"

python3 "$script_dir/inspect_build_log.py" \
  "$project_dir/$log_name" "$project_dir/$pdf_name" \
  --report "$validation_dir/validation-report.json"

if (( ! keep_aux )); then
  for ext in aux log out toc synctex.gz fls fdb_latexmk xdv; do
    rm -f "$project_dir/${main_tex%.tex}.$ext"
  done
else
  printf 'Kept build auxiliaries for review: %s/%s.*\n' "$project_dir" "${main_tex%.tex}"
fi

printf 'Template/build checks passed: %s. Fixed passes do not prove pagination or index stability.\n' "$project_dir/$pdf_name"
