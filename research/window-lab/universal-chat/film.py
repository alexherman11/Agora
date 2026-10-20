"""film: the universal conversation (a6638), filmed headless in a copy of a world at Alex's size (2560x1440 at 150%).
Nothing on his screen; every press is in the copy (screen.py), Pike's answer too.

    python research/window-lab/universal-chat/film.py [world] [out dir]     (world: frontier-try after apply.py lines)

The story, in the home base as Alex: a review item opens in the middle with the Conversation beside it, which says what
it is about; he highlights words in it, and the chat's own box becomes the comment: it goes to the document's author,
kept in its Talk, and the chat shows it quoted with who it went to; he asks JEFF a question, which carries the item;
Pike answers in the Talk, and the answer arrives in the same chat, tagged with what it is about.
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "writing"))
import film as base   # noqa: E402  (a5820's Reel and caption)

base.SIZE[:] = ["--size", "2560x1440", "--scale", "1.5"]
CHAT = "home/tiles/lens:home-tiling/stage/f5664/body/chatright/lens:home-viewer/viewer/mine/a5482/split/chat/lens:jeff-chat/chat/a5082/dock"
DOC = "a4934"       # The Workbench: a note, role=doc, author=pike, no Talk yet in frontier-try on 20 Oct


def main():
    world = sys.argv[1] if len(sys.argv) > 1 else "frontier-try"
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("C:/Projects/Agora4/research/window-lab/demos/a6638")
    (out / "frames").mkdir(parents=True, exist_ok=True)
    for f in (out / "frames").glob("*.png"):
        f.unlink()
    reel = base.Reel(out)
    reel.do("desk", "read a5482", "desk", "do prop a5482 viewing=a6549", "wait", "1500")
    reel.say("Something waits on you, open in the middle; the Conversation beside it says what it is about", secs=3.5)
    reel.do("desk", f"do prop a5482 viewing={DOC}", "wait", "1800")
    reel.say("Open another: a design from Pike. The chat follows: About The Workbench", secs=3.5)
    reel.do("js", "window.PHRASE = 'Builders keep real tools, and reach both the code and the things in the world'", "wait", "200")
    reel.do("js", "@" + str(HERE / "select.js"), "wait", "1500")
    reel.say("Highlight words: the chat's own box becomes the comment, and says who it goes to", secs=4)
    reel.do("click", CHAT + "/commenting/on/say")
    reel.type("Which tools? Say lenses, verbs and scripts by name.", every=6, secs=0.07)
    reel.do("key", "Enter", "wait", "2500")
    reel.say("Sent: quoted in the chat, sent to Pike, kept in the document's Talk and anchored in its margin", secs=4.5)
    reel.do("click", CHAT + "/say")
    reel.type("Is this one ready for me to say build it?", every=6, secs=0.07)
    reel.do("key", "Enter", "wait", "2500")
    reel.say("A plain line goes to JEFF, carrying what is open: about The Workbench", secs=3.8)
    reel.do("js", "@" + str(HERE / "reply.js"), "wait", "3000")
    reel.say("Pike answers in the Talk; it arrives here, tagged with what it is about", secs=4.5)
    reel.do("js", "document.getElementById('film-cap').hidden = true", "wait", "200", secs=2.5)
    reel.run(world, "home-base")

    lst = out / "frames.txt"
    lst.write_text("".join(f"file '{f.as_posix()}'\nduration {s}\n" for f, s in reel.frames)
                   + f"file '{reel.frames[-1][0].as_posix()}'\n", encoding="utf-8")
    mp4 = out / "universal-conversation.mp4"
    subprocess.run([base.FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf",
                    "scale=1920:-2,format=yuv420p", "-r", "30", str(mp4)], check=True)
    print("film:", mp4, f"({sum(s for _, s in reel.frames):.0f} s, {len(reel.frames)} frames)")


if __name__ == "__main__":
    main()
