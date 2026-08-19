# Mathematical PDF Extraction

## Decision Rule

If the task includes an associated Markdown file, identify that exact file and use it as the primary transcription scaffold for the TeX project. Transfer reliable Markdown content into TeX in coherent batches; do not create a second Markdown translation or repeat extraction for text already represented there. Keep the Markdown read-only unless the user explicitly authorizes editing it. Compare it against the rendered PDF, which remains authoritative, and extract or OCR only missing, garbled, or structurally ambiguous regions.

Read the Markdown in manageable, page- or section-marked batches rather than loading the entire book into one context. Preserve its heading hierarchy, math delimiters, anchors, footnotes, image references, and page/source markers while converting them into real TeX. Inspect the TeX diff after each batch. Never run blind global terminology replacement across Markdown or TeX code fences, formulas, URLs, citation keys, or personal names. If several Markdown files are plausible and task context does not identify the associated source, ask before choosing one.

If no associated Markdown file exists, run `scripts/inspect_pdf_source.py` first. Treat its classification as guidance, not truth. When Markdown is present, do not run a redundant full-text extraction before drafting; inspect only the source pages needed to resolve uncertainties.

- Electronic: use `extract_pdf_text.py` blocks/dict output; no OCR.
- Scanned or garbled: render only the affected pages at 300-400 dpi and OCR prose only.
- Mixed: use embedded text where it is clean, render only flagged pages, and OCR only the bad ones.

## Output Boundary

Extraction is a scaffold, not the final translation. Use coordinates to recover reading order, anchors, crop bounds, and LaTeX structure, then rebuild the page as real TeX. Do not translate by overlaying Chinese onto the source PDF.

## OCR and Hyphenation

- Environment checks are non-mutating. Use `scripts/preflight_environment.py --need-pdf` for source inspection, add `--need-render` only for page rendering/crops, and use `--require-ocr` only after ordinary extraction confirms that OCR is actually needed.
- Never bootstrap the OCR virtual environment automatically. Run `scripts/bootstrap_ocr_environment.sh` only after the user approves the optional installation, and prefer an existing OCR/Python environment when available.
- Figure cropping/alpha checks need Pillow only; set `PDF_TO_CHINESE_TEX_IMAGE_PYTHON` to an existing Pillow-capable interpreter instead of installing PaddleOCR for that work.
- Use PP-OCRv6 for ordinary English prose on scanned pages when available.
- Preserve the rendered page's Latin-script capitalization exactly. OCR engines can normalize title case to all caps or lowercase; use OCR for localization and rough transcription only, then verify every prominent title, heading, label, caption, and credit against the rendered PDF or a crop of the source pixels.
- Reconstruct formulas, special alphabets, diagrams, and equation numbering separately and verify them manually.
- Join a line-ending hyphen only when the source layout proves it is a typesetting break, not a real compound.

## Authority

The rendered source page is authoritative. Extraction and OCR output only help locate and transcribe content.
