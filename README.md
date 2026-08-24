<div align="center">

<h1>PDF 转中文 TeX</h1>

<p><strong>数学 PDF → 忠实中文 LaTeX → 可验证 PDF</strong></p>

<p>保留章节顺序、编号、公式、定理、证明、练习、图形、交叉引用与参考文献。</p>

<p><a href="#中文">中文</a> · <a href="#english">English</a> · <a href="#模板">模板</a> · <a href="#质量门">质量门</a></p>

</div>

> [!IMPORTANT]
> 原始渲染 PDF 是数学内容与结构的最终依据。编译成功只是语法信号；源文档对照、公式核验、图形 QA 和覆盖台账全部通过后，才算完成。

## 中文

`pdf-to-chinese-tex` 是面向数学 PDF、教材、讲义、论文和 Markdown 转录稿的 Codex 技能。它把可靠内容转换为真实 TeX，而不是把中文覆盖在原 PDF 上。

### 30 秒开始

```bash
git clone https://github.com/lanyangyang1234x/skill.git \
  ~/.codex/skills/pdf-to-chinese-tex
```

然后在 Codex 中调用：

```text
使用 $pdf-to-chinese-tex 将这本数学 PDF 翻译成中文 LaTeX 和 PDF。
```

技能会先让你选择模板，再按“源文件识别 → 术语/覆盖记录 → TeX 重建 → 编译 → 视觉验收”的顺序工作。若设置了 `CODEX_HOME`，把安装路径替换为 `$CODEX_HOME/skills/pdf-to-chinese-tex` 即可。

### 核心能力

| 内容保真 | 图形保真 |
| --- | --- |
| 原始 PDF 优先；Markdown 只作可靠底稿 | 一模一样模式默认使用源像素锁定裁图 |
| 保留编号、公式、交叉引用和大小写 | 困难交换图不手调 TikZ |

| 过程可追溯 | 运行可控 |
| --- | --- |
| `terminology.tsv`、`source-coverage.tsv`、`figure-manifest.tsv` | 分批台账、非变异预检和模板验证 |
| 源文件、裁图、翻译资产、发布资产分层 | SHA-256 锁定；二次 Python 运行不得覆盖已验证图 |

### 模板

| 模板 | 视觉与使用场景 |
| --- | --- |
| `Sage-Olive` | 随机风景封面、版权页、彩色数学环境、打包 Fandol/Libertinus 字体 |
| `Chinese Template` | 传统 `ctexart` 章节版式、定理环境、练习与答案互链、附录和参考文献 |
| `Chinese Template Project v2` | 本项目采用的 A4 酒红/金色章节层、中文定理环境、可点击目录、元数据署名和源图插入接口 |

三个模板均使用 XeLaTeX；Project v2 的可复用文件位于 [`assets/templates/chinese-template-project-v2/`](assets/templates/chinese-template-project-v2/)。

### 交换图：先保真，再谈重绘

| 判定 | 规则 |
| --- | --- |
| 拓扑简单 | 直线、规则网格、无回环/曲线/遮挡；最多 4 个节点、6 条箭头。TikZ 仍需通过同尺寸视觉差异检查。 |
| 几何困难 | 曲线、回环、平行重叠、对角线遮挡、长链、多层组合、超过阈值、立体/八面体/立方体语义；最终使用截图。 |
| 用户要求“一模一样” | 源像素锁定裁图是默认最终表示；TikZ 只是候选，不是自动替代。 |

详细判定、标签归属、混合策略和 Riehl 原书验证案例见 [`references/book-completion-and-figure-qa.md`](references/book-completion-and-figure-qa.md)。

### 质量门

- [ ] 源 PDF 已快照并校验 SHA-256、字节数和页数。
- [ ] 源页覆盖、术语、公式/数学和图形台账已关闭。
- [ ] 真实 TeX 交叉引用、编号和引用键通过检查。
- [ ] 代表性正文、公式、图形页、末页和目录已与源 PDF 对照。
- [ ] 透明图在非白背景和最终 PDF 中均无白底、光晕、裁切或缩放错误。
- [ ] 发布资产哈希与 `figure_asset_lock.py` 记录一致。

## 模板

### Chinese Template Project v2

这是本项目实际使用的可复用版式：A4、酒红/金色章节标题、中文定理层、可点击目录、练习—答案互链、元数据署名和源图物理宽度插入接口。模板本身不包含本书正文、图片、符号宏或参考文献。

入口文件、编译脚本和说明位于 [`assets/templates/chinese-template-project-v2/`](assets/templates/chinese-template-project-v2/)，选择规则位于 [`references/chinese-template-project-v2.md`](references/chinese-template-project-v2.md)。

## 常用命令

<details>
<summary>环境检查与编译</summary>

```bash
python3 scripts/preflight_environment.py
python3 scripts/preflight_environment.py --need-compile
python3 scripts/preflight_environment.py --need-pdf --need-render
```

只在确认扫描页或乱码页后考虑 OCR；图片裁切和透明度检查只需要 Pillow，不需要安装 PaddleOCR。

</details>

<details>
<summary>术语、覆盖与图形台账</summary>

```bash
python3 scripts/terminology_ledger.py terminology.tsv --init
python3 scripts/terminology_ledger.py terminology.tsv --check

python3 scripts/source_coverage_ledger.py source-coverage.tsv --init
python3 scripts/source_coverage_ledger.py source-coverage.tsv \
  --check --first-page 1 --last-page 500

python3 scripts/figure_manifest_ledger.py figure-manifest.tsv --init
python3 scripts/figure_manifest_ledger.py figure-manifest.tsv --check --require-complete
```

</details>

<details>
<summary>不可覆盖的图资产流程</summary>

```bash
python3 scripts/figure_asset_lock.py record work/figure-lock.json \
  assets/exact/FIGURE.png work/source-renders/SOURCE_PAGE.png \
  --page 1 --dpi 600 --crop '[x0,y0,x1,y1]' \
  --method source-pixel-locked --run-id RUN_ID

python3 scripts/figure_asset_lock.py check work/figure-lock.json
```

源渲染、原始裁图、翻译/透明资产和 `assets/exact/` 发布资产必须分目录保存。裁图脚本遇到同名文件默认失败；重跑请使用新的 run 目录，不能从透明或已翻译衍生图再次裁剪。

</details>

<details>
<summary>项目验证与长书批次</summary>

```bash
# Sage-Olive
scripts/validate_sage_project.sh PROJECT_DIR MAIN.tex

# Chinese Template / Project v2
scripts/validate_chinese_template_project.sh PROJECT_DIR MAIN.tex

python3 scripts/batch_checkpoint.py batch-checkpoints.tsv --init
python3 scripts/batch_checkpoint.py batch-checkpoints.tsv --check --project-dir PROJECT_DIR
```

长书按 4–6 页或一个连贯小节分批；每批一个写者、目标文件互斥，公共台账由协调者合并。

</details>

### 仓库结构

```text
.
├── SKILL.md
├── agents/openai.yaml
├── assets/templates/
│   ├── sage-olive-template/
│   ├── chinese-template/
│   └── chinese-template-project-v2/
├── references/
└── scripts/
```

### 重要原则

- 不使用 PDF 文字覆盖作为最终翻译方式。
- 不擅自总结、删节、改写或重排原文。
- 不因模板限制而省略公式、证明、练习或图片。
- 图片中的普通英文标签需要翻译；数学符号和不应翻译的人名保持原样。
- OCR 只用于定位和初步转录；标题、作者、图注、标签和封面大小写必须回看源 PDF。
- 编译成功不等于内容验收通过。

<details>
<summary>English documentation</summary>

## English

`pdf-to-chinese-tex` is a Codex skill for faithfully converting mathematical PDFs, books, lecture notes, papers, and Markdown transcriptions into Chinese LaTeX and PDF. It preserves source order, numbering, notation, formulas, theorem/proof structure, exercises, figures, cross-references, and bibliography content.

### Highlights

- Choose `Sage-Olive`, `Chinese Template`, or `Chinese Template Project v2` at the start of every new translation task.
- Treat the rendered source PDF as authoritative; use Markdown as a read-only drafting scaffold when reliable.
- Keep terminology, source-page coverage, figure provenance, and batch checkpoints in durable ledgers.
- In exact-appearance mode, use source-pixel-locked crops by default; difficult exchange diagrams must not be hand-redrawn in TikZ.
- Reject silent figure overwrites and verify promoted assets with SHA-256 before compilation and release.
- Treat compilation success and source fidelity as separate acceptance gates.

### Templates

| Template | Description |
| --- | --- |
| `Sage-Olive` | Random landscape cover, copyright page, colored mathematical environments, bundled Fandol/Libertinus fonts |
| `Chinese Template` | `ctexart`, chapter-style headings, theorem environments, linked exercises and answers, appendices, bibliography |
| `Chinese Template Project v2` | A4 burgundy/gold chapter layer, Chinese theorem layer, clickable contents, metadata credit line, source-relative figure insertion |

### Fidelity principles

- Never use translated PDF text overlays as the final output.
- Do not summarize, omit, modernize, or reorder source content.
- Translate ordinary English labels inside figures while preserving mathematical symbols and personal names when appropriate.
- Treat OCR output as a locator, not a capitalization authority.
- A successful build is not sufficient; compare the final output with the source PDF.

</details>

## Third-party assets

Bundled fonts and other third-party assets retain their upstream copyrights and licenses. Review the applicable upstream terms before redistributing this repository or derived packages.
