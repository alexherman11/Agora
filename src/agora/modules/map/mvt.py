"""EDITING A MODULE (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
A module is a seam to something outside the kernel (a model provider, git, Twitch, the media session, a map server) and
turns it into world facts and words. What the world does with them (who is told, when, in what words, how it looks)
belongs in rules, lenses and this module's settings thing, read at each use. Names (JEFF, Alex), ids (dk...), models,
counts, timeouts and message text in this file are debt: move them to settings when you touch them, and never add more.

A small Mapbox Vector Tile (MVT 2.1) reader: protobuf by hand, no packages.

decode(data, layers=None) -> {layer name: (extent, [Feature])}. A Feature is (type, props, geometry) where type is
1 point, 2 line, 3 polygon, and geometry is in tile units (y grows downward):
  point   -> [(x, y), ...]
  line    -> [[x0, y0, x1, y1, ...], ...]              one flat list per part
  polygon -> [[outer, hole, hole], [outer], ...]       rings as flat lists, closed implicitly (no repeated first point)
"""


def _varint(buf, i):
    shift = result = 0
    while True:
        b = buf[i]
        i += 1
        result |= (b & 0x7F) << shift
        if b < 0x80:
            return result, i
        shift += 7


def _fields(buf, start=0, end=None):
    """(field number, wire type, value or (start, end) for length-delimited) for each field of a message."""
    i, end = start, len(buf) if end is None else end
    while i < end:
        key, i = _varint(buf, i)
        field, wire = key >> 3, key & 7
        if wire == 0:
            v, i = _varint(buf, i)
            yield field, wire, v
        elif wire == 2:
            n, i = _varint(buf, i)
            yield field, wire, (i, i + n)
            i += n
        elif wire == 5:
            yield field, wire, buf[i:i + 4]
            i += 4
        elif wire == 1:
            yield field, wire, buf[i:i + 8]
            i += 8
        else:
            raise ValueError("unknown protobuf wire type %d" % wire)


def _packed(buf, s, e):
    out = []
    i = s
    while i < e:
        shift = result = 0
        while True:
            b = buf[i]
            i += 1
            result |= (b & 0x7F) << shift
            if b < 0x80:
                break
            shift += 7
        out.append(result)
    return out


def _value(buf, s, e):
    import struct
    for field, wire, v in _fields(buf, s, e):
        if field == 1:
            return bytes(buf[v[0]:v[1]]).decode("utf-8", "replace")
        if field == 2:
            return struct.unpack("<f", v)[0]
        if field == 3:
            return struct.unpack("<d", v)[0]
        if field == 4:
            return v - (1 << 64) if v >= 1 << 63 else v
        if field == 5:
            return v
        if field == 6:
            return (v >> 1) ^ -(v & 1)
        if field == 7:
            return bool(v)
    return None


def _geometry(cmds, gtype):
    x = y = 0
    parts, cur = [], None
    i, n = 0, len(cmds)
    while i < n:
        c = cmds[i]
        i += 1
        cid, count = c & 7, c >> 3
        if cid == 1 or cid == 2:
            if cid == 1:
                cur = []
                parts.append(cur)
            for _ in range(count):
                dx, dy = cmds[i], cmds[i + 1]
                i += 2
                x += (dx >> 1) ^ -(dx & 1)
                y += (dy >> 1) ^ -(dy & 1)
                cur.append(x)
                cur.append(y)
        elif cid == 7:
            pass
        else:
            break
    if gtype == 1:
        return [(p[k], p[k + 1]) for p in parts for k in range(0, len(p), 2)]
    if gtype == 2:
        return [p for p in parts if len(p) >= 4]
    polys = []
    for ring in parts:
        if len(ring) < 6:
            continue
        a = 0
        for k in range(0, len(ring), 2):
            j = (k + 2) % len(ring)
            a += ring[k] * ring[j + 1] - ring[j] * ring[k + 1]
        if a > 0 or not polys:          # positive area (y down) is an outer ring
            polys.append([ring])
        else:
            polys[-1].append(ring)
    return polys


def decode(data, layers=None):
    buf = memoryview(data)
    out = {}
    for field, wire, v in _fields(buf):
        if field != 3 or wire != 2:
            continue
        name, extent, keys, values, feats = None, 4096, [], [], []
        for f2, w2, v2 in _fields(buf, *v):
            if f2 == 1:
                name = bytes(buf[v2[0]:v2[1]]).decode("utf-8", "replace")
                if layers is not None and name not in layers:
                    break
            elif f2 == 5:
                extent = v2
            elif f2 == 3:
                keys.append(bytes(buf[v2[0]:v2[1]]).decode("utf-8", "replace"))
            elif f2 == 4:
                values.append(v2)
            elif f2 == 2:
                feats.append(v2)
        if name is None or (layers is not None and name not in layers):
            continue
        vals = [_value(buf, s, e) for s, e in values]
        features = []
        for s, e in feats:
            tags, gtype, geom, fid = [], 0, [], None
            for f3, w3, v3 in _fields(buf, s, e):
                if f3 == 2:
                    tags = _packed(buf, *v3)
                elif f3 == 3:
                    gtype = v3
                elif f3 == 4:
                    geom = _packed(buf, *v3)
                elif f3 == 1:
                    fid = v3
            props = {}
            for k in range(0, len(tags) - 1, 2):
                if tags[k] < len(keys) and tags[k + 1] < len(vals):
                    props[keys[tags[k]]] = vals[tags[k + 1]]
            if fid is not None:
                props.setdefault("$id", fid)
            if gtype in (1, 2, 3):
                g = _geometry(geom, gtype)
                if g:
                    features.append((gtype, props, g))
        out[name] = (extent, features)
    return out
