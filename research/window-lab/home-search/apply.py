"""apply.py: the home base's search moved out of the viewer into the top bar (a6642, Alex 20 Oct: 'I want search to be
outside of the tiling'), written into a world.

    python research/window-lab/home-search/apply.py check [--as who]          read the live world: every passage present once?
    python research/window-lab/home-search/apply.py try [--as who]            frontier-try of this worktree (no server)
    python research/window-lab/home-search/apply.py door [--as who]           the live world through the keeper's door
    python research/window-lab/home-search/apply.py restore <saved dir> [--as who]   put back what door changed

What it does, in order: the style's new roles (home-style), the new notes in Home base (lenses home-search,
home-thing, home-widgets-end; verbs open-found, close-panel, living on=f5189), the notices widget to the right end
(slot=bar-end), the viewer without its find box (home-viewer: pins and Back on one line), and last the top bar of
home-tiling (the search in its middle; the find no longer widens the viewer; × on a panel that shows one thing).
Edits are passages (do replace), never whole texts, so others' edits to the same lenses stand (a6549's pane body).
door first saves the live text of every note it edits, and the ids it makes, under saved/<stamp>/, and stops at the
first refusal. Its code half (painter words `arrows`, `caret`, the selection `title:a+b`) must be on main first.
"""
import json
import pathlib
import re
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "home-layout"))
import put  # noqa: E402  (Try, Live, q)

ROOM = "f5204"
NOTICES = "a5715"
NOTES = {"style": "a5206", "viewer": "a5486", "tiling": "a5692"}

# a style's `width <n>em` is a most (max-width); a width on the gap scale is the width (style.js)
ROLES = ["role searchbar : width gap x75",
         "role searchdrop : on card, edge rim, corner gap x1.5, pad gap, between gap /2, width gap x75, lift gap",
         "role hitname : text, ink",
         "role hitname.mention : text, soft",
         "role hitkind : text.label tracked, faint"]
HIT = "role hit : between gap, pad gap /2, corner gap"

PASSAGES = {
    "style": [(HIT, HIT + "\n" + "\n".join(ROLES))],
    "viewer": [
        ("# home-viewer: the home base's middle (a5398). Find anything in the world, or press a pin, and it opens here, on the left",
         "# home-viewer: the home base's middle (a5398). Press a pin, or choose a result in the bar's search (home-search, a6642), and it opens here, on the left"),
        ("find= the words in the box, pins=", "find= the words in the bar's search (home-search), pins="),
        ('''  let finding = "yes" when ($v.find or "") != ""
  let finding = "no" otherwise
  bar : row
    role findbar
    box : text "$v.find"
      role find
      hint "Find anything: a note, a chat, a board, a lens…"
      lines 1..1
      share 1
      commit enter only
      on edit do prop $v find="$value"
    clear : text "×"
      role tool
      only when ($v.find or "") != ""
      on click do prop $v find=""
    back : text "Back"
      role chip
      only when ($v.back or "") != ""
      on click do prop $v viewing="$v.back" back="$v.viewing" with=""
  pins : row
    role pins
    only when ($v.pins or "") != ""
    of $v.pins as p
    each pin
''', '''  bar : row
    role pins
    pins : row
      role pins
      share 1
      only when ($v.pins or "") != ""
      of $v.pins as p
      each pin
    gap : column
      share 1
      only when ($v.pins or "") = ""
    back : text "Back"
      role chip
      only when ($v.back or "") != ""
      on click do prop $v viewing="$v.back" back="$v.viewing" with=""
'''),
        ('''      only when open = "yes" or finding = "yes"
      found : column
        share 1
        role found
        scroll scroll
        let q = words-of($v.find)
        only when finding = "yes"
        none : text "Nothing holds those words."
          role meta
          only when count(?$q) = 0
        titles : column
          role foundlist
          of ?$q as f
          clamp 60
          each titled
        rest : column
          role foundlist
          of ?$q as f
          clamp 60
          each mentioned
      open : column
        share 1
        only when open = "yes" and finding = "no"
''', '''      only when open = "yes"
      open : column
        share 1
'''),
        ('''titled : column
  only when $title has $v.find
  hit : row
    role hit
    on click do prop $v viewing=$f back="$v.viewing" find="" with=""
    kind : text "$kind"
      role meta
    title : text "$title"
      role who
      clamp 1
      share 1
mentioned : column
  only when $title !has $v.find
  hit : row
    role hit
    on click do prop $v viewing=$f back="$v.viewing" find="" with=""
    kind : text "$kind"
      role meta
    title : text "$title"
      role meta
      clamp 1
      share 1
''', ""),
    ],
    "tiling": [
        ('''  top : row
    role top
    widgets : row
      lens home-widgets
    brand : text "AGORA"
      role brand
    gap : column
      share 1
    how : text "drag a title anywhere · double-click a title to fill the room · ⇔ widens · – shelves it"
      role hint
    side : text "chat ⇆"
      role tool
      let at = ($lay.pin or "right")
      on click when ($lay.pin or "right") = "right" do prop $lay pin=left
      on click when ($lay.pin or "right") = "left" do prop $lay pin=right
    keys : text "Ctrl+Alt+J or Esc closes"
      role meta
''', '''  top : row
    role top
    left : row
      share 1
      role top
      scroll none
      widgets : row
        lens home-widgets
      brand : text "AGORA"
        role brand
    search : column
      lens home-search
    right : row
      share 1
      role top
      scroll none
      gap : column
        share 1
      ends : row
        lens home-widgets-end
      side : text "chat ⇆"
        role tool
        let at = ($lay.pin or "right")
        on click when ($lay.pin or "right") = "right" do prop $lay pin=left
        on click when ($lay.pin or "right") = "left" do prop $lay pin=right
      keys : text "Ctrl+Alt+J or Esc closes"
        role meta
        tip "Panels" "Drag a title anywhere; double-click a title to fill the room; ⇔ widens a column; – shelves a panel."
'''),
        ('''    chatleft : column
      let wide = 7 when ($lay.full or "") != ""
      let wide = 32 when ($lay.full or "") = "" and count(prop:role=home-view,prop:actor=$me,prop:viewing,-prop:viewing=a5080) + count(prop:role=home-view,prop:actor=$me,prop:find) > 0''',
         '''    chatleft : column
      let wide = 7 when ($lay.full or "") != ""
      let wide = 32 when ($lay.full or "") = "" and count(prop:role=home-view,prop:actor=$me,prop:viewing,-prop:viewing=a5080) > 0'''),
        ('''    chatright : column
      let wide = 7 when ($lay.full or "") != ""
      let wide = 32 when ($lay.full or "") = "" and count(prop:role=home-view,prop:actor=$me,prop:viewing,-prop:viewing=a5080) + count(prop:role=home-view,prop:actor=$me,prop:find) > 0''',
         '''    chatright : column
      let wide = 7 when ($lay.full or "") != ""
      let wide = 32 when ($lay.full or "") = "" and count(prop:role=home-view,prop:actor=$me,prop:viewing,-prop:viewing=a5080) > 0'''),
        ('''      on click do prop $p shelf=yes
  body : column''', '''      on click do prop $p shelf=yes
    close : text "×"
      role tool
      only when ($p.shows or "") != ""
      on click do close-panel $p $col
  body : column'''),
    ],
}
# made in Home base, in this order (a verb before the lens that names it; home-search before home-tiling places it)
NEW = ["close-panel.verb", "open-found.verb", "home-thing.lens", "home-widgets-end.lens", "home-search.lens"]


def text_of(answer):
    """The note's text from a `read <id> :3` answer: between the first two lines that are exactly ---."""
    lines = answer.splitlines()
    marks = [i for i, l in enumerate(lines) if l == "---"]
    return "\n".join(lines[marks[0] + 1:marks[1]]) if len(marks) >= 2 else None


def found(w, name, tag):
    out = w.do(f"find title:{name},tag:{tag},in:{ROOM}")
    return [l.split()[0] for l in out.splitlines() if f'"{name}"' in l and l.strip().startswith("a")]


def plan(key, t):
    """-> [(old, new) still to send], or raises ValueError naming a passage that is neither there once nor done. A
    passage already made (old gone, new there) is skipped, so a run that stopped can run again; the style's roles,
    once in, are each set by their own line."""
    if key == "style" and "role searchbar :" in t:
        have = {l.split(" :")[0]: l for l in t.splitlines() if l.startswith("role ")}
        out = []
        for r in ROLES:
            name = r.split(" :")[0]
            if name not in have:
                raise ValueError(f"{name} missing beside the other search roles")
            if have[name] != r:
                out.append((have[name], r))
        return out
    out = []
    for old, new in PASSAGES[key]:
        n = t.count(old)
        if n == 1:
            out.append((old, new))
        elif not (n == 0 and (new == "" or t.count(new) == 1)):
            raise ValueError(f"passage appears {n} times: {old.splitlines()[0][:90]!r}")
    return out


def check(w):
    ok = True
    for key, nid in NOTES.items():
        t = text_of(w.do(f"read {nid} :3"))
        if t is None:
            print(f"{key} {nid}: could not read its text"); ok = False; continue
        try:
            print(f"{key} {nid}: {len(plan(key, t))} passage(s) to replace")
        except ValueError as e:
            print(f"{key} {nid}: {e}"); ok = False
    for f in NEW:
        p = HERE / f
        hit = found(w, p.stem, "verb" if p.suffix == ".verb" else "lens")
        print(f"{p.stem}: " + (f"exists ({hit[0]}), will be rewritten" if hit else "new"))
    print("check: " + ("every passage present once" if ok else "NOT ready"))
    return ok


def receipt(out):
    return " ".join(l.strip() for l in out.splitlines() if l.startswith(("ok ", "ERR", "~", "→", "stopped")) or "created" in l)[:300]


def refused(out):
    return out.startswith("ERR") or "\nERR" in out or "refused" in out.split("\n")[0]


def apply(w, saved=None):
    made = []

    def step(line, what):
        out = w.do(line)
        print(f"{what}: {receipt(out)}")
        if refused(out):
            raise SystemExit(f"stopped at {what}: {out[:600]}")
        return out

    def passages(key):
        nid = NOTES[key]
        for old, new in plan(key, text_of(w.do(f"read {nid} :3"))):
            w.do(f"read {nid} :3")
            step(f"do replace {nid} old={put.q(old)} new={put.q(new)}", f"{key} {nid} replace {old.splitlines()[0][:50]!r}")

    if saved:
        for key, nid in NOTES.items():
            (saved / f"{key}-{nid}.txt").write_text(text_of(w.do(f"read {nid} :3")), encoding="utf-8")
    passages("style")
    for f in NEW:
        p = HERE / f
        tag = "verb" if p.suffix == ".verb" else "lens"
        text = p.read_text(encoding="utf-8").rstrip("\n")
        hit = found(w, p.stem, tag)
        if hit:
            if text_of(w.do(f"read {hit[0]} :3")) == text:
                print(f"{p.stem} {hit[0]}: as written already")
                continue
            step(f"do rewrite {hit[0]} text={put.q(text)}", f"{p.stem} rewrite {hit[0]}")
            continue
        w.do(f"look {ROOM}")
        more = "tags=verb on=f5189" if tag == "verb" else "tags=lens style=home-style"
        out = step(f"do create {ROOM} kind=note title={p.stem} {more} text={put.q(text)}", f"{p.stem} create")
        m = re.search(r"created (a\d+)", out)
        made.append(m.group(1) if m else "?")
        if saved:
            (saved / "made.json").write_text(json.dumps(made), encoding="utf-8")
    if "slot=bar-end" not in w.do(f"read {NOTICES}").splitlines()[0]:
        step(f"do prop {NOTICES} slot=bar-end", "notices to the bar's right end")
    passages("viewer")
    passages("tiling")
    return made


def restore(w, saved):
    for key, nid in NOTES.items():
        f = saved / f"{key}-{nid}.txt"
        if f.exists():
            w.do(f"read {nid} :3")
            text = f.read_text(encoding="utf-8")
            print(f"{key} {nid}: {receipt(w.do(f'do rewrite {nid} text={put.q(text)}'))}")
    w.do(f"read {NOTICES}")
    print(f"notices: {receipt(w.do(f'do prop {NOTICES} slot=bar'))}")
    made = json.loads((saved / "made.json").read_text(encoding="utf-8")) if (saved / "made.json").exists() else []
    for nid in made:
        w.do(f"look {nid}")
        print(f"remove {nid}: {receipt(w.do(f'do remove {nid}'))}")


def main():
    args = sys.argv[1:]
    who = "worker-a6642"
    if "--as" in args:
        k = args.index("--as"); who = args[k + 1]; del args[k:k + 2]
    mode = args[0]
    w = put.Try(who) if mode == "try" else put.Live(who)
    if mode == "check":
        sys.exit(0 if check(w) else 1)
    if mode == "restore":
        restore(w, pathlib.Path(args[1])); w.save(); return
    if not check(w):
        raise SystemExit("not applied: a passage is missing or doubled (someone changed it); read it and adjust PASSAGES")
    saved = None
    if mode == "door":
        saved = HERE / "saved" / time.strftime("%Y%m%d-%H%M%S")
        saved.mkdir(parents=True)
    apply(w, saved)
    w.save()
    if saved:
        print(f"saved: {saved} (restore: python research/window-lab/home-search/apply.py restore {saved.relative_to(HERE.parents[2]).as_posix()})")


if __name__ == "__main__":
    main()
