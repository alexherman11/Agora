"""hud_stage: screen.py for the home base, with the stage the real one stands on. OWNER: worker-a5534 (15 Oct, a5534).

The home base (hud.py) paints over a frosted, darkened copy of Alex's screen, beside a house whose residents are at work
and a desktop of open windows. A screen.py copy of the world has none of these: the page is white, `house doing=working`
is empty (the copy's world has no house-state), and witnessed:desktop has no rows. This sets them for the copy only:

    python src/desktop/hud_stage.py [--busy] [--frost <name>] <screen.py arguments ...>

--busy      the house says jeff and sable are working (house-state/<the copy>/house.json, as house.py beats it)
--crew      instead, whom it says: corner=actor:doing,... (e.g. f5189=jeff:working,a6057=worker-a6057:working)
--frost     the stand-in frost behind the page: dusk (default), none. A gradient, never a picture of anyone's screen.
Always:     six stand-in windows as witnessed:desktop (generic titles), the first one in front.

It runs screen.main in this process, so the copy is sessions/<world>-screen-<this pid>, and removes what it wrote.
Everything screen.py says (--size, --lens, steps, js ...) works as there. Nothing reaches the shared world.
"""
import json
import os
import shutil
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parents[2] / "src" / "text-desk" / "notation"
sys.path.insert(0, str(LAB))
import screen      # noqa: E402
import witnessed   # noqa: E402

WINDOWS = [("Visual Studio Code", "Code.exe"), ("Inbox - Mail", "olk.exe"), ("Music", "Spotify.exe"),
           ("Agora notation - Terminal", "WindowsTerminal.exe"), ("Docs - Edge", "msedge.exe"), ("Files", "explorer.exe")]
FROSTS = {
    # a darkened, blurred desktop stand-in: two soft lights over near-black, as hud.py's frost reads after its 0.42
    "dusk": "html{background:radial-gradient(1200px 800px at 18% 22%,#2a3c4a 0%,transparent 60%),"
            "radial-gradient(900px 700px at 82% 70%,#3a2a40 0%,transparent 62%),"
            "radial-gradient(700px 500px at 60% 10%,#1d3a33 0%,transparent 60%),#0b0d10 fixed!important}"
            "body,#paint{background:transparent!important}",
    "none": "",
}


def main():
    a = sys.argv[1:]
    busy = "--busy" in a
    a = [x for x in a if x != "--busy"]
    crew = None
    if "--crew" in a:     # a6057: whom the house says is where, corner=actor:doing,... (implies --busy)
        i = a.index("--crew")
        crew = {c: tuple(v.split(":", 1)) for c, v in (x.split("=", 1) for x in a[i + 1].split(","))}
        busy = True
        del a[i:i + 2]
    frost = "dusk"
    if "--frost" in a:
        i = a.index("--frost")
        frost = a[i + 1]
        del a[i:i + 2]
    world = a[0]
    session = f"{world}-screen-{os.getpid()}"
    base = LAB / "house-state" / session
    # names as long as a real window handle's, so hud.py's SLOTS finds their tiles as it would (a5736)
    witnessed.write(session, "desktop", [{"name": str(1000000 + i), "title": t, "program": p, "front": "yes" if i == 0 else "no"}
                                         for i, (t, p) in enumerate(WINDOWS)], by="hud_stage")
    if busy:
        # two residents, and three builders at work on commissions that are working in the copy (their cards breathe)
        doing = {"f5189": ("jeff", "working"), "f571": ("sable", "working"), "f576": ("pike", "resting"),
                 "a5496": ("worker-a5496", "working"), "a5530": ("worker-a5530", "working"),
                 "a5534": ("worker-a5534", "working")} if crew is None else crew
        st = {"pid": os.getpid(), "beat": time.time() + 3600, "world": session,
              "residents": {c: {"actor": n, "alive": True, "doing": d, "turns": 3, "last_turn": time.time()}
                            for c, (n, d) in doing.items()}, "workers": {}}
        (base / "house.json").write_text(json.dumps(st), encoding="utf-8")
    css = FROSTS.get(frost, "")
    steps = []
    if css:     # first, before any step: the frost as hud.py's dress() puts it, then a moment for the repaint
        steps = ["js", "(() => { const s = document.createElement('style'); s.id = 'hud-frost'; s.textContent = "
                 + json.dumps(css) + "; document.head.append(s); return 'frost'; })()", "wait", "300"]
    # the steps go after the options: find where screen.py's options end
    opts, k = [a[0]], 1
    while k < len(a) and a[k].startswith("--"):
        n = 1 if a[k] in ("--reduced-motion", "--term", "--live", "--bare") else 2
        opts += a[k:k + n]
        k += n
    sys.argv = ["screen.py"] + opts + steps + a[k:]
    try:
        screen.main()
    finally:
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    import urllib.parse  # noqa: F401  (screen.main needs it, as its own __main__ imports it)
    main()
