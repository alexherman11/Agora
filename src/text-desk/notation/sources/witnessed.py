"""witnessed:<name> (15 Oct, the home base, JEFF's HUD): rows any living program keeps beside the house under a name of
its own, with the fields it wrote (read them through a frame, `of witnessed:desktop as w` and $w.title), and order, age
and by. A program says what it sees without a source edit per program; `windows` is the first such source, kept by its
name. A row source of its own file (scene.SOURCE_DIR, a5296)."""
import json

USAGE = "witnessed:<name>"
FIELDS = ("order", "age", "by")
ARG = "needed"
OPEN = True          # every field the program wrote is printed after these


def rows(desk, arg, session):
    import witnessed
    doc = witnessed.read(session, arg)
    return [] if doc is None else [{**{k: v if isinstance(v, (str, int, float)) else json.dumps(v) for k, v in r.items()},
                                    "order": k, "age": doc["age"], "by": doc.get("by") or ""}
                                   for k, r in enumerate(doc["rows"], 1) if isinstance(r, dict)]
