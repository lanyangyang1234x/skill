# Existing-project audit

Use this reference when a Chinese TeX/PDF project already exists or when the user asks for a full audit rather than a fresh conversion.

## Authority and write boundary

Use the original rendered PDF as the authority for mathematical content and source structure. User-confirmed errata or supplements come next, followed by the existing TeX project. MinerU Markdown and OCR are read-only scaffolds; when a missing or damaged TeX passage can be recovered reliably from Markdown, transfer that content directly into TeX and verify only the uncertain portions against the PDF. Edit Markdown itself only when the user explicitly authorizes it. Record actual edited files and read-only reference files in the report.

## Audit passes and ledgers

Run independent passes for:

1. coverage: account for front matter, main matter, appendices, references, index, publisher catalogue, cover text, and other backmatter in `source-coverage.tsv`;
2. terminology: record preferred Chinese terms, variants, forbidden forms, derived terms/fixed collocations, first source page, TeX locations, and evidence in `terminology.tsv`;
3. mathematics: compare formulas structurally (domains, signs, limits, indices, hypotheses, constants, norms, vectors/matrices, and numbering) and record key checks in `formula-ledger.tsv` or `math-audit.md`;
4. layout: record title page, copyright page, contents, chapter openings, later-chapter running heads, odd/even pages, long formulas, figures, missing glyphs, blank pages, final page, and backmatter in `visual-qa.md`.

Do not treat compilation success as proof of mathematical fidelity. Fix undefined or wrong references first; label ordinary hard-coded historical or illustrative numbers as lower-risk rather than mass-rewriting every number. Treat visible clipping or collisions as high-risk overflow; a harmless mathematical edge warning may be documented as low risk.

## PDF visual gate

Inspect the final rendered PDF, not only TeX macros. Include at least one later-chapter middle page (for example, chapters 5 or 6 in a long book), a chapter opening, a formula-heavy page, a figure page, and backmatter. Confirm the running head changes with the current chapter/section and does not retain a previous title.

## Named release gate

Before delivery:

1. compile and run the selected template validator;
2. scan undefined references, duplicate labels, missing glyphs, and high-risk overflow;
3. complete the coverage and audit ledgers;
4. rename or copy user-facing artifacts to one canonical filesystem-safe stem derived from the translated Chinese title;
5. ensure PDF, optional top-level TeX, ZIP, report, and output directory share that stem; internal `main.tex` is acceptable only as a private build entry;
6. rebuild and integrity-check the ZIP;
7. report the title stem, template, metadata, actual edits, read-only references, checks performed, skipped checks and reasons, final PDF page count, and artifact paths.

Do not deliver stale `main.pdf`, `main.zip`, or similarly generic files as the release artifacts.
