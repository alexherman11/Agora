"""put: the improved At work (a6265) into a world. worker-a6265, 17 Oct.

    python research/window-lab/at-work/put.py try            into frontier-try (a copy): style, lenses, and wear them
    python research/window-lab/at-work/put.py lines <out>    the same as desk lines, to read or send by hand
    python research/window-lab/at-work/put.py check          what a live apply would change, sent nowhere (door read)
    python research/window-lab/at-work/put.py door           live: check first, keep the live text replaced in
                                                             research/window-lab/at-work/kept/, then send through the door

The style is LAMPLIT's (a6057, directions/living/direction-living.style as committed) with at-work.style-roles laid in
before its overrides begin, called direction-living: the painter installs only the root lens's style, so the home base
must wear this one for the new roles to paint. Wearing (try only, unless Alex and the round-3 assembly say otherwise):
home-base's style -> direction-living, and the At work panel note shows house-at-work with house-at-work-small.
Never run door before the round-3 assembly (worker-a5994) has landed (JEFF's commission a6265).
"""
import json
import pathlib
import re
import subprocess
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
LAB = HERE.parents[1] / "text-desk-lab" / "notation"
LIVING = HERE.parent / "directions" / "living" / "direction-living.style"
ROOM = "f5204"
ME = "worker-a6265"
LENSES = ["house-at-work-row", "house-at-work", "house-at-work-small"]
MARK = "# ===== LAMPLIT"
DOOR = "http://127.0.0.1:8794/api/do"


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def style_text():
    base = LIVING.read_text(encoding="utf-8").rstrip("\n")
    mine = (HERE / "at-work.style-roles").read_text(encoding="utf-8").rstrip("\n")
    if mine.splitlines()[0] in base:
        return base                                   # LAMPLIT's build already lays them in (BORROWED)
    i = base.find(MARK)
    return (base[:i].rstrip("\n") + "\n" + mine + "\n" + base[i:]) if i >= 0 else base + "\n" + mine


def notes():
    yield "direction-living", "style", "", style_text()
    for name in LENSES:
        yield name, "lens", "style=direction-living", (HERE / f"{name}.lens").read_text(encoding="utf-8").rstrip("\n")


def explore(lines, world="frontier-try"):
    r = subprocess.run([sys.executable, str(LAB / "explore.py"), world, "--as", ME, "--whole"],
                       input="\n".join(lines) + "\n", capture_output=True, text=True, encoding="utf-8", cwd=LAB)
    return r.stdout + r.stderr


def in_room(text):
    return {m.group(2): m.group(1) for m in re.finditer(r'^\s+(a\d+) note "([^"]+)"', text, re.M)}


def lines(have):
    out = [f"look {ROOM}"]
    for title, tags, props, text in notes():
        if title in have:
            out += [f"read {have[title]}", f"do rewrite {have[title]} text={q(text)}"]
        else:
            out.append(f"do create {ROOM} kind=note title={q(title)} tags={tags} {props} text={q(text)}".replace("  ", " "))
    return out


def wear():
    """Each a run of its own: one already worn is refused ('nothing to change') and must not stop the next."""
    return [["read a5208", "do prop a5208 style=direction-living"],
            ["find prop:role=home-panel,prop:actor=alex,prop:lens=home-work",
             "do prop prop:role=home-panel,prop:actor=alex,prop:lens=home-work lens=house-at-work lesser=house-at-work-small"]]


def door(line, world="frontier"):
    req = urllib.request.Request(DOOR, data=json.dumps({"session": world, "as": ME, "line": line, "whole": True}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode()).get("text", "")


def main(a):
    if not a:
        print(__doc__)
        return
    if a[0] == "try":
        have = in_room(explore([f"look {ROOM} :2"]))
        out = explore(lines(have)) + "".join(explore(w) for w in wear())
        for l in out.splitlines():
            if re.match(r"^(ok |ERR|.*refus|.*MISS|.*unread|.*not compile|.*error|.*unknown role)", l, re.I):
                print(l[:400])
    elif a[0] == "lines":
        pathlib.Path(a[1]).write_text("\n".join(lines({})) + "\n", encoding="utf-8")
    elif a[0] in ("check", "door"):
        have = in_room(door(f"look {ROOM} :2"))
        kept = HERE / "kept"
        plan = lines(have)
        print(f"{len(plan)} lines; would rewrite {[t for t, *_ in notes() if t in have]}, create "
              f"{[t for t, *_ in notes() if t not in have]}")
        if a[0] == "door":
            kept.mkdir(exist_ok=True)
            for title, nid in have.items():
                if title in [t for t, *_ in notes()]:
                    (kept / f"{title}.before.txt").write_text(door(f"read {nid}"), encoding="utf-8")
            for l in plan:
                print(door(l)[:300])


if __name__ == "__main__":
    main(sys.argv[1:])
