"""windows (a5052, 14 Oct): the windows a host keeps on the screen (src/desktop/wm.py), as it last said them, in
its order: witnessed beside the house (witnessed.py), never in the world. name is the host's own for the window (a repeat
keys each by it), kind agora or adopted, pinned/collapsed/focused yes or no, age the seconds since it said so.
A row source of its own file (scene.SOURCE_DIR, a5296)."""
USAGE = "windows"
FIELDS = ("name", "title", "lens", "kind", "pinned", "collapsed", "focused", "order", "age", "by")
ARG = "none"


def rows(desk, arg, session):
    import witnessed
    doc = witnessed.read(session, "windows")
    return [] if doc is None else [{**{f: "" for f in FIELDS}, **{k: v for k, v in r.items() if k in FIELDS},
                                    "order": k, "age": doc["age"], "by": doc.get("by") or ""}
                                   for k, r in enumerate(doc["rows"], 1) if isinstance(r, dict) and r.get("name")]
