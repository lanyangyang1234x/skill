---
name: pdf-to-chinese-tex
description: "Faithfully convert or audit mathematical PDF translations into Chinese LaTeX/PDF with source-verified terminology, capitalization, formulas, coverage, layout, and stable Chinese-title deliverable names."
metadata:
  version: "2.3"
---

# PDF to Chinese TeX

Use this skill to produce a faithful Chinese LaTeX/PDF edition of a mathematical PDF with a user-selected bundled template.

## Task Routing and Template Selection

At the start, classify the request as one of:

- `conversion`: create a Chinese TeX/PDF project from a source PDF;
- `existing-project-audit`: revise an existing TeX/PDF translation without rebuilding its structure;
- `targeted-audit`: check only requested dimensions such as terminology, formulas, references, headers, or layout.

For `existing-project-audit`, inventory the existing entry TeX, chapter files, template, build scripts, PDF, ledgers, and output directory before editing. Preserve the existing project structure unless a change is required by the audit.

### Template Selection — First Action for New Projects

- At the start of every new translation task, before inspecting the source, preprocessing it, or creating output files, ask the user to choose `Sage-Olive` or `Chinese Template`.
- Always ask again for each new translation task; do not reuse an earlier task's choice or assume a standing preference.
- Do not begin translation work until the user answers the template question.
- Keep the selected template for the whole project unless the user asks to change it.
- Immediately after the template is chosen, ask for two project metadata values: the translator/editor display name and the model/tool display name (for example, `译者：张三` and `模型：Google Antigravity`). Do not silently reuse values from another task.
- If the user specifies a runtime/model, record it literally in metadata and the audit report. For this project the requested display value is `GPT-5.6 Sol（高）`; do not replace it with a generic `GPT`, `Sol`, or an unverified model name. This is a provenance label, not permission to claim a runtime that was not actually used.
- Do not inspect the source, preprocess files, or create the output project until both metadata values are confirmed. If the user intentionally wants anonymity, record the exact neutral label they provide rather than inventing a person's name.

For an existing project, reuse its confirmed template and metadata when they are already recorded; ask only for missing or changed values.

For book-length work, give progress checkpoints after each coherent batch. State the completed source range, current pass, next pass, and any blocker. Give an ETA only after at least one representative batch has been measured; revise it when scope or throughput changes.

### Throughput Without Quality Loss

- For book-length conversion or audit, use source-page batches small enough to finish and verify in one task, normally 4--6 PDF pages or one coherent section. Split unusually dense proofs or figure-heavy pages further; do not make a whole chapter the default unit.
- Give each batch one writer and a disjoint target-file set. Parallel workers may read the source and shared ledgers, but they must not edit the same `.tex`, `terminology.tsv`, `figure-manifest.tsv`, `source-coverage.tsv`, `PROJECT_STATUS.md`, or output report concurrently.
- Before dispatching a batch, claim it with `scripts/batch_checkpoint.py`. Do not dispatch a batch whose latest checkpoint is `in_progress`, `drafted`, or `verified`. A failed batch may be retried once with a recorded reason; never create a second worker for an unresolved active claim.
- Workers write a private batch report and propose ledger rows; the coordinator merges shared ledgers once per completed batch. A retry must reuse the same target files and replace only the failed batch, not retranslate neighboring pages.
- Separate stages: translation/reconstruction, mathematics and terminology review, then figure/layout QA. During translation use a local section or chapter harness and one or two XeLaTeX passes; reserve the full-book multi-pass compile and visual release gate for chapter merge checkpoints and final delivery.
- Treat a successful local compile as a syntax/layout signal only. A batch becomes `verified` only after source-page comparison and the relevant review pass; speed comes from reducing duplicated work, not from skipping evidence.
- If a main file does not yet include a chapter, validate that chapter with an isolated harness rather than using an incomplete full-book PDF as the completion test.
- Read [references/parallel-batch-workflow.md](references/parallel-batch-workflow.md) for the claim/checkpoint schema, retry rule, coordinator merge order, and stage-specific compile policy.

## Rules

- Preserve source order, numbering, notation, formulas, labels, citations, and figure geometry.
- Translate specialized terms into Chinese; keep personal names in the source spelling.
- Preserve the source's original capitalization in any Latin-script text that comes from the PDF, including English titles, headings, labels, captions, metadata, and credits. Do not normalize source-derived English into all caps, title case, or sentence case unless the source itself does so.
- Apply `references/translation-and-layout-policy.md` for the content-vs-presentation authority split, faithful translation, cross-reference mechanics, front-matter metadata, typography, hyperlink behavior, terminology index, and three-round review gate.
- Treat the original rendered PDF/book as the authority for mathematical content and source structure; treat the selected bundled template as the authority for page layout and presentation. When an associated Markdown transcription exists, use it as the primary drafting scaffold for the TeX project, but let the PDF override it whenever they conflict.
- Use this authority order for audits: original PDF > user-confirmed errata/supplements > existing TeX project > OCR/Markdown scaffold. Record the order and the actual edited files in the audit report.
- Never “润色” by adding source-absent explanations, examples, proofs, or motivational prose. Mathematical correctness, hypotheses, logical relations, formula semantics, and source numbering take priority over language smoothness.
- Use real TeX cross-references for every referenced theorem, formula, section, figure, table, exercise, or answer: `\\label`, `\\ref`/`\\autoref`, and `\\eqref`; do not hard-code translated numbers. Preserve the source edition's visible numbering by adjusting counters or environments when needed.
- Keep a final terminology index/ledger for substantial projects with Chinese term, source term, and first-use page; perform separate mathematics, terminology, and layout review passes before delivery.
- Treat user-provided Markdown/OCR as read-only by default, but use its reliable content directly as the primary drafting input for the TeX project. Convert Markdown structure into real TeX while editing the TeX files; do not re-extract or re-OCR passages that the Markdown already represents clearly. Edit the Markdown itself only when the user explicitly authorizes Markdown changes, and state that it was used as a read-only scaffold.
- If more than one Markdown file could be the source, identify the correct file from explicit task context; if ambiguity remains, ask before editing. Never choose by filename guesswork.
- Use the PDF as the authority to correct and complete the TeX reconstruction; inspect or OCR only the pages, passages, formulas, labels, figures, or structure that the Markdown omits, garbles, or conflicts with. Do not repeat a full-PDF extraction merely because a Markdown scaffold is present.
- For `Sage-Olive`, keep its random landscape cover and bundled Fandol/Libertinus typography unchanged.
- For `Sage-Olive`, register every selected random cover in the cross-project cover history. A reroll must exclude prior source URLs and image hashes; use a previously selected image again only when the user explicitly asks for that exact image.
- For `Sage-Olive`, use dynamic running heads: the inner/left side shows the current `section` number and title, and the outer/right side shows the current `subsection` number and title. Keep the light-gray body-font treatment and thin rule below the header; never use a static book title or author as the running head.
- For `Chinese Template`, preserve its `ctexart` chapter-title, contents, theorem, exercise/answer, appendix, bibliography, and title-page structure; keep `fontset=fandol` for portable compilation.
- For `Chinese Template`, preserve clickable contents and cross-references, `MidnightBlue` internal/URL links, `BrickRed` bibliography links, borderless link text, exercise-to-answer links, proof-ending markers, and long-proof navigation when applicable.
- Ensure front matter identifies the original title, author, edition/publication information, translator/editor, selected model/tool, and update/completion time; include a visible credit line equivalent to `本中文译本由{译者名}使用{模型名}完成。` and keep a deliberate visual gap before the first numbered chapter.
- For source-cropped figures, preserve high resolution, transparent background, and source-relative displayed size; a visible white rectangle or undersized crop on the compiled page fails QA.
- Transparency must be real alpha transparency with no opaque white canvas, halo, or white-pixel substitute; verify it on a non-white background and in the compiled PDF.
- A figure crop must contain only the target figure and integral in-figure labels; any unrelated prose, formula, caption, header, footer, page number, or neighboring artwork fails QA.
- Inventory every ordinary English label inside a figure and replace it with Chinese; do not leave English legends, axis labels, annotations, or in-figure captions untranslated.
- For exact-appearance figure requests, preserve source pixels and geometry; do not approximate it with hand-tuned TikZ.
- For exchange/commutative diagrams, apply the deterministic decision protocol in [references/book-completion-and-figure-qa.md](references/book-completion-and-figure-qa.md): classify the geometry before reconstruction, default the final asset to a source-pixel-locked crop in exact-appearance mode, and use native TikZ only when every stated gate passes. “Simple” means only that the topology is easy to redraw; it is not by itself evidence that TikZ will match the source.
- Never let a second extraction/render/crop run write into a verified figure directory. Keep immutable source renders, fresh crops, translated assets, and release assets in separate directories; reruns must write to a new run directory or fail on an existing output. A verified asset may be replaced only by an explicit versioned promotion after source hash, crop parameters, pixel hash, and compiled-page QA have been rechecked.
- Do not summarize, modernize, overlay, or replace the source PDF with translated text.
- For books, preserve hierarchy and order; do not invent chapter boundaries or drop front/back matter.
- If the source is unreadable, the structure is unclear, or a requested layout would force material simplification, stop and ask before changing strategy.
- Treat compilation success and source fidelity as separate checks.

## Quality Gate

- If source-derived English appears in all caps because of a sample placeholder or style default, treat it as a fidelity error and restore the source capitalization before delivery.
- The presence of an all-caps English title in the deliverable is a layout/terminology failure unless the source itself uses all caps.

## Capitalization Fidelity Protocol

- Before sustained translation, record the exact source spelling and capitalization of every prominent Latin-script string: the cover/title, author and edition lines, section headings, running heads, captions, figure labels, bibliography labels, and credits. Treat this record as evidence, not as a style suggestion.
- Keep source-derived Latin text literal in TeX. Do not wrap it in `\MakeUppercase`, `\uppercase`, `\MakeLowercase`, `\lowercase`, `\textsc`, or `\scshape`, and do not hand-retype it in all caps. If an inherited template style changes glyph shape or case, neutralize that inheritance with a local `\normalfont\upshape` (or an equivalent non-transforming style) around the source string.
- Distinguish visual small caps from textual capitalization. A template's small-caps treatment for interface labels such as `Chapter` or `Appendix` may remain when required by the selected layout; it is not evidence that a source-derived title or author should be uppercased. Preserve small caps for source text only when the source visibly uses small caps and the audit records that fact.
- For raster covers and figures, inspect the authoritative source pixels or a case-preserving transcription before recreating or overlaying any text. OCR output is a locator and may normalize case; it must not override the rendered source. Preserve the capitalization of retained Latin text in image edits as well as in TeX.
- During visual QA, compare the source and final cover/title page, contents, running heads, captions, and representative figures. Check both the character case and any inherited small-caps/uppercase styling before delivery.

## Markdown-First Path

When a reliable associated Markdown transcription is supplied, use this lower-cost path:

- Identify the exact Markdown file from task context and read it as the primary content scaffold. Work through it in coherent batches rather than loading or reprocessing the whole source repeatedly.
- Transfer each batch into the selected TeX project and convert Markdown headings, emphasis, lists, math delimiters, image references, anchors, footnotes, and page markers into real TeX. Do not leave raw Markdown syntax in the final `.tex`.
- “直接改” means edit the TeX representation produced from the Markdown, not blindly paste Markdown markers into TeX and not overlay translated text on the PDF. Use page/source markers to map only the current batch back to the original PDF when verification is needed.
- Translate and edit the TeX directly. Keep the Markdown file unchanged by default; it is a read-only input, not a second deliverable.
- Consult the original PDF selectively for missing or garbled passages, formula and notation checks, figure bounds and labels, page structure, source capitalization, and any Markdown/PDF conflict. Do not run a full extraction or OCR pass over text that is already reliable in Markdown.
- Keep the normal final PDF spot checks, ledgers, compilation, and visual QA. The Markdown shortcut reduces duplicated extraction work; it does not lower the source-fidelity gate.

## Lazy Environment Policy

- `scripts/preflight_environment.py` is a read-only capability check. It must not install packages, create an OCR virtual environment, or probe heavy OCR imports unless the corresponding capability is explicitly requested.
- For a Markdown-backed draft, do not require PDF extraction or OCR at startup. Check `--need-compile` only when compilation is about to begin; request `--need-pdf` or `--need-render` later if a targeted source check needs them.
- For a PDF without a usable Markdown scaffold, request `--need-pdf` when source inspection begins and `--need-render` only when rendering/cropping is needed. Request `--require-ocr` only after a page is confirmed scanned or unreadable by ordinary extraction.
- Never run `scripts/bootstrap_ocr_environment.sh` automatically. Installing PaddleOCR or other optional packages requires an explicit user choice; if an existing system tool or configured Python environment can perform the requested step, use it first.
- Figure cropping and alpha validation need Pillow, not PaddleOCR. Prefer an existing Pillow-capable Python or set `PDF_TO_CHINESE_TEX_IMAGE_PYTHON`; do not install the heavy OCR environment for image-only work.
- If a required capability is missing, report the exact stage it blocks and offer the smallest installation or a safe fallback. Do not install the full PDF/OCR stack merely because the skill was invoked.

## Deliverable Naming

- Confirm or derive the translated Chinese book title before creating final outputs. Use one canonical, filesystem-safe title stem derived from that Chinese title (preserve Chinese characters; normalize path separators, control characters, and repeated whitespace).
- Name user-facing deliverables with that stem, never with a generic `main` stem: `<中文书名>.pdf`, `<中文书名>.tex` (when a top-level TeX source is delivered), `<中文书名>.zip`, `<中文书名>-审计报告.md`, and similarly named ledgers or manifests.
- Use the same stem for the project/output directory when practical. If an internal template requires `main.tex`, it may remain inside a private build directory, but the release directory must expose the Chinese-title PDF and archive and must not present `main.pdf` as the final artifact.
- Keep an ASCII build alias only when a tool cannot handle Chinese paths; document the alias-to-title mapping in the audit report and copy/rename final artifacts to the canonical Chinese-title names after validation.
- Before delivery, assert that the PDF, TeX (if delivered), ZIP, report, and output directory use the same canonical title stem and that no stale generic `main.pdf` or `main.zip` is being handed off.
- Build named deliverables with `scripts/package_release.py`; it creates a UTF-8 ZIP and verifies every archived payload byte. Do not use legacy `zip` for Chinese-path releases unless its UTF-8 filename behavior has been independently round-trip tested.

## Source Identity and Audit Evidence

- If the authoritative PDF is supplied from a temporary, chat-download, cache, or external-app path, snapshot it before sustained work with `scripts/source_manifest.py create SOURCE --project-dir PROJECT`. Keep the snapshot under `work/source/`; never include the source PDF or its absolute local path in a public release archive unless the user explicitly requests it.
- If `source-manifest.json` exists, validation must recheck its hash, byte size, and page count. A missing or changed snapshot is a hard stop for source-fidelity claims.
- For any project with citations or bibliographies, run `scripts/audit_bibliography.py PROJECT MAIN.tex`. It must reject missing and duplicate keys; book audits should also require each explicit “参考文献” heading to have a contents entry and review possible hard-coded author citations.
- For parallel book work, validate the batch ledger with `scripts/batch_checkpoint.py PROJECT/batch-checkpoints.tsv --check --project-dir PROJECT` before merging or releasing. No active same-phase overlap may remain, and every drafted/verified batch that has not been superseded by a later review phase must point to existing target files with matching hashes.
- Validators write durable JSON evidence under `work/validation/`. Use `--keep-aux` when a human will inspect the final `.log`, `.toc`, or `.aux`; otherwise auxiliary files may be cleaned only after the report is written.
- For exact commands and bibliography/source/release evidence, read [references/audit-evidence-and-release.md](references/audit-evidence-and-release.md) when auditing or packaging an existing project.

## Existing-Project Audit Gate

For `existing-project-audit` and substantial `targeted-audit` tasks, read [references/existing-project-audit.md](references/existing-project-audit.md). Maintain at least `source-coverage.tsv`, `terminology.tsv`, a formula/math audit record, and a visual QA record when the project is book-length. The release gate is: compile, run the bundled validator, check references/missing glyphs/high-risk overflow, inspect representative final PDF pages (including later-chapter running heads and backmatter), close coverage, synchronize the named outputs, rebuild the ZIP, and verify ZIP integrity. Report skipped checks and their reasons.

## Read These References

- `references/source-extraction.md` for extraction and OCR.
- `references/terminology-policy.md` for terminology.
- `references/translation-and-layout-policy.md` for translation fidelity, authority priorities, cross-references, metadata, typography, hyperlink, terminology-index, and review requirements.
- `references/sage-olive-template.md` when the user selects `Sage-Olive`.
- `references/chinese-template.md` when the user selects `Chinese Template`.
- `references/book-completion-and-figure-qa.md` for books, long monographs, figure-heavy sources, or exact-appearance figure work.
- `references/parallel-batch-workflow.md` for book-length work using multiple batches or agents.

## Workflow

1. Ask the user to choose `Sage-Olive` or `Chinese Template`; do not inspect the source first.
2. Ask for and confirm the translator/editor display name and model/tool display name; store both in the selected template's metadata fields and credit line.
3. Check whether the task includes an associated Markdown file. If present, identify the exact file, read it as the primary drafting scaffold, and transfer its reliable content into the TeX project in coherent batches. Do not edit the Markdown unless the user explicitly authorizes that write. If multiple files are plausible, identify the file used for reference and record the ambiguity; ask only when it changes the source text to be edited.
4. For book-length work, initialize `batch-checkpoints.tsv` and claim disjoint source-page/file batches before dispatching work. Read [references/parallel-batch-workflow.md](references/parallel-batch-workflow.md) before starting parallel work.
5. Run the non-mutating preflight with only the capability flags needed for the current stage (`--need-pdf`, `--need-render`, `--need-compile`, or `--require-ocr`). Do not install anything at this point unless the user explicitly approves a missing capability.
6. Snapshot a temporary/external authoritative source with `scripts/source_manifest.py`, then inspect it with `scripts/inspect_pdf_source.py` when extraction is needed. If Markdown exists, skip redundant full-text extraction and inspect only the source pages needed to resolve gaps, garbling, formulas, figures, numbering, layout, or conflicts.
7. Create the output project next to the source by default and copy the selected directory from `assets/templates/`.
8. For `Sage-Olive`, run `python3 fetch_random_cover.py` once. Its cross-project history prevents accidental reuse; keep the selected cover stable unless the user asks to reroll.
9. Initialize `terminology.tsv` before sustained translation. For books, also initialize `source-coverage.tsv` with `scripts/source_coverage_ledger.py`. For figure-bearing sources, initialize `figure-manifest.tsv` with `scripts/figure_manifest_ledger.py`.
10. With Markdown, convert and translate its content directly in the TeX project, checking the PDF only for targeted uncertainties; without Markdown, extract text/layout as a scaffold and use OCR only for scanned or garbled pages. For diagrams, freeze a source-render run before any crop or label replacement, record its source SHA-256 and render parameters, and never regenerate a verified crop from a translated/transparent derivative. Check the terminology ledger after each coherent batch and audit the actual edited TeX (and any explicitly authorized Markdown) before final validation.
11. Reconstruct the source in real TeX. Audit citations with `scripts/audit_bibliography.py`, then validate `Sage-Olive` with `scripts/validate_sage_project.sh PROJECT_DIR MAIN.tex` or `Chinese Template` with `scripts/validate_chinese_template_project.sh PROJECT_DIR MAIN.tex`. Use `--keep-aux` for final human log review.
12. Inspect the title page, credit line, contents when present, representative text/formula pages, figure pages, and final page. Also inspect the copyright page for `Sage-Olive`. For books, close the coverage ledger and batch checkpoint ledger before delivery.
13. Package with `scripts/package_release.py PROJECT_DIR MAIN.tex --title-stem 中文书名`; confirm the UTF-8 archive round-trip, then report the selected template, translator/editor name, model/tool name, title stem, actual edited files, read-only references, validation evidence, and result.

Only skip PDF compilation when the user explicitly requests TeX only.

## Hard Stops

- Never deliver a preview as the final book.
- Never use PDF text overlay as the final translation method.
- For `Sage-Olive`, keep the random landscape cover and copyright page immediately before contents.
- For `Sage-Olive`, never omit, replace, or downgrade the random landscape cover unless the user explicitly asks to reroll it with `fetch_random_cover.py --force`.
- Preserve source PDF page numbers only in ledgers, manifests, or comments unless the user explicitly asks for facsimile pagination.
- If the task needs book-level completion or exact figure QA, follow the relevant reference completely before delivery.
