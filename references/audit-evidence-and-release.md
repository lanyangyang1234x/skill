# Audit Evidence and Release

Read this reference for existing-project audits, bibliography audits, temporary source files, and named release packaging.

## Freeze the authority

When a source comes from a chat application, browser cache, temporary download, or removable location, snapshot it before sustained work:

```bash
python3 scripts/source_manifest.py create SOURCE.pdf --project-dir PROJECT
```

This writes `PROJECT/source-manifest.json` and a private audit copy under `PROJECT/work/source/`. The manifest records the source hash, byte size, and PDF page count. Validate it later with:

```bash
python3 scripts/source_manifest.py check PROJECT/source-manifest.json
```

The snapshot and absolute local source path are local QA evidence, not release content. `package_release.py` excludes both by default.

## Audit citations and bibliographies

Run the audit from the main TeX dependency graph, not every `.tex` file in the directory; named release copies may otherwise create false duplicate keys.

```bash
python3 scripts/audit_bibliography.py PROJECT MAIN.tex \
  --require-toc-bibliographies \
  --report PROJECT/work/validation/bibliography-report.json
```

The checker rejects missing citation targets, duplicate `\bibitem` keys, and bibliography-heading/contents mismatches. It reports unused or numeric-only keys and likely author-name hard-coded citations for review. Use `--fail-hardcoded` only after reviewing the heuristic against the project; mathematical intervals can resemble `[n]` citations.

For a source comparison, record per chapter or bibliography scope: source page range, expected entry count, source order, TeX file, and review status. Static key checks do not prove that the source bibliography itself was transcribed correctly.

After compilation, inspect at least one rendered citation per bibliography scope and confirm that the PDF link lands on the intended scope. Also inspect every bibliography page for independent numbering, hanging indentation, clipping, and chapter transitions.

## Preserve validation evidence

Both template validators compile three times, inspect the final log, and write:

```text
PROJECT/work/validation/bibliography-report.json
PROJECT/work/validation/validation-report.json
```

Use `--keep-aux` for the final audit when `.log`, `.toc`, or `.aux` must remain available. Without it, validators remove only build auxiliaries after the durable report has been written.

For book coverage, do not use one verified row for an entire book. Split `source-coverage.tsv` at least by chapter or similarly coherent source block and enforce a project-appropriate maximum span:

```bash
python3 scripts/source_coverage_ledger.py PROJECT/source-coverage.tsv \
  --check --first-page FIRST --last-page LAST --max-verified-span 50
```

Choose the limit from the source structure; `50` is an example, not a universal chapter length.

## Package named deliverables

Use the packaging helper instead of ad hoc `cp` plus legacy `zip`:

```bash
python3 scripts/package_release.py PROJECT MAIN.tex --title-stem 中文书名
```

It synchronizes the Chinese-title PDF and TeX, copies standard audit/visual-QA reports when present, excludes private `work/` evidence and generic build PDFs, writes UTF-8 archive names, performs a CRC test, and byte-compares every archived member with its source. Use `--include-source-manifest` only for a private archive where exposing the local source record is intended.
