#!/usr/bin/env bash
set -euo pipefail

project_dir=${1:?Usage: validate_sage_project.sh PROJECT_DIR MAIN.tex}
main_tex=${2:?Usage: validate_sage_project.sh PROJECT_DIR MAIN.tex}
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
  python3 "$project_dir/fetch_random_cover.py" --project-dir "$project_dir"
fi
if [[ ! -s "$project_dir/assets/cover/cover-source.json" ]]; then
  printf 'Missing online cover source record: %s\n' "$project_dir/assets/cover/cover-source.json" >&2
  exit 1
fi

main_path="$project_dir/$main_tex"

python3 "$script_dir/terminology_ledger.py" "$project_dir/terminology.tsv" --check
python3 "$script_dir/terminology_ledger.py" "$project_dir/terminology.tsv" --audit "$project_dir"

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

if [[ -z "$cover_line" || -z "$copyright_line" || -z "$contents_line" ]]; then
  printf 'Main TeX must call \\MakeSageCover, \\MakeSageCopyright, and \\MakeSageContents.\n' >&2
  exit 1
fi
if ! (( cover_line < copyright_line && copyright_line < contents_line )); then
  printf 'Front matter order must be cover, copyright (physical PDF page 2), then contents.\n' >&2
  exit 1
fi

if grep -Eq '\\renewcommand\{\\Sage(ChineseTitle|Author|ChineseEditor|CopyrightDate|SourceLanguage)\}\{(中文标题|作者|中文译制者|中文译制负责人|完成时间|原文语言)\}' "$main_path"; then
  printf 'Template metadata placeholders remain in: %s\n' "$project_dir/$main_tex" >&2
  exit 1
fi

for field in SageAuthor SageChineseEditor SageProductionTool SageCopyrightDate SageSourceLanguage; do
  if ! grep -Eq "\\\\renewcommand\\{\\\\${field}\\}\\{[^}]" "$main_path"; then
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
