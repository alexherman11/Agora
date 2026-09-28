"""Seed (or reseed) the pixel style and the command-center lens into a world's Porch, then print `scene command-center`.

    python install_ui.py <world> [as]
"""
import pathlib
import re
import sys

sys.path.insert(0, "C:/Projects/Agora4/research/text-desk-lab/notation")
import desk_mcp  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
WORLD = sys.argv[1]
WHO = sys.argv[2] if len(sys.argv) > 2 else "claude"


def q(s):
    return '"' + s.replace("\\", "\\\\\\\\").replace('"', '\\"').replace("\n", "\\n").replace("$", "\\$") + '"'


def run(line):
    return desk_mcp.run_desk({"line": line, "as": WHO, "session": WORLD})[0]


def put(title, tags, text, props=""):
    found = run(f"find title:{title.split()[0]},tag:{tags.split(',')[0]}")
    m = re.search(r"(a\d+) note \"" + re.escape(title) + '"', found)
    if m:
        out = run(f"read {m.group(1)}; do rewrite {m.group(1)} text={q(text)}")
    else:
        out = run(f"do create Porch kind=note title={q(title)} tags={tags} text={q(text)}")
        m = re.search(r"→ created (a\d+)", out)
    if props and m:
        out += run(f"look {m.group(1)} :1; do prop {m.group(1)} {props}")
    if "ERR" in out:
        print(out)
    return m.group(1) if m else None


style = put("pixel", "style", (HERE / "pixel.style").read_text(encoding="utf-8"))
lens = put("command-center", "lens", (HERE / "command-center.lens").read_text(encoding="utf-8"), "style=pixel")
print("style", style, "lens", lens)
print(run("scene command-center"))
