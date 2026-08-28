# MathTranslations Template

在用户选择 `MathTranslations` 时使用 `assets/templates/mathtranslations-template/`。

## 结构与约束

- 复制整个模板目录，至少保留 `template.tex`、`anime-character-cover-badge.png`、`compile.sh` 和 `.latexmkrc`。
- 保留 `fontset=fandol`，使用 XeLaTeX 编译；不要改回依赖 macOS 专有字体的配置。
- 先替换模板开头的书目信息宏，再删除或改写示例正文。示例中的《代数学》内容不是用户源文档的证据。
- 保留章节式标题、中文定理环境、例/注菱形结束符、证明方块结束符、术语索引、习题/答案互链和长证明双向链接，除非用户明确要求改变版式。
- 人物徽记是彩色、不透明的暖纸色徽章，不要把它当作透明立绘；替换图片时应检查封面背景、尺寸和边缘是否协调。
- 人物素材的来源和许可未知。若要公开发布或再分发，先确认授权，必要时换成已获许可的素材。

## 验证

```bash
./compile.sh template.tex
```

检查编译日志中没有致命错误、未定义引用、重复标签或 `Overfull`，并目视检查封面、定理/证明页、长证明返回链接、附录答案和术语索引。编译产生的辅助文件由目录内 `.gitignore` 忽略，不应提交到仓库。
