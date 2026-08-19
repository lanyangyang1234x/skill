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
- The title page must replace all sample metadata with source-derived original title, author, edition/publication information, translator/editor, translation or retypesetting tool/model, and update/completion time. If the cover has a lower-right publisher block, add a translator line such as “译者 翻译及重排”.
- Replace `\TranslationEditor` and `\TranslationTool` with the two values collected immediately after template selection, and keep `\TranslationCreditLine` visible on the title page or front matter. The line should read naturally, for example: `本中文译本由张三使用 Google Antigravity 完成。`
- Preserve source-derived Latin-script capitalization in any English title, subtitle, label, or credit line. Do not convert it to all caps just because the template sample uses uppercase styling elsewhere.
- The chapter marker's `\scshape` styling for the template labels `Chapter`/`Appendix` is presentation-only. Replace source-derived title and author samples with `\normalfont\upshape` text unless the source itself uses small caps.
- Replace the sample title-page metadata, preface, body, exercises, answers, appendices, and bibliography with source-derived content. Do not leave example sentences such as `你好，我是...` in the deliverable.
- Keep `\documentclass[UTF8,12pt,fontset=fandol]{ctexart}` so the template does not depend on unavailable macOS `STHeiti` fonts.
- Preserve the template's visible English labels (`Chapter`, `Appendix`, theorem names, `Proof`, and `Exercise`) unless the user asks to localize them.
- Add packages only when required by the source. Do not change the presentation layer merely to simplify reconstruction.
- Preserve source numbering when it conflicts with the template's sample numbering; fidelity to the source takes precedence over the sample document.
- Implement references with `\\label`, `\\ref`/`\\autoref`, and `\\eqref`; never replace a source cross-reference with a hard-coded translated number. Adjust counters or theorem environments so displayed numbers match the source edition.
- Keep the bundled portable font setup. Use Chinese body text, theorem-style labels, and English serif text according to the template's existing font declarations; do not introduce unavailable macOS fonts merely to imitate a screenshot.
- Keep a visible but restrained vertical transition between preface/front matter and the first numbered chapter.

## Build and QA

Run `./compile.sh MAIN.tex`, then `scripts/validate_chinese_template_project.sh PROJECT_DIR MAIN.tex`. The validator checks and audits terminology, requires a complete figure manifest when figures exist, compiles the project, and renders figure-page contact sheets when applicable.
Inspect the title page, contents, a chapter-opening page, theorem/proof pages, exercise/answer links when present, figure pages, appendices, bibliography, and final page. Verify link colors and behavior: `MidnightBlue` for internal/URL links, `BrickRed` for bibliography links, clickable contents titles and page numbers, and no visible link borders.
