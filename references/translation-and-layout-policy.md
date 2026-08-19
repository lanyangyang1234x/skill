# Translation and Layout Policy

Use this policy for every mathematical translation, including projects that
start from a MinerU or other Markdown transcription.

## Authority and Priorities

Keep two kinds of authority separate:

- **Content authority:** the rendered original PDF/book is authoritative for
  mathematical meaning, formulas, numbering, structure, figures, and source
  order. When present, the Markdown file is the primary drafting scaffold for
  transferring content into TeX, but it yields to the source whenever they
  conflict; do not repeat full extraction for reliable Markdown content.
- **Presentation authority:** the selected bundled template is authoritative
  for page geometry, typography, title-page construction, theorem styling,
  hyperlinks, and running heads. Do not force a facsimile layout unless the
  user explicitly requests one.

When a conflict cannot be resolved without changing source content or
materially simplifying the layout, stop and identify the conflict before
choosing a workaround.

When Markdown is supplied, convert its reliable headings, prose, math, image
references, anchors, footnotes, and page markers into real TeX in coherent
batches. Keep the Markdown read-only by default and use targeted PDF checks for
uncertain, missing, garbled, or conflicting material.

## Translation Requirements

- Translate faithfully; do not add explanations, examples, proofs, or
  motivational prose that is absent from the source. Natural Chinese is useful,
  but mathematical meaning, hypotheses, logical relations, and formula
  semantics take priority over fluency.
- Preserve chapters, sections, theorem-like items, definitions, propositions,
  corollaries, lemmas, examples, exercises, footnotes, references, appendices,
  and their source order. Do not remove source material merely to make TeX
  compile.
- Use one Chinese rendering for the same mathematical term throughout the
  book. Keep personal names and eponyms in source spelling, and retain the
  English term at the first important occurrence when the Chinese rendering is
  not firmly established.
- At first use of a genuinely new concept, use `\\emph{中文术语}` followed by
  the source term in parentheses, for example `\\emph{概型} (scheme)`. Do not
  italicize every later occurrence.
- Use Chinese punctuation throughout, except that an English sentence ending
  inside an English quotation or source-language passage may retain its period.
- Preserve the source's capitalization for any Latin-script text copied from the
  PDF, including titles, section headings, labels, figure captions, metadata,
  and cover or title-page credits. Do not silently normalize source-derived
  English into all caps, title case, or sentence case unless the source itself
  does so.
- Keep source-derived text separate from template interface labels. A template
  may style labels such as `Chapter`, `Appendix`, or `Proof` with small caps,
  but that presentation rule must not leak into copied titles, author names,
  captions, or credits. If a source string is placed inside an inherited
  `\textsc`/`\scshape` context, locally restore `\normalfont\upshape`.

## Cross-References and Numbering

Every theorem, formula, section, figure, table, exercise, and answer that is
referenced must use real TeX anchors and links:

- use `\\label{...}` at the target;
- use `\\ref`, `\\autoref`, or `\\eqref` at the reference site;
- never hard-code a translated number in prose when a source reference exists.

For example, translate “By Theorem 3.4” as `根据定理~\\ref{thm:xxx}` and an
equation reference as `由式~\\eqref{eq:xxx}`. Preserve the numbering visible in
the source edition by adjusting counters, theorem environments, or numbering
formats when necessary; do not change the mathematical text to accommodate a
sample counter.

## Front Matter and Typography

At task initialization, collect and confirm the translator/editor display name
and the model/tool display name after the user chooses a template. Treat these
as per-project metadata, not global preferences. Render a visible credit line
equivalent to `本中文译本由{译者名}使用{模型名}完成。`; if the user supplies a
neutral or anonymous label, reproduce that label exactly.

The title page or cover metadata must identify, when the source provides it:
original title, author, edition/publication information, translator or editor,
translation/retypesetting tool or model, and update/completion time. For the
cover's lower-right publisher block, add a translator line such as “译者 翻译及
重排”; keep it visibly smaller than the main title but slightly larger than
the surrounding publisher metadata.

For `Chinese Template`, prefer the bundled template's Chinese body font for
正文, its theorem-style font for definition/theorem labels, and a serif
computer-modern-compatible font for English mathematical text. Use Kai-style
emphasis for Chinese specialist terms only when the template already supports
it; do not override the template's portable `fontset=fandol` requirement or
the Sage-Olive font map. The selected template remains the final layout
authority.

Keep front matter visually distinct from the first chapter: after a preface,
foreword, or introduction, leave an intentional amount of vertical space
before the first numbered chapter rather than compressing the transition.

## Hyperlinks and Template Features

For `Chinese Template`, preserve the template's link behavior:

- internal links and table-of-contents entries use `MidnightBlue`;
- bibliography links use `BrickRed`;
- URL links use `MidnightBlue`;
- linked text has no visible border; titles and page numbers in the contents
  remain clickable.

Retain the template's exercise-to-answer links, proof-ending marker, and
long-proof navigation behavior when the source contains those structures.

## Final Terminology Index

For a book or substantial set of notes, create a final terminology index or
ledger containing every specialized term that appears in the document: chosen
Chinese term, source-language term, and the first page on which it appears.
Use the terminology ledger scripts for machine checks, then inspect the final
PDF because page numbers can change after the last compilation.

## Three-Round Review Gate

Before delivery, perform three separate passes and record unresolved items:

1. **Mathematics:** formulas, variables, superscripts/subscripts, hypotheses,
   conclusions, theorem numbering, assumptions, and equation references.
2. **Terminology:** consistent Chinese renderings, first-use English notes,
   untranslated ordinary English, and forbidden legacy variants.
3. **Layout:** theorem/definition numbering, cross-links, table of contents,
   page numbers, running heads and footers, footnotes, figures, bibliography,
   cover metadata, front-matter spacing, and final-page completeness.

Compilation success is necessary but not sufficient: a document that compiles
while dropping content, breaking links, or changing mathematical meaning fails
the review gate.
