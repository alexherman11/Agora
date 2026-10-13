"""table: the row table (8 Oct 2026, step 4 of the grammar unification).

Every word a host reads is a row: its name, the host it is said in, and its slots, each with a type from one small
list. The hosts kept their own tables (moo.REGISTRY's args strings, scene.WORDS's shapes, DeskKnife.USAGE,
knife.TERMS, the kind notes); this module reads them into one table and gives it back to the world as row sources,
so a lens can show the desk's own vocabulary and `rows slots host=lens` lists what a lens word takes:

    rows words [host=verb|command|lens|term|kind]     host word form slots doc
    rows slots [host=... word=...]                    host word slot type needed doc
    rows kinds                                        kind is shape things props declared

A kind is a word said by making a thing, so a kind's row is its aspects. Two readings, both shown: what its things
actually carry (`props`: `status 157/158 text, owner 118/158 person`, the regular core and the ragged tail), and
what its note declares, one slot per line in the lens's own line form (`seats : number`, `host : person`, `due :
date, needed`). A kind describes and never enforces (kinds.py): a value that is not the declared kind is kept, and
the receipt says it is unusual (`remarks`); on a stored verb or lens the same types are checked when it is saved.

The slot types are the expression language's value kinds (number, text, date, time, duration, bool), plus the kinds
of thing a line names: thing, query, expr, prose, name, person, choice (a|b|c), flag, place."""
import re

import expr as X

TYPES = ("thing", "query", "expr", "prose", "name", "number", "date", "time", "duration", "bool", "person", "choice", "flag", "place", "text", "word")
_PLACEHOLDER = {"str": "prose", "text": "prose", "id": "thing", "surface": "thing", "card": "thing", "thing": "thing", "names": "person",
                "selection": "query", "selection | row source": "query", "words or selection": "query", "expr": "expr",
                "n": "number", "number": "number", "dx": "number", "dy": "number", "x": "number", "y": "number", "w": "number", "h": "number",
                "weight": "number", "YYYY-MM-DD": "date", "date": "date", "name": "name", "frame": "name", "role": "name", "handle": "name",
                "part": "name", "kind": "name", "actor": "person", "event": "thing", "verb": "name", "value": "text", "k": "name", "v": "text",
                "cNN": "thing", "lNN": "thing", "m id": "thing", "handle label": "prose", "label": "prose", "command": "prose", "desk command": "prose",
                "tracks: 1 3 3 1 | 1fr fit 2fr": "word", "min": "number", "max": "number", "start": "number", "gesture": "choice",
                "interpretation": "name", "inputs": "text", "a kind made here": "name"}
NEEDED = re.compile(r"^\[.*\]$")


class Slot:
    __slots__ = ("name", "type", "needed", "doc")

    def __init__(self, name, type_, needed=True, doc=""):
        self.name, self.type, self.needed, self.doc = name, type_, needed, doc

    def row(self, host, word):
        return {"host": host, "word": word, "slot": self.name, "type": self.type, "needed": "yes" if self.needed else "", "doc": self.doc}

    def __repr__(self):
        return f"{self.name}:{self.type}" + ("" if self.needed else "?")


def type_of_placeholder(ph):
    """`<surface>` -> thing, `<str>` -> prose, `a|b|c` -> choice, `YYYY-MM-DD` -> date, `<n>ch` -> number ..."""
    s = ph.strip().strip("<>").strip()
    if s in _PLACEHOLDER:
        return _PLACEHOLDER[s]
    if "|" in s and not s.startswith("<"):
        return "choice"
    if re.fullmatch(r"\d+(?:\.\d+)?", s):
        return "number"
    if re.fullmatch(r"[a-z]+", s):
        return "word"
    return "text"


def slots_of_args(args):
    """A verb's args string (`into=<surface> | before=<id> ... [one=1]`, `kind=note|task title=<str> [text=<str>]`) as slots.
    `k=<ph>` is a named slot typed by its placeholder; `a=x | b=y` alternatives are each optional; `[...]` is optional;
    `k=v ...` or `any other key` is an open slot for a prop."""
    out, seen = [], set()
    text = args or ""
    open_ = "any other key" in text or "k=v" in text
    text = re.sub(r"\[any other key[^\]]*\]", "", text)
    alternatives = " | " in text
    for m in re.finditer(r"(\[?)([a-z_][\w-]*)=((?:<[^>]*>|[^\s\]|]+)(?:\|(?:<[^>]*>|[^\s\]|]+))*)(\]?)", text):
        opt, key, val, close = m.groups()
        if key in seen or key == "k":
            continue
        seen.add(key)
        choice = "|" in val and not val.startswith("<")
        t = "choice" if choice else type_of_placeholder(val)
        needed = not (opt or alternatives or close) and "[" + key not in text
        out.append(Slot(key, t, needed, val if choice else ""))
    if open_:
        out.append(Slot("<prop>", "text", False, "any other key is a prop"))
    return out


def slots_of_shape(shape):
    """A lens word's shape (`fold ["<handle label>"] [open] [float] [handle <role>]`, `clamp [last] <n>`,
    `let <name> = <expr> [when <expr> | otherwise]`) as slots: each placeholder a slot, each bare word a flag."""
    out, seen = [], set()
    body = shape.split(" ", 1)[1] if " " in shape else ""
    for m in re.finditer(r"(\[)?\s*(?:(\w[\w-]*)\s+)?(<[^>]*>|\w[\w|-]*)(?:\s*\])?", body):
        opt, lead, tok = m.groups()
        if tok.startswith("<"):
            name = (lead or tok.strip("<>").split(":")[0].split("|")[0]).strip()
            t = type_of_placeholder(tok)
        elif "|" in tok:
            name, t = lead or tok.split("|")[0], "choice"
        elif tok in ("=", "when", "otherwise", "do", "of", "as", "step", "to", "last", "x", "y"):
            if tok in ("last", "otherwise"):
                name, t = tok, "flag"
            else:
                continue
        else:
            name, t = tok, "flag"
        if name in seen or not name:
            continue
        seen.add(name)
        out.append(Slot(name, t, not opt and t != "flag", tok if t == "choice" else ""))
    return out


# ---------------------------------------------------------------------------------------------------------------------
# the hosts' own tables, read into rows
# ---------------------------------------------------------------------------------------------------------------------
def _verb_rows(desk):
    import knife
    import moo
    import verbs
    rows = []
    for name, v in moo.REGISTRY.items():
        rows.append(("verb", name, f"do {name} <{'|'.join(v.kinds)}> {v.args}".strip(), [Slot("target", "thing", True, ", ".join(v.kinds))] + slots_of_args(v.args), v.doc))
    for name, (form, doc) in knife.PAIR_DOC.items():
        rows.append(("verb", name, f"{name} {form}", [Slot("A", "thing"), Slot("B", "thing")] + slots_of_args(form), doc))
    for s in verbs.all_verbs(desk.world):
        words = [x.strip() for x in str(s["title"]).split("|") if x.strip()]
        text = s.get("text") or ""
        need = sorted({int(m) for m in re.findall(r"\$(\d+)", text)})
        slots = [Slot(f"${k}", "text", True) for k in need] + ([Slot("$*", "prose", False, "the rest of the line")] if "$*" in text else [])
        doc = next((l.strip("# ").strip() for l in text.splitlines() if l.strip().startswith("#")), "")
        rows.append(("verb", words[0], f"{words[0]} " + " ".join(f"<{k}>" for k in need) + (" ..." if "$*" in text else ""), slots, doc + f" (a verb made here, {s['id']})"))
    return rows


def _command_rows(desk):
    rows = []
    for cmd, usage in getattr(desk, "USAGE", {}).items():
        rows.append(("command", cmd, usage, slots_of_shape(usage), ""))
    return rows


def _lens_rows():
    import scene
    return [("lens", word, shape, slots_of_shape(shape), "") for word, (shape, _f) in scene.WORDS.items()]


def _term_rows():
    import knife
    rows = []
    for t in knife.TERMS:
        name = t.rstrip(":")
        asp = knife.ASPECTS.get(name)
        rows.append(("term", t, f"{t}<value>", [Slot("value", "text")], "reads " + ", ".join(sorted(asp)) if asp else "reads nothing a verb declares"))
    rows.append(("term", "k op v", "<aspect or prop> = != < > <= >= <value>", [Slot("aspect", "name"), Slot("op", "choice", True, "=|!=|<|>|<=|>="), Slot("value", "text")],
                 "any aspect or prop compared, typed as the lens types values (8 Oct)"))
    rows.append(("term", "?words", "?word+word", [Slot("words", "text")], "title, text or tags contain every word"))
    rows.append(("term", "hidden", "hidden", [], "more than 5% covered"))
    rows.append(("term", "settled", "settled", [], "its work is over: status is one of " + " ".join(knife.SETTLED)
                 + ", or a promise that has ended; -settled is what is live"))
    return rows


def declared(w, kind, at=None):
    """The slots a kind note declares, one per line in the lens's line form: `seats : number`, `due : date, needed`,
    `status : open|doing|done`. Any other line is prose. -> [Slot]; [] for a kind with no note or no such lines."""
    import kinds
    s = kinds.note_for(w, kind, at)[0]
    if s is None:
        return []
    import tree
    out = []
    for node in tree.lines(s.get("text") or ""):      # 9 Oct: the one indentation reader strips the ` # ` comment
        m = re.match(r"^([a-z][\w-]*)\s*:\s*([A-Za-z][\w|-]*)\s*(?:,\s*(needed))?$", node.text)
        if not m:
            continue
        name, t, needed = m.groups()
        if t not in TYPES and "|" not in t:
            continue
        out.append(Slot(name, "choice" if "|" in t else t, bool(needed), t if "|" in t else ""))
    return out


def observed(w, kind):
    """What things of a kind actually carry: {prop: (count, total, usual type)}, over the placed things of that kind,
    the usual type being the value kind most of them have (expr.typed)."""
    import moo
    things = [n for n in w.nodes.values() if n["parent"] and moo.kind_of(w, n["id"]) == kind]
    total = len(things)
    counts, kinds_ = {}, {}
    for n in things:
        props = (n.get("props") if n["type"] == "surface" else (w.subjects.get(n.get("subject")) or {}).get("props")) or {}
        for k, v in props.items():
            if str(v).strip() == "":
                continue
            counts[k] = counts.get(k, 0) + 1
            kk = X.typed(v).kind
            d = kinds_.setdefault(k, {})
            d[kk] = d.get(kk, 0) + 1
    out = {}
    for k, c in counts.items():
        usual = max(kinds_[k].items(), key=lambda kv: kv[1])[0]
        out[k] = (c, total, usual)
    return out, total


def kind_rows(desk):
    import kinds
    w = desk.world
    rows = []
    for name in sorted(kinds.known(w) | set(kinds.notes(w))):
        obs, total = observed(w, name)
        top = sorted(obs.items(), key=lambda kv: -kv[1][0])[:8]
        props = ", ".join(f"{k} {c}/{t} {u}" for k, (c, t, u) in top)
        decl = declared(w, name)
        rows.append({"kind": name, "is": kinds.built_on(w, name) or "", "shape": kinds.shape(w, name), "things": total, "props": props,
                     "declared": ", ".join(repr(s) for s in decl)})
    return rows


def word_rows(desk):
    out = []
    for host, word, form, slots, doc in _command_rows(desk) + _verb_rows(desk) + _lens_rows() + _term_rows():
        out.append({"host": host, "word": word, "form": form, "slots": " ".join(repr(s) for s in slots), "doc": doc})
    for r in kind_rows(desk):
        slots = declared(desk.world, r["kind"]) or [Slot(k, u, False) for k, (c, t, u) in sorted(observed(desk.world, r["kind"])[0].items(), key=lambda kv: -kv[1][0])[:8]]
        out.append({"host": "kind", "word": r["kind"], "form": f"create kind={r['kind']} title=<str> " + " ".join(f"{s.name}=<{s.type}>" for s in slots),
                    "slots": " ".join(repr(s) for s in slots), "doc": __import__("kinds").describe(desk.world, r["kind"])[:120]})
    return out


def slot_rows(desk):
    out = []
    for host, word, form, slots, doc in _command_rows(desk) + _verb_rows(desk) + _lens_rows() + _term_rows():
        out += [s.row(host, word) for s in slots]
    w = desk.world
    for r in kind_rows(desk):
        decl = {s.name: s for s in declared(w, r["kind"])}
        obs, total = observed(w, r["kind"])
        for name, s in decl.items():
            c = obs.get(name, (0, total, ""))[0]
            out.append({"host": "kind", "word": r["kind"], "slot": name, "type": s.type, "needed": "yes" if s.needed else "", "doc": (s.doc + f" ({c}/{total} have it)").strip()})
        for name, (c, t, u) in sorted(obs.items(), key=lambda kv: -kv[1][0]):
            if name not in decl:
                out.append({"host": "kind", "word": r["kind"], "slot": name, "type": u, "needed": "", "doc": f"observed: {c}/{t} have it, usually {u}"})
    return out


# ---------------------------------------------------------------------------------------------------------------------
# a kind describes, it never enforces: the receipt remarks on an unusual value
# ---------------------------------------------------------------------------------------------------------------------
_KINDS = {"number": {"number"}, "date": {"date", "time"}, "time": {"time"}, "duration": {"duration"}, "bool": {"bool"},
          "text": None, "prose": None, "word": None, "name": None, "expr": None, "query": None, "place": None}


def fits(w, slot, value):
    """Does a stored value fit a declared slot? None when the type says nothing about values (text, name ...)."""
    v = str(value)
    if slot.type == "choice":
        return v in slot.doc.split("|")
    if slot.type == "thing":
        return v in w.nodes or v in w.subjects
    if slot.type == "person":
        import persons
        return not persons.on(w) or bool(persons.today(w, v)) or persons.is_pid(w, v)
    if slot.type == "flag":
        return v in ("1", "yes", "true", "0", "no", "false")
    want = _KINDS.get(slot.type)
    if want is None:
        return None
    return X.typed(v).kind in want


def remarks(desk, n0):
    """~ lines for a receipt: a value set on a thing whose kind declares the slot, when the value is not of the
    declared kind. The value is kept; the kind only describes."""
    import moo
    w = desk.world
    out, seen = [], set()
    for e in w.events[n0:]:
        if e.get("undone") or e["verb"] not in ("create", "prop", "edit", "rekind"):
            continue
        for i in [e.get("target")] + list(e.get("changed") or []):
            if i not in w.nodes or i in seen:
                continue
            seen.add(i)
            kind = moo.kind_of(w, i)
            import kinds
            import verbs
            here = verbs.room_holding(w, i)          # 9 Oct (step 7): the kind note nearest the thing describes it
            note, others = kinds.note_for(w, kind, here)
            if others:
                out.append(f"~ {len(others) + 1} kind notes are titled {kind} ({', '.join((w.appearances_of(x['id']) or [x['id']])[0] for x in [note] + others)}); "
                           f"none is nearer to {i}, so {(w.appearances_of(note['id']) or [note['id']])[0]} is read; retitle or move one so the name means one thing here")
            decl = declared(w, kind, here)
            if not decl:
                continue
            n = w.nodes[i]
            props = (n.get("props") if n["type"] == "surface" else (w.subjects.get(n.get("subject")) or {}).get("props")) or {}
            args = e.get("args") or {}
            for s in decl:
                if s.name not in props or (e["verb"] != "create" and s.name not in args):
                    continue
                ok = fits(w, s, props[s.name])
                if ok is False:
                    out.append(f"~ {s.name}={props[s.name]} kept; a {kind}'s {s.name} is usually a {s.type}" + (f" ({s.doc})" if s.type == "choice" else "") + f" (kind {kind} says so; it describes, it does not refuse)")
            if e["verb"] == "create":
                missing = [s.name for s in decl if s.needed and s.name not in props]
                if missing:
                    out.append(f"~ a {kind} usually has {', '.join(missing)}; this one has none yet (kind {kind} says so)")
    return out
