"""The MOO desk: same notation as Desk, verbs come from moo.REGISTRY with inheritance and an adapter.

New commands: examine id, help [verb], verbs id (by origin). `do` goes through the adapter.
"""

import shlex

import moo
from desk import Desk, HELP
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
            return self.cmd_help(arg.lstrip("@")) if arg else HELP_MOO
        if cmd in ("examine", "x", "ex"):
            return self.cmd_examine(arg.split()[0] if arg else None)
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
                kv[k] = v.replace("\\n", "\n")
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
        nid = self._resolve(ident or "desk", allow_subject=False)
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
            first = s["text"].strip().splitlines()[0][:80] if s["text"].strip() else "(no text)"
            self._mark_seen(s["id"])
            apps = w.appearances_of(s["id"])
            out.append(f"  a {s['kind']} (subject {s['id']}) on {n['parent']}; text begins: {first}")
            if len(apps) > 1:
                out.append("  also appears at " + ", ".join(f"{a} in {w.nodes[a]['parent']}" for a in apps if a != nid))
        out.append("  where: " + self._where_line(nid))
        for origin, names in moo.verbs_by_origin(w, nid).items():
            out.append(f"  verbs from {origin}: " + " ".join(names))
        out.append("  (help <verb> explains one; do <verb> " + nid + " ... uses it)")
        return "\n".join(out)

    def cmd_verbs(self, ident):
        nid = self._resolve(ident)
        if nid in self.world.subjects:
            return super().cmd_verbs(nid)
        self._mark_seen(nid)
        out = [f"{nid} verbs:"]
        for origin, names in moo.verbs_by_origin(self.world, nid).items():
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
        seen = self.seen.get(nid)
        if seen is None:
            raise Refusal(f"you have not looked at {nid} yet; look, examine or read it first")
        if seen != cur:
            raise Refusal(f"stale: {nid} changed since you last saw it; look at it again before acting")
        kv = {k: self._resolve(v, allow_subject=False) if k in ("into", "before", "after") else v for k, v in kv.items()}
        v = moo.REGISTRY[name]
        r = v.run(w, nid, kv)
        for e in r.get("events", []) or ([r["event"]] if r.get("event") else []):
            ev = next((x for x in w.events if x["id"] == e), None)
            if ev is not None:
                ev.setdefault("changed", []).extend(r.get("changed", []))
                ev["via"] = name
        self._after_mutation()
        evs = r.get("events") or ([r["event"]] if r.get("event") else [])
        head = f"ok {name} {nid} {self._fmt_args(kv)}".rstrip()
        if note:
            head += " " + note
        if evs:
            head += f"  [{evs[0]}" + (f"..{evs[-1]}, {len(evs)} steps" if len(evs) > 1 else "") + "]"
        out = head
        if r.get("created"):
            out += f" → created {r['created']}"
            cid = str(r["created"]).split()[0]
            if cid in w.nodes:
                out += "\n  " + self.line(cid, 1) + "\n    where: " + self._where_line(cid)
        if r.get("note"):
            out += f"\n  {r['note']}"
        for c in r.get("changed", []):
            if c in w.nodes and c != nid:
                self.seen.pop(c, None)
        if nid in w.nodes:
            self._mark_seen(nid)
            out += "\n  now: " + self.line(nid, 1) + self.position_note(nid)
            if w.nodes[nid]["type"] == "surface" and v.level >= 2:
                out += "\n" + "\n".join("  " + self.line(k["id"], 1) for k in w.children(nid))
        return out
