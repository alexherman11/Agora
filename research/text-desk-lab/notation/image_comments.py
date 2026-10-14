"""An image comment carries only a user-selected, immutable PNG crop.

No screen capture or image browsing capability is exposed to residents. The
attachment travels with the ordinary comment and its existing addressed delivery.
"""

import base64
import binascii
import hashlib
import math
import re
import struct

PREFIX = "data:image/png;base64,"
MAX_BYTES = 2 * 1024 * 1024


def regions(subject):
    """Presentation data only: retain the source association without exposing the crop twice."""
    digest = hashlib.sha256(subject.get("text", "").encode()).hexdigest()
    return [{"id": c["id"], "by": c["by"], "rect": c["image"]["rect"],
             "current": c["image"].get("source_hash") == digest}
            for c in subject.get("comments", []) if c.get("image") and not c.get("resolved")]


def validate(value, source, text):
    from world import Refusal

    def refuse():
        raise Refusal(
            "image comment needs a PNG crop, valid region, and the unchanged source image"
        )

    if not isinstance(value, dict) or value.get("source") != source:
        refuse()
    if value.get("source_hash") != hashlib.sha256(text.encode()).hexdigest():
        raise Refusal(
            "the image changed while this comment was being composed; select the region again"
        )
    rect = value.get("rect")
    if (
        not isinstance(rect, list)
        or len(rect) != 4
        or any(
            isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x)
            for x in rect
        )
    ):
        refuse()
    x, y, width, height = rect
    if min(x, y) < 0 or min(width, height) <= 0 or x + width > 1.000001 or y + height > 1.000001:
        refuse()
    data = value.get("data_url", "")
    if (
        not isinstance(data, str)
        or not data.startswith(PREFIX)
        or len(data) > MAX_BYTES * 4 // 3 + 100
    ):
        refuse()
    try:
        raw = base64.b64decode(data[len(PREFIX) :], validate=True)
        if len(raw) > MAX_BYTES or raw[:8] != b"\x89PNG\r\n\x1a\n":
            refuse()
        pos, dimensions, ended = 8, None, False
        while pos < len(raw):
            size = struct.unpack_from(">I", raw, pos)[0]
            kind, payload = raw[pos + 4 : pos + 8], raw[pos + 8 : pos + 8 + size]
            crc = struct.unpack_from(">I", raw, pos + 8 + size)[0]
            if binascii.crc32(kind + payload) & 0xFFFFFFFF != crc:
                refuse()
            if pos == 8:
                if kind != b"IHDR" or size != 13:
                    refuse()
                dimensions = struct.unpack_from(">II", payload)
            pos += size + 12
            if kind == b"IEND":
                ended = pos == len(raw)
                break
        if not ended or not dimensions or any(not 1 <= d <= 2048 for d in dimensions):
            refuse()
        if list(dimensions) != [value.get("width"), value.get("height")]:
            refuse()
    except (ValueError, binascii.Error, struct.error):
        refuse()
    return {
        "source": source,
        "source_hash": value["source_hash"],
        "rect": rect[:],
        "width": dimensions[0],
        "height": dimensions[1],
        "data_url": data,
    }


def command_target(line):
    """Only a single literal new comment accepts an HTTP attachment sidecar."""
    import shlex

    from world import Refusal

    try:
        tokens = shlex.split(line)
    except ValueError:
        tokens = []
    if (
        len(tokens) != 4
        or tokens[:2] != ["do", "comment"]
        or not re.fullmatch(r"[as]\d+", tokens[2])
        or not tokens[3].startswith("line=")
    ):
        raise Refusal('image context belongs to one new comment: do comment <id> line="..."')
    return tokens[2]


def describe(image):
    region = ", ".join(f"{v:.3f}" for v in image["rect"])
    return (
        f"image selection from {image['source']}; region x,y,w,h=[{region}]; "
        f"saved crop {image['width']}x{image['height']}; source SHA256 {image['source_hash']}"
    )


def content(world, refs):
    """Resolve only comments already delivered by the house's normal routing."""
    out = []
    for cid in dict.fromkeys(refs):
        _, comment = world.find_comment(cid)
        image = (comment or {}).get("image")
        if not image:
            out.append(
                {
                    "type": "text",
                    "text": f"{cid}: the selected image attachment is no longer available.",
                }
            )
            continue
        out.extend(
            [
                {
                    "type": "text",
                    "text": f"{cid}: {describe(image)}. This is the selected region only.",
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image["data_url"][len(PREFIX) :],
                    },
                },
            ]
        )
    return out
