# MathTranslations Template

在用户选择 `MathTranslations` 时使用 `assets/templates/mathtranslations-template/`。

## 结构与约束

- 每个新任务先询问本次模板，当前已明确选本模板则直接采用，同任务继续不重问。
- 复制整个模板目录，保留 `template.tex`、`anime-character-cover-badge.png`、`compile.sh`、`.latexmkrc`、`portable-math-fonts.sty`、`chinese-headings.sty` 和完整 `fonts/`（含清单、Noto Serif CJK SC SemiBold 字体及其 OFL 等许可）。
- 保留 `fontset=none` 并由相对路径字体样式显式配置，使用 XeLaTeX 编译；不依赖 macOS 字体或空分支 fallback。正文/证明/例题宋体、定理陈述仿宋、术语楷体；内页中文标题用 Noto Serif CJK SC SemiBold（600），西文标题与编号用 CMU Serif Bold，译校注标题仍用宋体粗体。数学 Computer Modern/AMS/RSFS，正文12pt和1.3倍行距。完整角色与验收见[字体约定](font-policy.md)。
- 中文 `template.tex` 显式加载 `\usepackage[chinese]{chinese-headings}`；数学环境名称与编号按对应正文正体“设”（仿宋或宋体 Regular）的字面中心分别校准，保留原生 CJKglue、字号、编号内容和公式，不套固定偏移或冻结整个名称盒。附加样式默认及 `[english]` 不作修改；英文等非中文原语言重排任务不启用 `[chinese]`，共享 `portable-math-fonts.sty` 与西文字形保持。更新只用于新中文工程或已授权迁移，不改封面。
- 先替换模板开头的书目信息宏，再删除或改写示例正文。示例中的《代数学》内容不是用户源文档的证据。
- 封面题名固定为中文一行、原文一行，共两行。`\MTCoverTitleLine` 按可用宽度实测字体并递减字号，保持完整题名；`\BookTitleCN` / `\BookTitleEN` 内不插入 `\\` / `\newline`。不使用缩放盒或删短题名凑行。特长题名先调整 `\MTCoverTitleIndent` 等封面参数；最小字号仍超宽时会明确报错，不静默折成四行。替换真实题名后必须看封面。
- 作者及正文、标题、图内的人名保留源拼写，不音译，重音符号、连字符与大小写一并核对；具体边界见[术语政策](terminology-policy.md)。
- 保留章节式标题、中文定理环境、例/注菱形结束符、证明方块结束符、术语索引、习题/答案互链和长证明双向链接，除非用户明确要求改变版式。
- 人物徽记是彩色、不透明的暖纸色徽章，不要把它当作透明立绘；替换图片时应检查封面背景、尺寸和边缘是否协调。
- 人物素材的来源和许可未知。若要公开发布或再分发，先确认授权，必要时换成已获许可的素材。

## 验证

```bash
./compile.sh template.tex
```

检查编译日志中没有致命错误、未定义引用、重复标签或 `Overfull`，并目视检查封面、定理/证明页、长证明返回链接、附录答案和术语索引。编译产生的辅助文件由目录内 `.gitignore` 忽略，不应提交到仓库。

另用 `validate_font_bundle.py PROJECT --main MAIN.tex` 核字体资源及哈希，用 `validate_project_fonts.py MAIN.pdf --log MAIN.log` 核实际嵌入、缺字和字体替代；这些不能代替逐角色看页。
