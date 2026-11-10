"""A short film of the home base's widgets (a5530), made on a COPY of the world in headless Chrome (screen.py), never on
Alex's screen: the clock, a Now line written, a notice arriving and dismissed, a 15-second focus counted down to its
end with a notice held while it runs, and the break letting it in. Frames are the bar, cropped, about one a second;
ffmpeg joins them. The click on the Now line is at its place in the frame before a5496's layout (366,47).

    python src/desktop/widgets/demo.py [out.mp4]      (default: src/desktop/demos/a5530-widgets.mp4
                                                                of the main checkout, which git ignores)
Needs the widgets in src/text-desk/notation/sessions/frontier-try.pickle first (apply.py lines, then explore.py)."""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCREEN = ROOT / "src" / "text-desk" / "notation" / "screen.py"
FFMPEG = ("C:/Users/Alex/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/"
          "ffmpeg-8.1.1-full_build/bin/ffmpeg.exe")
MAIN_DEMOS = pathlib.Path("C:/Projects/Agora4/src/desktop/demos")
TIMER = '"Alex\'s timer"'


def press(suffix):
    """A click on the painted part whose key ends with `suffix` (ids differ from world to world; part names do not)."""
    return ["js", f"(()=>{{const e=[...document.querySelectorAll('[data-key$=\"{suffix}\"]')].pop(); e.click(); return !!e}})()"]


def steps(frames):
    n = [0]

    def shot(k=1):
        out = []
        for _ in range(k):
            n[0] += 1
            out += ["shot", str(frames / f"screen-demo-{n[0]:03d}.png"), "wait", "850"]
        return out
    s = ["wait", "1200", "js", "document.body.style.background='#1b2321'"]
    s += shot(3)
    # a real press, where the Now line's words are painted (a scripted click does not give a text the caret)
    s += ["click", "366,47", "wait", "300", "type", "writing the widgets report", "key", "Enter", "wait", "800"] + shot(2)
    s += ["desk", "read a5530", "desk", "do prop a5530 commission=landed", "wait", "1200"] + shot(3)
    s += press("/open") + ["wait", "200", "js", "(()=>{const h=[...document.querySelectorAll('[data-key$=\"/open\"] button')].pop(); h && h.click(); return !!h})()",
                           "wait", "600"] + shot(3)
    s += press("/x") + ["wait", "1200"] + shot(2)
    s += ["desk", f"read {TIMER}", "desk", f"do prop {TIMER} focus=0.25", "wait", "800"] + shot(1)
    s += press("/acts/start") + ["wait", "300"] + shot(5)
    s += ["desk", "read a5496", "desk", "do prop a5496 commission=waiting", "wait", "600"] + shot(12)     # held: a focus runs
    s += press("/acts/rest") + ["wait", "1500"] + shot(4)                                                # the break lets it in
    return s, n


def main(argv):
    out = pathlib.Path(argv[0]) if argv else MAIN_DEMOS / "a5530-widgets.mp4"
    frames = ROOT / "screen-demo-frames"
    frames.mkdir(exist_ok=True)
    for old in frames.glob("screen-demo-*.png"):
        old.unlink()
    st, n = steps(frames)
    # the house copies the live world over frontier-try after every landing: put the widgets in first when it has none
    explore = [sys.executable, str(SCREEN.parent / "explore.py"), "frontier-try", "--as", "worker-a5530"]
    if "nothing matches" in subprocess.run(explore, input="find title:home-widgets\n", capture_output=True, text=True, encoding="utf-8").stdout:
        sys.path.insert(0, str(HERE))
        import apply
        said = subprocess.run(explore, input="\n".join(apply.lines()) + "\n", capture_output=True, text=True, encoding="utf-8").stdout
        print("applied the widgets to frontier-try:", "; ".join(l[:90] for l in said.splitlines() if l.startswith(("ERR", "~ !"))) or "all ok")
    subprocess.run([sys.executable, str(SCREEN), "frontier-try", "--as", "alex", "--lens", "home-base", "--size", "1920x1080", *st], check=True)
    from PIL import Image
    for p in sorted(frames.glob("screen-demo-*.png")):
        Image.open(p).crop((0, 0, 1720, 260)).save(p)
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-framerate", "1", "-i", str(frames / "screen-demo-%03d.png"),
                    "-vf", "fps=30,scale=1720:260,format=yuv420p", str(out)], check=True)
    print(f"{n[0]} frames -> {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
