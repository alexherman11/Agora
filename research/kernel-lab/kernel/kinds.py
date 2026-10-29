"""Shapes: what a thing must have for a word, a lens or a list to reach it (Alex approved 28 Oct 2026;
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
"""
import re

from .kernel import Refused

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
    """One need: names (spellings, the first is the shape's own) and, for a marker, the values it may have."""
    __slots__ = ("names", "values")

    def __init__(self, names, values=None):
        self.names, self.values = tuple(names), (tuple(values) if values else None)

    def text(self):
        return "|".join(self.names) + ("=" + "|".join(self.values) if self.values else "")

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
        return " or ".join(self.names)

    def __eq__(self, o):
        return isinstance(o, Need) and (self.names, self.values) == (o.names, o.values)

    def __hash__(self):
        return hash((self.names, self.values))


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
    """'title start|starts kind|post_kind=event' -> [Need]; refuses what the kernel could not read."""
    out = []
    for tok in str(text or "").split():
        names, _, values = tok.partition("=")
        ns = [n for n in names.casefold().split("|") if n]
        vs = [v for v in values.split("|") if v] if values else None
        if not ns or any(not NAME.match(n) for n in ns) or ("=" in tok and (not vs or any(not VALUE.match(v) for v in vs))):
            raise Refused(f"{tok} is not a need: a need is an aspect (start), spellings of one (start|starts), or a "
                          f"marker (game=yes, kind|post_kind=event)")
        out.append(Need(ns, vs))
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
                hits = [(t, a) for t, a in self.decls if a.get("name") == kind and self._lives(t) == g]
                if hits:
                    found = hits[-1]
                    break
            self._cache[key] = found
        return self._cache[key]

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

    def is_open(self, kind, group=None):
        """Whether things of other kinds can be a `kind`: it has a shape, or another kind extends it."""
        self._fresh()
        return bool(self.shape(kind, group)) or any(kind in str(a.get("extends") or "").split() for t, a in self.decls)

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
        if self._descends(own, kind, group):
            return f"{a_(own)}, so {a_(kind)}"
        if own in NOT_FITTED:
            return None
        needs = self.shape(kind, group)
        if not needs or self.missing(row, needs):
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
        return "has " + ", ".join(n.met(row) + (f"={row.get(n.met(row))}" if n.values else "") for n in needs)

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
                m = n.met(row)
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
                    m = n.met(row)
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

    def missing(self, row, needs):
        return [n for n in needs if not n.met(row)]

    def _lacks(self, row, entry):
        """(what the thing lacks for this word as [Need or kind name], needs counted) or None when it has no shape."""
        shape = self.word_shape(entry)
        if not shape:
            return None
        own, acts_on = shape
        group = entry.get("lives") or self.k.place
        lack = []
        count = len(own)
        if acts_on:
            ks = self.shape(acts_on, group)
            count += len(ks or [])
            if not self.fits(row, acts_on, group):
                # has the shape but isn't one: a child kind's members are declared (mark <thing> <kind>), so what it
                # lacks is being one (kinds-intelligence review K7: urgent.page paged an unmarked note)
                lack += (self.missing(row, ks) if ks else []) or [Need(["kind"], [acts_on])]
        lack += self.missing(row, own)
        return lack, count

    def check_word(self, actor, entry, target, tx=None):
        """The one check, at every place a word meets its thing: refuse a thing that lacks what the word reads. The
        thing is read as the actor sees it, so a refusal names the word's needs, never a hidden fact."""
        if not target or not isinstance(target, str) or not self.word_shape(entry):
            return
        if tx is not None and target in tx.made:
            return                                  # made by this same act: its facts are not in the world yet
        row = self.k.shown(actor.person, target)
        if row is None:
            return                                  # the caller says "no thing called …" in its own words
        lack, _ = self._lacks(row, entry)
        if not lack:
            return
        own, acts_on = self.word_shape(entry)
        word = entry.get("word")
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
        return (0 if mine else 1, -got[1]), acts_on or "its needs"

    def check_shape_text(self, text, what="needs"):
        """Refuse needs= the kernel could not read; returns them tidied."""
        return text_of(parse(text)) if str(text or "").strip() else ""

    def check_acts_on(self, name, group=None):
        """Refuse acts_on naming a kind nothing here declares or is (a typo would refuse everything, silently)."""
        name = str(name or "").casefold()
        if not KIND_NAME.match(name):
            raise Refused(f"acts_on={name}: a kind name (acts_on=event)")
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
        after = dict(old or {}, **kv)
        shaped = bool(after.get("needs") or after.get("extends"))
        scope = group or self.k.place
        kernel_kinds = RESERVED_KINDS | NOT_FITTED
        if shaped and (name in kernel_kinds or set(str(after.get("extends") or "").split()) & kernel_kinds):
            # trials 28 Oct: a shape on said put a member's notes among JEFF's lines (house reads rows said)
            raise Refused(f"{name if name in kernel_kinds else 'that'} is one of the kernel's own kinds; what it is "
                          f"can't be widened or extended")
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
            if not any(set(o.names) <= set(n.names) and (n.values is None or (o.values and set(o.values) <= set(n.values)))
                       for o in before):
                out.append(n.text())
        return out

    def _dropped(self, old, new, scope):
        """The aspects `old` needed that `new` needs under no spelling at all."""
        after = {x for n in self._expand(new, scope) for x in n.names}
        return [n.names[0] for n in self._expand(old, scope) if not set(n.names) & after]

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
    lack = k.kinds.missing(row, plain)
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
    found = k.kinds.kinds_of(a, (k.groups_of(t) or [k.place])[0])
    name = a.get("title") or k.name(t)
    lines = [f"{name} ({t}):"] + [f"  {kd} · {why}" for kd, why in found]
    return {"text": "\n".join(lines), "rows": [{"kind": kd, "why": why} for kd, why in found]}
