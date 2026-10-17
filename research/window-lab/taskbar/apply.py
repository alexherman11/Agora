"""apply.py: the one bar at the foot of the home base (a6271, 17 Oct 2026), written into a world.

    python research/window-lab/taskbar/apply.py check            a copy of frontier-try in memory: every step, then the
                                                                  bar, its icon lens and home-base built as alex; saves nothing
    python research/window-lab/taskbar/apply.py try               the same, saved into this worktree's frontier-try
    python research/window-lab/taskbar/apply.py door --as <who>   the live world through the keeper's door (127.0.0.1:8794)

Alex, 17 Oct: 'Lets not have two different bars at the bottom for different widgets vs native applications. For now i
want them in a more unified bar that is lower and more discreet like the windows bar. They should have good icons, no
text. If i hover them it should say what they are.' The steps, in order (each needs the one before it):
  1. home-style gets the bar's roles as ONE marked block (style-taskbar.desk), replaced whole on a re-run
  2. the surface Icons (role=icons) in Home base, and one note per icon (icons.desk); an icon already there is rewritten
  3. icon=, about=, lights= and a widget's name= on the dock's notes, the panels and the widgets (data.desk)
  4. lens home-icon (made, or rewritten)
  5. lens home-dock rewritten: the bar. Until this step nothing a person sees changes; it goes last.
door first reads everything it will change and keeps it in before-a6271/ (the texts, and each thing's props), and sends
nothing unless every thing data.desk names is there, home-dock still is the lens this was written against (the
a5500 dock, or this bar on a re-run), and home-tiling is lane 2's (full=), which the round-3 assembly puts live: this
goes after it, as one coordinated change (Alex's HUD sprint, a6049). check and try need the same: put lane 2's tiling
into frontier-try first (home-layout/put.py try ... home-tiling.lens, as its docstring says). The code it needs (the painter's `tip`, the style's `hover`) must be on main and
the home base's page reloaded (hud_probe.py says when it started), or the bar paints with no tips and no hover ground.
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "home-layout"))
import put  # noqa: E402  (q, Try, Live: the home layout's world writer)

HOME = "f5204"          # the Home base room
STYLE, DOCK, TILING = "a5206", "a5564", "a5692"
BEGIN, END = "# a6271 bar roles: begin", "# a6271 bar roles: end"


def said(out):
    return " ".join(l.strip() for l in out.splitlines() if l.startswith(("ok ", "ERR", "~", "stopped", "!!")) or "created" in l)[:400]


def text_of(w, thing):
    """A note's whole text, as `read <id> :3` prints it between its --- lines."""
    out = w.do(f"read {thing} :3")
    a, b = out.find("\n---\n"), out.rfind("\n---")
    if a < 0 or b <= a:
        raise SystemExit(f"apply: cannot read {thing}: {out[:300]}")
    return out[a + 5:b].rstrip("\n")


def block():
    lines = (HERE / "style-taskbar.desk").read_text(encoding="utf-8").splitlines()
    a, b = lines.index(next(l for l in lines if l.startswith(BEGIN))), lines.index(END)
    return "\n".join(lines[a:b + 1])


def step_style(w):
    have, new = text_of(w, STYLE), block()
    if BEGIN in have:
        old = have[have.index(BEGIN):have.index(END) + len(END)]
        if old == new:
            print("style: the block stands as written")
            return
        print("style: " + said(w.do(f"do replace {STYLE} old={put.q(old)} new={put.q(new)}")))
    else:
        print("style: " + said(w.do(f"do append {STYLE} line={put.q(new)}")))


def step_icons(w):
    found = w.do(f"find kind:surface,prop:role=icons,in:{HOME}")
    hit = re.findall(r"^\s*(f\d+) surface", found, re.M)
    if hit:
        icons = hit[0]
    else:
        w.do(f"look {HOME}")
        out = w.do(f"do create {HOME} kind=surface title=Icons layout=row")      # a surface takes no props in create
        m = re.search(r"created (f\d+)", out)
        if not m:
            raise SystemExit("apply: the Icons surface was not made: " + out[:400])
        icons = m.group(1)
        w.do(f"look {icons}")
        print("icons: " + said(w.do(f"do prop {icons} role=icons")))
    print(f"icons: the surface {icons}")
    w.do(f"look {icons}")
    for line in (HERE / "icons.desk").read_text(encoding="utf-8").splitlines():
        if not line.startswith("do create"):
            continue
        name = re.search(r" icon=(\S+)", line).group(1)
        svg = re.search(r' text="(.*)"$', line).group(1)
        there = re.findall(r"^\s*(a\d+) note", w.do(f"find kind:note,prop:role=icon,prop:icon={name}"), re.M)
        if there:
            if text_of(w, there[0]) == svg:
                continue
            out = w.do(f"do rewrite {there[0]} text={put.q(svg)}")
        else:
            out = w.do(line.replace("{icons}", icons))
        print(f"  {name}: {said(out)}")


def step_data(w):
    absent = False
    for line in (HERE / "data.desk").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        if line.startswith("look "):
            out = w.do(line)
            # a widget named by title may not be in this world (the round-3 assembly decides which are); an id must be
            absent = line.startswith('look "') and not answer(out).startswith(("a", "f", "s"))
            if absent:
                print(f"  {line[5:]}: not in this world, skipped")
            continue
        if absent:
            continue
        out = w.do(line)
        if "nothing to change" not in out:      # a re-run: already said
            print(f"  {line[:70]}: {said(out)}")


def step_lens(w, name):
    put.put_lens(w, HERE / f"{name}.lens")


def run_all(w):
    step_style(w)
    step_icons(w)
    step_data(w)
    step_lens(w, "home-icon")
    step_lens(w, "home-dock")


def things():
    return sorted(set(re.findall(r"^look (a\d+)$", (HERE / "data.desk").read_text(encoding="utf-8"), re.M)))


def backup(w):
    """Everything this changes, as it stands now: home-style's and home-dock's texts and each thing's props line."""
    keep = HERE / "before-a6271"
    keep.mkdir(exist_ok=True)
    (keep / "home-style.txt").write_text(text_of(w, STYLE) + "\n", encoding="utf-8")
    (keep / "home-dock.txt").write_text(text_of(w, DOCK) + "\n", encoding="utf-8")
    widgets = re.findall(r'^look ("[^"]+")$', (HERE / "data.desk").read_text(encoding="utf-8"), re.M)
    props = {t: answer(w.do(f"look {t}")) for t in things() + widgets}
    (keep / "things.json").write_text(json.dumps(props, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"backup: {keep} (home-style, home-dock, {len(props)} things)")
    return props


def answer(out):
    """The first line of a reply that is its answer, not a '!! since your last look' or its indented list."""
    return next((l for l in out.splitlines() if l.strip() and not l.startswith(("!!", " "))), "")


def preflight(w):
    """True when every thing data.desk names is there and home-dock is a lens this was written against."""
    ok = True
    for t in things():
        first = answer(w.do(f"look {t}"))
        if not first.startswith(t) and f" {t} " not in first:
            print(f"preflight: {t} is not there ({first[:120]})")
            ok = False
    dock = text_of(w, DOCK)
    if not (dock.startswith("# home-dock: the dock along the foot") or dock.startswith("# home-dock: the one bar")):
        print("preflight: home-dock is not the a5500 dock nor this bar; someone changed it: read it before going on")
        ok = False
    # the bar's panel press clears the layout's full= (lane 2's tiling, a5994); with a5496's big=/bigcol= tiling still
    # live, putting away a widened panel would leave the room widened for nothing. The round-3 assembly puts it live.
    if "full=" not in text_of(w, TILING):
        print("preflight: home-tiling is not lane 2's (no full=): the round-3 assembly has not landed; wait for it")
        ok = False
    return ok


def check(w):
    """The bar, its icon lens and home-base built as alex: what a person would be shown."""
    w.d.world.me = "alex"
    bad = 0
    for lens in ("home-dock", "home-base"):
        out = w.do(f"scene {lens}")
        errs = [l for l in out.splitlines() if l.startswith(("ERR", "refused")) or "no lens" in l
                or ("can't tell" in l and lens == "home-dock")]      # home-base's own can't-tells are its panels'
        print(f"scene {lens}: {len(out.splitlines())} lines" + (": " + " | ".join(errs[:4]) if errs else ", no refusal"))
        bad += bool(errs)
    out = w.do("scene home-dock")
    tips = re.findall(r'tip "([^"]*)"', out)
    print(f"tips: {len(tips)}: " + ", ".join(tips))
    return bad == 0


def main():
    args = sys.argv[1:]
    who = args[args.index("--as") + 1] if "--as" in args else "worker-a6271"
    mode = args[0] if args else "check"
    if mode in ("check", "try"):
        w = put.Try(who)
        if not preflight(w):
            raise SystemExit("apply: preflight failed; nothing written")
        run_all(w)
        ok = check(w)
        if mode == "try":
            w.save()
            print("saved into frontier-try")
        raise SystemExit(0 if ok else 1)
    if mode == "door":
        w = put.Live(who)
        if not preflight(w):
            raise SystemExit("apply: preflight failed; nothing sent")
        backup(w)
        run_all(w)
        print("door: done; look at the home base (a page reload brings the painter's tip and hover)")
        return
    raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
