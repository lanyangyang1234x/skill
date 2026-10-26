# Chinese Template Project v2

Use `assets/templates/chinese-template-project-v2/` after the user selects the
layout used by the extriangulated-category/Hovey project: A4 geometry, the
burgundy/gold chapter label, Chinese theorem names, clickable contents,
exercise/answer links, metadata credit line, and source-relative figure
insertion.

This template is a reusable presentation layer only. Do not copy the source
book's title, authors, abstract, bibliography, notation macros, figures, or
section files into a new project. Replace the metadata placeholders in
`template.tex`, then add translated content using a suitable chapter/section organization; serial work may keep a single main file.

Copy `portable-math-fonts.sty`, `chinese-headings.sty` and the whole `fonts/` directory, including the manifest, Noto Serif CJK SC SemiBold font and its OFL. Keep `fontset=none` and explicit project-relative mapping; the template must not fall back to a machine's CJK fonts. Follow [font-policy.md](font-policy.md): Song for body/proofs/examples, Fang for theorem statements, Kai for terms, Noto Serif CJK SC SemiBold (600) for interior Chinese headings, CMU Serif Bold for Latin headings/numbers, and Song Bold for editorial-note titles. Keep Computer Modern/AMS/RSFS mathematics, 12pt body and 1.3 line spacing.

The Chinese `template.tex` explicitly loads `\usepackage[chinese]{chinese-headings}` after the shared font style. Environment names and numbers align to corresponding upright body-font `设` (Fang or Song Regular); preserve native CJKglue, font sizes, numbering content and formulas instead of applying a fixed offset or freezing the whole name in a box. This sidecar is a no-op by default or with `[english]`; English or other non-Chinese source-language-preserving tasks must not enable `[chinese]` or change the shared `portable-math-fonts.sty` and Latin typography. This update applies only to new Chinese projects or authorized migrations. Inspect the final roles and embedding while preserving the selected cover, colors and geometry.

For diagrams follow [book-completion-and-figure-qa.md](book-completion-and-figure-qa.md): native TikZ/TikZ-CD is preferred, and an explicit native requirement must also match the original label positions, geometry and arrow styles. Never substitute screenshots for a required native drawing. Source-pixel-locked crops or label-only layers remain available when the task requires those pixels and no native method is required.

Validate matching projects with `scripts/validate_chinese_template_project.sh PROJECT MAIN.tex [--keep-aux] [--allow-anonymous]`. Anonymous credit may omit/clear the translator/tool display according to the project choice; remove sample values and inspect the final visible credit. A bibliography is checked when actually present; the template does not require an invented `mybibliography` environment. The validator runs two body passes before indexing and two after; continue if derived references are not stable.
