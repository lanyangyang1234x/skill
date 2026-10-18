#!/usr/bin/env python3
"""Validate the project-local Fandol, CMU and traditional math font bundle."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('--main', help='Project-relative main TeX file')
    args = parser.parse_args()
    project = args.project.resolve()
    findings = []
    fonts = project / 'fonts'
    manifest_path = fonts / 'manifest.json'
    if fonts.is_symlink() or not fonts.resolve().is_relative_to(project):
        print('ERROR: fonts/ must be copied into the project, not linked to an external bundle')
        return 1
    if manifest_path.is_symlink():
        print('ERROR: Font manifest must be a regular project-local file')
        return 1
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        records = manifest['files']
        if not isinstance(records, dict) or not records:
            raise ValueError('empty or invalid files object')
    except (OSError, ValueError, KeyError) as exc:
        print(f'Font manifest error: {exc}')
        return 1
    for relative, expected in records.items():
        path = fonts / relative
        if path.is_symlink() or not path.resolve().is_relative_to(fonts.resolve()):
            findings.append(f'Font resource must be project-local: {relative}')
        elif not path.is_file():
            findings.append(f'Missing bundled font resource: {relative}')
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            findings.append(f'Font resource SHA-256 mismatch: {relative}')
    style = project / 'portable-math-fonts.sty'
    if style.is_symlink() or not style.resolve().is_relative_to(project):
        findings.append('Portable typography style must be copied into the project')
    elif not style.is_file():
        findings.append('Missing portable-math-fonts.sty')
    elif manifest.get('style_sha256') != hashlib.sha256(style.read_bytes()).hexdigest():
        findings.append('Portable typography style differs from the selected template manifest')
    if args.main:
        main_path = project / args.main
        if not main_path.is_file():
            print(f'ERROR: Main TeX file not found: {main_path}')
            return 1
        source = main_path.read_text(encoding='utf-8')
        source = re.sub(r'(?m)(?<!\\)%.*$', '', source)
        if not re.search(r'\\documentclass\[[^]]*\b12pt\b[^]]*\]', source):
            findings.append('The selected template requires an explicit 12pt document class')
        if not re.search(r'\\usepackage\{portable-math-fonts\}', source):
            findings.append('Main TeX must load portable-math-fonts')
        if re.search(r'\\(?:setmainfont|setsansfont|setmonofont|setCJKmainfont|setCJKsansfont|setCJKmonofont)\b', source):
            findings.append('Keep font declarations in portable-math-fonts.sty; main-file overrides are not allowed')
    for item in findings:
        print('ERROR: ' + item)
    if findings:
        return 1
    print(f'Portable font resources and hashes passed: {len(records)} resources. Verify actual font roles, sizes and line spacing in the compiled PDF.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
