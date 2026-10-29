"""Second look: the board's posts and the spot, the place and groups, and what `rows event` and the map's Events layer
see today, before anything is declared."""
import sys
from pathlib import Path

sys.path.insert(0, "C:/Projects/Agora4/research/kernel-lab")
from kernel.kernel import Kernel, Actor  # noqa: E402

k = Kernel(Path(sys.argv[1]))
A = Actor("dk2", "dk2", "person")
print("place", k.place, k.state.get(k.place, "kind"), k.state.get(k.place, "name"))
for t, a in k.state.things.items():
    if a.get("kind") in ("post", "spot", "group", "place", "board-channel") and not a.get("forgotten"):
        print(t, {x: (str(v)[:50]) for x, v in a.items() if not x.startswith(("member:",))})
for line in ("rows event", "rows post post_kind=event", "kinds dk333", "actions dk864", "look dk333",
             "help board.rsvp", "help map.show"):
    out = k.run(A, line, mode="see") if line.startswith(("rows", "kinds", "actions", "look", "help")) else k.run(A, line)
    print(">>", line, "ok=", out.get("ok"))
    print("  ", str(out.get("text"))[:600].replace("\n", "\n   "))
