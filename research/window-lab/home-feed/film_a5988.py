"""film_a5988: At work -> an agent's live feed (a5988), filmed headless in a copy of a world at Alex's size (2560x1440).
Nothing on his screen. Uses a5820's Reel (research/window-lab/writing/film.py).

    python research/window-lab/home-feed/film_a5988.py <worker card id> [world] [out dir]
        (world: frontier-try, after research/window-lab/writing/apply.py lines and home-feed/apply.py lines)

A copy has no house, so this starts the two things a house would be: replay.py, which plays that worker's REAL recorded
transcript (from the live house's state, read only) into a scratch folder a record at a time, and feeds.py, which
writes the copy's witnessed:feed-<card> from it while the viewer watches. Both stop when the film ends. The story: At
work lists who is at work; a press opens the worker's card in the viewer with its feed; new lines arrive with no
reload; Pause holds the tail; Follow lets it run; a filter shows only its actions, then only errors.
The keys name ids in frontier-try on 16 Oct (layout f5664, its At work panel a5672, viewer a5482)."""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "writing"))
from film import FFMPEG, Reel   # noqa: E402

NOTATION = HERE.parents[1] / "text-desk-lab" / "notation"
LIVE_STATE = pathlib.Path("C:/Projects/Agora4/research/text-desk-lab/notation/house-state/frontier")
ROW = "home/tiles/lens:home-tiling/stage/f5664/body/tiling/f5665/a5672/body/lens:home-work/work/mine/a5482/workers/{card}"
TOOLS = ("home/tiles/lens:home-tiling/stage/f5664/body/pinned/lens:home-viewer/viewer/mine/a5482/split/left/open/{card}"
         "/with/lens:home-feed/feed/a5482/heads/0/tools/")


def main():
    card = sys.argv[1] if len(sys.argv) > 1 else "a6040"
    world = sys.argv[2] if len(sys.argv) > 2 else "frontier-try"
    out = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else pathlib.Path("C:/Projects/Agora4/research/window-lab/demos/a5988")
    (out / "frames").mkdir(parents=True, exist_ok=True)
    for f in (out / "frames").glob("*.png"):
        f.unlink()
    src = LIVE_STATE / f"worker-{card}" / "transcript.jsonl"
    n = len(src.read_bytes().splitlines())
    tools = TOOLS.format(card=card)
    reel = Reel(out)
    reel.do("js", "document.body.style.background='#15171b'", "wait", "1500")
    reel.say("At work: who of the house is at work now, and on which card", secs=3)
    reel.do("click", ROW.format(card=card), "wait", "3500")
    reel.say(f"A press opens worker-{card}'s card with its feed: its words, each tool call, results, edits", secs=4.5)
    for _ in range(8):
        reel.do("wait", "1800")
        reel.say("New lines arrive as it works, with no reload (a real recorded stream, replayed)", secs=0.9)
    reel.do("click", tools + "pause", "wait", "1500")
    reel.say("Pause: the tail stands still where it was; the count above keeps going", secs=2)
    reel.do("wait", "5000")
    reel.say("Pause: the tail stands still where it was; the count above keeps going", secs=2)
    reel.do("click", tools + "go", "wait", "2500")
    reel.say("Follow: it runs on to the newest line", secs=3)
    reel.do("click", tools + "actions", "wait", "2500")
    reel.say("A filter: only its actions (tool calls, desk lines, results)", secs=3)
    reel.do("click", tools + "thoughts", "wait", "2500")
    reel.say("Only its thoughts: what it wrote, and how long it thought (hidden words are not kept)", secs=3.5)
    reel.do("click", tools + "errors", "wait", "2500")
    reel.say("Only errors: refusals and failed commands", secs=3)
    reel.do("click", tools + "all", "wait", "1500")

    replay = subprocess.Popen([sys.executable, str(HERE / "replay.py"), str(src), f"worker-{card}",
                               "--start", str(max(0, n - 400)), "--every", "0.15", "--for", "300"])
    writer = subprocess.Popen([sys.executable, str(NOTATION / "feeds.py"), f"{world}-screen-*",
                               "--from", str(NOTATION / "house-state" / "feed-replay"), "--for", "320"])
    try:
        reel.run(world, "home-base")
    finally:
        for p in (replay, writer):
            p.terminate()

    lst = out / "frames.txt"
    lst.write_text("".join(f"file '{f.as_posix()}'\nduration {s}\n" for f, s in reel.frames)
                   + f"file '{reel.frames[-1][0].as_posix()}'\n", encoding="utf-8")
    mp4 = out / "at-work-live-feed.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf",
                    "scale=1920:-2:flags=lanczos,format=yuv420p", "-r", "30", "-c:v", "libx264", "-crf", "18", str(mp4)], check=True)
    print(f"film: {mp4} ({len(reel.frames)} frames, {sum(s for _, s in reel.frames):.0f} s)")


if __name__ == "__main__":
    main()
