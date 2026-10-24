"""Retain isolated test output and the exact reviewed production/input hashes."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
LAB = ROOT / "research" / "text-desk-lab" / "notation"
results_path = HERE / "results.json"
results = json.loads(results_path.read_text(encoding="utf-8")) if results_path.exists() else {}
for name, args in (
    ("journal-cache", ["test_journal_cache.py"]),
    ("atomic-world", ["test_atomic_world.py"]),
    ("store-quick", ["test_store.py", "--quick"]),
    ("log-world", ["test_log_world.py"]),
):
    if sys.argv[1:] and name not in sys.argv[1:]:
        continue
    result = subprocess.run([sys.executable, str(LAB / args[0]), *args[1:]],
                            cwd=ROOT, capture_output=True, timeout=120)
    (HERE / f"{name}.stdout.txt").write_bytes(result.stdout)
    (HERE / f"{name}.stderr.txt").write_bytes(result.stderr)
    results[name] = {"argv": args, "exit_code": result.returncode}
    print(name, "exit", result.returncode, flush=True)
    print((result.stdout + result.stderr).decode("utf-8", errors="replace")[-3000:], flush=True)
paths = [LAB / "store.py", LAB / "test_journal_cache.py"]
results["sha256"] = {str(p.relative_to(ROOT)).replace("\\", "/"):
                     hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
(HERE / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
sys.exit(any(r["exit_code"] for k, r in results.items() if k != "sha256"))
