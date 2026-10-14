"""captures: what a person took off their screen with the control-screen gesture (a5062), kept by the house beside the
world, never in it, until they send it.

Alex, e9743: 'I need to be able to control drag over my whole screen and whatever is there ... you understand it'.
Sable (a5062, c5088): an unsent capture of his email must not sit in the world, where every resident may read it, so
a capture is kept here, as painter reports are (reports.py, a4869), and only its id goes into the world, on the
person's own draft (do prop <draft note> context=<id>). On Send the chat copies it into the sent message (sent_copy);
only then is any of it in the world.

    house-state/captures/<session>/<actor>/cap-<n>.json    the envelope, written once and never rewritten
    house-state/captures/<session>/<actor>/cap-<n>.png     its pixels, when it has any
    house-state/captures/<session>/next                    the last n given, so an id is never reused after a discard

The envelope: id, by, session (given by make, never by the envelope); at; monitor {index, device, rect, scale}; rect
[x, y, w, h] in physical screen pixels; native full|mixed|none (none: no Agora page lay under it, refs is []); refs,
in screen order, each either named exactly {resolved: yes, world, item, subject, kind (None: the scene does not carry
it), role, lens, key, words (as shown under the rectangle), rev (the item's), seen_event (the latest event that changed
the item or its subject, among those its scene was built from; None if the log was not read), scene_count (how many
events that scene was built from: a count, not an event), viewer} or not {resolved: no, world, role, lens, words, why}
with no id at all, since words and roles repeat (Sable c5099); windows [{title, process, agora, share}]; image
(cap-<n>.png) or None, image_sha256, image_size [w, h] (at most 2048 a side and 2 MiB, Codex c5124), image_text (the
words Windows' own text recognition read in it) or None; timing_ms.

Written by the capture tool (research/window-lab/capture/capture.py, through make); read by whoever answers for the
person (the chat's send side, load_capture / sent_copy). Discard deletes at once; a sent capture is deleted by `sent`
once the send is durable, so a retry finds it still there.
"""
import base64
import hashlib
import json
import os
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "house-state" / "captures"
_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_@-]{0,63}$")     # deskd's SESSION_NAME; an actor is the same shape
_ID = re.compile(r"^cap-[1-9][0-9]{0,8}$")


class CaptureError(ValueError):
    """Any refusal from this module; the message is a plain sentence that can be shown as it is."""


class Missing(CaptureError):
    pass


class NotYours(CaptureError):
    pass


def _dir(session, actor=None):
    if not (session and _NAME.match(str(session))) or (actor is not None and not _NAME.match(str(actor))):
        raise CaptureError(f"not a session and person a capture can belong to: {session!r}, {actor!r}")
    d = ROOT / session
    return d / str(actor).lower() if actor is not None else d


def _file(session, actor, cid):
    if not _ID.match(str(cid)):
        raise Missing(f"{cid} is not a capture id (they read cap-<n>)")
    p = _dir(session, actor) / f"{cid}.json"
    if p.exists():
        return p
    for other in _dir(session).glob(f"*/{cid}.json"):
        raise NotYours(f"{cid} is {other.parent.name}'s, not {str(actor).lower()}'s")
    raise Missing(f"{cid} is not kept: never made, discarded, or sent")


def _write_once(p, data):
    """Create p with data, or fail if it exists: an envelope is never rewritten."""
    tmp = p.with_name(p.name + f".{os.getpid()}.tmp")
    tmp.write_bytes(data)
    try:
        os.link(tmp, p)              # refuses (FileExistsError) when p is there
    finally:
        tmp.unlink(missing_ok=True)


def _next_id(session):
    """The next cap-<n> for this session. One maker at a time (the tool is single-instance), so a plain file serves."""
    d = _dir(session)
    d.mkdir(parents=True, exist_ok=True)
    f = d / "next"
    try:
        n = int(f.read_text(encoding="utf-8").strip() or 0)
    except (OSError, ValueError):
        n = 0
    for p in d.glob("*/cap-*.json"):         # a lost counter never gives an id that is still kept
        try:
            n = max(n, int(p.stem[4:]))
        except ValueError:
            pass
    n += 1
    f.write_text(str(n), encoding="utf-8")
    return f"cap-{n}"


def make(session, actor, envelope, png=None):
    """Keep a new capture and return its id. `envelope` is everything but id, by, session and image (set here);
    `png` is the image's bytes, or None when the capture has no pixels."""
    d = _dir(session, actor)
    d.mkdir(parents=True, exist_ok=True)
    cid = _next_id(session)
    # Codex c5127: what make() gives (id, person, world, the image's name and hash) can never come from the envelope
    env = {k: v for k, v in envelope.items() if k not in ("id", "by", "session", "image", "image_sha256")}
    env.update(id=cid, by=str(actor).lower(), session=session, image=None)
    if png:
        _write_once(d / f"{cid}.png", png)
        env["image"] = f"{cid}.png"
        env["image_sha256"] = hashlib.sha256(png).hexdigest()
    _write_once(d / f"{cid}.json", json.dumps(env, ensure_ascii=False, indent=1).encode("utf-8"))
    return cid


def _image(session, actor, cid, e):
    """The path of a capture's pixels, held to cap-<id>.png in its own person's folder whatever the envelope says
    (Codex c5127): a changed envelope can never point a read or a delete anywhere else."""
    if not e.get("image"):
        return None
    if e["image"] != f"{cid}.png":
        raise CaptureError(f"{cid}'s envelope names an image that is not its own ({e['image']!r})")
    return _dir(session, actor) / f"{cid}.png"


def load_capture(session, actor, cid):
    """The envelope as it was made (a new dict each call). Missing / NotYours say why not."""
    return json.loads(_file(session, actor, cid).read_text(encoding="utf-8"))


def ids(session, actor):
    """This person's kept captures, oldest first."""
    try:
        return sorted((p.stem for p in _dir(session, actor).glob("cap-*.json")), key=lambda s: int(s[4:]))
    except CaptureError:
        return []


def preview(session, actor, cid):
    """A short text of what the capture holds, for its own person only."""
    e = load_capture(session, actor, cid)
    x, y, w, h = e.get("rect") or (0, 0, 0, 0)
    out = [f"{cid}: {w}x{h} at {x},{y} on screen {(e.get('monitor') or {}).get('index', '?')}, {e.get('at', '')}"]
    for r in e.get("refs") or []:
        words = " ".join(str(r.get("words") or "").split())
        words = words[:120] + ("..." if len(words) > 120 else "")
        if r.get("resolved") == "no":            # Sable c5099: a part not named exactly carries no id, only what it showed
            out.append(f"  not named exactly: a {r.get('role') or 'part'} in {r.get('lens')}: {words}")
            continue
        # Sable c5127: a count is not an event. The item's latest event when seen is its moment; scene_count is a count
        out.append(f"  {r.get('item')} ({r.get('subject')}, {r.get('role') or r.get('kind') or 'part'}, rev {r.get('rev')}, "
                   f"latest event {r.get('seen_event') or 'unknown'}, scene of {r.get('scene_count')} events): {words}")
    if e.get("image"):
        iw, ih = e.get("image_size") or ("?", "?")
        out.append(f"  pixels {iw}x{ih}" + (f"; words in them: {' '.join(e['image_text'].split())[:160]}" if e.get("image_text") else "; no words recognised"))
    if not e.get("refs"):
        out.append("  native=none: no Agora page lay under it")
    return "\n".join(out)


def sent_copy(session, actor, cid):
    """For Send: the envelope with its image's bytes inside it (never a path to a file that may go), a new dict each call."""
    e = load_capture(session, actor, cid)
    p = _image(session, actor, cid, e)
    if p:
        raw = p.read_bytes()
        if e.get("image_sha256") and hashlib.sha256(raw).hexdigest() != e["image_sha256"]:
            raise CaptureError(f"{cid}'s image is not the one captured")
        w, h = e.get("image_size") or (None, None)
        e["image"] = {"media_type": "image/png", "data": base64.b64encode(raw).decode("ascii"), "width": w, "height": h,
                      "sha256": hashlib.sha256(raw).hexdigest()}
    return e


def _remove(session, actor, cid):
    p = _file(session, actor, cid)
    try:
        img = _image(session, actor, cid, json.loads(p.read_text(encoding="utf-8")))
    except (ValueError, CaptureError):
        img = None
    (img or p.with_suffix(".png")).unlink(missing_ok=True)     # only ever its own cap-<id>.png
    for i in range(20):             # Windows: a reader holding the file open refuses the delete for a moment
        try:
            p.unlink()
            return
        except PermissionError:
            time.sleep(0.01 * (i + 1))
    p.unlink()


def discard(session, actor, cid):
    """The person's own Discard: gone at once, pixels and all."""
    _remove(session, actor, cid)


def sent(session, actor, cid):
    """The send side, once the sent message holds its copy durably: the kept capture is no longer needed."""
    _remove(session, actor, cid)
