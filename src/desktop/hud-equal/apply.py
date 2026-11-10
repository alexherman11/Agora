"""apply.py: equal footing for the home base (a5994's final pass, Alex 17 Oct, c6482), written into a world.

    python src/desktop/hud-equal/apply.py check [--as who]       read the live world: will every step stand?
    python src/desktop/hud-equal/apply.py try [--as who]         this worktree's frontier-try (no server)
    python src/desktop/hud-equal/apply.py door [--as who]        the live world through the keeper's door
    python src/desktop/hud-equal/apply.py restore <saved dir> [--as who]

What it does, in order (each step skips what is already done, so a run that stopped can run again):
 0. the search at the top (a6642's world half, src/desktop/home-search/apply.py), if the world lacks it;
 1. home-style: role tool.on (a lit tool: a pinned panel's ◆);
 2. verbs: unview (new: close the viewer, put its panel away, bring the chat out), drop-widget (new), view (one more
    step: bring the Viewer panel out), open-found (opens through view);
 3. home-viewer: no chat inside it any more (the chat is a panel); × closes through unview; with no viewer record or
    nothing open it says so;
 4. home-dock: Board and the other icons open through view, JEFF through unview; an icon can be dragged onto another
    to stand before it; home-widgets and home-widgets-end: a widget can be dragged onto another (drop-widget);
 5. every layout (role=home-layout) gains two panels if it lacks them: Viewer (lens home-viewer, a column of span 2)
    and Chat (lens jeff-chat, pin=yes), each in a new column at the end, so the chat is at the right as before;
 6. home-tiling, whole (it was rebuilt): only when the world's text is exactly home-tiling.before (the live text
    after a6642), so nobody's later edit is overwritten.
door first saves every text it changes, every id it makes and every prop it sets under saved/<stamp>/, and stops at
the first refusal; restore puts the texts back, removes what it made and the props it set.
"""
import json
import pathlib
import re
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "home-layout"))
sys.path.insert(0, str(HERE.parent / "home-search"))
import put  # noqa: E402  (Try, Live, q)
import apply as hs  # noqa: E402  (a6642's world half: text_of, found, plan, check, apply)

ROOM = "f5204"
NOTES = {"style": "a5206", "viewer": "a5486", "tiling": "a5692", "dock": "a5564", "widgets": "a5707", "view": "a6194",
         "drop": "a6340"}

PASSAGES = {
    "style": [("role tool : text down, faint, pad gap /2", "role tool : text down, faint, pad gap /2\nrole tool.on : text down, ink, pad gap /2")],
    "view": [("do prop prop:role=home-view,prop:actor=$me back=$(max(",
              "# a5994: with nothing open, max() below had nothing to read and the verb refused; the Conversation (a5080)\n"
              "# is what every viewer lens already reads as 'nothing open', so it stands there first (lines fill one by one)\n"
              "do prop prop:role=home-view,prop:actor=$me viewing=a5080 when count(prop:role=home-view,prop:actor=$me,prop:viewing) = 0\n"
              "do prop prop:role=home-view,prop:actor=$me back=$(max("),
             ("viewing=$1 find=\"\" with=\"\" when count(prop:role=home-view,prop:actor=$me,prop:viewing=$1) = 0",
              "viewing=$1 find=\"\" with=\"\" when count(prop:role=home-view,prop:actor=$me,prop:viewing=$1) = 0\n"
              "do prop prop:role=home-panel,prop:actor=$me,prop:lens=home-viewer shelf=no when count(prop:role=home-panel,prop:actor=$me,prop:lens=home-viewer,prop:shelf=yes) > 0")],
    "viewer": [
        ("# of JEFF's chat (a5949, Alex 16 Oct: 'I want it open on the left side of this chat'); × gives the chat its room back",
         "# of JEFF's chat (a5949, Alex 16 Oct: 'I want it open on the left side of this chat'); since a5994's equal footing it is\n"
         "# a panel of its own (lens home-viewer in a panel note) and the chat another (jeff-chat): × closes it (unview)"),
        ('''  lost : column
    share 1
    only when count(prop:role=home-view,prop:actor=$me) = 0
    chat : column
      share 1
      lens jeff-chat
''', '''  lost : text "No viewer of yours here: a note in Home base with role=home-view actor=<you>."
    role hint
    only when count(prop:role=home-view,prop:actor=$me) = 0
'''),
        ('''    chat : column
      share 2
      lens jeff-chat
''', '''    nothing : text "Nothing open. Find it at the top, press a pin, or a name anywhere."
      role hint
      only when open = "no"
'''),
        ('''      on click do prop $v viewing="" back="$v.viewing" with=""
  openwith : row''', '''      on click do unview $v
  openwith : row'''),
    ],
    "dock": [
        ('''app : column
  role appslot
''', '''app : column
  role appslot
  carry
  on drop app do move $carried before=$d.item
'''),
        ('''    on click do prop $v viewing=$d.opens back="$v.viewing" find="" with=""''', '''    on click do view $d.opens'''),
        ('''    on click do prop $v viewing="" back="$v.viewing" find=""''', '''    on click do unview $v'''),
    ],
    "drop": [("do remove $from when count(in:$from) = 0",
              "do remove $from when count(in:$from) = 0\n"
              "# a5994 (Alex, 20 Oct): a drop while a panel fills the room gives the room back, so what moved is seen\n"
              "do prop $5 full=\"\" when ($5.full or \"\") != \"\"")],
    "widgets": [('''  role widget.wide when $w.size = "m"
  lens $w.title''', '''  role widget.wide when $w.size = "m"
  carry
  on drop widget do drop-widget $carried $w
  lens $w.title''')],
}
# a6642's lens, same passage (found by title, as hs.found does)
WIDGETS_END = PASSAGES["widgets"]
OPEN_FOUND = ('do prop $2 viewing=$1 back="$2.viewing" find="" with="" when ($2.viewing or "") = "" or $2.viewing = "a5080"',
              'do view $1 when ($2.viewing or "") = "" or $2.viewing = "a5080"')
NEW = ["unview.verb", "drop-widget.verb"]
MINE = False      # try --mine: an earlier home-tiling.lens of this run may be replaced (on a try world only)


def plan(t, pairs):
    out = []
    for old, new in pairs:
        n = t.count(old)
        if new and t.count(new) == 1 and (old in new or n == 0):
            continue                                   # done already (a passage that keeps its old words inside)
        if n == 1:
            out.append((old, new))
        elif not (n == 0 and (new == "" or t.count(new) == 1)):
            raise ValueError(f"passage appears {n} times: {old.splitlines()[0][:90]!r}")
    return out


def targets(w):
    """{key: (id, pairs)} for every note this run edits by passages (the found lenses by title)."""
    out = {k: (nid, PASSAGES[k]) for k, nid in NOTES.items() if k in PASSAGES}
    for name, pairs in (("home-widgets-end", WIDGETS_END), ("open-found", [OPEN_FOUND])):
        hit = hs.found(w, name, "verb" if name == "open-found" else "lens")
        if hit:
            out[name] = (hit[0], pairs)
    return out


def layouts(w):
    out = w.do("find prop:role=home-layout")
    return re.findall(r"^\s+(f\d+) surface .*role=home-layout", out, re.M)     # never the echo of the words searched


MARK = "# EQUAL FOOTING (Alex, 17 Oct)"


def rebuilt(w):
    """home-tiling is already this run's (so a6642's passages in it were carried in and step 0 is done)."""
    return MARK in (hs.text_of(w.do(f"read {NOTES['tiling']} :3")) or "")


def check(w):
    ok = True
    if not rebuilt(w) and not hs.check(w):
        print("a6642's world half: NOT ready (see above)"); ok = False
    for key, (nid, pairs) in targets(w).items():
        t = hs.text_of(w.do(f"read {nid} :3"))
        try:
            print(f"{key} {nid}: {len(plan(t, pairs))} passage(s) to replace")
        except ValueError as e:
            print(f"{key} {nid}: {e}"); ok = False
    t = hs.text_of(w.do(f"read {NOTES['tiling']} :3"))
    if MARK not in t:
        for old, new in hs.plan("tiling", t):          # as it will read once step 0 has run
            t = t.replace(old, new)
    want = (HERE / "home-tiling.lens").read_text(encoding="utf-8").rstrip("\n")
    was = (HERE / "home-tiling.before").read_text(encoding="utf-8").rstrip("\n")
    print("tiling: " + ("as written already" if t == want else "the expected text: will be rewritten" if t == was
                        else "NOT the text expected (someone changed it since): compare with home-tiling.before"))
    if t not in (want, was) and not (MINE and MARK in t):
        ok = False
    for lay in layouts(w):
        inside = w.do(f"look {lay} :3")
        print(f"layout {lay}: " + ", ".join(f"{n} panel {'there' if f'lens={n}' in inside else 'to make'}" for n in ("home-viewer", "jeff-chat")))
    print("check: " + ("every step stands" if ok else "NOT ready"))
    return ok


def receipt(out):
    return " ".join(l.strip() for l in out.splitlines() if l.startswith(("ok ", "ERR", "~", "stopped")) or "created" in l)[:300]


def apply(w, saved=None):
    record = {"made": [], "props": []}

    def keep():
        if saved:
            (saved / "record.json").write_text(json.dumps(record, indent=1), encoding="utf-8")

    def step(line, what):
        out = w.do(line)
        print(f"{what}: {receipt(out)}")
        if hs.refused(out):
            keep()
            raise SystemExit(f"stopped at {what}: {out[:600]}")
        m = re.search(r"created ([af]\d+)", out)
        if m:
            record["made"].append(m.group(1)); keep()
        return out

    # 0. a6642 first: its passages are the ground these stand on
    if not rebuilt(w):
        if saved:
            (saved / "home-search").mkdir()
        hs.apply(w, saved / "home-search" if saved else None)
    # 1-4. passages, the verbs before the lenses that name them
    for f in NEW:
        p = HERE / f
        text = p.read_text(encoding="utf-8").rstrip("\n")
        hit = hs.found(w, p.stem, "verb")
        if hit:
            if hs.text_of(w.do(f"read {hit[0]} :3")) != text:
                step(f"do rewrite {hit[0]} text={put.q(text)}", f"{p.stem} rewrite {hit[0]}")
            continue
        w.do(f"look {ROOM}")
        step(f"do create {ROOM} kind=note title={p.stem} tags=verb on=f5189 text={put.q(text)}", f"{p.stem} create")
    order = ["style", "view", "drop", "open-found", "viewer", "dock", "widgets", "home-widgets-end"]
    tg = targets(w)
    for key in order:
        if key not in tg:
            continue
        nid, pairs = tg[key]
        t = hs.text_of(w.do(f"read {nid} :3"))
        if saved and plan(t, pairs):
            (saved / f"{key}-{nid}.txt").write_text(t, encoding="utf-8")
        for old, new in plan(t, pairs):
            w.do(f"read {nid} :3")
            step(f"do replace {nid} old={put.q(old)} new={put.q(new)}", f"{key} {nid} replace {old.splitlines()[0][:50]!r}")
    # 5. the two panels, in every layout that lacks them
    for lay in layouts(w):
        for lens, title, span, pin in (("home-viewer", "Viewer", 2, ""), ("jeff-chat", "Chat", 1, " pin=yes")):
            inside = w.do(f"look {lay} :3")
            if f"lens={lens}" in inside:
                continue
            actor = re.search(r"actor=(\S+)", inside.splitlines()[0]).group(1)
            col = step(f"do create {lay} kind=surface title=column layout=column", f"{lay} a column for {title}")
            cid = re.search(r"created (f\d+)", col).group(1)
            w.do(f"look {cid}")
            if span != 1:
                step(f"do prop {cid} span={span}", f"{cid} span {span}")
            step(f"do create {cid} kind=note title={title} role=home-panel actor={actor} lens={lens} shelf=no{pin}", f"{lay} panel {title}")
    # 6. home-tiling whole
    nid = NOTES["tiling"]
    t = hs.text_of(w.do(f"read {nid} :3"))
    want = (HERE / "home-tiling.lens").read_text(encoding="utf-8").rstrip("\n")
    was = (HERE / "home-tiling.before").read_text(encoding="utf-8").rstrip("\n")
    if t == want:
        print("tiling: as written already")
    elif t != was and not (MINE and MARK in t):
        keep()
        raise SystemExit("stopped before home-tiling: the world's text is not home-tiling.before (someone changed it): compare, carry their edit into home-tiling.lens and .before, run again")
    else:
        if saved:
            (saved / f"tiling-{nid}.txt").write_text(t, encoding="utf-8")
        step(f"do rewrite {nid} text={put.q(want)}", f"tiling {nid} rewrite")
    keep()
    return record


def restore(w, saved):
    """Texts back first (a lens that names a removed verb would stop compiling), then what was made goes."""
    for f in sorted(saved.glob("*-*.txt")):
        nid = f.stem.rsplit("-", 1)[1]
        w.do(f"read {nid} :3")
        text = f.read_text(encoding="utf-8")
        print(f"{f.stem}: {receipt(w.do(f'do rewrite {nid} text={put.q(text)}'))}")
    rec = json.loads((saved / "record.json").read_text(encoding="utf-8")) if (saved / "record.json").exists() else {"made": []}
    for nid in reversed(rec["made"]):
        w.do(f"look {nid}")
        print(f"remove {nid}: {receipt(w.do(f'do remove {nid}'))}")
    if (saved / "home-search").exists():
        hs.restore(w, saved / "home-search")


def main():
    args = sys.argv[1:]
    who = "worker-a5994"
    if "--as" in args:
        k = args.index("--as"); who = args[k + 1]; del args[k:k + 2]
    mode = args[0]
    global MINE
    MINE = mode == "try" and "--mine" in args
    w = put.Try(who) if mode == "try" else put.Live(who)
    if mode == "check":
        sys.exit(0 if check(w) else 1)
    if mode == "restore":
        restore(w, pathlib.Path(args[1])); w.save(); return
    if not check(w):
        raise SystemExit("not applied: a step would not stand; read the check above")
    saved = None
    if mode == "door":
        saved = HERE / "saved" / time.strftime("%Y%m%d-%H%M%S")
        saved.mkdir(parents=True)
    apply(w, saved)
    w.save()
    if saved:
        print(f"saved: {saved} (restore: python src/desktop/hud-equal/apply.py restore {saved.relative_to(HERE.parents[2]).as_posix()})")


if __name__ == "__main__":
    main()
