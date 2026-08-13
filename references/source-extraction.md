# Mathematical PDF Extraction

## Decision Rule

If the task includes an associated Markdown file, edit that exact file in place and treat it as the primary transcription scaffold. Do not create a second Markdown file or repeat extraction for text already represented there. Compare it against the rendered PDF, which remains authoritative, and extract or OCR only missing, garbled, or structurally ambiguous regions.

Read the complete Markdown file before editing. Preserve its heading hierarchy, math delimiters, anchors, footnotes, image references, and page/source markers unless the PDF proves they are wrong. Edit in coherent batches and inspect the diff after each batch. Never run blind global terminology replacement across code fences, formulas, URLs, citation keys, or personal names. If several Markdown files are plausible and task context does not identify the associated source, ask before modifying any of them.

If no associated Markdown file exists, run `scripts/inspect_pdf_source.py` first. Treat its classification as guidance, not truth.

- Electronic: use `extract_pdf_text.py` blocks/dict output; no OCR.
- Scanned or garbled: render only the affected pages at 300-400 dpi and OCR prose only.
- Mixed: use embedded text where it is clean, render only flagged pages, and OCR only the bad ones.

## Output Boundary

Extraction is a scaffold, not the final translation. Use coordinates to recover reading order, anchors, crop bounds, and LaTeX structure, then rebuild the page as real TeX. Do not translate by overlaying Chinese onto the source PDF.

## OCR and Hyphenation

- Use `scripts/bootstrap_ocr_environment.sh` and `scripts/preflight_environment.py --require-ocr` only when OCR is needed.
- Use PP-OCRv6 for ordinary English prose on scanned pages when available.
- Reconstruct formulas, special alphabets, diagrams, and equation numbering separately and verify them manually.
- Join a line-ending hyphen only when the source layout proves it is a typesetting break, not a real compound.

## Authority

The rendered source page is authoritative. Extraction and OCR output only help locate and transcribe content.
