# MathTranslations Template

这是一个独立的彩色数学中文译本模板变体，适合希望使用章节式标题、中文定理环境、术语索引、习题/答案互链以及长证明双向跳转的项目。

## 文件

- `template.tex`：可直接修改的 XeLaTeX 模板与完整示例。
- `anime-character-cover-badge.png`：封面左下角的人物徽记。
- `template.pdf`：当前示例的编译预览。
- `compile.sh`、`.latexmkrc`：XeLaTeX 编译配置。

## 编译

在本目录执行：

```bash
./compile.sh template.tex
```

模板使用 `fontset=fandol`，需要安装 XeLaTeX 和 TeX Live 的 Fandol/Computer Modern Unicode 字体。

## 使用前修改

先修改 `template.tex` 开头的书目信息宏（例如 `\BookTitleCN`、`\Translator` 和 `\TranslationDate`），再替换示例正文。人物徽记可以直接替换为同名 PNG；如果更换文件名，也要同步修改 `\includegraphics`。

人物图是用户提供并经过版式处理的素材，来源和再分发许可未核实。公开发布译本或二次分发仓库前，请确认拥有相应使用权，或替换为已获许可的图片。

该目录是独立模板变体，不会覆盖仓库现有的 `assets/templates/chinese-template-project-v2/`。
