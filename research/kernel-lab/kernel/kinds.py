"""EDITING THE KERNEL (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
The kernel changes only to give every world a general capability: a word, a check, a kind of fact any app, module or
person can use. It never names its tenants: no app, module, person, kind or field name appears in this code except the
kernel's own (word, rule, kind, grant, person, ...). If your change needs `if kind == "..."`, a person's name or one app's
field, stop: the missing piece is a general word (a kind's policy, a rule step, a reading). Build that, or put it on the
Board. Names already here are debt (research/source-edits/SOURCE-AUDIT-KERNEL.md lists them); take them out when you can.

Shapes: what a thing must have for a word, a lens or a list to reach it (Alex approved 28 Oct 2026;
research/kinds-lab/fresh-words-reach-kinds.md).

A shape is a list of needs, one grammar for kinds and words alike:

    start                       has a start (not empty)
    game=yes                    a marker: game is yes (someone said so on purpose)
    start|starts                one of these spellings; the first is the name the shape uses
    kind|post_kind=event        kind or post_kind is event
    kind=taskboard-task|task    one of these values

A kind is a named shape (make kind=kind name=event needs="title start|starts"), and may extend others
(name=meeting extends=event needs=place): a child keeps every need of its parents and may add more. Kinds are for
people, lenses and lists (rows event, of tag:event, kinds <thing>, actions <thing>). A kind with no needs and no extends
is closed: only things whose own kind is that word are one, as before.

A word says the shape its code reads: acts_on=<kind> (that kind's needs) and needs="<needs>" (its own). One check, at
every place a word meets its thing, refuses a thing that lacks one, naming what. A word with no shape reaches anything,
as every word did before shapes. Classifying never adds power: grants and rules still match a thing's own kind.

Kinds all the way down (Alex approved 29 Oct 2026; research/kinds-lab/kinds-all-the-way-down.md): "kind is what it's
made of, state is the values of its parts". A need may say its part's kind (start:time likes:upvote); the bottom is a
value kind (the kernel's text number time yes-no link person thing, or a declared one: name=upvote value=number). An
aspect is a part of a kind when a kind the thing is says so, or its name is a kind's name or synonym (aliases=);
otherwise it is loose. A word acting on a value kind reaches anything with such a part, and is told which (part=).
"""
import re

from .kernel import Refused

TIME = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$")
ID_LIKE = re.compile(r"^[a-z]{2,4}\d+$")


def _number(v):
    try:
        float(str(v))
        return str(v).strip().casefold() not in ("nan", "inf", "-inf", "infinity", "-infinity")
    except ValueError:
        return False


# the bottom: value kinds the kernel holds, each with its check. Everything else is declared in the world.
BASE = {
    "text": lambda k, v: bool(str(v).strip()),
    "number": lambda k, v: _number(v),
    "time": lambda k, v: bool(TIME.match(str(v))),
    "yes-no": lambda k, v: str(v).casefold() in ("yes", "no", "true", "false"),
    "link": lambda k, v: bool(re.match(r"^https?://\S+$", str(v))),
    "person": lambda k, v: k.state.get(str(v), "kind") == "person",
    "thing": lambda k, v: bool(ID_LIKE.match(str(v))),
}
COLON_FAMILIES = {"contact", "claim", "like", "vote", "member", "in", "is", "sees"}
# a part is never one of the kernel's own facts (who made it, where it lives, what it is)
SKIP_PREFIX = ("in:", "member:", "label.", "help.", "is.", "allows.", "seen.", "pin")

NAME = re.compile(r"^[a-z_][a-z0-9_.-]{0,40}$")
KIND_NAME = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
VALUE = re.compile(r"^[^\s|=\"']{1,60}$")
# what never fits a kind by its shape: the dictionary, authority and the machinery of views
NOT_FITTED = {"person", "agent", "module", "grant", "word", "invite", "world", "place", "group", "kit", "web-layout",
              "paint-report", "kind", "aspect", "rule", "lens", "part-style", "component", "topic", "view-preference",
              "widget", "button", "theme"}


def a_(word):
    return f"a{'n' if str(word)[:1] in 'aeiou' else ''} {word}"


class Need:
    """One need: names (spellings, the first is the shape's own), for a marker the values it may have, and for a typed
    part the kind its value is (start:time). Need.met is the untyped check; Kinds.met adds the part's kind."""
    __slots__ = ("names", "values", "kind")

    def __init__(self, names, values=None, kind=None):
        self.names, self.values = tuple(names), (tuple(values) if values else None)
        self.kind = kind

    def text(self):
        return ("|".join(self.names) + ("=" + "|".join(self.values) if self.values else "")
                + (":" + self.kind if self.kind else ""))

    def met(self, row):
        """The spelling that meets it on this row, or None."""
        for n in self.names:
            v = row.get(n)
            if v in (None, ""):
                continue
            if self.values is None or str(v) in self.values:
                return n
        return None

    def says(self):
        """How a refusal names it: start, a start or starts, kind event."""
        if self.values:
            return f"{' or '.join(self.names)} {' or '.join(self.values)}"
        return " or ".join(self.names) + (f" ({a_(self.kind)})" if self.kind else "")

    def __eq__(self, o):
        return isinstance(o, Need) and (self.names, self.values, self.kind) == (o.names, o.values, o.kind)

    def __hash__(self):
        return hash((self.names, self.values, self.kind))


class Unreadable(Need):
    """A stored shape this kernel can't read (a kit from a newer world, a rolled-back kernel). Nothing meets it, so the
    word reaches nothing and the kind admits nothing by shape: fail closed (kernel review C4, 28 Oct: an unreadable
    needs= was swallowed into none, and the word then reached everything)."""
    __slots__ = ("raw",)

    def __init__(self, raw):
        super().__init__(["(unreadable)"])
        self.raw = str(raw or "")[:120]

    def met(self, row):
        return None

    def says(self):
        return f"a shape this kernel can read (needs={self.raw})"

    def text(self):
        return self.raw

    def __eq__(self, o):
        return isinstance(o, Unreadable) and o.raw == self.raw

    def __hash__(self):
        return hash(("unreadable", self.raw))


def parse(text):
    """'title start|starts:time kind|post_kind=event' -> [Need]; refuses what the kernel could not read."""
    out = []
    for raw in str(text or "").split():
        tok, kind = raw, None
        if "=" not in tok and ":" in tok:
            tok, _, kind = tok.rpartition(":")
            kind = kind.casefold()
        names, _, values = tok.partition("=")
        ns = [n for n in names.casefold().split("|") if n]
        vs = [v for v in values.split("|") if v] if values else None
        if (not ns or any(not NAME.match(n) for n in ns) or ("=" in tok and (not vs or any(not VALUE.match(v) for v in vs)))
                or (kind is not None and (not KIND_NAME.match(kind) or set(ns) & COLON_FAMILIES))):
            # contact:<person>, claim:<…>: the kernel's own colon aspects are never a part's name (they read as one)
            raise Refused(f"{raw} is not a need: a need is an aspect (start), spellings of one (start|starts), a "
                          f"part of a kind (start:time, likes:upvote), or a marker (game=yes, kind|post_kind=event)")
        out.append(Need(ns, vs, kind))
    return out


def text_of(needs):
    return " ".join(n.text() for n in needs)


def merged(needs):
    """The same needs once each, in order."""
    return list(dict.fromkeys(needs))


class Kinds:
    def __init__(self, k):
        self.k = k
        self._seen = -1
        self._cache = {}
        self.decls = []

    def _fresh(self):
        n = len(self.k.log.records)
        if n != self._seen:
            self._seen, self._cache = n, {}
            self.decls = [(t, a) for t, a in list(self.k.state.things.items())
                          if a.get("kind") == "kind" and a.get("name") and not a.get("forgotten")]

    def _lives(self, t):
        return (self.k.groups_of(t) or [self.k.place])[0]

    # ------------------------------------------------------------------ kinds: named shapes
    def decl(self, kind, group=None):
        """(id, facts) of the declaration of `kind` nearest `group` (its own scope, then upward to the place), or None.
        Two at one level: the later wins (a steward hides one)."""
        self._fresh()
        key = ("decl", kind, group)
        if key not in self._cache:
            found = None
            for g in self.k.up(group or self.k.place):
                here = [(t, a) for t, a in self.decls if self._lives(t) == g]
                # its own name first; a synonym (aliases=) names the same kind (Alex, 29 Oct: "a synonym in the dictionary")
                hits = ([(t, a) for t, a in here if a.get("name") == kind]
                        or [(t, a) for t, a in here if kind in str(a.get("aliases") or "").split()])
                if hits:
                    found = hits[-1]
                    break
            self._cache[key] = found
        return self._cache[key]

    def canon(self, kind, group=None):
        """The kind's own name for a name or a synonym of it; any other word as it is."""
        d = self.decl(kind, group) if kind else None
        return d[1].get("name") if d else kind

    # ------------------------------------------------------------------ value kinds and parts
    def base_of(self, kind, group=None, _seen=None):
        """The kernel value kind at the bottom of `kind` (upvote value=number -> number), or None for a kind made of
        parts, a closed kind or no kind."""
        if kind in BASE:
            return kind
        d = self.decl(kind, group)
        if not d or not d[1].get("value"):
            return None
        seen = set(_seen or ()) | {d[1].get("name")}
        v = str(d[1]["value"])
        return None if v in seen else self.base_of(v, group, seen)

    def value_chain(self, kind, group=None):
        """[upvote, number]: a value kind and what its value is, down to the bottom."""
        out = []
        while kind and kind not in out:
            out.append(kind)
            if kind in BASE:
                break
            d = self.decl(kind, group)
            kind = str(d[1].get("value") or "") if d else ""
        return out

    def is_value(self, kind, group=None):
        """Whether words acting on `kind` reach parts: a value kind, not the bare person or thing (whose own things
        are people and things)."""
        return kind not in ("person", "thing") and self.base_of(kind, group) is not None

    def value_ok(self, kind, value, group=None):
        """Whether a value reads as `kind`: a value kind's check, or (a kind made of parts) the id of its own thing,
        which is checked when a word reaches it, as the reader sees it."""
        if value in (None, ""):
            return False
        base = self.base_of(kind, group)
        if base:
            return bool(BASE[base](self.k, value))
        return bool(ID_LIKE.match(str(value)))

    def met(self, n, row, group=None):
        """The spelling that meets need `n` on this row, its part's kind too, or None."""
        m = n.met(row)
        if m is None or not n.kind:
            return m
        for name in n.names:
            v = row.get(name)
            if v not in (None, "") and (n.values is None or str(v) in n.values) and self.value_ok(n.kind, v, group):
                return name
        return None

    def aspect_kind(self, row, aspect, group=None, fitted=None):
        """(kind, how) for one aspect of a thing: the kind a kind it is gives that part (likes:upvote), else the kind
        its name names (upvote=, or a synonym), when the value reads as one; (None, why) when it is loose."""
        from .words import RESERVED
        v = row.get(aspect)
        if v in (None, "") or aspect in RESERVED or aspect in ("id", "rev", "as", "groups", "by", "title", "name") \
                or aspect.startswith(SKIP_PREFIX):
            return None, None
        for kd in (fitted if fitted is not None else [x for x, _ in self.kinds_of(row, group)]):
            for n in (self.shape(kd, group) or []) + self.optional(kd, group):
                if n.kind and aspect in n.names:
                    if self.value_ok(n.kind, v, group):
                        return self.canon(n.kind, group), f"{a_(kd)} says {aspect}:{n.kind}"
                    return None, f"{a_(kd)} says {aspect}:{n.kind}, and {str(v)[:40]} isn't {a_(n.kind)}"
        named = aspect if aspect in BASE else (self.canon(aspect, group) if self.decl(aspect, group) else None)
        if named:
            if self.value_ok(named, v, group):
                return named, (f"named {aspect}" if named == aspect else f"{aspect} is a name for {named}")
            return None, f"{str(v)[:40]} isn't {a_(named)}"
        return None, "loose"

    def _part_is(self, part_kind, want, group):
        return (part_kind == want or self._descends(part_kind, want, group)
                or want in self.value_chain(part_kind, group))

    def parts_of(self, row, kind, group=None):
        """The aspects of a thing that are parts of `kind` (its likes, for upvote), in the thing's own order."""
        want = self.canon(kind, group)
        fitted = [x for x, _ in self.kinds_of(row, group)]
        out = []
        for aspect in list(row):
            pk, _ = self.aspect_kind(row, aspect, group, fitted)
            if pk and self._part_is(pk, want, group):
                out.append(aspect)
        return out

    def shape(self, kind, group=None, _seen=None):
        """[Need] a thing must have to be a `kind`: its parents' needs, then its own. None for a kind with no needs and
        no parents (closed), or none declared."""
        self._fresh()
        key = ("shape", kind, group)
        if _seen is None and key in self._cache:
            return self._cache[key]
        seen = set(_seen or ()) | {kind}
        d = self.decl(kind, group)
        if not d:
            out = None
        else:
            t, a = d
            parents = [p for p in str(a.get("extends") or "").split() if p]
            needs = []
            for p in parents:
                if p in seen:
                    continue                     # refused when made; a world copied from elsewhere stays readable
                needs += self.shape(p, group, seen) or [Need(["kind"], [p])]
            try:
                needs += parse(a.get("needs"))
            except Refused:
                needs.append(Unreadable(a.get("needs")))   # fail closed: nothing fits a kind it can't read
            out = merged(needs) if (parents or a.get("needs")) else None
        if _seen is None:
            self._cache[key] = out
        return out

    def optional(self, kind, group=None):
        """[Need] a kind's things MAY have (has="priority:number when:time"), its parents' first: typed parts that
        say what an aspect is without making every thing need it (Alex, 29 Oct: "a video without a location is still a
        video"; the board's fields=). Never part of fitting."""
        self._fresh()
        key = ("optional", kind, group)
        if key not in self._cache:
            out, todo, seen = [], [kind], set()
            while todo:
                kd = todo.pop(0)
                if kd in seen:
                    continue
                seen.add(kd)
                d = self.decl(kd, group)
                if d:
                    out = self._parsed(d[1].get("has")) + out
                    todo += [p for p in str(d[1].get("extends") or "").split() if p]
            self._cache[key] = merged(out)
        return self._cache[key]

    def is_open(self, kind, group=None):
        """Whether things of other kinds can be a `kind`: it has a shape, or another kind extends it."""
        self._fresh()
        d = self.decl(kind, group)
        return (bool(self.shape(kind, group)) or any(kind in str(a.get("extends") or "").split() for t, a in self.decls)
                or bool(d and str(d[1].get("aliases") or "").split()))     # things made under a synonym are one too

    def parents(self, kind, group=None):
        d = self.decl(kind, group)
        return [p for p in str(d[1].get("extends") or "").split() if p] if d else []

    def fits(self, row, kind, group=None):
        """Why a thing (a row as the reader sees it) is a `kind`, or None. Its own kind always is one."""
        own = row.get("kind")
        if not own:
            return None
        if own == kind:
            return a_(kind)
        if own not in NOT_FITTED and self.canon(own, group) == self.canon(kind, group) and self.decl(kind, group):
            return f"{a_(own)}, which is {a_(self.canon(kind, group))}"      # one kind, another name (aliases=)
        if self._descends(own, kind, group):
            return f"{a_(own)}, so {a_(kind)}"
        if own in NOT_FITTED:
            return None
        needs = self.shape(kind, group)
        if not needs or self.missing(row, needs, group):
            return None
        if self.parents(kind, group):
            # a child kind holds what is declared one, never what merely has its shape (Alex, 28 Oct: "Children by
            # declaration"; the trials made all 300 board events meetings, and a window's at= a place). Its own kind or
            # a kind extending it says so above; otherwise `mark <thing> <kind>` says so: is.<kind>=yes.
            marked = [a[3:] for a, v in row.items() if a.startswith("is.") and str(v) in ("yes", "True")]
            hit = next((m for m in marked if m == kind or self._descends(m, kind, group)), None)
            if hit is None:
                return None                      # a mark on a grandchild counts for every kind between (review M7)
            return f"marked {a_(kind)}" if hit == kind else f"marked {a_(hit)}, so {a_(kind)}"
        return "has " + ", ".join(self.met(n, row, group) + (f"={row.get(self.met(n, row, group))}" if n.values else "")
                                  for n in needs)

    def _descends(self, kind, ancestor, group, seen=None):
        seen = seen or set()
        for p in self.parents(kind, group):
            if p == ancestor:
                return True
            if p not in seen:
                seen.add(p)
                if self._descends(p, ancestor, group, seen):
                    return True
        return False

    def open_kinds(self, group=None):
        """The kinds with a shape that a thing in `group` may fit, the kind needing most first."""
        self._fresh()
        key = ("open", group)
        if key not in self._cache:
            names = dict.fromkeys(a["name"] for t, a in self.decls)
            shaped = [(kd, self.shape(kd, group)) for kd in names]
            self._cache[key] = [kd for kd, s in sorted((x for x in shaped if x[1]), key=lambda x: -len(x[1]))]
        return self._cache[key]

    def kinds_of(self, row, group=None):
        """[(kind, why)] for a thing: its own kind, its own kind's parents, then every kind whose shape it has, the
        kind needing most first (the more specific)."""
        out, seen = [], set()

        def add(kd, why):
            if kd and kd not in seen and why:
                seen.add(kd)
                out.append((kd, why))
        add(row.get("kind"), a_(row.get("kind")))
        if row.get("kind") not in NOT_FITTED:
            same = self.canon(row.get("kind"), group)
            if same != row.get("kind"):
                add(same, f"{a_(row.get('kind'))}, which is {a_(same)}")
        for p in self._ancestors(row.get("kind"), group):
            add(p, f"{a_(row.get('kind'))}, so {a_(p)}")
        for kd in self.open_kinds(group):
            if kd not in seen:
                add(kd, self.fits(row, kd, group))
        return out

    def _ancestors(self, kind, group):
        out, todo = [], list(self.parents(kind, group))
        while todo:
            p = todo.pop(0)
            if p not in out and p != kind:
                out.append(p)
                todo += self.parents(p, group)
        return out

    def filled(self, row, kind, group=None):
        """A row read as a `kind`: a thing that spells a need another way (starts) also shows the kind's name for it
        (start), and `as` says which. Only for a reading under that kind; the thing's facts are never changed."""
        needs = self.shape(kind, group) or []
        out, said = dict(row), []
        for n in needs:
            if len(n.names) > 1 and out.get(n.names[0]) in (None, ""):
                m = self.met(n, row, group)
                if m:
                    out[n.names[0]] = row[m]
                    said.append(f"{n.names[0]} as {m}")
        if said:
            out["as"] = ", ".join(said)
        return out

    def spellings_of(self, name):
        """{name} and every other spelling any declared kind joins it with (start -> start, starts). For the fence: a
        painted row may show a kind's name for a fact spelled otherwise, so a change to either is a change."""
        self._fresh()
        key = ("spellings", name)
        if key not in self._cache:
            out = {name}
            for t, a in self.decls:
                try:
                    needs = parse(a.get("needs"))
                except Refused:
                    continue
                for n in needs:
                    if name in n.names:
                        out |= set(n.names)
            self._cache[key] = out
        return self._cache[key]

    def spelled_otherwise(self, row, key, group=None):
        """The other spelling this thing already uses for `key`, under a kind it fits (as the reader sees it), or
        None. set refuses to add a second spelling beside it."""
        if row.get(key) not in (None, ""):
            return None
        for kd in self.open_kinds(group):
            if not self.fits(row, kd, group):
                continue
            for n in self.shape(kd, group) or []:
                if key in n.names:
                    m = self.met(n, row, group)
                    if m and m != key:
                        return m, kd
        return None

    # ------------------------------------------------------------------ words: the shape each one reads
    def word_shape(self, entry):
        """(own needs, acts_on) for a dictionary entry, or None when it says none (it reaches anything). acts_on is met
        the way a list or a lens meets a kind (its own kind, a kind extending it, or its shape); own needs are what the
        word's code reads besides (trials 28 Oct: a chat word refused things whose own kind is chat)."""
        acts_on, own = entry.get("acts_on"), entry.get("needs")
        if not acts_on and not own:
            return None
        try:
            needs = parse(own)
        except Refused:
            needs = [Unreadable(own)]                     # fail closed, never "no needs"
        return needs, acts_on

    def missing(self, row, needs, group=None):
        return [n for n in needs if not self.met(n, row, group)]

    def _lacks(self, row, entry):
        """(what the thing lacks for this word as [Need or kind name], needs counted, the parts it reaches) or None
        when it has no shape."""
        shape = self.word_shape(entry)
        if not shape:
            return None
        own, acts_on = shape
        group = entry.get("lives") or self.k.place
        lack, parts = [], []
        count = len(own)
        if acts_on:
            ks = self.shape(acts_on, group)
            count += len(ks or [])
            if not self.fits(row, acts_on, group):
                if self.is_value(acts_on, group):
                    # a word on upvotes reaches anything with an upvote (Alex, 29 Oct: "something with an upvote kind
                    # could be upvoted by verbs that work on upvotes"); it is told which part
                    parts = self.parts_of(row, acts_on, group)
                    if not parts:
                        lack.append(Need([acts_on]))
                else:
                    # has the shape but isn't one: a child kind's members are declared (mark <thing> <kind>), so what
                    # it lacks is being one (kinds-intelligence review K7: urgent.page paged an unmarked note)
                    lack += (self.missing(row, ks, group) if ks else []) or [Need(["kind"], [acts_on])]
        lack += self.missing(row, own, group)
        return lack, count, parts

    def check_word(self, actor, entry, target, tx=None, part=None):
        """The one check, at every place a word meets its thing: refuse a thing that lacks what the word reads. The
        thing is read as the actor sees it, so a refusal names the word's needs, never a hidden fact. A word on a value
        kind that reaches the thing through a part returns that part's aspect (part= picks one of several)."""
        if not target or not isinstance(target, str) or not self.word_shape(entry):
            return None
        if tx is not None and target in tx.made:
            return None                             # made by this same act: its facts are not in the world yet
        row = self.k.shown(actor.person, target)
        if row is None:
            return None                             # the caller says "no thing called …" in its own words
        lack, _, parts = self._lacks(row, entry)
        own, acts_on = self.word_shape(entry)
        word = entry.get("word")
        if not lack:
            if not parts:
                return None
            name = row.get("title") or row.get("name") or row.get("label") or target
            if part:
                if part not in parts:
                    raise Refused(f"{word} acts on {a_(acts_on)}; {name}'s {part} isn't one (its {acts_on} "
                                  f"part{'s are' if len(parts) > 1 else ' is'} {', '.join(parts)})",
                                  kept=f"{word}: part={part} isn't {a_(acts_on)} part of {target}")
                return part
            if len(parts) > 1:
                raise Refused(f"{name} has {len(parts)} {acts_on} parts ({', '.join(parts)}); say which: part={parts[0]}",
                              kept=f"{word}: {target} has {len(parts)} {acts_on} parts; say part=")
            return parts[0]
        bad = next((n for n in lack if isinstance(n, Unreadable)), None)
        if bad:
            raise Refused(f"{word}'s shape can't be read by this kernel (needs={bad.raw}); nothing was done. A steward "
                          f"can word-set {word} needs= to fix it")
        name = row.get("title") or row.get("name") or row.get("label") or target
        what = a_(acts_on) if acts_on else "things with " + ", ".join(n.says() for n in own)
        if acts_on and own:
            what += " with " + ", ".join(n.says() for n in own)
        lacks = ", ".join(n.says() for n in lack)
        raise Refused(f"{word} acts on {what}; {name} ({target}, {a_(row.get('kind'))}) has no {lacks}",
                      kept=f"{word} acts on {what}; {target} has no {lacks}")   # the log: no title, no kind

    def reaches(self, actor, entry, target):
        """(rank, why) when the word reaches this thing, else None. Rank orders plain words: the thing's own kind
        (or one it extends) first, then the shape needing most."""
        row = self.k.shown(actor.person, target) if target else None
        if row is None:
            return None
        got = self._lacks(row, entry)
        if got and any(isinstance(n, Unreadable) for n in got[0]):
            # a shape this kernel can't read: it still competes (as a word with no needs), so a plain word asks or
            # refuses loudly, never silently runs another word (kernel review round 2: done ran task.done instead)
            return (0, 0), "a shape this kernel can't read"
        if not got or got[0]:
            return None
        own, acts_on = self.word_shape(entry)
        kind = row.get("kind")
        group = entry.get("lives") or self.k.place
        mine = bool(acts_on and (acts_on == kind or self._descends(kind, acts_on, group))) or any(
            "kind" in n.names and n.values and kind in n.values for n in own)
        if got[2]:
            return (1, -got[1]), f"{acts_on} (its {', '.join(got[2])})"      # through a part (likes, an upvote)
        return (0 if mine else 1, -got[1]), acts_on or "its needs"

    def check_shape_text(self, text, what="needs"):
        """Refuse needs= the kernel could not read; returns them tidied."""
        return text_of(parse(text)) if str(text or "").strip() else ""

    def check_acts_on(self, name, group=None):
        """Refuse acts_on naming a kind nothing here declares or is (a typo would refuse everything, silently)."""
        name = str(name or "").casefold()
        if not KIND_NAME.match(name):
            raise Refused(f"acts_on={name}: a kind name (acts_on=event)")
        if name in BASE and name != "thing":
            return name                                     # the kernel's value kinds: a word on any time, any link
        if not self.decl(name, group) and not any(a.get("kind") == name for a in list(self.k.state.things.values())):
            raise Refused(f"acts_on={name}: no kind {name} is declared here and nothing is one (kinds lists them)")
        return name

    # ------------------------------------------------------------------ declaring and changing kinds
    def validate_decl(self, actor, kv, group, old=None, t=None):
        """A kind declaration a make or set would leave: readable, made by a leader when it has a shape, never on the
        kernel's own kinds, one per name in a scope, no cycle, and (for a change) only wider. Tidies kv in place."""
        from .words import RESERVED_KINDS
        self._fresh()
        name = str(kv.get("name") if "name" in kv else (old or {}).get("name") or "")
        if "needs" in kv:
            kv["needs"] = self.check_shape_text(kv["needs"])
        if "extends" in kv:
            ps = [p.casefold() for p in str(kv["extends"]).split()]
            bad = [p for p in ps if not KIND_NAME.match(p)]
            if bad:
                raise Refused(f"extends= names kinds, space-separated: {', '.join(bad)} is not one")
            kv["extends"] = " ".join(ps)
        if "has" in kv:
            kv["has"] = self.check_shape_text(kv["has"])
            if any(n.values for n in parse(kv["has"])):
                raise Refused("has= says parts a thing may have (priority:number when:time); a marker (game=yes) "
                              "belongs in needs=")
        if "value" in kv:
            kv["value"] = str(kv["value"] or "").casefold().strip()
            if kv["value"] and not KIND_NAME.match(kv["value"]):
                raise Refused(f"value= names one kind its value is: {', '.join(BASE)}, or a value kind declared here")
        if "aliases" in kv:
            kv["aliases"] = " ".join(dict.fromkeys(str(kv["aliases"] or "").casefold().replace(",", " ").split()))
            bad = [x for x in kv["aliases"].split() if not KIND_NAME.match(x)]
            if bad:
                raise Refused(f"aliases= are other names for this kind, space-separated: {', '.join(bad)} is not one")
        after = dict(old or {}, **kv)
        shaped = bool(after.get("needs") or after.get("extends") or after.get("value") or after.get("aliases")
                      or after.get("has"))
        scope = group or self.k.place
        kernel_kinds = RESERVED_KINDS | NOT_FITTED
        if shaped and (name in kernel_kinds or name in BASE
                       or set(str(after.get("extends") or "").split()) & kernel_kinds):
            # trials 28 Oct: a shape on said put a member's notes among JEFF's lines (house reads rows said)
            raise Refused(f"{name if name in kernel_kinds | set(BASE) else 'that'} is one of the kernel's own kinds; "
                          f"what it is can't be widened or extended")
        if after.get("value"):
            if after.get("needs") or after.get("extends") or after.get("has"):
                raise Refused(f"{name} is a value kind (value={after['value']}): it ends in a value, so it has no "
                              f"needs, has or extends; a kind made of parts says needs=\"likes:{name}\"")
            if self.base_of(after["value"], scope) is None or after["value"] == name:
                raise Refused(f"value={after['value']}: a value kind's value is one of {', '.join(BASE)}, or a value "
                              f"kind declared here (make kind=kind name=upvote value=number)")
        for x in str(after.get("aliases") or "").split():
            if x == name or x in kernel_kinds or x in BASE:
                raise Refused(f"aliases={x}: {'that is its own name' if x == name else 'one of the kernel own kinds'}")
            other = self.decl(x, scope)
            if other and other[0] != t and self._lives(other[0]) == scope:
                raise Refused(f"{x} already names {other[1].get('name')} here ({other[0]}); one name, one kind")
        if name and old is None:
            other = self.decl(name, scope)
            if other and other[1].get("name") != name and self._lives(other[0]) == scope:
                raise Refused(f"{name} is another name for {other[1].get('name')} here ({other[0]}); use it, or "
                              f"extend it (extends={other[1].get('name')})")
        typed = [n.kind for n in self._parsed(after.get("needs")) + self._parsed(after.get("has")) if n.kind]
        for kd in typed:
            # a part may be one of the kernel's own kinds (a said, a group, a widget) without declaring it
            if kd not in BASE and kd not in kernel_kinds and not self.decl(kd, scope) and kd != name:
                raise Refused(f"a part's kind {kd} is declared nowhere here; make kind=kind name={kd} first (a value "
                              f"kind: value=number), or use one of {', '.join(BASE)}")
        shadows = False
        if old is None:
            same = [d for d, a in self.decls if a.get("name") == name and self._lives(d) == scope]
            if same:
                # one declaration per name per scope, closed ones too (values review V1, ran: a member's later closed
                # `kind=kind name=issue` won decl() over the steward's, and with it whatever else it said)
                raise Refused(f"{name} is declared here already ({same[-1]}); set {same[-1]} changes it, and a kind "
                              f"only widens (trials 28 Oct: a second declaration silently replaced the first)")
            shadows = self.decl(name, scope) is not None     # a nearer declaration hides an outer one in this scope
        if not shaped and not shadows and not (old and (old.get("needs") or old.get("extends"))):
            return
        person = actor.person
        if not (self.k.is_steward(person) or (scope != self.k.place and self.k.is_leader(person, scope))):
            if shadows and not shaped:
                raise Refused(f"{name} is already declared for {self.k.name(scope)} ({self.decl(name, scope)[0]}); a "
                              f"second one here would change what it is for everyone in it, so its leaders declare it")
            raise Refused(f"a kind with needs or extends changes what words reach for everyone in {self.k.name(scope)}"
                          f"; its leaders declare it (a steward for the place)")
        # no cycle: a kind can't extend itself, however far round
        todo, seen = list(str(after.get("extends") or "").split()), set()
        while todo:
            p = todo.pop()
            if p == name:
                raise Refused(f"{name} would extend itself (through {', '.join(sorted(seen)) or name}); nothing was done")
            if p not in seen:
                seen.add(p)
                todo += self.parents(p, scope)
        for p in str(after.get("extends") or "").split():
            if not self.decl(p, scope):
                raise Refused(f"extends={p}: no kind {p} is declared here; make kind=kind name={p} first")
        if old is None:
            return
        if "name" in kv and kv["name"] != old.get("name"):
            users = self.users(old.get("name"), scope, person)
            if users:
                raise Refused(f"{old.get('name')} is named by {', '.join(users[:5])}; a kind keeps its name (make a new "
                              f"kind for a new meaning)")
        if "value" in kv and str(old.get("value") or "") != str(kv.get("value") or "") and old.get("value"):
            users = self.users(name, scope, person)
            if users:
                raise Refused(f"{name}'s value is {old['value']}, and {', '.join(users[:5])} rely on it; make a new kind "
                              f"for another value")
        narrower = self._narrower(old, after, scope)
        if narrower:
            users = self.users(name, scope, person)
            if users:
                raise Refused(f"that would make {name} need more ({', '.join(narrower)}), and {', '.join(users[:5])} "
                              f"rely on it; a kind only widens (make a new kind for the narrower meaning)")
        dropped = self._dropped(old, after, scope)
        words = []
        for e, a in list(self.k.state.things.items()):
            if a.get("kind") == "word" and a.get("acts_on") == name and not a.get("forgotten"):
                try:
                    says = {x for n in parse(a.get("needs")) for x in n.names}
                except Refused:
                    says = set()
                if set(dropped) - says:              # a word that needs it itself keeps reading it safely
                    words.append(a.get("word") if self.k.shown(person, e) is not None else "a word you can't see")
        if dropped and words:
            # trials 28 Oct: dropping status from issue let issue.close reach a lane; a word's code may read it
            raise Refused(f"{', '.join(words[:5])} act on {name} and may read {', '.join(dropped)}; give them that "
                          f"need first (word-set <word> needs=\"{' '.join(dropped)}\"), then {name} can drop it")

    def _expand(self, a, scope):
        needs = []
        for p in str(a.get("extends") or "").split():
            needs += self.shape(p, scope) or [Need(["kind"], [p])]
        try:
            needs += parse(a.get("needs"))
        except Refused:
            pass
        return merged(needs)

    def _narrower(self, old, new, scope):
        """What `new` would require that `old` did not. Opening a closed kind only adds what fits (its own things
        still are one), so it is never narrower (trials 28 Oct: opening the board's event was refused)."""
        if not (old.get("needs") or old.get("extends")):
            return []
        try:
            parse(old.get("needs"))
        except Refused:
            return []        # a shape this kernel couldn't read admitted nothing, so any readable one is no narrower
                             # and the steward can repair it (kernel review round 2, F7)
        before, after = self._expand(old, scope), self._expand(new, scope)
        out = []
        for n in after:
            # n is no narrower if some old need already implies it: same or fewer spellings, same or fewer values
            # and a part's kind: start:time is narrower than start (a typed part admits fewer values)
            if not any(set(o.names) <= set(n.names) and (n.values is None or (o.values and set(o.values) <= set(n.values)))
                       and (n.kind is None or o.kind == n.kind) for o in before):
                out.append(n.text())
        return out

    def _dropped(self, old, new, scope):
        """The aspects `old` needed that `new` needs under no spelling at all."""
        after = {x for n in self._expand(new, scope) for x in n.names}
        return [n.names[0] for n in self._expand(old, scope) if not set(n.names) & after]

    # ------------------------------------------------------------------ telling kinds apart, finding the same one
    def _parts_sig(self, needs, group):
        """{part: (its kind, marker values)}: one key per need, spellings any kind joins counted as one."""
        out = {}
        for n in needs or []:
            if isinstance(n, Unreadable):
                continue
            key = min(set().union(*(self.spellings_of(x) for x in n.names)))
            out[key] = (self.canon(n.kind, group) if n.kind else None, n.values)
        return out

    def alike(self, needs, group=None, reader=None, skip=None, value=None):
        """[(kind, score, shared, only theirs, told apart by)]: declared kinds made of the same parts as `needs`,
        closest first; for a value kind, the others with the same value at the bottom. No model: names through
        spellings, parts' kinds. The same name with different part kinds tells two apart (a game's score:points, a
        survey's score:rating, Alex 29 Oct: "same name does not mean same thing"): that part isn't shared, and it is
        said, so they're never offered as the same kind."""
        self._fresh()
        mine = self._parts_sig(needs, group)
        base = self.base_of(value, group) if value else None
        out = []
        for t, a in self.decls:
            nm = a.get("name")
            if nm == skip or (reader and self.k.shown(reader, t) is None):
                continue
            if value:
                if a.get("value") and self.base_of(nm, group) == base:
                    out.append((nm, 1.0, [f"its value is {a_(base)}"], [], []))
                continue
            theirs = self._parts_sig((self.shape(nm, group) or []) + self.optional(nm, group), group)
            same_name = [x for x in mine if x in theirs and mine[x][1] == theirs[x][1]]
            apart = [f"{x} ({mine[x][0]} here, {theirs[x][0]} there)" for x in same_name
                     if mine[x][0] and theirs[x][0] and mine[x][0] != theirs[x][0]]
            shared = [x for x in same_name if not (mine[x][0] and theirs[x][0] and mine[x][0] != theirs[x][0])]
            # parts that are only prose (source:text, import_reviewed_by:text) say where a thing came from, not what it
            # is: sharing only those isn't being the same kind (live, 29 Oct: charter matched soul on provenance alone)
            if not shared or all(mine[x][0] == "text" for x in shared):
                continue
            score = len(shared) / len(set(mine) | set(theirs))
            if score >= 0.5:
                out.append((nm, round(score, 2), shared, sorted(set(theirs) - set(mine)), apart))
        return sorted(out, key=lambda x: (-x[1], x[0]))

    def alike_note(self, actor, kv, group=None):
        """What make says when a new kind is made of the same parts as one already here: the maker (a person or an
        agent) can name that one instead (aliases=) or extend it. Said, never refused."""
        name = str(kv.get("name") or "")
        try:
            needs = parse(kv.get("needs")) + parse(kv.get("has"))
        except Refused:
            return ""
        parents = str(kv.get("extends") or "").split()
        inherited = set()
        for p in parents:
            theirs = (self.shape(p, group) or []) + self.optional(p, group)
            needs = theirs + needs
            inherited |= set(self._parts_sig(theirs, group))
        # not: a parent or its ancestors; one told apart by a part's kind; one made only of what a parent already has
        # (extending video answers clip, video under another name)
        hits = [h for h in self.alike(needs, group, actor.person, skip=name, value=kv.get("value"))
                if h[0] not in parents and not any(self._descends(p, h[0], group) for p in parents) and not h[4]
                and not (inherited and set(h[2]) | set(h[3]) <= inherited)]
        if not hits:
            return ""
        bits = [f"{h[0]} ({', '.join(h[2][:4])}" + (f"; it also has {', '.join(h[3][:3])}" if h[3] else "") + ")"
                for h in hits[:3]]
        return (f"\n~ {name} is made of the same parts as " + "; ".join(bits) + ". If it's the same kind, aliases= on "
                f"that one names it; if it has notably more, extends= it (alike {name} says more)")

    @staticmethod
    def _parsed(text):
        try:
            return parse(text)
        except Refused:
            return []

    def users(self, kind, group=None, reader=None, words_only=False):
        """What names this kind by name: words (acts_on), kinds (extends) and lenses (tag:). Things the reader can't
        see are counted, never named."""
        out, hidden = [], 0
        pat = re.compile(r"\btag:" + re.escape(str(kind)) + r"\b")
        for t, a in list(self.k.state.things.items()):
            if a.get("forgotten"):
                continue
            if a.get("kind") == "word" and a.get("acts_on") == kind:
                said = a.get("word")
            elif words_only:
                continue
            elif a.get("kind") == "kind" and kind in str(a.get("extends") or "").split():
                said = f"kind {a.get('name')}"
            elif a.get("kind") == "kind" and (str(a.get("value") or "") == kind or any(
                    n.kind == kind for n in self._parsed(a.get("needs")) + self._parsed(a.get("has")))):
                said = f"kind {a.get('name')}"                   # made of it: likes:upvote, or value=upvote
            elif a.get("kind") in ("lens", "component") and pat.search(str(a.get("text") or "")):
                said = f"lens {a.get('name') or t}"
            else:
                continue
            if reader and self.k.shown(reader, t) is None:
                hidden += 1
            else:
                out.append(said)
        if hidden:
            out.append(f"{hidden} thing{'s' if hidden != 1 else ''} you can't see")
        return out


# ---------------------------------------------------------------------- words
def mark(k, actor, st, entry, tx, group, saw=None):
    """mark <thing> <kind>: set the kind's markers on a thing that has its other needs, or say what is missing."""
    t = st.target
    words = st.words.split()
    if not words:
        raise Refused("mark <thing> <kind>: say which kind (mark dk5 game)")
    kind = words[0].casefold()
    g = (k.groups_of(t) or [group or k.place])[0]
    needs = k.kinds.shape(kind, g)
    if not needs:
        raise Refused(f"no kind {kind} with needs is declared here; mark sets a kind's markers (kinds lists the kinds)")
    row = k.shown(actor.person, t) or {}
    name = row.get("title") or row.get("name") or t
    markers = [n for n in needs if n.values]
    plain = [n for n in needs if not n.values]
    lack = k.kinds.missing(row, plain, g)
    if lack:
        raise Refused(f"a {kind} needs {', '.join(n.says() for n in lack)}; {name} has none, so it can't be marked one",
                      kept=f"a {kind} needs {', '.join(n.says() for n in lack)}; {t} has none, so it can't be marked one")
    if any(n.names == ("kind",) or "kind" in n.names for n in markers if not n.met(row)):
        raise Refused(f"a {kind} is made as one (its kind says so); mark sets markers, never a thing's kind")
    todo = {n.names[0]: n.values[0] for n in markers if not n.met(row)}
    if k.kinds.parents(kind, g) and k.kinds.fits(row, kind, g) is None:
        todo[f"is.{kind}"] = "yes"                 # a child kind's members are declared (kinds.fits)
    if not todo:
        return {"text": f"{name} is a {kind} already; nothing changed"}
    from .words import set_
    st.kv, st.words = dict(todo), ""
    out = set_(k, actor, st, entry, tx, group, saw=saw)       # set's own fences, grants and history
    return {"text": out["text"].replace("ok set", "ok mark", 1) + f" · {name} is a {kind} now"}


def words_for(k, actor, st, entry, tx, group, saw=None):
    """actions <thing>: every word that reaches it, by the kind it acts on, most specific first; then the lenses."""
    from . import lines as L
    t = st.target or (st.words.split() or [""])[0]
    if not L.ID.fullmatch(str(t)):
        hits = k.named(actor, st.words)
        if len(hits) > 1:
            raise Refused(f"{len(hits)} things are called {st.words}: " + ", ".join(f"{h} (a {kd})" for h, kd in hits[:4]))
        t = hits[0][0] if hits else None
    row = k.shown(actor.person, t) if t else None
    if row is None:
        raise k.no_such(st.words or st.target)
    name = row.get("title") or row.get("name") or t
    found, anything = [], 0
    for e in k.entries():
        a = k.state.things[e]
        if a.get("word_kind") not in ("do", "see") or k.shown(actor.person, e) is None:
            continue
        if not re.match(r"\[?<", str(a.get("takes") or "")):
            continue
        g = (k.groups_of(t) or [k.place])[0]
        if not k.may(actor, k.entry(e), t, g):
            continue
        hit = k.kinds.reaches(actor, a, t)
        if hit and any(isinstance(n, Unreadable) for n in (k.kinds.word_shape(a) or ([], None))[0]):
            hit = None              # it competes for plain words (so they ask, not swap), but isn't offered: it refuses
        if hit:
            found.append((hit[0], hit[1], a.get("word"), (str(a.get("help") or "").splitlines() or [""])[0]))
        elif not k.kinds.word_shape(a):
            anything += 1
    found.sort()
    lines, rows, last = [f"{name} ({t}), a {row.get('kind')}:"], [], None
    for rank, on, w, usage in found:
        if on != last:
            lines.append(f"  as {a_(on)}:" if on != "its needs" else "  by what it has:")
            last = on
        lines.append(f"    {w} · {usage[:100]}")
        rows.append({"word": w, "as": on, "usage": usage})
    g = (k.groups_of(t) or [k.place])[0]
    lenses = []
    for lt, la in list(k.state.things.items()):
        if la.get("kind") != "lens" or la.get("forgotten"):
            continue
        for tag in re.findall(r"\btag:([a-z0-9_-]+)", str(la.get("text") or "")):
            if k.kinds.fits(row, tag, g) and k.shown(actor.person, lt) is not None:
                lenses.append(f"{la.get('name') or lt} (as {tag})")
                break
    if lenses:
        lines.append("  lenses that show it: " + ", ".join(lenses[:8]))
    lines.append(f"  and {anything} words that take any thing (help lists them)")
    return {"text": "\n".join(lines), "rows": rows}


def kinds_reading(k, actor, st):
    """kinds <thing>: what it is, nearest first, each with why."""
    from . import lines as L
    first = st.words.split()[0]
    t = first if L.ID.fullmatch(first) else None
    if t is None:
        hits = k.named(actor, st.words)
        if len(hits) > 1:
            raise Refused(f"{len(hits)} things are called {st.words}: " + ", ".join(f"{h} (a {kd})" for h, kd in hits[:4]))
        t = hits[0][0] if hits else None
    a = k.shown(actor.person, t) if t else None
    if a is None:
        raise k.no_such(first)
    g = (k.groups_of(t) or [k.place])[0]
    found = k.kinds.kinds_of(a, g)
    name = a.get("title") or k.name(t)
    lines = [f"{name} ({t}):"] + [f"  {kd} · {why}" for kd, why in found]
    parts, loose = [], []
    if a.get("kind") not in NOT_FITTED:
        fitted = [kd for kd, _ in found]
        for aspect in a:
            pk, how = k.kinds.aspect_kind(a, aspect, g, fitted)
            if pk:
                parts.append(f"{aspect} ({a_(pk)})")
            elif how == "loose":
                loose.append(aspect)
            elif how:
                loose.append(f"{aspect} ({how})")
    if parts:
        lines.append("  parts: " + ", ".join(parts))
    if loose:
        lines.append("  loose (no kind gives them one): " + ", ".join(loose))
    return {"text": "\n".join(lines), "rows": [{"kind": kd, "why": why} for kd, why in found]}


def alike_word(k, actor, st, entry, tx, group, saw=None):
    """alike <kind>: the kinds here made of the same parts, closest first, with what they share and what only they
    have. What an agent reads before naming a kind, so the same thing isn't made twice."""
    name = (st.words.split() or [""])[0].casefold()
    if st.target and k.state.get(st.target, "kind") == "kind":
        name = k.state.get(st.target, "name")
    group = group or k.place
    d = k.kinds.decl(name, group)
    if not name or not d:
        raise Refused(f"alike <kind>: no kind {name or '(none said)'} is declared here (kinds lists the kinds)")
    own = d[1]["name"]
    hits = k.kinds.alike((k.kinds.shape(own, group) or []) + k.kinds.optional(own, group), group, actor.person,
                         skip=own, value=d[1].get("value"))
    if not hits:
        return {"text": f"no kind here is made of the same parts as {own}", "rows": []}
    lines, rows = [f"made of the same parts as {own}:"], []
    for nm, score, shared, theirs, apart in hits[:8]:
        rel = (" · extends it" if k.kinds._descends(nm, own, group) else
               " · it extends this" if k.kinds._descends(own, nm, group) else "")
        lines.append(f"  {nm} · {int(score * 100)}% · shares {', '.join(shared[:6])}"
                     + (f" · only {nm} has {', '.join(theirs[:4])}" if theirs else "")
                     + (f" · told apart by {', '.join(apart[:3])}" if apart else "") + rel)
        rows.append({"kind": nm, "score": score, "shared": shared, "only_there": theirs, "apart": apart})
    return {"text": "\n".join(lines), "rows": rows}


def aspects_word(k, actor, st, entry, tx, group, saw=None):
    """aspects [loose|suggest]: every aspect on things you can see, as a part of which kind or loose, with how many
    things say it, the most used first. What one thing alone says (a setting's knobs) and what the kernel computes for
    the reader (likes) are counted apart: they aren't vocabulary. Many things sharing one loose aspect is a kind nobody
    has named yet; `aspects suggest` proposes kinds for them from their values (no model)."""
    from .words import RESERVED_KINDS
    words = st.words.split()
    only_loose, suggest = "loose" in words, "suggest" in words
    seen, per_kind, counts = {}, {}, {}
    things = 0
    for t, a in list(k.state.things.items()):
        if t == "world" or a.get("forgotten") or a.get("kind") in NOT_FITTED or a.get("kind") in RESERVED_KINDS:
            continue
        row = k.shown(actor.person, t)
        if row is None:
            continue
        things += 1
        own = row.get("kind")
        counts[own] = counts.get(own, 0) + 1
        g = (k.groups_of(t) or [k.place])[0]
        fitted = [x for x, _ in k.kinds.kinds_of(row, g)]
        for aspect in row:
            pk, how = k.kinds.aspect_kind(row, aspect, g, fitted)
            if pk is None and how is None:
                continue
            c = seen.setdefault(aspect, {"n": 0, "kinds": {}, "as": {}, "computed": 0})
            c["n"] += 1
            c["kinds"][own] = c["kinds"].get(own, 0) + 1
            if a.get(aspect) in (None, ""):
                c["computed"] += 1                  # the kernel fills it for this reader (sealed like counts)
            key = pk or "loose"
            c["as"][key] = c["as"].get(key, 0) + 1
            if not pk and a.get(aspect) not in (None, ""):
                per_kind.setdefault(own, {}).setdefault(aspect, []).append((t, str(a.get(aspect))))
    if suggest:
        return _suggest(k, actor, per_kind, counts, group or k.place)
    rows = []
    for aspect, c in seen.items():
        loose_n = c["as"].get("loose", 0)
        if only_loose and not loose_n:
            continue
        rows.append({"aspect": aspect, "things": c["n"], "loose": loose_n,
                     "as": {x: n for x, n in c["as"].items() if x != "loose"},
                     "kinds": dict(sorted(c["kinds"].items(), key=lambda x: -x[1])[:4]),
                     "one_thing": c["n"] == 1, "computed": c["computed"] == c["n"]})
    # the most used first: how many things, then how many kinds
    rows.sort(key=lambda r: (r["one_thing"] or r["computed"], -r["loose"], -r["things"], -len(r["kinds"]), r["aspect"]))
    words_ = [r for r in rows if not (r["one_thing"] or r["computed"])]
    loose_words = [r for r in words_ if r["loose"]]
    one = [r["aspect"] for r in rows if r["one_thing"] and not r["computed"]]
    computed = [r["aspect"] for r in rows if r["computed"]]
    lines = [f"{len(words_)} aspects shared by things you can see ({things} things); {len(loose_words)} are loose "
             f"somewhere" + ("; aspects suggest proposes kinds for them" if loose_words else "")]
    for r in words_[:24]:
        kinds_ = ", ".join(str(x) for x in r["kinds"])
        as_ = ", ".join(f"{a_(x)} {n}" for x, n in r["as"].items())
        lines.append(f"  {r['aspect']} · {r['things']} things ({kinds_})"
                     + (f" · loose on {r['loose']}" if r["loose"] else "") + (f" · part: {as_}" if as_ else ""))
    if len(words_) > 24:
        lines.append(f"  and {len(words_) - 24} more (rows of this reading list them all)")
    if one:
        lines.append(f"  said by one thing only ({len(one)}, a setting's own knobs): {', '.join(one[:12])}"
                     + (" …" if len(one) > 12 else ""))
    if computed:
        lines.append(f"  computed for you, never stored ({len(computed)}): {', '.join(computed[:8])}")
    return {"text": "\n".join(lines), "rows": rows}


HEXISH = re.compile(r"^[0-9a-f]{7,64}$")


def KERNEL_KINDS():
    from .words import RESERVED_KINDS
    return RESERVED_KINDS | NOT_FITTED


def parse_safe(text):
    try:
        return parse(text)
    except Refused:
        return []


def _suggest(k, actor, per_kind, counts, group):
    """For each kind with loose aspects on two or more of its things: the parts their values already say (all times,
    all numbers, all links, yes or no, all people, all pointing at one kind of thing, long prose), and what needs
    judgment (a few repeated words like a stage, people written as names, hashes, two aspects that always agree)."""
    people = {str(a.get("name") or "").casefold() for t, a in k.state.things.items() if a.get("kind") == "person"}
    out_rows, lines, prereq = [], [], set()
    order = sorted(per_kind, key=lambda kd: -sum(len(v) for v in per_kind[kd].values()))
    for kd in order:
        aspects = {x: v for x, v in per_kind[kd].items() if len({t for t, _ in v}) >= 2}
        if not aspects or counts.get(kd, 0) < 2:
            continue
        typed, judge = [], []
        for x, pairs in sorted(aspects.items(), key=lambda p: -len(p[1])):
            vals = [v for _, v in pairs]
            kind_of = None
            for b in ("time", "number", "link", "yes-no", "person"):
                if all(BASE[b](k, v) for v in vals):
                    kind_of = b
                    break
            if kind_of is None and all(ID_LIKE.match(v) and v in k.state.things for v in vals):
                targets = {str(k.state.get(v, "kind")) for v in vals}
                if len(targets) == 1:
                    kind_of = targets.pop()
                    if kind_of not in BASE and kind_of not in KERNEL_KINDS() and not k.kinds.decl(kind_of, group):
                        prereq.add(kind_of)
                else:
                    judge.append(f"{x} points at {len(targets)} kinds of thing ({', '.join(sorted(targets))[:60]})")
                    continue
            if kind_of:
                typed.append((x, kind_of, len(vals)))
                continue
            distinct = sorted(set(vals))
            if all(HEXISH.match(v) for v in distinct):
                judge.append(f"{x} holds hashes ({len(distinct)}): one value kind for them")
            elif sum(len(v) for v in vals) / len(vals) > 40:
                typed.append((x, "text", len(vals)))
            elif sum(v.casefold() in people for v in distinct) * 2 >= len(distinct):   # mostly people (and agents)
                judge.append(f"{x} holds people written as names ({', '.join(distinct[:4])}): it should hold the person")
            elif all(all(BASE["person"](k, w) for w in v.split()) for v in distinct):
                judge.append(f"{x} holds lists of people ({len(distinct)} different): a list part")
            elif all(all(ID_LIKE.match(w) for w in v.split()) for v in distinct):
                judge.append(f"{x} holds lists of things ({len(distinct)} different): a list part")
            elif len(distinct) == 1:
                judge.append(f"{x} is always {distinct[0][:40]}: a setting, or a default nobody changes?")
            elif len(distinct) <= 6:
                judge.append(f"{x} is one of {len(distinct)} words ({', '.join(distinct)[:80]}): a stage or a choice?")
            else:
                judge.append(f"{x}: {len(distinct)} different short values (e.g. {', '.join(distinct[:2])[:60]})")
        # two aspects that say the same thing on every thing that has either: keep one, the other a synonym
        by_thing = {x: dict(v) for x, v in aspects.items()}
        names = sorted(by_thing)
        for i, x in enumerate(names):
            for y in names[i + 1:]:
                if set(by_thing[x]) == set(by_thing[y]) and all(by_thing[x][t] == by_thing[y][t] for t in by_thing[x]):
                    judge.append(f"{x} and {y} say the same on all {len(by_thing[x])}: keep one")
        d = k.kinds.decl(kd, group)
        old = parse_safe(d[1].get("has")) if d else []
        has = text_of(merged(old + [Need([x], None, kind_of) for x, kind_of, _ in typed]))
        line = (f'set {d[0]} has="{has}"' if d else f'make kind=kind name={kd} has="{has}"') if typed else ""
        lines.append(f"{kd} ({counts[kd]} things):")
        if typed:
            lines.append("  parts their values say: " + ", ".join(f"{x}:{kind_of}" for x, kind_of, _ in typed))
            lines.append(f"  {line}")
        for j in judge:
            lines.append(f"  judgment: {j}")
        out_rows.append({"kind": kd, "things": counts[kd], "line": line, "judgment": judge,
                         "typed": [{"aspect": x, "kind": kind_of, "things": n} for x, kind_of, n in typed]})
    if prereq:
        lines.insert(0, "first declare the kinds these point at: " + "; ".join(f"make kind=kind name={p}"
                                                                           for p in sorted(prereq)))
    if not lines:
        lines = ["nothing to suggest: no loose aspect is shared by two things of one kind"]
    return {"text": "\n".join(lines), "rows": out_rows, "first": sorted(prereq)}
