"""The knife desk (round 7): the MOO desk with general verbs only, selections as targets, and pair verbs."""

import re
import shlex

import blanks
import harness   # registers launch; provides sync
import knife
import moo
import persons
from desk import aspects_meet, event_aspects, rule_did_unseen, unescape_value
from desk_moo import DeskMoo, HELP_MOO
from world import Refusal

HELP_KNIFE = HELP_MOO.replace(
    "  do verb id k=v ...     change something. e.g. do move a04 into=f02   do tidy f04   do gather f02 words=harbor by=due",
    "  do verb target k=v ... change something. target is an id or a selection (help selections)\n"
    "                         e.g. do move a04 into=f02   do move kind:image,in:f04 into=f28   do remove also:a18\n"
    "  do swap A B | do beside A B | do match A to=B    pair verbs\n"
    "  do group <selection> as=column title=X          a new surface around the selection",
).replace(
    "  help [verb]            what a verb does, its arguments, one example\n",
    "  help [word]            any command (help history), verb (built-in or made in the world) or topic; a word it\n"
    "                         doesn't know lists all it does know, and the world verbs at hand where you are\n",
)

SELECTION_HELP = """selections: a target can be one id, or a selection that names many things:
  ?tide+parser       things whose title, text or tags contain all the words
  kind:image         by kind (kind:note|task for several)
  tag:harbor         by tag
  in:f04             inside surface f04, recursively
  hidden             more than 5% covered by something
  also:a18           the other appearances of a18's subject
  due<2026-09-20     due before (due> after)
  age<2              touched within the last 2 days by the clock (age>7: untouched for a week); needs clock
  title:agenda       title contains the word
  prop:status=done   by property (prop:status alone: has the property)
  answered-by:a1008  what a1008 answers (its links as=answers); answers:a1006 what answers a1006
                     (parts:a30 / part-of:a20 do the same for part-of links; links:a04 is any link, either way)
  -tag:fixed         leaves out what the term would select (any term may be negated)
  a20,a22            an explicit list
combine terms with commas (AND): kind:image,in:f04. The receipt lists everything the verb touched.
the Trash (a surface with prop trash=yes) is left out of every selection unless an in: term names it or a surface in
it; find and views say how many they left out. A thing moved out of the Trash loses status=trashed (a task's is open).
find <selection> lists what it matches, grouped by surface: find kind:image   find tag:harbor,in:f04   find hidden
e.g. do move ?harbor into=f02 one=1     do raise hidden,in:f04     do group kind:image,in:f04 as=column title=Pictures"""


# Juniper: `do prop prop:day=2026-10-10 tripday=1` lost its target, because the selection carries an =. A word that
# begins with a selection term is the target, = or not (a typed do line and a rule's action alike, a1027)
SEL = re.compile(r"^-?(kind|tag|in|also|prop|title|comments|links|parts|part-of|answers|answered-by):|^-?(due|age)[<>]|^[?]")


def is_target_word(a):
    return "=" not in a or a.startswith("?") or bool(SEL.match(a))


HELP_LEAN = HELP_KNIFE.replace(
    "commands (one per call):",
    "commands (several per call, separated by ; run in order, stopping at the first refusal; at most 4 reads per call):",
).replace(
    "  examine id             description plus every verb this thing answers to, by origin",
    "  examine id             a thing's detail: its lines, comments, links, and the verbs that apply right now",
) + """
  go <room>              walk to a room (by id or a word of its title); go alone: who is where. help rooms
  look                   with no id, in a world with rooms: the room you are in, as a person there sees it
  table <selection> [cols=a,b] [by=col]   one row per thing, props side by side (e.g. table kind:trial)
  rest                   go home to your corner (Home if you have none), marked via=rest in history
  wake <name>            end a resting resident's rest now, signed by you (an @name from a resident waits for their wake)
  $here $here.talk $new  blanks, filled when the line runs: the room you are in, a prop of it, the thing made most
                         recently earlier in this reply; $today $me. Words you type (line= text= title=) stay as typed;
                         \\$ is a literal dollar sign. help blanks
  in the house (a resident's reply): only a line beginning with > acts; any other line is thinking, whatever its
                         first word. One > line is one command: a ; in it is words, so several commands are several
                         > lines, run in order; a refusal stops the ones after it. A > line nothing answers (a
                         quote) is a MISS: logged in Misses, it stops nothing. A verb's lines and wake lines keep ;
  more: help rules · help scripts · help views · help clock · help handles · help blanks · help why · help export · help trials · help lens
  building: help verbs (capabilities anyone makes in the world) · help commissions (a worker changes the code for you)"""


class DeskKnife(DeskMoo):
    def __init__(self, world, variant="knife"):
        super().__init__(world, "acme")
        self.variant = variant

    lean = False        # round 11: no geometry inside tiled parents, no try: tags on outline lines (examine has them)
    _hints_on = False
    vars = None         # named handles: $draft

    def _geom(self, nid):
        n = self.world.nodes[nid]
        if self.lean and n["parent"] and self.world.nodes[n["parent"]]["layout"] != "free":
            return ""
        return super()._geom(nid)

    _hidden_verbs = knife.SPECIALIZED

    def _verbs_by_origin(self, nid):
        return knife.general_verbs_by_origin(self.world, nid)

    def _verb_names(self):
        return set(knife.GENERAL) | set(knife.PAIR_DOC) | set(moo.SYNONYMS)

    def verb_hints(self, nid):
        """Tags name a verb *and the selection it would take*, so selections are visible where the model looks."""
        if self.lean and not self._hints_on:
            return None
        w = self.world
        n = w.nodes[nid]
        out = []
        if n["type"] == "surface":
            kids = w.children(nid)
            leaves = [k for k in kids if k["type"] == "appearance"]
            kinds = {w.subjects[k["subject"]]["kind"] for k in leaves}
            if len(kids) >= 2 and n["layout"] == "free" and any(w.hidden_fraction(k["id"]) > 0.05 for k in kids):
                out.append("tile")
                out.append(f"raise hidden,in:{nid}")
                if len(kinds) > 1:
                    k0 = sorted(kinds)[0]
                    out.append(f"group kind:{k0},in:{nid}")
            elif len(kids) >= 2 and n["layout"] != "free":
                out.append("sort")
        else:
            s = w.subjects[n["subject"]]
            if w.hidden_fraction(nid) > 0.05:
                out.append("raise")
            if len(w.appearances_of(s["id"])) > 1:
                out.append(f"remove also:{nid}")
            if s["kind"] == "chat" and moo.unanswered(w, s["id"]):
                out.append("append")
            for c in s.get("comments", []):
                if not c["resolved"] and c["by"] != "alex":
                    out.append(f"resolve {c['id']}")
        import rooms
        if out and not rooms.layout_at_hand(self):
            out = [h for h in out if h.split()[0] not in rooms.LAYOUT]     # a990: shown where layout is at hand
        return out or None

    def _shown_verbs(self, nid):
        """a990: {origin: [verb names]} as examine and verbs show them to this reader: the layout verbs only where
        they are at hand (rooms.layout_at_hand). -> (groups, layout shown?)"""
        import rooms
        groups = knife.general_verbs_by_origin(self.world, nid)
        if rooms.layout_at_hand(self):
            return groups, True
        kept = {o: [v for v in names if v not in rooms.LAYOUT] for o, names in groups.items()}
        return {o: names for o, names in kept.items() if names}, False

    def cmd_verbs(self, ident):
        import rooms
        nid = self._resolve(ident)
        if nid in self.world.subjects:
            return f"{nid} verbs:\n" + self.subject_verbs_line(nid)
        self._mark_seen(nid)
        out = [f"{nid} verbs:"]
        groups, layout = self._shown_verbs(nid)
        for origin, names in groups.items():
            for name in names:
                v = moo.REGISTRY[name]
                args = v.args if layout or name != "move" else rooms.MOVE_ANYWHERE
                out.append(f"  {name} {args}".rstrip() + f"   - {v.doc.split('.')[0]}." + (f"  [{origin}]" if origin != "thing" else ""))
        if not layout:
            out.append("  " + rooms.layout_pointer(self))
        return "\n".join(out)

    bullets = False   # round 10: detail nested under a thing's line as * bullets, with a fold marker

    def bullet_block(self, nid, indent="  ", limit=4):
        """Content, comments and links of an appearance as nested bullets. Never looks complete when it is not."""
        w = self.world
        n = w.nodes[nid]
        s = w.subjects[n["subject"]]
        out = []
        if s["kind"] == "doc":
            secs = w.sections(s["text"])
            pre = next((b for h, b in secs if h is None), "")
            if pre:
                out.append(f"{indent}* {pre.splitlines()[0][:100]}")
            for h, b in secs:
                if h:
                    out.append(f"{indent}* ## {h}  ({len(b.split())}w; read {nid} #{h})")
        else:
            tl = [l for l in s["text"].splitlines() if l.strip()]
            for l in tl[:limit]:
                out.append(f"{indent}* {l}" if len(l) <= 240 else f"{indent}* {l[:240]}… (line cut; read {nid})")
            if len(tl) > limit:
                out.append(f"{indent}* … {len(tl) - limit} more line(s) folded; read {nid} for all")
        for c in s.get("comments", []):
            ct = c["text"] if len(c["text"]) <= 160 else c["text"][:160] + "… (read " + nid + " for all)"
            out.append(f"{indent}* {c['id']} {persons.comment_by(w, c)} ({'resolved' if c['resolved'] else 'open'}): {ct}")
        for l in w.links_of(s["id"]):
            other = l["to"] if l["from"] == s["id"] else l["from"]
            ot = w.subjects[other]["title"]
            apps_o = w.appearances_of(other)
            out.append(f"{indent}* " + (f"{l['kind']} → " if l["from"] == s["id"] else f"← {l['kind']} from ")
                       + f"{other} \"{ot}\"" + (f" ({', '.join(apps_o)})" if apps_o else "") + f"  [{l['id']}]")
        return "\n".join(out)

    # ---- views: live collections (round 11d) ---------------------------------------------------------
    def view_matches(self, nid):
        q = self.world.nodes[nid].get("query", "")
        try:
            sel = self._parse_selection(q)
        except Refusal:
            return None
        return [] if sel is None else [i for i in sel[0] if i != nid]

    def view_lines(self, nid, depth):
        ind = "  " * (depth + 1)
        ids = self.view_matches(nid)
        if ids is None:
            return [ind + f"(query {self.world.nodes[nid].get('query')!r} could not be evaluated now: help selections)"]
        n = self.world.nodes[nid]
        if n.get("cols") and ids:
            return [ind + l.strip() for l in self._table_lines(ids, n["cols"], n.get("by"), n.get("desc"))[:-1]]
        out = []
        for i in ids:
            out.append(ind + self.line(i, 1) + f"  (in {self.world.nodes[i]['parent']})")
            extra = self.child_extra(i, depth + 1) if self.world.nodes[i]["type"] == "appearance" else None
            if extra:
                out.append(extra)
        return out

    def child_extra(self, nid, depth):
        if not (self.bullets or getattr(self, "_deep", False)):
            return None
        w = self.world
        s = w.subjects[w.nodes[nid]["subject"]]
        ind = "  " * (depth + 1)
        if s["kind"] == "image":
            return None
        tl = [l for l in s["text"].splitlines() if l.strip()]
        if s["kind"] == "doc":
            secs = [h for h, _ in w.sections(s["text"]) if h]
            return f"{ind}* sections: {', '.join(secs)}" if secs else None
        if not tl:
            return None
        if getattr(self, "_full", False):
            # :4 — the text itself, up to eight lines, each uncut to 240; the fold is declared
            shown = tl[:8]
            out = [f"{ind}* " + (l if len(l) <= 240 else l[:240] + "… (cut; read " + nid + ")") for l in shown]
            if len(tl) > 8:
                out.append(f"{ind}* … {len(tl) - 8} more line(s); read {nid} for all")
            return "\n".join(out)
        rest = len(tl) - 1
        first = tl[0] if len(tl[0]) <= 160 else tl[0][:160] + "…"
        line = f"{ind}* {first}"
        if rest or first.endswith("…"):
            line += f"  (+{rest} more line(s); examine {nid})" if rest else f"  (cut; examine {nid})"
        return line

    # ---- rules: quiet notes that act on their own (a1027; the automation layer of round 11c, now as notes) ---------
    # A rule is a note tagged rule, placed in a room. Its text is one line, `when <selection> do <verb> ...` or
    # `on <verb> [by=<actor>] do ...`; # lines describe it. It lives in the room holding it (moving the note moves its
    # home) and acts as whoever last chose what it does: its maker, or the last to write its text or tag it rule
    # (a687; Juniper c1075). Its stored text is checked whenever the text, the home or the author changes: a rule that
    # fails the check is broken, says why, and never fires, never running an earlier version (a598). A valid one re-arms:
    # what matches it then counts as handled, so a fix never sets off a flood. Quiet (Alex, a585): a narrated look never
    # lists rule notes; the tree marks them; `rules` and `examine` say everything.
    rules = None            # retired: the desk-attribute rules from before a1027, kept only to say they never fire
    _rulestate = None       # {rule note subject id: {the parsed rule, sig, home, author, broken, done, fired ...}}
    _rule_authors = None    # {subject id: (events seen, author)}: who a rule acts as, read from the log once per change
    _rule_notes = None
    _in_rules = False
    RULE_BLANKS = ("item", "here", "today", "me")
    RULE_FORM = "when <selection> do <verb> [target] [k=v ...]   or   on <verb> [by=<actor>] do <verb> ..."

    def _rule_subjects(self):
        w = self.world
        return [s for s in w.subjects.values() if "rule" in (s.get("tags") or []) and w.appearances_of(s["id"])]

    def _rule_author(self, sid):
        """a1027 (c1075, call 1): whoever last chose what the rule does: its maker, or the last to write its text or
        tag it rule. An undone event counts for nothing, so an undo gives the rule back to whoever came before."""
        w = self.world
        cache = self._rule_authors = self._rule_authors or {}
        if sid in cache and cache[sid][0] == len(w.events):
            return cache[sid][1]
        ids, who = {sid} | set(w.appearances_of(sid)), None
        for e in w.events:
            if e.get("undone") or e["verb"] == "undo":
                continue
            a = e.get("args") or {}
            if e["verb"] == "create" and isinstance(e.get("undo"), dict):
                made = e["undo"].get("delete")
                if made in ids or (made in w.nodes and w.nodes[made].get("subject") == sid):
                    who = e["by"]
            elif e["target"] in ids and ((e["verb"] == "edit" and ("text" in a or "append" in a))
                                         or (e["verb"] == "tag" and "rule" in str(a.get("add", "")).split(","))):
                who = e["by"]
        cache[sid] = (len(w.events), who)
        return who

    @staticmethod
    def _rule_line(s):
        lines = [l.strip() for l in s["text"].splitlines() if l.strip() and not l.strip().startswith("#")]
        return lines

    def _rule_parse(self, s, home):
        """-> (the rule, None) or (None, why it is broken). Strict to the stored text, judged where the rule lives;
        a1156: a world verb's word is the verb it was bound to when the rule was saved."""
        import verbs
        self._parse_binds = verbs.binding_of(self.world, ("s", s["id"]), s["text"])
        try:
            return self._rule_parse_in(s, home)
        finally:
            self._parse_binds = None

    _parse_binds = None

    def _rule_parse_in(self, s, home):
        lines = self._rule_line(s)
        if not lines:
            return None, f"its text holds no rule yet: one line, {self.RULE_FORM}"
        if len(lines) > 1:
            return None, f"its text holds {len(lines)} lines; a rule note holds one rule (# lines describe it)"
        line = blanks.protect(lines[0])
        for m in blanks.BLANK.finditer(line):
            if m.group(0) == blanks.LIT:
                continue
            name, attr = m.group(1), m.group(2) or ""
            if name == "new":
                return None, "$new: a rule has no earlier line; it acts on $item, the thing it fired on"
            if name not in self.RULE_BLANKS and name not in (self.vars or {}):
                return None, (f"${name}{attr} is no blank in a rule. A rule's blanks: $item $item.title $item.<prop> "
                              f"$item.maker $here $here.<prop> $today $me, or a handle; a literal dollar sign is \\$")
            if attr and name in ("today", "me"):
                return None, f"${name}{attr}: ${name} has no parts"
        try:
            argv = shlex.split(line)
        except ValueError as e:
            return None, f"could not parse: {e}"
        try:
            if argv and argv[0] == "on":
                i = argv.index("do") if "do" in argv else -1
                if i < 2:
                    raise Refusal(f"a rule reads {self.RULE_FORM}")
                on_verb, by = argv[1].lower(), None
                for a in argv[2:i]:
                    if not a.startswith("by="):
                        raise Refusal(f"on: only by=<actor> may follow the event verb, not {a!r}")
                    by = a[3:]
                act = self._parse_action(argv[i + 1:], home)
                act["kv"].pop("now", None)
                return {"on": on_verb, "by": by, "sel": f"on {on_verb}" + (f" by={by}" if by else ""), **act}, None
            if len(argv) < 4 or argv[0] != "when" or argv[2] != "do":
                raise Refusal(f"a rule reads {self.RULE_FORM}")
            if self._rule_selection(argv[1], home) is None:
                raise Refusal(f"{argv[1]!r} is not a selection (help selections)")
            act = self._parse_action(argv[3:], home)
            return {"sel": argv[1], "now": act["kv"].pop("now", None), **act}, None
        except Refusal as e:
            return None, str(e)

    def _rules_sync(self, say=True):
        """Bring each rule note's state up to date with the world. A new rule, a changed text, a new home or a new
        author is checked again, strictly; a valid one re-arms (what matches it now counts as handled). The act that
        changed a rule hears what the rule is now, in ~ lines on its receipt. -> the active rules, in id order."""
        import verbs
        w = self.world
        states = self._rulestate = dict(self._rulestate or {})
        live = {s["id"]: s for s in self._rule_subjects()}
        for sid in [k for k in states if k not in live]:
            gone = states.pop(sid)
            if say:
                self._note(f"~ rule {gone['id']} no longer acts: its note is no longer placed, or no longer tagged rule")
        for sid, s in live.items():
            aid = w.appearances_of(sid)[0]
            home, author = verbs.room_holding(w, sid), self._rule_author(sid)
            b = verbs.binding_of(w, ("s", sid), s["text"])
            sig = (s["text"], home, author, repr(sorted((b or {}).get("words", {}).items())) if b else None)
            prev = states.get(sid)
            if prev is not None and prev["sig"] == sig:
                prev["id"] = aid
                continue
            if prev is not None and prev["sig"][:3] == sig[:3]:
                # 1 Oct (Juniper e3531): only its bound words changed, or the code that computes the sig did (a1156 made
                # it four parts, so every rule re-armed on its first pass and a1087 counted a1156's own landing as
                # handled). Re-read it, but keep what it has handled and its cursor: re-arming is for a rule its
                # author changed, never a silent swallow of what is entering now
                rule, broken = self._rule_parse(s, home)
                prev.update({"id": aid, "sig": sig, "broken": broken, **(rule or {})})
                continue
            prev = prev or {}
            rule, broken = self._rule_parse(s, home)
            st = {"id": aid, "sid": sid, "sig": sig, "home": home, "author": author, "broken": broken, "done": set(),
                  "cursor": len(w.events), "last_fail": prev.get("last_fail"), "last_skip": prev.get("last_skip"),
                  "last_stop": prev.get("last_stop"),
                  **{k: prev.get(k, 0) for k in ("fired", "failed", "skipped", "stopped")}, **(rule or {})}
            already = []
            if not broken and not st.get("on") and not st.get("now"):
                try:
                    already = self._rule_selection(st["sel"], home)[0]
                    st["done"].update(already)
                except Refusal as e:
                    st["broken"] = broken = str(e)
            states[sid] = st
            if not say:
                continue
            if broken:
                self._note(f"~ rule {aid} saved broken: {broken}. It never fires until its text is fixed (rules lists it)")
                continue
            where = f"lives in {w.nodes[home]['title']} ({home})" if home in w.nodes else "lives in no room, so $here refuses"
            said = f"~ rule {aid} saved: {self._rule_line(s)[0]}  ({where}; acts as {author or '?'}"
            if st.get("now"):
                said += "; now=1: it fires on what matches now too"
            elif already:
                said += f"; {len(already)} thing(s) already match, counted as handled: it fires on what enters from now on"
            said += ")"
            if prev.get("author") and prev["author"] != author:
                said += (f"\n  this rule now acts as you (it acted as {prev['author']})" if author == w.me
                         else f"\n  this rule now acts as {author} (it acted as {prev['author']})")
            self._note(said)
        return sorted((st for st in states.values() if not st["broken"]), key=lambda r: int(re.sub(r"\D", "", r["id"]) or 0))

    def _rule_of_note(self, nid):
        """The rule state for a rule note named by an appearance or subject id, or None."""
        w = self.world
        sid = w.nodes[nid].get("subject") if nid in w.nodes else nid
        return (self._rulestate or {}).get(sid) if sid in w.subjects and "rule" in (w.subjects[sid].get("tags") or []) else None

    def _rule_lines(self, r, indent="  "):
        """What rules and examine say of one rule: its home, who it acts as, and how it has gone."""
        w = self.world
        s = w.subjects[r["sid"]]
        where = (f"lives in {w.nodes[r['home']]['title']} ({r['home']})" if r.get("home") in w.nodes
                 else "lives in no room ($here refuses)")
        head = f'{indent}{r["id"]} "{s["title"]}" · {where} · acts as {r.get("author") or "?"}'
        if r["broken"]:
            head += f" · BROKEN: {r['broken']}. It never fires until its text is fixed"
        else:
            head += (f" · fired {r['fired']}x" + (f" · failed {r['failed']}x (last: {r['last_fail']})" if r["failed"] else "")
                     + (f" · skipped {r['skipped']}x (last: {r['last_skip']})" if r["skipped"] else "")
                     + (f" · stopped by the {self.ROUNDS}-round bound {r['stopped']}x (last: {r['last_stop']})"
                        if r.get("stopped") else ""))
        text = self._rule_line(s)
        return [head] + [f"{indent}    {l}" for l in text[:3]]

    def rule_mark(self, sid):
        """The tree's mark on a rule note (c1075, call 5: the tree is the builder's inventory, so a rule shows there)."""
        import verbs
        w, r = self.world, (self._rulestate or {}).get(sid)
        s, home = w.subjects[sid], verbs.room_holding(w, sid)
        if r is not None and r["sig"][:3] == (s["text"], home, self._rule_author(sid)):
            broken = r["broken"]
        else:
            # judged afresh, never stored: the act printing this line has not synced the rules yet, and its receipt
            # must still say 'saved' (a read of the state here would arm the rule silently)
            broken = self._rule_parse(s, home)[1] if w.appearances_of(sid) else None
        return "rule, broken (rules says why)" if broken else "rule"

    def cmd_rules(self):
        self._rules_sync(say=False)
        sts = sorted(self._rulestate.values(), key=lambda r: int(re.sub(r"\D", "", r["id"]) or 0))
        out = [f"{len(sts)} rule(s), each a note tagged rule; a narrated look never lists them, the tree marks them:"
               if sts else f"no rules. A rule is a note tagged rule, in the room it acts from; its text is one line: "
                           f"{self.RULE_FORM} (help rules)"]
        for r in sts:
            out += self._rule_lines(r)
        if self.rules:
            out.append(f"(this world still holds {len(self.rules)} rule(s) from before rules were notes; they never fire: "
                       f"write each as a note)")
        return "\n".join(out)

    def cmd_rule(self, arg):
        """a1027 (c1075, call 4): rules are notes, so the old command names the door, with the exact line to write."""
        a = arg.strip().replace(blanks.LIT, "\\$")
        if a.startswith(("when ", "on ")):
            q = a.replace("\\", "\\\\").replace('"', '\\"')
            raise Refusal("rules are notes now: a note tagged rule, placed in the room it acts from, whose text is the "
                          f'rule. Write:\n  do create $here kind=note tags=rule title="<what it does>" text="{q}"')
        if a.startswith(("drop", "home")):
            raise Refusal("rules are notes now: remove a rule's note to drop it (do remove <id>), move it to change its "
                          "home (do move <id> into=<room>); rules lists them")
        raise Refusal(f"rules are notes now: a note tagged rule whose text is {self.RULE_FORM}. help rules")

    def cmd_table(self, arg):
        """table <selection> [cols=a,b,c] [by=col] [desc=1]: one row per thing, props side by side."""
        try:
            argv = shlex.split(arg)
        except ValueError as e:
            raise Refusal(f"could not parse: {e}")
        words, kv = [], {}
        for a in argv:
            if a.split("=")[0] in ("cols", "by", "desc") and "=" in a:
                k, _, v = a.partition("=")
                kv[k] = v
            else:
                words.append(a)
        if not words:
            raise Refusal("table <selection> [cols=a,b,c] [by=col] [desc=1]   e.g. table kind:trial cols=task,model,score,calls")
        sel = self._parse_selection(" ".join(words))
        if sel is None:
            raise Refusal(f"{' '.join(words)!r} is not a selection (help selections)")
        ids, desc = sel
        aside = self._trash_note(" ".join(words))
        aside = f"; {aside}" if aside else ""
        if not ids:
            return f"table {desc}: nothing matches" + aside
        lines = self._table_lines(ids, kv.get("cols"), kv.get("by"), kv.get("desc"))
        notes = self._column_notes(ids, kv.get("cols") or ",".join(self.HOUSE_COLS))   # without cols=, a shadowed prop
        return "\n".join([f"table {desc}: {len(ids)} row(s)" + aside] + lines + ["  " + x for x in notes])

    # a1431: four columns the house answers from its own events, never from props: who made a thing and when (its
    # create), who last changed it and when (the latest edit: its text, title, props, tags, due, a checked item, a put).
    # A comment, a link or a move is not an edit. An undone event counts for nothing.
    HOUSE_COLS = ("made_by", "made_at", "edited_by", "edited_at")
    TABLE_COLS = ("id", "title", "kind", "tags", "due", "in", "age", "words")

    def _house_record(self, ids):
        """-> {shown id: {house column: value}}, read from the event log in one pass."""
        w = self.world
        key = {}
        for i in ids:
            key[i] = i
            sid = w.nodes[i].get("subject")
            if sid:
                key[sid] = i
        rec = {i: {} for i in ids}
        stamp = lambda e: (e.get("at") or "").replace("T", " ")[:16] or e.get("day") or ""   # noqa: E731
        def put(i, kind, e):
            rec[i][kind + "_by"], rec[i][kind + "_at"] = persons.by(w, e), stamp(e)    # a1568: the person, by name
        for e in w.events:
            if e.get("undone") or e["verb"] == "undo":
                continue
            u = e.get("undo") if isinstance(e.get("undo"), dict) else {}
            if e["verb"] in ("create", "group"):
                made = u.get("delete")
                hit = key.get(u.get("delete_subject")) or key.get(made) or key.get((w.nodes.get(made) or {}).get("subject"))
                if hit and "made_by" not in rec[hit]:
                    put(hit, "made", e)
                continue
            if "restore_subject" in u:
                hit = key.get(u["restore_subject"].get("id"))
            elif u.get("restore_subjects"):
                hit = key.get(u["restore_subjects"][0].get("id"))   # a put: the card put, not the ones renumbered quietly
            elif "restore_props" in u:
                hit = key.get(u["restore_props"][0])
            elif e["verb"] in ("rename", "prop") and "restore" in u:
                hit = key.get(e["target"])
            else:
                hit = None
            if hit:
                put(hit, "edited", e)
        return rec

    def _column_notes(self, ids, cols_spec):
        """a1431: what a receipt says about the columns asked for: a column that names nothing on any shown thing, and
        a prop that a house column shadows."""
        w = self.world
        cols = [c.strip() for c in str(cols_spec or "").split(",") if c.strip()]
        held = {}
        for i in ids:
            sid = w.nodes[i].get("subject")
            for k in ((w.subjects[sid].get("props") if sid else None) or {}):
                held[k] = held.get(k, 0) + 1
        n = len(ids)
        things = f"{n} thing" + ("" if n == 1 else "s")
        out = []
        missing = [c for c in dict.fromkeys(cols) if c not in self.TABLE_COLS and c not in self.HOUSE_COLS and c not in held]
        if missing:
            out.append(f"{', '.join(missing)}: nothing by {'that name' if len(missing) == 1 else 'those names'} on any of "
                       f"{things}; house columns are {', '.join(self.HOUSE_COLS)}")
        for c in dict.fromkeys(cols):
            if c in self.HOUSE_COLS and c in held:
                out.append(f"{c}: the house's record, not the prop {c}= that {held[c]} of {things} "
                           f"{'has' if held[c] == 1 else 'have'} (prop:{c}= still selects by it)")
        return out

    def _table_lines(self, ids, cols_spec, by, desc_flag):
        """Header, one row per thing, and a columns hint; shared by table and by views with cols=."""
        w = self.world
        def subj(i):
            n = w.nodes[i]
            return w.subjects[n["subject"]] if n["type"] == "appearance" else None
        props_seen, kinds = [], set()
        for i in ids:
            s = subj(i)
            kinds.add(s["kind"] if s else "surface")
            for k in ((s or {}).get("props") or {}):
                if k not in props_seen:
                    props_seen.append(k)
        if cols_spec:
            cols = [c.strip() for c in cols_spec.split(",") if c.strip()]
            if "title" not in cols:
                cols.insert(0, "title")   # titles are the names; a table of ids alone cannot be read
        else:
            cols = ["title"] + (["kind"] if len(kinds) > 1 else []) + props_seen
            if any((subj(i) or {}).get("due") for i in ids):
                cols.append("due")
            if any((subj(i) or {}).get("tags") for i in ids):
                cols.append("tags")
        house = self._house_record(ids) if set(cols) & set(self.HOUSE_COLS) else {}
        def cell(i, c):
            n, s = w.nodes[i], subj(i)
            if c in self.HOUSE_COLS:
                return house[i].get(c, "")
            if c == "id":
                return i
            if c == "title":
                return w.title(n)
            if c == "kind":
                return s["kind"] if s else n["layout"]
            if c == "tags":
                return ",".join(s["tags"]) if s else ""
            if c == "due":
                return (s or {}).get("due") or ""
            if c == "in":
                return w.title(w.nodes[n["parent"]]) if n["parent"] else ""
            if c == "words":
                return str(len((s.get("text") or "").split())) if s else ""
            if c == "age":
                d = w.last_day(i)
                return str(w.days_between(d, self.today)) if d and self.today else ""
            return str(((s or {}).get("props") or {}).get(c, ""))
        shown = [{"title": "title", "tags": "tags", "due": "due", "in": "place"}.get(c, None if c in ("id", "kind", "words", "age") + self.HOUSE_COLS else f"prop:{c}") for c in cols]
        shown = [a for a in shown if a]
        for i in ids:                       # Juniper (reads case): a table that printed status has shown status
            self._mark_seen(i, shown)
            if w.nodes[i].get("subject"):
                self._mark_seen(w.nodes[i]["subject"], shown)
        rows = [[i] + [cell(i, c) for c in cols] for i in ids]
        if by:
            if by not in cols:
                raise Refusal(f"by={by} is not a column here; columns: id " + " ".join(cols))
            j = cols.index(by) + 1
            def key(row):
                v = str(row[j])
                try:
                    return (0, float(v.split("/")[0]), v)
                except ValueError:
                    return (1, 0.0, v.lower())
            rows.sort(key=key, reverse=bool(desc_flag))
        header = ["id"] + cols
        widths = [min(max(len(str(r[k])) for r in [header] + rows), 40 if header[k] == "title" else 24) for k in range(len(header))]
        def fmt(row):
            return "  " + "  ".join(str(v)[:widths[k]].ljust(widths[k]) for k, v in enumerate(row)).rstrip()
        out = [fmt(header)] + [fmt(r) for r in rows]
        out.append("  columns: id title kind tags due in age words, made_by made_at edited_by edited_at (the house's record), "
                   "and any prop; cols= picks, by= sorts (desc=1)")
        return out

    def _rule_selection(self, sel, home=None):
        """A rule's selection, its blanks filled each time it is asked ($today follows the clock; $here is the rule's
        home, a990)."""
        return self._parse_selection(blanks.fill(self, sel, ctx=blanks.Ctx("rule", home=home)))

    def _parse_action(self, argv, home=None):
        """The part of a rule after do: <verb> [target] [k=v ...], or a verb made in the world (a990): its word, or use
        <id>, then its words. $item stands for the thing the rule fired on, in a world verb's words (the only word, when
        none are given), a target or a k=v value. A world verb's word is judged where the rule lives (`home`): one only
        another room has makes the rule broken, naming the door."""
        verb = argv[0].lower() if argv else ""
        if not verb:
            raise Refusal(f"nothing after do; a rule reads {self.RULE_FORM}")
        if verb in ("run", "script"):
            raise Refusal(self.SCRIPTS_DOOR)
        if verb == "use" or verb not in self._verb_names() or verb in knife.SPECIALIZED:
            import verbs
            args = [a for a in argv[1:] if a != "now=1"]
            kv = {"now": "1"} if len(args) < len(argv) - 1 else {}
            if verb == "use":
                if not args:
                    raise Refusal("rule ... do use <verb id> [words]   ($item, the thing it fired on, when no words follow the id)")
                s = self.world.subjects.get(self.world.nodes.get(self._resolve(args[0]), {}).get("subject") or args[0])
                if not s or "verb" not in (s.get("tags") or []):
                    raise Refusal(f"{args[0]} is not a verb (a note tagged verb)")
                return {"verb": "use", "world": True, "args": args, "kv": kv, "target": None}
            b = self._parse_binds
            if b is not None and verb in b["words"]:
                rec = b["words"][verb]
                if not rec.get("thing") and verbs._verb_named(self.world, rec["id"]) is None:
                    raise Refusal(f"{verb} {rec['at']} is gone; this rule was bound to it. A rule never finds another "
                                  f"{verb} on its own: save it again to bind it to one that is here, or use <id>")
                return {"verb": verb, "world": True, "args": args, "kv": kv, "target": None}
            if b is not None and verb in b["missing"]:
                raise Refusal(b["missing"][verb])        # a1156: decided when it was saved, never looked up again
            if verb in {n for s in verbs.all_verbs(self.world) for n in verbs._names(s["title"])}:
                verbs.find(self, verb, [a for a in args if "=" not in a], self.world.me, at=(home, True))
                return {"verb": verb, "world": True, "args": args, "kv": kv, "target": None}
            raise Refusal(f"{verb} is not a verb here; general verbs: " + " ".join(knife.GENERAL) + "; or a verb made in "
                          f"the world (help verbs)")
        rest = list(argv[1:])
        target = None
        if rest and is_target_word(rest[0]):
            target = rest.pop(0)   # an explicit target instead of the thing that entered: rule when in:Today do sort Today by=due
        kv = {}
        for a in rest:
            if "=" not in a:
                raise Refusal(f"rule arguments are k=v; got {a!r}")
            k, _, v = a.partition("=")
            if not re.fullmatch(r"[A-Za-z_][\w-]*", k):
                # a1027: a misspelled selection term (answred-by:$item,...=...) must not pass as a prop named for it
                raise Refusal(f"{k!r} is neither a k=v key nor a selection term (help selections)")
            kv[k] = v
        return {"verb": verb, "target": target, "kv": kv}

    @staticmethod
    def _q(a):
        return '"' + a.replace("\\", "\\\\").replace('"', '\\"') + '"' if (" " in a or not a) else a

    def _action_text(self, r):
        if r.get("world"):
            text = " ".join([r["verb"]] + [self._q(a) for a in r.get("args", [])])
        else:
            text = f"{r['verb']} {r.get('target') or ''} {self._fmt_args(r['kv'])}".replace("  ", " ").rstrip()
        return text.replace(blanks.LIT, "\\$")      # a literal dollar sign reads back as it was written

    def _fire(self, r, i):
        """Run rule r's action on thing i; returns one receipt line. A rule is a template its author wrote: every
        value is filled by the one filler, $item being the thing it fired on (a806)."""
        import verbs
        ctx = blanks.Ctx("rule", item=i, name=r["id"], home=r.get("home"))
        s = self.world.subjects.get(r.get("sid"))
        ctx.binds = verbs.binding_of(self.world, ("s", s["id"]), s["text"]) if s else None     # a1156
        self._ctxs = (self._ctxs or []) + [ctx]
        try:
            return self._fire_in(r, i, ctx)
        finally:
            self._ctxs = self._ctxs[:-1]

    def _fire_in(self, r, i, ctx):
        if r.get("world"):
            # a990: a verb made in the world, found from where the rule lives (the rule's ctx is innermost), strictly
            import verbs
            args = list(r.get("args") or [])
            if len(args) < (2 if r["verb"] == "use" else 1):
                args.append("$item")
            line = " ".join([r["verb"]] + [self._q(blanks.fill(self, a, ctx=ctx)).replace("$", "\\$") for a in args])
            res = verbs.try_line(self, blanks.protect(line), self.world.me)
            if res is None:
                raise Refusal(f"nothing answers to {r['verb']} where {r['id']} lives")
            return line + " → " + next((l.strip() for l in res.splitlines()[1:] if l.strip()), "ok")
        tgt = blanks.fill(self, r.get("target") or "$item", ctx=ctx)
        if r.get("target") and tgt != i:
            sel = self._parse_selection(tgt)
            if sel is not None and not sel[0]:
                return None     # a1027: a selection that matches nothing is nothing to do, not a refusal
            for x in (sel[0] if sel is not None else [self._resolve(tgt)]):
                self._mark_seen(x)
        kv = {k: blanks.fill(self, v, ctx=ctx) for k, v in r["kv"].items()}     # a rule is a template: all filled
        return self.cmd_do_knife(r["verb"], [tgt], kv).splitlines()[0]

    def _title_of(self, ident):
        """The title behind an id or handle, for $1.title and $item.title; a non-thing stays as it is."""
        try:
            nid = self._resolve(ident)
        except Refusal:
            return ident
        w = self.world
        if nid in w.subjects:
            return w.subjects[nid]["title"]
        return w.title(w.nodes[nid])

    # ---- compare: two things side by side (round 11i) ------------------------------------------------
    def cmd_compare(self, arg):
        try:
            words = shlex.split(arg)
        except ValueError as e:
            raise Refusal(f"could not parse: {e}")
        if len(words) != 2:
            raise Refusal('compare A B   (two ids or quoted titles)')
        w = self.world
        a, b = (self._resolve(x) for x in words)
        sa = w.subjects.get(w.nodes[a]["subject"]) if a in w.nodes and w.nodes[a]["type"] == "appearance" else w.subjects.get(a)
        sb = w.subjects.get(w.nodes[b]["subject"]) if b in w.nodes and w.nodes[b]["type"] == "appearance" else w.subjects.get(b)
        if not sa or not sb:
            raise Refusal("compare needs two things with content, not surfaces")
        out = [f"compare {a} \"{sa['title']}\"  |  {b} \"{sb['title']}\""]
        keys = sorted(set(sa.get("props") or {}) | set(sb.get("props") or {}))
        for k in keys:
            va, vb = (sa.get("props") or {}).get(k, "-"), (sb.get("props") or {}).get(k, "-")
            out.append(f"  {k:10} {va:>24}  |  {vb:<24}" + ("" if va == vb else "   <- differs"))
        for k in ("kind", "due"):
            if sa.get(k) != sb.get(k):
                out.append(f"  {k:10} {str(sa.get(k)):>24}  |  {str(sb.get(k)):<24}   <- differs")
        ta, tb = sa["text"].splitlines(), sb["text"].splitlines()
        if ta != tb:
            only_a, only_b = [l for l in ta if l not in tb], [l for l in tb if l not in ta]
            out.append(f"  text: {len(ta)} vs {len(tb)} lines; {len(only_a)} only in {a}, {len(only_b)} only in {b}")
        tags_a, tags_b = set(sa["tags"]), set(sb["tags"])
        if tags_a != tags_b:
            out.append(f"  tags: only {a}: {','.join(sorted(tags_a - tags_b)) or '-'}; only {b}: {','.join(sorted(tags_b - tags_a)) or '-'}")
        if len(out) == 1:
            out.append("  no differences in props, kind, due, text or tags")
        return "\n".join(out)

    # ---- a1568: persons, a thing with one id for a life; names are labels on it ------------------------------------
    def cmd_person(self, arg):
        w = self.world
        try:
            argv = shlex.split(arg)
        except ValueError as e:
            raise Refusal(f"could not parse: {e}")
        kv = dict(a.split("=", 1) for a in argv if "=" in a)
        words = [a for a in argv if "=" not in a]
        if not words and not kv:
            return persons.listing(w)
        if words[:1] == ["begin"]:
            pairs = []
            for x in [x for x in str(kv.pop("again", "")).split(",") if x.strip()]:
                n, _, e = x.partition(":")
                if not re.fullmatch(r"e\d+", e.strip()):
                    raise Refusal(f"again= takes <name>:<event id>, e.g. again=pike:e718; not {x!r}")
                pairs.append((n.strip(), e.strip()))
            paused = [x for x in str(kv.pop("paused", "")).split(",") if x.strip()]
            if kv or len(words) > 1:
                raise Refusal("person begin [again=<name>:<event>,...] [paused=<name>,...]")
            r = persons.begin(w, pairs, paused)
            self._after_mutation()
            twice = sorted({n for _, n, k in r["plan"] if k})
            return (f"ok {r['event']}: {len(r['made'])} person(s) made; {r['stamped']} past events now name their person "
                    f"(by= unchanged)" + (f"; borne by two persons: {', '.join(twice)}" if twice else "")
                    + f". person lists them; undo {r['event']} takes it all back")
        if not persons.on(w):
            raise Refusal(persons.listing(w))
        if words[:1] == ["new"]:
            if len(words) != 2 or set(kv) - {"kind"}:
                raise Refusal("person new <name> [kind=resident|human|agent|worker]")
            r = persons.new(w, words[1], kv.get("kind"))
            self._after_mutation()
            self._mark_seen(r["created"])
            pid = r["created"]
            return (f"ok {r['event']}: a new person {pid} bears the name {words[1].lower()} from now on"
                    + (f"; earlier: " + ", ".join(f"{persons.label(w, x)} ({x}), who keeps every act before {r['event']}"
                                                    for x in r["earlier"]) if r["earlier"] else ""))
        if len(words) != 1:
            raise Refusal("person [<name or id> [name=<new>]] | person new <name> | person begin (help person)")
        hit = persons.typed(w, words[0])
        if not hit:
            raise Refusal(f"no person called {words[0]!r} (person lists them all)")
        pid, note = hit
        if not kv:
            self._mark_seen(pid)
            return persons.card(w, pid, note)
        if set(kv) != {"name"}:
            raise Refusal("person <name or id> name=<new> renames; nothing else is changed here")
        r = persons.rename(w, pid, kv["name"])
        self._after_mutation()
        self._mark_seen(pid)
        return (f"ok {r['event']}: {pid} is now called {persons.label(w, pid)} (was {r['was']}); their acts, made_by "
                f"and corner follow them. undo {r['event']} takes the name back")

    # ---- why: how a thing got where it is (round 11d; Terra: "where a rule will file a new item felt awkward")
    def cmd_why(self, ident):
        w = self.world
        nid = self._resolve(ident)
        sid = w.nodes[nid].get("subject") if nid in w.nodes else nid
        mine = [e for e in w.events if e["target"] in (nid, sid) or nid in (e.get("changed") or []) or sid in (e.get("changed") or [])]
        head = self.line(nid, 1) if nid in w.nodes else f"{sid} (subject)"
        if not mine:
            return head + "\n  no recorded history: it was here before this session began"
        out = [head]
        for e in mine[-12:]:
            who = persons.by(w, e)
            via = e.get("via")
            how = f" by rule {via.split()[1]}" if via and via.startswith("rule ") else (f" via {via}" if via else "")
            if e.get("tripped_by") and e["tripped_by"] != e["by"]:
                how += f", tripped by {persons.tripped(w, e)}"
            cause = f" (because of {e['cause']})" if e.get("cause") else ""
            done = " (undone)" if e.get("undone") else ""
            args = {k: (v if len(str(v)) <= 120 else str(v)[:117] + "…") for k, v in (e.get("args") or {}).items()}   # a fold, declared
            out.append(f"  {e['id']} {e['verb']} {self._fmt_args(args)}".rstrip() + f" · {who}{how}{cause}{done}")
        # what would happen next: rules whose selection this thing matches but has not been handled by
        pending = []
        for r in self._rules_sync(say=False):
            if r.get("on"):
                continue
            try:
                ids, _ = self._rule_selection(r["sel"], r.get("home"))
            except Refusal:
                continue
            if nid in ids and nid not in r["done"]:
                pending.append(f"{r['id']} would {self._action_text(r)}")
        if pending:
            out.append("  next: " + "; ".join(pending))
        return "\n".join(out)

    # ---- export: the desk as the commands that rebuild it (round 11c) --------------------------------
    def cmd_export(self):
        """Emit desk commands that rebuild this desk from an empty one. Things are named by title, since ids
        are reassigned on replay. Says what it cannot carry (others' comments, resolved state, exact geometry)."""
        w = self.world
        out = ["# export of this desk; replay on an empty desk after one look", "look"]
        if self.today:
            out.append("clock follow" if self.follow else f"clock {self.today}")   # first: texts may mention $today, and age rules need a clock
        titles = {}
        for n in w.nodes.values():
            titles.setdefault(w.title(n).lower(), []).append(n["id"])
        dup = sorted(t for t, ids in titles.items() if len(ids) > 1 and not (
            len({w.nodes[i].get("subject") for i in ids}) == 1))   # several appearances of one subject are fine
        if dup:
            out.append("# WARNING: these titles name several different things, and replay resolves by title: " + ", ".join(dup))

        def q(s):
            # a literal backslash becomes four: shlex halves it, then the do parser halves it again after
            # turning unescaped \n into newlines, so text with a literal backslash-n survives a round trip
            # every $ as \$: a replayed value is what was stored, never a blank filled again (a806)
            return '"' + str(s).replace("\\", "\\\\\\\\").replace('"', '\\"').replace("\n", "\\n").replace("$", "\\$") + '"'

        def ref(nid):
            return "desk" if nid == w.root else q(w.title(w.nodes[nid]))

        placed = set()
        skipped = []

        def walk(fid):
            for k in w.children(fid):
                if k["type"] == "surface" and k["layout"] == "view":
                    out.append(f"do create {ref(fid)} kind=view title={q(k['title'])} query={q(k.get('query', ''))}"
                               + "".join(f" {x}={q(k[x])}" for x in ("cols", "by", "desc") if k.get(x)))
                    continue
                if k["type"] == "surface":
                    out.append(f"do create {ref(fid)} kind=surface title={q(k['title'])} layout={k['layout']}")
                    if k.get("props"):
                        out.append(f"do prop {q(k['title'])} " + " ".join(f"{a}={q(b)}" for a, b in k["props"].items()))
                    walk(k["id"])
                    continue
                s = w.subjects[k["subject"]]
                if s["id"] in placed:
                    out.append(f"do place {q(s['title'])} into={ref(fid)}")
                else:
                    placed.add(s["id"])
                    line = f"do create {ref(fid)} kind={s['kind']} title={q(s['title'])}"
                    if s["text"]:
                        line += f" text={q(s['text'])}"
                    if s["tags"]:
                        line += f" tags={','.join(s['tags'])}"
                    if s.get("due"):
                        line += f" due={s['due']}"
                    out.append(line)
                    if s.get("props"):
                        out.append(f"do prop {q(s['title'])} " + " ".join(f"{k}={q(v)}" for k, v in s["props"].items()))
                    for c in s.get("comments", []):
                        if c["by"] == "alex":
                            out.append(f"do comment {q(s['title'])} line={q(c['text'])}")
                        else:
                            skipped.append(f"comment {c['id']} by {c['by']} on {q(s['title'])}")
                if k["folded"]:
                    out.append(f"do fold {q(s['title'])}")
                if fid != w.root and w.nodes[fid]["layout"] == "free":
                    out.append(f"do move {q(s['title'])} to={k['x']},{k['y']}; do resize {q(s['title'])} to={k['w']}x{k['h']}")

        walk(w.root)
        for l in w.links:
            a, b = w.subjects.get(l["from"]), w.subjects.get(l["to"])
            if a and b:
                out.append(f"do link {q(a['title'])} {q(b['title'])} as={l['kind']}")
        if skipped:
            out.append("# not carried (only you can write as you): " + "; ".join(skipped))
        return "\n".join(out)

    # ---- scripts retired into verbs (a1027): a script was a verb nobody declared ----------------------------------
    scripts = None          # retired: the scripts of worlds from before a1027, kept only to say they never run
    SCRIPTS_DOOR = "scripts are verbs now: make a note tagged verb (help verbs); run X is just X"

    def cmd_scripts(self):
        old = sorted(self.scripts or {})
        return self.SCRIPTS_DOOR + (f"\n  (this world still holds {len(old)} old script(s), {', '.join(old)}; they never run)"
                                    if old else "")

    def cmd_script(self, arg):
        raise Refusal(self.SCRIPTS_DOOR)

    def cmd_run(self, arg):
        import verbs
        name = (arg.split() or ["X"])[0]
        door = f"scripts are verbs now: make a note tagged verb (help verbs); run {name} is just {name}"
        if name != "X" and not verbs.visible(self, name, self.world.me):
            door += f" (nothing answers to {name} yet: make it a verb, or just look)"
        raise Refusal(door)

    def _rule_event_targets(self, r, evs):
        """An event rule's targets among events evs: each matching event names the thing to act on."""
        targets = []
        for e in evs:
            # the log records append/retitle/rewrite as "edit"; name the event by the verb a person would use
            said = e["verb"]
            if said == "edit":
                a = e.get("args") or {}
                said = "append" if "append" in a else "retitle" if "title" in a else "rewrite"
            if (said != r["on"] and e.get("via") != r["on"]) or (r["by"] and e["by"] != r["by"]) \
                    or str(e.get("via", "")).startswith("rule "):
                continue
            t = e["target"]
            if e["verb"] == "create" and isinstance(e.get("undo"), dict) and e["undo"].get("delete"):
                t = e["undo"]["delete"]   # a create happens to the new thing, not to the surface it landed in
            if t in self.world.subjects:
                apps = self.world.appearances_of(t)
                t = apps[0] if apps else None
            if t in self.world.nodes:
                targets.append(t)
        return targets

    def _rule_in_place(self, r, i):
        """A move rule whose thing is already where it would put it: not a firing."""
        if r["verb"] == "move" and r["kv"].get("into"):
            try:
                # a990: into=$here is the rule's home, not the room of whoever tripped it
                into = blanks.fill(self, r["kv"]["into"], ctx=blanks.Ctx("rule", item=i, home=r.get("home")))
                return self._resolve(into, allow_subject=False) == self.world.nodes[i]["parent"]
            except Refusal:
                pass
        return False

    def _rule_pending(self, r):
        """What rule r would fire on in another round, judged without firing or changing its state (a1388)."""
        if r.get("on"):
            ids = self._rule_event_targets(r, self.world.events[r["cursor"]:])
            done = set()
        else:
            try:
                ids = self._rule_selection(r["sel"], r.get("home"))[0]
            except Refusal:
                return []
            done = r["done"]
        return [i for i in dict.fromkeys(ids) if i not in done and i in self.world.nodes and not self._rule_in_place(r, i)]

    ROUNDS = 3   # a rule's action may make another rule fire; each act runs at most this many rounds of rules

    def _run_rules(self, cause=None):
        if self._in_rules:
            return
        active = self._rules_sync()         # a1027: rules are notes; what each one is now is read from the world
        if not active:
            return
        self._in_rules = True
        chain = []   # (round, rule, thing) for each firing in this run, so a stopped chain can be told whole
        try:
            for rnd in range(1, self.ROUNDS + 1):
                fired = False
                for r in active:
                    if r.get("on"):
                        # event rule: each new matching event names the thing to act on
                        evs = self.world.events[r["cursor"]:]
                        r["cursor"] = len(self.world.events)
                        ids, desc = self._rule_event_targets(r, evs), r["sel"]
                        r["done"] = set()   # an event rule fires every time
                    else:
                        try:
                            ids, desc = self._rule_selection(r["sel"], r.get("home"))
                        except Refusal as e:
                            self._note(f"~ {r['id']} could not select ({e})")
                            continue
                        # a1027: a thing that left the selection is forgotten, so entering again fires again (a
                        # commission landed, reverted, then landed once more is due a live check twice)
                        r["done"] &= set(ids)
                    for i in ids:
                        if i in r["done"] or i not in self.world.nodes:
                            continue
                        r["done"].add(i)
                        if self._rule_in_place(r, i):
                            continue
                        n0 = len(self.world.events)
                        revs0 = {k: v["rev"] for k, v in list(self.world.nodes.items()) + list(self.world.subjects.items())}
                        self._mark_seen(i)
                        # a683/a687: a rule is a standing act its author chose, so it acts as its author: events say
                        # by=<author> via=rule rN, and a chat line it adds is the author's own. What gets printed meanwhile
                        # is still the tripper's to have seen (_observer). A rule saved before a656 has no author and
                        # runs as the tripper, its chat line signed 'Name, via rule rN', until someone re-saves it.
                        author, tripper = r.get("author"), self.world.me
                        if author:
                            self._firing_observer, self.world.me = self._observer(), author
                        else:
                            self.world.acting_rule = r["id"]
                        try:
                            receipt = self._fire(r, i)
                            if receipt is not None:     # None: its selection target matched nothing, nothing to do
                                r["fired"] += 1
                                fired = True
                                chain.append((rnd, r, i))
                                self._note(f"~ {r['id']} fired on {i}" + (f" as {author}" if author and author != tripper else "")
                                           + ": " + receipt)
                        except Refusal as e:
                            why = str(e)
                            if "no sill for" in why:
                                # c1075: a sill that isn't there (claude has no corner) is recorded quietly, for rules
                                r["skipped"] += 1
                                r["last_skip"] = f"{i}, " + why[why.index("no sill for"):].split(":")[0]
                            else:
                                r["failed"] += 1
                                r["last_fail"] = f"{i}, {why[:160]}"
                                self._note(f"~ {r['id']} could not {r['verb']} {i}: {e}")
                        finally:
                            self.world.acting_rule = None
                            self.world.me, self._firing_observer = tripper, None
                        for ev in self.world.events[n0:]:
                            ev["via"] = f"rule {r['id']}"
                            if author:
                                ev["tripped_by"] = tripper
                                # a1568 (Pike, c1910): who= is whose rule ran (its author, resolved as it fired);
                                # tripped_who is the person who set it off, kept apart, never folded into who=
                                tw = persons.today(self.world, tripper) if persons.on(self.world) else None
                                if tw and persons.norm(tripper) not in persons.NOT_PERSONS:
                                    ev["tripped_who"] = tw
                            if cause:
                                ev["cause"] = cause
                        # the rule is our own automation: what it changed counts as seen, like our own writes
                        for k, v in list(self.world.nodes.items()) + list(self.world.subjects.items()):
                            if revs0.get(k) != v["rev"]:
                                self._mark_seen(k)
                if not fired:
                    break
            else:
                self._rules_stopped(active, chain, cause)
        finally:
            self._in_rules = False

    def _rules_stopped(self, active, chain, cause):
        """a1388 (Claude e3229, Pike a1356): the last round still fired, so the bound may have cut a chain. What would
        fire in another round is not run; it is said on the receipt, counted on each stopped rule, and told on the sill
        of each author whose rule is in the chain (once per rule until its text changes)."""
        import rooms
        w, tripper = self.world, self.world.me
        stopped = [(r, ids) for r in active for ids in [self._rule_pending(r)] if ids]
        if not stopped:
            return      # the chain ended in the last round: nothing was cut
        names = lambda ids: ", ".join(ids[:5]) + (f" and {len(ids) - 5} more" if len(ids) > 5 else "")
        what = "; ".join(f"{r['id']} on {names(ids)}, by {r.get('author') or '?'}" for r, ids in stopped)
        for r, ids in stopped:
            r["stopped"] = r.get("stopped", 0) + 1
            r["last_stop"] = f"on {names(ids)}, set off by {tripper}" + (f" ({cause})" if cause else "")
        said = (f"~ rules still firing after {self.ROUNDS} rounds: {what}; not run. Each act runs at most "
                f"{self.ROUNDS} rounds of rules (a round runs each rule once, in the order they were made); what was "
                f"stopped fires on the next change if it still matches. rules counts each stop")
        steps = [f"round {rnd}: {r['id']} on {i} (as {r.get('author') or '?'})" for rnd, r, i in chain]
        steps += [f"stopped: {r['id']} on {names(ids)} (as {r.get('author') or '?'})" for r, ids in stopped]
        mine = {}
        for r in [r for _, r, _ in chain] + [r for r, _ in stopped]:
            if r.get("author") and not r.get("told_stop"):
                mine.setdefault(r["author"], {})[r["id"]] = r
        made, told = w.last_created, []
        for who, rs in sorted(mine.items()):
            for r in rs.values():
                r["told_stop"] = True       # kept in the rule's state; a re-save starts it fresh
            if who == tripper:
                continue                    # the ~ line above is theirs to read
            fid = rooms.corner_of(w, who)
            if not fid:
                told.append(f"{who} has no sill to tell")
                continue
            yours = "\n".join(f"- {r['id']} \"{w.subjects[r['sid']]['title']}\""
                              + (" was stopped: it would still fire on " + names(ids) if ids else " fired in it")
                              for r in rs.values() for ids in [next((x for s, x in stopped if s is r), [])])
            text = (f"An act by {tripper}" + (f" ({cause})" if cause else "") + f" set off rules that were still firing "
                    f"after {self.ROUNDS} rounds, so the desk stopped them: each act runs at most {self.ROUNDS} rounds of "
                    f"rules. What was stopped was not run; it fires on the next change if it still matches.\n"
                    f"Your rules in it:\n{yours}\nThe chain:\n" + "\n".join(f"- {s}" for s in steps)
                    + "\nA chain longer than the bound, or rules that undo each other, both end here. rules counts each stop; "
                      "you are told once per rule until its text changes.")
            w.apply("create", fid, None, {"kind": "note", "title": f"your rules were stopped after {self.ROUNDS} rounds",
                                          "text": text}, tripper)
            told.append(f"{who} ({w.last_created})")
        w.last_created = made
        if told:
            said += "\n  told on their sills: " + ", ".join(told)
        self._note(said)

    def _visual_notes(self, n0, styles0=None):
        """a1101 (Pike e2213, Juniper e2201): an edit to a style or a lens says its effect, not only that the text
        changed. A style: whether it parses as the painter parses it, the props the painter cannot read, and each lens
        using it that now refuses. A lens: whether it compiles (lens_ir.check). ~ lines after the receipt."""
        import lens_ir
        import scene
        w = self.world
        touched = []
        for e in w.events[n0:]:
            if e.get("undone") or not aspects_meet(event_aspects(e), {"text", "title", "tags", "prop:style", "contents"}):
                continue
            for i in [e.get("target")] + list(e.get("changed") or []):
                sid = (w.nodes.get(i) or {}).get("subject") or (i if i in w.subjects else None)
                if sid and sid not in touched:
                    touched.append(sid)
        lenses = [s for s in w.subjects.values() if "lens" in (s.get("tags") or []) and w.appearances_of(s["id"])]
        checked = set()
        for sid in touched:
            s = w.subjects[sid]
            tags = s.get("tags") or []
            if "style" in tags:
                c = scene.style_check(s["text"])
                using = [x for x in lenses if str((x.get("props") or {}).get("style", "")).lower() == s["title"].lower()]
                if c["refusal"]:
                    said = (f"~ style {s['title']} does not parse: {c['refusal']}. The painter keeps the last version that "
                            f"parsed (none, on a fresh load: unstyled); fix it with replace, or undo")
                else:
                    said = f"~ style {s['title']} parses: {c['roles']} roles, {c['tokens']} tokens"
                    if c["unread"]:
                        # new ones (by this line) whole, each on its line; the ones it already had, counted by cause
                        was = (styles0 or {}).get(sid)
                        old = {(r, p) for r, p, _l, _w in scene.style_check(was)["unread"]} if was is not None else set()
                        new = [u for u in c["unread"] if (u[0], u[1]) not in old]
                        said += f"; the painter draws nothing for {len(c['unread'])} prop(s)"
                        said += "".join(f"\n  - new: role {r} `{p}` (line {ln}): {why}" for r, p, ln, why in new[:8])
                        if len(new) > 8:
                            said += f"\n  - and {len(new) - 8} more new"
                        byw = {}
                        for r, p, _ln, why in c["unread"]:
                            if (r, p) in old:
                                byw.setdefault(why, []).append(p)
                        for why, ps in byw.items():
                            said += f"\n  - already there, {len(ps)}: {why}: " + ", ".join(f"`{p}`" for p in dict.fromkeys(ps))
                bad = []
                for x in using:
                    ok, line = lens_ir.check(self, x)
                    checked.add(x["id"])
                    if not ok:
                        bad.append(line)
                said += (f"\n  lenses using it: {', '.join(x['title'] for x in using)}; "
                         + ("all compile" if not bad else f"now refusing: {len(bad)}")) if using \
                    else "\n  no placed lens says style=" + s["title"]
                self._note(said + "".join(f"\n  ! {b}" for b in bad))
            if "lens" in tags and sid not in checked and w.appearances_of(sid):
                checked.add(sid)
                ok, line = lens_ir.check(self, s)
                self._note(("~ " if ok else "~ ! ") + line)

    def _note(self, text):
        self._rule_notes = (self._rule_notes or []) + [text]

    def snapshot(self):
        snap = self.world.snapshot()
        self._rules_sync(say=False)
        snap["rules"] = [{"id": r["id"], "text": " ".join(self._rule_line(self.world.subjects[r["sid"]])[:1]),
                          "on": r.get("on"), "by": r.get("by"), "author": r.get("author"), "home": r.get("home"),
                          "when": None if r.get("on") else r.get("sel"), "verb": r.get("verb"), "broken": r["broken"],
                          "fired": r.get("fired", 0), "failed": r.get("failed", 0), "skipped": r.get("skipped", 0), "stopped": r.get("stopped", 0)}
                         for r in (self._rulestate or {}).values()]
        snap["clock"] = {"today": self.today, "follow": bool(self.follow)}
        return snap

    follow = False      # clock follow: today is the wall date, read at every command; time passes on its own
    last_here = None    # when the last command ran (wall time), so the desk can say how long you were away

    def _tick(self):
        """Following the wall clock: notice a new day (and run the rules for it), or a long absence."""
        if not self.follow or self._in_rules:
            return None
        from datetime import datetime
        now = datetime.now()
        wall, last, note = now.date().isoformat(), self.last_here, None
        away = ""
        if last:
            hours = (now - last).total_seconds() / 3600
            away = (f"; you were last here {int(hours // 24)} day(s) {int(hours % 24)} h ago" if hours >= 24
                    else f"; you were last here {hours:.0f} h ago" if hours >= 1 else "")
        if wall != self.today:
            n = self.world.days_between(self.today, wall) if self.today else 0
            self.today = self.world.today = wall
            self._run_rules(cause=None)
            note = f"~ {n} day(s) passed: today is {wall}{away}"
        elif away:
            note = "~ same day" + away
        self.last_here = now
        return note

    _ctxs = None        # a806: where lines are being filled, innermost last (blanks.Ctx); empty for a typed line
    _reply = None       # the reply the current top-level call belongs to (the caller's token, or one per call)
    _made = None        # {reader slot: (reply, ids made most recently in that reply)}: what $new reads next
    _taught_new = None  # the reply whose receipt last taught $new (a948 (6)): once per reply

    def dispatch(self, name, args):
        if not self._ctxs:
            # lines sent one by one (deskd, explore, the house) share the caller's reply token; without one, the
            # lines of one call are one reply, and a later call starts a new one
            import uuid
            self._reply = args.get("reply") or uuid.uuid4().hex
        return super().dispatch(name, args)

    def _echo(self, part):
        """A step of a verb, script or rule is echoed as it runs, its blanks filled: a receipt shows values (a806 (5));
        a typed line is echoed as it was typed."""
        ctx = blanks.ctx_of(self)
        return blanks.show(self, blanks.protect(part), ctx) if ctx.template else part

    def _slot(self):
        return str(self.world.me) + ("/" + self._window if getattr(self, "_window", "") else "")

    def _one(self, args, name="desk", whole=False):
        top = not self._ctxs
        if top:
            # a typed line: $new is what this reader made most recently in this same reply, never in an earlier one
            rec = (self._made or {}).get(self._slot())
            self._ctxs = [blanks.Ctx("typed", prev=rec[1] if rec and rec[0] == self._reply else None)]
        try:
            return self._one_filled(args, name, whole, top)
        finally:
            if top:
                self._ctxs = None

    def _one_filled(self, args, name, whole, top):
        if top:
            import verbs
            verbs.bind_unbound(self)      # a1156: once per world, lines saved before bindings bind to what they mean now
            for sid in self.world.chats_without_lines():
                self.world.chat_lines(sid)        # a1581: once per chat, its lines become things (one event each)
        tick = self._tick()
        if tick:
            self._rule_notes = [tick] + (self._rule_notes or [])
        n0 = len(self.world.events)
        # a1101: each style as it stood before this line, so its receipt can say which unreadable props are new
        styles0 = {s["id"]: s["text"] for s in self.world.subjects.values() if "style" in (s.get("tags") or [])} if top else {}
        ctx, self._filled_new = self._ctxs[-1], None
        r = super()._one(args, name, whole)
        if self._filled_new:
            # a806 (10): the receipt names what $new was, so a $new that meant something else is seen at once
            key = "text" if "text" in r else "error"
            r[key] += f"\n  ($new = {self._filled_new})"
            self._filled_new = None
            self._taught_new = self._reply          # they know the word already: no lesson in this reply
        # what this line made itself, before the rules act on it; $new is the most recent thing made in this reply
        made = blanks.made_by(self.world.events[n0:])
        if top and made and "text" in r and self._taught_new != self._reply:
            # a948 (6): an id guessed for a thing just made (a943 for a948) is the habit $new replaces; the lesson
            # comes once per reply, on the receipt, exactly where the guess would be
            r["text"] += "\n  (next lines in this reply can call it $new)"
            self._taught_new = self._reply
        ctx.prev = made or ctx.prev
        if top:
            self._made = dict(self._made or {})
            self._made[self._slot()] = (self._reply, ctx.prev)
        if len(self.world.events) > n0:
            # after the receipt is composed, so the receipt describes the command, then the rules; the command's
            # last event is the cause of whatever the rules do, so one undo takes both back
            self._run_rules(cause=self.world.events[-1]["id"])
            if top:
                self._visual_notes(n0, styles0)
        if self._rule_notes:
            key = "text" if "text" in r else "error"
            r[key] = r[key] + "\n" + "\n".join(self._rule_notes)
            self._rule_notes = None
        return r

    today = None   # set by the clock command; `today` in a due< / due> term stands for it

    def cmd_clock(self, arg):
        if not arg:
            if self.follow:
                from datetime import datetime
                return f"today is {self.today}, {datetime.now():%H:%M}; following the wall clock (clock YYYY-MM-DD stops following)"
            return f"today is {self.today}" if self.today else "no clock set. clock follow keeps today on the wall date; clock YYYY-MM-DD sets it by hand"
        if arg == "follow":
            from datetime import date, datetime
            wall, w = date.today().isoformat(), self.world
            ahead = [e for e in w.events if (e.get("day") or "") > wall]
            for e in ahead:
                e["day"] = wall   # days that were simulated by hand: they happened no later than today
            self.follow, self.today, w.today, self.last_here = True, wall, wall, datetime.now()
            self._run_rules(cause=None)
            return (f"ok following the wall clock: today is {wall}. Days pass on their own now; the desk says so on the first command of a new day"
                    + (f"\n  {len(ahead)} event(s) carried simulated dates after today; they now count as today" if ahead else ""))
        self.follow = False
        if arg == "now":
            from datetime import date
            arg = date.today().isoformat()   # the wall clock, read once, as a command: still nothing advances on its own
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", arg):
            raise Refusal("clock YYYY-MM-DD, or clock now")
        prev, self.today = self.today, arg
        self.world.today = arg
        self._run_rules(cause=None)
        out = f"ok today is {arg}"
        if prev and arg < prev:
            w = self.world
            future = sum(1 for i in w.nodes if (w.last_day(i) or "") > arg)
            if future:
                out += f"\n  the clock went back from {prev}: {future} thing(s) were last touched after {arg}; their age is negative until the clock passes them"
        return out

    def _selection_terms(self, token):
        """Titles are allowed wherever a selection term wants an id: in:Today, also:"Standup agenda", links:Tessera.
        `today` in a due term is the clock's date."""
        out = []
        if "today" in token:
            if not self.today:
                raise Refusal("today is unset; clock YYYY-MM-DD sets it")
            token = token.replace("today", self.today)
        for t in re.split(r",", token):
            for key in ("in:", "also:", "links:", "parts:", "part-of:", "answers:", "answered-by:"):
                if t.startswith(key) and t[len(key):] not in self.world.nodes and t[len(key):] not in self.world.subjects:
                    t = key + self._resolve(t[len(key):].strip('"'))
            out.append(t)
        return ",".join(out)

    def _parse_selection(self, token):
        return knife.parse_selection(self.world, self._selection_terms(token.strip()))

    def _trash_note(self, token):
        """a1327: what a selection left out because it is in the Trash, said so the leaving out is never silent."""
        try:
            n, bins = knife.trash_left_out(self.world, self._selection_terms(token.strip()))
        except Refusal:
            return ""
        return f"{n} in the Trash left out (add in:{bins[0]} to see them)" if n else ""

    def cmd_find(self, words):
        # round 11b: find also takes a selection, which is the scalable listing view (examine is one thing in depth)
        sel = self._parse_selection(words) if words.strip() else None
        if sel is not None:
            ids, desc = sel
            aside = self._trash_note(words)
            if not ids:
                return f"find {desc}: nothing matches" + (f"; {aside}" if aside else "")
            w = self.world
            by_parent = {}
            for i in ids:
                by_parent.setdefault(w.nodes[i]["parent"], []).append(i)
            out = [f"find {desc}: {len(ids)} thing(s)" + (f"; {aside}" if aside else "")]
            cap = 8
            for p, kids in by_parent.items():
                out.append(f"  in {p} \"{w.title(w.nodes[p])}\":")
                out.extend("    " + self.line(i, 1) for i in kids[:cap])
                if len(kids) > cap:
                    more = f"look {p} :2 shows all of it" if "in:" in words else f"find {words.strip()},in:{p} lists them"
                    out.append(f"    (+{len(kids) - cap} more here; {more})")
            out.append(f"  as a selection: {words.strip()}   e.g. do move {words.strip()} into=<surface>   (help selections)")
            return "\n".join(out)
        text = super().cmd_find(words)
        q = "+".join(words.lower().split())
        if q and not text.endswith(": nothing"):
            n = text.split(":")[1].split()[0] if ":" in text else "?"
            text += f"\n  as a selection: ?{q}   e.g. do move ?{q} into=<surface> one=1   (help selections)"
        return text

    def repl(self, line):
        line = (line or "").strip()
        if not line:
            return HELP_KNIFE
        # a806: blanks are filled after the line is parsed, as values, by the one filler (blanks.py); a script is
        # defined as written. \$ is a literal dollar sign: it is set aside here, before any parser can eat the backslash
        if not line.lower().startswith("script "):
            line = blanks.protect(line)
        words = line.split(None, 1)
        cmd = words[0].lower()
        arg = words[1].strip() if len(words) > 1 else ""
        if arg and cmd not in ("do", "rule", "run", "script") and (blanks.ctx_of(self).template or cmd in blanks.READS):
            # words that name things (look $new, go $here); inside a verb or script, every command's words
            arg = blanks.fill(self, arg, quote=True)
            line = words[0] + " " + arg
        if cmd == "rest":
            import rooms
            return rooms.cmd_rest(self, arg)
        if cmd == "go":
            import rooms
            return rooms.cmd_go(self, arg)
        if cmd == "wake":
            import rooms
            return rooms.cmd_wake(self, arg)
        if cmd == "look":
            import rooms           # a678: a bare look narrates the room you are in; a948: look <room> narrates that
            if rooms.narrates(self):   # room, from wherever you are; look <room> :2 and look <anything else> keep the tree
                fid = rooms.look_target(self, arg) if arg else rooms.room_of(self.world, self.world.me)
                if fid:
                    return rooms.narrate(self, fid)
        if cmd in ("person", "persons"):
            return self.cmd_person(arg)
        if cmd == "rules":
            return self.cmd_rules()
        if cmd == "rule":
            return self.cmd_rule(arg)
        if cmd == "export":
            return self.cmd_export()
        if cmd == "why":
            return self.cmd_why(arg)
        if cmd == "compare":
            return self.cmd_compare(arg)
        if cmd == "table":
            return self.cmd_table(arg)
        if cmd == "sync":
            # the harness writes as another actor: its changes are not "seen" by you; the delta header names them
            return "sync:\n" + "\n".join(harness.sync(self))
        if cmd == "vars":
            return "\n".join(f"${k} = {v}" for k, v in (self.vars or {}).items()) or "no handles. set name = <id or title>, or create ... as=name; then $name names it"
        if cmd == "set":
            name, eq, val = arg.partition("=")
            name, val = name.strip().lstrip("$"), val.strip()
            if not eq or not name or not val or " " in name:
                raise Refusal("set name = <id or title>")
            self.vars = self.vars or {}
            self.vars[name] = self._resolve(val)
            return f"ok ${name} = {self.vars[name]}"
        if cmd == "rows":
            import scene
            try:
                return scene.rows_text(self, arg.strip())
            except scene.LensRefusal as e:
                raise Refusal(str(e))
        if cmd == "scene":
            # the same tree the painter draws, printed: what is shown, where, and what each gesture would do
            import scene
            if not arg.strip():
                raise Refusal("scene <lens name> [<part path> | ok]. A lens is a note tagged lens; help scene")
            try:
                name, rest = scene.split_scene_arg(self, arg)
                if rest == "ok":
                    import lens_ir
                    return lens_ir.check(self, scene.find_lens(self, name), ages=True)[1]
                sc, text = scene.scene_for(self, name, rest)
            except scene.LensRefusal as e:
                raise Refusal(str(e))
            w = self.world

            def walk(n):
                # Juniper (reads case): a lens print that showed a status has shown it; each node says what it printed
                if n.get("item") in w.nodes and n.get("shown"):
                    self._mark_seen(n["item"], n["shown"])
                    if w.nodes[n["item"]].get("subject"):
                        self._mark_seen(w.nodes[n["item"]]["subject"], n["shown"])
                for fid, asp in (n.get("fshown") or {}).items():
                    if fid in w.nodes or fid in w.subjects:
                        self._mark_seen(fid, asp)
                for k in n.get("kids") or []:
                    walk(k)
            for n in sc.get("printed") or [sc]:      # a1101: only what was printed has been seen
                walk(n)
            return text
        if cmd == "clock":
            return self.cmd_clock(arg)
        if cmd == "scripts":
            return self.cmd_scripts()
        if cmd == "script":
            return self.cmd_script(arg)
        if cmd == "run":
            return self.cmd_run(arg)
        if cmd in ("help", "?"):
            if not arg:
                return HELP_LEAN if self.lean else HELP_KNIFE
            return "\n\n".join(self.cmd_help(a.lstrip("@")) for a in arg.split())
        if cmd == "do":
            try:
                argv = [a.lstrip("@") for a in shlex.split(arg)]
            except ValueError as e:
                raise Refusal(f"could not parse: {e}")
            if len(argv) < 2:
                raise Refusal("do needs: do <verb> <target> [k=v ...]")
            verb = argv[0].lower()
            is_target = is_target_word      # a selection term is the target, = or not (Juniper; see SEL)
            # tier 1: `do sweep porch` may name a verb made in the world; a990: so may a retired built-in's word (tidy,
            # reply, stack ...), which this desk only refuses, so a world verb answers it first
            if verb not in self._builtin_verbs() or verb in knife.SPECIALIZED:
                import verbs
                hit = verbs.try_line(self, arg, self.world.me)
                if hit is not None:
                    return hit
            # a806: each value is filled once, after parsing: targets always; each k=v by what the verb's own
            # argument list says it is (a965: text is words by default; blanks.fill_arg)
            positional = [blanks.fill(self, unescape_value(a)) for a in argv[1:] if is_target(a)]   # titles carry escapes too
            kv, kept = {}, []
            for a in argv[1:]:
                if "=" in a and not is_target(a):
                    k, _, v = a.partition("=")
                    kept += blanks.kept(self, verb, k, unescape_value(v))
                    kv[k] = blanks.fill_arg(self, verb, k, unescape_value(v))
            out = self.cmd_do_knife(verb, positional, kv)
            return out + "\n  " + blanks.kept_note(kept) if kept else out
        return super().repl(line)

    HELP_TOPICS = {
        "rooms": """rooms: you are always in one room. A room is a surface with prop role=room (a corner, role=resident, is its
  resident's room). Its props: describe=<id> its description, talk=<id> the chat where talk here lands,
  shows=<selection> what is at hand (default: what is inside it), home=<in:|tag: selection> where things made here land.
  go <room>        walk there, from anywhere, by id or a word of its title (go lounge); prints the room
  go <room> :1     walk without looking            go alone: where you are, and who is in each room
  look             with no id: the room you are in: the date and time, its description, who is here, what is at hand
                   (one id each), the last lines said here. Only what it prints whole counts as seen: look <id> or read
                   before changing a thing listed at hand.
  look <room>      the same for any room, from where you are (it says so); look <room> :2 is the tree. look <id> on
                   anything that is not a room is the tree, as always.
  rest             go home to your corner (Home if you have none); history marks it via=rest
  wake <name>      call a resting resident now, without a line: their wake says you called. An @name or @everyone
                   in a chat (outside quotes) wakes them too, from anyone; your line comes first in their wake,
                   marked for them, and the receipt says whom it took and what happened ('Pike: woken'; a1566)
  $here            the room you are in, in any target or value: do move a12 into=$here; $here.talk its chat, so
                   a verb can say: do append $here.talk line="$*" (help blanks)
  Where you are is kept in the world (history lists each go) but undo leaves it: go back instead. Someone who never
  went anywhere is in their own corner, or in Home (Jeff too). Resting sends a resident home to their corner. A
  resident asleep (want=rest on their corner) is never 'here with you': the room says they are asleep here. One
  between turns is named '(resting)'; one in a turn right now, or anyone the house does not run, is named plain.
  Verbs by room (shown, never locked): examine and verbs list the layout verbs (move to=/by=, resize, raise, lower,
  tile, untile, fold, unfold, match) only in a room whose prop verbs=layout says so (the Desktop) and the rooms
  inside it; elsewhere one line says where they are. They work from anywhere, as always. A verb made in the world
  can live on a room (on=<room>): its bare word works there; from elsewhere, use <id> (help verbs).""",
        "commissions": """commissions: a worker changes what the world can't (the desk's code, the house, the painter) for you.
  Write a task with prop commission=asked; its text says what you want, why, and how you'll know it's done:
    do create <place> kind=task title="..." commission=asked text="What: ... Why: ... Done when: ..."
  The house gives it to a disposable worker with real tools, in its own copy of the code. The worker talks to you in
  comments on the task (to widen its scope, to put a decision to you, or when it's stuck); answer with
    do comment <task> line="..."
  When it's done, the house lands it between turns: checks the host is still whole, and reverts it if not. The task
  shows where it is: commission=asked|working|waiting|ready|landing|landed|reverted|failed. Set commission=cancelled
  to stop it. Most things don't need a worker: views, styles, notes and verbs (help verbs) change in the world itself.
  The queue: at most `workers` run at once (a prop of the note The house; 1 unless it says more). Asked tasks wait
  and start in the order they were made, whether they were made asked or set asked later. See it with
    find prop:commission=asked      (waiting)      find prop:commission=working      (holding a slot)""",
        "rules": """rules: the desk acts on its own when things change. A rule is a note tagged rule, placed in the room it
  acts from; its text is one line (# lines describe it):
    when <selection> do <verb> [target] [k=v ...]   fires once on each thing that enters the selection
                                                    (now=1: also on what matches when it is saved)
    on <verb> [by=<actor>] do <verb> [target] [k=v]  fires on each such event, on the thing it happened to
  target is the thing itself unless you name one: when in:Today do sort Today by=due. A selection target that
  matches nothing is nothing to do. The action may be a verb made in the world: when tag:messy do tidy (its words;
  $item when none are given), or use <verb id> [words].
  A rule is a template: its values are filled when it fires: $item the thing it fired on, $item.title,
  $item.<prop> one of its props, $item.maker who made it, $today, $here (help blanks). corner:<name> is the corner
  whose actor= is that name: a sill (a missing one is skipped quietly, and rules counts it).
  It lives in the room holding its note: $here is that room. A verb word made in the world is bound when the rule is
  saved, to the verb it means there then (the receipt says which); moving the note moves $here, never its words.
  A bound verb that is removed makes the rule fail, saying so; it never finds another. It acts as whoever last chose what it does: its maker, or the last to write its text or tag
  it rule (their receipt says so). It is checked whenever its text, home or author changes; one that fails is saved
  broken, says why, and never fires until fixed. When it is (re)saved, what already matches counts as handled.
  Quiet: a narrated look never lists rules; the tree marks them. rules lists every one: its home, who it acts as,
  how often it fired, failed, was skipped or stopped by the bound, and whether it is broken; examine <rule note>
  says the same.
  A rule's actions print as ~ lines after your command's receipt; undo of your command undoes them too.
  Rules can trip rules, in rounds: a round runs each rule once, in the order they were made, and each act runs at
  most 3. When a fourth would still fire something, it is not run: a ~ line says which rules, on what, by whom
  (they fire on the next change if it still matches), each such rule counts a stop, and each author whose rule is
  in the chain gets a note on their sill naming their rules and the chain, once per rule until its text changes.
  why <id> shows how a thing got where it is and which rule would act on it next.
  e.g. do create $here kind=note tags=rule title="Fixed goes to Done" text="when tag:fixed do move into=Done\"""",
        "scripts": """scripts are verbs now: a script was a verb nobody declared. Make a note tagged verb (help verbs), and
  say its word: run X is just X. script, run and scripts only say so.""",
        "views": """views: a surface whose contents are a selection, evaluated at every look. Nothing is in it; it lists
  whatever matches, wherever that is, with (in fXX) after each line. Change a thing and it appears or leaves.
  do create <surface> kind=view title=<str> query=<selection>      e.g. query=kind:task,due<today
  do prop <view> query=<selection>    changes what it shows (judged as find judges a selection; undo takes it back)
  with cols=a,b [by=col] [desc=1] the view is a table at every look (help table)
  house columns: made_by made_at (its create) and edited_by edited_at (its latest edit), read from the house's own
  record, never from props. The create's receipt names a column that matches nothing on any thing shown""",
        "scene": """scene <lens>: print the scene a lens makes of the world right now. The painter in the browser draws the very
  same tree, so this is what the other person sees: each part, its words, its role, its place, and the desk
  command each gesture would send. A lens is a note tagged lens; its text is the description (grammar: the
  docstring of scene.py; help lens). Edit a lens with rewrite like any note; the picture follows.
  scene <lens> <part path>   only that part and what is inside it, each match under its full key (= porch/main/people).
                   A path is part names or key segments, matched at the end: people, people/list, list/f571.
                   Only what it prints counts as seen.
  scene <lens> ok  one line: compiles, its node count against the budget, and its style; or the refusal
                   with the lens line it names.
  The name may be quoted ("scratch lens") or bare, spaces and all. A lens with no style= says so on the scene's
  first line (no style=; using the default (calm)); do prop <lens> style=<name> chooses one.
  Receipts: editing a lens (create, rewrite, replace, append, prop, tag) adds a ~ line: compiles, or the refusal.
  Editing a style (a note tagged style) says whether it parses as the painter parses it, the props the painter
  draws nothing for (new ones by name, the rest counted), and every placed lens with style=<it> that now refuses.
  count <selection>, on a part, is how many things match without drawing them: text "$count paused",
  count kind:task,prop:status=paused. On a repeat, $count is its true size before any clamp and $n what it shows.""",
        "worktree": """worktree: work apart from a shared desk, then come back as commands.
  worktree fork <name>    copy this world into <session>@<name>; enter it as its own session
  worktree                list them (inside one: where it came from and how much is journalled)
  worktree diff <name>    the commands made there, and what this desk did since (! = both touched it)
  worktree merge <name>   replay those commands here, signed by who made them, all or nothing. A command whose
                          target someone else changed since the fork is refused, and then nothing is applied.""",
        "clock": """clock: clock follow keeps today on the wall date: days pass on their own, the rules run when a new day is
  noticed, and the first command after an absence says how long you were away. clock alone shows the date and hour.
  clock YYYY-MM-DD (or clock now) sets today by hand, re-evaluates the rules, and stops following.
  today in due< / due> terms is the clock's date; $today in a target or value (not in words you type: help
  blanks); age<N / age>N select by days since a
  thing was last touched (undo is not touching). examine prints when: with the last touch.""",
        "handles": """handles: names for ids. do create ... as=draft, or set draft = <id or title>; then $draft names it.
  vars lists them. $new is the thing made most recently in this reply (help blanks).""",
        "blanks": blanks.HELP,
        "export": "export: prints the commands that rebuild this desk from an empty one, by title. Replay them after one look.",
        "trials": """trials: model runs as things on the desk.
  do create <surface> kind=trial title=<str> then do prop <trial> task=home2 variant=lean model=gpt-5.6-sol
  do launch <trial>        starts it in the background; external effect, undo cannot take it back
  sync                     brings finished trials in, as the actor harness: props status/pass/score/calls/seconds,
                           a comment with the model's reply, and a linked transcript doc (## call N sections)
  prop:status=running / prop:pass=0 select trials; rule on prop by=harness watches results arriving""",
        "why": "why <id>: the events that put a thing where it is (by whom, via which rule, because of what) and which rule would act on it next.",
        "table": """table <selection> [cols=a,b,c] [by=col] [desc=1]: one row per matching thing, props side by side.
  columns: id title kind tags due in age words, and any prop name; without cols= every prop present is a column.
  house columns made_by made_at edited_by edited_at come from the house's record (its create, its latest edit), never
  from props; a column that names nothing on any row is said after the table.
  e.g. table kind:trial cols=task,model,score,calls by=calls desc=1      table in:Today cols=due,age""",
        "find": """find <words> searches titles and text; find <selection> lists what matches, grouped by surface (8 per surface,
  then a pointer). Both end with the selection form to act on: do move <selection> into=<surface>. help selections.""",
        "read": """read <id> shows a text's sections with word counts; read <id> #<n> or #<name> one section (names may have
  spaces); read <id> :3 all of it; tail=<n> the last n lines of what was asked for.
  A chat: read <id> shows only the lines added since you last read it (yours too), under one header; the first time,
  its last 10. Rewriting a chat needs you to have seen every line once (read <id> :3).""",
        "sync": "sync: brings finished trials in as the actor harness (props, a comment with the reply, a transcript doc). help trials.",
        "compare": "compare <A> <B>: two things side by side, line by line, with what differs marked.",
    }

    # a1308: help knows every command a person can type, not only the verbs (s1286 (4): the Board says 'history lists
    # every event', and help history answered 'no verb history here'). One entry per command word, aliases pointing at
    # theirs; HELP_TOPICS answers first for a command that has a longer topic (find, read, rules, scene ...).
    # test_house_words.py checks that every desk word (verbs.DESK_WORDS) is answered here or there.
    COMMAND_HELP = {
        "look": """look [id] [:1|:2|:3|:4]: what is there. look alone, in a world with rooms: the room you are in, narrated
  (help rooms); look <room> narrates that room from where you are. look <id> is the tree from it: :1 its one line,
  :2 its children (the default), :3 everything under it with first lines, :4 with full text. On an event, comment
  or link id (e12, c40, l41) it prints that record, as examine does.""",
        "examine": """examine <id> (or x, ex): one thing in depth: its line, its text's first lines, comments, links, where it
  is, and every verb that applies to it now, with the verbs at hand in your room. examine <e12|c40|l41>: an event
  (who did what, when, why, what it caused, how to undo it), a comment (its text, replies, open or resolved) or a
  link (its two ends).""",
        "history": """history [id]: the latest events, newest last, each with its event id (e12): who did what to which id, via
  which verb or rule, and (undone) when taken back. history <id> only those about one thing. history <e12> that
  event, what it caused and its undo; history <c40|l41> a comment's or link's making, closing and removal.
  examine <e12> explains one event; undo <e12> takes it back; why <id> tells how a thing got where it is.
  history <person> (a name, pike,first, or an id like p1895): what that person did. help person""",
        "person": persons.HELP,
        "go": "go <room>: walk to a room, by id or a word of its title (go lounge), and see it; go <room> :1 walks without "
              "looking; go alone says where you are and who is in each room. help rooms",
        "rest": "rest: go home to your corner (Home if you have none); history marks it via=rest. In the house a resident "
                "also says > rest, or > rest 2 hours, to stop until someone calls (or until then). help rooms",
        "wake": "wake <name>: call a resting resident now; their wake says you called, and which of your lines was "
                "waiting for them. help rooms",
        "where": "where <id>: a thing's exact place: screen rectangle, the surface it is in, its local position and "
                 "layer, and what it overlaps or sits beside.",
        "verbs": None,      # help verbs: the world's verbs (verbs.HELP), then this command (below)
        "pivot": "pivot <id>: an appearance's subject and every place it appears; on a subject, its appearances. One "
                 "subject (what a thing says) can appear on several surfaces; editing it changes them all.",
        "undo": "undo [e12]: take an event back (and whatever a rule did because of it). undo alone takes back your latest "
                "change. An event a later change built on is refused until that is undone first. history lists ids.",
        "do": """do <verb> <target> [k=v ...]: change something. The target is an id, a quoted title or a selection (help
  selections); values with spaces are quoted. The verb is a built-in one (help <verb>: move, create, append, prop ...)
  or a verb made in the world (help verbs). examine <id> lists the verbs that apply to a thing. You must have looked
  at a thing since it last changed: the desk refuses otherwise, and says why.""",
        "open": "open <surface>: unfold it in your later looks (a view of yours; nothing moves). close <surface> folds it.",
        "close": "close <surface>: fold it in your later looks (a view of yours; nothing moves). open <surface> unfolds it.",
        "rule": "rule: rules are notes now (a note tagged rule, in the room it acts from); rule only says how to write "
                "one. help rules",
        "vars": "vars: the handles you named ($draft = a12). help handles",
        "set": "set <name> = <id or title>: name a handle, then $name means it in any line. help handles",
        "rows": "rows <source>: the rows a lens repeats over, with their fields ($title, $by ...); rows alone lists the "
                "sources. help lens",
        "script": "script, run and scripts are retired: a script is a verb now (help verbs); run X is just X.",
        "use": "use <verb id> [words]: run exactly that verb, from anywhere (when a bare word is at hand in several rooms, "
               "or a stored line must name its door). help verbs",
        "help": "help [word ...]: the manual. help <command>, help <verb> (built-in or made in the world), help <topic> "
                "(rooms, rules, views, selections, blanks, lens, verbs, commissions ...), help <id> examines the thing.",
        "plan": "plan / apply: an outline-editing desk's commands; this desk changes things with do.",
    }
    # a1308 (3), the words check: the nouns the house names itself by, asked as a newcomer asks (help chat, help ids).
    # A verb made in the world answers its word first (card is a house verb); a built-in verb (link, comment) keeps its own
    NOUN_HELP = {
        "ids": "ids: every id the house prints can be typed back. f02 a surface or room; a05 a thing on a surface (an "
               "appearance); s03 what a thing says, its subject (one subject can appear in several places); e12 an "
               "event (history lists them; examine e12 explains one; undo e12 takes it back); c40 a comment (examine "
               "c40; do resolve c40 closes it); l41 a link between two subjects (examine l41); m42 a chat line "
               "(examine m42: who said it, when, to whom).",
        "events": "events: every change is an event, e12, signed by who made it. history lists the latest; history <id> "
                  "those about one thing; examine e12 one event (when, why, what it caused); undo e12 takes it back. "
                  "The !! line atop a reply names the events by others since your last look. A ~ line under it says "
                  "someone changed a note or task you made: who, which line, the event and its undo (~ pike replaced "
                  "line 8 of your a12 \"Plan\" (e40; undo e40)); several edits by one person to one note in an hour "
                  "are one line with a count. Chats, comments and what your own rule did are not told this way.",
        "comments": "comments: remarks on a thing, each with an id (c40), open until resolved. do comment <id> line=\"...\" "
                    "adds one; read <id> lists them; examine c40 shows one; do resolve c40 line=\"...\" answers and closes it.",
        "links": "links: a relation between two subjects, as=refers (default), answers, blocks or part-of, each with an "
                 "id (l41). do link A B as=answers makes one; examine l41 shows it; find links:A lists A's; do unlink A "
                 "id=l41 removes it. help selections for answers:, part-of: and links: terms.",
        "note": "a note is a thing with a title and text. do create <surface> kind=note title=\"...\" text=\"...\"; read, "
                "rewrite, replace, append change it. When someone else changes a note you made, your next reply says "
                "so in a ~ line (help events). Tagged verb it is a verb (help verbs); tagged rule, a rule; tagged "
                "lens, a lens.",
        "task": "a task is a note with a status: the Board's cards are tasks (card <title> makes one where you are, if "
                "the house has that verb). do create <surface> kind=task title=\"...\"; do prop <id> status=done.",
        "chat": "a chat is a thing whose text is lines said, one per line, signed. do append <chat> line=\"...\" says "
                "one; read <chat> shows what is new to you. A room's talk= chat is where say lands. examine a chat says "
                "what awaits a reply. Each line is a thing, m42: it keeps who it addresses (each @name outside quotes, "
                "or to=<names>; the receipt says to: ...), and examine m42 says who said it and when. A changed line "
                "shows (edited) and keeps its words before; rows lines:<chat> lists the lines.",
        "doc": "a doc is a long text with ## sections: read <id> shows the outline, read <id> #<n> one section, "
               "read <id> :3 all of it. do create <surface> kind=doc title=\"...\".",
        "surface": "a surface holds things, laid out free, as a column, row or grid; it may be a room (help rooms) or a "
                   "view (help views). look <id> :2 lists what is on it; do create <surface> kind=surface title=\"...\".",
        "resident": "a resident is an agent who lives in the house: its corner is a room with role=resident and actor=<its "
                    "name>; the house wakes it and runs its > lines. corner:<name> names a resident's corner. help rooms",
        "house": "the house keeps the residents alive (it wakes them, runs their > lines, lets them rest) and gives "
                 "commissions to workers. Verbs on=house work everywhere. help rooms, help commissions",
    }
    NOUN_ALIAS = {"id": "ids", "event": "events", "comment": "comments", "link": "links", "notes": "note",
                  "tasks": "task", "chats": "chat", "docs": "doc", "surfaces": "surface", "corner": "resident",
                  "corners": "resident", "residents": "resident", "worker": "commissions", "workers": "commissions",
                  "commission": "commissions"}
    COMMAND_ALIAS = {"x": "examine", "ex": "examine", "?": "help", "run": "script", "scripts": "script", "apply": "plan",
                     "persons": "person"}

    def _command_help(self, name):
        """-> the help for a command word, or None. HELP_TOPICS answers first where it has the word."""
        name = self.COMMAND_ALIAS.get(name, name)
        if name in self.HELP_TOPICS:
            return self.HELP_TOPICS[name]
        return self.COMMAND_HELP.get(name)

    def _commands(self):
        """The command words help lists when it doesn't know a word: each answers help <it>."""
        import verbs
        return [w for w in sorted(verbs.DESK_WORDS) if w not in ("?", "x", "ex", "plan", "apply", "script", "scripts", "run", "persons")]

    def cmd_help(self, name):
        name = name.lower()
        rec = self.record_text(name)       # a1308: help e12 is examine e12, as help <thing> is
        if rec:
            return rec
        if name in self.HELP_TOPICS:
            return self.HELP_TOPICS[name]
        if name in self.COMMAND_HELP and name != "verbs" or name in self.COMMAND_ALIAS:
            return self._command_help(name)
        if name in ("selections", "selection", "select"):
            return SELECTION_HELP
        if name in ("lens", "lenses"):
            import scene      # a1032: the words from the parser's own table, so this help cannot lag behind it
            return ("a lens is a note tagged lens; each line is `name : word, word`, indentation is containment (scene <lens>\n"
                    "  prints what it makes). Its words: " + scene.vocabulary() + ".\n"
                    "  fold: the viewer's own toggle; a folded part hides its children and gives up its share, except a child\n"
                    "  marked peek, which stays shown as the folded part's summary (e.g. a resident's Now cards on a folded tile).\n"
                    "  Only a direct child peeks: a peek under a hidden part (a plain child of the folded part, or a fold inside\n"
                    "  it) stays hidden, so a folded part never leaks its insides (test_peek_paint.py).\n"
                    "  A selection (of, the, only when) is filled from fields ($id) and frames, not from a thing's props: name\n"
                    "  the repeat (of ... as r) and write $r.actor; a bare $actor there stays the literal word and matches nothing.")
        if name in knife.PAIR_DOC:
            args, doc = knife.PAIR_DOC[name]
            return f"{name}  (pair verb; level 2)\n  {doc}\n  args: {args}\n  e.g. do {name} a20 a22" + (" to=a22" if name == "match" else "")
        import verbs
        if name in knife.SPECIALIZED and verbs.visible(self, name, self.world.me):
            # a990: a retired built-in's word that a verb made in the world answers (tidy on a room) is that verb
            return "\n\n".join(verbs.describe(self, s) for s in verbs.visible(self, name, self.world.me))
        if name in knife.SPECIALIZED:
            return (f"no verb {name} here; use {self.SPECIALIZED_ALT.get(name, 'a general verb')}. general verbs: "
                    + " ".join(self._help_verbs()) + "\nselections do the specializing (help selections).")
        if name in moo.SYNONYMS and name not in moo.REGISTRY and moo.SYNONYMS[name] in knife.SPECIALIZED:
            # F21: moo would say "read as tidy" and then point at a verb this desk refuses
            to = moo.SYNONYMS[name]
            return f"{name} is not a verb here; elsewhere it means {to}, which this desk does not do.\n" + self.cmd_help(to)
        import verbs
        if name in ("verbs", "verb", "world verbs"):
            return verbs.HELP + ("\n  verbs <id> (the command): what can be done to one thing, with argument forms; "
                                 "examine <id> says the same and more.")
        if name not in self._builtin_verbs():
            made = verbs.visible(self, name, self.world.me)      # a verb someone made that you could use
            if made:
                return "\n\n".join(verbs.describe(self, s) for s in made)
            key = self.NOUN_ALIAS.get(name, name)
            noun = self.NOUN_HELP.get(key) or self.HELP_TOPICS.get(key)
            if noun:
                return noun
            try:
                self._resolve(name)                           # help <thing> is examine <thing>
                return self.cmd_examine(name)
            except Refusal:
                pass
            # F21: moo's list is its whole registry, reply and tidy included; list only what this desk does.
            # a1308 (with Pike's a1299): it names every door: the commands, the built-in verbs (that list unchanged),
            # the verbs made in the world that are at hand where you are, and the topics
            out = [f"no command, verb or topic {name!r} here.",
                   "  commands: " + " ".join(self._commands()) + "   (help <command>)",
                   "  verbs: " + " ".join(self._help_verbs())]
            at_hand = self._world_verbs_at_hand()
            if at_hand:
                out.append("  world verbs at hand here, made in the world: " + " · ".join(at_hand) + "   (help <word>)")
            out.append("  topics: " + " ".join(self._topics()))
            out.append("examine <id> shows which verbs apply to a thing; find <words> searches titles and text.")
            return "\n".join(out)
        return super().cmd_help(name)

    def _topics(self):
        cmds = set(self._commands()) | set(self.COMMAND_ALIAS)
        return sorted((set(self.HELP_TOPICS) | {"lens", "selections"}) - cmds)

    def _world_verbs_at_hand(self):
        """a1299 (Pike): the verbs made in the world whose bare word works where you stand, grouped by where they live:
        what you carry, the room you are in and the rooms around it (nearest first), the house. -> ['release, wish
        (Pike's corner f576)', 'card, say (the house)'], each group sorted."""
        import rooms
        import verbs
        w, me = self.world, str(self.world.me or "").lower()
        groups = []
        mine = sorted({verbs._names(s["title"])[0] for s in verbs.all_verbs(w) if verbs.where(w, s) == ("actor", me)})
        if mine:
            groups.append(", ".join(mine) + " (yours, carried)")
        here = rooms.room_of(w, w.me) if rooms.all_rooms(w) else None
        for r in (verbs.rooms_up(w, here) if here in w.nodes else []):
            names = sorted({verbs._names(s["title"])[0] for s in verbs.all_verbs(w) if verbs.where(w, s) == ("room", r)})
            if names:
                groups.append(", ".join(names) + f" ({w.nodes[r]['title']} {r})")
        house = sorted({verbs._names(s["title"])[0] for s in verbs.all_verbs(w) if verbs.where(w, s)[0] == "house"})
        if house:
            groups.append(", ".join(house) + " (the house)")
        return groups

    SPECIALIZED_ALT = {"reply": "append (examine the chat: it shows what awaits a reply)", "dedupe": "remove also:<id>",
                       "reveal": "raise", "tidy": "tile", "split": "group kind:<k>,in:<surface> then tile the surface as=row",
                       "gather": "move ?<words> into=<surface> one=1", "done": "retitle", "stack": "tile"}

    def _help_verbs(self):
        """The verbs help may name: each answers help <verb> here and is done by this desk."""
        return knife.GENERAL + [p for p in knife.PAIR_DOC if p not in knife.GENERAL]     # link is both

    def _builtin_verbs(self):
        return set(knife.GENERAL) | set(knife.PAIR_DOC) | set(knife.SPECIALIZED) | set(moo.REGISTRY) | self._verb_names()

    def cmd_examine(self, ident):
        rec = self.record_text(ident) if ident else None     # a1308: an event, comment or link id
        if rec:
            return rec
        nid = self._resolve(ident or "desk")
        if persons.is_person(self.world, nid):
            note, self._person_note = getattr(self, "_person_note", ""), ""
            self._mark_seen(nid)
            return persons.card(self.world, nid, note)          # a1568: a person is a thing the house can show
        if nid in self.world.subjects:
            return self.cmd_pivot(nid)
        w = self.world
        self._mark_seen(nid)
        n = w.nodes[nid]
        self._hints_on = True
        try:
            out = [self.line(nid, 1)]
        finally:
            self._hints_on = False
        if n["type"] == "surface" and n["layout"] == "view":
            kids = []
            out.append(f"  a view inside {n['parent']}: it lists whatever matches {n.get('query')}, wherever it is. "
                       f"Things are not in it; change a thing (tag, due, move) and it appears or leaves.")
            out.extend(self.view_lines(nid, 0))
        elif n["type"] == "surface":
            kids = w.children(nid)
            out.append(f"  a {n['layout']} surface" + (f" inside {n['parent']}" if n["parent"] else " (the desk itself)")
                       + (f", holding {len(kids)} thing(s):" if kids else ", empty"))
            # round 11: a surface's content is its children, shown as lines, the way a note shows its lines
            for k in kids:
                kl = "    " + self.line(k["id"], 1)
                if k["type"] == "surface" and w.children(k["id"]):
                    kl += f"  (examine {k['id']} for inside)"
                out.append(kl)
        else:
            s = w.subjects[n["subject"]]
            self._mark_seen(s["id"])
            apps = w.appearances_of(s["id"])
            if self.bullets or self.lean:
                out.append(f"  a {s['kind']} (subject {s['id']}) on {n['parent']}:")
                block = self.bullet_block(nid, indent="    ")
                if block:
                    out.append(block)
            else:
                # as run in round 9: a one-line teaser
                first = s["text"].strip().splitlines()[0][:80] if s["text"].strip() else "(no text)"
                out.append(f"  a {s['kind']} (subject {s['id']}) on {n['parent']}; text begins: {first}")
            if len(apps) > 1:
                out.append("  also appears at " + ", ".join(f"{a} in {w.nodes[a]['parent']}" for a in apps if a != nid))
            if "rule" in (s.get("tags") or []):
                # a1027: a rule note says what rules says of it: its home, who it acts as, how it has gone
                self._rules_sync(say=False)
                r = self._rule_of_note(nid)
                if r is not None:
                    out.append("  a rule (its home is the room holding it; move the note to move it):")
                    out += self._rule_lines(r)
            import verbs
            out += verbs.binding_lines(w, ("s", s["id"]), s["text"])     # a1156: what its stored words are bound to
            if s["kind"] == "chat":
                pend = moo.unanswered(w, s["id"], str(w.me or "alex").lower())
                out.append("  awaiting reply: " + " | ".join(pend) if pend else "  nothing awaiting a reply")
                out.append("  " + moo.CHAT_RULES)
            if not (self.bullets or self.lean):
                open_c = [c for c in s.get("comments", []) if not c["resolved"]]
                if open_c:
                    out.append("  open comments: " + " | ".join(f"{c['id']} {c['by']}: {c['text']}" for c in open_c))
                for l in w.links_of(s["id"]):
                    other = l["to"] if l["from"] == s["id"] else l["from"]
                    ot = w.subjects[other]["title"]
                    apps_o = w.appearances_of(other)
                    out.append(f"  link {l['id']}: " + (f"{l['kind']} → " if l["from"] == s["id"] else f"← {l['kind']} from ")
                               + f"{other} \"{ot}\"" + (f" (at {', '.join(apps_o)})" if apps_o else ""))
        if (n.get("props") or {}).get("wake"):
            import verbs
            out += verbs.binding_lines(w, ("n", nid), str(n["props"]["wake"]), indent="  wake: ")
        out.append("  where: " + self._where_line(nid))
        if self.today:
            d = w.last_day(nid)
            out.append("  when: " + (f"last touched {d} ({w.days_between(d, self.today)}d ago by the clock)" if d else "not touched since the clock was set"))
        import rooms
        import verbs
        made = verbs.on_thing(self, nid)
        if made:
            out.append("  verbs on this thing, made in the world: " + ", ".join(
                f"{verbs._names(s['title'])[0]} ({w.appearances_of(s['id'])[0]})" for s in made) + "   (help <verb>)")
        here = rooms.room_of(w, w.me) if rooms.all_rooms(w) else None
        room_made = [s for s in verbs.at_hand_in(self, here) if s not in made] if here else []
        if room_made:
            # a990: a room is a namespace; what its verbs' bare words do here is shown where you stand
            out.append(f"  at hand in {w.nodes[here]['title']}, made in the world: " + ", ".join(
                f"{verbs._names(s['title'])[0]} ({w.appearances_of(s['id'])[0]})" for s in room_made) + "   (help <verb>)")
        groups, layout = self._shown_verbs(nid)
        pair = "swap beside match link" if layout else "swap beside link"
        if self.lean:
            out.append("  verbs: " + " · ".join(" ".join(names) for names in groups.values()) + (f" · pair: {pair}" if n["parent"] else "")
                       + "   (help <verb> for args; the target may be a selection: help selections)")
            if not layout:
                out.append("  " + rooms.layout_pointer(self))
            return "\n".join(out)
        for origin, names in groups.items():
            out.append(f"  verbs from {origin}: " + "  ".join(
                nm + (f"({(moo.REGISTRY[nm].args if layout or nm != 'move' else rooms.MOVE_ANYWHERE).split('  (')[0].strip()})"
                      if moo.REGISTRY[nm].args else "") for nm in names))
        if n["parent"]:
            out.append("  pair verbs: swap A B  beside A B" + ("  match A to=B" if layout else ""))
        if not layout:
            out.append("  " + rooms.layout_pointer(self))
        out.append("  any verb also takes a selection instead of an id (help selections)")
        return "\n".join(out)

    def _fence_selection(self, ids):
        w = self.world
        stale = []
        for i in ids:
            seen = self.seen.get(i)
            if seen is not None and seen != w.nodes[i]["rev"]:
                sid = w.nodes[i].get("subject")
                last = [e for e in w.events if e["target"] == i or (sid and e["target"] == sid) or i in (e.get("changed") or [])]
                if last and (not persons.mine(self.world, last[-1]) or rule_did_unseen(last[-1], self.world.me)):
                    stale.append(f"{i} (changed by {persons.by(self.world, last[-1])})")
        if stale:
            raise Refusal("stale: " + ", ".join(stale) + "; look at them again before acting")

    def _check_view_query(self, target, query):
        """a1322: prop query= on a view changes what it shows, so the selection is judged as find judges one, before
        anything is stored. On anything else the world's prop refuses it (moo.v_prop), naming what query is."""
        if self._parse_selection(target) is not None:
            raise Refusal("prop query= changes one view's selection at a time; name the view by its id")
        nid = self._resolve(target, allow_subject=False)
        n = self.world.nodes.get(nid) or {}
        if n.get("layout") != "view":
            return
        q = str(query).strip()
        if not q:
            raise Refusal("a view needs query=<selection>, e.g. query=kind:task,due<today")
        if self._parse_selection(q) is None:          # a term that doesn't parse has already refused, as in find
            raise Refusal(f"{q!r} is not a selection, so a view of it would show nothing; ?{q.replace(' ', '+')} "
                          f"matches its words (help selections)")

    def cmd_do_knife(self, verb, positional, kv):
        """a990: an act that makes or changes a verb (its word, where it lives, its lines) is judged once it is done,
        and taken back whole if refused. a1156: a verb's word may not be a built-in's, nor one another verb answers
        where it would live (unless it says overrides=); and every stored line the act saved (a verb's lines, a rule, a
        lens's acts, a wake) is bound where it stands: a word nothing answers there is refused (a rule: saved broken),
        and a verb whose lines changed tells the authors of the lines bound to it."""
        import verbs
        w = self.world
        if verb == "prop" and "query" in kv and positional:
            self._check_view_query(positional[0], kv["query"])
        before, texts, n0 = verbs.state(w), verbs.stored_texts(w), len(w.events)
        out = self._do_knife(verb, positional, kv)
        if len(w.events) == n0:
            return out
        bad = verbs.check_change(self, before)
        notes = []
        if not bad:
            bad, notes = verbs.after_act(self, texts)
        if bad:
            verbs.rollback(self, n0)
            raise Refusal(bad + ". Nothing was changed")
        made = w.nodes.get(w.last_created) or {}
        if verb == "create" and made.get("layout") == "view" and made.get("cols"):
            # a1431: a column that names nothing would print empty at every look; its receipt says so once
            notes += ["  " + x for x in self._column_notes(self.view_matches(made["id"]) or [], made["cols"])]
        return out + "".join("\n" + n for n in notes)

    def _do_knife(self, verb, positional, kv):
        w = self.world
        if not positional:
            raise Refusal("do needs a target after the verb")
        alias = kv.pop("as", None) if verb == "create" or (verb == "group" and kv.get("as") not in ("column", "row", "free")) else None
        if alias:
            out = self._do_knife(verb, positional, kv)
            self.vars = self.vars or {}
            self.vars[alias] = w.last_created
            return out + f"\n  ${alias} = {w.last_created}"
        if verb == "put" and ("above" in kv or "status" in kv) and self._parse_selection(positional[0]) is None:
            tid = self._resolve(positional[0], allow_subject=False)
            tn = w.nodes.get(tid)
            kind = (w.subjects[tn["subject"]]["kind"] if tn.get("subject") else "surface") if tn else "thing"
            if kind != "task":
                raise Refusal(f"put above=/status= orders a task's card in its lane; {tid} is a {kind}. "
                              f"To move it, do put {tid} into=<surface> (put is move for anything but a card)")
        if verb == "put" and kv.get("above"):
            # a1069: the card it goes above is part of what the act means, so it must have been looked at
            kv["above"] = self._resolve(kv["above"], allow_subject=False)
            if self.seen.get(kv["above"]) is None:
                raise Refusal(f"you have not looked at {kv['above']} yet; look or examine it first")
        if verb == "place" and positional[0] not in w.subjects:
            # place is a subject verb; a title or appearance id names the subject behind it
            hit = self._resolve(positional[0])
            if hit in w.nodes and w.nodes[hit]["type"] == "appearance":
                positional = [w.nodes[hit]["subject"]] + positional[1:]
        if verb not in knife.PAIR_DOC and len(positional) > 1:
            # unquoted values with spaces land here as stray words; refusing beats silently keeping the first word
            raise Refusal(f"unexpected words after the target: {' '.join(positional[1:])!r}; quote values with spaces, "
                          f"e.g. line=\"{' '.join(positional[1:])}\"")
        if verb == "resolve" and positional[0].startswith("c") and positional[0][1:].isdigit():
            owner, c = w.find_comment(positional[0])
            if owner is None:
                raise Refusal(f"no comment {positional[0]}; examine or read the thing to see its comments")
            apps = w.appearances_of(owner["id"])
            host = next((a for a in apps if a in self.seen), apps[0] if apps else owner["id"])
            return super().cmd_do("resolve", host, {"id": positional[0], **{k: v for k, v in kv.items() if k != "id"}})
        if verb in knife.PAIR_DOC:
            second = positional[1] if len(positional) > 1 else kv.get("to") or kv.get("with") or ""
            if not second:
                raise Refusal(f"{verb} needs two ids: do {verb} A B (or A to=B)")
            a, b = self._resolve(positional[0], allow_subject=False), self._resolve(second, allow_subject=False)
            for x in (a, b):
                if self.seen.get(x) is None:
                    raise Refusal(f"you have not looked at {x} yet; look or examine it first")
            r = knife.pair_verb(w, verb, a, b, kv)
            self._after_mutation()
            self._mark_seen(a)
            self._mark_seen(b)
            evs = r.get("events") or []
            return (f"ok {verb} {a} {b}  [{evs[0]}" + (f"..{evs[-1]}" if len(evs) > 1 else "") + "]\n  now: "
                    + self.line(a, 1) + self.position_note(a) + "\n  now: " + self.line(b, 1) + self.position_note(b))
        if (verb if verb in moo.REGISTRY else moo.SYNONYMS.get(verb, verb)) in knife.SPECIALIZED:
            alt = self.SPECIALIZED_ALT.get(verb, "a general verb")
            raise Refusal(f"no {verb} here; use {alt}. help selections lists the selection forms")
        sel = self._parse_selection(positional[0])
        if sel is None:
            return super().cmd_do(verb, positional[0], kv)
        ids, desc = sel
        if verb not in self._verb_names():
            raise Refusal(f"{verb} is not a verb here; general verbs: " + " ".join(knife.GENERAL) + " (help selections)")
        verb = moo.SYNONYMS.get(verb, verb)
        if verb in knife.SPECIALIZED:
            raise Refusal(f"no {verb} here; compose it: help selections")
        if not ids:
            raise Refusal(f"nothing matches {desc}")
        self._fence_selection(ids)
        kv = {k: (self._resolve(v, allow_subject=False) if k in ("into", "before", "after", "in") else v) for k, v in kv.items()}
        dest = kv.get("into") or kv.get("in")
        skipped = ""
        if dest and dest in ids:
            ids = [i for i in ids if i != dest]
            skipped = f"\n  ({dest} matched too; skipped, it is the destination)"
            if not ids:
                raise Refusal(f"only {dest} matches {desc}, and it is the destination")
        if verb == "group":
            r = knife.group_around(w, ids, kv)
        else:
            steps = []
            kept = set()
            for i in ids:
                if verb == "move" and kv.get("one"):
                    sid = w.nodes[i].get("subject")
                    if sid in kept:
                        steps.append(("remove", i, {}))
                        continue
                    kept.add(sid)
                steps.append((verb, i, {k: v for k, v in kv.items() if k != "one"}))
            r = moo._compose(w, steps)
        for e in r.get("events", []):
            ev = next((x for x in w.events if x["id"] == e), None)
            if ev is not None:
                ev["via"] = f"{verb} {desc}"
        self._after_mutation()
        evs = r.get("events") or []
        out = f"ok {verb} {len(ids)} thing(s) matching {desc}: {' '.join(ids)}" + skipped
        if evs:
            out += f"  [{evs[0]}" + (f"..{evs[-1]}, {len(evs)} steps" if len(evs) > 1 else "") + "]"
        if r.get("created"):
            gid = r["created"]
            out += f" → created {gid}\n  " + self.line(gid, 1) + "\n    where: " + self._where_line(gid)
            out += "\n" + "\n".join("    " + self.line(k["id"], 1) for k in w.children(gid))
            if r.get("note"):
                out += "\n  " + r["note"]
        else:
            for i in ids:
                if i in w.nodes:
                    out += "\n  now: " + self.line(i, 1) + self.position_note(i)
                else:
                    out += f"\n  {i} removed"
        for c in r.get("changed", []):
            if c in w.nodes:
                self._mark_seen(c)
        return out
