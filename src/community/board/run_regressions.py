"""Run existing scratch proofs; relocate outputs away from other builders' folders.

No proof source is edited. EvidencePath only redirects an `evidence` child of
the three proof directories. All source reads and scratch kernel paths retain
their original meaning. Each proof runs in its own Python interpreter.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1] / 'agora'
OUT = HERE / 'regressions'
PROOFS = {
    'council': ('proof/council_night.py', 'main'),
    'hunt': ('proof/hidden_hunt.py', 'main'),
    'kits': ('proof/kits.py', 'main'),
    'agent': ('proof/byo_agent.py', 'main'),
    'web': ('proof/web_host.py', 'run'),
    'model': ('proof/local_model.py', 'run'),
    'summarize': ('modules/summarize/proof.py', None),
    'taskboard': ('apps/taskboard/proof.py', 'run'),
    'taskboard-v2': ('apps/taskboard/proof_v2.py', 'run'),
    'widgets': ('widgets/proof.py', 'main'),
    'pixel-guy': ('widgets/pixel_guy_proof.py', 'main'),
    'painter-contract': ('painter/contract_proof.py', 'main'),
    'painter-purpose': ('painter/purpose_proof.py', 'run'),
    'painter-isolation': ('painter/isolation_proof.py', 'run'),
    'painter': ('painter/proof.py', 'run'),
}


def worker(name, minutes):
    sys.dont_write_bytecode = True
    target, entry = PROOFS[name]
    path = LAB / target
    destination = OUT / name
    destination.mkdir(parents=True, exist_ok=True)
    sys.path[:0] = [str(path.parent), str(LAB), str(LAB / 'tests')]

    class EvidencePath(type(Path())):
        def __truediv__(self, value):
            result = super().__truediv__(value)
            for root in (LAB / 'painter', LAB / 'widgets', LAB / 'proof'):
                evidence_root = root / 'evidence'
                if result.is_relative_to(evidence_root):
                    return destination / result.relative_to(evidence_root)
            return result

    spec = importlib.util.spec_from_file_location('scratch_regression', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.Path = EvidencePath
    if hasattr(module, 'HERE'):
        module.HERE = EvidencePath(module.HERE)
    if hasattr(module, 'LAB') and name == 'model':
        module.LAB = EvidencePath(LAB)
    if hasattr(module, 'EVIDENCE'):
        module.EVIDENCE = destination
    if target.startswith('apps/taskboard/'):
        module.HERE = destination
        (destination / 'evidence').mkdir(exist_ok=True)
        # proof.py intentionally re-exports proof_v2.run; its function has the
        # other module's globals. Redirect that evidence too, without edits.
        if entry and callable(getattr(module, entry, None)):
            getattr(module, entry).__globals__['HERE'] = destination
    if name in ('council', 'hunt', 'kits', 'agent'):
        return module.main(['--out', str(destination)])
    if name == 'web':
        module.run(str(destination))
        return 0
    if name == 'summarize':
        import unittest
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
        return 0 if result.wasSuccessful() else 1
    sys.argv = [str(path)]
    if name in ('taskboard', 'taskboard-v2'):
        sys.argv += ['--minutes', str(minutes)]
        return module.run(minutes) if 'minutes' in __import__('inspect').signature(module.run).parameters else module.run()
    result = getattr(module, entry)()
    return result if type(result) is int else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('names', nargs='*', default=list(PROOFS))
    ap.add_argument('--worker')
    ap.add_argument('--minutes', type=float, default=10)
    args = ap.parse_args()
    if args.worker:
        return worker(args.worker, args.minutes)
    OUT.mkdir(exist_ok=True)
    results = []
    for name in args.names:
        start = time.perf_counter()
        with (OUT / (name + '.txt')).open('w', encoding='utf-8') as log:
            p = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()), '--worker', name,
                                '--minutes', str(args.minutes)], stdout=log, stderr=subprocess.STDOUT,
                               env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'},
                               creationflags=0x08000000 if sys.platform == 'win32' else 0)
        result = dict(name=name, exit_code=p.returncode, seconds=round(time.perf_counter() - start, 2))
        results.append(result)
        print(json.dumps(result), flush=True)
        (OUT / ('results-' + '-'.join(args.names) + '.json')).write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    return int(any(r['exit_code'] for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
