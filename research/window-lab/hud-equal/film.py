"""film.py: equal footing (a5994's final pass), filmed headless on a copy of frontier-try as alex at his size
(2560x1440 at 150%). Nothing on Alex's screen.

    python research/window-lab/hud-equal/film.py [out.mp4]

The story, from his own layout of today (The board filled): the board fills the room, the Viewer and the pinned Chat
stand beside it, the rest a rail; a double-click gives the room back, every panel with the same header (◆ pin, ⇔, –);
the viewer's × puts the Viewer away and the chat takes the room; Board on the dock brings it back; the Chat dragged by
its title to the far left; Music double-clicked fills the room with the pinned chat kept; a dock icon dragged along
the dock; the timer dragged to the bar's right end; a reload, and it is all still there. Frames are screen.py shots,
joined by ffmpeg, each held for the seconds below: a slideshow of real states, not a timed recording.
Before it, frontier-try must hold this pass (apply.py try): a landing recopies frontier-try.
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NOTATION = ROOT / "research" / "text-desk-lab" / "notation"
FFMPEG = "C:/Users/Alex/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.1-full_build/bin/ffmpeg.exe"
B = "home/tiles/lens:home-tiling/stage/f5664/body"


def main():
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("C:/Projects/Agora4/research/window-lab/demos/a5994/equal.mp4")
    frames = []

    def shot(secs):
        f = ROOT / f"screen-film-{len(frames):02d}.png"
        frames.append((f, secs))
        return ["shot", str(f)]

    # the copy's layout: the board filled (as Alex left his), Viewer and Chat in columns of their own (apply.py try)
    steps = ["desk", "look f5664", "desk", "do prop f5664 full=a5674", "wait", "1500"] + shot(2.6)
    steps += ["double", f"{B}/filled/room/a5674/grip/title", "wait", "1500"] + shot(2.6)
    # keys as they stand in this worktree's frontier-try after apply.py try (columns f6735 Viewer, f6738 Chat)
    steps += ["click", f"{B}/tiling/f6735/a6737/body/lens:home-viewer/viewer/mine/a5482/split/left/open/f4358/head/close", "wait", "1500"] + shot(2.2)
    steps += ["click", "home/dock/lens:home-dock/foot/dock/f5565/a5482/apps/a5569/view", "wait", "1800"] + shot(2.2)
    steps += ["drag", f"{B}/tiling/f6738/a6740/grip/title", "60,300", "wait", "1800"] + shot(2.4)
    steps += ["double", f"{B}/tiling/f5665/a5676/grip/title", "wait", "1800"] + shot(2.8)
    steps += ["js", "@" + str(HERE / "reload.js"), "wait", "3500"] + shot(2.4)
    steps += ["events", "14"]
    subprocess.run([sys.executable, str(NOTATION / "screen.py"), "frontier-try", "--as", "alex", "--lens", "home-base",
                    "--size", "2560x1440", "--scale", "1.5", *steps], check=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    lst = out.with_suffix(".frames.txt")
    lst.write_text("".join(f"file '{f.as_posix()}'\nduration {s}\n" for f, s in frames) + f"file '{frames[-1][0].as_posix()}'\n", encoding="utf-8")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf",
                    "scale=1920:-2,format=yuv420p", "-r", "25", str(out)], check=True)
    for i, (f, _s) in enumerate(frames):
        (out.parent / f"equal-{i:02d}.png").write_bytes(f.read_bytes())
    print(f"film: {out} ({len(frames)} frames, {sum(s for _, s in frames):.1f} s)")


if __name__ == "__main__":
    main()
