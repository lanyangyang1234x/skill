# Whole-Book Completion and Figure QA

Use this reference for books, long monographs, figure-bearing sources, or any task that asks for visual fidelity. Apply the current task's scope: a whole-book audit needs complete source coverage; a targeted figure repair needs complete coverage of its authorized figures and their affected pages. Preserve correct figures unless the user requests a different presentation or the audit finds a verified problem.

## Complete-Book Gate

For an authorized whole-book translation, account for every source page and logical unit in order: front matter, chapters, unnumbered passages, proofs, exercises, footnotes, figures, captions, appendices, bibliography, and index when present. Record any user-authorized exclusions explicitly; a blank page or an excluded publisher catalogue must not conceal missing mathematical content.

Before delivery, apply the requested output scope: when the user explicitly wants TeX only, PDF build/render/click checks below are not applicable; perform source and source-package checks as defined in [audit-evidence-and-release.md](audit-evidence-and-release.md#仅交付-tex-时).

1. Close the source-page coverage range and distinguish translated, verified, excluded, and unresolved content.
2. Compare logical-item counts by chapter or section, then compare the actual content; equal counts alone do not establish fidelity.
3. Check that every section fragment appears exactly once and in source order.
4. Search for untranslated prose and placeholders, including ordinary English embedded in images.
5. Compare the actual capitalization of prominent Latin-script text on the cover, title page, contents, running heads, captions, and figure labels; OCR-normalized or template-induced all caps are not acceptable evidence.
6. Compile the explicit formal main file using the selected template or existing project's build procedure, until references, contents, and index have stabilized. A fixed number of passes is not a universal completion test.
7. Inspect the first and last pages, representative formula pages, later-chapter running heads, every affected figure page, and any neighboring pages whose pagination or layout changed.

Keep coverage, mathematics, terminology, Chinese expression, figures/layout, hyperlinks, and release reconstruction as separate results. A source scan, ledger validation, or successful build does not prove the other dimensions. Read [audit-evidence-and-release.md](audit-evidence-and-release.md) for final archive extraction and rebuild evidence.

## Ledgers and a Two-Way Figure Inventory

For books, initialize `source-coverage.tsv` with `scripts/source_coverage_ledger.py source-coverage.tsv --init`. Use one-based PDF physical pages, not printed page labels. Mark rows `verified` only after the relevant source-vs-TeX comparison. Record the actual source range, review dimension, version, and exclusions; do not inherit an old `verified` row as evidence of a new review.

For figure-bearing sources, maintain `figure-manifest.tsv` with a stable ID and source anchor for every logical figure or diagram:

```bash
python3 scripts/figure_manifest_ledger.py figure-manifest.tsv --init
python3 scripts/figure_manifest_ledger.py figure-manifest.tsv --check --require-complete
```

Inventory in both directions before claiming completeness:

- **Source to TeX:** inspect the rendered source pages and their logical units, including unnumbered diagrams, exercise figures, proof diagrams, inline quivers, formula-embedded pictures, figure panels, and tables. Map each in-scope source item to its TeX location, asset or native diagram, and final PDF occurrence. Record a genuine exclusion with its reason; absence of a numbered caption is not an exclusion.
- **TeX to source:** scan chapter files and the macros they call for `\includegraphics`, `tikzpicture`, `tikzcd`, XY-pic (`\xymatrix`, `xy`), PSTricks, and other drawing environments or macro-built diagrams. Inspect inline and display math that contains a small diagram. Map each output item back to its source anchor, or identify it as an authorized translator note or user-provided illustration. Do not infer that every `\to` is a figure, or that every diagram is inside a `figure` environment.
- **Reconcile the lists:** resolve missing source figures, extra output diagrams, accidentally duplicated panels, obsolete asset references, and reused assets with different mathematical labels. Record intentional repeated uses and their individual PDF occurrences. Use separate occurrence IDs or an attached occurrence list when one figure appears more than once; do not let a single target page conceal other uses.

For each manifest row, record: figure ID, source page and anchor, bounds, included content, excluded neighbors, chosen method, asset or TeX path, source visible-width ratio, target TeX width, background mode (`transparent`, `exact-flat`, or `not-applicable`), source labels, translated labels, target PDF page, status, and notes. `output_asset_or_tex` can point to a native TeX file with `#anchor`; provenance and per-occurrence details may be kept in `notes` or a linked sidecar without changing the current manifest header. Tables need source-to-output cell and caption checks even when they are editable TeX rather than image assets.

Before delivery, run:

```bash
python3 scripts/source_coverage_ledger.py source-coverage.tsv --check --first-page FIRST --last-page LAST
python3 scripts/figure_manifest_ledger.py figure-manifest.tsv --check --require-complete
```

The coverage checker validates its recorded ranges and the figure checker validates required fields, statuses, and existing output paths. Neither discovers all source figures, expands all TeX macros, proves label meaning, or verifies final PDF image embedding. The two-way reconciliation and rendered checks remain necessary.

## Choose the Figure Method for the Current Goal

Determine whether the current task prioritizes exact source appearance, mathematical structure, or reading clarity. Reuse a recorded choice when it is already clear; do not repeatedly ask the user or replace correct diagrams merely to standardize a technology.

| Current goal | Method and acceptance |
|---|---|
| Exact source appearance, such as “一模一样”, “和原图一致”, or “只把英文换成中文” | Use `source-pixel-locked` crops or a verified label-only hybrid. Preserve source non-language pixels and geometry; replace only the authorized labels. A redraw that is merely visually similar does not satisfy this goal. |
| Mathematical structure fidelity | TikZ, `tikz-cd`, existing XY-pic, a clean source crop, or a verified hybrid may be suitable. Check every node, edge, arrow direction/type, route, label, relation, and meaningful grouping. Position changes must not introduce different mathematical meaning. |
| Reading clarity | Choose a verifiable representation with readable labels, sufficient scale, balanced spacing, and correct relationships. Native reconstruction or moderate enlargement may help when source appearance is not an exact constraint. Preserve the source mathematics and record meaningful presentation changes. |

Node counts, arrow counts, or the presence of a bent arrow are not automatic method gates. A larger grid may be completely reconstructible, while a two-node curved figure may require source rendering to preserve an unambiguous route. Curves, loops, crossings, layer ordering, pale fills, source-specific glyphs, and dense labels increase the verification burden; choose a crop when reconstruction would require guessing. Correct existing native diagrams do not become defective because another project used crops.

### Verification Protocol

1. **Scope and goal:** record the authorized figure range and presentation goal, plus protected labels, geometry, background, and sizing requirements.
2. **Source inspection:** view the entire source page and then the figure at useful scale. Inventory visible objects, arrow direction/type, crossings, labels, shading, integral legends, and meaningful spacing before editing.
3. **Method choice:** choose the representation that can meet the goal with evidence. Exact appearance requires the pixel-locked rules below. For structure or clarity, native diagrams remain candidates when all relevant relationships and output details can be checked; uncertainty is a reason to retain or crop the source, not to guess.
4. **Label ownership:** assign each translated label to exactly one raster or TeX layer. Check ordinary prose separately from mathematical symbols, formulas, personal names, and references.
5. **Candidate check:** compare source and candidate at the intended physical display size. Verify missing/extra nodes or arrows, topology, signs and indices, integral labels, aspect ratio, clipping, background, and legibility. In exact mode, compare unchanged non-language regions against the authoritative crop; in other modes, document deliberate presentation differences.
6. **Final PDF check:** inspect actual output occurrences, including transparent masks and their placement. An asset file check alone is insufficient.
7. **Promotion and evidence:** record the chosen method and checks in `figure-manifest.tsv`; later crop or processing runs must not silently change the method, path, or accepted asset.

Useful method descriptions include `source-pixel-locked`, `native-tikz`, `native-tikz-cd`, `native-xypic`, and `hybrid-label-overlay`. Use a descriptive method for a verified mixed representation; each component and label must have a clear owner, and the join must preserve the required geometry. A hybrid is not evidence that unresolved parts are correct.

## Immutable Figure-Asset Pipeline

Use distinct locations (names may vary):

```text
work/source-renders/<source-sha>/<run-id>/       # immutable page renders
work/crops/<run-id>/                            # fresh opaque source crops
work/translated-assets/<run-id>/                # label-replaced or alpha assets
assets/exact/                                   # promoted release assets only
```

At the beginning of a run, record the authoritative source SHA-256, PDF page, DPI, bounds, background mode, and processing script version in the manifest or a sidecar JSON. A crop script must refuse to overwrite an existing file by default. Re-running writes a new run directory; promotion is an explicit versioned copy/rename after validation, not an in-place regeneration. Never use a transparent or translated derivative as the input to a new crop. If a verified asset appears wrong, preserve its hash and row, regenerate from the immutable source render, and promote a corrected version only after the relevant QA gates.

Use `scripts/figure_asset_lock.py record ...` for promoted raster assets and run `scripts/figure_asset_lock.py check LOCK.json` before compilation and release. Verify that manifest paths exist and accepted hashes still match. A mismatch must be resolved against the actual edit history; do not silently refresh the lock or recrop to make a check pass. Native TeX diagrams also need recorded source locations and controlled edits, although their fidelity cannot be established by a raster asset lock.

## Source-Pixel-Locked Mode

Use this mode when the user requires exact appearance. A switch to structure or clarity equivalence needs support in the current user request; it cannot be inferred from the difficulty of exact preservation.

- Render a lossless crop from the authoritative source PDF, normally at 450–600 dpi, preserving every non-language pixel: geometry, fills, curves, arrows, object positions, line weights, and aspect ratio. Record the actual resolution and physical size; do not invent detail absent from the source.
- Replace only the authorized language labels. Keep a source crop, original label bounds, translated label bounds, and a comparison of unchanged regions.
- Regenerate only from the fresh opaque source crop, never from an already translated or transparent derivative.
- Transparency may remove only the verified exterior page background. Preserve integral black backgrounds, intentional white regions, shadows, and pale fills; an indiscriminate “remove all white” threshold fails this requirement. Retain a flat source background when alpha conversion would damage source appearance.
- Label removal must not touch a mathematical glyph or drawing path. When a label overlaps geometry, use a source-backed reconstruction of the affected region that can be checked, or leave the item unresolved and continue other authorized work. Do not invent hidden geometry.
- A native redraw with matching topology is not pixel-locked. Use it only when the task permits structural or visual equivalence rather than requiring source pixels, and record that goal accurately.
- Compare the translated asset with the source crop and inspect its final compiled occurrence. Verify geometry at the same physical size; a reflowed Chinese book need not reproduce the original whole-page layout.

## Crop Bounds, Transparency, and Size

- Crop only the intended figure and all integral labels; exclude headers, footers, page numbers, neighboring prose, separate captions, rules, punctuation fragments, and unrelated figures. Translate separate captions in TeX. View the full source page before setting explicit bounds, and verify the lower and outer edges so a final row of nodes or an arrow tip is not lost.
- Keep a lossless asset at sufficient resolution, normally 450–600 dpi for source line art. Do not downsample merely to fit a float.
- Trim unused exterior canvas before insertion; `\centering` does not correct asymmetric transparent or white padding. Center the visible artwork, then inspect the compiled balance and clipping.
- When a transparent background is required, use a genuine alpha channel, not white pixels or nominal RGBA with a fully opaque canvas. Composite over a non-white background and inspect the final PDF for white panels, halos, residual pixels, and damage to pale fills.
- Flatten only when transparency would damage meaningful content, with the correct page or box background and a recorded reason. An integral source fill is not unwanted page background.
- Record visible source width relative to its text block. Exact appearance follows that scale and aspect ratio; structure/clarity tasks may use another documented width when it improves reading. Do not automatically shrink every figure to a tiny width or enlarge every figure to `\linewidth`.

## Label Ownership and Translation

Translated labels belong to exactly one layer: raster or TeX, never both.

- Inventory all ordinary English, including legends, axes, annotations, callouts, and in-figure explanations. A transparent source crop is not exempt from translation coverage.
- Translate ordinary prose according to the task. Preserve mathematical symbols, formulas, personal names and their required source forms, operator notation, and reference numbers according to their identities. `Ker`, `Coh`, `Rep`, `Spec`, or `Proj` should not be treated as ordinary prose merely because they contain Latin letters.
- Preserve the source's actual spelling and capitalization for Latin text that remains. Template small caps or all caps are not a substitute for checking the source.
- For raster-owned labels, remove the full original glyph and antialiasing region from a fresh opaque crop, preserve the underlying geometry/background, then place Chinese once at the verified anchor.
- For TeX-owned labels, use an image or clipping layer without the original label and place Chinese exactly once. Avoid a white covering panel over a transparent or colored figure background.
- Check replacement regions against mathematical glyphs and drawing paths, then compare source and output at final size. Ordinary English remnants, duplicated labels, hidden arrowheads, or a label that moved into a different mathematical association fail QA.

## Final PDF Figure QA

Render and inspect every final PDF page containing an in-scope figure or diagram. In a whole-book figure audit, this means all such pages, including native XY-pic and inline diagrams. In a targeted repair, also inspect the changed page and any neighboring pages whose layout, float position, formulas, footnotes, or environment end marks changed.

Use the manifest to make page contacts:

```bash
python3 scripts/render_figure_page_contacts.py FINAL.pdf figure-manifest.tsv --output-dir work/figure-page-qa
```

Contacts are a navigation aid, not proof that the figures were viewed. At readable scale verify intended content, no stray page furniture or neighboring text, complete nodes/arrowheads, no ordinary English remnants, no clipping or duplicate labels, correct mathematical labels and routes, centering, intended size, and correct background treatment. Native vector diagrams need rendered inspection even though they have no embedded raster image.

For raster assets, compare the **actual final PDF occurrences** with the accepted assets: decoded color pixels and alpha, transparency/soft masks, dimensions, usage order, bounding boxes, and target pages. Pair each occurrence with its manifest identity rather than matching only file names or dimensions. Distinct same-size transparent images can be wrongly reused during PDF processing; correct PNG hashes alone do not prove that the intended image was embedded at every location. Record intentional repetitions and investigate unplanned repeated images.

Also composite every transparent asset over gray or another non-white background. A white panel, halo, unexpected padding, or damaged pale region requires a source-backed correction and another compiled-page check. If PDF mask/occurrence inspection tools are unavailable, record that limitation and the visual evidence actually obtained; do not claim a machine-level embedding check passed.

After a repair, compare changed pages with the previous accepted PDF and explain pagination changes. Inspect affected neighboring pages for displaced captions, isolated proof/example end marks, clipped long formulas, and missing footnotes. Untouched pages can retain prior evidence when their content/assets and relevant layout are verified unchanged; do not describe this as a fresh full-book review. The final release archive must still be independently extracted and rebuilt according to [audit-evidence-and-release.md](audit-evidence-and-release.md).
