# Chinese Template Reference

Use this template only after the user selects `Chinese Template`.

## Required Files

Copy the whole directory into the output project:

```text
assets/templates/chinese-template/
  template.tex
  compile.sh
  .latexmkrc
```

Initialize `terminology.tsv` before validation. If the project contains any raster or TeX-native figure/diagram, also initialize and complete `figure-manifest.tsv` with `scripts/figure_manifest_ledger.py`.

## Required Adaptation

- Preserve the chapter-style section headings, customized contents, theorem and proof styling, exercise/answer links, appendix behavior, bibliography environment, and title-page geometry.
- Replace the sample title-page metadata, preface, body, exercises, answers, appendices, and bibliography with source-derived content. Do not leave example sentences such as `你好，我是...` in the deliverable.
- Keep `\documentclass[UTF8,12pt,fontset=fandol]{ctexart}` so the template does not depend on unavailable macOS `STHeiti` fonts.
- Preserve the template's visible English labels (`Chapter`, `Appendix`, theorem names, `Proof`, and `Exercise`) unless the user asks to localize them.
- Add packages only when required by the source. Do not change the presentation layer merely to simplify reconstruction.
- Preserve source numbering when it conflicts with the template's sample numbering; fidelity to the source takes precedence over the sample document.

## Build and QA

Run `./compile.sh MAIN.tex`, then `scripts/validate_chinese_template_project.sh PROJECT_DIR MAIN.tex`. The validator checks and audits terminology, requires a complete figure manifest when figures exist, compiles the project, and renders figure-page contact sheets when applicable.
Inspect the title page, contents, a chapter-opening page, theorem/proof pages, exercise/answer links when present, figure pages, appendices, bibliography, and final page.
