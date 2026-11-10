"""tabs_world.py (a7544): the staged tabs world half (a7439/a7441, patches.json) read against a world and applied to a
DISPOSABLE COPY only, through its door's public /api/do, refusing drift. Nothing here writes the live world: `drift`
only reads it (`read <id> :3`, `find`).

    python src/desktop/browsing/tabs/review/tabs_world.py drift|hashes [--port 8794] [--world frontier]

prints, for each staged note, whether the live text equals originals.json and whether every old passage stands there
exactly once (stage.prepare), and the SHA-256 of every payload this review stands on.
"""
import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
TABS = HERE.parent
ROOT = HERE.parents[4]
NOTATION = ROOT / "src" / "text-desk" / "notation"
sys.path.insert(0, str(TABS))
import stage  # noqa: E402

NOTES = ("a5486", "a6194", "a6782", "a6790")          # home-viewer, view, open-found, unview (unview is read, never changed)
PAYLOAD = [TABS / f for f in ("patches.json", "originals.json", "stage.py", "home-viewer.lens", "view.verb",
                              "open-found.verb", "HANDOFF.md", "search-exclusions.json")]
SOURCE = [NOTATION / f for f in ("tab_history.py", "viewer_tabs.py", "moo.py", "desk_moo.py", "desk_knife.py", "scene.py",
                                 "lens_ir.py", "desk-shell/viewer.js", "desk-shell/lens.js", "desk-shell/textedit.js")]


def sha(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode("utf-8")).hexdigest().upper()


def hashes():
    return {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p.read_bytes()) for p in PAYLOAD + SOURCE}


def door(base, session, who, line):
    body = json.dumps({"session": session, "as": who, "line": line, "whole": True}).encode()
    req = urllib.request.Request(f"{base}/api/do", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.loads(r.read())
    return (("ERR " + out["error"] + "\n") if out.get("error") else "") + (out.get("text") or "")


def body(said):
    ls = said.splitlines()
    i = ls.index("---")
    return "\n".join(ls[i + 1:ls.index("---", i + 1)])


def texts(do):
    return {n: body(do(f"read {n} :3")) for n in NOTES}


def viewer_line(do, who="alex"):
    out = do(f"find prop:role=home-view,prop:actor={who}")
    return [l.strip() for l in out.splitlines() if re.match(r"\s+a\d+ note ", l)]


def check(do):
    """-> (report lines, texts read, prepared replacements or None). Reads only."""
    have, orig = texts(do), json.loads((TABS / "originals.json").read_text(encoding="utf-8"))
    patches = json.loads((TABS / "patches.json").read_text(encoding="utf-8"))
    rep = []
    for n in NOTES:
        rep.append(f"{n}: {'equals originals.json' if have[n].rstrip() == orig[n].rstrip() else 'DIFFERS from originals.json'}"
                   f" · live text sha {sha(have[n])[:16]}")
        for k, h in enumerate(patches.get(n, [])):
            c = have[n].count(h["old"])
            rep.append(f"  hunk {k + 1}: old stands {c} time(s){'' if c == 1 else '  <- REFUSE'}")
    try:
        ready = stage.prepare({n: have[n] for n in patches}, patches)
        rep.append("stage.prepare: every hunk stands exactly once; replacements ready")
    except ValueError as e:
        ready = None
        rep.append(f"stage.prepare REFUSED: {e}")
    if ready:
        staged = {n: (TABS / f).read_text(encoding="utf-8").rstrip("\n") for n, f in stage.FILES.items()}
        for n in staged:
            same = ready[n].rstrip("\n") == staged[n]
            rep.append(f"{n}: prepared text {'equals' if same else 'DIFFERS from'} the staged file {stage.FILES[n]}")
    return rep, have, ready


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def apply_copy(do_as):
    """Apply the scoped hunks to a COPY through `do replace` (old -> new, one passage each), as alex for nothing but
    the init. do_as(who, line). -> (log, saved texts, viewer props line before)."""
    do = lambda line: do_as("worker-a7544", line)  # noqa: E731
    rep, have, ready = check(do)
    if ready is None:
        raise SystemExit("copy apply refused: drift\n" + "\n".join(rep))
    log = list(rep)
    before = viewer_line(do)
    patches = json.loads((TABS / "patches.json").read_text(encoding="utf-8"))
    for n, hs in patches.items():
        do(f"read {n} :3")
        for h in hs:
            said = do(f"do replace {n} old={q(h['old'])} new={q(h['new'])}")
            ok = not said.startswith("ERR") and "refused" not in said.split("\n")[0]
            log.append(f"replace {n}: {said.strip().splitlines()[-1][:160] if said.strip() else '(nothing said)'}")
            if not ok:
                raise SystemExit("copy apply refused at a hunk:\n" + said[:1500])
    now = texts(do)
    for n in patches:
        log.append(f"{n}: after apply {'equals' if now[n] == ready[n] else 'DIFFERS from'} the prepared text")
    vid = before[0].split()[0]
    do_as("alex", f"read {vid}")
    said = do_as("alex", f"do browse {vid} action=init")
    log.append("init as alex: " + said.strip().splitlines()[-1][:200])
    return log, have, before, vid


# c7704/e16026: JEFF's copy-review payload a7761, exactly, composed on the COPY (never live). (old, new, times)
# Search: a7693/search-exclusions.json exactly. Menu: role searchdrop before measure 40ch, by order after the of line.
# Routes: the 20 clauses of Study note a7754, as a7761 converts them (view; or browse open with lens=, then unshelve).
MENU = [("      menu : column\n        measure 40ch\n        scroll scroll\n        of prop:role=viewer-tab,prop:viewer=$v,prop:closed=no as t\n",
         "      menu : column\n        role searchdrop\n        measure 40ch\n        scroll scroll\n        of prop:role=viewer-tab,prop:viewer=$v,prop:closed=no as t\n        by order\n", 1)]
UNSHELF = ("do prop prop:role=home-panel,prop:actor=$me,prop:lens=home-viewer shelf=no when "
           "count(prop:role=home-panel,prop:actor=$me,prop:lens=home-viewer,prop:shelf=yes) > 0")
FEED = "do browse $v action=open target={x} lens=home-feed; " + UNSHELF
ROUTES = {
    "a5548": [('do read $hv; do prop $hv viewing=$c back="$hv.viewing" find=""', "do view $c", 8)],
    "a5715": [('do prop $hv viewing=$nt.about back="$hv.viewing" find=""; do remove $nt', "do view $nt.about; do remove $nt", 1),
              ('do prop $hv viewing=$s.item back="$hv.viewing" find=""', "do view $s.item", 1)],
    "a5439": [('on click when ($hv.find or "") != "" do prop $hv viewing=$w back="$hv.viewing" find=""', 'on click when ($hv.find or "") != "" do view $w', 1),
              ('on click when ($hv.find or "") = "" do prop $hv viewing=$w back="$hv.viewing"', 'on click when ($hv.find or "") = "" do view $w', 1)],
    "a5484": [('do prop $v viewing=$c back="$v.viewing"', "do view $c", 2)],
    "a5544": [('do prop $v viewing=$h.corner back="$v.viewing" find="" with=home-feed', FEED.format(x="$h.corner"), 1),
              ('do prop $v viewing=$c back="$v.viewing" find="" with=home-feed', FEED.format(x="$c"), 1)],
    "a6352": [('do prop $v viewing=$h.corner back="$v.viewing" find="" with=home-feed', FEED.format(x="$h.corner"), 1),
              ('do prop $v viewing=$r.corner back="$v.viewing" find="" with=home-feed', FEED.format(x="$r.corner"), 1)],
    "a6771": [('do read $v; do prop $v viewing=$u back="$v.viewing" with=plan-usage-reader find=""',
               "do browse $v action=open target=$u lens=plan-usage-reader; " + UNSHELF, 2)],
}


# c7956: JEFF's staged a7937 replaces the six lens-preserving clauses' invalid lens-line unshelve with a world verb,
# view-with-lens <item> <lens>, whose conditional unshelve stays inside the verb. Its body is read from a7937 itself.
HELPER_NOTE = "a7937"


def helper_body(live_do):
    """The verb's exact lines, as a7937 proposes them (from '# view-with-lens' to the guarded unshelve line)."""
    text = body(live_do(f"read {HELPER_NOTE} :3"))
    lines = text.splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith("# view-with-lens"))
    j = next(k for k in range(i, len(lines)) if lines[k].startswith("do prop prop:role=home-panel"))
    return "\n".join(lines[i:j + 1])


def helped_routes():
    """a7761's routes with the six lens-preserving clauses sent through view-with-lens (a7937)."""
    out = {}
    for n, hs in ROUTES.items():
        rows = []
        for old, new, times in hs:
            m = re.search(r"target=(\$[\w.]+) lens=([\w-]+)", new)
            rows.append((old, f"do view-with-lens {m.group(1)} {m.group(2)}" if m else new, times))
        out[n] = rows
    return out


def compose_jeff(do, helper=None):
    """Apply the three world fixes to the COPY after the staged hunks. Every passage is counted first (the exact times
    expected, or nothing is written); a lens with repeated identical clauses is rewritten whole, in the copy only.
    helper: a7937's verb body: made on the copy (Home base, beside view) and used by the six lens routes. -> log"""
    log = []
    search = json.loads((TABS / "search-exclusions.json").read_text(encoding="utf-8"))
    plan = {"a5486": MENU, **(helped_routes() if helper else ROUTES)}
    if helper:
        do("look f5204")
        said = do(f"do create f5204 kind=note title=view-with-lens tags=verb on=house text={q(helper)}")
        log.append("helper view-with-lens (a7937, copy only): " + (said.strip().splitlines() or [""])[0][:160])
        if "ERR" in said:
            raise SystemExit("compose refused at the helper verb:\n" + said[:800])
    have = {n: body(do(f"read {n} :3")) for n in [*search, *plan]}
    stage.prepare({n: have[n] for n in search}, search)          # all six search passages exactly once, before any write
    for n, hs in plan.items():
        for old, new, times in hs:
            c = have[n].count(old)
            if c != times:
                raise SystemExit(f"compose refused: {n} has {c} of {old[:70]!r}, want {times}")
    for n, hs in search.items():
        for h in hs:
            do(f"read {n} :3")
            said = do(f"do replace {n} old={q(h['old'])} new={q(h['new'])}")
            log.append(f"search {n}: {said.strip().splitlines()[-1][:120]}")
    for n, hs in plan.items():
        text = have[n]
        for old, new, times in hs:
            text = text.replace(old, new)
        do(f"read {n} :3")
        said = do(f"do rewrite {n} text={q(text)}")
        ok = not said.startswith("ERR") and "refused" not in said.split("\n")[0]
        log.append(f"{'menu' if n == 'a5486' else 'routes'} {n}: {said.strip().splitlines()[-1][:120]}")
        if not ok:
            raise SystemExit(f"compose refused at {n}:\n{said[:800]}")
        if body(do(f"read {n} :3")) != text:
            raise SystemExit(f"compose: {n} reads back differently")
    return log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["drift", "hashes"])
    ap.add_argument("--port", type=int, default=8794)
    ap.add_argument("--world", default="frontier")
    a = ap.parse_args()
    if a.mode == "hashes":
        print(json.dumps(hashes(), indent=1))
        return
    do = lambda line: door(f"http://127.0.0.1:{a.port}", a.world, "worker-a7544", line)  # noqa: E731
    at = do("history")
    m = re.search(r"\be(\d+)\b", at)
    rep, have, _ = check(do)
    print(f"world {a.world} (read-only; latest event seen e{m.group(1) if m else '?'})")
    print("\n".join(rep))
    print("viewer:", viewer_line(do))
    print(json.dumps({n: sha(t) for n, t in have.items()}, indent=1))


if __name__ == "__main__":
    main()
