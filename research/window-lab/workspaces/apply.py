"""apply.py: workspaces for Alex's home base (a6427, 17-20 Oct 2026), written into a world.

    python research/window-lab/workspaces/apply.py check            frontier-try in memory: every step; saves nothing
    python research/window-lab/workspaces/apply.py try              the same, saved into this worktree's frontier-try
    python research/window-lab/workspaces/apply.py door --as <who>  the live world through the keeper's door (8794)
    python research/window-lab/workspaces/apply.py undo try|door [saved/<time>]   takes it all out again

Alex, 17 Oct 10:11: 'I need you to be able to quickly reorganize the desk for me. So if I say let's start app dev right
now, the screen reorganizes around it.' What it writes, in order (each needs the one before it; nothing a person sees
changes until step 5, and the shipped workspaces only change his screen when someone says `workspace <name>`):
  1. home-tiling: four small words (exact passages, all must stand): chat=no on the layout hides the chat; with no
     panel out the chat (and what is open beside it) takes the room; a panel with thing=<id> stands its lens on that
     thing (Codex's Pin contract, c6468); and a line in its header saying so
  2. home-widgets: a layout's widgets=<titles> shows only those (rewritten whole; it must still be a5530's)
  3. Workspaces (role=workspaces actor=alex) and Workspaces going (role=workspaces-going: emptied by every use) in Home
     base; the six shipped workspaces in it, each a copy of Alex's layout as it stands, rearranged: default (his own,
     as it is now), app-dev, writing, review, quiet, play. His layout is marked name=default.
  4. the verb workspace (on=house), from workspace.verb with the two surfaces' ids filled in
  5. home-workspaces (the dock's icons) and one part placing it in home-dock, whichever dock is live (a5500's, or
     a6271's bar: re-run this step after a6271's apply, which rewrites home-dock whole)
door keeps every text it replaces in saved/<time>/ before it writes, and sends nothing unless every passage stands.
"""
import datetime
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "home-layout"))
import put  # noqa: E402  (q, Try, Live)

HOME, TILING, WIDGETS, DOCK = "f5204", "a5692", "a5707", "a5564"
LAYOUT = "kind:surface,prop:role=home-layout,prop:actor=alex"
VIEW = "prop:role=home-view,prop:actor=alex"
OUT = "kind:note,in:{ws},prop:role=home-panel,prop:shelf=no"

TILING_EDITS = [
    # (old, new, how many times old must stand)
    ('# or ⤡, gives it back. – shelves it (home-panels, in the dock). Nothing scrolls, nothing moves by itself.\n',
     '# or ⤡, gives it back. – shelves it (home-panels, in the dock). Nothing scrolls, nothing moves by itself.\n'
     '# a6427 (workspaces): chat=no on the layout hides the chat; with no panel out, the chat and what is open beside it\n'
     '# take the room; a panel with thing=<id> stands its lens= on that thing (a pinned document with its chosen lens).\n', 1),
    ('      let wide = 7 when ($lay.full or "") != ""\n',
     '      let wide = 1 when count(kind:note,in:$lay.item,prop:role=home-panel,prop:shelf=no) = 0\n'
     '      let wide = 7 when ($lay.full or "") != ""\n', 2),
    ('      only when ($lay.pin or "right") = "left"\n',
     '      only when ($lay.pin or "right") = "left" and ($lay.chat or "") != "no"\n', 1),
    ('      only when ($lay.pin or "right") != "left"\n',
     '      only when ($lay.pin or "right") != "left" and ($lay.chat or "") != "no"\n', 1),
    ('      only when ($lay.full or "") = ""\n      of kind:surface,in:$lay.item as col\n',
     '      only when ($lay.full or "") = "" and count(kind:note,in:$lay.item,prop:role=home-panel,prop:shelf=no) > 0\n'
     '      of kind:surface,in:$lay.item as col\n', 1),
    ('      only when ($lay.full or "") != ""\n      rail : column\n',
     '      only when ($lay.full or "") != "" and count(kind:note,in:$lay.item,prop:role=home-panel,prop:shelf=no) > 0\n'
     '      rail : column\n', 1),
    # a6549 (20 Oct) gave both panel bodies share 1 and scroll scroll: a long panel scrolls inside itself
    ('  body : column\n    share 1\n    scroll scroll\n    role panebody\n    lens $p.lens\nrailitem : column\n',
     '  body : column\n    share 1\n    scroll scroll\n    role panebody\n    only when ($p.thing or "") = ""\n    lens $p.lens\n'
     '  on : column\n    share 1\n    scroll scroll\n    role panebody\n    only when ($p.thing or "") != ""\n    of $p.thing as t\n    each stood\n'
     'stood : column\n  share 1\n  lens $p.lens\nrailitem : column\n', 1),
    ('  body : column\n    role panebody\n    share 1\n    scroll scroll\n    lens $p.lens',
     '  body : column\n    role panebody\n    share 1\n    scroll scroll\n    only when ($p.thing or "") = ""\n    lens $p.lens\n'
     '  on : column\n    role panebody\n    share 1\n    scroll scroll\n    only when ($p.thing or "") != ""\n'
     '    of $p.thing as t\n    each stood', 1),
]

DOCK_OLD = ("  left : column\n    share 1\n  dock : row\n",
            "  left : column\n    share 1\n    spaces : row\n      lens home-workspaces\n  dock : row\n")
DOCK_BAR = ("  sep1 : column\n",
            "  spaces : row\n    role tbgroup\n    lens home-workspaces\n  sep1 : column\n")

# the shipped workspaces: (name, title, glyph, about, columns [(span, [panel lens, ...])], props)
# a panel lens the layout lacks is made (app-preview: worker-a6431's phone preview, c6483)
NEW_PANELS = {"app-preview": ("Phone preview", "app-preview-small",
                              "The app you are building, live, at a phone's size.")}
SHIPPED = [
    ("app-dev", "app dev", "▯", "App dev: the phone preview in the middle, the workers on the left, the chat on the right.",
     [(1, ["home-house"]), (2, ["app-preview"])], {"pin": "right", "chat": "", "widgets": "", "view": "", "with": ""}),
    ("writing", "writing", "✎", "Writing: your documents open beside the chat, nothing else out.",
     [], {"pin": "right", "chat": "", "widgets": "", "view": "{writing}", "with": ""}),
    ("review", "review", "☷", "Review: what waits on you on the left and the board large beside it, the chat on the right.",
     [(1, ["waiting-on-me"]), (2, ["home-board"])], {"pin": "right", "chat": "", "widgets": "", "view": "", "with": ""}),
    ("quiet", "quiet", "◌", "Quiet: only the glance at the top and the chat.",
     [], {"pin": "right", "chat": "", "widgets": "home-glance", "view": "", "with": ""}),
    ("play", "play", "▶", "Play: everything put away; only the focus timer and the notices at the top.",
     [], {"pin": "right", "chat": "no", "widgets": "home-timer-bar,home-notices", "view": "", "with": ""}),
]


def answer(out):
    return next((l for l in out.splitlines() if l.strip() and not l.startswith(("!!", " "))), "")


def created(out):
    m = re.search(r"→ created (\w+)", out)
    if not m:
        raise SystemExit("apply: nothing was made:\n" + out[:800])
    return m.group(1)


def text_of(w, thing):
    out = w.do(f"read {thing} :3")
    a, b = out.find("\n---\n"), out.rfind("\n---")
    if a < 0 or b <= a:
        raise SystemExit(f"apply: cannot read {thing}: {out[:300]}")
    return out[a + 5:b].rstrip("\n")


def must(out, what):
    first = answer(out)
    if first.startswith(("ERR", "stopped")) or "\nERR" in out:
        raise SystemExit(f"apply: {what} refused:\n{out[:1200]}")
    return out


def tiling_text(have):
    new = have
    for old, rep, n in TILING_EDITS:
        if new.count(old) != n:
            raise SystemExit(f"apply: home-tiling passage stands {new.count(old)} times, not {n}: {old[:90]!r}")
        new = new.replace(old, rep)
    return new


def dock_text(have):
    if "lens home-workspaces" in have:
        return None
    old, rep = DOCK_BAR if have.startswith("# home-dock: the one bar") else DOCK_OLD
    if have.count(old) != 1:
        raise SystemExit(f"apply: home-dock passage stands {have.count(old)} times, not 1: {old[:80]!r}")
    return have.replace(old, rep)


def preflight(w):
    """Every passage this replaces stands, and nothing of this is there yet. -> the texts as read now."""
    texts = {k: text_of(w, k) for k in (TILING, WIDGETS, DOCK)}
    tiling_text(texts[TILING])
    dock_text(texts[DOCK])
    if not texts[WIDGETS].startswith("# home-widgets: every widget of the home base's top bar"):
        raise SystemExit("apply: home-widgets is not a5530's: read it before going on")
    if "a6427" in texts[WIDGETS] or "a6427" in texts[TILING]:
        raise SystemExit("apply: workspaces are already in (a6427 in the lenses)")
    if "nothing matches" not in w.do("find kind:surface,prop:role=workspaces,prop:actor=alex"):
        raise SystemExit("apply: Workspaces are already there")
    if "1 thing(s)" not in w.do(f"find {LAYOUT}"):
        raise SystemExit("apply: Alex has not exactly one home layout here")
    return texts


def rewrite(w, thing, text, what):
    w.do(f"read {thing} :3")
    print(what + ": " + answer(must(w.do(f"do rewrite {thing} text={put.q(text)}"), what)))


def lens(w, name, text):
    found = w.do(f"find title:{name},tag:lens,in:{HOME}")
    hit = [l.split()[0] for l in found.splitlines() if f'"{name}"' in l and l.strip().startswith("a")]
    if hit:
        rewrite(w, hit[0], text, name)
        return
    w.do(f"look {HOME}")
    print(name + ": " + answer(must(w.do(f"do create {HOME} kind=note title={name} tags=lens style=home-style text={put.q(text)}"), name)))


def build_workspace(w, ws_home, base, name, title, glyph, about, cols, props, ids, keep=False):
    """A copy of `base` (Alex's layout) in Workspaces, rearranged (unless keep): every panel put away, then the
    columns made, each holding its panels out. -> the workspace's id"""
    ws = created(must(w.do(f"do copy {base} into={ws_home} title={put.q(title)}"), f"copy for {name}"))
    w.do(f"look {ws} :3")
    if not keep and "nothing matches" not in w.do(f"find {OUT.format(ws=ws)}"):
        must(w.do(f"do prop {OUT.format(ws=ws)} shelf=yes"), f"{name}: put panels away")
    for span, lenses in cols:
        col = created(must(w.do(f"do create {ws} kind=surface title=column layout=column"), f"{name}: a column"))
        if span != 1:
            must(w.do(f"do prop {col} span={span}"), f"{name}: span")
        for ln in lenses:
            sel = f"kind:note,in:{ws},prop:role=home-panel,prop:lens={ln}"
            if "nothing matches" in w.do(f"find {sel}"):
                ptitle, lesser, pabout = NEW_PANELS[ln]
                must(w.do(f"do create {col} kind=note title={put.q(ptitle)} role=home-panel actor=alex lens={ln} "
                          f"lesser={lesser} shelf=no about={put.q(pabout)}"), f"{name}: panel {ln}")
            else:
                must(w.do(f"do move {sel} into={col}"), f"{name}: move {ln}")
                must(w.do(f"do prop {sel} shelf=no"), f"{name}: {ln} out")
    vals = {k: v.format(**ids) for k, v in props.items()}
    kv = " ".join(f"{k}={put.q(v)}" for k, v in vals.items())
    # a rearranged workspace fills nothing; 'default' (keep) keeps his full= as copy remapped it to its own panel
    full = "" if keep else ' full=""'
    must(w.do(f"do prop {ws} role=workspace actor=alex name={name} glyph={glyph}{full} about={put.q(about)} {kv}"),
         f"{name}: its props")
    print(f"workspace {name}: {ws}")
    return ws


def run(w, keep=None):
    texts = preflight(w)
    if keep:
        keep.mkdir(parents=True, exist_ok=True)
        for k, t in texts.items():
            (keep / f"{k}.txt").write_text(t + "\n", encoding="utf-8")
    # 1, 2: the lenses
    rewrite(w, TILING, tiling_text(texts[TILING]), "home-tiling")
    rewrite(w, WIDGETS, (HERE / "home-widgets.lens").read_text(encoding="utf-8").rstrip("\n"), "home-widgets")
    # 3: Workspaces, its going-box, and the shipped workspaces
    w.do(f"look {HOME}")
    ws_home = created(must(w.do(f"do create {HOME} kind=surface title=Workspaces layout=column"), "Workspaces"))
    must(w.do(f"do prop {ws_home} role=workspaces actor=alex about={put.q('Arrangements of the home base, applied in one act by the verb workspace (a6427).')}"), "Workspaces props")
    going = created(must(w.do(f"do create {HOME} kind=surface title={put.q('Workspaces going')} layout=column"), "Workspaces going"))
    must(w.do(f"do prop {going} role=workspaces-going actor=alex about={put.q('Emptied by every use of the verb workspace: the workspaces it replaces pass through here.')}"), "going props")
    base = w.do(f"find {LAYOUT}")
    lay = re.search(r"\b(f\d+) surface", base).group(1)
    w.do(f"look {lay} :3")
    seen = w.do(f"find {VIEW}")
    viewing = (re.search(r" viewing=(\S*)", seen) or [None, ""])[1]
    withl = (re.search(r" with=(\S*)", seen) or [None, ""])[1]
    if " name=default" not in base:
        must(w.do(f"do prop {lay} name=default"), "his layout is default")
    # default: his own layout as it stands (panels, columns, pin, full, viewer), the arrangement he knows
    build_workspace(w, ws_home, lay, "default", "default", "⌂", "Default: your home base as you had it when workspaces came.",
                    [], {"view": viewing, "with": withl}, {}, keep=True)
    dock = w.do("look f5565 :2")
    writing = (re.search(r'"Writing room"[^\n]*opens=(\w+)', dock) or [None, ""])[1]
    for name, title, glyph, about, cols, props in SHIPPED:
        build_workspace(w, ws_home, lay, name, title, glyph, about, cols, props, {"writing": writing})
    # 4: the verbs, the two that work first (a verb's words are bound when it is saved)
    for word in ("workspace-use", "workspace-keep", "workspace"):
        verb = (HERE / f"{word}.verb").read_text(encoding="utf-8").rstrip("\n").replace("{WS}", ws_home).replace("{R}", going)
        w.do(f"look {HOME}")
        print(word + ": " + answer(must(w.do(f"do create {HOME} kind=note title={word} tags=verb on=house text={put.q(verb)}"), word)))
    # 5: the phone preview's stand-ins, only where a6431's lenses are not there yet; then the dock
    for name in ("app-preview-small", "app-preview"):
        if f'"{name}"' not in w.do(f"find title:{name},tag:lens"):
            lens(w, name, (HERE / f"{name}.lens").read_text(encoding="utf-8").rstrip("\n"))
    lens(w, "home-workspaces", (HERE / "home-workspaces.lens").read_text(encoding="utf-8").rstrip("\n"))
    new = dock_text(text_of(w, DOCK))
    if new:
        rewrite(w, DOCK, new, "home-dock")
    return ws_home, going


def undo(w, keep=None):
    """Takes workspaces out again: the lenses as they were (a kept dir's texts when given, else the edits reversed and
    a5530's home-widgets), the verbs, the dock's icons, the stand-ins (only if still stand-ins) and both surfaces with
    all they hold. Alex's layout stays as it is when this runs (whatever workspace he is in)."""
    tiling = text_of(w, TILING)
    if keep:
        old_t = (keep / f"{TILING}.txt").read_text(encoding="utf-8").rstrip("\n")
        old_w = (keep / f"{WIDGETS}.txt").read_text(encoding="utf-8").rstrip("\n")
    else:
        old_t = tiling
        for old, rep, n in TILING_EDITS:
            old_t = old_t.replace(rep, old)
        old_w = (HERE / "home-widgets-a5530.lens").read_text(encoding="utf-8").rstrip("\n")
    if old_t != tiling:
        rewrite(w, TILING, old_t, "home-tiling back")
    if old_w != text_of(w, WIDGETS):
        rewrite(w, WIDGETS, old_w, "home-widgets back")
    dock = text_of(w, DOCK)
    back = re.sub(r"(?m)^( *)spaces : row\n(?:\1  role tbgroup\n)?\1  lens home-workspaces\n", "", dock + "\n").rstrip("\n")
    if back != dock:
        rewrite(w, DOCK, back, "home-dock back")
    for title, tag in (("workspace", "verb"), ("workspace-keep", "verb"), ("workspace-use", "verb"), ("home-workspaces", "lens"),
                       ("app-preview", "lens"), ("app-preview-small", "lens")):
        for line in w.do(f"find title:{title},tag:{tag},in:{HOME}").splitlines():
            m = re.match(rf'\s+(a\d+) note "{re.escape(title)}"', line)
            if m and (not title.startswith("app-preview") or "STAND-IN (a6427)" in text_of(w, m.group(1))):
                w.do(f"look {m.group(1)}")
                print(f"{title}: " + answer(must(w.do(f"do remove {m.group(1)}"), title)))
    for role in ("workspaces", "workspaces-going"):
        hit = re.search(r"\b(f\d+) surface", w.do(f"find kind:surface,prop:role={role},prop:actor=alex"))
        if not hit:
            continue
        f = hit.group(1)
        w.do(f"look {f} :3")
        for sel in (f"kind:note,in:{f}", f"kind:surface,in:{f},-prop:role=workspace", f"kind:surface,in:{f}"):
            if "nothing matches" not in w.do(f"find {sel}"):
                must(w.do(f"do remove {sel}"), f"empty {role}")
        print(f"{role}: " + answer(must(w.do(f"do remove {f}"), role)))


def main():
    args = sys.argv[1:]
    who = args[args.index("--as") + 1] if "--as" in args else "worker-a6427"
    mode = args[0]
    if mode in ("check", "try"):
        w = put.Try(who)
        run(w)
        if mode == "try":
            w.save()
            print("saved into frontier-try")
    elif mode == "undo":
        # undo try | undo door [saved/<time>]: take it out of frontier-try, or of the live world
        w = put.Try(who) if args[1] == "try" else put.Live(who)
        undo(w, pathlib.Path(args[2]) if len(args) > 2 and not args[2].startswith("--") else None)
        w.save()
    elif mode == "door":
        keep = HERE / "saved" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        run(put.Live(who), keep)
        print(f"kept the texts it replaced in {keep}")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
