"""store: the world as a log of records, each the facts one command changed (7 Oct 2026, Claude with Alex).

    python store.py begin <world>        start a world's log: one genesis record holding every fact, as it is now
    python store.py check <world>        replay the log and compare it with the world as it is; then the round trip
    python store.py stats <world>        how many records, their sizes, what they are made of
    python store.py tail <world> [n]     the last n records, one line each
    python store.py show <world> <seq>   one record whole

Why (measured 7 Oct): frontier's world is 3.2 MB and its file 124 MB, because every edit keeps a whole copy of the
thing it changed for undo; and the file holds Python objects only this code can read. The events could not rebuild
the world: they are command words plus those copies. A record here is what a command changed, said as facts.

A FACT is (thing, aspect, value): s710 prop:status "done". A thing is a subject (s..), a surface or appearance
(f.., a..), a link (l..) or the world itself ("world"). `flatten(world)` says a whole world as facts and nothing else;
`apply(world, facts)` assigns facts onto a world and then repairs what is derived. No verb and no rule runs in
either, so any code that knows this shape can read any world.

A RECORD is one line of JSON: the line someone sent (one press) and everything it set off, undone whole.
    {seq, shape, at, by, words, press?, saw, parts: [{cause, e, verb, target, args, facts}], ids?, state}
  parts   the events the command made, in order, each with the facts on the things it named; a rule's events say
          `cause: "rule a1088"`, the act's own say "act"
  facts   [thing, aspect, hash of the value before, value], or without the value when the aspect is gone; a long
          text changed in one place is written as that change, {"$splice": [start, characters gone, what came]}
  saw     what its author had been shown of the things it touched: {thing: {aspect: last event by then}} (the fence's own
          record); how a later merge tells a real conflict from two unrelated edits
  state   a digest of every fact after the record; the next command checks the world still says so (below)

ON THE LOG: what someone stated about a thing (title, text, kind, tags, due, each prop, each comment, each chat line,
links, where a thing is and what it comes after), definitions (they are things), a hand-set day.
NOT ON IT: revisions, boxes in a flow, a chat's joined text, indexes (derived: `apply` rebuilds them); what a person
has seen, folds, views (personal: the desk's, not the world's); where someone is standing (Alex, 7 Oct: presence has
no effect, so a `go` makes no record); reads, refusals, the house's state.

The bridge (why no verb was rewritten): a command runs as it always did, on the Python world; `begin` flattens the
world before it, `commit` flattens it after and writes the difference. About forty places make events today, with
sixteen shapes of undo; none of them is asked to log, so none can forget. `undo_plan` puts a record back by its
facts: one mechanism for every verb.

Shadow first: the pickle is still the truth. A world is on the log only once `begin` made its log (a fork takes its
base's log with it); a world without a log file is untouched. Out-of-band changes are never lost: when the world's
digest at a command's start is not the one the last record left, a record with `cause: "outside"` is written first
with the difference. `check` is the proof that matters: the log replayed equals the world flattened, and a world
rebuilt from its facts flattens back to the same facts.

Not built: loading a world from its log (the flip), a fork as a shared beginning plus a tail, ids that are safe
across forks, the personal store, reads that tell a scene which facts it depends on.
"""
import hashlib
import json
import os
import re
import sys
import time
from copy import deepcopy
from pathlib import Path

SHAPE = 1
HERE = Path(__file__).resolve().parent
SESSIONS = HERE / "sessions"
ABSENT = type("Absent", (), {"__repr__": lambda s: "ABSENT", "__bool__": lambda s: False})()

# a world's own attributes that are not facts: the things themselves, the event list (the log is that), who is acting
# right now, caches, and the counters (a record carries them when they move)
OFF_WORLD = {"subjects", "nodes", "events", "links", "injections", "me", "intent", "_intent_k", "acting_rule",
             "_ev_index", "last_created", "last_surface", "_ids", "_eseq"}
OFF_VERBS = {"go"}                    # presence: no record
SUBJECT_PLAIN = ("kind", "title", "due", "text", "tags")
SUBJECT_KNOWN = set(SUBJECT_PLAIN) | {"id", "rev", "comments", "props", "lines"}
NODE_PLAIN = ("type", "subject", "title", "layout", "query", "cols", "folded")
NODE_KNOWN = set(NODE_PLAIN) | {"id", "rev", "parent", "x", "y", "w", "h", "z", "props"}
ARG_CUT = 200                         # an event's argument longer than this is in the facts; the record keeps its size
SPLICE_OVER = 400                     # a text longer than this, changed in one place, is written as the change


# ---------------------------------------------------------------- values

def plain(v):
    """A value as plain JSON data, cut loose from the world's own objects (a comment is changed in place)."""
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    return json.loads(json.dumps(v, ensure_ascii=False, default=_unplain))


def _unplain(o):
    if isinstance(o, (set, frozenset)):
        return {"$set": sorted(o, key=str)}
    if isinstance(o, tuple):
        return list(o)
    return {"$repr": repr(o)}


def canon(v):
    return v if isinstance(v, str) else "\x00" + json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def h(v):
    """A short name for a value; '-' for none at all."""
    if v is ABSENT:
        return "-"
    return hashlib.blake2b(canon(v).encode("utf-8", "surrogatepass"), digest_size=5).hexdigest()


def _num(tid):
    m = re.search(r"(\d+)$", str(tid))
    return int(m.group(1)) if m else -1


def _order(key):
    tid, aspect = key
    return (0 if tid == "world" else 1, {"s": 0, "f": 1, "a": 2, "l": 3}.get(str(tid)[:1], 4), _num(tid), str(tid), aspect)


def digest(flat):
    """Every fact, as one word. Order does not matter, so a changed fact changes it by two cheap steps."""
    x = 0
    for (tid, aspect), v in flat.items():
        x ^= _fact_word(tid, aspect, v)
    return f"{x:016x}"


def _fact_word(tid, aspect, v):
    return int.from_bytes(hashlib.blake2b(f"{tid}\x01{aspect}\x01{canon(v)}".encode("utf-8", "surrogatepass"),
                                          digest_size=8).digest(), "big")


# ---------------------------------------------------------------- a world as facts

def flatten(w):
    """-> {(thing, aspect): value}: everything the world states, and nothing derived."""
    flat = {}
    for sid, s in w.subjects.items():
        _subject_facts(flat, sid, s)
    kids = {}
    for nid, n in w.nodes.items():
        kids.setdefault(n.get("parent"), []).append(n)
        _node_facts(flat, nid, n)
    choices = bool(getattr(w, "choices", False))
    for fid, group in kids.items():
        _order_facts(flat, w, fid, group, choices)
    _loose_facts(flat, w)
    return flat


# 14 Oct (Snappy Desk, stage 1; Alex: 'i approve the whole plan'): the pieces `flatten` is made of, so that a command's
# record can say only the things it touched (flatten_some) with the very same code that says a whole world

def _subject_facts(flat, sid, s):
    for k in ("kind", "title"):
        flat[(sid, k)] = s.get(k)
    if s.get("due") is not None:
        flat[(sid, "due")] = s["due"]
    if s.get("tags"):
        flat[(sid, "tags")] = list(s["tags"])
    for k, v in (s.get("props") or {}).items():
        flat[(sid, f"prop:{k}")] = plain(v)
    for c in s.get("comments") or ():
        flat[(sid, f"comment:{c['id']}")] = plain({k: v for k, v in c.items() if k != "id"})
    lines = s.get("lines")
    text = s.get("text") or ""
    if lines is not None:
        flat[(sid, "lines")] = True
        for l in lines:
            flat[(sid, f"line:{l['id']}")] = plain({k: v for k, v in l.items() if k != "id"})
        if text == "\n".join(l["text"] for l in lines):
            text = ""             # a chat's text is its lines joined: derived, or every line would store the chat again
    if text:
        flat[(sid, "text")] = text
    for k, v in s.items():
        if k not in SUBJECT_KNOWN:
            flat[(sid, f"x:{k}")] = plain(v)


def _node_facts(flat, nid, n):
    for k in NODE_PLAIN:
        if k in n:
            flat[(nid, k)] = n[k]
    flat[(nid, "in")] = n.get("parent")
    for k, v in (n.get("props") or {}).items():
        flat[(nid, f"prop:{k}")] = plain(v)
    for k, v in n.items():
        if k not in NODE_KNOWN:
            flat[(nid, f"x:{k}")] = plain(v)


def _order_facts(flat, w, fid, group, choices):
    lay = w.nodes[fid].get("layout") if fid in w.nodes else "free"
    if lay == "free" or fid is None:
        for n in group:       # a box someone chose
            flat[(n["id"], "box")] = [n.get("x", 0), n.get("y", 0), n.get("w", 0), n.get("h", 0)]
            flat[(n["id"], "z")] = n.get("z", 0)
    elif not choices:
        # in a flow the boxes are derived from the order; the order is said as what each child comes after, so a
        # move is three facts, not one per sibling
        prev = ""
        for n in w.children(fid) if len(group) > 1 else group:
            flat[(n["id"], "after")] = prev
            prev = n["id"]


def _loose_facts(flat, w):
    for l in w.links:
        flat[(l["id"], "link")] = plain({k: v for k, v in l.items() if k != "id"})
    for k, v in vars(w).items():
        if k not in OFF_WORLD:
            flat[("world", k)] = plain(v)


def flatten_some(w, flat0, sids, nids):
    """-> (old, new): the facts of the things a command touched, as `flat0` said them and as the world says them now.
    Touched are the subjects `sids` and the nodes `nids`; with a node come its siblings before and after (a move changes
    what each comes after) and, for a surface, its children; links and the world's own facts are always said whole
    (they are few). Everything else is as it was, so flat0 with `old` taken out and `new` put in is the world now."""
    parents = set()
    for nid in nids:
        if nid in w.nodes:
            parents.add(w.nodes[nid].get("parent"))
            if w.nodes[nid].get("type") == "surface":
                parents.add(nid)
        if (nid, "in") in flat0:
            parents.add(flat0[(nid, "in")])
        if (nid, "type") in flat0 and flat0[(nid, "type")] == "surface":
            parents.add(nid)
    groups = {p: [] for p in parents}
    for n in w.nodes.values():
        p = n.get("parent")
        if p in groups:
            groups[p].append(n)
    nodeset = set(nids) | {n["id"] for g in groups.values() for n in g}
    things = set(sids)
    old = {}
    for k, v in flat0.items():                 # one pass: the touched things, the old children of the parents, loose facts
        tid, aspect = k
        if tid in things or tid in nodeset or tid == "world" or aspect == "link" or (aspect == "in" and v in parents):
            old[k] = v
            if aspect == "in" and v in parents:
                nodeset.add(tid)
    # an old child found in that pass brings all of its facts (it may have been met before its `in`)
    old.update({k: v for k, v in flat0.items() if k[0] in nodeset and k not in old})
    new = {}
    for sid in things:
        if sid in w.subjects:
            _subject_facts(new, sid, w.subjects[sid])
    for nid in nodeset:
        if nid in w.nodes:
            _node_facts(new, nid, w.nodes[nid])
            parents.add(w.nodes[nid].get("parent"))
    choices = bool(getattr(w, "choices", False))
    for p in parents:
        group = groups.get(p)
        if group is None:
            group = groups[p] = [n for n in w.nodes.values() if n.get("parent") == p]
        part = {}
        _order_facts(part, w, p, group, choices)
        new.update({k: v for k, v in part.items() if k[0] in nodeset})
    _loose_facts(new, w)
    return old, new


def diff(a, b):
    """-> [(thing, aspect, value | ABSENT)]: what turns flat a into flat b."""
    out = [(k[0], k[1], v) for k, v in b.items() if k not in a or a[k] != v]
    out += [(k[0], k[1], ABSENT) for k in a if k not in b]
    return sorted(out, key=lambda f: _order((f[0], f[1])))


def whole(v, old):
    """A fact's value as it is read from a record: itself, or, for a long text changed in one place, the text before
    with that place changed ({"$splice": [start, how many characters go, what comes instead]})."""
    if isinstance(v, dict) and len(v) == 1 and "$splice" in v:
        start, cut, ins = v["$splice"]
        old = "" if old is ABSENT or old is None else old
        return old[:start] + ins + old[start + cut:]
    return v


def patch(flat, facts):
    """Assign facts onto a flat, in place."""
    for tid, aspect, v in facts:
        if v is ABSENT:
            flat.pop((tid, aspect), None)
        else:
            flat[(tid, aspect)] = whole(v, flat.get((tid, aspect), ABSENT))
    return flat


# ---------------------------------------------------------------- facts onto a world

def _subject_skeleton(sid):
    return {"id": sid, "kind": "note", "title": "", "text": "", "tags": [], "due": None, "rev": 1, "comments": [], "props": {}}


def _node_skeleton(nid):
    return {"id": nid, "type": "appearance", "parent": None, "x": 0, "y": 0, "w": 200, "h": 100, "z": 1, "rev": 1}


def _put(rows, rid, value):
    """Set or drop the row with this id in a list kept in id order (comments, chat lines, links)."""
    at = next((i for i, r in enumerate(rows) if r["id"] == rid), None)
    if value is ABSENT:
        if at is not None:
            del rows[at]
        return
    row = dict(plain(value), id=rid)
    row = {"id": rid, **{k: v for k, v in row.items() if k != "id"}}
    if at is not None:
        rows[at] = row
    else:
        rows.append(row)
        rows.sort(key=lambda r: _num(r["id"]))


def apply(w, facts, bump=True):
    """Assign facts onto a world's plain state, then repair what is derived from them: a chat's text, the order and
    boxes of the flows that changed, and (bump) the revisions of what was touched. -> the ids touched."""
    facts = list(facts)
    if hasattr(w, "forget_appearances"):
        w.forget_appearances()        # nodes are made and taken away here with no event between
    old_order = {}
    for tid, aspect, v in facts:      # the order of every flow about to change, as it is now: the one a thing leaves
        if aspect in ("after", "in", "type"):       # and the one it arrives in
            for p in ((w.nodes[tid].get("parent") if tid in w.nodes else None), (v if aspect == "in" and v is not ABSENT else None)):
                if p in w.nodes and p not in old_order:
                    old_order[p] = [k["id"] for k in w.children(p)]
    relined, texted, after, reflow, gone, touched = set(), set(), {}, set(), set(), set()
    # a thing is a subject or a node by what is said of it (kind, type), never by the letter its id begins with
    # (a person is p12, a subject all the same)
    new_subjects = {tid for tid, aspect, v in facts if aspect == "kind" and v is not ABSENT}
    new_nodes = {tid for tid, aspect, v in facts if aspect == "type" and v is not ABSENT}
    for tid, aspect, v in facts:
        touched.add(tid)
        if tid == "world":
            if v is ABSENT:
                vars(w).pop(aspect, None)
            else:
                val = plain(v)
                setattr(w, aspect, set(val["$set"]) if isinstance(val, dict) and set(val) == {"$set"} else val)
            continue
        if aspect == "link":
            _put(w.links, tid, v)
            continue
        if tid in w.subjects or tid in new_subjects:
            s = w.subjects.get(tid)
            if s is None:
                if v is ABSENT:
                    continue
                s = w.subjects[tid] = _subject_skeleton(tid)
            if aspect == "kind" and v is ABSENT:
                gone.add(tid)
            elif aspect in ("kind", "title"):
                s[aspect] = v
            elif aspect == "due":
                s["due"] = None if v is ABSENT else v
            elif aspect == "tags":
                s["tags"] = [] if v is ABSENT else list(v)
            elif aspect == "text":
                s["text"] = "" if v is ABSENT else v
                texted.add(tid)
            elif aspect == "lines":
                if v is ABSENT:
                    s.pop("lines", None)
                else:
                    s.setdefault("lines", [])
                    relined.add(tid)
            elif aspect.startswith("line:"):
                _put(s.setdefault("lines", []), aspect[5:], v)
                relined.add(tid)
            elif aspect.startswith("comment:"):
                _put(s["comments"], aspect[8:], v)
            elif aspect.startswith("prop:"):
                if v is ABSENT:
                    s["props"].pop(aspect[5:], None)
                else:
                    s["props"][aspect[5:]] = v
            elif aspect.startswith("x:"):
                if v is ABSENT:
                    s.pop(aspect[2:], None)
                else:
                    s[aspect[2:]] = plain(v)
            continue
        n = w.nodes.get(tid)
        if n is None:
            if v is ABSENT or tid not in new_nodes:
                continue          # a fact about a thing that is not here and is not being made: nothing to assign
            n = w.nodes[tid] = _node_skeleton(tid)
        if aspect == "type" and v is ABSENT:
            gone.add(tid)
            reflow.add(n.get("parent"))
        elif aspect in NODE_PLAIN:
            if v is ABSENT:
                n.pop(aspect, None)
            else:
                n[aspect] = v
        elif aspect == "in":
            reflow.add(n.get("parent"))
            n["parent"] = None if v is ABSENT else v
            reflow.add(n["parent"])
        elif aspect == "box":
            if v is not ABSENT:
                n["x"], n["y"], n["w"], n["h"] = v
        elif aspect == "z":
            if v is not ABSENT:
                n["z"] = v
        elif aspect == "after":
            if v is not ABSENT:
                after[tid] = v
        elif aspect.startswith("prop:"):
            if v is ABSENT:
                (n.get("props") or {}).pop(aspect[5:], None)
            else:
                n.setdefault("props", {})[aspect[5:]] = v
        elif aspect.startswith("x:"):
            if v is ABSENT:
                n.pop(aspect[2:], None)
            else:
                n[aspect[2:]] = plain(v)
    for tid in gone:
        w.subjects.pop(tid, None)
        w.nodes.pop(tid, None)
    # ---- derived
    for sid in relined - texted:
        s = w.subjects.get(sid)
        if s is not None and s.get("lines") is not None:
            s["text"] = "\n".join(l["text"] for l in s["lines"])
    flows = {w.nodes[k]["parent"] for k in after if k in w.nodes} | {p for p in reflow if p}
    for fid in sorted((f for f in flows if f in w.nodes), key=lambda f: _depth(w, f)):
        if w.nodes[fid].get("layout") == "free":
            continue
        kids = {k["id"] for k in w.children(fid)}
        was = [k for k in old_order.get(fid, []) if k in kids and not (k in after and k in new_nodes)]
        was += sorted((k for k in kids if k not in was), key=_num)     # arrivals last, whatever box they came with
        pred, prev = {}, ""
        for k in was:
            if k in after:
                pred[k] = after[k]        # said: it comes after this one now
            else:
                pred[k], prev = prev, k   # not said: it still follows the one before it among those not moved
        order, placed, nxt = [], set(), {}
        for k in was:
            nxt.setdefault(pred[k], []).append(k)
        # read the order off: each thing, then what comes after it, the ones that were said to first. With every fact
        # of a change this is exactly the order it left; with only some (an undo, a merge) the rest keep their order
        for root in [""] + was:
            stack = [root] if root else []
            if root == "":
                stack = sorted(nxt.get("", []), key=lambda k: k not in after)[::-1]
            while stack:
                k = stack.pop()
                if k in placed:
                    continue
                order.append(k)
                placed.add(k)
                stack.extend(sorted((c for c in nxt.get(k, []) if c not in placed), key=lambda c: c not in after)[::-1])
        if getattr(w, "choices", False):
            w._order(fid, order)
        else:
            col = w.nodes[fid].get("layout") == "column"
            for i, k in enumerate(order):     # the legacy order is carried by position along the flow
                n = w.nodes[k]
                n["y" if col else "x"], n["x" if col else "y"], n["z"] = i * 1000, 0, i + 1
            w.reflow(fid)
    if hasattr(w, "forget_appearances"):
        w.forget_appearances()
    if bump:
        for tid in touched - gone:
            if tid in w.subjects:
                w.subjects[tid]["rev"] += 1
                for a in w.appearances_of(tid):
                    w._bump(a)
            elif tid in w.nodes:
                w._bump(tid)
    return touched


def _depth(w, fid):
    d = 0
    while fid in w.nodes and w.nodes[fid].get("parent"):
        fid, d = w.nodes[fid]["parent"], d + 1
    return d


def materialize(flat, counters=None):
    """A World from facts alone: assign every fact, then derive. `counters`: {"ids", "eseq"} when known."""
    from world import World
    w = World.__new__(World)
    w.subjects, w.nodes, w.events, w.injections, w.links = {}, {}, [], [], []
    w.last_created = w.last_surface = None
    facts = sorted(((k[0], k[1], v) for k, v in flat.items()), key=lambda f: _order((f[0], f[1])))
    apply(w, [f for f in facts if f[1] != "after"], bump=False)       # every thing first, then the orders
    apply(w, [f for f in facts if f[1] == "after"], bump=False)
    ids = [_num(k[0]) for k in flat if k[0] != "world"]
    ids += [_num(k[1]) for k in flat if k[1].startswith(("comment:", "line:"))]
    w._ids = max([*ids, (counters or {}).get("ids", 0)])
    w._eseq = (counters or {}).get("eseq", 0)
    return w


# ---------------------------------------------------------------- the log

def log_path(pickle_path):
    p = Path(pickle_path)
    return p.with_name(p.name[:-len(".pickle")] + ".log.jsonl") if p.name.endswith(".pickle") else p.with_name(p.name + ".log.jsonl")


def _enc(facts, before):
    """Facts as they are written: [thing, aspect, hash before, value], or without the value when it is gone."""
    out = []
    for tid, aspect, v in facts:
        was = before.get((tid, aspect), ABSENT)
        hb = h(was)
        if aspect == "text" and isinstance(v, str) and isinstance(was, str) and len(v) > SPLICE_OVER:
            # a long text changed in one place (a line added to a notebook, one passage replaced) is written as that
            # change, or every line added to a 40 KB note would write the note again (frontier, 7 Oct)
            a = 0
            top = min(len(was), len(v))
            while a < top and was[a] == v[a]:
                a += 1
            z = 0
            while z < top - a and was[len(was) - 1 - z] == v[len(v) - 1 - z]:
                z += 1
            ins = v[a:len(v) - z]
            if len(ins) * 2 < len(v):
                out.append([tid, aspect, hb, {"$splice": [a, len(was) - z - a, ins]}])
                continue
        out.append([tid, aspect, hb] if v is ABSENT else [tid, aspect, hb, v])
    return out


def dec(rows):
    return [(r[0], r[1], r[3] if len(r) > 3 else ABSENT) for r in rows]


def facts_of(rec):
    return [f for p in rec.get("parts") or () for f in dec(p.get("facts") or ())]


_HEADS = {}     # log path -> (size, seq, state, flat): what this process knows the log says, so a long-lived one reads only the tail


class Log:
    def __init__(self, path):
        self.path = Path(path)

    def exists(self):
        return self.path.exists()

    def records(self, start=0):
        """Every record from byte `start`, as (record, end byte). A torn last line (a write cut short) is not one."""
        if not self.path.exists():
            return
        with open(self.path, "rb") as f:
            f.seek(start)
            pos = start
            for raw in f:
                if not raw.endswith(b"\n"):
                    return
                pos += len(raw)
                if raw.strip():
                    yield json.loads(raw.decode("utf-8")), pos

    def head(self):
        """-> (seq, state) of the last whole record, read from the end of the file; None for no log."""
        if not self.path.exists():
            return None
        size = self.path.stat().st_size
        known = _HEADS.get(str(self.path))
        if known and known[0] == size:
            return known[1], known[2]
        with open(self.path, "rb") as f:
            back = 4096
            while True:
                f.seek(max(0, size - back))
                chunk = f.read(min(back, size))
                body = chunk[:chunk.rfind(b"\n") + 1] if b"\n" in chunk else b""
                lines = [l for l in body.split(b"\n") if l.strip()]
                if lines and (len(lines) > 1 or back >= size):
                    # only the two fields are read: the last record may be a genesis of megabytes
                    last = lines[-1].decode("utf-8")
                    m = re.match(r'\{"seq": (\d+), "shape": \d+, "state": "([0-9a-f]+)"', last)
                    if m:
                        return int(m.group(1)), m.group(2)
                    rec = json.loads(last)
                    return rec["seq"], rec.get("state")
                if back >= size:
                    return None
                back *= 16

    def flat(self):
        """-> (flat, seq, state): the log replayed. A process that asked before reads only what was added."""
        key = str(self.path)
        size = self.path.stat().st_size if self.path.exists() else 0
        known = _HEADS.get(key)
        if known and known[0] == size:
            return known[3], known[1], known[2]
        flat, seq, state, start = ({}, 0, None, 0) if not known or known[0] > size else (known[3], known[1], known[2], known[0])
        end = start
        for rec, end in self.records(start):
            patch(flat, facts_of(rec))
            seq, state = rec["seq"], rec.get("state")
        _HEADS[key] = (end, seq, state, flat)
        return flat, seq, state

    def append(self, rec, flat_after=None):
        """Write one record as one line, flushed to disk before anyone is answered. -> its seq."""
        head = self.head()
        rec = {"seq": (head[0] if head else 0) + 1, "shape": SHAPE, "state": rec.pop("state", None), **rec}
        line = (json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8", "surrogatepass")
        if self.path.exists():
            with open(self.path, "r+b") as f:     # a write cut short left half a line: it was never acknowledged
                f.seek(0, 2)
                size = f.tell()
                back = min(size, 1 << 16)
                f.seek(size - back)
                tail = f.read(back)
                if tail and not tail.endswith(b"\n"):
                    # A large interrupted record can exceed the last 64 KiB.
                    # Find its actual beginning before appending the next line.
                    while b"\n" not in tail and back < size:
                        back = min(size, back * 2)
                        f.seek(size - back)
                        tail = f.read(back)
                    cut = tail.rfind(b"\n") + 1
                    f.truncate(size - back + cut)
        with open(self.path, "ab") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        size = self.path.stat().st_size
        if flat_after is not None:
            _HEADS[str(self.path)] = (size, rec["seq"], rec["state"], flat_after)
        else:
            _HEADS.pop(str(self.path), None)
        return rec["seq"]

    def find(self, pred):
        return next((rec for rec, _ in self.records() if pred(rec)), None)

    def record_of_event(self, eid):
        """The record a world event belongs to, or None (an event from before the log, or one that left no record)."""
        hit = None
        for rec, _ in self.records():
            if any(p.get("e") == eid for p in rec.get("parts") or ()):
                hit = rec
        return hit

    def before(self, seq, keys):
        """-> {key: value | ABSENT}: what each fact said just before record `seq`."""
        out, keys = {k: ABSENT for k in keys}, set(keys)
        for rec, _ in self.records():
            if rec["seq"] >= seq:
                break
            for tid, aspect, v in facts_of(rec):
                if (tid, aspect) in keys:
                    out[(tid, aspect)] = v if v is ABSENT else whole(v, out[(tid, aspect)])
        return out

    def value_at(self, key, seq):
        """What one fact said once record `seq` was written."""
        return self.before(seq + 1, [key])[key]


# ---------------------------------------------------------------- begin / commit: the bridge

class Ctx:
    """One command's hold on the log: the world as facts before it. The desk carries it as `_store` while the command
    runs (undo and the fence ask the log through it); it is never saved with the desk."""

    def __init__(self, log, flat0, state0, n0, seen0):
        self.log, self.flat0, self.state0, self.n0, self.seen0 = log, flat0, state0, n0, seen0
        self.t0 = time.time()
        self.quick = None             # (subject ids, node ids) at the start, when the command began from kept facts

    def __reduce__(self):
        return (type(None), ())       # pickled with a desk by accident, it is nothing


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def genesis(desk, pickle_path, by="house", why=""):
    """Start a world's log: every fact it holds now, as the first record. Refuses a world that has one."""
    log = Log(log_path(pickle_path))
    if log.exists() and log.head():
        raise ValueError(f"{log.path.name} already begins this world's log")
    w = desk.world
    flat = flatten(w)
    rec = {"state": digest(flat), "at": _now(), "by": by, "words": "", "ids": getattr(w, "_ids", 0),
           "eseq": getattr(w, "_eseq", 0), "events_before": len(w.events),
           "parts": [{"cause": "genesis" + (f": {why}" if why else ""), "facts": _enc(diff({}, flat), {})}]}
    return log.append(rec, flat)


import weakref  # noqa: E402

# 14 Oct (Snappy Desk, stage 1): a world this process last wrote a record for, and the log's size just after it. While
# both hold, the world is what that record left, so a command begins from the facts kept in memory (no flatten of the
# whole world, no digest of every fact: 65 ms of every Enter on the bench). A world loaded again from its file is a new
# object, and is flattened whole once.
_MARKS = weakref.WeakKeyDictionary()
VERIFY_EVERY = 20                   # every 20th quick record is also checked against the whole world flattened
FULL_VERBS = {"undo", "redo", "merge"}       # commands that put back many things at once are recorded the whole way
_QUICK = [0]


def begin(desk, pickle_path):
    """Before a command: the world as facts. -> a Ctx, or None when this world has no log. When the world is not what
    the last record left (something changed it without a record), that difference is written first, as its own
    record, so the log never falls behind the world."""
    log = Log(log_path(pickle_path))
    head = log.head()
    if head is None:
        return None
    w = desk.world
    known = _HEADS.get(str(log.path))
    size = log.path.stat().st_size
    if known is not None and known[0] == size and _MARKS.get(w) == (str(log.path), size):
        desk._store = Ctx(log, known[3], known[2], len(w.events), dict(getattr(desk, "_seen_idx", None) or {}))
        desk._store.quick = (set(w.subjects), set(w.nodes))
        return desk._store
    flat0 = flatten(w)
    state0 = digest(flat0)
    if head[1] != state0:
        said, _seq, _state = log.flat()
        facts = diff(said, flat0)
        if facts:
            log.append({"state": state0, "at": _now(), "by": "?", "words": "",
                        "parts": [{"cause": "outside", "facts": _enc(facts, said)}],
                        "note": "the world changed without a record; this is the difference, found at the next command"},
                       dict(flat0))
    seen0 = dict(getattr(desk, "_seen_idx", None) or {})
    desk._store = Ctx(log, flat0, state0, len(w.events), seen0)
    return desk._store


def _args(args):
    out = {}
    for k, v in (args or {}).items():
        v = plain(v)
        s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
        out[k] = v if len(s) <= ARG_CUT else {"…": len(s), "h": h(v)}
    return out


def commit(ctx, desk, words, by, press=None, window=None):
    """After a command: write what it changed. -> the record's seq, or None when nothing on the log changed."""
    if ctx is None:
        return None
    vars(desk).pop("_store", None)
    w = desk.world
    events = [e for e in w.events[ctx.n0:] if e.get("verb") not in OFF_VERBS]
    flat1 = None
    if ctx.quick is not None and not any(e.get("verb") in FULL_VERBS for e in w.events[ctx.n0:]):
        flat1, facts, outside = _quick_facts(ctx, w, w.events[ctx.n0:])
        if outside:
            # what the check found that no event of this command names: written first, as its own record, as a
            # command beginning the whole way does; the command's own record then follows from there
            mid = patch(dict(ctx.flat0), outside)
            mid_state = _move(ctx.state0, ctx.flat0, outside)
            ctx.log.append({"state": mid_state, "at": _now(), "by": "?", "words": "",
                            "parts": [{"cause": "outside", "facts": _enc(outside, ctx.flat0)}],
                            "note": "the world changed without a record (or a command changed what its events do not name); "
                                    "found when a quick record was checked against the whole world"}, dict(mid))
            ctx.flat0, ctx.state0 = mid, mid_state
    if flat1 is None:
        flat1 = flatten(w)
        facts = diff(ctx.flat0, flat1)
    if not facts and not events:
        _MARKS[w] = (str(ctx.log.path), ctx.log.path.stat().st_size)
        return None
    # each fact goes to the first event of the command that names its thing and touched that aspect, as the fence
    # reads aspects (one reading: desk.event_aspects); else the first that names it; what no event names is the act's
    from desk import event_aspects
    subject_of = lambda nid: flat1.get((nid, "subject")) or ctx.flat0.get((nid, "subject"))      # noqa: E731
    owners, parts = {}, []
    for i, e in enumerate(events):
        names = {e.get("target"), *(e.get("changed") or [])} - {None}
        names |= {subject_of(n) for n in list(names)} - {None}
        if e.get("verb") == "create":
            names |= {f[0] for f in facts if f[1] in ("kind", "type") and f[2] is not ABSENT}
        asp = event_aspects(e)
        for n in names:
            owners.setdefault(n, []).append((i, asp))
        via = str(e.get("via") or "")
        part = {"cause": via if via.startswith("rule ") else "act", "e": e["id"], "verb": e["verb"], "target": e.get("target"),
                "args": _args(e.get("args"))}
        for k in ("by", "via", "cause", "tripped_by", "note", "to", "knocked"):
            if e.get(k) and not (k == "by" and e[k] == by):
                part["from" if k == "cause" else k] = plain(e[k])      # `from`: the event that caused this one
        part["facts"] = []
        parts.append(part)
    loose = []
    for f in facts:
        cands = owners.get(f[0])
        if not cands and f[1] == "link":           # a link is named by its ends
            v = f[2] if f[2] is not ABSENT else ctx.flat0.get((f[0], "link")) or {}
            cands = next((owners[x] for x in (v.get("from"), v.get("to")) if x in owners), None)
        if not cands:
            loose.append(f)
            continue
        fa = fence_aspect(f[1])
        i = next((i for i, asp in cands if asp is not None and fa in asp), None)
        if i is None:
            i = next((i for i, asp in cands if asp is None), cands[0][0])
        parts[i]["facts"].append(f)
    for p in parts:
        p["facts"] = _enc(p["facts"], ctx.flat0)
    if loose:
        if parts:
            parts[0]["facts"] += _enc(loose, ctx.flat0)
        else:
            parts.append({"cause": "unnamed", "facts": _enc(loose, ctx.flat0)})
    touched = {f[0] for f in facts} | {subject_of(f[0]) for f in facts} - {None}
    me = by + ("/" + window if window else "")
    # the fence counts in events (how many the world held when a thing was last shown); a record names the event
    # itself, the last one made by then, so the number can be read against the world's own ids (Juniper, 7 Oct:
    # 'text seen at 6209' looked older than her read after e6215, and was the same moment)
    at = lambda i: w.events[i - 1]["id"] if 0 < i <= len(w.events) else "e0"      # noqa: E731
    saw = {}
    for (obs, nid), v in ctx.seen0.items():
        if nid in touched and obs.split("/")[0] == by and (obs == me or "/" not in obs):
            saw[nid] = {a: at(i) for a, i in ({"*": v} if isinstance(v, int) else v).items()}
    rec = {"state": _move(ctx.state0, ctx.flat0, facts), "at": _now(), "by": by, "words": words, "parts": parts}
    if press:
        rec["press"] = press
    if window:
        rec["window"] = window
    if saw:
        rec["saw"] = saw
    if getattr(w, "_ids", None) is not None:
        rec["ids"] = w._ids
    rec["ms"] = int((time.time() - ctx.t0) * 1000)
    seq = ctx.log.append(rec, flat1)
    _MARKS[w] = (str(ctx.log.path), ctx.log.path.stat().st_size)
    return seq


def mark_snapshot(desk, pickle_path):
    """Before a world is pickled to its file: which record of its log the file will hold (seq, byte after it). A world
    read back from that file puts on any record written after it (catch_up)."""
    log = Log(log_path(pickle_path))
    head = log.head() if log.exists() else None
    if head is not None:
        desk._snap_at = (head[0], log.path.stat().st_size)


def catch_up(desk, pickle_path):
    """14 Oct (Snappy Desk, stage 1, step 2; Alex approved the log as the world's record): the world server keeps the
    world in memory and saves its file in the background, so a world read from its file (after a crash, or by a reader
    in another process) may be behind its log. The records written after the file's snapshot are put on: their facts
    onto the world, their events into its history (as the record says them: arguments cut long, no undo copy; undo of
    such a record goes through the log). -> how many records were put on."""
    at = getattr(desk, "_snap_at", None)
    if not at:
        return 0
    log = Log(log_path(pickle_path))
    if not log.exists():
        return 0
    seq0, byte0 = at
    head = log.head()
    if head is None or head[0] <= seq0:
        return 0
    w = desk.world
    flat, n = None, 0
    for rec, end in log.records(byte0 if byte0 <= log.path.stat().st_size else 0):
        if rec["seq"] <= seq0:
            continue
        if flat is None:
            flat = flatten(w)
        facts = [(t, a, v if v is ABSENT else whole(v, flat.get((t, a), ABSENT))) for t, a, v in facts_of(rec)]
        patch(flat, facts)
        apply(w, facts)
        for p in rec.get("parts") or ():
            eid = str(p.get("e") or "")
            if not eid:
                continue
            if rec.get("atomic_world"):
                # Keep metadata used by aspect fences, rules and whole undo.
                w.events.append(deepcopy(p["event"]))
            else:
                w.events.append({"id": eid, "verb": p.get("verb"), "target": p.get("target"), "args": p.get("args") or {},
                                 "by": p.get("by") or rec.get("by"), "at": rec.get("at"), "cmd": rec.get("words", ""),
                                 "note": "put back from the log: the world's file was saved before it"})
            if eid[1:].isdigit():
                w._eseq = max(getattr(w, "_eseq", 0) or 0, int(eid[1:]))
            if p.get("verb") == "undo":
                original = w.event_by_id(p.get("target"))
                if original:
                    original["undone"] = True
        if rec.get("ids") is not None:
            w._ids = max(getattr(w, "_ids", 0) or 0, rec["ids"])
        if rec.get("atomic_world"):
            import atomic_world
            atomic_world.restore_metadata(desk, rec)
        desk._snap_at = (rec["seq"], end)
        n += 1
    if n:
        vars(w).pop("_ev_index", None)
    return n


def _quick_facts(ctx, w, events):
    """-> (flat after, the command's facts, facts no event names), from the things the command's events name and the
    things it made or removed. Every VERIFY_EVERY-th time, and always with DESK_LOG_VERIFY=1, the answer is checked
    against the whole world flattened; what it missed is said in the log's .err and returned as the third part."""
    subs0, nodes0 = ctx.quick
    flat0 = ctx.flat0
    names = set()
    for e in events:
        names.add(e.get("target"))
        names.update(e.get("changed") or ())
    names.discard(None)
    sids = {n for n in names if n in w.subjects or (n, "kind") in flat0}
    nids = {n for n in names if n in w.nodes or (n, "type") in flat0}
    sids |= (set(w.subjects) ^ subs0)
    nids |= (set(w.nodes) ^ nodes0)
    for nid in list(nids):
        sub = (w.nodes.get(nid) or {}).get("subject") or flat0.get((nid, "subject"))
        if sub:
            sids.add(sub)
    old, new = flatten_some(w, flat0, sids, nids)
    facts = diff(old, new)
    flat1 = dict(flat0)
    for k in old:
        del flat1[k]
    flat1.update(new)
    _QUICK[0] += 1
    if os.environ.get("DESK_LOG_VERIFY") == "1" or _QUICK[0] % VERIFY_EVERY == 0:
        whole_flat = flatten(w)
        if whole_flat != flat1:
            missed = diff(flat1, whole_flat)      # on things the command did not touch, so flat1 there is flat0
            try:
                with open(Path(str(ctx.log.path) + ".err"), "a", encoding="utf-8") as f:
                    f.write(f"--- {_now()} quick record missed {sorted({m[0] for m in missed})[:20]} after "
                            f"{[(e.get('verb'), e.get('target')) for e in events][:6]}; written as an outside record\n")
            except OSError:
                pass
            return whole_flat, facts, missed
    return flat1, facts, []


def fence_aspect(aspect):
    """A fact's aspect in the fence's words (desk.aspects_of): the same question, 'what did this touch', asked once."""
    head = aspect.split(":", 1)[0]
    if head == "prop":
        return aspect
    return {"title": "title", "due": "due", "tags": "tags", "text": "text", "lines": "text", "line": "text",
            "comment": "comments", "link": "links", "in": "place", "after": "place", "box": "place", "z": "place",
            "folded": "place", "type": "place", "subject": "place"}.get(head)


def _move(state, flat0, facts):
    """The digest after `facts`, from the digest before: each changed fact leaves and its new value joins."""
    x = int(state, 16)
    for tid, aspect, v in facts:
        old = flat0.get((tid, aspect), ABSENT)
        if old is not ABSENT:
            x ^= _fact_word(tid, aspect, old)
        if v is not ABSENT:
            x ^= _fact_word(tid, aspect, whole(v, old))
    return f"{x:016x}"


def _fault(log_file, what):
    """The log beside the world must never break a command: a fault here is written down and the command goes on."""
    import traceback
    try:
        with open(Path(str(log_file) + ".err"), "a", encoding="utf-8") as f:
            f.write(f"--- {_now()} {what}\n{traceback.format_exc()}\n")
    except Exception:      # noqa: BLE001
        pass


def safe_begin(desk, pickle_path):
    if os.environ.get("DESK_LOG", "") == "off":
        return None
    try:
        return begin(desk, pickle_path)
    except Exception:      # noqa: BLE001
        _fault(log_path(pickle_path), "begin")
        return None


def safe_commit(ctx, desk, words, by, press=None, window=None):
    if ctx is None:
        return None
    try:
        return commit(ctx, desk, words, by, press, window)
    except Exception:      # noqa: BLE001
        vars(desk).pop("_store", None)
        _fault(ctx.log.path, f"commit of {words[:200]!r} by {by}")
        return None


# ---------------------------------------------------------------- undo: a record put back by its facts

class CannotUndo(Exception):
    pass


CREATES = {"kind", "type", "link"}


def undo_plan(log, rec, flat_now):
    """-> the facts that put record `rec` back, whole. Refused (CannotUndo, saying what) when any fact it set has been
    changed since, or when something it made is pointed at by something this undo leaves in the world."""
    facts = facts_of(rec)
    if not facts:
        raise CannotUndo(f"record {rec['seq']} changed nothing in the world: there is nothing to put back")
    keys = [(f[0], f[1]) for f in facts]
    before = log.before(rec["seq"], keys)
    facts = [(tid, aspect, v if v is ABSENT else whole(v, before[(tid, aspect)])) for tid, aspect, v in facts]
    made = {tid for tid, aspect, v in facts if aspect in CREATES and before[(tid, aspect)] is ABSENT}
    # where a thing stands in a flow (`after`) moves whenever a neighbour does: it is not a change to the thing, and
    # apply repairs the order, so by itself it never stops an undo
    moved = [f"{tid} {aspect}" for tid, aspect, v in facts
             if aspect != "after" and flat_now.get((tid, aspect), ABSENT) != v]
    if moved:
        raise CannotUndo("changed since: " + ", ".join(moved[:6]) + (f" and {len(moved) - 6} more" if len(moved) > 6 else ""))
    back = []
    for tid, aspect, _v in facts:
        was = before[(tid, aspect)]
        if aspect == "after" and (tid in made or (was not in ("", ABSENT) and (was, "type") not in flat_now)):
            continue          # the thing goes, or what it came after is no longer there: it stays where it is
        back.append((tid, aspect, was))
    if made:
        after = patch(dict(flat_now), back)
        held = []
        for (tid, aspect), v in after.items():
            if tid in made:
                continue
            ref = None
            if aspect in ("in", "subject") and v in made:
                ref = v
            elif aspect == "link" and isinstance(v, dict) and (v.get("from") in made or v.get("to") in made):
                ref = v.get("from") if v.get("from") in made else v.get("to")
            elif aspect.startswith("line:") and isinstance(v, dict) and v.get("reply_to") in made:
                ref = v["reply_to"]
            if ref:
                held.append(f"{tid} ({aspect}) points at {ref}")
        made_lines = {aspect[5:] for tid, aspect, v in facts if aspect.startswith("line:") and before[(tid, aspect)] is ABSENT}
        for (tid, aspect), v in after.items():
            if aspect.startswith("line:") and isinstance(v, dict) and v.get("reply_to") in made_lines:
                held.append(f"line {aspect[5:]} replies to {v['reply_to']}")
        if held:
            raise CannotUndo("something made later points at what it made: " + "; ".join(held[:4]))
    else:
        made_lines = {aspect[5:] for tid, aspect, v in facts if aspect.startswith("line:") and before[(tid, aspect)] is ABSENT}
        if made_lines:
            after = patch(dict(flat_now), back)
            held = [f"line {aspect[5:]} replies to {v['reply_to']}" for (tid, aspect), v in after.items()
                    if aspect.startswith("line:") and isinstance(v, dict) and v.get("reply_to") in made_lines]
            if held:
                raise CannotUndo("a later line answers one it made: " + "; ".join(held[:4]))
    return back


# ---------------------------------------------------------------- two people in one text

def text_at_event(log, w, sid, index):
    """The text of subject `sid` as it stood when the world had `index` events: what someone who last read it then was
    shown. Read from the log. -> the text, or None when the log cannot say (they read it before the log began)."""
    began = _began(log)
    if began is None or index < began:
        return None
    first = int(w.events[index]["id"][1:]) if index < len(w.events) else None
    key, val = (sid, "text"), ABSENT
    for rec, _ in log.records():
        if first is not None and any(int(str(p.get("e", "e0"))[1:] or 0) >= first for p in rec.get("parts") or () if p.get("e")):
            break
        for tid, aspect, v in facts_of(rec):
            if (tid, aspect) == key:
                val = v if v is ABSENT else whole(v, val)
    return "" if val is ABSENT else val


_BEGAN = {}


def _began(log):
    """How many events the world held when its log began (the genesis record says)."""
    key = str(log.path)
    if key not in _BEGAN:
        try:
            with open(log.path, "rb") as f:
                m = re.search(rb'"events_before": (\d+)', f.read(600))
            _BEGAN[key] = int(m.group(1)) if m else None
        except OSError:
            return None
    return _BEGAN[key]


def merge3(base, theirs, mine):
    """Two changes to one text, each made from `base`: -> (text holding both, None), or (None, why) when they changed
    the same lines. A line is the unit: in prose a paragraph, in a lens a word of a part. Changes to different lines
    both land; the same change made twice lands once."""
    import difflib
    B, T, M = base.split("\n"), theirs.split("\n"), mine.split("\n")

    def edits(X):
        out = []
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, B, X, autojunk=False).get_opcodes():
            if tag == "equal":
                continue
            if tag == "replace" and i2 - i1 == j2 - j1:      # line for line: each line is its own change
                out += [(i1 + k, i1 + k + 1, (X[j1 + k],)) for k in range(i2 - i1) if B[i1 + k] != X[j1 + k]]
            else:
                out.append((i1, i2, tuple(X[j1:j2])))
        return out
    et, em = edits(T), edits(M)
    for a in em:
        for b in et:
            if a == b:
                continue
            (a1, a2, _), (b1, b2, _) = a, b
            if a1 == a2 and b1 == b2:
                clash = a1 == b1                      # two insertions at one place: which comes first is a choice
            elif a1 == a2:
                clash = b1 < a1 < b2
            elif b1 == b2:
                clash = a1 < b1 < a2
            else:
                clash = a1 < b2 and b1 < a2
            if clash:
                lo, hi = min(a1, b1) + 1, max(a2, b2, min(a1, b1) + 1)
                return None, (f"line {lo}" if hi <= lo else f"lines {lo}-{hi}") + " of what you read"
    out, pos = [], 0
    for i1, i2, rep in sorted(set(et) | set(em)):
        out += B[pos:i1]
        out += rep
        pos = i2
    out += B[pos:]
    return "\n".join(out), None


# ---------------------------------------------------------------- checks

def roundtrip(w):
    """Does a world rebuilt from its facts say the same facts? -> (same, [differences])."""
    flat = flatten(w)
    again = flatten(materialize(flat, {"ids": getattr(w, "_ids", 0), "eseq": getattr(w, "_eseq", 0)}))
    d = diff(flat, again)
    return not d, [f"{tid} {aspect}: {'gone' if v is ABSENT else 'differs'}" for tid, aspect, v in d]


def derived_gap(w):
    """What `apply` could not rebuild exactly from facts: how many boxes in flows differ once re-derived, and whether
    revisions are kept (they are not: a revision is a count, not a fact). For the report, not a failure."""
    m = materialize(flatten(w), {"ids": getattr(w, "_ids", 0)})
    boxes = sum(1 for nid, n in w.nodes.items() if nid in m.nodes
                and (n.get("x"), n.get("y"), n.get("w"), n.get("h")) != tuple(m.nodes[nid].get(k) for k in "xywh"))
    order = sum(1 for fid, f in w.nodes.items() if f["type"] == "surface" and fid in m.nodes
                and [k["id"] for k in w.children(fid)] != [k["id"] for k in m.children(fid)])
    return {"nodes": len(w.nodes), "boxes differ": boxes, "orders differ": order}


def check(w, log):
    """-> (ok, lines). The log replayed must equal the world flattened; each fact's `before` must be what the log held."""
    out, ok = [], True
    flat, n, bad, state = {}, 0, 0, f"{0:016x}"
    for rec, _ in log.records():
        n += 1
        for p in rec.get("parts") or ():
            for row in p.get("facts") or ():
                key = (row[0], row[1])
                if h(flat.get(key, ABSENT)) != row[2]:
                    bad += 1
                    if bad <= 5:
                        out.append(f"  record {rec['seq']}: {row[0]} {row[1]} was not what the record says it was before")
        state = _move(state, flat, facts_of(rec))
        patch(flat, facts_of(rec))
        if rec.get("state") and rec["state"] != state:
            bad += 1
            if bad <= 5:
                out.append(f"  record {rec['seq']}: the digest it wrote is not the digest of the log replayed to it")
            state = rec["state"]
    now = flatten(w)
    d = diff(flat, now)
    ok = not d and not bad
    out.insert(0, f"{n} records replayed: {len(flat)} facts; the world says {len(now)}; {len(d)} differ; {bad} broken links between records")
    out += [f"  differs: {tid} {aspect}" for tid, aspect, _v in d[:10]]
    same, why = roundtrip(w)
    ok = ok and same
    out.append(f"round trip (a world rebuilt from its facts says the same facts): {'yes' if same else 'NO'}")
    out += ["  " + x for x in why[:10]]
    out.append(f"derived, re-derived: {derived_gap(w)}")
    return ok, out


def stats(log):
    import collections
    n, size, causes, aspects, biggest = 0, collections.Counter(), collections.Counter(), collections.Counter(), []
    last = 0
    for rec, end in log.records():
        n += 1
        b = end - last
        last = end
        kind = (rec["parts"][0]["cause"].split(":")[0] if rec.get("parts") else "empty")
        kind = "genesis" if kind.startswith("genesis") else "outside" if kind == "outside" else "command"
        size[kind] += b
        causes[kind] += 1
        for tid, aspect, v in facts_of(rec):
            aspects[aspect.split(":")[0]] += 1
        if kind == "command":
            biggest.append((b, rec["seq"], rec.get("words", "")[:60]))
    biggest.sort(reverse=True)
    return {"records": n, "by kind": dict(causes), "bytes by kind": dict(size),
            "mean command bytes": int(size["command"] / max(1, causes["command"])),
            "facts by aspect": dict(aspects.most_common(14)), "largest commands": biggest[:5]}


def _load(world):
    import export_docs
    return export_docs.load(world)


def main(argv):
    if len(argv) < 2 or argv[0] not in ("begin", "check", "stats", "tail", "show"):
        print(__doc__.split("\n\n")[1])
        return 2
    cmd, world = argv[0], argv[1]
    path = SESSIONS / f"{world}.pickle"
    log = Log(log_path(path))
    if cmd == "begin":
        import explore
        lock = SESSIONS / f"{world}.lock"
        explore.take_lock(lock)
        try:
            import pickle
            desk = pickle.loads(path.read_bytes())
            seq = genesis(desk, path, by="house", why=" ".join(argv[2:]))
        finally:
            explore.release_lock(lock)
        print(f"{log.path.name}: record {seq} holds the world as it is ({log.path.stat().st_size / 1e6:.1f} MB)")
        return 0
    if not log.exists():
        print(f"{world} has no log ({log.path.name}); python store.py begin {world} starts one")
        return 1
    if cmd == "check":
        ok, lines = check(_load(world).world, log)
        print("\n".join(lines))
        print("ok" if ok else "NOT ok")
        return 0 if ok else 1
    if cmd == "stats":
        print(json.dumps(stats(log), ensure_ascii=False, indent=1))
        return 0
    if cmd == "tail":
        n = int(argv[2]) if len(argv) > 2 else 10
        recs = [rec for rec, _ in log.records()][-n:]
        for rec in recs:
            nf = sum(len(p.get("facts") or ()) for p in rec.get("parts") or ())
            causes = ",".join(dict.fromkeys(p["cause"].split(":")[0] for p in rec.get("parts") or ()))
            print(f"{rec['seq']:>6} {rec.get('at', '')[11:]} {rec.get('by', ''):<10} {nf:>3} facts [{causes}] {rec.get('words', '')[:90]}")
        return 0
    if cmd == "show":
        rec = log.find(lambda r: r["seq"] == int(argv[2]))
        print(json.dumps(rec, ensure_ascii=False, indent=1)[:20000] if rec else f"no record {argv[2]}")
        return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
