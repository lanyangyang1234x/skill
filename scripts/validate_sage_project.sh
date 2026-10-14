#!/usr/bin/env bash
set -euo pipefail

if (( $# < 2 )); then
  printf 'Usage: validate_sage_project.sh PROJECT_DIR MAIN.tex [--keep-aux] [--allow-anonymous] [--without-contents]\n' >&2
  exit 2
fi
project_dir=$1
main_tex=$2
shift 2
keep_aux=0
allow_anonymous=0
without_contents=0
while (( $# )); do
  case "$1" in
    --keep-aux) keep_aux=1 ;;
    --allow-anonymous) allow_anonymous=1 ;;
    --without-contents) without_contents=1 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; exit 2 ;;
  esac
  shift
done
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

required=(
  "$main_tex"
  terminology.tsv
  sage-math.sty
  .latexmkrc
  compile.sh
  fetch_random_cover.py
  fonts/FandolFang-Regular.otf
  fonts/FandolHei-Regular.otf
  fonts/FandolKai-Regular.otf
  fonts/FandolSong-Bold.otf
  fonts/FandolSong-Regular.otf
  fonts/LibertinusMono-Regular.otf
  fonts/LibertinusSans-Bold.otf
  fonts/LibertinusSans-Italic.otf
  fonts/LibertinusSans-Regular.otf
  fonts/LibertinusSerif-Bold.otf
  fonts/LibertinusSerif-BoldItalic.otf
  fonts/LibertinusSerif-Italic.otf
  fonts/LibertinusSerif-Regular.otf
)

for required in "${required[@]}"; do
  if [[ ! -e "$project_dir/$required" ]]; then
    printf 'Missing required template resource: %s\n' "$required" >&2
    exit 1
  fi
done

if [[ ! -s "$project_dir/assets/cover/selected-cover.jpg" && ! -s "$project_dir/assets/cover/selected-cover.png" ]]; then
  printf 'Missing frozen Sage-Olive cover asset: %s/assets/cover/selected-cover.jpg or .png. Initialize the selected cover before validation; this validator does not download assets or update cover history.\n' "$project_dir" >&2
  exit 1
fi
if [[ ! -s "$project_dir/assets/cover/cover-source.json" ]]; then
  printf 'Missing online cover source record: %s\n' "$project_dir/assets/cover/cover-source.json" >&2
  exit 1
fi

main_path="$project_dir/$main_tex"

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

font_commands=(
  setmainfont
  setsansfont
  setmonofont
  setCJKmainfont
  setCJKsansfont
  setCJKmonofont
)

for command in "${font_commands[@]}"; do
  count=$(grep -Ec "^[[:space:]]*\\\\${command}(\\[|\\{)" "$main_path" || true)
  if [[ "$count" -ne 1 ]]; then
    printf 'The fixed Sage-Olive typography requires exactly one \\%s declaration; found %s.\n' "$command" "$count" >&2
    exit 1
  fi
done

font_tokens=(
  'UprightFont={LibertinusSerif-Regular.otf}'
  'ItalicFont={LibertinusSerif-Italic.otf}'
  'BoldFont={LibertinusSerif-Bold.otf}'
  'BoldItalicFont={LibertinusSerif-BoldItalic.otf}'
  'UprightFont={LibertinusSans-Regular.otf}'
  'ItalicFont={LibertinusSans-Italic.otf}'
  'BoldFont={LibertinusSans-Bold.otf}'
  '\setmonofont[Path=fonts/]{LibertinusMono-Regular.otf}'
  'UprightFont={FandolSong-Regular.otf}'
  'BoldFont={FandolSong-Bold.otf}'
  'ItalicFont={FandolKai-Regular.otf}'
  'UprightFont={FandolHei-Regular.otf}'
  'BoldFont={FandolHei-Regular.otf}'
  'ItalicFont={FandolHei-Regular.otf}'
  'BoldItalicFont={FandolHei-Regular.otf}'
  '\setCJKmonofont[Path=fonts/]{FandolFang-Regular.otf}'
)

for token in "${font_tokens[@]}"; do
  if ! grep -Fq "$token" "$main_path"; then
    printf 'Required Sage-Olive font mapping is missing or changed: %s\n' "$token" >&2
    exit 1
  fi
done

if ! grep -Fq '\setkomafont{section}{\sffamily' "$project_dir/sage-math.sty" \
    || ! grep -Fq '\setkomafont{subsection}{\sffamily' "$project_dir/sage-math.sty" \
    || ! grep -Fq '\sffamily\fontsize{38pt}{47pt}\selectfont\bfseries\SageChineseTitle' "$project_dir/sage-math.sty"; then
  printf 'Sage-Olive headings and cover title must use the bundled sans families (FandolHei / Libertinus Sans).\n' >&2
  exit 1
fi

cover_line=$(grep -nF '\MakeSageCover' "$main_path" | head -n 1 | cut -d: -f1 || true)
copyright_line=$(grep -nF '\MakeSageCopyright' "$main_path" | head -n 1 | cut -d: -f1 || true)
contents_line=$(grep -nF '\MakeSageContents' "$main_path" | head -n 1 | cut -d: -f1 || true)

if [[ -z "$cover_line" || -z "$copyright_line" ]]; then
  printf 'Main TeX must call \\MakeSageCover and \\MakeSageCopyright.\n' >&2
  exit 1
fi
if ! (( cover_line < copyright_line )); then
  printf 'Front matter order must be cover, then copyright.\n' >&2
  exit 1
fi
if [[ -z "$contents_line" ]] && (( ! without_contents )); then
  printf 'Main TeX must call \\MakeSageContents unless the user chose no contents and --without-contents was supplied.\n' >&2
  exit 1
fi
if [[ -n "$contents_line" ]] && ! (( copyright_line < contents_line )); then
  printf 'Contents, when present, must follow the cover and copyright page.\n' >&2
  exit 1
fi

if grep -Eq '\\renewcommand\{\\Sage(ChineseTitle|Author|ChineseEditor|ProductionTool|CopyrightDate|SourceLanguage)\}\{[[:space:]]*(中文标题|作者|中文译制者|中文译制负责人|译者姓名|使用模型或工具|工具/模型显示名|完成时间|原文语言)[[:space:]]*\}' "$main_path" \
    || grep -Eq '\\renewcommand\{\\SageEnglishTitle\}\{(ENGLISH TITLE|English Title)\}' "$main_path"; then
  printf 'Template metadata placeholders remain in: %s\n' "$project_dir/$main_tex" >&2
  exit 1
fi

if grep -Eiq '\\(MakeUppercase|uppercase|MakeLowercase|lowercase|textsc|scshape)[^[:cntrl:]]*Sage(EnglishTitle|ChineseTitle|Author|EditionLine|ScopeLine)' "$main_path" \
    || grep -Eiq 'Sage(EnglishTitle|ChineseTitle|Author|EditionLine|ScopeLine)[^[:cntrl:]]*\\(MakeUppercase|uppercase|MakeLowercase|lowercase|textsc|scshape)' "$main_path"; then
  printf 'Source-derived Sage metadata must not be placed inside a case-transforming or small-caps command. Restore the source case explicitly: %s\n' "$project_dir/$main_tex" >&2
  exit 1
fi

metadata_fields=(SageAuthor SageCopyrightDate SageSourceLanguage)
if (( allow_anonymous )); then
  for field in SageChineseEditor SageProductionTool; do
    if ! grep -Eq "^[[:space:]]*\\\\renewcommand\\{\\\\${field}\\}\\{[^}]*\\}" "$main_path"; then
      printf 'Anonymous credit requires an explicit \\%s override ({} is allowed); omitted declarations can inherit sample credit from sage-math.sty.\n' "$field" >&2
      exit 1
    fi
  done
else
  metadata_fields+=(SageChineseEditor SageProductionTool)
fi
for field in "${metadata_fields[@]}"; do
  if ! grep -Eq "\\\\renewcommand\\{\\\\${field}\\}\\{[[:space:]]*[^}[:space:]]" "$main_path"; then
    printf 'Missing or empty copyright metadata: \\%s\n' "$field" >&2
    exit 1
  fi
done

if grep -Eqi '\\renewcommand\{\\SageChineseEditor\}\{[^}]*(OpenAI|Codex|ChatGPT|GPT-)' "$main_path"; then
  printf 'The responsible human contributor must be stored in \\SageChineseEditor; put the automation tool in \\SageProductionTool.\n' >&2
  exit 1
fi

while IFS= read -r theorem_env; do
  [[ -z "$theorem_env" ]] && continue
  if ! grep -Fq "\\SageStyleEnvironment{$theorem_env}" "$main_path" \
      && ! grep -Fq "\\SageStyleEnvironment{$theorem_env}" "$project_dir/sage-math.sty"; then
    printf 'Theorem-like environment %s has no Sage-Olive style registration. Add \\SageStyleEnvironment{%s}{COLOR}{TINT}.\n' \
      "$theorem_env" "$theorem_env" >&2
    exit 1
  fi
done < <(sed -nE 's/^[[:space:]]*\\newtheorem\*?\{([^}]*)\}.*/\1/p' "$main_path" | sort -u)

if grep -REq --include='*.tex' '\\begin\{figure\*?\}' "$project_dir"; then
  if ! grep -Fq '\g@addto@macro\@floatboxreset{\centering}' "$main_path" \
      && ! grep -Fq '\g@addto@macro\@floatboxreset{\centering}' "$project_dir/sage-math.sty"; then
    printf 'Figure environments require post-reset centering through \\g@addto@macro\\@floatboxreset{\\centering}; environment-begin hooks are insufficient for [H] figures.\n' >&2
    exit 1
  fi
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
