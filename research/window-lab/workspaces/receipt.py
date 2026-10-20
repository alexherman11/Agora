"""receipt.py: what JEFF reads back from one `workspace <words>` (a6427), on a copy in memory with apply.py's steps.

    python research/window-lab/workspaces/receipt.py app-dev [back ...]
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "home-layout"))
import apply  # noqa: E402
import put  # noqa: E402

w = put.Try("jeff")
apply.run(w)
w.d.world.me = "jeff"
for words in sys.argv[1:]:
    out = w.do("workspace " + words.replace("+", " "))
    print(f"> workspace {words}\n{out}\n  ({len(out)} characters)\n")
