#!/usr/bin/env python3
"""Check the pinned chinese-writing method library and unmodified source archive."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile


def safe_name(name: object) -> bool:
    if not isinstance(name, str):
        return False
    parts = PurePosixPath(name)
    return bool(name) and not parts.is_absolute() and '..' not in parts.parts and '\\' not in name and str(parts) == name


def check_bytes(name: str, data: bytes, record: object, errors: list[str]) -> None:
    if not isinstance(record, dict):
        errors.append(f'Invalid file record: {name}')
        return
    if hashlib.sha256(data).hexdigest() != record.get('sha256'):
        errors.append(f'Hash mismatch: {name}')
    if len(data) != record.get('bytes'):
        errors.append(f'Size mismatch: {name}')


def verify(skill_dir: Path) -> dict:
    vendor = skill_dir / 'vendor/chinese-writing'
    errors: list[str] = []
    try:
        lock = json.loads((skill_dir / 'vendor/chinese-writing.lock.json').read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        return {'status': 'failed', 'errors': [f'Cannot read lock: {exc}']}
    if not isinstance(lock, dict):
        return {'status': 'failed', 'errors': ['Lock must be an object']}
    commit = lock.get('commit', '')
    if not isinstance(commit, str) or not re.fullmatch(r'[0-9a-f]{40}', commit):
        errors.append('Invalid pinned commit')
    if lock.get('schema_version') != 2:
        errors.append('Expected method-library lock schema 2')
    files = lock.get('files')
    if not isinstance(files, dict) or not files:
        return {'status': 'failed', 'errors': errors + ['Lock has no runtime file map']}
    expected: set[str] = set()
    for name, record in files.items():
        if not safe_name(name):
            errors.append(f'Unsafe lock path: {name!r}')
            continue
        expected.add(name)
        path = vendor / name
        if path.is_symlink() or not path.resolve().is_relative_to(vendor.resolve()):
            errors.append(f'Symlink or escaping path: {name}')
        elif not path.is_file():
            errors.append(f'Missing file: {name}')
        else:
            check_bytes(name, path.read_bytes(), record, errors)
    actual = {path.relative_to(vendor).as_posix() for path in vendor.rglob('*')
              if path.is_file() and '__pycache__' not in path.parts and path.name != '.DS_Store'}
    errors.extend(f'Unexpected method file: {name}' for name in sorted(actual - expected))
    for required in ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'references/sentence-construction.md'):
        if required not in expected:
            errors.append(f'Required method file absent from lock: {required}')
    for path in vendor.rglob('*'):
        if path.name in {'SKILL.md', 'AGENTS.md'} or path.relative_to(vendor).as_posix() == 'agents/openai.yaml':
            errors.append(f'Standalone skill or agent guidance in method library: {path.relative_to(vendor)}')

    archive_record = lock.get('upstream_archive')
    archive_files = {}
    if not isinstance(archive_record, dict) or not safe_name(archive_record.get('path')):
        errors.append('Missing or unsafe source archive record')
    else:
        archive = skill_dir / archive_record['path']
        if archive.is_symlink() or not archive.resolve().is_relative_to(skill_dir.resolve()):
            errors.append('Source archive escapes skill directory')
        elif not archive.is_file():
            errors.append('Missing source archive')
        else:
            check_bytes(archive_record['path'], archive.read_bytes(), archive_record, errors)
            archive_files = archive_record.get('files')
            if not isinstance(archive_files, dict) or not archive_files:
                errors.append('Source archive has no file map')
                archive_files = {}
            else:
                try:
                    with zipfile.ZipFile(archive) as z:
                        names = z.namelist()
                        if len(names) != len(set(names)):
                            errors.append('Duplicate archive members')
                        for info in z.infolist():
                            if not safe_name(info.filename) or info.is_dir() or stat.S_ISLNK(info.external_attr >> 16):
                                errors.append(f'Unsafe archive member: {info.filename}')
                                continue
                            if info.filename not in archive_files:
                                errors.append(f'Unexpected archive member: {info.filename}')
                                continue
                            check_bytes(f'archive:{info.filename}', z.read(info), archive_files[info.filename], errors)
                        errors.extend(f'Missing archive member: {name}' for name in sorted(set(archive_files) - set(names)))
                except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
                    errors.append(f'Cannot verify source archive: {exc}')
                for required in ('SKILL.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md'):
                    if required not in archive_files:
                        errors.append(f'Original upstream file absent from archive: {required}')
                for name, record in files.items():
                    if archive_files.get(name) != record:
                        errors.append(f'Method file differs from upstream lock: {name}')
    return {'status': 'failed' if errors else 'passed', 'repository': lock.get('repository'),
            'version': lock.get('version'), 'commit': commit, 'runtime_files': len(files),
            'upstream_files': len(archive_files), 'errors': errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-dir', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = verify(args.skill_dir.expanduser().resolve())
    serialized = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialized, encoding='utf-8')
    print(serialized, end='')
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
