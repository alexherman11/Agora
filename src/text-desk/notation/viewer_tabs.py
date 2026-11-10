"""Current-desk Agora navigation; no web, disk, host or chat access.

The versioned snapshot is authoritative. Tab notes and legacy viewer fields are
projections for ordinary lenses. World props confer no new reading permission.
"""
import hashlib
import json
from urllib.parse import parse_qs, urlencode, urlsplit

import names
from tab_history import Browser, NavigationError, Target, need
from world import Refusal


def props(w, item):
    n = w.nodes[item]
    return (w.subjects[n["subject"]] if n.get("subject") else n).get("props", {})


def resolve(w, address, world="current", lens=""):
    """Return canonical target, appearance, lens, title, using ONLY this world."""
    if "://" not in address:
        # IDs/unique names are the same read-only targets the existing viewer uses.
        item, _, n = names.thing_of(w, address)
        if n is None:
            matches = [(i, n) for i, n in w.nodes.items()
                       if (w.subjects[n["subject"]]["title"] if n.get("subject") else n.get("title")) == address]
            need(len(matches) == 1, "That Agora item is unavailable or ambiguous")
            item, n = matches[0]
        address = f"agora://{world}/item/{item}"
        if lens:
            address += "?" + urlencode({"lens": lens})
    target = Target.parse(address)
    need(target.kind == "agora", "Web and device tabs are unavailable; use an intentional external-open action")
    u = urlsplit(target.address)
    need(u.netloc in ("current", world), "Other-world tabs are unavailable")
    need(not u.fragment, "Agora section links are not supported yet")
    category, key = u.path.strip("/").split("/")
    using = parse_qs(u.query).get("lens", [""])[0]
    if category == "lens":
        matches = [(i, n) for i, n in w.nodes.items() if n.get("subject")
                   and w.subjects[n["subject"]]["title"] == key
                   and "lens" in w.subjects[n["subject"]].get("tags", [])]
        need(len(matches) == 1, "That lens is unavailable or ambiguous")
        item, n = matches[0]
    else:
        item, _, n = names.thing_of(w, key)
        need(n is not None, "That Agora item is unavailable")
    if using:
        need(any(s["title"] == using and "lens" in s.get("tags", []) for s in w.subjects.values()),
             "That lens is unavailable")
    title = w.subjects[n["subject"]]["title"] if n.get("subject") else n["title"]
    # Current-desk references remain stable in a private test fork and through
    # both primitive and composed command paths. No other world is ever loaded.
    canonical = f"agora://current/item/{item}" + ("?" + urlencode({"lens": using}) if using else "")
    return Target.parse(canonical), item, using, title[:512]


def run(w, viewer, args, world="current"):
    """Validate before writing; every written projection uses normal undoable events."""
    import moo
    a = dict(args)
    action = a.pop("action", "open")
    try:
        need(not set(a) - {"target", "tab", "lens", "scroll", "zoom"}, "Unknown browse argument")
        p = props(w, viewer)
        need(p.get("role") == "home-view", "Browse needs a home-view record")
        need(p.get("actor") == w.me, "Use your own viewer")
        need(action in ("init", "open", "new", "select", "close", "back", "forward", "reload", "position", "lens"),
             "Unknown browse action")
        b = Browser.restore(json.loads(p["tabs_state"])) if p.get("tabs_state") else Browser()
        # Re-authorize every restored entry as current-world Agora, never trust a
        # forged snapshot to turn this controller into a generic URL renderer.
        for t in b.tabs.values():
            for e in t.entries:
                need(e.target.kind == "agora" and urlsplit(e.target.address).netloc in ("current", world),
                     "Saved tab is not a current-world Agora page")
        if not p.get("tabs_state"):
            key = b.new_tab()
            old = p.get("viewing", "")
            if old and old != "a5080":   # old viewer's deliberate empty sentinel
                target, _, _, title = resolve(w, old, world, p.get("with", ""))
                b.commit(key, b.begin(key, target.address), title)
        if not b.tabs:
            b.new_tab()
        key = a.get("tab") or b.active
        need(key in b.tabs, "Tab is closed")
        if action == "new":
            need(len(b.tabs) < 100, "Close a tab before opening another")
            key = b.new_tab()
        elif action == "select":
            b.select(key)
        elif action == "close":
            b.close(key)
            if not b.tabs:
                b.new_tab()
        elif action in ("back", "forward"):
            b.move(key, -1 if action == "back" else 1)
            b.select(key)
        elif action == "position":
            b.position(key, int(a.get("scroll", 0)), float(a.get("zoom", 1)))
        if action in ("open", "new", "lens", "reload"):
            t = b.tabs[key]
            current = t.entries[t.index] if t.index >= 0 else None
            address = a.get("target", "")
            if action in ("lens", "reload"):
                need(current is not None, "No page to reload or change lens")
                _, item, using, _ = resolve(w, current.target.address, world)
                address = item
                using = a.get("lens", "") if action == "lens" else using
            else:
                using = a.get("lens", "")
            if address:
                target, _, _, title = resolve(w, address, world, using)
                mode = "reload" if action == "reload" else "push"
                if mode == "reload" or current is None or target != current.target:
                    need(mode != "push" or t.index < 999, "This tab's history is full; open a new tab")
                    b.commit(key, b.begin(key, target.address, mode), title)
                b.select(key)
            else:
                need(action == "new", "Choose an Agora page")
        t = b.tabs[b.active]
        entry = t.entries[t.index] if t.index >= 0 else None
        item, using, title, address = "", "", "New tab", ""
        if entry:
            target, item, using, title = resolve(w, entry.target.address, world)
            entry.title = title
            address = target.address
        previous = ""
        if t.index > 0:
            # Deleted previous pages remain named in history; traversal refuses
            # without dropping the current page or rewriting that history.
            try:
                previous = resolve(w, t.entries[t.index - 1].target.address, world)[1]
            except (Refusal, NavigationError):
                pass
        snapshot = json.dumps(b.snapshot(), ensure_ascii=False, separators=(",", ":"))
        need(len(snapshot) <= 1024 * 1024, "Tab history is full")
        desired = {"tabs_state": snapshot, "viewing": item, "with": using, "back": previous,
                   "active_tab": b.active, "tab_count": str(len(b.tabs)), "location": address,
                   "page_name": title, "can_back": "yes" if t.index > 0 else "no",
                   "can_forward": "yes" if t.index + 1 < len(t.entries) else "no",
                   "reading_key": b.active + "-" + str(t.index) + "-" + hashlib.sha256(address.encode()).hexdigest()[:16]}
        if action == "reload":
            desired["reload_seq"] = str(int(p.get("reload_seq", "0")) + 1)
        if action in ("open", "new"):
            desired["find"] = ""
        # Tab chrome uses ordinary named notes; keys refer to controller tabs,
        # never treat the notes as a second source of history or authority.
        notes, containers = {}, []
        for i, n in w.nodes.items():
            pp = props(w, i)
            if pp.get("viewer") != viewer or pp.get("role") not in ("viewer-tab", "viewer-tabs"):
                continue
            need(pp.get("actor") == w.me, "Tab projection belongs to another actor")
            if pp["role"] == "viewer-tabs":
                need(n["type"] == "surface" and n["parent"] == w.nodes[viewer]["parent"],
                     "Tab projection container moved; repair before navigating")
                containers.append(i)
            else:
                need(n.get("subject") is not None, "Invalid tab projection")
                need(pp.get("tab") not in notes, "Duplicate tab projection; repair before navigating")
                need(len(w.appearances_of(n["subject"])) == 1,
                     "Shared tab projection; repair before navigating")
                notes[pp.get("tab")] = i
        need(len(containers) <= 1, "Duplicate tab containers; repair before navigating")
        events, changed = [], []

        def collect(r):
            events.extend(r.get("events") or ([r["event"]] if r.get("event") else []))
            changed.extend(r.get("changed", []))
            return r

        def update(i, values):
            values = {k: v for k, v in values.items() if props(w, i).get(k) != v}
            if values:
                collect(moo.v_prop(w, i, values))

        # All fallible target/snapshot checks above precede these projections.
        try:
            if containers:
                container = containers[0]
            else:
                container = collect(moo.v_create(w, w.nodes[viewer]["parent"],
                                                {"kind": "surface", "title": "Viewer tabs"}))["created"]
                update(container, {"role": "viewer-tabs", "viewer": viewer, "actor": w.me})
            # Reuse inactive slots. History lives in the snapshot, not these
            # chrome appearances; repeated close/new cycles must not grow notes.
            spare = [notes[tk] for tk in notes if tk not in b.tabs]
            assigned = set()
            for order, (tk, tab) in enumerate(b.tabs.items(), 1):
                label = tab.entries[tab.index].title if tab.index >= 0 else "New tab"
                values = {"role": "viewer-tab", "viewer": viewer, "actor": w.me, "tab": tk,
                          "label": label, "active": "yes" if tk == b.active else "no",
                          "order": str(order), "closed": "no"}
                if tk not in notes:
                    if spare:
                        notes[tk] = spare.pop(0)
                        update(notes[tk], values)
                    else:
                        notes[tk] = collect(moo.v_create(
                            w, container, dict(values, kind="note", title=label)))["created"]
                else:
                    update(notes[tk], values)
                assigned.add(notes[tk])
            for i in set(notes.values()):
                if i not in assigned:
                    update(i, {"closed": "yes", "active": "no", "label": ""})
                label = props(w, i)["label"] if i in assigned else "Closed tab"
                if w.subjects[w.nodes[i]["subject"]]["title"] != label:
                    collect(moo.v_retitle(w, i, {"title": label}))
                if w.nodes[i]["parent"] != container:
                    collect(moo.v_move(w, i, {"into": container}))
            update(viewer, desired)
        except Refusal:
            for ev in reversed(events):
                w.undo(ev)
            raise
        return {"ok": True, "event": events[-1] if events else None, "events": events,
                "changed": sorted(set(changed)), "note": "Agora tabs updated" if events else "Already on this page"}
    except (NavigationError, ValueError, TypeError, KeyError) as exc:
        raise Refusal(str(exc)) from exc
