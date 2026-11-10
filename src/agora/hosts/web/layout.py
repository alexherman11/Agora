"""Personal tiling, expressed as ordinary dictionary words and private facts.

The tree belongs to a person, never to the lenses or the groups it displays.
No browser storage or second write route: words use the kernel transaction/fence.
"""
import copy

from kernel.kernel import Refused


HELP = {
    "panes": "panes: read your web layout (Feed, Council and Help by default).",
    "pane.split": "pane.split <pane name> lens=<lens name> [axis=row|column]: split a pane, opening another view. Names may be quoted.",
    "pane.close": "pane.close <pane name>: close your pane. The last pane stays open; the things inside are untouched.",
    "pane.move": "pane.move <pane name> to=<pane name>: swap two panes, also by dragging one pane header onto another.",
    "pane.focus": "pane.focus <pane name>: focus your pane; on a phone show it alone. Swipe the pane strip or use the switcher too.",
    "pane.resize": "pane.resize <pane name> ratio=<10..90> [at=root|<binary path>]: size its containing split, or the named split from the root; or drag its divider.",
}


def defaults():
    return {"tree": {"axis": "row", "ratio": 55, "kids": [
        {"id": "p1", "lens": "feed", "name": "Feed"}, {"axis": "column", "ratio": 60, "kids": [
            {"id": "p2", "lens": "council", "name": "Council"}, {"id": "p3", "lens": "help", "name": "Help"}]}]},
        "active": "p1", "next": 4}


def leaves(tree):
    if "id" in tree:
        return [tree]
    return [p for kid in tree["kids"] for p in leaves(kid)]


def personal(k, person, tx=None):
    candidates = list(k.state.things) + (tx.made if tx else [])
    get = tx.get if tx else k.state.get
    for t in candidates:
        if get(t, "kind") == "web-layout" and get(t, "owner") == person and not get(t, "forgotten"):
            return t, copy.deepcopy(get(t, "layout"))
    return None, defaults()


def panes(k, actor, st, entry, tx, group, saw=None):
    t, layout = personal(k, actor.person)
    if t:
        k.mark(actor, t, k.shown(actor.person, t))
    return {"text": "Your panes: " + ", ".join(p.get("name", p["lens"].title()) for p in leaves(layout["tree"])),
            "rows": [{"id": t, "rev": k.state.rev.get(t, 0), "layout": layout}]}


def arrange(k, actor, st, entry, tx, group, saw=None):
    if k.state.get(actor.person, "kind") != "person":
        raise Refused("A web layout belongs to a person; act for your person first.")
    t, layout = personal(k, actor.person, tx)
    if t and t not in tx.made:
        k.fence(actor, t, ["layout"], saw)
    nodes = leaves(layout["tree"])

    def select(name):
        found = [p for p in nodes if p["id"] == name or p.get("name", p["lens"]).casefold() == name.casefold()]
        if len(found) != 1:
            raise Refused("Name one of your panes; panes lists their names, including numbered copies.")
        return found[0]

    pane = select(st.words.strip())
    word = entry["bound"]
    if word == "pane.split":
        lens = st.kv.get("lens", "")
        axis = st.kv.get("axis", "row")
        if axis not in ("row", "column"):
            raise Refused("axis says row or column")
        if len(nodes) >= 12:
            raise Refused("Twelve panes are open; close one first.")
        visible = [k.shown(actor.person, x) for x in k.things("lens")]
        matches = [a for a in visible if a and a.get("name", "").casefold() == lens.casefold()]
        if len(matches) != 1:
            raise Refused("Choose a lens you may see; rows lens lists them.")
        lens = matches[0]["name"]
        old = dict(pane)
        label, number = lens.title(), 1
        names = {p.get("name", p["lens"].title()).casefold() for p in nodes}
        while label.casefold() in names:
            number += 1
            label = f"{lens.title()} {number}"
        new = {"id": f"p{layout['next']}", "lens": lens, "name": label}
        layout["next"] += 1
        pane.clear()
        pane.update(axis=axis, ratio=50, kids=[old, new])
        layout["active"] = new["id"]
    elif word == "pane.close":
        if len(nodes) == 1:
            raise Refused("Keep one pane open; split it to open another view.")

        def remove(node):
            if "id" in node:
                return None if node["id"] == pane["id"] else node
            kids = [n for child in node["kids"] if (n := remove(child)) is not None]
            return kids[0] if len(kids) == 1 else dict(node, kids=kids)
        layout["tree"] = remove(layout["tree"])
        if layout["active"] == pane["id"]:
            layout["active"] = leaves(layout["tree"])[0]["id"]
    elif word == "pane.move":
        other = select(st.kv.get("to", ""))
        a, b = dict(pane), dict(other)
        pane.update(b)
        other.update(a)
    elif word == "pane.focus":
        layout["active"] = pane["id"]
    elif word == "pane.resize":
        try:
            ratio = int(st.kv.get("ratio", ""))
        except ValueError:
            raise Refused("ratio says a percentage from 10 to 90") from None
        if not 10 <= ratio <= 90:
            raise Refused("ratio says a percentage from 10 to 90")

        def resize(node):
            if "id" in node:
                return False
            if any(child is pane for child in node["kids"]):
                node["ratio"] = ratio
                return True
            return any(resize(child) for child in node["kids"])
        path = st.kv.get("at")
        if path is not None:
            node = layout["tree"]
            for part in ("" if path == "root" else path):
                if part not in "01" or "kids" not in node:
                    raise Refused("That split is gone; read panes again.")
                node = node["kids"][int(part)]
            if "kids" not in node:
                raise Refused("That is a pane, not a split.")
            node["ratio"] = ratio
        elif not resize(layout["tree"]):
            raise Refused("Split this pane before resizing it.")
    if t is None:
        t = tx.mint()
        for key, value in {"kind": "web-layout", "owner": actor.person, "made_by": actor.id,
                           "sees": f"person:{actor.person}", f"in:{k.place}": len(k.log.records) + 1}.items():
            tx.set(t, key, value)
    # A happening must name the private layout even when this act did not mint it.
    tx.parts[-1]["target"] = t
    tx.set(t, "layout", layout)
    return {"text": "Your panes arranged [r?]", "rows": [{"id": t, "layout": layout}]}
