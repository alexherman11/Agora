"""put.py: the home base's layout seed (a5496, 15 Oct 2026), written into a world.

    python research/window-lab/home-layout/put.py try|live [--as who] <file.lens | file.desk> ...

The world is the truth: these files are what a5496 wrote there on 15 Oct, kept so the step can be repeated (a fresh
world, a copy) and read. Change the lenses in the world, not here.

A .lens file's name is the lens title and its text is the lens: a note of that title in Home base (f5204) is
rewritten (read first), else made, tagged lens, style=home-style. A .desk file is desk lines, one a line, run in order;
a line that begins with # is skipped. try: the worktree's frontier-try, loaded and saved here (never a world a
server holds). live: through the keeper's door (127.0.0.1:8794), a real act in the real world.

The whole step, in order, once the code it needs (share $(...), scroll none and none end) is on main:
    style.desk  waiting-on-me-small.lens home-board-small.lens home-work-small.lens home-tiles-small.lens
    home-panels.lens home-tiling.lens  layout-alex.desk  strip.desk dock.desk chat.desk  home-base.lens
strip.desk, dock.desk and chat.desk replace exact passages as they stood on 15 Oct: a refusal there means someone has
changed that lens since, so read it and adjust the line, never force it. home-base.lens goes last: until then the home
base is the old frame and nothing a person sees changes.
"""
import json
import pathlib
import sys
import urllib.request
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
NOTATION = pathlib.Path(__file__).resolve().parents[2] / "text-desk-lab" / "notation"
sys.path.insert(0, str(NOTATION))


def q(s):
    """A value in double quotes, as the door reads one: backslash, quote and dollar escaped, newlines as \\n."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


class Try:
    def __init__(self, who):
        import explore
        self.explore = explore
        self.path = NOTATION / "sessions" / "frontier-try.pickle"
        self.d = explore.load_desk(self.path)
        self.d.world.me = who

    def do(self, line):
        r = self.d.dispatch("desk", {"line": line, "reply": "put"})
        return r.get("text") or "ERR " + str(r.get("error"))

    def save(self):
        self.explore.save_desk(self.path, self.d)


class Live:
    def __init__(self, who):
        self.who = who

    def do(self, line):
        body = json.dumps({"session": "frontier", "as": self.who, "line": line, "whole": True}).encode()
        req = urllib.request.Request("http://127.0.0.1:8794/api/do", data=body, headers={"Content-Type": "application/json"})
        out = json.loads(urllib.request.urlopen(req, timeout=60).read())
        return out.get("text") or "ERR " + str(out.get("error"))

    def save(self):
        pass


def put_lens(w, path):
    name, text = path.stem, path.read_text(encoding="utf-8").rstrip("\n")
    found = w.do(f"find title:{name},tag:lens,in:f5204")
    hit = [l.split()[0] for l in found.splitlines() if f'"{name}"' in l and l.strip().startswith("a")]
    if hit:
        w.do(f"read {hit[0]}")
        out = w.do(f"do rewrite {hit[0]} text={q(text)}")
    else:
        out = w.do(f"look f5204; do create f5204 kind=note title={name} style=home-style text={q(text)}; do tag $new add=lens")
    print(name + ": " + " ".join(l.strip() for l in out.splitlines() if l.startswith(("ok ", "ERR", "~", "stopped"))))


def main():
    args = sys.argv[1:]
    who = args[args.index("--as") + 1] if "--as" in args else "worker-a5496"
    if "--as" in args:
        k = args.index("--as")
        del args[k:k + 2]
    w = Try(who) if args[0] == "try" else Live(who)
    for f in args[1:]:
        p = pathlib.Path(f)
        if p.suffix == ".lens":
            put_lens(w, p)
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                out = w.do(line)
                print("> " + line[:160] + "\n  " + "\n  ".join(l for l in out.splitlines() if l.startswith(("ok ", "ERR", "stopped", "~")))[:600])
    w.save()


if __name__ == "__main__":
    main()
