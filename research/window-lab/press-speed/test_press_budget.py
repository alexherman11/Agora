"""test_press_budget (a6153): a press on the home base stays inside its budget, or this fails and says which and why.

    python research/window-lab/press-speed/test_press_budget.py [<world>] [--as alex] [--budget 260] [--aim 230] [--rounds 3]

On a scratch copy of the world (default frontier-try, else frontier; never written) with a log, as the live world has,
and the house and host staged as the home base meets them (residents at work, six windows, the host's verbs), it
serves the copy with deskd's own request code in this process and presses as Alex's painter does: POST /api/do with
the press's line, then GET /api/scene?view=painter&text=0 (the build the painter asks for after it). The presses are
the person's own panels (role=home-panel actor=<who>): each one put away and brought back, with the board out.

It fails when
  - a press's server time (the act and the build after it, the median over --rounds) is over --budget ms (260). The
    whole press should paint in 300 ms (a6153): that is --aim (230) here, the rest being the trip to the page and its
    paint, ~40-70 ms measured. A press between the two is printed as over the aim, not failed: a6153 left them there;
  - a build after a press keeps less than 80% of the instances it could keep (a press changes one panel: the rest of
    the home base is the one built before; a6153 found 4 of 264 kept, the stores pushed out each build);
  - the scene sent with text=0 has a text (the painter's inspector is off: ~400 KB, ~25 ms);
  - a witnessed source written again with the same rows is rewritten (each rewrite is a new scene on every page).
Timing on a busy machine is noisy: the median of several rounds is judged, and the budget has room. A failure prints
every press's numbers so the cause can be read.
"""
import json
import os
import pickle
import shutil
import statistics
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

NOTATION = Path(__file__).resolve().parents[3] / "research" / "text-desk-lab" / "notation"
sys.path.insert(0, str(NOTATION))
sys.path.insert(0, str(NOTATION.parents[1] / "window-lab"))

import deskd       # noqa: E402
import lens_ir     # noqa: E402
import store       # noqa: E402
import witnessed   # noqa: E402

SESSION = "pressbudget"
WINDOWS = [("Visual Studio Code", "Code.exe"), ("Inbox - Mail", "olk.exe"), ("Music", "Spotify.exe"),
           ("Agora notation - Terminal", "WindowsTerminal.exe"), ("Docs - Edge", "msedge.exe"), ("Files", "explorer.exe")]


def main(argv):
    opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d      # noqa: E731
    pos = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or not argv[i - 1].startswith("--"))]
    world = pos[0] if pos else ("frontier-try" if (NOTATION / "sessions" / "frontier-try.pickle").exists() else "frontier")
    # the aim is 230 ms (a 300 ms press, less ~70 for the trip and the paint); a6153 left presses at ~190-250 ms, so the
    # line that fails is 260: over it a press has regressed (the 24-store bug was +100 ms), under 230 it meets the aim
    who, budget, rounds = opt("--as", "alex"), float(opt("--budget", "260")), int(opt("--rounds", "3"))
    aim = float(opt("--aim", "230"))
    failures = []
    tmp = Path(tempfile.mkdtemp(prefix="press-budget-"))
    house = NOTATION / "house-state" / SESSION
    try:
        shutil.copyfile(NOTATION / "sessions" / f"{world}.pickle", tmp / f"{SESSION}.pickle")
        deskd.SESSIONS, deskd.STATIC = tmp, NOTATION / "desk-shell"
        import reports
        reports.ROOT = tmp / "reports"
        store.genesis(pickle.loads((tmp / f"{SESSION}.pickle").read_bytes()), tmp / f"{SESSION}.pickle", why="test_press_budget")
        # the house and host as the home base meets them (hud_playtest's staging)
        import host_verbs
        house.mkdir(parents=True, exist_ok=True)
        witnessed.write(SESSION, "desktop", [{"name": str(1000000 + i), "title": t, "program": p, "front": "yes" if i == 0 else "no"}
                                             for i, (t, p) in enumerate(WINDOWS)], by="test")
        witnessed.write(SESSION, "host", host_verbs.rows(), by="hud")
        doing = {"f5189": ("jeff", "working"), "f571": ("sable", "working"), "f576": ("pike", "resting")}
        (house / "house.json").write_text(json.dumps({"pid": os.getpid(), "beat": time.time() + 3600, "world": SESSION, "workers": {},
                                                      "residents": {c: {"actor": a, "alive": True, "doing": d, "turns": 3, "last_turn": time.time()}
                                                                    for c, (a, d) in doing.items()}}), encoding="utf-8")
        # a witnessed source said again with the same rows is not rewritten
        before = witnessed.stamp(SESSION)
        again = witnessed.write(SESSION, "host", host_verbs.rows(), by="hud", changed_only=True)
        if again is not None or witnessed.stamp(SESSION) != before:
            failures.append("witnessed.write(changed_only=True) rewrote a source whose rows had not changed")

        srv = ThreadingHTTPServer(("127.0.0.1", 0), deskd.Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        deskd.HOLD[0], deskd.PORT[0] = True, srv.server_address[1]

        def call(path, body=None):
            t = time.perf_counter()
            req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None)
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read()
            return json.loads(raw), (time.perf_counter() - t) * 1000

        q = f"/api/scene?session={SESSION}&as={who}&lens=home-base&view=painter&text=0"
        sc, _ = call(q)
        if sc.get("refused"):
            print(f"FAIL the home base does not build here: {sc['refused'][:300]}")
            return 1
        if sc.get("text"):
            failures.append(f"a scene asked with text=0 came with {len(sc['text'])} characters of text")
        with deskd.Session(SESSION, who, read=True) as desk:
            w = desk.world
            panels = [(i, (w.subjects[n["subject"]].get("props") or {})) for i, n in w.nodes.items() if n["type"] == "appearance"
                      and (w.subjects[n["subject"]].get("props") or {}).get("role") == "home-panel"
                      and str((w.subjects[n["subject"]].get("props") or {}).get("actor", "")).lower() == who]
        if len(panels) < 2:
            print(f"FAIL {who} has {len(panels)} home panels in {world}: nothing to press")
            return 1
        at = [sc.get("events_total")]

        def press(line):
            a, ms1 = call("/api/do", {"session": SESSION, "as": who, "line": line, "observed": {"at": at[0]},
                                      "gesture": f"budget-{time.time()}"})
            said = a.get("error") or a.get("text") or ""
            k0, m0 = lens_ir._STATS["kept"], lens_ir._STATS["made"]
            r, ms2 = call(q)
            at[0] = r.get("events_total")
            return ms1, ms2, lens_ir._STATS["kept"] - k0, lens_ir._STATS["made"] - m0, said

        board = next((i for i, p in panels if p.get("lens") == "home-board"), None)
        if board is not None:            # the board out: the home base at its fullest (more than 24 placed lenses)
            press(f"look {board}; do prop {board} shelf=no")
        # warm: each panel once each way, so what follows is a press on a home base already built
        for i, p in panels:
            for v in ("yes", "no"):
                press(f"look {i}; do prop {i} shelf={v}")
        rows = {}
        for _ in range(rounds):
            for i, p in panels:
                for v in ("yes", "no"):
                    ms1, ms2, kept, made, said = press(f"look {i}; do prop {i} shelf={v}")
                    if "ERR" in said[:200]:
                        failures.append(f"the press on {i} ({p.get('lens')}) shelf={v} was refused: {said[:200]}")
                    rows.setdefault((i, p.get("lens"), v), []).append((ms1, ms2, kept, made))
        print(f"{world}, as {who}: each press's act + the build after it, median of {rounds} (budget {budget:.0f} ms)")
        for (i, lens, v), rs in rows.items():
            tot = statistics.median(a + b for a, b, _, _ in rs)
            act, build = statistics.median(a for a, *_ in rs), statistics.median(b for _, b, *_ in rs)
            kept, made = statistics.median(k for *_, k, _ in rs), statistics.median(m for *_, m in rs)
            share = kept / (kept + made) if kept + made else 1
            print(f"  {i} {lens} shelf={v}: {tot:.0f} ms (act {act:.0f}, build {build:.0f}), kept {kept:.0f} made {made:.0f}"
                  + ("" if tot <= aim else f"  (over the {aim:.0f} ms aim)"))
            if tot > budget:
                failures.append(f"{i} {lens} shelf={v}: {tot:.0f} ms, over the budget of {budget:.0f} ms (act {act:.0f}, build {build:.0f})")
            # putting a panel away makes nothing; bringing one back makes its own parts, which were dropped with it
            if v == "yes" and share < 0.8:
                failures.append(f"{i} {lens} shelf={v}: the build after it kept {kept:.0f} and made {made:.0f} "
                                f"({share:.0%} kept; a press changes one panel, the rest should be kept)")
        srv.shutdown()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(house, ignore_errors=True)
    for f in failures:
        print("FAIL " + f)
    print("all within budget" if not failures else f"{len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
