#!/usr/bin/env python3
"""Regression checks for PDF embedding and actual LaTeX font diagnostics."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import inspect_build_log
import validate_project_fonts as validator


HEADER = "name                                 type              encoding         emb sub uni object ID\n------------------------------------ ----------------- ---------------- --- --- --- ---------\n"
EMBEDDED = HEADER + "ABCDEF+FandolSong-Regular             CID Type 0C (OT)  Identity-H       yes yes yes     12  0\nGHIJKL+CMUSerif-Roman                  Type 1C           WinAnsi          yes yes no      20  0\n[none]                               Type 3            Custom           yes no  no      31  0\n"


class ProjectFontTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="project-font-test-")
        self.project = Path(self.temp.name)
        self.pdf = self.project / "main with spaces.pdf"
        self.pdf.write_bytes(b"%PDF-1.7\nfixture: pdffonts is mocked\n")

    def tearDown(self):
        self.temp.cleanup()

    def completed(self, stdout=EMBEDDED, returncode=0, stderr=""):
        return subprocess.CompletedProcess(["pdffonts"], returncode, stdout, stderr)

    def test_embedded_types_with_spaces_and_type3_columns(self):
        fonts, findings = validator.parse_pdffonts(EMBEDDED)
        self.assertEqual(findings, [])
        self.assertEqual([font["type"] for font in fonts], ["CID Type 0C (OT)", "Type 1C", "Type 3"])
        self.assertTrue(all(font["embedded"] for font in fonts))
        self.assertFalse(fonts[-1]["unicode_mapping"])
        self.assertFalse(fonts[-1]["subset"])
        self.assertEqual(fonts[-1]["object_id"], 31)

    def test_unembedded_font_fails_without_confusing_unicode_column(self):
        text = HEADER + "Times-Roman                          Type 1            Standard         no  no  yes      8  0\n"
        with patch.object(validator.subprocess, "run", return_value=self.completed(stdout=text)):
            report = validator.validate_project_fonts(self.pdf)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["embedded_font_count"], 0)
        self.assertEqual(report["blocking_findings"][0]["category"], "font_not_embedded")

    def test_empty_and_malformed_tables_never_pass(self):
        for output in ("", HEADER, HEADER + "unexpected row\n", EMBEDDED + "unparsed extra font data\n"):
            with self.subTest(output=output), patch.object(validator.subprocess, "run", return_value=self.completed(stdout=output)):
                report = validator.validate_project_fonts(self.pdf)
                self.assertEqual(report["status"], "failed")

    def test_command_failure_unavailable_and_timeout_are_reported(self):
        cases = [
            (self.completed(returncode=1, stderr="Syntax Error: damaged PDF"), None, "pdffonts_failed"),
            (None, FileNotFoundError("pdffonts"), "pdffonts_unavailable"),
            (None, subprocess.TimeoutExpired("pdffonts", 30), "pdffonts_timeout"),
        ]
        for result, error, category in cases:
            with self.subTest(category=category), patch.object(validator.subprocess, "run", return_value=result, side_effect=error):
                report = validator.validate_project_fonts(self.pdf)
                self.assertEqual(report["status"], "failed")
                self.assertEqual(report["blocking_findings"][0]["category"], category)

    def test_no_log_is_explicit_and_does_not_claim_semantic_roles(self):
        with patch.object(validator.subprocess, "run", return_value=self.completed()) as run:
            report = validator.validate_project_fonts(self.pdf)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["embedded_font_count"], 3)
        self.assertFalse(report["log"]["checked"])
        self.assertIn("does not verify semantic font roles", " ".join(report["limitations"]))
        self.assertEqual(run.call_args.args[0], ["pdffonts", str(self.pdf.resolve())])

    def test_font_log_failure_overrides_embedded_pdf(self):
        log = self.project / "main.log"
        log.write_text("Missing character: There is no 字 (U+5B57) in font Example!\n", encoding="utf-8")
        with patch.object(validator.subprocess, "run", return_value=self.completed()):
            report = validator.validate_project_fonts(self.pdf, log)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(report["log"]["checked"])
        self.assertEqual(report["blocking_findings"][0]["category"], "missing_glyph")

    def test_normal_log_and_saved_json_agree_with_stdout(self):
        log = self.project / "main.log"
        log.write_text("LaTeX Font Info: Font shape `TU/CMUSerif/m/n' will be\n(Font) scaled to size 12pt.\nOutput written on main.pdf (3 pages).\n", encoding="utf-8")
        target = self.project / "qa" / "fonts.json"
        stdout = io.StringIO()
        with patch.object(validator.subprocess, "run", return_value=self.completed()), contextlib.redirect_stdout(stdout):
            code = validator.main([str(self.pdf), "--log", str(log), "--report", str(target)])
        self.assertEqual(code, 0)
        report = json.loads(stdout.getvalue())
        self.assertEqual(report, json.loads(target.read_text(encoding="utf-8")))
        self.assertTrue(report["log"]["checked"])

    def test_missing_explicit_files_fail_closed(self):
        with patch.object(validator.subprocess, "run") as run:
            report = validator.validate_project_fonts(self.project / "absent.pdf")
        run.assert_not_called()
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["blocking_findings"][0]["category"], "pdf_not_found")
        with patch.object(validator.subprocess, "run", return_value=self.completed()):
            report = validator.validate_project_fonts(self.pdf, self.project / "absent.log")
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["blocking_findings"][0]["category"], "log_not_found")


class BuildLogFontTests(unittest.TestCase):
    def test_wrapped_shape_and_default_substitution_are_blocking(self):
        log = "LaTeX Font Warning: Font shape `TU/Fandol/m/it'\n(Font)              undefined\n(Font)              using `TU/Fandol/m/n' instead.\nLaTeX Font Warning: Some font shapes were not available, defaults substituted.\n"
        findings = inspect_build_log.inspect_log(log)
        self.assertEqual({finding.get("category") for finding in findings}, {"font_substitution"})
        self.assertEqual(findings[0]["line"], 1)
        self.assertEqual(findings[0]["end_line"], 2)
        self.assertIn("undefined", findings[0]["text"])

    def test_missing_font_variants_and_size_substitution(self):
        logs = [
            'Package fontspec Error: The font "NotInstalled" cannot be found.\n',
            '! Font \\test=Absent at 12.0pt not loadable: Metric (TFM) file not found.\n',
            'Cannot find the requested font\n',
            "LaTeX Font Warning: Size substitutions with differences\n",
        ]
        for log in logs:
            with self.subTest(log=log):
                self.assertTrue(inspect_build_log.font_log_findings(log))

    def test_normal_font_information_is_not_an_error(self):
        log = "LaTeX Font Info: Checking defaults for TU/lmr/m/n on input line 12.\nLaTeX Font Info: Font shape `TU/CMUSerif/m/n' will be scaled to size 12pt.\n"
        self.assertEqual(inspect_build_log.inspect_log(log), [])

    def test_existing_nonfont_failures_still_block(self):
        findings = inspect_build_log.inspect_log("Overfull \\hbox (1.0pt too wide)\nLaTeX Warning: Reference `x' undefined.\n")
        self.assertEqual(len(findings), 2)


if __name__ == "__main__":
    unittest.main()
