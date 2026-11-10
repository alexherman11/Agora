"""a8191: which combined-review shots guarded_artifacts.prepare would accept (its report/Guard/row/hash checks, on a
stand-in desk naming one resident), and whether a Codex model takes images. Read-only.
    python src/desktop/artifact-view/candidates.py [codex-model ...]
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src" / "text-desk" / "notation"))
import guarded_artifacts as ga  # noqa: E402

DESK = {"nodes": {"f1": {"id": "f1", "type": "surface", "rev": 1,
                         "props": {"role": "resident", "actor": "pike", "provider": "claude", "model": "claude-opus-5-5"}},
                  "a2": {"id": "a2", "type": "appearance", "subject": "s2", "rev": 1}},
        "subjects": {"s2": {"id": "s2", "kind": "note", "title": "n", "text": "n", "rev": 1}}}


def main():
    for model in sys.argv[1:]:
        print(f"codex {model} takes images: {ga._codex_image_model(model)}")
    ok = 0
    for run in sorted(p for p in ga.DEMO_ROOT.iterdir() if p.is_dir() and ga.RUN.fullmatch(p.name)):
        try:
            report = json.loads((run / "report.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for row in report.get("rows", []):
            for shot in row.get("shots", []) if row.get("outcome") == "pass" else []:
                try:
                    sha = hashlib.sha256((run / shot).read_bytes()).hexdigest()
                    p = ga.prepare(DESK, artifact=f"{run.name}/{shot}", sha256=sha, recipient="pike", target="a2",
                                   prompt="p")["provenance"]
                    ok += 1
                    print(f"ACCEPTED {run.name}/{shot} sha256={sha} {p['dimensions']} journey={p['journey']}")
                except (ga.Refusal, OSError) as e:
                    print(f"refused  {run.name}/{shot}: {e}")
    print(f"{ok} accepted")


if __name__ == "__main__":
    main()
