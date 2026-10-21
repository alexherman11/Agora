"""Compile both music forms against event-fed stand-ins, entirely in memory."""
import sys
import atexit
import uuid
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
WL = HERE.parent
LAB = WL.parents[1] / "research" / "text-desk-lab" / "notation"
sys.path[:0] = [str(WL), str(LAB)]
import explore
import scene
import style
import witnessed
import media
import put


def walk(n):
    yield n
    for k in n.get("kids", []):
        yield from walk(k)


desk = explore.fresh()
desk._session = "music-inmemory"
root = desk.world.root


def act(line):
    result = desk.dispatch("desk", {"line": line, "whole": True})
    assert not result.get("error"), result
    assert not result.get("text", "").startswith("ERR"), result
    return result


def create(title, text, tags):
    act(f"look {root}")
    act(f"do create {root} kind=note title={title} tags={tags} style=music-test text={put.q(text)}")


skin = (LAB / "desk-shell" / "style" / "calm.style").read_text(encoding="utf-8")
skin += "\n" + (HERE / "home-music.style").read_text(encoding="utf-8")
look = style.looks(skin)
assert not look.get("refusal"), look
assert not [(r, v["unread"]) for r, v in look["roles"].items() if v["unread"]]
create("music-test", skin, "style")
for name in put.LENSES:
    create(name, (HERE / (name + ".lens")).read_text(encoding="utf-8"), "lens")

art = media.ART / ("test-" + uuid.uuid4().hex + ".png")
art.parent.mkdir(parents=True, exist_ok=True)
from PIL import Image
Image.new("RGB", (16, 16), "#1ed760").save(art)
atexit.register(art.unlink, missing_ok=True)
state = {"app": "Spotify.exe", "title": "Night Drive", "artist": "Stand-in Band", "status": "Playing",
         "position": 60, "end": 227, "art": str(art), "can": {"play": True, "pause": True}}
current = []


def feed(world, name):
    return {"rows": current, "age": 0, "by": "stand-in"} if name == "media" else None


with patch.object(witnessed, "read", feed):
    for name in ("home-music", "home-music-full"):
        for liked in ("no", "yes", "unknown"):
            for pos in (0, 60, 150, 227):
                current[:] = [media.session_row({**state, "position": pos}, (liked, "Not connected" if liked == "unknown" else ""))]
                sc, text = scene.scene_for(desk, name)
                nodes = list(walk(sc))
                assert "Night Drive" in text and "Stand-in Band" in text, text
                assert not any(n.get("live") for n in nodes), "music must never run a clock"
                fill = next(n for n in nodes if n.get("part") == "fill")
                assert (fill.get("share") == pos if pos else fill["paint"].get("absent")), fill
                if pos:
                    ink = fill["kids"][0]
                    assert "share" not in ink and look["roles"][ink["role"]]["look"]["height"] > 0, ink
                pictures = [n["paint"]["media"] for n in nodes if n.get("paint", {}).get("media")]
                assert len(pictures) == 1 and pictures[0]["mode"] == "picture", pictures
                assert pictures[0]["items"][0]["kind"] == "image", pictures
                acts = [a.get("line", "") for n in nodes for a in n.get("acts", [])]
                assert any("media.unlike" in a for a in acts) == (liked == "yes"), acts
                assert any("media.like" in a for a in acts) == (liked != "yes"), acts
                assert any("media.connect" in a for a in acts), acts
                assert not any(n.get("scroll") not in (None, "none") for n in nodes), nodes
        print(f"ok: {name}: three heart states, four playback positions, album picture, Connect; no clock or scrolling")
        current.clear()
        _, text = scene.scene_for(desk, name)
        assert "Nothing playing" in text and "Night Drive" not in text, text
        print(f"ok: {name}: calm empty state")
print("all ok: music scenes in memory; pixel rendering not checked")
