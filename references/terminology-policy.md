# Chinese Mathematical Terminology Policy

Every professional term needs a Chinese rendering.

## Priority

1. User glossary or existing series translation.
2. Banana Space entries.
3. Same-field Chinese papers, reports, theses, or lecture notes.
4. Authoritative Chinese textbooks, monographs, encyclopedia entries, or official terminology resources.
5. Broad web usage only as weak support.

## Rules

- Keep personal names in the source spelling, including eponyms; translate only the surrounding common noun, e.g. `Nakayama 引理`.
- Use `中文（English）` at first important appearance, then stay consistent.
- For a new concept in running text, prefer an emphasized first-use form such as `\\emph{概型} (scheme)`; do not repeat the parenthetical English or emphasis at every later occurrence.
- Use Chinese punctuation in translated prose, with English full stops retained only inside genuine source-language sentences or quotations.
- If evidence is split, choose a defensible provisional translation, mark it `provisional`, and record alternatives in `terminology.tsv`.
- Do not claim support from a source unless the exact entry or document has been opened and cited.

## Ledger

Initialize, check, and audit the ledger with:

```bash
scripts/terminology_ledger.py terminology.tsv --init
scripts/terminology_ledger.py terminology.tsv --check
scripts/terminology_ledger.py terminology.tsv --audit SOURCE.md PROJECT_DIR
```

Run `--check` after every coherent translation batch. Run `--audit` against the source Markdown (when present) and the final TeX project before delivery; the TeX project is the edited deliverable unless Markdown write-back was explicitly authorized. The audit permits one important bilingual first-use occurrence such as `拟同构（quasi-isomorphism）` and reports later source-term remnants.

When a source term must remain in a bibliography title, quotation, or other justified context, add `audit-allow-source=N` to that ledger row's `notes`, where `N` is the permitted count. Use `audit-allow-all` when all source-language occurrences are intentionally preserved, and `audit-ignore` only when the entire entry is exempt from document auditing. Record the reason next to any directive.

To catch previously used Chinese variants, add `audit-forbid=旧译名一|旧译名二` to `notes`. The audit then rejects those variants and points back to `chosen_zh`.

Treat audit findings as review targets, not permission for blind replacement. Inspect context before changing Markdown or TeX, especially around formulas, code, citation keys, URLs, and personal names.
