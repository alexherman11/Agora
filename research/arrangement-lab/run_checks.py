"""Write scoped, reproducible evidence; no network or third-party dependencies."""

import argparse
import hashlib
import json
import platform
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="evidence/latest.json")
    parser.add_argument("--test", action="append", default=[])
    args = parser.parse_args()
    names = args.test or ["test_mechanics"]
    suite = unittest.defaultTestLoader.loadTestsFromNames(names)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "scope": "in-memory executable contract model, no production or browser integration",
        "tests_run": result.testsRun,
        "successful": result.wasSuccessful(),
        "failures": [{"test": t.id(), "trace": trace} for t, trace in result.failures],
        "errors": [{"test": t.id(), "trace": trace} for t, trace in result.errors],
        "source_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.glob("*.py"))
        },
    }
    destination = ROOT / args.output
    if not destination.resolve().is_relative_to(ROOT):
        raise ValueError("Evidence must remain in this lab")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    run()
