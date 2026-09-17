"""The knife desk (round 7): the MOO desk with general verbs only, selections as targets, and pair verbs."""

import re
import shlex

import knife
import moo
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
  $new                   the surface created earlier in this session; $item the last created thing"""


class DeskKnife(DeskMoo):
    def __init__(self, world, variant="knife"):
        super().__init__(world, "acme")
        self.variant = variant

    lean = False        # round 11: no geometry inside tiled parents, no try: tags on outline lines (examine has them)
    _hints_on = False

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
            out.append(f"{indent}* {c['id']} {c['by']} ({'resolved' if c['resolved'] else 'open'}): {c['text'][:90]}")
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
        return "\n".join(f"{r['id']} {'' if r.get('on') else 'when '}{r['sel']} do {r['verb']} {self._fmt_args(r['kv'])}".rstrip()
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
            verb = argv[i + 1].lower() if len(argv) > i + 1 else ""
            if verb not in self._verb_names() or verb in knife.SPECIALIZED:
                raise Refusal(f"{verb} is not a verb here; general verbs: " + " ".join(knife.GENERAL))
            kv = {}
            for a in argv[i + 2:]:
                if "=" not in a:
                    raise Refusal(f"rule arguments are k=v; got {a!r}")
                k, _, v = a.partition("=")
                kv[k] = v
            self.rules = self.rules or []
            rid = self._next_rule_id()
            self.rules.append({"id": rid, "on": on_verb, "by": by, "verb": verb, "kv": kv, "done": set(), "fired": 0,
                               "cursor": len(self.world.events), "sel": f"on {on_verb}" + (f" by={by}" if by else "")})
            return f"ok {rid}: on {on_verb}" + (f" by={by}" if by else "") + f" do {verb} {self._fmt_args(kv)}".rstrip()
        if len(argv) < 4 or argv[0] != "when" or argv[2] != "do":
            raise Refusal("rule when <selection> do <verb> [k=v ...]   |   rule on <verb> [by=<actor>] do <verb> [k=v ...]   |   rule drop rN")
        sel_text, verb = argv[1], argv[3].lower()
        if self._parse_selection(sel_text) is None:
            raise Refusal(f"{sel_text!r} is not a selection (help selections)")
        if verb not in self._verb_names() or verb in knife.SPECIALIZED:
            raise Refusal(f"{verb} is not a verb here; general verbs: " + " ".join(knife.GENERAL))
        kv = {}
        for a in argv[4:]:
            if "=" not in a:
                raise Refusal(f"rule arguments are k=v; got {a!r}")
            k, _, v = a.partition("=")
            kv[k] = v
        self.rules = self.rules or []
        rid = f"r{len(self.rules) + 1}"
        rule = {"id": rid, "sel": sel_text, "verb": verb, "kv": kv, "done": set(), "fired": 0}
        self.rules.append(rule)
        out = f"ok {rid}: when {sel_text} do {verb} {self._fmt_args(kv)}".rstrip()
        # things already in the selection count as already handled: a rule is about what enters, not what is,
        # unless now=1 says to fire on the current matches too
        ids, desc = self._parse_selection(sel_text)
        if kv.pop("now", None):
            out += f"\n  {len(ids)} thing(s) match {desc} now; firing on them"
            self._run_rules()
        else:
            rule["done"].update(ids)
            out += (f"\n  {len(ids)} thing(s) already match {desc}; the rule fires on things that enter it from now on"
                    + (f" (to fire on these {len(ids)} too, define it with now=1)" if ids else "")
                    + f". rules lists it; rule drop {rid} removes it")
        return out

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
            cause = f" (because of {e['cause']})" if e.get("cause") else ""
            done = " (undone)" if e.get("undone") else ""
            out.append(f"  {e['id']} {e['verb']} {self._fmt_args(e.get('args') or {})}".rstrip() + f" · {who}{how}{cause}{done}")
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
                pending.append(f"{r['id']} would {r['verb']} {self._fmt_args(r['kv'])}".rstrip())
        if pending:
            out.append("  next: " + "; ".join(pending))
        return "\n".join(out)

    # ---- export: the desk as the commands that rebuild it (round 11c) --------------------------------
    def cmd_export(self):
        """Emit desk commands that rebuild this desk from an empty one. Things are named by title, since ids
        are reassigned on replay. Says what it cannot carry (others' comments, resolved state, exact geometry)."""
        w = self.world
        out = ["# export of this desk; replay on an empty desk after one look", "look"]
        titles = {}
        for n in w.nodes.values():
            titles.setdefault(w.title(n).lower(), []).append(n["id"])
        dup = sorted(t for t, ids in titles.items() if len(ids) > 1 and not (
            len({w.nodes[i].get("subject") for i in ids}) == 1))   # several appearances of one subject are fine
        if dup:
            out.append("# WARNING: these titles name several different things, and replay resolves by title: " + ", ".join(dup))

        def q(s):
            return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'

        def ref(nid):
            return "desk" if nid == w.root else q(w.title(w.nodes[nid]))

        placed = set()
        skipped = []

        def walk(fid):
            for k in w.children(fid):
                if k["type"] == "surface" and k["layout"] == "view":
                    out.append(f"do create {ref(fid)} kind=view title={q(k['title'])} query={q(k.get('query', ''))}")
                    continue
                if k["type"] == "surface":
                    out.append(f"do create {ref(fid)} kind=surface title={q(k['title'])} layout={k['layout']}")
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
        if self.today:
            out.append(f"clock {self.today}")   # before the rules: a due<today rule cannot be defined without it
        for r in self.rules or []:
            out.append(f"rule {'' if r.get('on') else 'when '}{r['sel']} do {r['verb']} {self._fmt_args(r['kv'])}".rstrip())
        for name, body in (self.scripts or {}).items():
            out.append(f"script {name} = {body}")
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
        name, eq, body = arg.partition("=")
        name, body = name.strip(), body.strip()
        if not eq or not name or not body:
            raise Refusal("script <name> = <commands separated by ;>")
        if " " in name:
            raise Refusal("a script name is one word")
        self.scripts = self.scripts or {}
        self.scripts[name] = body
        return f"ok script {name} = {body}\n  run {name} [args]   ({body.count('$')} placeholder(s))"

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
            inside = body[:m.start()].count('"') % 2 == 1   # already inside a double-quoted value: paste raw
            if inside:
                return val.replace("\\", "\\\\").replace('"', '\\"')
            return '"' + val.replace("\\", "\\\\").replace('"', '\\"') + '"' if (" " in val or not val) else val
        line = re.sub(r"\$(\d+)", fill, body)
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
                        try:
                            receipt = self.cmd_do_knife(r["verb"], [i], dict(r["kv"]))
                            r["fired"] += 1
                            fired = True
                            self._note(f"~ {r['id']} fired on {i}: " + receipt.splitlines()[0])
                        except Refusal as e:
                            self._note(f"~ {r['id']} could not {r['verb']} {i}: {e}")
                        for ev in self.world.events[n0:]:
                            ev["via"] = f"rule {r['id']}"
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

    def _one(self, args, name="desk"):
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
            return f"today is {self.today}" if self.today else "no clock set. clock YYYY-MM-DD sets today and re-evaluates the rules"
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", arg):
            raise Refusal("clock YYYY-MM-DD")
        self.today = arg
        self.world.today = arg
        self._run_rules(cause=None)
        return f"ok today is {arg}"

    def _selection_terms(self, token):
        """Titles are allowed wherever a selection term wants an id: in:Today, also:"Standup agenda", links:Tessera.
        `today` in a due term is the clock's date."""
        out = []
        if "today" in token:
            if not self.today:
                raise Refusal("today is unset; clock YYYY-MM-DD sets it")
            token = token.replace("today", self.today)
        for t in re.split(r",", token):
            for key in ("in:", "also:", "links:"):
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
            for p, kids in by_parent.items():
                out.append(f"  in {p} \"{w.title(w.nodes[p])}\":")
                out.extend("    " + self.line(i, 1) for i in kids)
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
            if not self.today:
                raise Refusal("$today is unset; clock YYYY-MM-DD sets it")
            line = line.replace("$today", self.today)
        words = line.split(None, 1)
        cmd = words[0].lower()
        arg = words[1].strip() if len(words) > 1 else ""
        if cmd == "rules":
            return self.cmd_rules()
        if cmd == "rule":
            return self.cmd_rule(arg)
        if cmd == "export":
            return self.cmd_export()
        if cmd == "why":
            return self.cmd_why(arg)
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
            positional = [a for a in argv[1:] if "=" not in a or a.startswith("?")]
            kv = {}
            for a in argv[1:]:
                if "=" in a and not a.startswith("?"):
                    k, _, v = a.partition("=")
                    kv[k] = v.replace("\\n", "\n")
            return self.cmd_do_knife(verb, positional, kv)
        return super().repl(line)

    def cmd_help(self, name):
        name = name.lower()
        if name in ("selections", "selection", "select"):
            return SELECTION_HELP
        if name in knife.PAIR_DOC:
            args, doc = knife.PAIR_DOC[name]
            return f"{name}  (pair verb; level 2)\n  {doc}\n  args: {args}\n  e.g. do {name} a20 a22" + (" to=a22" if name == "match" else "")
        if name in knife.SPECIALIZED:
            return f"no verb {name} here. general verbs: " + " ".join(knife.GENERAL + list(knife.PAIR_DOC)) + "\nselections do the specializing (help selections)."
        return super().cmd_help(name)

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
                pend = moo.unanswered(w, s["id"])
                out.append("  awaiting reply: " + " | ".join(pend) if pend else "  nothing awaiting a reply")
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
                if last and last[-1]["by"] != "jeff":
                    stale.append(f"{i} (changed by {last[-1]['by']})")
        if stale:
            raise Refusal("stale: " + ", ".join(stale) + "; look at them again before acting")

    def cmd_do_knife(self, verb, positional, kv):
        w = self.world
        if not positional:
            raise Refusal("do needs a target after the verb")
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
            alt = {"reply": "append (examine the chat: it shows what awaits a reply)", "dedupe": "remove also:<id>",
                   "reveal": "raise", "tidy": "tile", "split": "group kind:<k>,in:<surface> then tile the surface as=row",
                   "gather": "move ?<words> into=<surface> one=1", "done": "retitle", "stack": "tile"}.get(verb, "a general verb")
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
