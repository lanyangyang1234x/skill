# Chinese Template Project v2

Use `assets/templates/chinese-template-project-v2/` when the project needs the
layout used by the extriangulated-category/Hovey project: A4 geometry, the
burgundy/gold chapter label, Chinese theorem names, clickable contents,
exercise/answer links, metadata credit line, and source-relative figure
insertion.

This template is a reusable presentation layer only. Do not copy the source
book's title, authors, abstract, bibliography, notation macros, figures, or
section files into a new project. Replace the metadata placeholders in
`template.tex`, then add translated content using a suitable chapter/section organization; serial work may keep a single main file.

For exact-appearance exchange diagrams, follow
[book-completion-and-figure-qa.md](book-completion-and-figure-qa.md): use a
source-pixel-locked crop or a verified label-only layer; native redrawing is
appropriate when the task permits mathematical-structure fidelity or improved
reading clarity. Do not claim a visually similar redraw preserves source pixels.

Validate matching projects with `scripts/validate_chinese_template_project.sh PROJECT MAIN.tex [--keep-aux] [--allow-anonymous]`. Anonymous credit may omit/clear the translator/tool display according to the project choice; remove sample values and inspect the final visible credit. A bibliography is checked when actually present; the template does not require an invented `mybibliography` environment. The validator runs two body passes before indexing and two after; continue if derived references are not stable.
