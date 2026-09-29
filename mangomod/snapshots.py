"""Versioned snapshots retaining external paths, with legacy folder support."""
import json
import os
import tempfile
from pathlib import Path

from mangomod import config_parser, storage

MANIFEST = '.mangomod-manifest.json'


def create(directory: Path, sources: set[Path], texts: dict[str, str] | None = None):
    directory.parent.mkdir(parents=True, exist_ok=True)
    # A failed copy must not leave a partial folder that resembles a legacy
    # snapshot. Publish only after every member and the manifest is complete.
    with tempfile.TemporaryDirectory(prefix='.snapshot-', dir=directory.parent) as temporary:
        stage = Path(temporary) / 'snapshot'
        stage.mkdir()
        _write_snapshot(stage, sources, texts)
        os.replace(stage, directory)


def _write_snapshot(directory: Path, sources: set[Path], texts: dict[str, str] | None):
    main = config_parser.MANGO_CONFIG.resolve()
    texts = {str(Path(path).resolve()): text for path, text in (texts or {}).items()}
    records = []
    for index, source in enumerate(sorted({path.resolve() for path in sources})):
        data = texts.get(str(source)).encode('utf-8') if texts and str(source) in texts else storage.read_bytes(source)
        if data is None:
            continue
        try:
            relative = str(source.relative_to(main.parent))
        except ValueError:
            relative = None
        member = 'config.conf' if source == main else f'files/{index}.conf'
        dest = directory / member
        dest.parent.mkdir(exist_ok=True)
        dest.write_bytes(data)
        records.append({'member': member, 'original': str(source), 'relative': relative, 'main': source == main})
    (directory / MANIFEST).write_text(json.dumps({'version': 1, 'files': records}, indent=2), encoding='utf-8')


def contents(directory: Path) -> dict[Path, bytes]:
    main = config_parser.MANGO_CONFIG
    if not (directory / MANIFEST).exists():
        return {main.parent / item.relative_to(directory): item.read_bytes()
                for item in directory.rglob('*') if item.is_file() and not item.is_symlink()}
    manifest = json.loads((directory / MANIFEST).read_text(encoding='utf-8'))
    if manifest.get('version') != 1:
        raise ValueError('Unsupported snapshot version')
    result = {}
    for record in manifest['files']:
        member = (directory / record['member']).resolve()
        if not member.is_relative_to(directory.resolve()) or not member.is_file():
            raise ValueError('Invalid snapshot file')
        if record['main']:
            target = main
        elif record['relative'] is not None:
            target = main.parent / record['relative']
            if not target.resolve().is_relative_to(main.parent.resolve()):
                raise ValueError('Invalid snapshot destination')
        else:
            target = Path(record['original'])
            if not target.is_absolute():
                raise ValueError('Invalid external snapshot destination')
        if target.resolve() in {path.resolve() for path in result}:
            raise ValueError('Duplicate snapshot destination')
        result[target] = member.read_bytes()
    return result


def restore(directory: Path) -> bool:
    try:
        return restore_contents(contents(directory))
    except (OSError, ValueError, KeyError, TypeError):
        return False


def restore_contents(files: dict[Path, bytes]) -> bool:
    from mangomod import backup
    try:
        if not files:
            return False
        expected = {path: storage.read_bytes(path) for path in files}
        backup.backup_all_sources(set(files), limit=0)
        storage.write_files(files, expected)
        return True
    except (OSError, ValueError):
        return False
