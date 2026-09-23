"""A synthetic desk with one mutation boundary and a bounded text projection.
Never access Agora worlds, execute authored code, or interpret subject text as commands.
"""

from copy import deepcopy
import json
import math
import threading


class Refused(ValueError):
    pass


class Desk:
    def __init__(self, nodes, variant="outline", concurrent=None):
        self.nodes = deepcopy(nodes)
        self.initial = deepcopy(nodes)
        self.variant = variant
        self.events = []
        self.lock = threading.RLock()
        self.concurrent = concurrent
        self.injections = []

    def get(self, ref):
        if ref not in self.nodes:
            raise Refused(f"Unknown reference {ref!r}. Navigate from root; use exact displayed IDs.")
        return self.nodes[ref]

    def children(self, ref):
        return sorted([n for n in self.nodes.values() if n.get("parent") == ref],
                      key=lambda n: (n.get("y", 0), n.get("x", 0), n["id"]))

    def source(self, node):
        return self.get(node["source"]) if node["kind"] == "appearance" else node

    def label(self, node):
        return node.get("label") or self.source(node).get("title", node["id"])

    def actions(self, n):
        result = {}
        if n["kind"] == "surface":
            result.update({
                "reference": 'args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.',
                "create": 'args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.',
            })
            if n.get("layout") == "free":
                result["tile"] = 'args {items: [appearance IDs], columns: integer}. Place only these immediate children in a grid. Pinned children refuse. One undoable event.'
            if n.get("layout") == "list":
                result["order"] = 'args {items: [all immediate child IDs in desired order]}. Change reading order, not content.'
        if n["kind"] == "appearance":
            result["remove"] = 'args {}. Remove this appearance only; retain content and other appearances.'
            result["place"] = 'args {container: destination surface ID}. Move this appearance. Entering a task column ALSO changes shared task status; Done requires all dependencies Done.'
            parent = self.get(n["parent"])
            if parent.get("layout") == "free":
                result["move"] = 'args {x: number, y: number}. Position this appearance in its immediate parent; preserve content. Read geometry for bounds.'
        if n["kind"] in {"note", "document", "task"}:
            result["edit"] = 'args {part: part ID, before: exact unique substring, after: replacement}. Edit only that match in this part; changes shared content.'
            result["insert"] = 'args {after: existing part ID, id: new part ID, text: text}. Insert a content part immediately after the named part.'
        return result

    def line(self, n):
        line = f"{n['id']} [{n['kind']}; rev {n['rev']}] {self.label(n)}"
        if n["kind"] == "appearance":
            line += f" -> {n['source']}" + (f" / part {n['part']}" if n.get("part") else "")
            if n.get("pinned"):
                line += " [pinned]"
        if n["kind"] == "surface":
            line += f" ({len(self.children(n['id']))} children; {n.get('layout', 'fixed')})"
        return line

    def look(self, target="root", aspect="structure", depth=1, offset=0, limit=12):
        with self.lock:
            n = self.get(target)
            if aspect not in {"structure", "content", "actions", "links", "geometry"}:
                raise Refused("aspect must be structure, content, actions, links, or geometry.")
            if not 0 <= depth <= 3 or not 1 <= limit <= 20 or offset < 0:
                raise Refused("Use depth 0..3, limit 1..20, offset >= 0.")
            lines = [self.line(n)]
            if aspect == "structure":
                entries = []
                def visit(ref, level):
                    if level > depth:
                        return
                    for child in self.children(ref):
                        entries.append((level, child))
                        visit(child["id"], level + 1)
                visit(target, 1)
                lines.extend("  " * level + self.line(child) for level, child in entries[offset:offset+limit])
                if offset + limit < len(entries):
                    lines.append(f"OMITTED {len(entries)-offset-limit} entries; continue offset={offset+limit}, same depth.")
                elif not entries:
                    lines.append("No visual children. Other aspects: content, actions, links, geometry.")
            elif aspect == "content":
                s = self.source(n)
                lines.append(f"CONTENT {s['id']} rev {s['rev']} ({s['kind']})")
                if "status" in s:
                    lines.append(f"status={s['status']}; dependencies={s.get('depends', [])}")
                parts = s.get("parts", [])
                if n.get("part"):
                    parts = [p for p in parts if p["id"] == n["part"]]
                lines.extend(f"  part {p['id']}: {p['text']}" for p in parts[offset:offset+limit])
                if offset + limit < len(parts):
                    lines.append(f"OMITTED parts; continue offset={offset+limit}.")
                if not parts:
                    lines.append("No text parts.")
            elif aspect == "actions":
                lines.extend(f"  {verb}: {description}" for verb, description in self.actions(n).items())
                if not self.actions(n):
                    lines.append("No mutation verbs here.")
                lines.append("act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.")
            elif aspect == "geometry":
                for key in ("parent", "x", "y", "width", "height", "pinned", "layout", "status"):
                    if key in n:
                        lines.append(f"  {key}: {n[key]}")
                if "parent" in n:
                    p = self.get(n["parent"])
                    lines.append(f"  Parent extent: {p.get('width')} x {p.get('height')}")
            else:
                s = self.source(n)
                lines.append(f"content={s['id']}")
                lines.extend(f"  {self.line(o)}; parent={o['parent']}" for o in self.nodes.values()
                             if o.get("source") == s["id"])
                if n.get("parent"):
                    lines.append(f"parent={n['parent']}")
            return {"text": "\n".join(lines)}

    def validate_place(self, n, container):
        if container["kind"] != "surface":
            raise Refused("Destination must be a surface.")
        if container.get("status"):
            s = self.source(n)
            if s["kind"] != "task":
                raise Refused("Task columns accept tasks only.")
            if container["status"] == "done":
                blocked = [d for d in s.get("depends", []) if self.get(d).get("status") != "done"]
                if blocked:
                    raise Refused(f"Dependencies are not done: {blocked}. Nothing moved or completed.")

    def _perform(self, verb, n, args):
        if verb == "edit":
            p = next((p for p in n["parts"] if p["id"] == args["part"]), None)
            if not p or not args.get("before") or p["text"].count(args["before"]) != 1:
                raise Refused("The selected part must contain exactly one nonempty before string. Read content again.")
            p["text"] = p["text"].replace(args["before"], args["after"], 1)
        elif verb == "insert":
            if any(p["id"] == args["id"] for p in n["parts"]):
                raise Refused("Part identity already exists.")
            index = next((i for i,p in enumerate(n["parts"]) if p["id"] == args["after"]), None)
            if index is None:
                raise Refused("after must identify an existing part.")
            n["parts"].insert(index+1, {"id": args["id"], "text": args["text"]})
        elif verb in {"create", "reference"}:
            if verb == "create":
                if args["kind"] not in {"note", "task"}:
                    raise Refused("create kind must be note or task.")
                if not isinstance(args["parts"], list) or any(set(p) != {"id", "text"} for p in args["parts"]):
                    raise Refused("parts must contain {id,text} records.")
                sid = f"content-{len(self.events)+1}"
                if sid in self.nodes:
                    raise Refused("Generated content identity collision.")
                self.nodes[sid] = {"id": sid, "kind": args["kind"], "title": args["title"],
                                   "parts": deepcopy(args["parts"]), "rev": 0}
                if args["kind"] == "task":
                    self.nodes[sid].update(status=n.get("status", "todo"), depends=[])
            else:
                sid = args["source"]
                source = self.get(sid)
                if source["kind"] in {"surface", "appearance"}:
                    raise Refused("reference source must be content, not an appearance or surface.")
                if args.get("part") and not any(p["id"] == args["part"] for p in source.get("parts", [])):
                    raise Refused("Unknown content part.")
            oid = f"appearance-{len(self.events)+1}"
            if oid in self.nodes:
                raise Refused("Generated appearance identity collision.")
            appearance = {"id": oid, "kind": "appearance", "source": sid, "parent": n["id"],
                          "x": args.get("x",16), "y": args.get("y",16), "width":180,"height":130,"rev":0}
            if args.get("part"):
                appearance["part"] = args["part"]
            self.validate_place(appearance, n)
            self.nodes[oid] = appearance
        elif verb == "remove":
            if n.get("pinned"):
                raise Refused("Pinned appearance cannot be removed.")
            del self.nodes[n["id"]]
        elif verb == "move":
            if n.get("pinned"):
                raise Refused("Pinned appearance cannot move.")
            p = self.get(n["parent"])
            x,y = args["x"],args["y"]
            if not (isinstance(x,(int,float)) and isinstance(y,(int,float)) and math.isfinite(x) and math.isfinite(y)):
                raise Refused("Coordinates must be finite numbers.")
            if x < 0 or y < 0 or x+n["width"] > p["width"] or y+n["height"] > p["height"]:
                raise Refused("Placement exceeds parent bounds. Inspect geometry.")
            n.update(x=x,y=y)
        elif verb == "place":
            if n.get("pinned"):
                raise Refused("Pinned appearance cannot move.")
            dest = self.get(args["container"])
            self.validate_place(n, dest)
            n.update(parent=dest["id"],x=16,y=16)
            if dest.get("status"):
                self.source(n)["status"] = dest["status"]
        elif verb == "tile":
            ids = args["items"]
            if not ids or len(set(ids)) != len(ids):
                raise Refused("items must be a nonempty list of distinct appearance IDs.")
            columns = args["columns"]
            if type(columns) is not int or not 1 <= columns <= len(ids):
                raise Refused("columns must be an integer from 1 to item count.")
            for index,oid in enumerate(ids):
                child = self.get(oid)
                if child["kind"] != "appearance" or child.get("parent") != n["id"] or child.get("pinned"):
                    raise Refused("Every tiled item must be an unpinned immediate appearance of this surface.")
                x,y = 16+(index%columns)*200,16+(index//columns)*150
                if x+child["width"] > n["width"] or y+child["height"] > n["height"]:
                    raise Refused("Grid does not fit. Choose fewer columns or items.")
                child.update(x=x,y=y)
        elif verb == "order":
            children = self.children(n["id"])
            if set(args["items"]) != {c["id"] for c in children} or len(args["items"]) != len(children):
                raise Refused("order must name every child exactly once.")
            for index,oid in enumerate(args["items"]):
                self.get(oid)["y"] = index*150
        else:
            raise Refused("Unsupported operation.")

    def act(self, verb, target, args=None, expected=None):
        args = args or {}
        with self.lock:
            if verb == "undo":
                return self.undo(target)
            # Fixed external edit: occurs before the first edit of the proposal.
            if self.concurrent and verb == "edit" and target == self.concurrent["target"]:
                injected = self.concurrent
                self.concurrent = None
                node = self.get(target)
                prior = deepcopy(node)
                part = next(p for p in node["parts"] if p["id"] == injected["part"])
                part["text"] = injected["text"]
                node["rev"] += 1
                self.injections.append(deepcopy(injected))
                self.events.append({"id":f"event-{len(self.events)+1}","verb":"external-edit","target":target,
                                    "before":{target:prior},"after":{target:deepcopy(node)}})
            n = self.get(target)
            if expected != n["rev"]:
                raise Refused(f"Stale target {target}: expected {expected}, current revision {n['rev']}. Read again; nothing from this action changed.")
            if verb not in self.actions(n):
                raise Refused(f"{verb} does not apply to {target} ({n['kind']}). Inspect actions and content links.")
            before = deepcopy(self.nodes)
            try:
                self._perform(verb,n,args)
                changed = {key for key in before.keys()|self.nodes.keys() if before.get(key) != self.nodes.get(key)}
                # Container membership/layout revisions advance, not content edits.
                for key in list(changed):
                    for value in (before.get(key,{}),self.nodes.get(key,{})):
                        if value.get("parent"):
                            changed.add(value["parent"])
                changed.add(target)
                for key in changed:
                    if key in self.nodes:
                        self.nodes[key]["rev"] = before.get(key,{}).get("rev",0)+1
                event = {"id": f"event-{len(self.events)+1}","verb":verb,"target":target,
                         "before":{k:before.get(k) for k in changed},
                         "after":{k:deepcopy(self.nodes.get(k)) for k in changed}}
                self.events.append(event)
            except Exception:
                self.nodes = before
                raise
            return {"text":f"Committed {event['id']}: {verb} {target}.\n"+
                    "\n".join(self.line(self.nodes[k]) if k in self.nodes else f"{k}: appearance removed" for k in sorted(changed))}

    def undo(self, event_id):
        event = next((e for e in self.events if e["id"] == event_id), None)
        if not event:
            raise Refused("Unknown event ID.")
        for key,after in event["after"].items():
            if self.nodes.get(key) != after:
                raise Refused("Undo conflicts with a subsequent change; nothing undone.")
        before = deepcopy(self.nodes)
        for key,value in event["before"].items():
            if value is None:
                self.nodes.pop(key,None)
            else:
                self.nodes[key] = deepcopy(value)
                self.nodes[key]["rev"] = before.get(key,{}).get("rev",0)+1
        undone = {"id":f"event-{len(self.events)+1}","verb":"undo","target":event_id,
                  "before":{k:before.get(k) for k in event["after"]},
                  "after":{k:deepcopy(self.nodes.get(k)) for k in event["after"]}}
        self.events.append(undone)
        return {"text":f"Committed {undone['id']}: undid {event_id}."}

    def dispatch(self, name, arguments):
        try:
            if name == "look":
                return self.look(**arguments)
            if name == "act":
                return self.act(**arguments)
            raise Refused("Only look and act exist.")
        except (Refused,KeyError,TypeError,ValueError) as exc:
            return {"error":str(exc),"recovery":"look at the target's actions or current state; no partial action committed."}

    def snapshot(self):
        return json.loads(json.dumps(self.nodes))
