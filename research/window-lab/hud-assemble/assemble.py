"""assemble: the HUD sprint's three lanes put into a world as ONE home base, in one safe pass (a5994, round 3; JEFF c6333).
OWNER: worker-a5994, 17 Oct.

    python research/window-lab/hud-assemble/assemble.py check [--as <who>]     read only, against the LIVE world: every
        note it would change found as expected, every old= passage present; prints the plan; writes nothing anywhere
    python research/window-lab/hud-assemble/assemble.py try [--as <who>]       the whole pass into frontier-try (a copy)
    python research/window-lab/hud-assemble/assemble.py door [--as <who>]      the whole pass into the LIVE world
    python research/window-lab/hud-assemble/assemble.py expect      read only: keep the live home-tiling as the text
        this pass was built on (home-tiling.expected); check and door refuse if it has changed since
    python research/window-lab/hud-assemble/assemble.py restore <saved dir> [--as <who>]
        puts the live world back as it was before that door run, in one step (lane 3's own undo, then this pass's)

The order (agreed on the design table a6049, c6262):
  A. lane 2, the desk (research/window-lab/home-layout/): the landing-box and rail roles appended to home-style, the verb
     drop-panel, home-panels, home-tiling (drag a panel by its title, snap, double-click to fill, the chat pinned);
     a5988's feed half (research/window-lab/home-feed/): its roles, the lens home-feed, home-work and home-work-small;
     lane 1, the board (research/window-lab/board-lab/): its nb* block in home-style, home-board, home-board-small,
     The board tagged glance-you and glance-board.
  B. lane 3, LAMPLIT (research/window-lab/directions/living/apply.py, run as itself): home-style made one flat style by
     meaning (it reads home-style as A left it), the glance, The house, the timer, the notices; it saves its own undo.
  C. the assembler's own: The board out of the shelf, Waiting on you on the shelf (the board's NEEDS YOU answers all it
     did, and glance-you is the board's now).
door saves first, under saved/<when>/ beside this file: the text of every note A changes, the panels' lines, undo.desk
(the lines that put A and C back, home-style last, to the text it had before ANY of this) and, once B has run, living.txt
naming lane 3's own saved dir. restore runs lane 3's undo, then undo.desk; each stops at the first refusal and says so.
Every line goes through the keeper's door (127.0.0.1:8794) one command a request; a refusal stops the pass.
"""
import datetime
import json
import pathlib
import re
import subprocess
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
WL = HERE.parent
LAB = WL.parents[0] / "text-desk-lab" / "notation"
DOOR = "http://127.0.0.1:8794/api/do"
sys.path.insert(0, str(WL / "board-lab"))
sys.path.insert(0, str(WL / "home-feed"))
import importlib.util  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


BOARD = _load("board_apply", WL / "board-lab" / "apply.py")
FEED = _load("feed_apply", WL / "home-feed" / "apply.py")
LIVING = WL / "directions" / "living" / "apply.py"
LAYOUT = WL / "home-layout"
ROOM, STYLE, TILING, PANELS = "f5204", "a5206", "a5692", "a5690"
WAITING, THEBOARD = "a5668", "a5674"


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def body_of(said):
    if "---" not in (said or ""):
        return None
    return said.split("---", 1)[1].rsplit("---", 1)[0].strip("\n")


class Live:
    name = "frontier (live)"

    def __init__(self, who):
        self.who = who

    def do(self, line):
        body = json.dumps({"session": "frontier", "as": self.who, "line": line, "whole": True}).encode()
        with urllib.request.urlopen(urllib.request.Request(DOOR, body, {"Content-Type": "application/json"}), timeout=90) as f:
            r = json.loads(f.read())
        if r.get("error"):
            return "ERR " + str(r["error"])
        return r.get("text") or ""

    def apply(self, lines):
        out = []
        for l in lines:
            said = self.do(l)
            out.append(said)
            print(said[:240].replace("\n", " | "))
            if refused(said):
                return out, l
        return out, None


class Try:
    name = "frontier-try (a copy)"

    def __init__(self, who):
        self.who = who

    def run(self, lines):
        r = subprocess.run([sys.executable, str(LAB / "explore.py"), "frontier-try", "--as", self.who, "--whole"],
                           input="\n".join(lines) + "\n", capture_output=True, text=True, encoding="utf-8", cwd=LAB)
        return r.stdout + r.stderr

    def do(self, line):
        return self.run([line])

    def apply(self, lines):
        out = self.run(lines)
        for chunk in re.split(r"^> ", out, flags=re.M):
            if refused(chunk):
                print(chunk[:400])
                return [out], chunk.splitlines()[0]
        print("\n".join(l[:200] for l in out.splitlines() if re.match(r"^(ok |~ lens|~ style)", l)))
        return [out], None


def refused(said):
    s = said or ""
    return bool(re.search(r"^(ERR|MISS)|\brefused\b|does not compile|stopped:", s[:600], re.M))


def text_of(w, ident):
    return body_of(w.do(f"read {ident} :3"))


def note_line(w, ident):
    """The note's own line (title, props, tags), as find prints it."""
    said = w.do(f"examine {ident}")
    return said.splitlines()[0] if said else ""


def file(path):
    return pathlib.Path(path).read_text(encoding="utf-8").rstrip("\n")


def plan(w):
    """-> (lines A, lines C, saves, undo A+C in the order to run, report, problems)."""
    report, problems, saves = [], [], {}
    A, C, undo = [], [], []
    style0 = text_of(w, STYLE)
    if not style0 or "role " not in style0:
        raise SystemExit(f"refused: {STYLE} is not home-style in {w.name}")
    saves["home-style.style"] = style0
    # --- lane 2, the desk ---
    style_lines = [l for l in file(LAYOUT / "style-a5994.desk").splitlines() if l.startswith("do append")]
    if "role landing :" in style0:
        report.append("desk: home-style already has the landing and rail roles; not appended again")
    else:
        A += [f"read {STYLE}"] + style_lines
        report.append(f"desk: {len(style_lines)} lines appended to home-style (rail, railitem, railitem.on, landing)")
    if 'note "drop-panel"' in w.do("find title:drop-panel,tag:verb"):
        problems.append("a verb drop-panel already exists here: remove it or adjust this plan")
    verb = file(LAYOUT / "drop-panel.verb")
    A += [f"look {ROOM}", f"do create {ROOM} kind=note title=drop-panel tags=verb on=f5189 text={q(verb)}"]
    undo_created = ['read "drop-panel"', 'do remove "drop-panel"']
    report.append("desk: the verb drop-panel made in Home base (on=f5189)")
    tiling0, panels0 = text_of(w, TILING), text_of(w, PANELS)
    saves["home-tiling.lens"], saves["home-panels.lens"] = tiling0, panels0
    expected = file(HERE / "home-tiling.expected")
    if tiling0 != expected:
        problems.append("home-tiling (a5692) is not the text this pass was built on (home-tiling.expected): someone has "
                        "changed it; carry their change into home-layout/home-tiling.lens and refresh the expected copy")
    A += [f"read {PANELS}", f"do rewrite {PANELS} text={q(file(LAYOUT / 'home-panels.lens'))}",
          f"read {TILING}", f"do rewrite {TILING} text={q(file(LAYOUT / 'home-tiling.lens'))}"]
    undo += [f"read {TILING}", f"do rewrite {TILING} text={q(tiling0)}", f"read {PANELS}", f"do rewrite {PANELS} text={q(panels0)}"]
    report.append(f"desk: home-panels {PANELS} and home-tiling {TILING} rewritten")
    # --- a5988's feed half ---
    if 'note "home-feed"' in w.do("find title:home-feed,tag:lens"):
        problems.append("a lens home-feed already exists: the feed half is for a world that has none")
    work0, worksmall0 = text_of(w, '"home-work"'), text_of(w, '"home-work-small"')
    saves["home-work.lens"], saves["home-work-small.lens"] = work0, worksmall0
    if FEED.SMALL_OLD not in (worksmall0 or ""):
        problems.append("home-work-small does not hold the passage the feed half replaces")
    A += FEED.lines()
    undo_created += ['read "home-feed"', 'do remove "home-feed"']
    undo += ['read "home-work-small"', f'do rewrite "home-work-small" text={q(worksmall0 or "")}',
             'read "home-work"', f'do rewrite "home-work" text={q(work0 or "")}']
    report.append("feed: its roles appended, home-feed made, home-work rewritten, home-work-small counts workers too")
    # --- lane 1, the board ---
    board0, small0 = text_of(w, BOARD.BOARD), text_of(w, BOARD.SMALL)
    saves["home-board.lens"], saves["home-board-small.lens"] = board0, small0
    saves["the-board-panel.txt"] = note_line(w, THEBOARD)
    A += BOARD.lines(style0)
    undo += [f"read {BOARD.SMALL}", f"do rewrite {BOARD.SMALL} text={q(small0)}",
             f"read {BOARD.BOARD}", f"do rewrite {BOARD.BOARD} text={q(board0)}",
             f"read {THEBOARD}", f"do tag {THEBOARD} remove=glance-you,glance-board"]
    report.append("board: the nb* block into home-style, home-board and home-board-small rewritten, The board tagged")
    # --- C, the assembler's own ---
    wline, bline = note_line(w, WAITING), note_line(w, THEBOARD)
    saves["waiting-panel.txt"] = wline
    bshelf = re.search(r"\bshelf=(\S+)", bline)
    wshelf = re.search(r"\bshelf=(\S+)", wline)
    if not bshelf or bshelf.group(1) != "no":
        C += [f"read {THEBOARD}", f"do prop {THEBOARD} shelf=no"]
        undo = [f"read {THEBOARD}", f"do prop {THEBOARD} shelf={bshelf.group(1) if bshelf else 'yes'}"] + undo
    if not wshelf or wshelf.group(1) != "yes":
        C += [f"read {WAITING}", f"do prop {WAITING} shelf=yes"]
        undo = [f"read {WAITING}", f"do prop {WAITING} shelf={wshelf.group(1) if wshelf else 'no'}"] + undo
    if "glance-you" in wline:
        C += [f"read {WAITING}", f"do tag {WAITING} remove=glance-you"]
        undo = [f"read {WAITING}", f"do tag {WAITING} add=glance-you"] + undo
    # the board's column takes two shares of the panels' room: with a document open beside the chat that room is about
    # 730 px, and at one share the board's NEEDS YOU titles were cut to a few letters (playtest 17 Oct, card step)
    col = re.search(r"\bin (f\d+)", w.do(f"examine {THEBOARD}"))
    if col:
        span = re.search(r"\bspan=(\S+)", note_line(w, col.group(1)))
        if not span or span.group(1) != "2":
            C += [f"look {col.group(1)}", f"do prop {col.group(1)} span=2"]
            undo = [f"look {col.group(1)}", f"do prop {col.group(1)} " + (f"span={span.group(1)}" if span else "remove=span")] + undo
    report.append("assembler: The board out of the shelf, its column two shares wide, Waiting on you shelved (and glance-you off it if tagged)")
    # home-style last of all, back to the text it had before any lane wrote to it
    undo += undo_created + [f"read {STYLE}", f"do rewrite {STYLE} text={q(style0)}"]
    return A, C, saves, undo, report, problems


def run_living(how, who):
    extra = ["--world", "live"] if how == "check" else []
    r = subprocess.run([sys.executable, str(LIVING), how, "--as", who, *extra], capture_output=True, text=True, encoding="utf-8")
    out = r.stdout + r.stderr
    print("\n".join(l[:200] for l in out.splitlines()[-40:]))
    m = re.search(r"undo\.desk, in (\S+)", out)
    return r.returncode, out, (m.group(1) if m else None)


def opt(a, k, d=None):
    return a[a.index(k) + 1] if k in a else d


def main(a):
    if not a or a[0] not in ("check", "try", "door", "restore", "expect"):
        print(__doc__)
        return 0
    who = opt(a, "--as", "worker-a5994")
    if a[0] == "expect":             # read only: the live home-tiling this pass is built on, kept to compare against
        t = text_of(Live(who), TILING)
        (HERE / "home-tiling.expected").write_text(t + "\n", encoding="utf-8")
        print(f"kept the live home-tiling ({len(t.splitlines())} lines) as home-tiling.expected")
        return 0
    if a[0] == "restore":
        d = pathlib.Path(a[1])
        w = Live(who)
        liv = (d / "living.txt")
        if liv.exists():
            ld = pathlib.Path(liv.read_text(encoding="utf-8").strip())
            if not ld.is_absolute():               # as committed: from the checkout's root, wherever that is now
                ld = WL.parents[1] / ld
            r = subprocess.run([sys.executable, str(LIVING), "undo", str(ld), "--as", who],
                               capture_output=True, text=True, encoding="utf-8")
            print(r.stdout[-3000:] + r.stderr[-1000:])
            if r.returncode:
                print("stopped: lane 3's undo was refused; nothing more was put back")
                return 1
        _, bad = w.apply((d / "undo.desk").read_text(encoding="utf-8").splitlines())
        if bad:
            print(f"stopped at: {bad[:160]}")
            return 1
        print("restored: the home base is as it was before", d.name)
        return 0
    w = Live(who) if a[0] in ("check", "door") else Try(who)
    A, C, saves, undo, report, problems = plan(w)
    print(f"the assembled HUD into {w.name}:")
    for r in report:
        print("  " + r)
    for p in problems:
        print("  PROBLEM " + p)
    print(f"  {len(A)} lines (A), then lane 3's apply (B), then {len(C)} lines (C); undo {len(undo)} lines")
    if a[0] == "check":
        code, out, _ = run_living("check", who)
        return 1 if problems or code else 0
    if problems:
        print("refused: the problems above; nothing sent")
        return 1
    d = None
    if a[0] == "door":
        d = HERE / "saved" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        d.mkdir(parents=True, exist_ok=True)
        for name, t in saves.items():
            (d / name).write_text((t or "") + "\n", encoding="utf-8")
        (d / "undo.desk").write_text("\n".join(undo) + "\n", encoding="utf-8")
        (d / "apply-A.desk").write_text("\n".join(A) + "\n", encoding="utf-8")
        (d / "apply-C.desk").write_text("\n".join(C) + "\n", encoding="utf-8")
        print(f"saved what it replaces, and undo.desk, in {d}")
        mirror(d, None)
    _, bad = w.apply(A)
    if bad:
        print(f"stopped in A at: {bad[:200]}" + (f"\nto put back what was done: assemble.py restore {d}" if d else ""))
        return 1
    code, out, living_dir = run_living("door" if a[0] == "door" else "try", who)
    if d and living_dir:
        try:
            said = pathlib.Path(living_dir).resolve().relative_to(WL.parents[1]).as_posix()
        except ValueError:
            said = living_dir
        (d / "living.txt").write_text(said + "\n", encoding="utf-8")
    if code:
        print("stopped in B (lane 3's apply)" + (f"\nto put back what was done: assemble.py restore {d}" if d else ""))
        return 1
    _, bad = w.apply(C)
    if d:
        mirror(d, living_dir)
    if bad:
        print(f"stopped in C at: {bad[:200]}" + (f"\nto put back what was done: assemble.py restore {d}" if d else ""))
        return 1
    print("done" + (f"; to put it all back: python research/window-lab/hud-assemble/assemble.py restore {d}" if d else ""))
    return 0


def mirror(d, living_dir):
    """A worker's worktree goes when it is done: the record is copied where the main checkout keeps films (ignored by
    git, outliving any worktree) as well as committed with the branch. living.txt in the copy names the copy of lane 3's."""
    import shutil
    base = pathlib.Path("C:/Projects/Agora4/research/window-lab/demos/a5994/saved")
    try:
        shutil.copytree(d, base / d.name, dirs_exist_ok=True)
        if living_dir:
            shutil.copytree(living_dir, base / d.name / "living", dirs_exist_ok=True)
            (base / d.name / "living.txt").write_text(str(base / d.name / "living") + "\n", encoding="utf-8")
        print(f"a copy of the record: {base / d.name}")
    except OSError as e:
        print(f"(the copy into the main checkout failed: {e}; the record is in {d})")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
