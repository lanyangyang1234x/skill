#!/usr/bin/env python3
"""Create consistently named Chinese deliverables and a UTF-8-safe ZIP archive."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import zipfile
from pathlib import Path


AUX_SUFFIXES = {
    ".aux",
    ".log",
    ".out",
    ".toc",
    ".fls",
    ".fdb_latexmk",
    ".xdv",
    ".synctex.gz",
}
EXCLUDED_DIRS = {".git", "work", "__pycache__"}


def normalized_stem(value: str) -> str:
    stem = " ".join(value.split()).strip()
    if not stem or any(character in stem for character in "/\\\0"):
        raise SystemExit("Title stem must be nonempty and filesystem-safe")
    if any(ord(character) < 32 for character in stem):
        raise SystemExit("Title stem contains control characters")
    return stem


def is_auxiliary(path: Path) -> bool:
    name = path.name
    return any(name.endswith(suffix) for suffix in AUX_SUFFIXES)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def copy_if_different(source: Path, destination: Path) -> None:
    if source.resolve() != destination.resolve():
        shutil.copy2(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("main_tex")
    parser.add_argument("--title-stem", required=True)
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--audit-report", type=Path)
    parser.add_argument("--visual-qa", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--include-source-manifest", action="store_true")
    args = parser.parse_args()

    project = args.project_dir.expanduser().resolve()
    main_tex = (project / args.main_tex).resolve()
    stem = normalized_stem(args.title_stem)
    output_dir = (args.output_dir or project).expanduser().resolve()
    source_pdf = (args.pdf or main_tex.with_suffix(".pdf")).resolve()
    if not main_tex.is_file():
        raise SystemExit(f"Main TeX file not found: {main_tex}")
    if not source_pdf.is_file():
        raise SystemExit(f"Compiled PDF not found: {source_pdf}")
    output_dir.mkdir(parents=True, exist_ok=True)

    named_tex = output_dir / f"{stem}.tex"
    named_pdf = output_dir / f"{stem}.pdf"
    copy_if_different(main_tex, named_tex)
    copy_if_different(source_pdf, named_pdf)

    report_source = (args.audit_report or project / "AUDIT_REPORT.md").resolve()
    visual_source = (args.visual_qa or project / "visual-qa.md").resolve()
    named_report = output_dir / f"{stem}-审计报告.md"
    named_visual = output_dir / f"{stem}-版面检查.md"
    if report_source.is_file():
        copy_if_different(report_source, named_report)
    if visual_source.is_file():
        copy_if_different(visual_source, named_visual)

    archive = output_dir / f"{stem}.zip"
    temporary = output_dir / f".{stem}.zip.tmp"
    if temporary.exists():
        temporary.unlink()

    expected: dict[str, Path] = {}

    def add_member(handle: zipfile.ZipFile, source: Path, archive_name: str) -> None:
        if archive_name in expected:
            raise SystemExit(f"Duplicate archive member planned: {archive_name}")
        handle.write(source, archive_name)
        expected[archive_name] = source

    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as handle:
        for path in sorted(project.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(project)
            if any(part in EXCLUDED_DIRS for part in relative.parts):
                continue
            if output_dir != project and (path == output_dir or output_dir in path.parents):
                continue
            if (
                path == archive
                or path == temporary
                or path.suffix == ".zip"
                or path.name.endswith(".zip.tmp")
            ):
                continue
            if is_auxiliary(path) or path.name == ".DS_Store":
                continue
            if path == source_pdf and source_pdf != named_pdf:
                continue
            if path.name == "template.pdf":
                continue
            if path.name == "source-manifest.json" and not args.include_source_manifest:
                continue
            archive_name = f"{stem}/{relative.as_posix()}"
            add_member(handle, path, archive_name)

        for path in (named_tex, named_pdf, named_report, named_visual):
            if not path.is_file() or output_dir == project:
                continue
            archive_name = f"{stem}/{path.name}"
            add_member(handle, path, archive_name)

    with zipfile.ZipFile(temporary) as handle:
        damaged = handle.testzip()
        if damaged:
            raise SystemExit(f"Archive CRC check failed: {damaged}")
        names = handle.namelist()
        if any("�" in name for name in names):
            raise SystemExit("Archive contains replacement characters in filenames")
        for info in handle.infolist():
            if any(ord(character) > 127 for character in info.filename) and not info.flag_bits & 0x800:
                raise SystemExit(f"Archive member is missing the UTF-8 filename flag: {info.filename}")
        if len(names) != len(expected) or set(names) != set(expected):
            raise SystemExit("Archive member set differs from the planned release set")
        for name, source in expected.items():
            if sha256_bytes(handle.read(name)) != sha256_bytes(source.read_bytes()):
                raise SystemExit(f"Archive round-trip comparison failed: {name}")

    temporary.replace(archive)
    print(f"Release PDF: {named_pdf}")
    print(f"Release TeX: {named_tex}")
    if named_report.is_file():
        print(f"Audit report: {named_report}")
    if named_visual.is_file():
        print(f"Visual QA: {named_visual}")
    print(f"UTF-8 release archive verified: {archive} ({len(expected)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
