"""Trials as things on the desk (round 11g).

A trial is a subject of kind `trial` whose props say task, variant and model. `launch` starts run.py for it in the
background: the first verb here whose effect leaves the world, so its event cannot be undone and its receipt says so.
`sync` reads finished reports and writes them back as the actor `harness`: props (status, pass, calls, seconds),
a comment with the model's reply, and a transcript doc linked to the trial. Rules can watch `on prop by=harness`.
Never blocks on a running trial; time passing is a command here too (sync, or a morning script that calls it).
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import moo
from world import Refusal

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"
PYTHON = Path(r"C:\Projects\Agora4\.venv\Scripts\python.exe")
CODEX = r"C:\Users\Alex\AppData\Local\OpenAI\Codex\bin\bffc5354119c8421\codex.exe"


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]


@moo.verb("launch", ["trial"], "Start this trial in the background (run.py). External effect: cannot be undone.",
          "", "do launch a12", level=2)
def v_launch(w, nid, a):
    s = w.subjects[w.nodes[nid]["subject"]]
    p = s.setdefault("props", {})
    task, variant, model = p.get("task"), p.get("variant", "lean"), p.get("model", "gpt-5.6-terra")
    if not task:
        raise Refusal("a trial needs task= (do prop <trial> task=home2 variant=lean model=gpt-5.6-sol)")
    if p.get("status") == "running":
        raise Refusal(f"{nid} is already running as {p.get('label')}; sync to see whether it finished")
    base = f"desk-{_slug(s['title'])}"
    n = 1
    while (RUNS / f"{base}-{n}").exists():
        n += 1
    label = f"{base}-{n}"
    env = dict(os.environ, AGORA_CODEX_BIN=os.environ.get("AGORA_CODEX_BIN", CODEX))
    cmd = [str(PYTHON), str(HERE / "run.py"), task, "--variant", variant, "--model", model, "--label", label]
    log = open(RUNS / f"{label}.launch.log", "w", encoding="utf-8")
    subprocess.Popen(cmd, cwd=str(HERE), env=env, stdout=log, stderr=subprocess.STDOUT,
                     creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    before = dict(s, props=dict(p))
    p.update(status="running", label=label, started=w.today or "")
    s["rev"] += 1
    for x in w.appearances_of(s["id"]):
        w._bump(x)
    ev = w._event("launch", nid, {"label": label, "task": task, "variant": variant, "model": model}, {"external": True})
    return {"ok": True, "event": ev["id"], "changed": [s["id"]] + w.appearances_of(s["id"]),
            "note": f"launched {label}: {task} on {model} ({variant}). External effect: undo cannot take this back. sync brings the result in."}


def sync(desk):
    """Bring finished trials in. Returns receipt lines."""
    w = desk.world
    out = []
    for s in list(w.subjects.values()):
        p = s.get("props") or {}
        if s["kind"] != "trial" or p.get("status") != "running":
            continue
        label = p.get("label")
        report = RUNS / label / "report.json"
        if not report.exists():
            out.append(f"  {s['id']} {label}: still running")
            continue
        rep = json.loads(report.read_text(encoding="utf-8"))
        a = rep.get("assessment") or {}
        apps = w.appearances_of(s["id"])
        host = apps[0] if apps else s["id"]
        checks = [k for k, v in a.items() if k != "pass" and k != "injection_fired" and not k.startswith("judgment")]   # gating only
        passed = sum(1 for k in checks if a[k])
        moo.REGISTRY["prop"].run(w, host, {"status": "done", "pass": "1" if a.get("pass") else "0",
                                           "score": f"{passed}/{len(checks)}", "calls": str(rep.get("calls")),
                                           "seconds": str(rep.get("elapsed_seconds")), "refusals": str(rep.get("refusals")),
                                           **({"failed": ",".join(k for k in checks if not a[k])} if not a.get("pass") else {}),
                                           "_by": "harness"})
        reply = (rep.get("reply") or "").strip()
        if reply:
            w.add_comment(s["id"], "harness", reply[:600], "harness")
        # transcript as a doc, one section per call, linked to the trial
        secs = [f"{label}: {rep.get('task')} on {rep.get('model')} ({rep.get('variant')}); {rep.get('calls')} calls, "
                f"{'pass' if a.get('pass') else 'fail'} {passed}/{len(checks)}"]
        for t in (json.loads(l) for l in (RUNS / label / "tools.jsonl").open(encoding="utf-8")):
            line = t["arguments"].get("line", json.dumps(t["arguments"]))
            body = t["result"].get("text") if "text" in t["result"] else "ERR " + str(t["result"].get("error"))
            body = "\n".join("    " + l for l in str(body).splitlines())   # indented: a ## inside a result is not a section
            secs.append(f"## call {t['index']}: {line[:80]}\n{body}")
        doc = w.add_subject("doc", f"{label} transcript", "\n".join(secs))
        parent = w.nodes[host]["parent"] if host in w.nodes else w.root
        aid = w.place(doc, parent, 8, 8, 300, 160)
        w._fair_share(aid)
        w.reflow(parent)
        w.add_link(s["id"], doc, "refers", actor="harness")
        fails = [k for k in checks if not a[k]]
        out.append(f"  {s['id']} {label}: {'pass' if a.get('pass') else 'FAIL ' + ','.join(fails)} · {rep.get('calls')} calls · "
                   f"{rep.get('elapsed_seconds')}s · transcript {aid}")
    return out or ["  nothing running"]
