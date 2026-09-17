"""The knife desk (round 7): the MOO desk with general verbs only, selections as targets, and pair verbs."""

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
  title:agenda       title contains the word
  a20,a22            an explicit list
combine terms with commas (AND): kind:image,in:f04. The receipt lists everything the verb touched.
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

    def child_extra(self, nid, depth):
        if not self.bullets:
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
        rest = len(tl) - 1
        line = f"{ind}* {tl[0][:100]}"
        if rest:
            line += f"  (+{rest} more line(s); examine {nid})"
        return line

    def cmd_find(self, words):
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
        words = line.split(None, 1)
        cmd = words[0].lower()
        arg = words[1].strip() if len(words) > 1 else ""
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
        if n["type"] == "surface":
            kids = w.children(nid)
            out.append(f"  a {n['layout']} surface" + (f" inside {n['parent']}" if n["parent"] else " (the desk itself)")
                       + (f", holding {len(kids)} thing(s): " + ", ".join(k["id"] for k in kids) if kids else ", empty"))
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
        sel = knife.parse_selection(w, positional[0])
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
