#!/usr/bin/env python3
"""Check that a portable font bundle cannot silently use external resources."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/validate_font_bundle.py'

class FontBundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='font-bundle-test-')
        self.base = Path(self.tmp.name)
        self.project = self.base / 'project'
        self.fonts = self.project / 'fonts'
        self.fonts.mkdir(parents=True)
        (self.fonts / 'font.otf').write_bytes(b'fixture font; no TeX or PDF build')
        self.style = self.project / 'portable-math-fonts.sty'
        self.style.write_text('fixture style')
        self.main = self.project / 'main.tex'
        self.main.write_text(r'\documentclass[12pt]{article}\usepackage{portable-math-fonts}')
        self.manifest = self.fonts / 'manifest.json'
        self.manifest.write_text(json.dumps({'files': {'font.otf': hashlib.sha256((self.fonts / 'font.otf').read_bytes()).hexdigest()}, 'style_sha256': hashlib.sha256(self.style.read_bytes()).hexdigest()}))

    def tearDown(self):
        self.tmp.cleanup()

    def check_result(self, expected):
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.project), '--main', 'main.tex'], capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)

    def test_complete_local_bundle_passes(self):
        self.check_result(0)

    def test_missing_font_fails(self):
        (self.fonts / 'font.otf').unlink()
        self.check_result(1)

    def test_changed_font_fails(self):
        (self.fonts / 'font.otf').write_bytes(b'changed')
        self.check_result(1)

    def test_changed_style_fails(self):
        self.style.write_text('changed')
        self.check_result(1)

    def add_companion(self):
        style = self.project / 'chinese-headings.sty'
        style.write_text('fixture Chinese-only heading profile')
        manifest = json.loads(self.manifest.read_text())
        manifest['companion_styles'] = {
            style.name: hashlib.sha256(style.read_bytes()).hexdigest()
        }
        self.manifest.write_text(json.dumps(manifest))
        return style

    def test_complete_companion_passes(self):
        self.add_companion()
        self.check_result(0)

    def test_changed_companion_fails(self):
        self.add_companion().write_text('stale heading calibration')
        self.check_result(1)

    def test_missing_companion_fails(self):
        self.add_companion().unlink()
        self.check_result(1)

    def test_external_companion_fails(self):
        style = self.add_companion()
        external = self.base / 'external-headings.sty'
        style.rename(external)
        style.symlink_to(external)
        self.check_result(1)

    def test_external_fonts_directory_symlink_fails(self):
        target = self.base / 'external-fonts'
        self.fonts.rename(target)
        self.fonts.symlink_to(target, target_is_directory=True)
        self.check_result(1)

    def test_external_style_symlink_fails(self):
        target = self.base / 'external-style.sty'
        self.style.rename(target)
        self.style.symlink_to(target)
        self.check_result(1)

    def test_external_resource_symlink_fails(self):
        f = self.fonts / 'font.otf'
        target = self.base / 'external.otf'
        f.rename(target)
        f.symlink_to(target)
        self.check_result(1)

    def test_missing_main_fails_with_diagnostic(self):
        self.main.unlink()
        self.check_result(1)

if __name__ == '__main__':
    unittest.main()
