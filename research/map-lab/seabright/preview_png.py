"""A flat picture of the ground (for checking the build by eye): python preview_png.py out.png [width]"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw
g = json.loads((Path(__file__).with_name("seabright-ground.json")).read_text(encoding="utf-8"))
W = int(sys.argv[2]) if len(sys.argv) > 2 else 1400
x0, y0, x1, y1 = g["bounds"]
s = W / (x1 - x0); H = int((y1 - y0) * s)
P = lambda f: [((f[i] - x0) * s, (y1 - f[i + 1]) * s) for i in range(0, len(f), 2)]
im = Image.new("RGB", (W, H), "#efe9dc"); d = ImageDraw.Draw(im)
AC = {"sea": "#9fd0e6", "water": "#a8d8ea", "pool": "#9fd7ef", "marina": "#b4dbe9", "beach": "#f3e2b3",
      "park": "#c5e3b0", "green": "#cfe8bb", "wood": "#a9d39a", "wetland": "#bfe0c9", "pitch": "#b5dda0",
      "play": "#e9dcb8", "parking": "#e2ded6", "residential": "#ece6d8", "commercial": "#efdfd6",
      "industrial": "#e2dcd6", "school": "#efe2c8"}
for a in g["areas"]:
    for i, r in enumerate(a["r"]):
        if len(r) >= 6: d.polygon(P(r), fill=AC[a["k"]] if i == 0 else "#efe9dc")
RW = {"major": 9, "street": 6, "service": 3, "walk": 4, "path": 1.5, "cycle": 2, "steps": 1.5}
RC = {"major": "#ffffff", "street": "#ffffff", "service": "#fbf8f2", "walk": "#f7f1e6", "path": "#d9c9a8",
      "cycle": "#b7d3c4", "steps": "#c9a98a"}
for cls in ["path", "cycle", "steps", "service", "walk", "street", "major"]:
    for r in g["roads"]:
        if r["c"] == cls:
            d.line(P(r["p"]), fill=RC[cls], width=max(1, int(RW[cls] * s * 4)))
for r in g["rail"]: d.line(P(r["p"]), fill="#9b8f86", width=2)
for st in g["streams"]: d.line(P(st["p"]), fill="#8cc6df", width=2)
for b in g["buildings"]:
    d.polygon(P(b["r"][0]), fill="#e7c9a9" if b["hs"] == "levels" else "#f0d8bd", outline="#a98c74")
for p in g["pois"]:
    x, y = (p["x"] - x0) * s, (y1 - p["y"]) * s; d.ellipse([x - 2, y - 2, x + 2, y + 2], fill="#d0603f")
im.save(sys.argv[1]); print(W, H)
