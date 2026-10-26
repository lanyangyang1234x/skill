#!/usr/bin/env python3
"""Exercise real Chinese alignment and the English no-op path with XeLaTeX."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import unittest

try:
    import pymupdf
    from fontTools.ttLib import TTFont
    from fontTools.pens.boundsPen import BoundsPen
except ImportError:
    pymupdf = None

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'assets/templates/sage-olive-template'

DOCUMENT = r'''\documentclass[12pt]{article}
\usepackage[paperwidth=17cm,paperheight=24cm,margin=2cm]{geometry}
\usepackage{portable-math-fonts}
PROFILE
\usepackage{hyperref}
PROOFLAYER
\newtheoremstyle{fixture}{6pt}{6pt}{\theoremfont}{0pt}{\headingfont}
 {PUNCT}{.5em}{HEAD}
\theoremstyle{fixture}
\newtheorem{corollary}{NAME}[section]
\newtheorem{englishclaim}{Theorem}
\newtheorem*{starred}{NAME}
\providecommand{\corollaryautorefname}{推论}
\begin{document}
\setcounter{section}{5}\setcounter{corollary}{2}
\begin{corollary}\label{c:test}
BODY
\end{corollary}
\begin{proof}[PROOF]
The equality \(a=b\) implies \(b=a\).
\end{proof}
\begin{englishclaim}English names retain normal word spacing.\end{englishclaim}
\begin{starred}BODY\end{starred}
\end{document}
'''

BASE_CHINESE_FONT = r'''\setCJKfamilyfont{fixtureheading}[Path=fonts/,
 BoldFont=NotoSerifCJKsc-SemiBold.otf,
 ItalicFont=NotoSerifCJKsc-SemiBold.otf,
 BoldItalicFont=NotoSerifCJKsc-SemiBold.otf]{NotoSerifCJKsc-SemiBold.otf}
\renewcommand{\headingfont}{\normalfont\rmfamily\bfseries\CJKfamily{fixtureheading}}
'''


@unittest.skipUnless(pymupdf and shutil.which('xelatex'), 'XeLaTeX, PyMuPDF and fontTools required')
class ChineseHeadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='chinese-headings-')
        cls.project = Path(cls.temp.name)
        shutil.copytree(TEMPLATE / 'fonts', cls.project / 'fonts')
        for name in ['portable-math-fonts.sty', 'chinese-headings.sty']:
            shutil.copy2(TEMPLATE / name, cls.project / name)
        cls.outputs = {}
        main = (TEMPLATE / 'template.tex').read_text()
        cls.proof_layer = re.search(r'\\makeatletter\n\\renewenvironment\{proof\}.*?\\makeatother', main, re.S).group(0)
        # Neither English path may load the new Chinese font at all.
        font = cls.project / 'fonts/NotoSerifCJKsc-SemiBold.otf'
        held = font.with_suffix('.withheld')
        font.rename(held)
        for name, profile, helpers in [
            ('english-base', '', False),
            ('english-optout', r'\usepackage[english]{chinese-headings}', True),
            ('english-default', r'\usepackage{chinese-headings}', True),
        ]:
            cls.build(name, profile, helpers, chinese=False)
        held.rename(font)
        cls.build('chinese-base', BASE_CHINESE_FONT, False, chinese=True)
        cls.build('chinese-centred', r'\usepackage[chinese]{chinese-headings}', True, chinese=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def build(cls, name, profile, helpers, chinese):
        body = (r'设 \(A\) 与 \(B\) 为基本有限维 \(k\)-代数，且 \(A\) 的整体维数有限。'
                r'若 \(F:D^b(A)\to D^b(B)\) 是三角等价，则 \(B\) 的整体维数也有限。') if chinese else (
                r'Let \(A\) and \(B\) be finite dimensional algebras. If \(A=B\), then \(B=A\).')
        source = DOCUMENT.replace('PROFILE', profile).replace('NAME', '推论' if chinese else 'Corollary')
        source = source.replace('PROOFLAYER', cls.proof_layer if helpers else '')
        source = source.replace('PUNCT', r'\ChineseHeadingPunctuation{.}' if helpers else '.')
        source = source.replace('HEAD', r'\ChineseStatementHead{#1}{#2}{#3}' if helpers else '')
        proof = r'证明（\autoref{c:test}）' if chinese and helpers else 'Proof'
        source = source.replace('PROOF', proof).replace('BODY', body)
        (cls.project / (name + '.tex')).write_text(source)
        env = dict(os.environ, TFMFONTS='./fonts/math//:' + os.environ.get('TFMFONTS', ''))
        for _ in range(2):
            result = subprocess.run(['xelatex', '-interaction=nonstopmode', '-halt-on-error', name + '.tex'],
                                    cwd=cls.project, env=env, capture_output=True, text=True, timeout=90)
            if result.returncode:
                raise AssertionError(result.stdout[-5000:])
        cls.outputs[name] = cls.project / (name + '.pdf')

    def test_english_profiles_preserve_text_and_pixels_without_chinese_font(self):
        before = pymupdf.open(self.outputs['english-base'])
        for name in ['english-optout', 'english-default']:
            after = pymupdf.open(self.outputs[name])
            self.assertEqual(len(before), len(after))
            for a, b in zip(before, after):
                self.assertEqual(a.get_text(), b.get_text())
                self.assertEqual(a.get_pixmap(dpi=96).samples, b.get_pixmap(dpi=96).samples)
            self.assertFalse(any('NotoSerif' in f[3] for p in after for f in p.get_fonts()))

    def test_chinese_line_breaks_and_mixed_proof_label(self):
        before = pymupdf.open(self.outputs['chinese-base'])
        after = pymupdf.open(self.outputs['chinese-centred'])
        self.assertEqual(len(before), len(after))
        # The changed proof name is deliberate; theorem text wrapping must stay.
        text = ''.join(p.get_text() for p in after)
        for expected in ['设A', 'Theorem', '证明']:
            self.assertIn(expected, ''.join(text.split()))
        a = before[0].get_text().split('Proof')[0]
        b = after[0].get_text().split('证明')[0]
        self.assertEqual(a, b)
        for page in after:
            for link in page.get_links():
                if link['kind'] == pymupdf.LINK_GOTO:
                    self.assertGreaterEqual(link['page'], 0)

    def test_name_number_and_fangsong_ink_centres_agree(self):
        doc = pymupdf.open(self.outputs['chinese-centred'])
        spans = [s for b in doc[0].get_text('dict')['blocks']
                 for line in b.get('lines', []) for s in line['spans']]
        name = next(s for s in spans if s['text'] == '推论')
        number = next(s for s in spans if '5.3' in s['text'] and s['font'] == 'CMUSerif-Bold')
        body = next(s for s in spans if s['text'].startswith('设') and s['font'] == 'FandolFang-Regular')
        def centre(span, file, text):
            font = TTFont(self.project / 'fonts' / file)
            glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
            bounds = []
            for char in text:
                pen = BoundsPen(glyphs)
                glyphs[cmap[ord(char)]].draw(pen)
                if pen.bounds:
                    bounds.append(pen.bounds)
            mid = (min(b[1] for b in bounds) + max(b[3] for b in bounds)) / 2
            return span['origin'][1] - mid / font['head'].unitsPerEm * span['size']
        values = [centre(name, 'NotoSerifCJKsc-SemiBold.otf', '推论'),
                  centre(number, 'cmunbx.otf', '5.3'),
                  centre(body, 'FandolFang-Regular.otf', '设')]
        self.assertLess(max(values) - min(values), .003)


if __name__ == '__main__':
    unittest.main()
