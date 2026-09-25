"""The MOO desk: same notation as Desk, verbs come from moo.REGISTRY with inheritance and an adapter.

New commands: examine id, help [verb], verbs id (by origin). `do` goes through the adapter.
"""

import shlex

import moo
from desk import Desk, HELP, aspects_of, unescape_value
from world import Refusal

HELP_MOO = HELP.replace(
    "  do verb id k=v ...     change something. e.g. do move a04 into=f02   do append a03 line=\"new item\"",
    "  examine id             description plus every verb this thing answers to, by origin\n"
    "  help [verb]            what a verb does, its arguments, one example\n"
    "  do verb id k=v ...     change something. e.g. do move a04 into=f02   do tidy f04   do gather f02 words=harbor by=due",
).replace("  plan / apply           (apply variant only) paste an edited outline; the desk diffs it into ops\n", "")


class DeskMoo(Desk):
    def __init__(self, world, variant="moo"):
        super().__init__(world, "outline")
        self.variant = variant
        self.adapter = moo.Adapter()
        self.world.coords = True
        self.acme = variant == "acme"       # verbs shown inline on outline lines, plus usage nudges
        self.streak = {}                    # surface id -> count of consecutive low-level placement calls
        self.nudged = set()

    def verb_hints(self, nid):
        if not self.acme:
            return None
        w = self.world
        n = w.nodes[nid]
        out = []
        if n["type"] == "surface":
            kids = w.children(nid)
            if len(kids) >= 2 and n["layout"] == "free" and any(w.hidden_fraction(k["id"]) > 0.05 for k in kids):
                out += ["tidy", "split"]
            elif len(kids) >= 2 and n["layout"] != "free":
                out.append("sort")
            if n["layout"] != "free" or not kids:
                out.append("gather")
        else:
            s = w.subjects[n["subject"]]
            if w.hidden_fraction(nid) > 0.05:
                out.append("reveal")
            if len(w.appearances_of(s["id"])) > 1:
                out.append("dedupe")
            if s["kind"] == "chat" and moo.unanswered(w, s["id"]):
                out.append("reply")
            for c in s.get("comments", []):
                if not c["resolved"] and c["by"] != "alex":
                    out.append(f"resolve {c['id']}")
        return out or None

    def _nudge(self, name, nid, kv):
        """After repeated low-level placement on one surface, say once which verb does it in one call."""
        if not self.acme:
            return ""
        w = self.world
        n = w.nodes.get(nid)
        if not n or not n["parent"]:
            return ""
        p = n["parent"]
        low = name in ("move", "resize") and any(k in kv for k in ("to", "by", "before", "after"))
        self.streak[p] = self.streak.get(p, 0) + 1 if low else 0
        if self.streak[p] >= 3 and p not in self.nudged:
            self.nudged.add(p)
            pl = w.nodes[p]["layout"]
            if pl == "free":
                return (f"\n  hint: that is the third placement by hand in {p}. `split {p} by=kind left=image` or "
                        f"`tidy {p} as=row` arranges everything in one call (help split).")
            return f"\n  hint: `sort {p} by=due` (or by=title) orders all of {p} in one call."
        return ""

    # verbs come from the registry from here on
    def _verb_names(self):
        return set(moo.REGISTRY) | set(moo.SYNONYMS)

    def repl(self, line):
        line = (line or "").strip()
        if not line:
            return HELP_MOO
        words = line.split(None, 1)
        cmd = words[0].lower()
        arg = words[1].strip() if len(words) > 1 else ""
        if cmd in ("help", "?"):
            if not arg:
                return HELP_MOO
            return "\n\n".join(self.cmd_help(a.lstrip("@")) for a in arg.split())
        if cmd in ("examine", "x", "ex"):
            try:
                words = shlex.split(arg)
            except ValueError as e:
                raise Refusal(f"could not parse: {e}")
            if len(words) > 1:
                raise Refusal(f"examine takes only an id; depth belongs to look (look {words[0]} :3 shows everything under it)")
            return self.cmd_examine(words[0] if words else None)
        if cmd == "verbs":
            return self.cmd_verbs(arg.split()[0] if arg else None)
        if cmd == "do":
            try:
                argv = [a.lstrip("@") for a in shlex.split(arg)]
            except ValueError as e:
                raise Refusal(f"could not parse: {e}")
            if len(argv) < 2:
                raise Refusal("do needs: do <verb> <id> [k=v ...]")
            kv = {}
            for a in argv[2:]:
                k, eq, v = a.partition("=")
                if not eq:
                    raise Refusal(f"argument {a!r} must be key=value")
                kv[k] = unescape_value(v)
            verb, target = argv[0], argv[1]
            if target.lower() in self._verb_names() and verb.lower() not in self._verb_names() and (verb in self.world.nodes or verb in self.world.subjects):
                verb, target = target, verb
            return self.cmd_do(verb, target, kv)
        return super().repl(line)

    def cmd_help(self, name):
        name = name.lower()
        if name in moo.SYNONYMS and name not in moo.REGISTRY:
            name2 = moo.SYNONYMS[name]
            return f"{name} is not a verb here; the desk would read it as {name2}.\n" + self.cmd_help(name2)
        v = moo.REGISTRY.get(name)
        if not v:
            return f"no verb {name}. verbs: " + " ".join(sorted(moo.REGISTRY)) + "\nexamine <id> shows which apply to a thing."
        on = ", ".join(v.kinds)
        return (f"{v.name}  (on: {on}; level {v.level})\n  {v.doc}\n"
                + (f"  args: {v.args}\n" if v.args else "") + f"  e.g. {v.example}")

    def cmd_examine(self, ident):
        nid = self._resolve(ident or "desk")
        if nid in self.world.subjects:
            return self.cmd_pivot(nid)
        w = self.world
        self._mark_seen(nid)
        n = w.nodes[nid]
        out = [self.line(nid, 1)]
        if n["type"] == "surface":
            kids = w.children(nid)
            out.append(f"  a {n['layout']} surface" + (f" inside {n['parent']}" if n["parent"] else " (the desk itself)")
                       + (f", holding {len(kids)} thing(s): " + ", ".join(k["id"] for k in kids) if kids else ", empty"))
        else:
            s = w.subjects[n["subject"]]
            tl = [l for l in s["text"].strip().splitlines() if l.strip()]
            first = " / ".join(l[:80] for l in tl[:2]) if tl else "(no text)"
            more = f"  (+{len(tl) - 2} more line(s), {len(s['text'].split())}w; read {nid} for all)" if len(tl) > 2 else ""
            self._mark_seen(s["id"])
            apps = w.appearances_of(s["id"])
            out.append(f"  a {s['kind']} (subject {s['id']}) on {n['parent']}; text: {first}{more}")
            if len(apps) > 1:
                out.append("  also appears at " + ", ".join(f"{a} in {w.nodes[a]['parent']}" for a in apps if a != nid))
            if s["kind"] == "chat":
                pend = moo.unanswered(w, s["id"])
                out.append("  awaiting reply: " + " | ".join(pend) if pend else "  nothing awaiting a reply")
        out.append("  where: " + self._where_line(nid))
        for origin, names in moo.verbs_by_origin(w, nid).items():
            out.append(f"  verbs from {origin}: " + "  ".join(
                nm + (f"({moo.REGISTRY[nm].args.split('  (')[0].strip()})" if moo.REGISTRY[nm].args else "") for nm in names))
        big = [moo.REGISTRY[nm] for names in moo.verbs_by_origin(w, nid).values() for nm in names if moo.REGISTRY[nm].level >= 2]
        for v in big:
            out.append(f"    {v.name}: {v.doc.split('.')[0]}.")
        out.append("  (help <verb> [<verb> ...] explains; do <verb> " + nid + " ... uses one)")
        return "\n".join(out)

    _hidden_verbs = ()   # the knife desk hides the specialized verbs everywhere, not only in examine

    def _verbs_by_origin(self, nid):
        return moo.verbs_by_origin(self.world, nid)

    def subject_verbs_line(self, sid):
        """Subject verbs from the registry: the text-level verbs of its kind, plus place. One verb source."""
        s = self.world.subjects[sid]
        chain = set(moo.KIND_CHAIN.get(s["kind"], [])) - {"appearance", "thing"}
        names = [v.name for v in moo.REGISTRY.values() if set(v.kinds) & chain]
        if not self.world.checklist(s["text"]):
            names = [n for n in names if n != "check"]
        names = [n for n in names if n not in self._hidden_verbs]
        return "  verbs: " + " ".join(names) + " · place into=<surface> (a new appearance)   (help <verb> for args; edits change every appearance)"

    def cmd_verbs(self, ident):
        nid = self._resolve(ident)
        if nid in self.world.subjects:
            return f"{nid} verbs:\n" + self.subject_verbs_line(nid)
        self._mark_seen(nid)
        out = [f"{nid} verbs:"]
        for origin, names in self._verbs_by_origin(nid).items():
            for name in names:
                v = moo.REGISTRY[name]
                out.append(f"  {name} {v.args}".rstrip() + f"   - {v.doc.split('.')[0]}." + (f"  [{origin}]" if origin != "thing" else ""))
        return "\n".join(out)

    def cmd_do(self, verb, target, kv):
        if not verb or not target:
            raise Refusal("do needs a verb and an id")
        w = self.world
        nid = self._resolve(target)
        if nid in w.subjects:
            return super().cmd_do(verb, target, kv)
        name, note = self.adapter.resolve(w, verb, nid)
        cur = w.nodes[nid]["rev"]
        seen = cur if getattr(self, "_in_rules", False) else self.seen.get(nid)   # a rule is the desk's own hands: no fence
        if seen is None:
            raise Refusal(f"you have not looked at {nid} yet; look, examine or read it first"
                          + (" (on a fresh desk, start with look)" if not self.seen else ""))
        # Sable's spec 1, first test: the fence is keyed by (subject, aspect). A windowed reader (Juniper's step 11) is
        # judged on what it saw, whoever acted since; an unwindowed one is excused its own deeds.
        mine = aspects_of(name, kv)
        hit = name not in ("create", "comment") and self._touched_by_others(nid, mine, others_only=not getattr(self, "_window", ""))
        if hit:
            via = f" through {hit['target']}" if hit["target"] != nid else ""
            who = "you, in your other window" if hit["by"] == self.world.me else hit["by"]
            raise Refusal(f"stale: {nid} changed since you last saw it{via} ({hit['id']} {hit['verb']} by {who}); look at it again before acting")
        kv = {k: self._resolve(v, allow_subject=False) if k in ("into", "before", "after") else v for k, v in kv.items()}
        v = moo.REGISTRY[name]
        r = v.run(w, nid, kv)
        for e in r.get("events", []) or ([r["event"]] if r.get("event") else []):
            ev = next((x for x in w.events if x["id"] == e), None)
            if ev is not None:
                ev.setdefault("changed", []).extend(r.get("changed", []))
                ev["via"] = name
                ev["window"] = getattr(self, "_window", "") or ""     # which of this actor's windows acted (Sable: the observer)
        self._after_mutation()
        for c in {nid, *r.get("changed", [])}:      # you did it, you saw the result of what YOU touched; the scan for others' deeds still
            if c in w.nodes:                        # starts at your last real look, and it is keyed by aspect (Sable's spec 1)
                self.seen[c] = w.nodes[c]["rev"]
            elif c in w.subjects:
                self.seen[c] = w.subjects[c]["rev"]
        evs = r.get("events") or ([r["event"]] if r.get("event") else [])
        head = f"ok {name} {nid} {self._fmt_args(kv)}".rstrip()
        if note:
            head += " " + note
        if name == "move" and ("before" in kv or "after" in kv) and nid in w.nodes and w.nodes[nid]["parent"] \
                and w.nodes[w.nodes[nid]["parent"]]["layout"] == "free":
            head += f"\n  note: {w.nodes[nid]['parent']} is a free surface, so before/after only changed stacking order, not position. tile it for order to mean position."
        if evs:
            head += f"  [{evs[0]}" + (f"..{evs[-1]}, {len(evs)} steps" if len(evs) > 1 else "") + "]"
        out = head
        if r.get("created"):
            out += f" → created {r['created']}"
            cid = str(r["created"]).split()[0]
            if cid in w.nodes:
                out += "\n  " + self.line(cid, 1)
                parent = w.nodes[cid]["parent"]
                if parent and w.nodes[parent]["layout"] == "free":
                    out += "\n    where: " + self._where_line(cid)   # geometry matters only where things can overlap
        if r.get("note"):
            out += f"\n  {r['note']}"
        for c in r.get("changed", []):
            if c in w.nodes and c != nid:
                self._mark_rev(c)    # your own change; the receipt shows the revision, not the other aspects
        if nid in w.nodes:
            self._mark_rev(nid)
            self._receipt = True
            try:
                out += "\n  now: " + self.line(nid, 1) + self.position_note(nid)
            finally:
                self._receipt = False
            if w.nodes[nid]["type"] == "surface" and v.level >= 2:
                out += "\n" + "\n".join("  " + self.line(k["id"], 1) for k in w.children(nid))
        out += self._nudge(name, nid, kv)
        return out
