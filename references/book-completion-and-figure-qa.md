# Whole-Book Completion and Figure QA

Use this reference for books, long monographs, figure-heavy sources, or any task that asks for exact visual fidelity.

## Complete-Book Gate

Treat “translate the whole book” as a terminal condition. A final deliverable must include all source content in order: front matter, chapters, unnumbered passages, proofs, exercises, footnotes, figures, captions, appendices, bibliography, and index when present.

Before delivery:

1. Close the source-page coverage range.
2. Compare logical-item counts by chapter or section.
3. Check that every section fragment appears exactly once and in order.
4. Search for untranslated source prose and placeholder text.
5. Compare the exact capitalization of prominent Latin-script text on the source cover, title page, contents, running heads, captions, and figure labels; do not accept OCR-normalized or template-induced all caps.
6. Compile the formal main file twice.
7. Inspect the first page, last page, representative formula pages, and every figure-bearing page.

## Ledgers

For books, initialize `source-coverage.tsv` with `scripts/source_coverage_ledger.py source-coverage.tsv --init`. Use PDF page indices, not printed page labels. Mark rows `verified` only after source-vs-TeX comparison. Use `excluded` only for genuine non-content pages.

For figure-bearing sources, initialize and maintain `figure-manifest.tsv` with one row per figure or diagram, using source page indices and a source anchor:

```bash
python3 scripts/figure_manifest_ledger.py figure-manifest.tsv --init
python3 scripts/figure_manifest_ledger.py figure-manifest.tsv --check --require-complete
```

For each figure row, record: figure ID, source page, source anchor, crop bounds, included content, excluded neighboring content, reconstruction method, output asset or TeX file, source visible-width ratio, target TeX width, background mode (`transparent`, `exact-flat`, or `not-applicable`), all source labels, translated labels, target PDF page, final status, and notes.

Before delivery, run:

```bash
python3 scripts/source_coverage_ledger.py source-coverage.tsv --check --first-page FIRST --last-page LAST
python3 scripts/figure_manifest_ledger.py figure-manifest.tsv --check --require-complete
```

The coverage checker rejects missing pages, duplicate IDs, incomplete rows, out-of-order ranges, and overlapping page ranges.

## Figure Decision Rule

Choose TikZ or `tikz-cd` only when every visible object, arrow, label, spacing, line weight, and aspect ratio can be verified. Use a high-resolution crop when the source geometry, shading, or rendering itself matters, or when redrawing would force guessing.

## Source-Pixel-Locked Mode

Enter this mode when the user says “一模一样”, “和原图一致”, “只把英文换成中文”, or otherwise requires exact appearance.

- Use a 450-600 dpi crop from the authoritative source PDF.
- Preserve every non-language pixel: geometry, fills, curves, arrows, object positions, line weights, and aspect ratio.
- Replace only the requested labels.
- Regenerate only from the fresh opaque source crop, never from an already translated or transparent derivative.
- Compare the translated asset against the source crop, then compare the compiled page against the source page.

## Figure Crops

- Crop only the intended figure and its integral labels.
- Exclude headers, footers, page numbers, neighboring prose, captions, rules, and unrelated figures.
- Inspect the complete rendered source page before choosing bounds. Set an explicit bounding box around the target figure; if any unrelated source text enters the crop, the crop is invalid and must be redone.
- Render source crops at 450-600 dpi and keep a lossless asset; do not downsample merely to fit the page.
- Trim away unused canvas before insertion; `\centering` does not fix off-center transparent or white padding.
- For line art and diagrams, make the background actually transparent with an alpha channel, not white pixels or a nominally RGBA file with an opaque canvas. A white rectangle, halo, or white-pixel background visible over the Sage-Olive gray theorem/example background fails QA.
- Flatten only when transparency damages meaningful pale fills, and then match the exact page or box background color.
- Measure the visible artwork width against the source text block and reproduce that ratio in TeX. Do not shrink a figure merely to fit a float or default every image to a tiny width or to `\linewidth`.
- Center the trimmed artwork explicitly and inspect the compiled page for balance and clipping.

## Label Ownership

Translated labels must belong to exactly one layer: raster or TeX, never both.

- Inventory all ordinary English inside the figure, including legends, axis labels, annotations, callouts, and in-figure captions.
- Replace ordinary English with Chinese. Preserve mathematical symbols, formulas, and personal names when they are not translatable prose.
- For any Latin text intentionally retained in a figure or cover, preserve the source's exact capitalization. Do not use small caps or all-caps styling as a substitute for a source transcription.
- For raster-owned labels, erase the complete original glyph and antialiasing region from a fresh opaque crop, then place the Chinese label at the same anchor.
- For TeX-owned labels, use a clean raster without that label and place the Chinese label exactly once in TeX/TikZ.
- A figure with unexplained ordinary English remnants fails QA. If translation would damage geometry, use source-pixel-locked replacement or a verified redraw; do not silently leave it untranslated.

## Figure QA

Render and inspect every final PDF page that contains a figure or diagram. Checking the PNG alone is not enough.

Use:

```bash
python3 scripts/render_figure_page_contacts.py FINAL.pdf figure-manifest.tsv --output-dir work/figure-page-qa
```

Then verify that each figure page has the intended content only, with no stray page furniture, no unrelated source text, no ordinary English remnants, no clipped labels, no duplicate labels, correct centering, source-relative size, and correct background treatment. For transparent assets, verify both the source image alpha channel and the compiled PDF image mask if the checker is available.

Also composite every transparent crop over a gray or other non-white background before delivery. If a white panel, halo, unexpected padding, opaque canvas, or undersized display is visible, regenerate the asset from the source crop, adjust TeX width to the source-relative size, recompile, and recheck.
