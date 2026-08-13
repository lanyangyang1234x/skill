# PDF to Chinese TeX

[中文](#中文) · [English](#english)

## 中文

`pdf-to-chinese-tex` 是一个面向数学 PDF、教材、讲义、论文和 Markdown 转录稿的 Codex 技能。它将原始材料忠实转换为中文 LaTeX 与 PDF，同时保留章节顺序、编号、数学符号、公式、定理、证明、练习、图片、交叉引用和参考文献。

### 主要特性

- 每个新翻译任务开始时，先询问使用 `Sage-Olive` 还是 `Chinese Template`。
- 如果任务包含对应的 Markdown 文件，直接在该文件上翻译和修订，不另建重复译稿。
- 以原始 PDF 为最终依据，只对 Markdown 缺失、乱码或结构不清的部分重新提取或 OCR。
- 使用 `terminology.tsv` 统一数学术语，并审计英文残留和禁用旧译名。
- 使用 `source-coverage.tsv` 检查长书的漏页、重叠页、乱序范围和未完成条目。
- 使用 `figure-manifest.tsv` 跟踪图片来源、裁切、尺寸、背景、标签翻译和最终验收状态。
- 将“能否编译”与“是否忠于原文”作为两项独立的质量检查。

### 模板

| 模板 | 特点 |
| --- | --- |
| `Sage-Olive` | 随机风景封面、版权页、彩色数学环境、打包的 Fandol 与 Libertinus 字体 |
| `Chinese Template` | `ctexart`、章节式大标题、定理环境、练习与答案互链、附录和参考文献版式 |

两个模板均使用 XeLaTeX。Sage-Olive 所需字体已随仓库打包，不依赖系统字体。

### 安装

克隆到 Codex 技能目录：

```bash
git clone https://github.com/lanyangyang1234x/skill.git \
  ~/.codex/skills/pdf-to-chinese-tex
```

如果设置了 `CODEX_HOME`，可改用：

```bash
git clone https://github.com/lanyangyang1234x/skill.git \
  "$CODEX_HOME/skills/pdf-to-chinese-tex"
```

重新启动 Codex 或打开一个新任务，使技能被重新发现。

### 环境检查

核心环境需要 Python 3.9+、PyMuPDF、XeLaTeX 和 Poppler 的 `pdftoppm`：

```bash
python3 scripts/preflight_environment.py
```

只有扫描页或乱码页需要 OCR。可选 OCR 环境通过以下命令建立：

```bash
scripts/bootstrap_ocr_environment.sh
python3 scripts/preflight_environment.py --require-ocr
```

### 使用方式

在 Codex 中调用技能，例如：

```text
使用 $pdf-to-chinese-tex 将这本数学 PDF 翻译成中文 LaTeX 和 PDF。
```

技能首先要求选择模板，然后执行环境检查、源文件分析、术语与覆盖记录、翻译重建、编译以及视觉验收。

如果同时提供 PDF 和 Markdown，Markdown 是直接编辑的文字底稿，PDF 是校对公式、图片、编号和版式的权威来源。

### 术语台账

```bash
python3 scripts/terminology_ledger.py terminology.tsv --init
python3 scripts/terminology_ledger.py terminology.tsv --check
python3 scripts/terminology_ledger.py terminology.tsv --audit SOURCE.md PROJECT_DIR
```

术语状态包括：

- `verified`：已有可靠依据；
- `provisional`：暂定译名，等待进一步核对；
- `user-supplied`：由用户指定。

正文第一次重要出现通常写作“中文（English）”，后续统一使用中文。人名保持原文拼写，例如 `Nakayama 引理`。

### 长书与图片记录

```bash
python3 scripts/source_coverage_ledger.py source-coverage.tsv --init
python3 scripts/source_coverage_ledger.py source-coverage.tsv \
  --check --first-page 1 --last-page 500

python3 scripts/figure_manifest_ledger.py figure-manifest.tsv --init
python3 scripts/figure_manifest_ledger.py figure-manifest.tsv \
  --check --require-complete
```

### 项目验证

```bash
# Sage-Olive
scripts/validate_sage_project.sh PROJECT_DIR MAIN.tex

# Chinese Template
scripts/validate_chinese_template_project.sh PROJECT_DIR MAIN.tex
```

验证器会检查模板结构、术语台账、图片清单、引用和编译日志；存在图片时还会生成图片页联系表，供最终视觉检查。

### 目录结构

```text
.
├── SKILL.md
├── agents/openai.yaml
├── assets/templates/
│   ├── sage-olive-template/
│   └── chinese-template/
├── references/
└── scripts/
```

### 重要原则

- 不使用 PDF 文字覆盖作为最终翻译方式。
- 不擅自总结、删节、改写或重排原文。
- 不因模板限制而省略公式、证明、练习或图片。
- 图片中的普通英文标签需要翻译；数学符号和不应翻译的人名保持原样。
- 编译成功不等于内容验收通过，最终仍需与原始 PDF 对照检查。

## English

`pdf-to-chinese-tex` is a Codex skill for faithfully converting mathematical PDFs, books, lecture notes, papers, and Markdown transcriptions into Chinese LaTeX and PDF. It preserves source order, numbering, notation, formulas, theorem/proof structure, exercises, figures, cross-references, and bibliography content.

### Highlights

- Ask the user to choose `Sage-Olive` or `Chinese Template` at the start of every new translation task.
- Edit an associated Markdown transcription in place instead of creating a duplicate translation file.
- Treat the source PDF as authoritative and extract or OCR only content that is missing, garbled, or structurally ambiguous in Markdown.
- Maintain `terminology.tsv` to enforce mathematical terminology and audit untranslated source terms or forbidden legacy translations.
- Maintain `source-coverage.tsv` to detect missing, overlapping, out-of-order, or incomplete book coverage.
- Maintain `figure-manifest.tsv` to track source bounds, display size, background handling, label translation, and final figure QA.
- Treat compilation success and source fidelity as separate acceptance gates.

### Templates

| Template | Description |
| --- | --- |
| `Sage-Olive` | Random landscape cover, copyright page, colored mathematical environments, and bundled Fandol/Libertinus fonts |
| `Chinese Template` | `ctexart`, chapter-style headings, theorem environments, linked exercises and answers, appendices, and bibliography layout |

Both templates compile with XeLaTeX. Sage-Olive bundles its required fonts and does not depend on system font installation.

### Installation

Clone the repository into the Codex skills directory:

```bash
git clone https://github.com/lanyangyang1234x/skill.git \
  ~/.codex/skills/pdf-to-chinese-tex
```

If `CODEX_HOME` is configured, use:

```bash
git clone https://github.com/lanyangyang1234x/skill.git \
  "$CODEX_HOME/skills/pdf-to-chinese-tex"
```

Restart Codex or open a new task so the skill can be rediscovered.

### Environment check

The core workflow requires Python 3.9+, PyMuPDF, XeLaTeX, and Poppler's `pdftoppm`:

```bash
python3 scripts/preflight_environment.py
```

OCR is optional and is needed only for scanned or garbled pages:

```bash
scripts/bootstrap_ocr_environment.sh
python3 scripts/preflight_environment.py --require-ocr
```

### Usage

Invoke the skill in Codex, for example:

```text
Use $pdf-to-chinese-tex to translate this mathematical PDF into Chinese LaTeX and PDF.
```

The skill first asks for a template choice, then performs environment checks, source analysis, terminology and coverage tracking, faithful reconstruction, compilation, and visual QA.

When both a PDF and Markdown file are supplied, the Markdown file is edited directly as the text scaffold, while the PDF remains authoritative for formulas, figures, numbering, and layout.

### Terminology ledger

```bash
python3 scripts/terminology_ledger.py terminology.tsv --init
python3 scripts/terminology_ledger.py terminology.tsv --check
python3 scripts/terminology_ledger.py terminology.tsv --audit SOURCE.md PROJECT_DIR
```

Supported statuses are `verified`, `provisional`, and `user-supplied`. At the first important occurrence, use `中文（English）`; use the Chinese term consistently afterward. Keep personal names in the source spelling, for example `Nakayama 引理`.

### Book and figure ledgers

```bash
python3 scripts/source_coverage_ledger.py source-coverage.tsv --init
python3 scripts/source_coverage_ledger.py source-coverage.tsv \
  --check --first-page 1 --last-page 500

python3 scripts/figure_manifest_ledger.py figure-manifest.tsv --init
python3 scripts/figure_manifest_ledger.py figure-manifest.tsv \
  --check --require-complete
```

### Project validation

```bash
# Sage-Olive
scripts/validate_sage_project.sh PROJECT_DIR MAIN.tex

# Chinese Template
scripts/validate_chinese_template_project.sh PROJECT_DIR MAIN.tex
```

The validators check template structure, terminology, figure manifests, references, and build logs. Figure-bearing projects also receive rendered contact sheets for final visual inspection.

### Repository layout

```text
.
├── SKILL.md
├── agents/openai.yaml
├── assets/templates/
│   ├── sage-olive-template/
│   └── chinese-template/
├── references/
└── scripts/
```

### Fidelity principles

- Never use translated PDF text overlays as the final output.
- Do not summarize, omit, modernize, or reorder source content.
- Do not drop formulas, proofs, exercises, or figures to accommodate a template.
- Translate ordinary English labels inside figures while preserving mathematical symbols and personal names when appropriate.
- A successful build is not sufficient; the final output must still be compared against the source PDF.

## Third-party assets

Bundled fonts and other third-party assets retain their upstream copyrights and licenses. Review the applicable upstream terms before redistributing this repository or derived packages.
