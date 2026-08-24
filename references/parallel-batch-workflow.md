# Parallel Batch Workflow

Use this reference for long books or projects where several independent source ranges will be translated or reviewed. It is a coordination protocol, not a substitute for the mathematics, terminology, or layout review gates.

## Batch Boundaries

Choose a batch that can be translated, source-checked, and locally compiled in one task:

- normally 4--6 consecutive source PDF pages or one coherent section;
- split a dense proof, a page with several diagrams, or a scanned/OCR-heavy page into a smaller batch;
- keep each batch's target `.tex` files disjoint from every other active batch;
- keep source ranges ordered and non-overlapping in `source-coverage.tsv`.

Do not use a whole chapter as the default worker unit. A chapter remains the merge and review unit, not necessarily the translation unit.

## Claim Before Dispatch

Initialize and claim batches with:

```bash
python3 scripts/batch_checkpoint.py batch-checkpoints.tsv --init
python3 scripts/batch_checkpoint.py batch-checkpoints.tsv --claim \
  --project-dir PROJECT --batch-id ch06-s08 \
  --source-start 324 --source-end 327 --source-id chapter-06 \
  --phase translation --owner worker-1 --file chapters/ch06/section-08.tex
```

The command refuses a second claim for an overlapping batch in the same phase. A claim records the owner, phase, source range, target files, and attempt number. A later mathematics, terminology, or layout phase may inspect and revise the same target file after the translation claim is complete; it may not run concurrently with it. The worker may read shared ledgers but must not edit them directly.

## Completion and Retry

After the worker writes its private report and target files, record the result:

```bash
python3 scripts/batch_checkpoint.py batch-checkpoints.tsv --complete \
  --project-dir PROJECT --batch-id ch06-s08 --status drafted \
  --notes "Source pages compared; figure QA pending"
```

Use `verified` only after the relevant source comparison and review pass are complete. Use `blocked` with a concrete reason when a source or capability prevents progress. A blocked batch may be retried once with `--retry`; the retry must use the same batch ID, phase, and target files. Never start a second worker for a batch that already has an active or completed claim in the same phase.

Check before merge and release:

```bash
python3 scripts/batch_checkpoint.py PROJECT/batch-checkpoints.tsv \
  --check --project-dir PROJECT
```

The checker verifies same-phase active overlap, target-file existence, and output hashes for drafted or verified batches that have not been superseded by a later phase.

## Coordinator Merge Order

1. Read the private batch report and inspect the target diff.
2. Run the terminology and figure-ledger checks against the batch proposal.
3. Merge shared `terminology.tsv`, `figure-manifest.tsv`, and `source-coverage.tsv` once, in source order; only the coordinator writes these files.
4. Compile a local section/chapter harness. Do not use an incomplete main file as the completion signal.
5. Mark the batch `drafted` or `verified` only after the evidence exists.
6. At chapter boundaries, run the chapter-level mathematics, terminology, and layout passes; run the full-book validator only at a planned merge checkpoint or final release.

## Stage-Specific Compile Policy

The quality gate does not change. The compile scope changes:

- translation stage: one or two passes in a section/chapter harness;
- chapter merge: the chapter harness plus cross-reference checks;
- final release: the formal main file, the bundled validator, final log inspection, figure-page QA, and named UTF-8 packaging.

If a local harness cannot represent a cross-reference or figure dependency, escalate that batch to the smallest harness that can. Do not silently replace a required source check with a faster but weaker one.

## Failure Handling

Classify a failure before retrying:

- source/OCR failure: isolate the affected pages and request the smallest missing capability;
- TeX syntax failure: return the same batch to its owner with the exact log location;
- shared-state conflict: stop both writers, restore one coordinator, and do not retry translation;
- timeout: split the batch or remove final visual QA from the worker; do not blindly rerun the whole batch.

Retries are for the failed unit only. Neighboring verified batches and their evidence remain valid unless a shared numbering or layout change proves otherwise.
