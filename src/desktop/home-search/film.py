"""film.py: the search at the top of the home base (a6642), filmed headless on a copy of frontier-try as alex, at his
size (2560x1440 at 150%). Nothing on Alex's screen.

    python src/desktop/home-search/film.py [out.mp4]

The story: the home base at rest, the search at the top middle of the bar; a key typed with nothing in hand starts a
search there; Enter drops the results under it, titles first, each with its kind; Down twice and the second is lit;
Enter opens it beside the chat (the viewer already shows something); a panel dragged and Music filled, the search still
where it was; Ctrl+K from anywhere brings the caret back. Frames are screen.py shots (real keys through DevTools),
joined by ffmpeg, each held for the seconds below: a slideshow of real states, not a timed recording.
Default out: src/desktop/demos/a6642/search.mp4 of the main checkout (ignored by git, outlives a worktree).
Before it, frontier-try must hold this commission's world half (apply.py try): a landing recopies frontier-try.
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NOTATION = ROOT / "src" / "text-desk" / "notation"
FFMPEG = "C:/Users/Alex/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.1-full_build/bin/ffmpeg.exe"
T = "home/tiles/lens:home-tiling/stage/f5664"


def main():
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("C:/Projects/Agora4/src/desktop/demos/a6642/search.mp4")
    frames = []

    def shot(secs):
        f = ROOT / f"screen-film-{len(frames):02d}.png"
        frames.append((f, secs))
        return ["shot", str(f)]

    steps = ["wait", "1000"] + shot(2.4)
    steps += ["blur", "key", "h"] + shot(1.2)
    steps += ["type", "ome base"] + shot(1.2)
    steps += ["key", "Enter", "wait", "1500"] + shot(2.6)
    steps += ["key", "ArrowDown", "key", "ArrowDown", "wait", "200"] + shot(1.8)
    steps += ["key", "Enter", "wait", "2000"] + shot(2.6)
    steps += ["drag", f"{T}/body/tiling/f5665/a5674/grip", "200,300", "wait", "1800"] + shot(2.0)
    steps += ["double", f"{T}/body/tiling/f5665/a5676/grip", "wait", "1800"] + shot(2.4)
    steps += ["click", "1800,600", "key", "Ctrl+k", "type", "music", "wait", "300"] + shot(2.2)
    steps += ["events", "10", "facts", f"{T}/top", "1"]
    subprocess.run([sys.executable, str(NOTATION / "screen.py"), "frontier-try", "--as", "alex", "--lens", "home-base",
                    "--size", "2560x1440", "--scale", "1.5", *steps], check=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    lst = out.with_suffix(".frames.txt")
    lst.write_text("".join(f"file '{f.as_posix()}'\nduration {s}\n" for f, s in frames) + f"file '{frames[-1][0].as_posix()}'\n", encoding="utf-8")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf",
                    "scale=1920:-2,format=yuv420p", "-r", "25", str(out)], check=True)
    for i, (f, _s) in enumerate(frames):            # the frames beside the film, to read one by one
        (out.parent / f"search-{i:02d}.png").write_bytes(f.read_bytes())
    print(f"film: {out} ({len(frames)} frames, {sum(s for _, s in frames):.1f} s)")


if __name__ == "__main__":
    main()
