"""film (a6010): acting on a card from the board, filmed headless in a copy. Nothing on Alex's screen.

    python src/desktop/board-lab/film.py [out.mp4] [--lens direction-board-inbox] [--size 680x1340]

The story, as Alex: a test card waits on him (made in the copy, tagged ready-for-review); he opens it in place, writes
a reply to JEFF, and presses Looks good; it leaves Needs you. A drawn pointer shows where each press lands (headless
Chrome has none). Each frame is a screen.py shot; ffmpeg holds each for its own time (the holds are the story's pace,
not measured times; the times measured are printed by probe.js beside the presses). Writes <out>.mp4 and keeps the
frames beside it. The copy is screen.py's own and goes when it ends.
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
LAB = HERE.parents[1] / "text-desk" / "notation"
FFMPEG = ("C:/Users/Alex/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/"
          "ffmpeg-8.1.1-full_build/bin/ffmpeg.exe")
TITLE = "Test card: the new board, try it"
FIND = ("(() => { const e = [...document.querySelectorAll('[data-key]')].find(e => /\\/reviews\\/a\\d+$/.test(e.dataset.key)"
        " && e.textContent.includes('Test card')); if (!e) return 'no test card';"
        " e.querySelector(':scope > [data-key$=\"/line\"]').id = 'testline';"
        " e.querySelector('[data-key$=\"/line/ok\"]').id = 'testok'; return e.dataset.key; })()")
POINTER = ("(() => { let p = document.getElementById('fake-pointer'); if (!p) { p = document.createElement('div');"
           " p.id = 'fake-pointer'; p.style.cssText = 'position:fixed;z-index:99;width:18px;height:18px;border-radius:50%;"
           "border:2px solid #fff;background:#ffffff55;pointer-events:none;transform:translate(-50%,-50%)';"
           " document.body.append(p); } const t = document.querySelector('%s'); if (!t) return 'none';"
           " const r = t.getBoundingClientRect(); p.style.left = (r.left + %s) + 'px'; p.style.top = (r.top + r.height / 2) + 'px';"
           " return 'at ' + Math.round(r.left) + ',' + Math.round(r.top); })()")


def point(sel, dx="r.width / 2"):
    return ["js", POINTER.replace("'%s')", f"'{sel}')").replace("%s)", f"{dx})")]


def main():
    a = sys.argv[1:]
    out = pathlib.Path(next((x for x in a if x.endswith(".mp4")), "C:/Projects/Agora4/src/desktop/demos/a6010/board-approve.mp4"))
    lens = a[a.index("--lens") + 1] if "--lens" in a else "direction-board-inbox"
    size = a[a.index("--size") + 1] if "--size" in a else "680x1340"
    frames = out.with_suffix("")
    frames.mkdir(parents=True, exist_ok=True)
    plan, n = [], [0]

    def shot(hold):
        n[0] += 1
        f = frames / f"f{n[0]:03d}.png"
        plan.append((f, hold))
        return ["shot", str(f)]

    steps = ["js", "document.body.style.background='#0E1211'", "desk", "look f5189",
             "desk", f'do create f5189 kind=note title="{TITLE}" tags=ready-for-review text="A card made for the film, in a copy: open it, answer, approve."',
             "wait", "1500", "js", FIND, "js", "window.scrollTo(0, 0)"]
    steps += shot(1.6)
    steps += point("#testline", "60") + shot(0.8)
    steps += ["click", "#testline", "wait", "120"] + shot(1.4)                  # opened in place (local, no round trip)
    if "--reply" in a:      # rounds 1 and 2: a reply typed in the card (round 3 moved words to the middle, a6049)
        steps += ["js", "(() => { const t = document.getElementById('testline').parentElement.querySelector('[data-key$=\"/body/say\"]');"
                        " if (t) t.id = 'testsay'; return !!t; })()"]
        steps += point("#testsay", "40") + ["click", "#testsay", "type", "Nice. One thing: make the reply box smaller next round."] + shot(1.6)
        steps += ["key", "Enter", "wait", "600"] + shot(1.2)
    steps += ["js", FIND] + point("#testok") + shot(0.8)
    # round 3: the card is gone on the next frame (leaves/away), before the desk answers; then the answer is painted
    steps += ["click", "#testok"] + shot(0.6) + ["wait", "250"] + shot(0.5) + ["wait", "600"] + shot(2.0)
    steps += ["desk", f"find title:Test"]
    cmd = [sys.executable, str(LAB / "screen.py"), "frontier-try", "--as", "alex", "--lens", lens, "--size", size,
           "--scale", "1.5", "--logged"] + steps
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print((r.stdout + r.stderr)[-3000:])
    have = [(f, h) for f, h in plan if f.exists()]
    lst = frames / "frames.txt"
    lst.write_text("".join(f"file '{f.as_posix()}'\nduration {h}\n" for f, h in have) + f"file '{have[-1][0].as_posix()}'\n", encoding="utf-8")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf",
                    "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p", "-r", "30", str(out)], check=True)
    print(f"film: {out} ({len(have)} frames)")


if __name__ == "__main__":
    main()
