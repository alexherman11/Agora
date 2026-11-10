# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_captures (14 Oct 2026, a5062): a control-screen capture is kept by the house, off the world, until it is sent.

    python test_captures.py

In a scratch folder (captures.ROOT moved there), asks of captures.py:
  - make keeps an envelope and its pixels under <session>/<actor>/, gives cap-<n>, and never rewrites one;
  - load_capture gives it back unchanged, a new dict each time; another person's id is NotYours, a gone one Missing;
  - sent_copy carries the image's bytes, not a path, and the hash they were kept with;
  - discard and sent remove both files at once, and an id is never given again after a discard;
  - a capture with no pixels says so: image None, no png beside it;
  - thumb gives its own person a small png data address of the pixels (a5834), and nothing to anyone else.
The scratch folder is removed at the end.
"""
import base64
import hashlib
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import captures  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:2000]}"))
    if not ok:
        fails.append(name)


def raises(kind, fn, *a):
    try:
        fn(*a)
    except kind as e:
        return str(e)
    except Exception as e:      # noqa: BLE001
        return f"wrong error {type(e).__name__}: {e}"
    return None


PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
scratch = Path(tempfile.mkdtemp(prefix="captures-test-"))
captures.ROOT = scratch
try:
    native = {"at": "2026-10-14T17:00:00-0700", "rect": [10, 20, 300, 80], "monitor": {"index": 0}, "native": "full",
              "refs": [{"world": "frontier", "item": "a5076", "subject": "s5075", "kind": None, "role": "qcard",
                        "resolved": "yes", "words": "Try a capture", "scene_count": 9890, "seen_event": "e9881", "rev": 3}], "image_size": None, "image_text": None}
    a = captures.make("frontier", "alex", native)
    d = scratch / "frontier" / "alex"
    check("make gives cap-<n> and keeps it under <session>/<actor>", a == "cap-1" and (d / "cap-1.json").exists(), list(scratch.rglob("*")))
    e = captures.load_capture("frontier", "alex", a)
    check("load gives the envelope back with its id, its person and its refs",
          e["id"] == a and e["by"] == "alex" and e["refs"][0]["item"] == "a5076" and e["image"] is None, e)
    e["refs"].clear()
    check("each load is a new dict: changing one changes nothing kept", captures.load_capture("frontier", "alex", a)["refs"], "")
    check("a capture with no pixels has no png beside it", not list(d.glob("*.png")), list(d.iterdir()))

    b = captures.make("frontier", "alex", {"rect": [0, 0, 1, 1], "native": "none", "refs": [], "image_size": [1, 1],
                                           "image_text": "words"}, PNG)
    check("pixels are kept beside it as cap-<n>.png", b == "cap-2" and (d / "cap-2.png").read_bytes() == PNG, list(d.iterdir()))
    s = captures.sent_copy("frontier", "alex", b)
    check("sent_copy carries the bytes, their hash, and no path", s["image"]["data"] == base64.b64encode(PNG).decode()
          and s["image"]["sha256"] == hashlib.sha256(PNG).hexdigest() and s["image"]["media_type"] == "image/png", s["image"])
    check("sent_copy of a capture with no pixels has image None", captures.sent_copy("frontier", "alex", a)["image"] is None, "")
    check("an envelope is never rewritten", raises(FileExistsError, captures._write_once, d / "cap-1.json", b"{}") is not None
          and captures.load_capture("frontier", "alex", a)["refs"], "")

    msg = raises(captures.NotYours, captures.load_capture, "frontier", "rowan", a)
    check("another person's capture is NotYours, and says whose", msg and "alex's" in msg and "rowan" in msg, msg)
    msg = raises(captures.NotYours, captures.preview, "frontier", "rowan", a)
    check("a preview is only for its own person", msg is not None and not msg.startswith("wrong"), msg)
    check("the preview names the item and its words", "a5076" in captures.preview("frontier", "alex", a)
          and "Try a capture" in captures.preview("frontier", "alex", a), captures.preview("frontier", "alex", a))
    check("ids lists one person's captures in order", captures.ids("frontier", "alex") == ["cap-1", "cap-2"], captures.ids("frontier", "alex"))

    forged = captures.make("frontier", "alex", {"id": "cap-99", "by": "rowan", "session": "other", "image": "../../x.png",
                                                "image_sha256": "0", "refs": []})
    fe = captures.load_capture("frontier", "alex", forged)
    check("an envelope cannot set the id, person, world or image make() gives",
          (fe["id"], fe["by"], fe["session"], fe["image"]) == (forged, "alex", "frontier", None) and "image_sha256" not in fe, fe)
    victim = scratch / "frontier" / "keep-me.png"
    victim.write_bytes(PNG)
    p = d / f"{forged}.json"
    p.write_text(p.read_text(encoding="utf-8").replace('"image": null', '"image": "../keep-me.png"'), encoding="utf-8")
    msg = raises(captures.CaptureError, captures.sent_copy, "frontier", "alex", forged)
    check("a changed envelope naming another file is refused, not read", msg and "not its own" in msg, msg)
    captures.discard("frontier", "alex", forged)
    check("nor deleted: discard removes only cap-<id>.png in its own folder", victim.exists() and not p.exists(), list(scratch.rglob("*")))
    check("the preview names no count as an event", "e9890" not in captures.preview("frontier", "alex", a)
          and "scene of 9890 events" in captures.preview("frontier", "alex", a), captures.preview("frontier", "alex", a))
    loose = captures.make("frontier", "alex", {"refs": [{"world": "frontier", "resolved": "no", "role": "qtitle", "lens": "board",
                                                         "words": "Try a capture"}]})
    pv = captures.preview("frontier", "alex", loose)
    check("a part not named exactly is previewed with no id", "not named exactly" in pv and "None" not in pv, pv)

    # a5834: the draft's chip shows the pixels small, as a data address a `picture` text paints
    import io
    from PIL import Image
    big = io.BytesIO()
    Image.new("RGB", (1600, 900), (40, 90, 200)).save(big, "PNG")
    wide = captures.make("frontier", "alex", {"rect": [0, 0, 1600, 900], "refs": [], "image_size": [1600, 900]}, big.getvalue())
    t = captures.thumb("frontier", "alex", wide)
    tw, th = Image.open(io.BytesIO(base64.b64decode(t.split(",", 1)[1]))).size if t.startswith("data:image/png;base64,") else (0, 0)
    check("thumb is a small png data address, its shape kept", (tw, th) == (320, 180), (t[:40], tw, th))
    check("thumb of a capture with no pixels is empty", captures.thumb("frontier", "alex", a) == "", "")
    check("thumb is only for its own person", captures.thumb("frontier", "rowan", wide) == "", "")
    captures.discard("frontier", "alex", wide)

    captures.discard("frontier", "alex", b)
    check("discard removes the envelope and its pixels", not (d / "cap-2.json").exists() and not (d / "cap-2.png").exists(), list(d.iterdir()))
    msg = raises(captures.Missing, captures.load_capture, "frontier", "alex", b)
    check("a discarded capture is Missing", msg and "not kept" in msg, msg)
    c = captures.make("frontier", "alex", {"rect": [0, 0, 1, 1], "refs": []})
    check("an id is never given again after a discard", c == "cap-6", c)
    captures.sent("frontier", "alex", a)
    check("sent removes it once the send is durable", raises(captures.Missing, captures.load_capture, "frontier", "alex", a) is not None, "")
    check("a bad id or name is refused plainly", raises(captures.CaptureError, captures.load_capture, "frontier", "alex", "../x") is not None
          and raises(captures.CaptureError, captures.load_capture, "../w", "alex", "cap-1") is not None, "")
    check("both errors are ValueErrors", issubclass(captures.Missing, ValueError) and issubclass(captures.NotYours, captures.CaptureError), "")
finally:
    shutil.rmtree(scratch, ignore_errors=True)

print(f"\n{'FAIL' if fails else 'ok'}: {len(fails)} failed" if fails else "\nok")
sys.exit(1 if fails else 0)
