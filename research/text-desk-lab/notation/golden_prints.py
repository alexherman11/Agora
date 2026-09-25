"""Print every lens in every lab session to a directory, on throwaway copies so no session file changes: the instrument for
the staged-compiler refactor (Jeff). Usage: python golden_prints.py <out dir>; diff two runs. The world @N header and the
`of events` rows drift when a session is live; everything else must match except intended changes."""
import sys, pathlib, shutil, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import deskd, scene
S = pathlib.Path(__file__).resolve().parent / "sessions"
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
n_l = n_s = 0
for pk in sorted(S.glob("*.pickle")):
    if pk.name.startswith("_") or "@" in pk.name:
        continue
    tmp = S / f"_golden_{pk.stem}.pickle"
    shutil.copy(pk, tmp)
    try:
        with deskd.Session(tmp.stem, "jeff") as desk:
            lenses = sorted({s["title"] for s in desk.world.subjects.values() if "lens" in (s.get("tags") or [])})
            d = out / pk.stem
            if lenses:
                d.mkdir(exist_ok=True)
            for t in lenses:
                try:
                    _, text = scene.scene_for(desk, t)
                except scene.LensRefusal as e:
                    text = f"REFUSED: {e}"
                (d / (re.sub(r"[^\w.-]+", "_", t) + ".txt")).write_text(text, encoding="utf-8")
                n_l += 1
            n_s += 1
    finally:
        tmp.unlink(missing_ok=True)
print(f"{n_l} lenses in {n_s} sessions -> {out}")
