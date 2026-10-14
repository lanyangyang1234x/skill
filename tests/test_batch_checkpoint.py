#!/usr/bin/env python3
"""Behavioral regressions for the batch checkpoint command-line protocol."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts/batch_checkpoint.py"
FIELDS = ["batch_id", "source_start", "source_end", "source_id", "phase", "owner", "target_files", "status", "attempt", "output_sha256", "updated_at_utc", "notes"]


class BatchCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="batch-checkpoint-test-")
        self.project = Path(self.temp.name)
        self.ledger = self.project / "batches.tsv"
        for name in ("a.tex", "b.tex", "c.tex"):
            (self.project / name).write_text(f"original {name}\n", encoding="utf-8")
        self.run_cmd("--init")

    def tearDown(self):
        self.temp.cleanup()

    def run_cmd(self, *args, ok=True, contains=None):
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.ledger), "--project-dir", str(self.project), *args], text=True, capture_output=True)
        output = result.stdout + result.stderr
        self.assertNotIn("Traceback", output)
        if ok:
            self.assertEqual(result.returncode, 0, output)
        else:
            self.assertNotEqual(result.returncode, 0, output)
        if contains:
            self.assertIn(contains, output)
        return result

    def claim(self, batch, files=("a.tex",), phase="translation", start=1, end=None, source="book", extra=(), ok=True, contains=None):
        args = ["--claim", "--batch-id", batch, "--source-start", str(start), "--source-end", str(end or start), "--source-id", source, "--phase", phase]
        for name in files:
            args += ["--file", name]
        return self.run_cmd(*args, *extra, ok=ok, contains=contains)

    def complete(self, batch, status="drafted", notes="checkpoint evidence"):
        return self.run_cmd("--complete", "--batch-id", batch, "--status", status, "--notes", notes)

    def rows(self):
        with self.ledger.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle, delimiter="\t"))

    def write_rows(self, rows):
        with self.ledger.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    def manual_row(self, batch, files="a.tex", phase="translation", start="1", end="1", status="in_progress", hashes=""):
        return dict(zip(FIELDS, [batch, start, end, "book", phase, "tester", files, status, "1", hashes, "2026-10-10T00:00:00+00:00", "fixture evidence"]))

    def legacy_digest(self, files):
        digest = hashlib.sha256()
        for name in sorted(files):
            digest.update(name.encode("utf-8") + b"\0" + (self.project / name).read_bytes())
        return digest.hexdigest()

    def assert_rejected_without_mutation(self, *args, contains=None):
        before = self.ledger.read_bytes()
        result = self.run_cmd(*args, ok=False, contains=contains)
        self.assertEqual(self.ledger.read_bytes(), before)
        return result

    def test_normal_disjoint_claims_and_promotion_release(self):
        self.claim("draft", ("a.tex",))
        self.claim("ready", ("b.tex",), start=2)
        self.complete("draft")
        self.complete("ready", "verified")
        self.run_cmd("--check", "--require-complete")
        self.run_cmd("--check", "--require-verified", ok=False, contains="draft: release requires verified")
        self.run_cmd("--promote", "--batch-id", "draft", "--notes", "source and language checks: audit.md pages 1-2")
        self.run_cmd("--check", "--require-complete", "--require-verified")
        rows = self.rows()
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[-1]["attempt"], "1")
        self.assertEqual(rows[-1]["output_sha256"], rows[2]["output_sha256"])
        self.assertEqual(set(json.loads(rows[2]["output_sha256"])), {"a.tex"})

    def test_numeric_error_in_active_row_never_throws_valueerror(self):
        self.write_rows([self.manual_row("broken", start="oops"), self.manual_row("other", files="b.tex")])
        self.run_cmd("--check", ok=False, contains="invalid numeric checkpoint field")
        self.assert_rejected_without_mutation("--complete", "--batch-id", "broken", "--status", "drafted", contains="Invalid batch checkpoint ledger")

    def test_malformed_rows_and_hash_encodings_are_rejected(self):
        bad_values = ["", "nohash", "{}", '{"a.tex":"bad"}', '{"b.tex":"' + "0" * 64 + '"}', '{"a.tex":"' + "0" * 64 + '","a.tex":"' + "0" * 64 + '"}']
        for value in bad_values:
            with self.subTest(hash=value):
                self.write_rows([self.manual_row("bad", status="drafted", hashes=value)])
                self.run_cmd("--check", ok=False)
        for field, value in [("target_files", ""), ("phase", "unknown"), ("attempt", "0"), ("source_end", "0"), ("batch_id", "")]:
            with self.subTest(field=field):
                row = self.manual_row("bad")
                row[field] = value
                self.write_rows([row])
                self.run_cmd("--check", ok=False)
        self.write_rows([self.manual_row("bad")])
        self.ledger.write_text(self.ledger.read_text() + "too\tfew\tcolumns\n")
        self.run_cmd("--check", ok=False, contains="Invalid batch checkpoint columns")
        self.ledger.write_text("wrong\theader\n")
        self.run_cmd("--check", ok=False, contains="Invalid batch checkpoint header")
        self.ledger.write_text('"unclosed header\n')
        self.run_cmd("--check", ok=False, contains="Invalid batch checkpoint TSV")
        self.write_rows([self.manual_row("nul", files="a\0.tex")])
        self.run_cmd("--check", ok=False, contains="Target file names cannot contain NUL")

    def test_claim_rejects_cross_phase_active_file_overlap_and_alias(self):
        self.claim("translate")
        before = self.ledger.read_bytes()
        self.claim("review", ("./a.tex",), phase="review", ok=False, contains="Target files overlap active")
        self.assertEqual(self.ledger.read_bytes(), before)
        self.claim("language", ("b.tex",), phase="language", start=2)
        self.run_cmd("--check")

    def test_checker_rejects_cross_phase_active_file_overlap(self):
        self.write_rows([self.manual_row("translate"), self.manual_row("review", files="./a.tex", phase="review")])
        self.run_cmd("--check", ok=False, contains="overlapping active target files")

    def test_checker_and_claim_reject_same_phase_active_range_overlap(self):
        self.claim("first")
        self.claim("second", ("b.tex",), ok=False, contains="Source range overlaps")
        self.write_rows([self.manual_row("first"), self.manual_row("second", files="b.tex")])
        self.run_cmd("--check", ok=False, contains="overlapping active source ranges")

    def test_later_active_claim_cannot_hide_tampered_completed_file(self):
        self.claim("original")
        self.complete("original", "verified")
        (self.project / "a.tex").write_text("tampered\n")
        self.claim("review", phase="review")
        self.run_cmd("--check", ok=False, contains="target file hash changed: a.tex")

    def test_own_active_append_cannot_hide_completed_history(self):
        self.claim("original")
        self.complete("original", "verified")
        rows = self.rows()
        rows.append({**rows[0]})
        self.write_rows(rows)
        (self.project / "a.tex").write_text("tampered\n")
        result = self.run_cmd("--check", ok=False, contains="invalid checkpoint transition")
        self.assertIn("target file hash changed: a.tex", result.stderr)

    def test_per_file_partial_supersession_keeps_other_file_hash(self):
        self.claim("original", ("a.tex", "b.tex"), end=2)
        self.complete("original")
        (self.project / "a.tex").write_text("reviewed a\n")
        self.claim("review-a", phase="review")
        self.complete("review-a", "verified")
        self.run_cmd("--check")
        self.run_cmd("--check", "--require-verified", ok=False, contains="original: release requires verified")
        (self.project / "b.tex").write_text("unrecorded change\n")
        self.run_cmd("--check", ok=False, contains="target file hash changed: b.tex")
        self.claim("review-b", ("b.tex",), phase="review", start=2)
        self.complete("review-b", "verified")
        self.run_cmd("--check", "--require-verified", contains="original: drafted output superseded by verified batches: review-a, review-b")

    def test_legacy_aggregate_partial_cover_is_not_skipped(self):
        self.write_rows([self.manual_row("legacy", files="a.tex;b.tex", end="2", status="drafted", hashes=self.legacy_digest(("a.tex", "b.tex")))])
        self.run_cmd("--check")
        (self.project / "a.tex").write_text("reviewed a\n")
        self.claim("review-a", phase="review")
        self.complete("review-a", "verified")
        (self.project / "b.tex").write_text("tampered b\n")
        self.run_cmd("--check", ok=False, contains="partially superseded legacy aggregate needs a new checkpoint")
        self.claim("review-b", ("b.tex",), phase="review", start=2)
        self.complete("review-b", "verified")
        self.run_cmd("--check", "--require-verified", contains="review-a, review-b")

    def test_legacy_aggregate_unchanged_promotion(self):
        digest = self.legacy_digest(("a.tex",))
        self.write_rows([self.manual_row("legacy", status="drafted", hashes=digest)])
        self.run_cmd("--promote", "--batch-id", "legacy", "--notes", "legacy source QA complete")
        self.run_cmd("--check", "--require-verified")
        self.assertEqual(self.rows()[-1]["output_sha256"], digest)

    def test_retry_requires_blocked_and_reason(self):
        self.claim("unknown", extra=("--retry", "--notes", "reason"), ok=False, contains="existing blocked")
        self.claim("batch")
        self.claim("batch", extra=("--retry", "--notes", "reason"), ok=False, contains="existing blocked")
        self.assert_rejected_without_mutation("--complete", "--batch-id", "batch", "--status", "blocked", contains="concrete reason")
        self.complete("batch", "blocked", "OCR missing")
        self.claim("batch", extra=("--retry",), ok=False, contains="concrete reason")
        self.claim("batch", ok=False, contains="use --retry")

    def test_retry_preserves_range_source_phase_and_files_and_history(self):
        self.claim("batch")
        self.complete("batch", "blocked", "OCR missing")
        before = self.ledger.read_bytes()
        variants = [{"start": 2}, {"end": 2}, {"source": "other"}, {"phase": "review"}, {"files": ("b.tex",)}]
        for variant in variants:
            with self.subTest(variant=variant):
                self.claim("batch", extra=("--retry", "--notes", "OCR repaired"), ok=False, contains="Retry must keep", **variant)
                self.assertEqual(self.ledger.read_bytes(), before)
        # The protocol supports reasoned retries after each blocked result, not an arbitrary once-only cap.
        for attempt in (2, 3, 4):
            self.claim("batch", extra=("--retry", "--notes", f"repaired blocker {attempt}"))
            self.assertEqual(self.rows()[-1]["attempt"], str(attempt))
            if attempt < 4:
                self.complete("batch", "blocked", "a new concrete blocker")
        self.complete("batch", "verified")
        self.run_cmd("--check", "--require-verified")
        self.assertEqual(len(self.rows()), 8)

    def test_promote_requires_draft_notes_and_unchanged_output(self):
        self.claim("batch")
        self.assert_rejected_without_mutation("--promote", "--batch-id", "batch", "--notes", "evidence", contains="no drafted")
        self.complete("batch")
        self.assert_rejected_without_mutation("--promote", "--batch-id", "batch", contains="verification evidence")
        before_file = (self.project / "a.tex").read_bytes()
        (self.project / "a.tex").write_text("revised\n")
        self.assert_rejected_without_mutation("--promote", "--batch-id", "batch", "--notes", "evidence", contains="Cannot promote changed output")
        (self.project / "a.tex").write_bytes(before_file)
        self.run_cmd("--promote", "--batch-id", "batch", "--notes", "review.md full source comparison")
        self.assert_rejected_without_mutation("--promote", "--batch-id", "batch", "--notes", "again", contains="no drafted")

    def test_release_flags_reject_each_unfinished_status(self):
        for status in ("pending", "in_progress", "blocked"):
            with self.subTest(status=status):
                self.write_rows([self.manual_row(status, status=status)])
                self.run_cmd("--check")
                self.run_cmd("--check", "--require-complete", ok=False, contains=f"status is {status}")
                self.run_cmd("--check", "--require-verified", ok=False, contains=f"status is {status}")

    def test_later_drafted_responsibility_cannot_reuse_prior_verified_release(self):
        self.claim("translation")
        self.complete("translation")
        self.claim("review", phase="review")
        self.complete("review", "verified")
        self.run_cmd("--check", "--require-verified")
        self.claim("layout", phase="layout")
        self.complete("layout")
        self.run_cmd("--check", "--require-complete")
        result = self.run_cmd("--check", "--require-verified", ok=False)
        self.assertIn("translation: release requires verified", result.stderr)
        self.assertIn("layout: release requires verified", result.stderr)

    def test_missing_file_after_active_claim_still_fails_old_hash(self):
        self.claim("translation")
        self.complete("translation", "verified")
        self.claim("review", phase="review")
        (self.project / "a.tex").unlink()
        self.run_cmd("--check", ok=False, contains="Target file not found: a.tex")

    def test_invalid_option_combination_and_unsafe_path_are_rejected(self):
        self.assert_rejected_without_mutation("--claim", "--require-verified", contains="require --check")
        self.assert_rejected_without_mutation("--check", "--retry", contains="requires --claim")
        self.claim("escape", ("../escape.tex",), ok=False, contains="escapes project")
        self.claim("absolute", (str(self.project / "a.tex"),), ok=False, contains="must be relative")

    def test_named_review_rounds_allow_later_authorized_revision(self):
        self.claim("translation")
        self.complete("translation")
        self.claim("first-review", phase="review:r1", extra=("--notes", "first full review after source comparison"))
        self.complete("first-review", "verified")
        self.claim("second-review", phase="review:r2", extra=("--notes", "authorized correction found after first review"))
        (self.project / "a.tex").write_text("corrected after first review\n")
        self.complete("second-review", "verified")
        self.run_cmd("--check", "--require-verified", contains="translation: drafted output superseded by verified batches: second-review")
        self.assertEqual(self.rows()[-1]["phase"], "review:r2")

    def test_active_named_rounds_keep_exclusive_file_ownership(self):
        self.claim("first-review", phase="review:r1", extra=("--notes", "first review"))
        before = self.ledger.read_bytes()
        self.claim("second-review", phase="review:r2", extra=("--notes", "new authorized finding"), ok=False, contains="Target files overlap active")
        self.assertEqual(self.ledger.read_bytes(), before)
        self.write_rows([self.manual_row("first-review", phase="review:r1"), self.manual_row("second-review", phase="review:r2")])
        self.run_cmd("--check", ok=False, contains="overlapping active target files")

    def test_named_review_rounds_require_reason_and_safe_slug(self):
        self.claim("no-reason", phase="review:r1", ok=False, contains="concrete re-review reason")
        for phase in ("review:", "review:../r2", "review:r 2", "review:第2轮", "review:r2:again", "review:.hidden", "translation:r2"):
            with self.subTest(phase=phase):
                self.claim("bad-round", phase=phase, extra=("--notes", "reason"), ok=False, contains="ASCII letter/digit first")
                self.write_rows([self.manual_row("bad-round", phase=phase)])
                self.run_cmd("--check", ok=False, contains="invalid phase")
                self.write_rows([])
        self.claim("valid-round", phase="review:R2_notes.final-3", extra=("--notes", "authorized final correction"))
        self.complete("valid-round", "verified")
        self.run_cmd("--check", "--require-verified")


if __name__ == "__main__":
    unittest.main(verbosity=2)
