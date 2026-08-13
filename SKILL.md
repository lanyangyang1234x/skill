---
name: pdf-to-chinese-tex
description: "Faithfully convert mathematical PDFs and accompanying Markdown transcriptions into Chinese LaTeX/PDF after asking the user to choose between the bundled Sage-Olive and Chinese Template layouts; edit an existing Markdown source in place, use OCR only when needed, and apply evidence-backed terminology, coverage and figure ledgers, and source-verified fidelity."
---

# PDF to Chinese TeX

Use this skill to produce a faithful Chinese LaTeX/PDF edition of a mathematical PDF with a user-selected bundled template.

## Template Selection — First Action

- At the start of every new translation task, before inspecting the source, preprocessing it, or creating output files, ask the user to choose `Sage-Olive` or `Chinese Template`.
- Always ask again for each new translation task; do not reuse an earlier task's choice or assume a standing preference.
- Do not begin translation work until the user answers the template question.
- Keep the selected template for the whole project unless the user asks to change it.

## Rules

- Preserve source order, numbering, notation, formulas, labels, citations, and figure geometry.
- Translate specialized terms into Chinese; keep personal names in the source spelling.
- When the task includes an associated Markdown file, edit that exact file in place as the primary text scaffold. Do not create a duplicate Markdown translation or regenerate text already present there.
- If more than one Markdown file could be the source, identify the correct file from explicit task context; if ambiguity remains, ask before editing. Never choose by filename guesswork.
- Use the PDF as the authority to correct and complete the Markdown; extract or OCR only passages, formulas, labels, or structure that the Markdown omits or garbles.
- For `Sage-Olive`, keep its random landscape cover and bundled Fandol/Libertinus typography unchanged.
- For `Chinese Template`, preserve its `ctexart` chapter-title, contents, theorem, exercise/answer, appendix, bibliography, and title-page structure; keep `fontset=fandol` for portable compilation.
- For source-cropped figures, preserve high resolution, transparent background, and source-relative displayed size; a visible white rectangle or undersized crop on the compiled page fails QA.
- Transparency must be real alpha transparency with no opaque white canvas, halo, or white-pixel substitute; verify it on a non-white background and in the compiled PDF.
- A figure crop must contain only the target figure and integral in-figure labels; any unrelated prose, formula, caption, header, footer, page number, or neighboring artwork fails QA.
- Inventory every ordinary English label inside a figure and replace it with Chinese; do not leave English legends, axis labels, annotations, or in-figure captions untranslated.
- For exact-appearance figure requests, preserve source pixels and geometry; do not approximate it with hand-tuned TikZ.
- Do not summarize, modernize, overlay, or replace the source PDF with translated text.
- For books, preserve hierarchy and order; do not invent chapter boundaries or drop front/back matter.
- If the source is unreadable, the structure is unclear, or a requested layout would force material simplification, stop and ask before changing strategy.
- Treat compilation success and source fidelity as separate checks.

## Read These References

- `references/source-extraction.md` for extraction and OCR.
- `references/terminology-policy.md` for terminology.
- `references/sage-olive-template.md` when the user selects `Sage-Olive`.
- `references/chinese-template.md` when the user selects `Chinese Template`.
- `references/book-completion-and-figure-qa.md` for books, long monographs, figure-heavy sources, or exact-appearance figure work.

## Workflow

1. Confirm the user's template choice as the first action.
2. Check whether the task includes an associated Markdown file. If it does, read it completely, use and edit that exact file in place, and inspect the diff after each coherent batch; do not make a replacement Markdown file. If multiple files are plausible and context does not resolve them, ask which one to edit.
3. Run `scripts/preflight_environment.py` and install only missing requirements.
4. If no Markdown exists, inspect the PDF with `scripts/inspect_pdf_source.py` and classify pages as electronic, scanned, or mixed. If Markdown exists, inspect the PDF as the fidelity authority and identify only gaps or garbled regions that still need extraction.
5. Create the output project next to the source by default and copy the selected directory from `assets/templates/`.
6. For `Sage-Olive`, run `python3 fetch_random_cover.py` once and keep that cover stable unless the user asks to reroll.
7. Initialize `terminology.tsv` before sustained translation. For books, also initialize `source-coverage.tsv` with `scripts/source_coverage_ledger.py`. For figure-bearing sources, initialize `figure-manifest.tsv` with `scripts/figure_manifest_ledger.py`.
8. Without Markdown, extract text/layout as a scaffold and use OCR only for scanned or garbled pages. With Markdown, translate and correct it in place, extracting or OCRing only missing or unreliable portions. Check the terminology ledger after each coherent batch and audit the edited Markdown/TeX before final validation.
9. Reconstruct the source in real TeX and run the selected template's bundled `compile.sh`. Validate `Sage-Olive` with `scripts/validate_sage_project.sh PROJECT_DIR MAIN.tex`; validate `Chinese Template` with `scripts/validate_chinese_template_project.sh PROJECT_DIR MAIN.tex`.
10. Inspect the title page, contents when present, representative text/formula pages, figure pages, and final page. Also inspect the copyright page for `Sage-Olive`. For books, close the coverage ledger before delivery.
11. Clean only auxiliary files created by this build and report the selected template and result.

Only skip PDF compilation when the user explicitly requests TeX only.

## Hard Stops

- Never deliver a preview as the final book.
- Never use PDF text overlay as the final translation method.
- For `Sage-Olive`, keep the random landscape cover and copyright page immediately before contents.
- For `Sage-Olive`, never omit, replace, or downgrade the random landscape cover unless the user explicitly asks to reroll it with `fetch_random_cover.py --force`.
- Preserve source PDF page numbers only in ledgers, manifests, or comments unless the user explicitly asks for facsimile pagination.
- If the task needs book-level completion or exact figure QA, follow the relevant reference completely before delivery.
