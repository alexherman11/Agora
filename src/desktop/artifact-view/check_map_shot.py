"""a8191 first proof, independently: can research/map-lab/ground/shots/map-800x600.png be tied to a passed guarded run?

Read-only: hashes the committed bytes, reads the report beside it and the git history of both, and asks
guarded_artifacts.prepare. Captures nothing, writes nothing, starts nothing.
    python src/desktop/artifact-view/check_map_shot.py
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHOT = "research/map-lab/ground/shots/map-800x600.png"
REPORT = "research/map-lab/ground/results/measure.json"
PRODUCER = "research/map-lab/ground/measure.py"
sys.path.insert(0, str(ROOT / "src" / "text-desk" / "notation"))


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def main():
    raw = (ROOT / SHOT).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    report_raw = (ROOT / REPORT).read_bytes()
    report = json.loads(report_raw)
    rows = []
    say = lambda k, v: rows.append((k, v)) or print(f"{k}: {v}")  # noqa: E731
    say("shot sha256", sha)
    say("shot bytes", len(raw))
    say("shot unchanged from HEAD", subprocess.run(["git", "diff", "--quiet", "HEAD", "--", SHOT], cwd=ROOT).returncode == 0)
    say("report sha256", hashlib.sha256(report_raw).hexdigest())
    say("shot last written in", git("log", "-1", "--format=%h %ad", "--date=iso", "--", SHOT))
    say("report last written in", git("log", "-1", "--format=%h %ad", "--date=iso", "--", REPORT))
    say("producer last changed in", git("log", "-1", "--format=%h %ad", "--date=iso", "--", PRODUCER))
    say("report run at", report.get("at"))
    say("report top-level keys", sorted(report))
    text = report_raw.decode("utf-8", "replace")
    say("report names the shot", Path(SHOT).name in text)
    say("report holds the shot's sha256", sha in text)
    say("report has per-shot outcomes", any(isinstance(s, dict) and ("shots" in s or "outcome" in s)
                                            for s in report.get("sizes", [])))
    g = report.get("guard")
    say("guard form", type(g).__name__ + (": verdict text only, no success code" if isinstance(g, str) else ""))
    say("guard text", (g or "")[:160])
    import guarded_artifacts
    try:
        guarded_artifacts.prepare({"nodes": {}, "subjects": {}}, artifact=SHOT, sha256=sha, recipient="rowan",
                                  target="a1", prompt="p")
        say("selector", "ACCEPTED (unexpected)")
    except guarded_artifacts.Refusal as e:
        say("selector", f"refused: {e}")
    tied = dict(rows)["report holds the shot's sha256"] and not isinstance(g, str)
    print("VERDICT:", "provenance established" if tied else
          "REFUSE: the report neither names nor hashes this shot and keeps no Guard success code; "
          "the selector cannot tie these bytes to a passed guarded run")


if __name__ == "__main__":
    main()
