"""Card-owned review suites: data selects a runner, never a shell command.

`test_suites` on a card is a JSON list of {name, runner, paths, timeout,
desktop}. The House reads it again before reusing a review or publishing it.
Paths are relative to the reviewed worktree. Desktop scripts must own a
guarded hidden desktop; the House additionally checks the gaming gate.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath


def plan(card, tree, defaults):
    tree = Path(tree).resolve()
    suites = [dict(name=f'House baseline {i + 1}', runner='pytest', paths=list(paths),
                   timeout=600, desktop=False) for i, paths in enumerate(defaults)]
    raw = card.get('test_suites', [])
    if raw == '':
        raw = []
    try:
        extra = json.loads(raw) if isinstance(raw, str) else raw
    except ValueError as exc:
        raise ValueError('test_suites must be a JSON list') from exc
    if not isinstance(extra, list):
        raise ValueError('test_suites must be a JSON list')
    names = {s['name'] for s in suites}
    for spec in extra:
        if not isinstance(spec, dict) or set(spec) - {'name', 'runner', 'paths', 'timeout', 'desktop'}:
            raise ValueError('suite fields: name, runner, paths, timeout, desktop')
        name, runner, paths = spec.get('name'), spec.get('runner'), spec.get('paths')
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError('suite names must be nonempty and unique')
        if runner not in ('pytest', 'python', 'node'):
            raise ValueError(f'{name}: runner must be pytest, python or node')
        if not isinstance(paths, list) or not paths or (runner != 'pytest' and len(paths) != 1):
            raise ValueError(f'{name}: paths must name tests, or one script')
        for value in paths:
            if not isinstance(value, str):
                raise ValueError(f'{name}: invalid path')
            path = PurePosixPath(value)
            if (not value or '\\' in value or ':' in value or path.is_absolute()
                    or any(p in ('..', '.') or p.startswith('-') for p in value.split('/'))):
                raise ValueError(f'{name}: use worktree-relative paths without options or traversal')
            resolved = (tree / value).resolve()
            if not resolved.is_relative_to(tree) or not resolved.exists():
                raise ValueError(f'{name}: missing or outside worktree: {value}')
            if runner != 'pytest' and not resolved.is_file():
                raise ValueError(f'{name}: script must be a file')
        timeout, desktop = spec.get('timeout', 600), spec.get('desktop', False)
        if type(timeout) is not int or timeout <= 0 or type(desktop) is not bool:
            raise ValueError(f'{name}: timeout must be positive seconds; desktop must be boolean')
        suites.append(dict(name=name, runner=runner, paths=paths, timeout=timeout, desktop=desktop))
        names.add(name)
    return suites


def fingerprint(suites):
    return hashlib.sha256(json.dumps(suites, sort_keys=True).encode()).hexdigest()


def command(suite, python):
    prefix = {'pytest': [str(python), '-B', '-m', 'pytest', '-q'],
              'python': [str(python), '-B'], 'node': ['node']}
    return prefix[suite['runner']] + suite['paths']


def summary(checks):
    return '\n'.join(f"{c['name']}: {c['status']} ({c['evidence']})" for c in checks
                     if 'name' in c)
