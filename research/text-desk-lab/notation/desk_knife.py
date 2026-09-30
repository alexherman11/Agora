"""The knife desk (round 7): the MOO desk with general verbs only, selections as targets, and pair verbs."""

import re
import shlex

import harness   # registers launch; provides sync
import knife
import moo
from desk import rule_did_unseen, unescape_value
from desk_moo import DeskMoo, HELP_MOO
from world import Refusal

HELP_KNIFE = HELP_MOO.replace(
    "  do verb id k=v ...     change something. e.g. do move a04 into=f02   do tidy f04   do gather f02 words=harbor by=due",
    "  do verb target k=v ... change something. target is an id or a selection (help selections)\n"
    "                         e.g. do move a04 into=f02   do move kind:image,in:f04 into=f28   do remove also:a18\n"
    "  do swap A B | do beside A B | do match A to=B    pair verbs\n"
    "  do group <selection> as=column title=X          a new surface around the selection",
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
  -tag:fixed         leaves out what the term would select (any term may be negated)
  a20,a22            an explicit list
combine terms with commas (AND): kind:image,in:f04. The receipt lists everything the verb touched.
find <selection> lists what it matches, grouped by surface: find kind:image   find tag:harbor,in:f04   find hidden
e.g. do move ?harbor into=f02 one=1     do raise hidden,in:f04     do group kind:image,in:f04 as=column title=Pictures"""


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
  $new                   the surface created earlier in this session; $item the last created thing
  more: help rules · help scripts · help views · help clock · help handles · help why · help export · help trials
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
        return out or None

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
            out.append(f"{indent}* {c['id']} {c['by']} ({'resolved' if c['resolved'] else 'open'}): {ct}")
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

    # ---- rules: the first automation layer (round 11c) ----------------------------------------------
    # rule when <selection> do <verb> [k=v ...]   fires the verb once on each thing that enters the selection
    rules = None
    _rule_notes = None
    _in_rules = False

    _rule_seq = 0

    def _next_rule_id(self):
        # ids never reuse a dropped rule's number; history and receipts keep naming the old one
        self._rule_seq = max(self._rule_seq, max((int(r["id"][1:]) for r in self.rules or []), default=0)) + 1
        return f"r{self._rule_seq}"

    def cmd_rules(self):
        if not self.rules:
            return "no rules. rule when <selection> do <verb> [k=v ...]   e.g. rule when kind:task,due<2026-09-19 do move into=Today"
        return "\n".join(f"{r['id']} {'' if r.get('on') else 'when '}{r['sel']} do {self._action_text(r)}"
                         + f"   (fired {r['fired']}x)" for r in self.rules)

    def cmd_rule(self, arg):
        try:
            argv = shlex.split(arg)
        except ValueError as e:
            raise Refusal(f"could not parse: {e}")
        if len(argv) >= 2 and argv[0] == "drop":
            rid = argv[1]
            before = len(self.rules or [])
            self.rules = [r for r in (self.rules or []) if r["id"] != rid]
            if len(self.rules) == before:
                raise Refusal(f"no rule {rid}; rules lists them")
            return f"ok dropped {rid}"
        if len(argv) >= 4 and argv[0] == "on":
            # rule on <verb> [by=<actor>] do <verb> [k=v ...]: fires on each such event, on the event's thing
            i = argv.index("do") if "do" in argv else -1
            if i < 2:
                raise Refusal("rule on <verb> [by=<actor>] do <verb> [k=v ...]")
            on_verb, by = argv[1].lower(), None
            for a in argv[2:i]:
                if a.startswith("by="):
                    by = a[3:]
                else:
                    raise Refusal(f"rule on: only by=<actor> may follow the event verb, not {a!r}")
            act = self._parse_action(argv[i + 1:])
            act["kv"].pop("now", None)
            self.rules = self.rules or []
            rid = self._next_rule_id()
            # author: who made it (a656); the rule fires as its author (a687, decided in a683)
            self.rules.append({"id": rid, "on": on_verb, "by": by, "author": self.world.me, **act, "done": set(), "fired": 0,
                               "cursor": len(self.world.events), "sel": f"on {on_verb}" + (f" by={by}" if by else "")})
            return f"ok {rid}: on {on_verb}" + (f" by={by}" if by else "") + f" do {self._action_text(act)}"
        if len(argv) < 4 or argv[0] != "when" or argv[2] != "do":
            raise Refusal("rule when <selection> do <verb> [k=v ...]   |   rule on <verb> [by=<actor>] do <verb> [k=v ...]   |   rule drop rN")
        sel_text = argv[1]
        if self._parse_selection(sel_text) is None:
            raise Refusal(f"{sel_text!r} is not a selection (help selections)")
        act = self._parse_action(argv[3:])
        now = act["kv"].pop("now", None)
        self.rules = self.rules or []
        rid = self._next_rule_id()
        rule = {"id": rid, "sel": sel_text, "author": self.world.me, **act, "done": set(), "fired": 0}
        self.rules.append(rule)
        out = f"ok {rid}: when {sel_text} do {self._action_text(act)}"
        # things already in the selection count as already handled: a rule is about what enters, not what is,
        # unless now=1 says to fire on the current matches too
        ids, desc = self._parse_selection(sel_text)
        if now:
            out += f"\n  {len(ids)} thing(s) match {desc} now; firing on them"
            self._run_rules()
        else:
            rule["done"].update(ids)
            out += (f"\n  {len(ids)} thing(s) already match {desc}; the rule fires on things that enter it from now on"
                    + (f" (to fire on these {len(ids)} too, define it with now=1)" if ids else "")
                    + f". rules lists it; rule drop {rid} removes it")
        return out

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
        if not ids:
            return f"table {desc}: nothing matches"
        return "\n".join([f"table {desc}: {len(ids)} row(s)"] + self._table_lines(ids, kv.get("cols"), kv.get("by"), kv.get("desc")))

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
        def cell(i, c):
            n, s = w.nodes[i], subj(i)
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
        shown = [{"title": "title", "tags": "tags", "due": "due", "in": "place"}.get(c, None if c in ("id", "kind", "words", "age") else f"prop:{c}") for c in cols]
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
        out.append("  columns: id title kind tags due in age words, and any prop; cols= picks, by= sorts (desc=1)")
        return out

    def _parse_action(self, argv):
        """The part of a rule after do: <verb> [target] [k=v ...], or run <script> [args ...]. $item stands for the
        thing the rule fired on, in a script's args or in a k=v value."""
        verb = argv[0].lower() if argv else ""
        if verb == "run":
            if len(argv) < 2:
                raise Refusal("rule ... do run <script> [args]   ($item stands for the thing the rule fired on)")
            if argv[1] not in (self.scripts or {}):
                raise Refusal(f"no script {argv[1]}; define it first (scripts lists them)")
            args = [a for a in argv[2:] if a != "now=1"]
            return {"verb": "run", "script": argv[1], "args": args, "kv": ({"now": "1"} if len(args) < len(argv) - 2 else {}), "target": None}
        if verb not in self._verb_names() or verb in knife.SPECIALIZED:
            raise Refusal(f"{verb} is not a verb here; general verbs: " + " ".join(knife.GENERAL) + "; or run <script>")
        rest = list(argv[1:])
        target = None
        if rest and "=" not in rest[0]:
            target = rest.pop(0)   # an explicit target instead of the thing that entered: rule when in:Today do sort Today by=due
        kv = {}
        for a in rest:
            if "=" not in a:
                raise Refusal(f"rule arguments are k=v; got {a!r}")
            k, _, v = a.partition("=")
            kv[k] = v
        return {"verb": verb, "target": target, "kv": kv}

    @staticmethod
    def _q(a):
        return '"' + a.replace("\\", "\\\\").replace('"', '\\"') + '"' if (" " in a or not a) else a

    def _action_text(self, r):
        if r["verb"] == "run":
            return "run " + " ".join([r["script"]] + [self._q(a) for a in r.get("args", [])])
        return f"{r['verb']} {r.get('target') or ''} {self._fmt_args(r['kv'])}".replace("  ", " ").rstrip()

    def _fire(self, r, i):
        """Run rule r's action on thing i; returns one receipt line."""
        if r["verb"] == "run":
            args = [a.replace("$item.title", self._title_of(i)).replace("$item", i) for a in r.get("args", [])]
            line = "run " + " ".join([r["script"]] + [self._q(a) for a in args])
            saved, self._rule_notes = self._rule_notes, None   # the nested command must not swallow the notes so far
            try:
                res = self.dispatch("desk", {"line": line})
            finally:
                self._rule_notes = saved
            if "error" in res:
                raise Refusal(res["error"])
            lines = res["text"].splitlines()
            start = next((k + 1 for k, l in enumerate(lines) if l.startswith("run ")), 0)   # after the script's echo line
            body = [l.strip() for l in lines[start:] if l.strip() and not l.strip().startswith("[")]
            err = next((l for l in body if l.startswith("ERR ")), None)
            if err:
                raise Refusal(err[4:])
            return line + " → " + (body[0] if body else "ok")
        tgt = r.get("target") or i
        if tgt == "$item":
            tgt = i
        elif r.get("target"):
            self._mark_seen(self._resolve(tgt))
        kv = {k: v.replace("$item.title", self._title_of(i)).replace("$item", i) for k, v in r["kv"].items()}
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
            who = e["by"]
            via = e.get("via")
            how = f" by rule {via.split()[1]}" if via and via.startswith("rule ") else (f" via {via}" if via else "")
            if e.get("tripped_by") and e["tripped_by"] != who:
                how += f", tripped by {e['tripped_by']}"
            cause = f" (because of {e['cause']})" if e.get("cause") else ""
            done = " (undone)" if e.get("undone") else ""
            args = {k: (v if len(str(v)) <= 120 else str(v)[:117] + "…") for k, v in (e.get("args") or {}).items()}   # a fold, declared
            out.append(f"  {e['id']} {e['verb']} {self._fmt_args(args)}".rstrip() + f" · {who}{how}{cause}{done}")
        # what would happen next: rules whose selection this thing matches but has not been handled by
        pending = []
        for r in self.rules or []:
            if r.get("on"):
                continue
            try:
                ids, _ = self._parse_selection(r["sel"])
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
            return '"' + str(s).replace("\\", "\\\\\\\\").replace('"', '\\"').replace("\n", "\\n").replace("$today", "\\$today") + '"'

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
        for name, body in (self.scripts or {}).items():   # scripts first: a rule may run one
            out.append(f"script {name} = {body}")
        for r in self.rules or []:
            out.append(f"rule {'' if r.get('on') else 'when '}{r['sel']} do {self._action_text(r)}")
        if skipped:
            out.append("# not carried (only you can write as you): " + "; ".join(skipped))
        return "\n".join(out)

    # ---- scripts: named command sequences with $1.. placeholders (round 11c) --------------------------
    scripts = None

    def cmd_scripts(self):
        if not self.scripts:
            return "no scripts. script <name> = <commands separated by ;>   ($1 $2 .. stand for run's arguments)   e.g. script tidy = do sort $1 by=due; look $1"
        return "\n".join(f"{k} = {v}" for k, v in self.scripts.items())

    def cmd_script(self, arg):
        if arg.startswith("drop "):
            name = arg[5:].strip()
            if name not in (self.scripts or {}):
                raise Refusal(f"no script {name}; scripts lists them")
            users = [r["id"] for r in (self.rules or []) if r["verb"] == "run" and r.get("script") == name]
            if users:
                raise Refusal(f"{', '.join(users)} run {name}; drop those rules first (rule drop rN)")
            del self.scripts[name]
            return f"ok dropped script {name}"
        name, eq, body = arg.partition("=")
        name, body = name.strip(), body.strip()
        if not eq or not name or not body:
            raise Refusal("script <name> = <commands separated by ;>")
        if " " in name:
            raise Refusal("a script name is one word")
        self.scripts = self.scripts or {}
        self.scripts[name] = body
        out = f"ok script {name} = {body}\n  run {name} [args]   ({body.count('$')} placeholder(s))"
        if ";" in body:
            out += f"\n  ({body.count(';') + 1} commands in the script: a definition keeps every ; as its own, so define a script alone on its line)"
        return out

    def cmd_run(self, arg):
        try:
            argv = shlex.split(arg)
        except ValueError as e:
            raise Refusal(f"could not parse: {e}")
        if not argv:
            raise Refusal("run <script> [args]; scripts lists them")
        name, args = argv[0], argv[1:]
        body = (self.scripts or {}).get(name)
        if body is None:
            raise Refusal(f"no script {name}; scripts lists them")
        missing = sorted({m for m in re.findall(r"\$(\d+)", body) if int(m) > len(args)})
        if missing:
            raise Refusal(f"run {name} needs {max(int(m) for m in missing)} argument(s); got {len(args)}")
        def fill(m):
            val = args[int(m.group(1)) - 1]
            if m.group(2):   # $1.title: the thing's title, for prose (Terra asked for this form before it existed)
                val = self._title_of(val)
            inside = body[:m.start()].count('"') % 2 == 1   # already inside a double-quoted value: paste raw
            if inside:
                return val.replace("\\", "\\\\").replace('"', '\\"')
            return '"' + val.replace("\\", "\\\\").replace('"', '\\"') + '"' if (" " in val or not val) else val
        line = re.sub(r"\$(\d+)(\.title)?", fill, body)
        r = self.dispatch("desk", {"line": line})
        body_text = r["text"] if "text" in r else "ERR " + r["error"]
        return f"run {name}: {line}\n" + body_text

    def _run_rules(self, cause=None):
        if not self.rules or self._in_rules:
            return
        self._in_rules = True
        try:
            for _ in range(3):   # a rule's action may make another rule fire; bounded
                fired = False
                for r in self.rules:
                    if r.get("on"):
                        # event rule: each new matching event names the thing to act on
                        evs = self.world.events[r["cursor"]:]
                        r["cursor"] = len(self.world.events)
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
                        ids, desc = targets, r["sel"]
                        r["done"] = set()   # an event rule fires every time
                    else:
                        try:
                            ids, desc = self._parse_selection(r["sel"])
                        except Refusal as e:
                            self._note(f"~ {r['id']} could not select ({e})")
                            continue
                    for i in ids:
                        if i in r["done"] or i not in self.world.nodes:
                            continue
                        r["done"].add(i)
                        if r["verb"] == "move" and r["kv"].get("into"):
                            try:
                                if self._resolve(r["kv"]["into"], allow_subject=False) == self.world.nodes[i]["parent"]:
                                    continue   # already where the rule would put it: not a firing
                            except Refusal:
                                pass
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
                            r["fired"] += 1
                            fired = True
                            self._note(f"~ {r['id']} fired on {i}" + (f" as {author}" if author and author != tripper else "")
                                       + ": " + receipt)
                        except Refusal as e:
                            self._note(f"~ {r['id']} could not {r['verb']} {i}: {e}")
                        finally:
                            self.world.acting_rule = None
                            self.world.me, self._firing_observer = tripper, None
                        for ev in self.world.events[n0:]:
                            ev["via"] = f"rule {r['id']}"
                            if author:
                                ev["tripped_by"] = tripper
                            if cause:
                                ev["cause"] = cause
                        # the rule is our own automation: what it changed counts as seen, like our own writes
                        for k, v in list(self.world.nodes.items()) + list(self.world.subjects.items()):
                            if revs0.get(k) != v["rev"]:
                                self._mark_seen(k)
                if not fired:
                    break
        finally:
            self._in_rules = False

    def _note(self, text):
        self._rule_notes = (self._rule_notes or []) + [text]

    def snapshot(self):
        snap = self.world.snapshot()
        snap["rules"] = [{"id": r["id"], "text": ("" if r.get("on") else "when ") + r["sel"] + " do " + self._action_text(r),
                          "on": r.get("on"), "by": r.get("by"), "author": r.get("author"), "when": None if r.get("on") else r["sel"],
                          "verb": r["verb"], "script": r.get("script"), "fired": r.get("fired", 0)} for r in (self.rules or [])]
        snap["scripts"] = dict(self.scripts or {})
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

    def _one(self, args, name="desk"):
        tick = self._tick()
        if tick:
            self._rule_notes = [tick] + (self._rule_notes or [])
        n0 = len(self.world.events)
        r = super()._one(args, name)
        if len(self.world.events) > n0:
            # after the receipt is composed, so the receipt describes the command, then the rules; the command's
            # last event is the cause of whatever the rules do, so one undo takes both back
            self._run_rules(cause=self.world.events[-1]["id"])
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
            for key in ("in:", "also:", "links:", "parts:", "part-of:"):
                if t.startswith(key) and t[len(key):] not in self.world.nodes and t[len(key):] not in self.world.subjects:
                    t = key + self._resolve(t[len(key):].strip('"'))
            out.append(t)
        return ",".join(out)

    def _parse_selection(self, token):
        return knife.parse_selection(self.world, self._selection_terms(token.strip()))

    def cmd_find(self, words):
        # round 11b: find also takes a selection, which is the scalable listing view (examine is one thing in depth)
        sel = self._parse_selection(words) if words.strip() else None
        if sel is not None:
            ids, desc = sel
            if not ids:
                return f"find {desc}: nothing matches"
            w = self.world
            by_parent = {}
            for i in ids:
                by_parent.setdefault(w.nodes[i]["parent"], []).append(i)
            out = [f"find {desc}: {len(ids)} thing(s)"]
            cap = 8
            for p, kids in by_parent.items():
                out.append(f"  in {p} \"{w.title(w.nodes[p])}\":")
                out.extend("    " + self.line(i, 1) for i in kids[:cap])
                if len(kids) > cap:
                    more = f"look {p} shows all of it" if "in:" in words else f"find {words.strip()},in:{p} lists them"
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
        if "$today" in line and not line.lower().startswith("script "):
            # substituted when a command runs, not when a script is defined
            if not self.today and re.search(r"(?<!\\)\$today", line):
                raise Refusal("$today is unset; clock YYYY-MM-DD sets it")
            line = re.sub(r"(?<!\\)\$today", self.today or "", line)   # \$today stays literal (export writes it so)
        words = line.split(None, 1)
        cmd = words[0].lower()
        arg = words[1].strip() if len(words) > 1 else ""
        if cmd == "go":
            import rooms
            return rooms.cmd_go(self, arg)
        if cmd == "look" and not arg:
            import rooms           # a678: a bare look narrates the room you are in; look <id> keeps the tree
            if rooms.narrates(self):
                return rooms.narrate(self, rooms.room_of(self.world, self.world.me))
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
                raise Refusal("scene <lens name>. A lens is a note tagged lens; help scene")
            try:
                sc, text = scene.scene_for(self, arg.strip())
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
            walk(sc)
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
            # Juniper: `do prop prop:day=2026-10-10 tripday=1` lost its target, because the selection carries an =. A word that
            # begins with a selection term is the target, = or not.
            SEL = re.compile(r"^-?(kind|tag|in|also|prop|title|comments|links|parts|part-of):|^-?(due|age)[<>]|^[?]")
            is_target = lambda a: "=" not in a or a.startswith("?") or bool(SEL.match(a))
            positional = [unescape_value(a) for a in argv[1:] if is_target(a)]   # titles carry escapes too
            kv = {}
            for a in argv[1:]:
                if "=" in a and not is_target(a):
                    k, _, v = a.partition("=")
                    kv[k] = unescape_value(v)
            if verb not in self._builtin_verbs():     # tier 1: `do sweep porch` may name a verb made in the world
                import verbs
                hit = verbs.try_line(self, arg, self.world.me)
                if hit is not None:
                    return hit
            return self.cmd_do_knife(verb, positional, kv)
        return super().repl(line)

    HELP_TOPICS = {
        "rooms": """rooms: you are always in one room. A room is a surface with prop role=room (a corner, role=resident, is its
  resident's room). Its props: describe=<id> its description, talk=<id> the chat where talk here lands,
  shows=<selection> what is at hand (default: what is inside it), home=<in:|tag: selection> where things made here land.
  go <room>        walk there, from anywhere, by id or a word of its title (go lounge); prints the room
  go <room> :1     walk without looking            go alone: where you are, and who is in each room
  look             with no id: the room you are in: its description, who is here, what is at hand (one id each),
                   the last lines said here. Only what it prints whole counts as seen: look <id> or read before changing
                   a thing listed at hand. look <id> is the tree, as always.
  Where you are is kept in the world (history lists each go) but undo leaves it: go back instead. Someone who never
  went anywhere is in their own corner, or in Home. Resting sends a resident home to their corner.""",
        "commissions": """commissions: a worker changes what the world can't (the desk's code, the house, the painter) for you.
  Write a task with prop commission=asked; its text says what you want, why, and how you'll know it's done:
    do create <place> kind=task title="..." commission=asked text="What: ... Why: ... Done when: ..."
  The house gives it to a disposable worker with real tools, in its own copy of the code. The worker talks to you in
  comments on the task (to widen its scope, to put a decision to you, or when it's stuck); answer with
    do comment <task> line="..."
  When it's done, the house lands it between turns: checks the host is still whole, and reverts it if not. The task
  shows where it is: commission=asked|working|waiting|ready|landing|landed|reverted|failed. Set commission=cancelled
  to stop it. Most things don't need a worker: views, styles, notes and verbs (help verbs) change in the world itself.""",
        "rules": """rules: the desk acts on its own when things change.
  rule when <selection> do <verb> [target] [k=v ...]   fires once on each thing that enters the selection
                                                        (now=1: also on the things that match right now)
  rule on <verb> [by=<actor>] do <verb> [target] [k=v]  fires on each such event, on the thing it happened to
  target is the thing itself unless you name one: rule when in:Today do sort Today by=due
  the action may run a script: rule on prop by=harness do run announce $item   ($item = the thing it fired on,
                                                                               $item.title its title)
  rules              list them, with how often each fired      rule drop rN   remove one
  A rule's actions print as ~ lines after your command's receipt; undo of your command undoes them too.
  why <id> shows how a thing got where it is and which rule would act on it next.
  e.g. rule when tag:fixed do move into=Done      rule on append by=priya do tag add=needs-reply""",
        "scripts": """scripts: named command sequences.
  script <name> = <commands separated by ;>     $1 $2 .. stand for run's arguments; $today for the clock's date
                                                 $1.title is the title of the thing $1 names (for prose)
  run <name> [args]                              scripts may call scripts; a rule may run one (help rules)
  scripts                                        list them
  e.g. script morning = clock $1; look Overdue; look Today; find age<1""",
        "views": """views: a surface whose contents are a selection, evaluated at every look. Nothing is in it; it lists
  whatever matches, wherever that is, with (in fXX) after each line. Change a thing and it appears or leaves.
  do create <surface> kind=view title=<str> query=<selection>      e.g. query=kind:task,due<today
  with cols=a,b [by=col] [desc=1] the view is a table at every look (help table)""",
        "scene": """scene <lens>: print the scene a lens makes of the world right now. The painter in the browser draws the very
  same tree, so this is what the other person sees: each part, its words, its role, its place, and the desk
  command each gesture would send. A lens is a note tagged lens; its text is the description (grammar: the
  docstring of scene.py). Edit a lens with rewrite like any note; the picture follows.""",
        "worktree": """worktree: work apart from a shared desk, then come back as commands.
  worktree fork <name>    copy this world into <session>@<name>; enter it as its own session
  worktree                list them (inside one: where it came from and how much is journalled)
  worktree diff <name>    the commands made there, and what this desk did since (! = both touched it)
  worktree merge <name>   replay those commands here, signed by who made them, all or nothing. A command whose
                          target someone else changed since the fork is refused, and then nothing is applied.""",
        "clock": """clock: clock follow keeps today on the wall date: days pass on their own, the rules run when a new day is
  noticed, and the first command after an absence says how long you were away. clock alone shows the date and hour.
  clock YYYY-MM-DD (or clock now) sets today by hand, re-evaluates the rules, and stops following.
  today in due< / due> terms is the clock's date; $today in any command; age<N / age>N select by days since a
  thing was last touched (undo is not touching). examine prints when: with the last touch.""",
        "handles": """handles: names for ids. do create ... as=draft, or set draft = <id or title>; then $draft names it.
  vars lists them. $new is the last surface created, $item the last thing.""",
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
  e.g. table kind:trial cols=task,model,score,calls by=calls desc=1      table in:Today cols=due,age""",
        "find": """find <words> searches titles and text; find <selection> lists what matches, grouped by surface (8 per surface,
  then a pointer). Both end with the selection form to act on: do move <selection> into=<surface>. help selections.""",
        "read": """read <id> shows a text's sections with word counts; read <id> #<n> or #<name> one section (names may have
  spaces); read <id> :3 all of it; tail=<n> the last n lines of what was asked for.""",
        "sync": "sync: brings finished trials in as the actor harness (props, a comment with the reply, a transcript doc). help trials.",
        "compare": "compare <A> <B>: two things side by side, line by line, with what differs marked.",
    }

    def cmd_help(self, name):
        name = name.lower()
        if name in self.HELP_TOPICS:
            return self.HELP_TOPICS[name]
        if name in ("selections", "selection", "select"):
            return SELECTION_HELP
        if name in knife.PAIR_DOC:
            args, doc = knife.PAIR_DOC[name]
            return f"{name}  (pair verb; level 2)\n  {doc}\n  args: {args}\n  e.g. do {name} a20 a22" + (" to=a22" if name == "match" else "")
        if name in knife.SPECIALIZED:
            return (f"no verb {name} here; use {self.SPECIALIZED_ALT.get(name, 'a general verb')}. general verbs: "
                    + " ".join(self._help_verbs()) + "\nselections do the specializing (help selections).")
        if name in moo.SYNONYMS and name not in moo.REGISTRY and moo.SYNONYMS[name] in knife.SPECIALIZED:
            # F21: moo would say "read as tidy" and then point at a verb this desk refuses
            to = moo.SYNONYMS[name]
            return f"{name} is not a verb here; elsewhere it means {to}, which this desk does not do.\n" + self.cmd_help(to)
        import verbs
        if name in ("verbs", "verb", "world verbs"):
            return verbs.HELP
        if name not in self._builtin_verbs():
            made = verbs.visible(self, name, self.world.me)      # a verb someone made that you could use
            if made:
                return "\n\n".join(verbs.describe(self, s) for s in made)
            try:
                self._resolve(name)                           # help <thing> is examine <thing>
                return self.cmd_examine(name)
            except Refusal:
                pass
            # F21: moo's list is its whole registry, reply and tidy included; list only what this desk does
            return f"no verb {name} here. verbs: " + " ".join(self._help_verbs()) + "\nexamine <id> shows which apply to a thing."
        return super().cmd_help(name)

    SPECIALIZED_ALT = {"reply": "append (examine the chat: it shows what awaits a reply)", "dedupe": "remove also:<id>",
                       "reveal": "raise", "tidy": "tile", "split": "group kind:<k>,in:<surface> then tile the surface as=row",
                       "gather": "move ?<words> into=<surface> one=1", "done": "retitle", "stack": "tile"}

    def _help_verbs(self):
        """The verbs help may name: each answers help <verb> here and is done by this desk."""
        return knife.GENERAL + [p for p in knife.PAIR_DOC if p not in knife.GENERAL]     # link is both

    def _builtin_verbs(self):
        return set(knife.GENERAL) | set(knife.PAIR_DOC) | set(knife.SPECIALIZED) | set(moo.REGISTRY) | self._verb_names()

    def cmd_examine(self, ident):
        nid = self._resolve(ident or "desk")
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
        out.append("  where: " + self._where_line(nid))
        if self.today:
            d = w.last_day(nid)
            out.append("  when: " + (f"last touched {d} ({w.days_between(d, self.today)}d ago by the clock)" if d else "not touched since the clock was set"))
        import verbs
        made = verbs.on_thing(self, nid)
        if made:
            out.append("  verbs on this thing, made in the world: " + ", ".join(
                f"{verbs._names(s['title'])[0]} ({w.appearances_of(s['id'])[0]})" for s in made) + "   (help <verb>)")
        if self.lean:
            groups = [" ".join(names) for names in knife.general_verbs_by_origin(w, nid).values()]
            out.append("  verbs: " + " · ".join(groups) + (" · pair: swap beside match link" if n["parent"] else "")
                       + "   (help <verb> for args; the target may be a selection: help selections)")
            return "\n".join(out)
        for origin, names in knife.general_verbs_by_origin(w, nid).items():
            out.append(f"  verbs from {origin}: " + "  ".join(
                nm + (f"({moo.REGISTRY[nm].args.split('  (')[0].strip()})" if moo.REGISTRY[nm].args else "") for nm in names))
        if n["parent"]:
            out.append("  pair verbs: swap A B  beside A B  match A to=B")
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
                if last and (last[-1]["by"] != self.world.me or rule_did_unseen(last[-1], self.world.me)):
                    stale.append(f"{i} (changed by {last[-1]['by']})")
        if stale:
            raise Refusal("stale: " + ", ".join(stale) + "; look at them again before acting")

    def cmd_do_knife(self, verb, positional, kv):
        w = self.world
        if not positional:
            raise Refusal("do needs a target after the verb")
        alias = kv.pop("as", None) if verb == "create" or (verb == "group" and kv.get("as") not in ("column", "row", "free")) else None
        if alias:
            out = self.cmd_do_knife(verb, positional, kv)
            self.vars = self.vars or {}
            self.vars[alias] = w.last_created
            return out + f"\n  ${alias} = {w.last_created}"
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
