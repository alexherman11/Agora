"""test_textedit_paint (a6067): the continuous-text module (desk-shell/textedit.js) in a real browser.

    python test_textedit_paint.py [-v] [--shot file.png]

Drives screen.py (headless Chrome or Edge) on a scratch world with one document, lens te-probe (the document as
`markdown` with `on edit` a whole-text rewrite, and a chat composer), and runs two checks in the page:
  checks/textedit_core.js   the module's core and plain surface against a stand-in desk (fitting, conflicts, two
                            windows, an input method, AltGr, the two undos);
  checks/textedit_page.js   the same in the painter, against deskd: a resident's `do replace` over live typing
                            (fitted, and a conflict refused loudly), composition, AltGr, the undo seam (the world's
                            undo of a sent edit), passage ids, two windows (a named frame), and the chat composer.
health runs every test_*_paint.py when a browser is here.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

LENS = "\n".join([
    "w : column",
    "  docs : column",
    "    of title:te-doc as d",
    "    each page",
    '  say : text ""',
    '    hint "Write to the chat"',
    "    lines 1..6",
    "    commit explicit",
    '    on edit do append CHAT line="$value"',
    "page : column",
    '  body : text "$d.text"',
    "    markdown",
    '    hint "Start writing"',
    '    on edit do read $d.item; do rewrite $d.item text="$value"',
])
TEXT = "Intro.\n\nThe plan is to bild it.\n"
q = lambda s: '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def main():
    import explore
    import screen
    if not any(os.path.exists(b) for b in screen.BROWSERS):
        print("skip: no Chrome or Edge to paint with")
        return 0
    d = explore.fresh()
    d.world.me = "worker-a6067"
    d.dispatch("desk", {"line": "look"})
    root = d.world.root
    chat = d.dispatch("desk", {"line": f"do create {root} kind=chat title=te-chat"})
    cid = re.search(r"\b(a\d+)\b", chat.get("text") or "").group(1)
    made = d.dispatch("desk", {"line": f"do create {root} kind=note title=te-doc text={q(TEXT)}"})
    assert "created" in (made.get("text") or ""), made
    made = d.dispatch("desk", {"line": f"do create {root} kind=note title=te-probe tags=lens text={q(LENS.replace('CHAT', cid))}"})
    assert "created" in (made.get("text") or ""), made
    world = "_test_textedit_paint"
    path = HERE / "sessions" / f"{world}.pickle"
    explore.save_desk(path, d)
    shot = sys.argv[sys.argv.index("--shot") + 1] if "--shot" in sys.argv else "screen-textedit.png"
    try:
        out = subprocess.run([sys.executable, str(HERE / "screen.py"), world, "--as", "worker-a6067", "--lens", "te-probe", "--size", "1400x900",
                              "js", "@" + str(HERE / "desk-shell" / "checks" / "textedit_core.js"),
                              "js", "@" + str(HERE / "desk-shell" / "checks" / "textedit_page.js"),
                              "js", "@" + str(HERE / "desk-shell" / "checks" / "viewer_contract.js"), "shot", shot],
                             capture_output=True, text=True, timeout=400, encoding="utf-8", errors="replace").stdout
    finally:
        for p in path.parent.glob(world + "*"):
            p.unlink(missing_ok=True)
    answers = re.findall(r'^"(.*)"$', out, re.M)
    if "-v" in sys.argv or len(answers) < 3 or not all(re.search(r"all \d+ passed", a) for a in answers):
        print(out.replace("\\n", "\n"))
    said = []
    for name, a in zip(("core", "page", "viewer contract"), answers + [""] * 3):
        m = re.search(r"(all \d+ passed|\d+ passed, \d+ FAILED)", a)
        said.append((name, m.group(1) if m else "no answer"))
    ok = all(s.startswith("all") for _, s in said)
    print(f"{'ok' if ok else 'FAIL'} textedit: " + "; ".join(f"{n} {s}" for n, s in said))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
