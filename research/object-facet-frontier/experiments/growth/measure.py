"""Growth measures for the lens compiler and painter (Pike, round six). Read-only over git history and source.

    .venv/Scripts/python.exe research/object-facet-frontier/experiments/growth/measure.py [--history]

M1 lines per word over history; M2 per-word branches inside the scene builder; M3 how many compiler functions and
painter each word's field touches; M4 painter fields that the text printer does not print; M5 hidden state written
by the compiler outside world events; M6 painted elements per scene node (createElement sites in the painter).
"""
import ast, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
NOT = ROOT / "research/text-desk-lab/notation"
SCENE, PAINTER = "research/text-desk-lab/notation/scene.py", "research/text-desk-lab/notation/desk-shell/lens.js"
WORDS = {"layout": ["layout"], "role": ["role"], "text": ["text", "props", "read", "missing"], "clamp": ["clamp", "cut"],
         "of": ["of", "states"], "over": ["over"], "each": ["each"], "at": ["at", "box", "facts"], "spread": ["spread", "placed"],
         "lens": ["lens"], "only": ["only", "absent"], "the": ["the"], "as": ["as", "frames", "freads"],
         "derive": ["derive", "derived"], "capture": ["capture", "captured"], "on": ["on", "acts", "reads", "rev", "bind"]}


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, encoding="utf-8", cwd=ROOT).stdout


def funcs(src):
    t, out = ast.parse(src), {}
    for n in ast.walk(t):
        if isinstance(n, ast.FunctionDef):
            out[n.name] = "\n".join(src.splitlines()[n.lineno - 1:n.end_lineno])
    return out


def parse_words(src):
    p = funcs(src).get("parse", "")
    return len(re.findall(r"^\s+(?:elif|if) (?:word|p )", p, re.M))


def make_branches(src):
    m = funcs(src).get("make", "")
    return len(re.findall(r"^\s+if node\[|^\s+if node\.get", m, re.M))


def history():
    print("M1/M2 history: commit date total_lines parse_word_branches make_lines make_word_branches")
    for c in git("log", "--reverse", "--format=%h %cd", "--date=format:%m-%d", "--", SCENE).split("\n"):
        if not c:
            continue
        h, d = c.split()
        s = git("show", f"{h}:{SCENE}")
        print(f"  {h} {d} {len(s.splitlines()):4d} {parse_words(s):3d} {len(funcs(s).get('make', '').splitlines()):4d} {make_branches(s):3d}")


def touch():
    s, js = (NOT / "scene.py").read_text(encoding="utf-8"), (NOT / "desk-shell/lens.js").read_text(encoding="utf-8")
    fs = funcs(s)
    print("M3 functions each word's fields appear in (compiler) + painter:")
    for w, fields in WORDS.items():
        pat = re.compile(r"""(?:node|n|out|kid)(?:\[|\.get\()["'](%s)["']""" % "|".join(fields))
        where = sorted(name for name, body in fs.items() if pat.search(body))
        painter = bool(re.search(r"\bn\.(%s)\b" % "|".join(fields), js))
        print(f"  {w:8s} {len(where)} fn {'+ painter' if painter else '         '}  {', '.join(where)}")
    painted = set(re.findall(r"\bn\.([a-z_]+)", js)) - {"length", "search", "kids", "key"}
    printed = set(re.findall(r"""n(?:\[|\.get\()["']([a-z_]+)["']""", fs.get("to_text", "")))
    print(f"M4 painted fields not printed by to_text: {sorted(painted - printed) or 'none'}")
    hidden = sorted(set(re.findall(r"desk\.(_[a-z_]+) *=", s)))
    print(f"M5 compiler state written outside world events: {hidden or 'none'}")
    print(f"M6 createElement sites in painter make(): {js.count('createElement')} (one element per scene node when 1)")
    print(f"sizes: scene.py {len(s.splitlines())} lines, make() {len(fs['make'].splitlines())}, lens.js {len(js.splitlines())}")


if __name__ == "__main__":
    if "--history" in sys.argv or len(sys.argv) == 1:
        history()
    touch()
