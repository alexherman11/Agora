"""A stand-in for Rocket League in the overlay test (a6313): a window covering one monitor, as a borderless game does,
with a ball that moves every frame (so a film shows it kept running) and a line that says whether it has the keyboard.

    python standin_game.py <out-dir> <x> <y> <w> <h>

Writes <out-dir>/standin.json ({"hwnd": its top-level window}) once shown, and appends every focus change it gets to
<out-dir>/standin-focus.log. Only ever started on the sandbox desktop by test_overlay.py."""
import ctypes
import json
import sys
import time
import tkinter as tk
from pathlib import Path

ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
out = Path(sys.argv[1])
x, y, w, h = (int(v) for v in sys.argv[2:6])
log = out / "standin-focus.log"

root = tk.Tk()
root.title("stand-in game")
root.geometry(f"{w}x{h}+{x}+{y}")
root.configure(bg="#14361f")
c = tk.Canvas(root, bg="#14361f", highlightthickness=0)
c.pack(fill="both", expand=True)
ball = c.create_oval(0, 0, h // 12, h // 12, fill="#e8e8e8", outline="")
label = c.create_text(w // 2, h // 2, text="stand-in game", fill="#9fd3a8", font=("Segoe UI", max(12, h // 40)))
state = {"focus": "not yet", "n": 0}


def note(what):
    state["focus"] = what
    with log.open("a", encoding="utf-8") as f:
        f.write(f"{time.time():.3f} {what}\n")


root.bind("<FocusIn>", lambda e: e.widget is root and note("in"))
root.bind("<FocusOut>", lambda e: e.widget is root and note("out"))


def frame():
    state["n"] += 1
    n = state["n"]
    bx = (n * 9) % (2 * w)
    bx = bx if bx < w else 2 * w - bx
    c.coords(ball, bx, h * 0.62, bx + h // 12, h * 0.62 + h // 12)
    c.itemconfigure(label, text=f"stand-in game   frame {n}   keyboard: {state['focus']}")
    root.after(33, frame)


def shown():
    root.focus_force()
    (out / "standin.json").write_text(json.dumps({"hwnd": int(root.wm_frame(), 16)}), encoding="utf-8")


root.after(300, shown)
root.after(33, frame)
root.mainloop()
