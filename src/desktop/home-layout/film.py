"""film.py: the working tiling (a5994), filmed headless on a copy of frontier-try as alex. Nothing on Alex's screen.

    python src/desktop/home-layout/film.py [out.mp4]

The story: the home base at rest with the board in the middle; the board is picked up by its title and carried left,
the landing box showing the empty space under Music; let go, it takes that room and the emptied column goes; a
double-click on Music's title fills the room (the rest a rail, the chat kept); a double-click gives it back; the page
is reloaded and the layout is still there. Frames are screen.py shots (a real pointer and double-click through
DevTools), joined by ffmpeg, each held for the seconds below: a slideshow of real states, not a timed recording.
Default out: src/desktop/demos/a5994/tiling.mp4 of the main checkout (ignored by git, outlives a worktree).
Before it, frontier-try must hold this commission's world lines (put.py try style-a5994.desk drop-panel.verb
home-panels.lens home-tiling.lens): a landing recopies frontier-try and wipes them.
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NOTATION = ROOT / "src" / "text-desk" / "notation"
FFMPEG = "C:/Users/Alex/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.1-full_build/bin/ffmpeg.exe"
T = "home/tiles/lens:home-tiling/stage/f5664/body"
# every element that scrolls and has more than its box: none, if nothing scrolls anywhere (a5496's check)
NOSCROLL = ("[...document.querySelectorAll('*')].filter(e => { const s = getComputedStyle(e); return /(auto|scroll)/.test(s.overflow + s.overflowY + s.overflowX)"
            " && (e.scrollHeight > e.clientHeight + 1 || e.scrollWidth > e.clientWidth + 1); }).map(e => e.dataset.key || e.tagName)")


def main():
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("C:/Projects/Agora4/src/desktop/demos/a5994/tiling.mp4")
    frames = []

    def shot(secs):
        f = ROOT / f"screen-film-{len(frames):02d}.png"
        frames.append((f, secs))
        return ["shot", str(f)]

    steps = ["js", "document.body.style.background='#223'", "desk", "look a5674", "desk", "do prop a5674 shelf=no", "wait", "900"]
    steps += shot(2.0)
    # Alex's layout on 16 Oct evening: left column Waiting on you and At work, middle the board (shelved, brought
    # out above) and Music; a document open beside the chat makes the panels' room narrow
    steps += ["hold", f"{T}/tiling/f5666/a5674/grip", "560,500"] + shot(0.6)
    steps += ["hold", "-", "380,800"] + shot(0.6)
    steps += ["hold", "-", "190,1030"] + shot(1.8)
    steps += ["release", "wait", "800"] + shot(2.2)
    steps += ["double", f"{T}/tiling/f5666/a5676/grip/title", "wait", "900"] + shot(2.4)
    steps += ["double", f"{T}/filled/room/a5676/grip/title", "wait", "900"] + shot(1.8)
    steps += ["js", "location.reload()", "wait", "3500", "js", "document.body.style.background='#223'", "wait", "500"] + shot(2.2)
    steps += ["events", "6", "facts", T, "2", "js", NOSCROLL]
    subprocess.run([sys.executable, str(NOTATION / "screen.py"), "frontier-try", "--as", "alex", "--lens", "home-base",
                    "--size", "2560x1440", *steps], check=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    lst = out.with_suffix(".frames.txt")
    lst.write_text("".join(f"file '{f.as_posix()}'\nduration {s}\n" for f, s in frames) + f"file '{frames[-1][0].as_posix()}'\n", encoding="utf-8")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf",
                    "scale=1920:-2,format=yuv420p", "-r", "25", str(out)], check=True)
    print(f"film: {out} ({len(frames)} frames, {sum(s for _, s in frames):.1f} s)")


if __name__ == "__main__":
    main()
