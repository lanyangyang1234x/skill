<div align="center">

<h1>PDF 转中文 TeX</h1>

<p><strong>3.2 · 数学 PDF → 忠实中文 LaTeX → 可验证 PDF</strong></p>

<p>保留章节顺序、编号、公式、定理、证明、练习、图形、交叉引用与参考文献。</p>

<p><a href="#中文">中文</a> · <a href="#english">English</a> · <a href="#模板">模板</a> · <a href="#质量门">质量门</a></p>

</div>

> [!IMPORTANT]
> 原始渲染 PDF 及用户已确认的勘误/补充决定数学内容与结构。编译成功只是构建信号；按当前任务范围分别记录原书对照、数学、术语、中文表达、图表、链接和发布重建结果，不能将定点修订标成全书审计通过。

## 中文

`pdf-to-chinese-tex` 是面向数学 PDF、教材、讲义、论文和 Markdown 转录稿的 Codex 技能。它把可靠内容转换为真实 TeX，而不是把中文覆盖在原 PDF 上。

### 30 秒开始

```bash
git clone https://github.com/lanyangyang1234x/skill.git \
  ~/.agents/skills/pdf-to-chinese-tex
```

上述是来源仓库安装方式；本地交付的 3.2 源包以实际版本为准，安装本地源包时保留旧技能后复制完整目录。然后在 Codex 中调用：

```text
使用 $pdf-to-chinese-tex 将这本数学 PDF 翻译成中文 LaTeX 和 PDF。
```

每个新任务必须询问本次模板：新项目列出可用模板，既有项目询问沿用现工程还是改用指定模板。本次请求已明确模板或要求保持现有版式时视为已回答；同一任务“继续”不重问。未回答前可盘点源文，不自动套用 Sage-Olive 或迁移版式。未知署名留空或匿名，不阻塞译写。工作顺序是：

`识别任务与保护范围` → `源文件/台账核验` → `按批译写与审校` → `编译与成书检查` → `交付包独立重建`

书籍每一批默认经过：`译写` → `数学与术语核对` → `中文句群审校` → `数学保护复核` → `编译合入`。中文表达审校是翻译流程的一部分，无需另行要求；中文改句后仍须核条件、量词、对象、证明和公式保护，才能合入。

默认安装路径为：

```text
~/.agents/skills/pdf-to-chinese-tex
```

只保留一个可发现的安装入口；旧副本和备份移到 skills 扫描目录之外，不能在 `~/.codex/skills` 与 `~/.agents/skills` 同时安装同一技能。

### 核心能力

3.2 在既有项目经验与中文方法接入的基础上，精简主入口、按任务加载专题，并修复工具与工作流的契约问题。新建翻译、既有项目审计和定点修订使用各自的改动范围；书籍翻译默认每批完成中文句群审校，再做数学保护复核。保护个人批注、正确图形和已确认的版式；改善中文语序与衔接时保持假设、量词、证明步骤、公式和源文单元。

| 内容保真 | 图形保真 |
| --- | --- |
| 原始 PDF 优先；Markdown 只作可靠底稿 | 原生 TikZ 优先；明确要求 TikZ 时不得用截图替代 |
| 保留编号、公式、交叉引用和大小写 | 逐项核标签位置、箭头样式、坐标与尺寸比例 |
| 中文表达与数学含义分别审校；原书疑误单列 | 源书与 TeX 双向图清单，包含 XY-pic 和行内图式 |

| 过程可追溯 | 运行可控 |
| --- | --- |
| `terminology.tsv`、`source-coverage.tsv`、`figure-manifest.tsv` | 分批台账、非变异预检和模板验证 |
| 源文件、裁图、翻译资产、发布资产分层 | SHA-256 锁定；二次 Python 运行不得覆盖已验证图 |
| 记录实际审查范围和沿用证据 | 最终 ZIP 全新解压并独立构建；归档完整性不替代重建 |

### chinese-writing：固定快照与数学适配

内置 [Ou-Liu-Red-Sugar/chinese-writing](https://github.com/Ou-Liu-Red-Sugar/chinese-writing) **2.13.3**，固定提交 `9818d89aee474ef813f9c5d8a6164e0cb265fe1b`。完整 46 文件上游源码保留在 [`vendor/chinese-writing-upstream.zip`](vendor/chinese-writing-upstream.zip)，日常只读 [`vendor/chinese-writing/`](vendor/chinese-writing/) 中的 38 文件方法库，数学翻译入口是 [`references/chinese-writing-integration.md`](references/chinese-writing-integration.md)。按当前问题读取句子、衔接、标点和限定语方法，日常使用不联网更新，也不需要另装上游技能。

中文句群审校默认嵌入书籍每批翻译，不作为需要另行开启的选项。忠实翻译使用原书结构审校中文，不为顺句新增数学理由、删除原书重复或启动整篇原创文章的审批流程。用户另行授权的导读、注释和报告可以使用相应写作流程，并与译文分开。快照完整性检查只证明文件一致，不能证明中文审校或数学验证已经完成。

```bash
python3 scripts/verify_chinese_writing_vendor.py
```

来源、更新规则及 MIT/教学示例 CC BY-NC-SA 4.0 的区别见适配入口与上游 [`THIRD_PARTY_NOTICES.md`](vendor/chinese-writing/THIRD_PARTY_NOTICES.md)。

### 模板

| 模板 | 视觉与使用场景 |
| --- | --- |
| `Sage-Olive` | 随机风景封面、版权页、彩色数学环境、打包 Fandol/CMU 与 CM/AMS/RSFS 字体 |
| `Chinese Template Project v2` | 本项目采用的 A4 酒红/金色章节层、中文定理环境、可点击目录、元数据署名和源图插入接口 |
| `MathTranslations` | 彩色暖纸封面、动漫人物徽记、中文定理环境、术语索引、长证明和习题/答案双向链接 |

三个模板均使用 XeLaTeX 与完整相对路径字体包；正文/证明/例题宋体、定理陈述仿宋、术语楷体、标题黑体配 CMU Serif 粗体，正文 12pt、1.3 倍行距。完整角色与嵌入验收见 [字体约定](references/font-policy.md)。Project v2 的可复用文件位于 [`assets/templates/chinese-template-project-v2/`](assets/templates/chinese-template-project-v2/)，MathTranslations 位于 [`assets/templates/mathtranslations-template/`](assets/templates/mathtranslations-template/)。

### 图形：按当前目标选择方法

| 判定 | 规则 |
| --- | --- |
| 明确要求 TikZ 或全部原图用 TikZ | 指定范围全部原生 TikZ/TikZ-CD；同时核原书标签内容与位置、节点、箭头起止/头型/虚实/路径、填充和尺寸比例。不能以截图、描边字形或拓扑近似代替。 |
| 源图外观精确一致 | 可核验的原生重建；未限定原生方法且需要保留源像素或只改文字时，可用像素锁定裁图或标签混合层。 |
| 数学结构保真 | TikZ、tikz-cd、既有 XY-pic、源裁图或混合方法均可；逐项核节点、方向、箭型、路径、标签和关系。 |
| 阅读清晰 | 在保留数学结构的前提下选择可核验且易读的方法，可适度调整尺寸与间距，并记录呈现变化。 |

默认优先原生 TikZ/TikZ-CD；节点数、箭头数或弯箭的存在不是固定门槛。严格 TikZ 范围中读不清的细节应回查原页并单列，不能悄换截图。保留正确既有图形与用户限定的简单图/局部范围。禁止用 `resizebox`、`scalebox`、`adjustbox` 或整图 `scale` 压缩图/表格掩盖溢出；修正原生间距和版面后重验。图内普通英文需要翻译，数学符号和人名按其身份保留。裁图资产检查之外，还须核最终 PDF 的实际图像、透明蒙版、使用次序、尺寸与页位置，并查看改动影响的邻页。

双向图清单、标签归属、透明化边界与精确模式见 [`references/book-completion-and-figure-qa.md`](references/book-completion-and-figure-qa.md)。这些是工作要求，台账脚本不会自动发现所有源图或证明成品中的图形正确。

### 质量门

- [ ] 本次模板已询问并确认；完整字体与许可随包，缺字/替代及实际嵌入已核。
- [ ] 源 PDF 已快照并校验 SHA-256、字节数和页数。
- [ ] 授权范围内的源页覆盖、术语、中文表达、公式/数学和图形结果分别记录；排除项与剩余项明确。
- [ ] 真实 TeX 交叉引用、编号和引用键通过检查。
- [ ] 原书与 TeX 双向图清单完成，编号图、XY-pic、行内小图、图式与全部最终使用位置对应。
- [ ] 当前任务所需的正文、公式、图形页、末页、目录及受影响邻页已核对；逐页任务有实际逐页覆盖证据。
- [ ] 透明图在非白背景和最终 PDF 中均无白底、光晕、裁切或缩放错误。
- [ ] 发布资产哈希与 `figure_asset_lock.py` 记录一致。
- [ ] 最终 PDF 的实际嵌入图像/透明蒙版/次序核验已记录；工具不可用时明确检查限制。
- [ ] 最终 ZIP 在新的空目录解压，仅用包内工程独立构建，并比较页数、正文、关键渲染和链接。

## 模板

### Chinese Template Project v2

这是本项目实际使用的可复用版式：A4、酒红/金色章节标题、中文定理层、可点击目录、练习—答案互链、元数据署名和源图物理宽度插入接口。模板本身不包含本书正文、图片、符号宏或参考文献。

入口文件、编译脚本和说明位于 [`assets/templates/chinese-template-project-v2/`](assets/templates/chinese-template-project-v2/)，选择规则位于 [`references/chinese-template-project-v2.md`](references/chinese-template-project-v2.md)。

### MathTranslations

这是一个独立的彩色数学中文译本变体：暖纸色封面、动漫人物徽记、中文定理环境、术语索引、长证明双向跳转以及习题—答案互链。入口文件和编译说明位于 [`assets/templates/mathtranslations-template/`](assets/templates/mathtranslations-template/)，使用前请确认人物素材的再分发许可。

## 工具与适用范围

以下命令以 skill 根目录为参考；在任务目录执行时，把脚本换成实际的绝对路径，并显式传项目/主文件。只运行当前任务适用的工具，不把所有检查套在定点修改上。

| 工具 | 适用范围与限制 |
|---|---|
| `preflight_environment.py` | 只查当前步骤需要的能力；不修改环境 |
| `source_manifest.py` | 临时/易丢来源的私有快照及身份核验 |
| 术语、覆盖、图形台账工具 | 长译稿/全文审计复用项目台账；工具验证格式、范围或状态，不证明实质审读 |
| `project_figure_usage.py` | 从主 TeX 输入图检测常见实际图式调用，忽略注释/宏定义；用于验证器路由，不能代替完整图清单 |
| `audit_bibliography.py` | 静态核引用键与实际书目范围/目录登记；不证明最终标题或点击目标，也不展开任意宏 |
| `batch_checkpoint.py` | 并行/多阶段协调；`--check --require-complete --require-verified` 检查已结束的最新输出责任；不是全书覆盖验证 |
| 模板验证器 | 仅匹配模板；`--allow-anonymous` 支持已选匿名信用，Sage 另有 `--without-contents`；不自动修改呈现 |
| `package_release.py` | 含 PDF 发布包，验证归档后仍须独立解压重建；仅 TeX 的源包另见发布专题 |
| `validate_font_bundle.py` | 核字体及许可清单哈希，拒绝工程外符号链接；不证明样页角色和字号 |
| `validate_project_fonts.py` | 检查最终 PDF 字体嵌入及日志字体错误；不代替字体角色的实际样页核验 |
| `verify_chinese_writing_vendor.py` | 校验方法库、完整上游归档与同源哈希，不代表语言或数学审校 |

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

# Chinese Template Project v2
scripts/validate_chinese_template_project.sh PROJECT_DIR MAIN.tex

# MathTranslations
(cd PROJECT_DIR && ./compile.sh MAIN.tex)

python3 scripts/batch_checkpoint.py batch-checkpoints.tsv --init
python3 scripts/batch_checkpoint.py batch-checkpoints.tsv --check --project-dir PROJECT_DIR
```

长书按可核验的源页/完整单元分批；并行写入才要求目标文件互斥，公共台账由协调者合并。详见批次协调文档中的 claim、promote、后续 review 和发布检查。

</details>

### 仓库结构

```text
.
├── SKILL.md
├── agents/openai.yaml
├── assets/templates/
│   ├── sage-olive-template/
│   ├── chinese-template-project-v2/
│   └── mathtranslations-template/
├── references/
├── vendor/chinese-writing/
├── vendor/chinese-writing-upstream.zip
├── vendor/chinese-writing.lock.json
└── scripts/
```

### 重要原则

- 不以在原 PDF 整页覆盖中文作为最终译本；图内标签的局部 TeX 替换须有明确归属和保真检查。
- 不擅自总结、删节、改写或重排原文。
- 不因模板限制而省略公式、证明、练习或图片。
- 图片中的普通英文标签需要翻译；数学符号和不应翻译的人名保持原样。
- OCR 只用于定位和初步转录；标题、作者、图注、标签和封面大小写必须回看源 PDF。
- 编译成功不等于内容验收通过。
- 仅改变字体或环境显示名时，保持未授权的框线、底色、正文、内部环境名、编号和链接。
- 发布报告分别说明本轮实际审查和沿用的历史证据；固定快照、脚本检查和旧台账不代表行为测试已完成。
- `MathTranslations` 中的人物徽记来源和再分发许可需要在公开发布前单独确认。

<details>
<summary>English documentation</summary>

## English

`pdf-to-chinese-tex` is a Codex skill for faithfully converting mathematical PDFs, books, lecture notes, papers, and Markdown transcriptions into Chinese LaTeX and PDF. It preserves source order, numbering, notation, formulas, theorem/proof structure, exercises, figures, cross-references, and bibliography content.

### Highlights

- Version 3.2 supports new translation, existing-project audit, and targeted repair with separate scopes and evidence. Chinese expression review is integrated into every book-translation batch by default.
- Ask for the template at the beginning of every independent task, including whether an existing project should retain its template. An explicit current choice counts as an answer; continuations reuse it. Do not silently default to Sage-Olive. Unknown translator/tool credit may stay blank or anonymous.
- Treat the rendered source PDF as authoritative; use Markdown as a read-only drafting scaffold when reliable.
- Keep terminology, source-page coverage, figure provenance, and batch checkpoints in durable ledgers.
- Use the pinned `chinese-writing` 2.13.3 snapshot through [the mathematics adaptation](references/chinese-writing-integration.md); improve Chinese without adding source-absent arguments or applying an original-article approval workflow to ordinary translation.
- Each book batch proceeds through translation, mathematics/terminology checks, Chinese sentence-group review, mathematical protection checks, and compilation/merge; the user does not need to request Chinese review separately.
- Prefer editable native TikZ/TikZ-CD. Explicit native requirements prohibit raster substitution; exact native diagrams must match label positions, geometry and arrow styles as well as topology. Do not squeeze whole diagrams or tables with resizebox/scalebox/adjustbox or blanket scale wrappers. Source-pixel preservation remains available when no native requirement applies.
- Use portable Fandol/CMU font roles: Song for body/proofs/examples, Fang for theorem statements, Kai for terms, Hei and bold CMU Serif for headings; Computer Modern/AMS/RSFS for mathematics, 12pt body and 1.3 line spacing. Bundle licenses, inspect role-specific pages, and verify actual font embedding.
- Reconcile source figures with TeX in both directions, including XY-pic and inline diagrams, and check actual PDF occurrences, alpha masks, order, and affected neighboring pages.
- Reject silent figure overwrites and verify promoted assets with SHA-256 before compilation and release.
- Treat compilation, source fidelity, Chinese review, visual QA, and independent archive rebuild as separate acceptance gates. Snapshot/ledger checks do not establish completed behavioral tests.

### Templates

| Template | Description |
| --- | --- |
| `Sage-Olive` | Random landscape cover, copyright page, colored mathematical environments, bundled Fandol/CMU and CM/AMS/RSFS fonts |
| `Chinese Template Project v2` | A4 burgundy/gold chapter layer, Chinese theorem layer, clickable contents, metadata credit line, source-relative figure insertion |
| `MathTranslations` | Warm-paper color cover, anime character badge, Chinese theorem environments, terminology index, long-proof links, and linked exercises/answers |

### Fidelity principles

- Do not use full-page translated PDF overlays as the final edition; a verified figure-label layer is a distinct, local representation choice.
- Do not summarize, omit, modernize, or reorder source content.
- Translate ordinary English labels inside figures while preserving mathematical symbols and personal names when appropriate.
- Treat OCR output as a locator, not a capitalization authority.
- A successful build is not sufficient; compare the final output with the source PDF.
- Preserve personal annotations and unauthorized style dimensions; report the actual review scope and any inherited evidence.

</details>

## Third-party assets

Bundled fonts and other third-party assets retain their upstream copyrights and licenses. Review the applicable upstream terms before redistributing this repository or derived packages.
The `MathTranslations` anime badge is user-supplied artwork with unverified provenance; replace it or confirm permission before redistribution.

The pinned `chinese-writing` snapshot retains its upstream MIT license; the `examples/independence-correlation/` teaching example has a separate CC BY-NC-SA 4.0 license. See [`vendor/chinese-writing/THIRD_PARTY_NOTICES.md`](vendor/chinese-writing/THIRD_PARTY_NOTICES.md) and the [adaptation policy](references/chinese-writing-integration.md).


## 技能维护检查

修改协调工具或内置写作材料后，可运行以下离线回归；临时工程写入系统临时目录，不修改已安装模板或译稿。

```bash
python3 tests/test_batch_checkpoint.py
python3 tests/test_chinese_writing_vendor.py
python3 tests/test_project_fonts.py
python3 tests/test_font_bundle.py
python3 scripts/verify_chinese_writing_vendor.py
```

这些检查覆盖批次状态/哈希责任与固定快照完整性，不代表真实译稿的数学或中文审校完成。模板验证器的无图检测仅为静态工具路由，完整图形清单仍需源书与 TeX 双向核对。
