"""Text notations over the World, plus a one-line REPL grammar.

Experiments carried by this module:
  * fold-as-budget: level 1 = one folded line, level 2 = opened (children folded), level 3 = focus.
  * seen-fencing: `do` is refused unless the caller has seen the target at its current rev.
    Lines carry no revision numbers; the desk remembers what it showed you.
  * delta header: every look begins with what changed since your last look.
  * relations variant: geometry printed as spatial relations, coordinates on request.
  * apply variant: edit the outline text, the desk diffs it into operations.
"""

import re
import shlex
from copy import deepcopy

from world import Refusal, SCREEN, World
import persons

HELP = """commands (one per call):
  look [id] [:1|:2|:3|:4] outline from id (default desk). :1 the line, :2 its children (default), :3 everything under it with first lines, :4 with full text
  open id | close id     expand / collapse id in later looks (view only; nothing moves)
  read id                full text of a note/task/etc (via an appearance or subject id)
  where id               exact geometry and spatial relations
  verbs id               what you can do to id, with argument forms
  pivot id               appearance -> its subject and every place it appears; subject -> appearances
  find words             search titles and text
  history [id]           recent events (with undo ids); history e12 one event, what it caused, its undo
  log-world [check|status|baseline <note>] isolated log replay; baseline needs a documented request and matching full check
  do verb id k=v ...     change something. e.g. do move a04 into=f02   do append a03 line="new item"
  undo eN                revert an event
  plan / apply           (apply variant only) paste an edited outline; the desk diffs it into ops
ids: f.. surface, a.. appearance, s.. subject, e.. event, c.. comment, l.. link. quote values with spaces."""


class Unanswered(Refusal):
    """Nothing answers the line's first word: no command, no verb in the world. For a resident's > line (whole) it is a
    miss, not a refusal: it changed nothing, so the lines after it still run (Sable, a736 c742)."""


# a1308: every kind of id the house prints, and what each names. A refusal that lists some of them can't name the door
# to the rest (s1286: 'ids look like f02, a05, s03' left out the e-ids every !! line hands out)
ID_HINT = ("ids: f02 a surface or room, a05 a thing on one, s03 what a thing says (its subject), e12 an event, c40 a "
           "comment, l41 a link, m42 a chat line; use look or find")
RECORD_KINDS = {"e": "an event", "c": "a comment", "l": "a link", "m": "a chat line"}
RECORD_ID = re.compile(r"^([eclm])(\d+)$")
HASH = re.compile(r"^[0-9a-f]{7,40}$")

BASE_COMMANDS = {"help", "?", "look", "open", "close", "read", "where", "verbs", "pivot", "find", "history", "undo",
                 "do", "plan", "apply", "log-world"}


def aspects_of(verb, args):
    """The aspects a deed touches, as Sable's spec 1 names them: prop:<k>, title, text, due, tags, place.
    None means everything (a verb this table does not know)."""
    a = args or {}
    if verb == "prop":
        return {f"prop:{k}" for k in a if k not in ("at", "_by", "remove")} | {f"prop:{k.strip()}" for k in str(a.get("remove", "")).split(",") if k.strip()}
    if verb == "put":
        # a1069: a card put in a lane's order touches its props; put with a move's arguments is move (a synonym)
        if any(k in a for k in ("into", "before", "after", "to", "by")):
            return {"place"}
        return {"prop:status", "prop:priority", "prop:rank"}
    if verb in ("retitle", "rename"):
        return {"title"}
    if verb == "edit":
        return {k for k in ("title", "text", "due") if k in a} | ({"text"} if "append" in a else set()) or None
    if verb in ("rewrite", "replace", "append", "reply", "check", "uncheck", "split", "seal", "unseal"):
        return {"text"}              # reply is the chat verb: it adds a line to the text (a656; it was counted as comments)
    if verb == "due":
        return {"due"}
    if verb in ("tag", "untag"):
        return {"tags"}
    if verb in ("comment", "resolve"):
        return {"comments"}           # Juniper: a comment must not refresh a finish, nor stale a card's gestures
    if verb in ("link", "unlink"):
        return {"links"}
    if verb == "go":
        return {"presence"}           # a678: where an actor is; no thing's aspect
    if verb == "knock":
        return {"knock"}              # a3150: the house's record of whom a line knocked; no thing's aspect
    if verb == "create":
        # 30 Sep: a create adds to a surface's contents and changes none of its props or title. It counted as touching
        # everything, so a resident making a note in its corner staled Alex's wake/rest press (prop want=) on the corner.
        return {"contents"}
    if verb in ("move", "resize", "place", "tile", "untile", "stack", "fold", "unfold", "sort", "tidy", "gather", "swap",
                "beside", "match", "align", "flow", "size", "raise", "lower", "group", "cast", "dedupe", "pop", "remove"):
        # remove takes an appearance off its surface: the subject and all it says survive (undo puts it back), so it is
        # fenced as the other placement verbs are. Alex, 29 Sep: deleting a task from the Desktop was refused over an
        # owner removed hours before the page was painted, a change no view could show.
        return {"place"}
    if verb == "promises" and a.get("aspects"):
        # a1587: the migration says which aspects it touched (owe=, awaiting=, a view's query, a lens's text), so a card
        # whose awaiting= went is not 'doing since' the migration
        return set(a["aspects"])
    return None


def event_aspects(e):
    """The aspects a recorded event touched. `via` names the verb a person used when it is one (append, tidy);
    an act through a selection ("tag in:f02") or by a rule ("rule r1") keeps its verb as the first word or not at
    all, so the recorded primitive decides then (review 29 Sep: such events counted as touching everything)."""
    via = str(e.get("via") or "").split(" ", 1)[0].lower()
    if via and via != "rule":
        a = aspects_of(via, e.get("args"))
        if a is not None:
            return a
    return aspects_of(e["verb"], e.get("args"))


def rule_did_unseen(e, me):
    """An event a rule did as `me`, its author, while someone else tripped it (a687). The author did not watch it
    happen, so it is not on their receipts: it counts as someone else's deed for their fence and their !! line."""
    return e["by"] == me and e.get("tripped_by") not in (None, me)


def _within_hour(first, e):
    """a1471: does e fall within an hour of first? An event without a wall time counts as within."""
    from datetime import datetime
    try:
        return abs((datetime.fromisoformat(e["at"]) - datetime.fromisoformat(first["at"])).total_seconds()) < 3600
    except (KeyError, TypeError, ValueError):
        return True


def _line_change(old, new):
    """a1471: which lines of a text a change touched -> (word, line numbers in the new text, or the old for removed)."""
    import difflib
    a, b = old.splitlines(), new.splitlines()
    ops = [op for op in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if op[0] != "equal"]
    if not ops:
        return "rewrote", []
    touched = sum(max(i2 - i1, j2 - j1) for _, i1, i2, j1, j2 in ops)
    if touched > 3 and touched * 2 > max(len(a), len(b)):
        return "rewrote", []
    if len(ops) == 1:
        tag, i1, i2, j1, j2 = ops[0]
        if tag == "insert":
            return "added", list(range(j1 + 1, j2 + 1))
        if tag == "delete":
            return "removed", list(range(i1 + 1, i2 + 1))
        return "replaced", list(range(j1 + 1, j2 + 1))
    return "changed", sorted({n for _, i1, i2, j1, j2 in ops for n in (range(j1 + 1, j2 + 1) if j2 > j1 else [j1 + 1])})


def _numbered(noun, nums):
    """line 8 · lines 3-5 · lines 3, 8, 12 · lines 3, 8, 12, 15, 20 and 4 more"""
    if len(nums) == 1:
        return f"{noun} {nums[0]}"
    if nums == list(range(nums[0], nums[-1] + 1)):
        return f"{noun}s {nums[0]}-{nums[-1]}"
    return f"{noun}s " + ", ".join(map(str, nums[:5])) + (f" and {len(nums) - 5} more" if len(nums) > 5 else "")


def aspects_meet(a, b):
    """Do two aspect sets overlap? Either side unknown (None) counts as everything."""
    return a is None or b is None or bool(a & b)


def unescape_value(v):
    """A k=v value after shlex: an unescaped \\n is a newline; \\\\ is one literal backslash (so \\\\n stays literal)."""
    return re.sub(r"(?<!\\)\\n", "\n", v).replace("\\\\", "\\").replace("\\$", "$")


def split_batch(line):
    """Split on ; or newlines outside quotes."""
    out, cur, q, esc = [], "", None, False
    for ch in line or "":
        if q:
            cur += ch
            if esc:
                esc = False
            elif ch == "\\":
                esc = True   # an escaped quote inside a value does not close it (export writes \" inside text=)
            elif ch == q:
                q = None
        elif ch in "\"'":
            q = ch
            cur += ch
        elif ch in ";\n":
            if cur.strip():
                out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out or [""]


class Desk:
    def __init__(self, world: World, variant="outline"):
        self.world = world
        self.variant = variant
        self.open = {world.root}
        self.seen = {}          # id -> rev last shown to the caller
        self.last_event_seen = 0
        self.injections = world.injections
        self.hooks = []         # callables run after each successful mutation (for scenarios)
        self.world.coords = variant != "tree"
        self.hide_coords = variant in ("relations", "tree")

    # ---- public harness surface -------------------------------------
    @property
    def events(self):
        return self.world.events

    def snapshot(self):
        return self.world.snapshot()

    batch = False   # round 9: several commands per call, ; or newline separated; $new = last created surface
    read_cap = None # round 11 (lean): at most this many read/examine commands per call; the rest are folded, visibly

    def dispatch(self, name, args):
        # Worktree recording happens once per call, after a batch may have stopped.
        # Keep the actual steps and their event ranges, including read-only steps;
        # matching appends by target alone would confuse two sends to one chat.
        journal = {"line": args.get("line", ""), "steps": []}

        def one(step_args, step_name="desk", whole=False):
            n0 = len(self.world.events)
            result = self._one(step_args, step_name, whole=whole)
            journal["steps"].append({
                "line": step_args.get("line", ""),
                "events": [e["id"] for e in self.world.events[n0:]],
                "ok": "error" not in result and not result.get("miss"),
            })
            if getattr(self, "_wt", None) is not None and name == "desk":
                self._journal_dispatch = journal
            return result

        self.__dict__.pop("_journal_dispatch", None)
        if name == "desk" and args.get("whole"):
            # a736: a line a resident typed after > is one command; a ; in it is words (the desk may still refuse them)
            return one({"line": args.get("line", "")}, whole=True)
        if self.batch and name == "desk":
            parts = split_batch(args.get("line", ""))
            if parts and parts[0].lower().startswith("script "):
                parts = [args.get("line", "").strip()]   # a script definition keeps its ; for later
            if len(parts) > 1:
                outs, error = [], False
                reads = 0
                for i, part in enumerate(parts):
                    if self.read_cap and part.split()[0].lower() in ("read", "examine"):
                        reads += 1
                        if reads > self.read_cap:
                            rest = parts[i:]
                            outs.append(f"({len(rest)} later command(s) not run: at most {self.read_cap} reads per call. "
                                        f"Not run: {'; '.join(rest)}. Ask for them in another call, or narrow with find)")
                            break
                    shown = self._echo(part)
                    r = one({"line": part})
                    body = r["text"] if "text" in r else "ERR " + r["error"]
                    outs.append(f"[{i + 1}] {shown}\n{body}")
                    if "error" in r:
                        error = True
                        if i < len(parts) - 1:
                            rest = parts[i + 1:]
                            if not getattr(self, "_ctxs", None) and hasattr(self, "_hold"):
                                for p in rest:      # a6437: what they would have made is held back from later lines
                                    self._hold(p)
                            outs.append(f"(stopped; {len(rest)} later command(s) not run. Not run: {'; '.join(rest)}. "
                                        f"Fix [{i + 1}] and resubmit them in one call)")
                        break
                return {"text": "\n\n".join(outs), "batch": len(parts), "batch_error": error}
        return one(args, name)

    _cmd_no = 0

    def _echo(self, part):
        """How a command of a batch is echoed above its receipt: as written (a desk that fills blanks shows values)."""
        return part

    def _one(self, args, name="desk", whole=False):
        header = self.delta_header()
        self._cmd_no += 1
        n0 = len(self.world.events)
        r = self._dispatch(name, args)
        if "error" in r and not r.get("miss") and name == "desk" and not getattr(self, "_in_rules", False):
            import verbs        # a3806: a refusal leaves a trace (a miss left its own, in repl), counted by shape
            verbs.record_reach(self, args.get("line", ""), "refused", r["error"])
        if whole and r.get("miss"):
            # a736: a > line nothing answers is a miss. It says MISS, not ERR, so the lines after it go on
            r = {"text": f"MISS {r['error']}. Nothing ran; the lines after it still run", "miss": True}
        elif whole and "error" in r and len(split_batch(args.get("line", ""))) > 1:
            r["error"] += ("\n  (one > line is one command, and a ; in it is part of the words; for several commands, "
                           "put each command on its own > line)")
        for e in self.world.events[n0:]:
            e.setdefault("cmd", self._cmd_no)   # which command produced it: undo groups steps by this, not by verb
        if header:
            if "text" in r:
                r["text"] = header + r["text"]
            else:
                r["error"] = header + r["error"]
        return r

    def _dispatch(self, name, args):
        try:
            if name == "desk":
                line = args.get("line", "")
                return {"text": self.repl(line)}
            if name == "look":
                return {"text": self.repl(f"look {args.get('target', '')} :{args.get('level', 2)}".strip())}
            if name == "open":
                return {"text": self.repl(f"open {args.get('target', '')}")}
            if name == "read":
                return {"text": self.repl(f"read {args.get('target', '')}")}
            if name == "where":
                return {"text": self.repl(f"where {args.get('target', '')}")}
            if name == "verbs":
                return {"text": self.repl(f"verbs {args.get('target', '')}")}
            if name == "pivot":
                return {"text": self.repl(f"pivot {args.get('target', '')}")}
            if name == "find":
                return {"text": self.repl(f"find {args.get('words', '')}")}
            if name == "history":
                return {"text": self.repl(f"history {args.get('target', '')}".strip())}
            if name == "undo":
                return {"text": self.repl(f"undo {args.get('event', '')}")}
            if name == "do":
                return {"text": self.cmd_do(args.get("verb"), args.get("target"), dict(args.get("args") or {}))}
            return {"error": f"unknown tool {name}"}
        except Refusal as r:
            return {"error": str(r), **({"miss": True} if isinstance(r, Unanswered) else {})}

    # ---- repl -------------------------------------------------------
    def repl(self, line):
        line = (line or "").strip()
        if not line:
            return HELP
        first = line.split(None, 1)[0].lower()
        if first in ("plan", "apply"):
            head, _, rest = line.partition("\n")
        else:
            head, rest = line, ""
        try:
            words = shlex.split(head)
        except ValueError as e:
            if first.lstrip("@") in BASE_COMMANDS:
                raise Refusal(f"could not parse: {e}")
            import verbs
            hit = verbs.try_line(self, line, self.world.me)    # a806: say it's fine is a verb's words, apostrophe and all
            if hit is not None:
                return hit
            # a736: prose after > ("> I don't think so") has an apostrophe; nothing answers it, and it is a miss
            verbs.record_miss(self, line)
            raise Unanswered(f"unknown command {first!r}; nothing here answers to it. help lists the desk's commands; "
                             f"a verb anyone can make is a note tagged verb (help verbs)")
        cmd, argv = words[0].lower(), words[1:]
        argv = [a.lstrip("@") for a in argv]
        if cmd == "log-world":
            import log_world
            return log_world.command(self, argv)
        if cmd in ("help", "?"):
            return HELP
        if cmd == "look":
            level = 2
            target = None
            for a in argv:
                if a.startswith(":") and a[1:].isdigit():
                    level = int(a[1:])
                else:
                    target = a
            return self.cmd_look(target, level)
        if cmd in ("open", "close"):
            if not argv:
                raise Refusal(f"{cmd} needs an id")
            if len(argv) > 1:
                raise Refusal(f"{cmd} takes only an id; examine {argv[0]} shows what is inside")
            return self.cmd_fold(argv[0], cmd == "open")
        if cmd == "read":
            section, full, tail = None, False, None
            for a in argv[1:]:
                if a.startswith("#"):
                    section = a[1:]
                elif a in (":3", ":full"):
                    full = True
                elif a.startswith("tail="):
                    if not (a[5:].isdigit() and int(a[5:]) > 0):
                        raise Refusal("tail=<n> wants a positive number of lines")
                    tail = int(a[5:])
                elif section is not None and "=" not in a and not a.startswith(":"):
                    section += " " + a    # read a07 #Session 2: a section name may have spaces
            return self.cmd_read(argv[0] if argv else None, section, full, tail)
        if cmd == "where":
            return self.cmd_where(argv[0] if argv else None)
        if cmd == "verbs":
            return self.cmd_verbs(argv[0] if argv else None)
        if cmd == "pivot":
            return self.cmd_pivot(argv[0] if argv else None)
        if cmd == "find":
            return self.cmd_find(" ".join(argv))
        if cmd == "history":
            return self.cmd_history(argv[0] if argv else None)
        if cmd == "undo":
            return self.cmd_undo(argv[0] if argv else None)
        if cmd == "do":
            if len(argv) < 2:
                raise Refusal("do needs: do <verb> <id> [k=v ...]")
            kv = {}
            for a in argv[2:]:
                k, eq, v = a.partition("=")
                if not eq:
                    raise Refusal(f"argument {a!r} must be key=value")
                kv[k] = unescape_value(v)
            if argv[1].lower() in self._verb_names() and argv[0].lower() not in self._verb_names():
                return self.cmd_do(argv[1], argv[0], kv)
            return self.cmd_do(argv[0], argv[1], kv)
        if cmd in ("plan", "apply"):
            if self.variant != "apply":
                raise Refusal("plan/apply are not available in this desk; use do")
            return self.cmd_apply(rest, dry=(cmd == "plan"))
        import verbs      # tier 1: a word the desk does not know may be a verb someone made in the world
        hit = verbs.try_line(self, line, self.world.me)
        if hit is not None:
            return hit
        verbs.record_miss(self, line)
        if cmd in self._verb_names():
            # 9 Oct (a3806; Pike in Wishes, twice in two minutes): a built-in verb typed bare was called an unknown
            # command, in 235 characters that never said the one word missing. The line that runs is said as printed
            raise Unanswered(f"{cmd} is a verb, and a verb of the desk's own is typed after do: do {line.strip()}")
        raise Unanswered(f"unknown command {cmd!r}; nothing here answers to it. help lists the desk's commands; "
                      f"a verb anyone can make is a note tagged verb (help verbs)")

    def _verb_names(self):
        return {"move", "resize", "raise", "lower", "remove", "tile", "untile", "rename", "group", "fold", "unfold",
                "edit", "append", "retitle", "rewrite", "replace", "place"}

    # ---- rendering --------------------------------------------------
    def _resolve(self, ident, allow_subject=True):
        if not ident:
            raise Refusal("which id?")
        ident = ident.lstrip("@").strip().strip('"\'')   # any command may name a thing by its quoted title
        if ident.startswith("$") and ident[1:] in (getattr(self, "vars", None) or {}):
            ident = self.vars[ident[1:]]   # a handle you named: create ... as=draft, or set draft = a98
        import blanks
        if blanks.WORD.match(ident) and getattr(self, "_ctxs", None) is not None:
            ident = blanks.fill(self, ident)   # a806: a blank that reaches a target unfilled goes to the one filler
        if ident in ("desk", "root"):
            return self.world.root
        if ident.lower().startswith("corner:"):
            # a1027: someone's sill, by their name. The one place a name becomes a room: when persons have ids (a1016),
            # this is what changes
            import rooms
            who = ident[7:].strip()
            fid = rooms.corner_of(self.world, who)
            if not fid:
                raise Refusal(f"no sill for {who!r}: no corner says actor={who} (corner:<name> finds a resident's corner by "
                              f"the name it was given; a1016)")
            return fid
        if ident in self.world.nodes:
            return ident
        if allow_subject and ident in self.world.subjects:
            return ident
        hits = [n["id"] for n in self.world.nodes.values() if self.world.title(n).lower() == ident.lower()]
        # a990 (4), Pike e1804 (F25): a verb's title is a word, not a name. Verb notes stay out of title resolution, so
        # two rooms each growing a tidy never make `read tidy` ambiguous; a verb note is reached by its id
        verbish = [h for h in hits if self.world.nodes[h]["type"] == "appearance"
                   and "verb" in (self.world.subjects[self.world.nodes[h]["subject"]].get("tags") or [])]
        hits = [h for h in hits if h not in verbish]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            raise Refusal(f"{ident!r} names {len(hits)} things: {', '.join(hits)}; use an id")
        if verbish:
            raise Refusal(f"{ident!r} is a verb's word, not a name for a thing: the verb note is {', '.join(verbish)} "
                          f"(help {ident} explains it; read or change it by its id)")
        hit = persons.typed(self.world, ident) if allow_subject else None
        if hit:
            # a1568: a typed name is today's bearer; the door to an earlier one is said where the answer is printed
            self._person_note = hit[1]
            return hit[0]
        rec = self._record(ident)
        if rec:
            # a1308: an event, comment or link id the house printed is never 'no such id'; this command can't take it,
            # and the refusal names the ones that do
            raise Refusal(f"{ident} is {RECORD_KINDS[rec[0]]}, not a thing on the desk: examine {ident} or history "
                          f"{ident} shows it" + {"c": f"; do resolve {ident} closes it", "l": f"; do unlink <one end> "
                                                 f"id={ident} removes it"}.get(rec[0], ""))
        m = RECORD_ID.match(ident)
        if m:
            last = self.world.events[-1]["id"] if m.group(1) == "e" and self.world.events else None
            raise Refusal(f"no {RECORD_KINDS[m.group(1)].split(' ', 1)[1]} {ident} in this world"
                          + (f" (the latest event is {last}; history lists the recent ones)" if last else
                             " (it may have been undone or removed: history shows what happened)") + f". {ID_HINT}")
        if re.fullmatch(r"[afs]\d+", ident):
            # a1308: an id the world once held (the Handbook still names some) is not 'no such id': say where it went
            last = next((e for e in reversed(self.world.events) if e["target"] == ident
                         or (e.get("undo") or {}).get("delete") == ident), None)
            if last is not None:
                raise Refusal(f"{ident} is not in the world now; its last event was {last['id']} ({last['verb']} by "
                              f"{persons.by(self.world, last)}): examine {last['id']} shows it; history {ident} lists what happened to it")
        if HASH.match(ident) and any(ch.isdigit() for ch in ident) and not ident.isdigit():
            # a3295: the house keeps the door already: a landed card's landed= holds its commit. Name the card, or say
            # plainly that none has it (a commit a landing did not make: a worker's own, a docs export, another repo's)
            w = self.world
            cards = [a for s in w.subjects.values() for v in [str((s.get("props") or {}).get("landed") or "")]
                     if v and (v.startswith(ident) or ident.startswith(v)) for a in w.appearances_of(s["id"])[:1]]
            if cards:
                raise Refusal(f"no such id {ident!r}: it looks like a commit (the code's history, kept in git, outside the "
                              f"world), landed by " + ", ".join(f"{a} \"{w.title(w.nodes[a])[:80]}\"" for a in cards)
                              + f": read {cards[0]} (its comments say what it changed)")
            raise Refusal(f"no such id {ident!r}: it looks like a commit (the code's history, kept in git, outside the "
                          f"world), and no card here landed it: no landed= holds that hash (find prop:landed=<hash> finds "
                          f"the card that landed one). {ID_HINT}")
        raise Refusal(f"no such id {ident!r} ({ID_HINT})")

    def _touched_by_others(self, nid, fields=None, others_only=True):
        """Has a deed named this thing, its subject, or (for a surface) its membership since I last saw it, on an ASPECT
        my act is about to touch? Sable's spec 1: the fence is keyed by (referent, aspect), so a write to prop:surface
        does not block a write to prop:beds. `fields` is what my act touches (None = everything). `others_only` skips my
        own deeds, which a receipt already showed me; a windowed reader passes False and is judged on what it saw.
        Geometry that moved because a sibling reflowed is not a reason to refuse."""
        w = self.world
        seen = self._seen_index(nid)
        star = seen.get("*", 0)

        def since_for(aspects):
            # the earliest index among the aspects an event and my act share: unseen aspects were seen at 0
            if aspects is None:
                return min(seen.values()) if seen else 0
            # prop:* is a print that showed every prop, the absent ones too (absence is a value, R6): a prop that did
            # not exist when it was printed was seen as absent there (F5)
            return min(max(seen.get(a, 0), star, seen.get("prop:*", 0) if a.startswith("prop:") else 0)
                       for a in aspects) if aspects else star

        def hits_since(e, k):
            ea = event_aspects(e)
            if e["verb"] == "create" and e["target"] == nid:
                ea = {"contents"}         # a thing made inside this surface changed what it holds, not its title or props (F5)
            if not aspects_meet(fields, ea):
                return False
            rel = None if (fields is None and ea is None) else (fields & ea if (fields is not None and ea is not None) else (ea if fields is None else fields))
            return k >= since_for(rel)
        since = since_for(fields)          # an aspect never printed is judged from the beginning
        n = w.nodes.get(nid)
        names = {nid} | ({n["subject"]} if n and n.get("subject") else set())
        subj = n.get("subject") if n else None
        mywin = getattr(self, "_window", "") or ""
        for k, e in enumerate(w.events[since:], since):
            if e.get("undone") or (persons.mine(w, e) and (others_only or e.get("window", "") == mywin)
                                   and not rule_did_unseen(e, w.me)):
                continue                      # my own deeds from this window are already on my receipts; my rule's, tripped by another, are not
            if e["verb"] == "undo":
                # Sable's baseline (3): an undo's target is an event id, so the fence never saw what it reverted. It
                # touches what the reverted event touched, on the same aspects.
                ue = next((x for x in w.events if x["id"] == e["target"]), None)
                if ue is None:
                    continue
                if ue["target"] in names or (names & set(ue.get("changed") or [])):
                    if hits_since(ue, k):
                        return e
                continue
            hit = e["target"] in names
            # Sable: an edit through a sibling appearance changes what I am looking at; the event lists the subject as changed
            hit = hit or (subj and subj in (e.get("changed") or []) and e["verb"] not in ("place", "remove"))
            hit = hit or (n and n["type"] == "surface" and e["verb"] in ("sort", "tile", "untile", "remove", "move") and nid in (e.get("changed") or []))
            if hit and hits_since(e, k):
                return e
        return None

    def _observer(self):
        if getattr(self, "_firing_observer", None):
            return self._firing_observer   # a rule acting as its author: what is printed meanwhile is the tripper's to have seen (a687)
        win = getattr(self, "_window", "") or ""
        return self.world.me + ("/" + win if win else "")

    def _seen_index(self, nid, obs=None):
        """{aspect: event index of the last print that showed it}; "*" is a print that showed everything (a verb's own
        receipt, a rule's change). Older pickles hold one int, which was a whole look."""
        idx = getattr(self, "_seen_idx", None) or {}
        n = self.world.nodes.get(nid)
        out = {}
        for name in [nid] + ([n["subject"]] if n and n.get("subject") else []):    # a print of the appearance or of its subject
            v = idx.get((obs or self._observer(), name))
            if v is None:
                v = idx.get(((obs or self._observer()).split("/")[0], name))
            if v is None:
                continue
            for a, k in ({"*": v} if isinstance(v, int) else v).items():
                out[a] = max(out.get(a, 0), k)
        return out

    def _note_seen(self, nid, at, aspects=None, obs=None):
        """Juniper's first-line trap (attacks probe look-clears-the-fence, e04710b): a print reads only what it printed
        whole. A look that showed a title and a word count has not read the text."""
        idx = getattr(self, "_seen_idx", None)
        if idx is None:
            idx = self._seen_idx = {}
        key = (obs or self._observer(), nid)
        cur = idx.get(key)
        cur = {"*": cur} if isinstance(cur, int) else dict(cur or {})
        for a in (["*"] if aspects is None else aspects):
            cur[a] = at
        idx[key] = cur

    REPLACING = ("rewrite", "replace", "retitle", "rename", "edit", "due", "prop", "untag")

    def _adds_line(self, nid, verb, kv):
        """Sable a656: a line added to a chat replaces nothing, so it is never refused as stale (in a live room every
        message was refused if someone else spoke first). Rewriting, retitling or removing a chat stays fenced, and the
        adder's receipt does not count as reading the lines it did not see. Appends to notes are unchanged.
        a5068: not stale, but an agent's line can wait (_hold_line), when someone else spoke there since it last saw."""
        if verb == "edit":
            if set(kv or {}) != {"append"}:
                return False
        elif verb not in ("append", "reply") or (kv or {}).get("section"):
            return False
        n = self.world.nodes.get(nid)
        s = self.world.subjects.get(n.get("subject") if n else nid)
        return bool(s) and s["kind"] == "chat"

    def _blind(self, nid, verb, kv):
        """The aspect this act would replace without ever having had it printed, or None. Adding (tag, append, comment,
        check) carries no claim about the old value; replacing does. A rule is the desk's own hands."""
        if verb not in self.REPLACING or getattr(self, "_in_rules", False):
            return None
        seen = self._seen_index(nid)
        if "*" in seen:
            return None
        w = self.world
        n = w.nodes.get(nid)
        s = w.subjects.get(n["subject"]) if n and n.get("subject") else w.subjects.get(nid)
        if s is None:
            return None
        for a in sorted(aspects_of(verb, kv) or ()):
            if a in seen:
                continue
            k = a.partition(":")[2]
            valued = {"text": bool(s.get("text")), "title": True, "due": bool(s.get("due")), "tags": bool(s.get("tags"))}.get(a)
            if valued is None:
                valued = a.startswith("prop:") and k in (s.get("props") or {})
            if valued:
                return a
        return None

    def _again(self, nid, aspects):
        """The advice in a stale refusal names a print that would satisfy the rule: `look` never prints the text
        (Sable, S10), so a text write is sent to `read`, and to `read :3` when the note is folded."""
        if aspects is None or "text" in aspects:
            return self._read_hint(nid, "text").replace(" shows it", "").replace(" shows all of it", "") + " again"
        if aspects & {"tags", "comments", "links"}:       # look's line never prints these; read does
            return f"read {nid} again"
        return "look at it again"

    def _read_hint(self, nid, aspect):
        s = self.world.subjects.get((self.world.nodes.get(nid) or {}).get("subject") or nid) or {}
        t = s.get("text") or ""
        folded = aspect == "text" and any(h for h, _ in self.world.sections(t)) and (len(t.split()) > 300 or t.count("\n") >= 40)
        return f"read {nid} :3 shows all of it" if folded else f"read {nid} shows it"

    def _mark_rev(self, nid, aspects=None):
        """A receipt shows the result of what I touched, so the revision is seen; but it is not a look, so the scan for
        other observers' deeds on other aspects still starts at my last real look (Sable's spec 1; Juniper's two windows).
        The aspects I wrote I have seen (a person may change the start date they set): None marks everything, as a
        verb the aspect table does not know touches everything."""
        self._note_seen(nid, len(self.world.events), None if aspects is None else sorted(aspects))
        if nid in self.world.nodes:
            self.seen[nid] = self.world.nodes[nid]["rev"]
        elif nid in self.world.subjects:
            self.seen[nid] = self.world.subjects[nid]["rev"]

    def _mark_seen(self, nid, aspects=None):
        """`aspects`: what this print showed whole (None: everything, which only a verb's own result or a rule may say)."""
        if getattr(self, "_receipt", False):      # a receipt printing a line is not a look (see _mark_rev)
            return      # the act already marked the aspects it wrote; marking * here let a later rewrite drop unread text
        self._note_seen(nid, len(self.world.events), aspects)     # Sable: "who saw what" is the observer, actor plus window
        if nid in self.world.nodes:
            self.seen[nid] = self.world.nodes[nid]["rev"]
        elif nid in self.world.subjects:
            self.seen[nid] = self.world.subjects[nid]["rev"]

    def _place_words(self, nid):
        x, y, w, h = self.world.abs_rect(nid)
        cx, cy = x + w / 2, y + h / 2
        col = "left" if cx < SCREEN[0] / 3 else "right" if cx > 2 * SCREEN[0] / 3 else "mid"
        row = "top" if cy < SCREEN[1] / 3 else "bottom" if cy > 2 * SCREEN[1] / 3 else "mid"
        if col == "mid" and row == "mid":
            return "center"
        return f"{row}-{col}" if row != "mid" else col if col != "mid" else row

    def _geom(self, nid):
        n = self.world.nodes[nid]
        if self.hide_coords:
            if n["parent"] and self.world.nodes[n["parent"]]["layout"] != "free":
                return ""
            return self._place_words(nid)
        if n["parent"] and self.world.nodes[n["parent"]]["layout"] != "free":
            return f"{n['w']}x{n['h']}"
        return f"{n['w']}x{n['h']} at {n['x']},{n['y']}"

    def verb_hints(self, nid):
        """Verbs worth showing on this line right now. Plain desks show none; the acme desk overrides."""
        return None

    def view_matches(self, nid):
        """Ids a view currently shows. Plain desks have no selections, so no views."""
        return None

    def view_lines(self, nid, depth):
        return []

    def child_extra(self, nid, depth):
        """Extra lines printed under an appearance in an outline. Plain desks print none; the bullets desk overrides."""
        return None

    def line(self, nid, level=1):
        w = self.world
        n = w.nodes[nid]
        self._mark_seen(nid, ["title", "place", "due", "prop:*"] + [f"prop:{k}" for k in (n.get("props") or {})])    # the outline line: not the text, not the tags; every prop, absent ones too
        bits = []
        if n["type"] == "surface" and n["layout"] == "view":
            head = f"{nid} view \"{n['title']}\" of {n.get('query')}" + (f" as table {n['cols']}" if n.get("cols") else "")
            kids = []
            m = self.view_matches(nid)
            bits.append("query not evaluable" if m is None else f"{len(m)} match" + ("es" if len(m) != 1 else ""))
            if m is not None and hasattr(self, "_trash_note"):
                bits.append(self._trash_note(n.get("query", "")))      # a1327: never a silent leaving out
        elif n["type"] == "surface":
            kids = w.children(nid)
            head = f"{nid} surface \"{n['title']}\" {n['layout']}"
            geo = self._geom(nid) if n["parent"] else f"{n['w']}x{n['h']}"
            bits.append(geo)
            if n.get("props"):
                bits.append(" ".join(f"{k}={v}" for k, v in persons.shown_props(w, n["props"]).items()))
            bits.append(f"{len(kids)} inside" if kids else "empty")
            if kids and n["layout"] != "free":
                axis = "h" if n["layout"] == "column" else "w"
                share = min(k[axis] for k in kids)
                if share < 80 and self._geometry_said():
                    bits.append(f"cramped, {share}px each")   # fuller than it is tall: the fold that a screen would show
                lim = n["h"] if axis == "h" else n["w"]
                pos = "y" if axis == "h" else "x"
                spilled = sum(1 for k in kids if k[pos] + k[axis] > lim + 1) if self._geometry_said() else 0
                if spilled:
                    bits.append(f"{spilled} past the {'bottom' if axis == 'h' else 'right edge'} (offscreen)")
        else:
            s = w.subjects[n["subject"]]
            self._mark_seen(s["id"], ["title", "place", "due", "prop:*"] + [f"prop:{k}" for k in (s.get("props") or {})])    # a word count is not the text
            head = f"{nid} {s['kind']} \"{s['title']}\""
            if "rule" in (s.get("tags") or []) and hasattr(self, "rule_mark"):
                bits.append(self.rule_mark(s["id"]))     # a1027: a narrated look leaves rules out; the tree marks them
            geo = self._geom(nid)
            if geo:
                bits.append(geo)
            if s.get("due"):
                bits.append(f"due {s['due']}")
            if s.get("props") and s["kind"] == "trial":
                p = s["props"]   # a trial's line reads as a result, not as a property dump
                bits.append(" ".join(x for x in [p.get("task", ""), str(p.get("model", "")).replace("gpt-5.6-", ""),
                                                 p.get("status", ""),
                                                 ("FAIL" + (f" ({p['failed']})" if p.get("failed") else "")) if p.get("pass") == "0"
                                                 else "pass" if p.get("pass") == "1" else "",
                                                 p.get("score", ""),
                                                 f"{p['calls']} calls" if p.get("calls") else "",
                                                 f"{p['seconds']}s" if p.get("seconds") else ""] if x))
            elif s["kind"] == "promise":
                import promises     # a1587: how it stands, as it reads to you ('asked of you by sable'), not its to=
                st = promises.state(w, s["id"])
                bits.append(promises.phrase(w, st) + (f" · about {st['about']}" if st["about"] else ""))
            elif s.get("props"):
                bits.append(" ".join(f"{k}={v}" for k, v in persons.shown_props(w, s["props"]).items() if k not in ("label", "started")))
            if s["kind"] in ("note", "task", "chat", "doc", "trial"):
                bits.append(f"{len(s['text'].split())}w")
            if n["folded"]:
                bits.append("folded")
            others = len(w.appearances_of(s["id"])) - 1
            if others:
                bits.append(f"also x{others}")
            if s.get("comments"):
                open_ = sum(1 for c in s["comments"] if not c["resolved"])
                bits.append(f"{len(s['comments'])} comment" + ("s" if len(s["comments"]) != 1 else "") + (f", {open_} open" if open_ else ""))
            nl = len(w.links_of(s["id"]))
            if nl:
                bits.append(f"{nl} link" + ("s" if nl != 1 else ""))
            if s["kind"] == "doc":
                secs = [h for h, _ in w.sections(s["text"]) if h]
                if secs:
                    bits.append(f"{len(secs)} sections")
        hid = w.hidden_fraction(nid)
        if hid > 0.05:
            by = [r.split()[1] for r in w.relations(nid) if r.startswith("under")]
            bits.append(("hidden" if hid >= 0.95 else f"{int(hid * 100)}% hidden") + (" by " + ",".join(by) if by else ""))
        for r in w.relations(nid) if self._geometry_said() else ():
            if r.startswith(("offscreen", "spills")):
                bits.append(r)
        if n["type"] == "surface":
            covered = [r.split()[1] for r in w.relations(nid) if r.startswith("covers") and w.nodes[r.split()[1]]["type"] == "surface"]
            if covered:
                bits.append("covers " + ",".join(covered))
        hints = self.verb_hints(nid)
        if hints:
            bits.append("try: " + " ".join(hints))
        out = head + (" · " + " · ".join(b for b in bits if b) if bits else "")
        if level >= 2 and n["type"] == "appearance":
            s = w.subjects[n["subject"]]
            first = s["text"].strip().splitlines()[0] if s["text"].strip() else ""
            if first:
                out += f'\n{"":4}> {first[:90]}'
        if level >= 3:
            out += "\n    verbs: " + " ".join(w.verbs_for(nid))
        return out

    def outline(self, root, level=2, deep=False, full=False):
        lines = []
        self._full = full   # :4 shows each thing's text, not only its first line

        def walk(nid, depth, force_open):
            n = self.world.nodes[nid]
            lvl = 2 if (depth == 0 and level >= 2) else 1
            lines.append(("  " * depth) + self.line(nid, lvl).replace("\n", "\n" + "  " * depth))
            if n["type"] == "surface" and n["layout"] == "view":
                if depth == 0 or force_open or deep or nid in self.open:
                    lines.extend(self.view_lines(nid, depth))
                elif self.view_matches(nid):
                    lines[-1] += f"  (open {nid} to see them)"
                return
            if n["type"] == "appearance":
                extra = self.child_extra(nid, depth)
                if extra:
                    lines.append(extra)
            if n["type"] == "surface":
                kids = self.world.children(nid)
                if kids and (force_open or deep or nid in self.open):
                    cap = 16 if deep else None   # a deep look folds a long panel; the fold says how to see the rest
                    folded = [] if deep else self._settled_fold(nid, [k["id"] for k in kids])
                    kids = [k for k in kids if k["id"] not in folded]
                    for k in kids[:cap]:
                        walk(k["id"], depth + 1, False)
                    if folded:
                        lines.append(("  " * (depth + 1)) + f"({len(folded)} settled, not shown: table in:{nid},settled lists them)")
                    if cap and len(kids) > cap:
                        lines.append(("  " * (depth + 1)) + f"(… {len(kids) - cap} more in {nid}; look {nid} :2 lists one line each)")
                elif kids:
                    lines[-1] += f"  (open {nid} to see inside)"

        self._deep = deep   # :3 also shows each thing's first line (child_extra reads this)
        try:
            walk(root, 0, True)
        finally:
            self._deep = False
            self._full = False
        return "\n".join(lines)

    def delta_header(self):
        me = self.world.me
        w = self.world
        # a rule acts as its author (a687): its tripper saw it on their receipt, its author did not
        # a1568: 'mine' is by person once the world has persons, so a renamed person's own acts stay theirs
        evs = [e for e in self.world.events[self.last_event_seen:]
               if (not persons.mine(w, e) and e.get("tripped_by") != me) or rule_did_unseen(e, me)]
        # a3150: the house's record of a knock is no news to anyone: it is there for whoever asks (history, examine)
        evs = [e for e in evs if e["verb"] != "knock"]
        self.last_event_seen = len(self.world.events)
        # a678 (6): walking folds, at most one line per actor, their latest room
        latest = {persons.by(w, e): e for e in evs if e["verb"] == "go"}
        evs = [e for e in evs if e["verb"] != "go" or latest.get(persons.by(w, e)) is e]
        yours, told = self.edits_to_yours(evs)      # a1471: an edit to what you made has its own line, not a count
        import promises     # a3275: the house's `landed` on a promise you hold is said to you in its own sentence
        ended, told2 = promises.landings_told(w, evs)
        yours, told = yours + ended, told | told2
        evs = [e for e in evs if e["id"] not in told]
        yours = "".join(l + "\n" for l in yours)
        if not evs:
            return yours

        def rule_of(e):
            return str(e.get("via") or "").split(" ", 1)[-1] if e.get("tripped_by") else None

        def went(e):
            to = (e.get("args") or {}).get("to")
            return self.world.nodes[to]["title"] if to in self.world.nodes else to

        if len(evs) <= 4:
            def part(e):
                if e["verb"] == "go":
                    return f"{e['id']} {persons.by(w, e)} went to {went(e)}"
                if rule_did_unseen(e, me):
                    args = {k: (v if len(str(v)) <= 60 else str(v)[:57] + "…") for k, v in (e.get("args") or {}).items()}
                    verb = e["verb"]
                    if verb == "edit":       # the log records append/retitle/rewrite as edit; say the verb a person used
                        verb, args = next(((v, {"line" if k == "append" else k: args[k]}) for k, v in
                                           (("append", "append"), ("title", "retitle"), ("text", "rewrite")) if k in args), (verb, args))
                    return (f"{e['id']} your rule {rule_of(e)} did {verb} {e['target']} {self._fmt_args(args)}".rstrip()
                            + f" (tripped by {e['tripped_by']})")
                return f"{e['id']} {e['verb']} {e['target']} by {persons.by(w, e)}" + (f" via rule {rule_of(e)}" if rule_of(e) else "")
            return "!! since your last look: " + "; ".join(part(e) for e in evs) + "\n" + yours
        mine = {e["undo"].get("delete_subject") for e in w.events if persons.mine(w, e) and isinstance(e.get("undo"), dict)} - {None}
        mine |= {e["undo"].get("delete") for e in w.events if persons.mine(w, e) and isinstance(e.get("undo"), dict)} - {None}
        lines, to_me, undone = {}, [], []
        moved = {}
        for e in evs:
            if e["verb"] == "go":
                moved[persons.by(w, e)] = went(e)
                lines.setdefault(persons.by(w, e), {})
                continue
            if e["verb"] == "undo":
                undone.append(e)
            if e["verb"] == "comment" and e["target"] in mine:
                to_me.append(e)
            where = e["target"]
            if where in w.nodes and w.nodes[where]["type"] == "appearance":
                where = w.nodes[where]["parent"]
            name = w.title(w.nodes[where]) if where in w.nodes else (w.subjects[where]["title"] if where in w.subjects else where)
            who = f"your rule {rule_of(e)}" if rule_did_unseen(e, me) else persons.by(w, e)
            lines.setdefault(who, {}).setdefault((e["verb"], name), []).append(e["id"])
        out = [f"!! since your last look: {len(evs)} changes by {', '.join(lines)} ({evs[0]['id']}..{evs[-1]['id']}; history lists them)"]
        for e in to_me:   # never folded: someone answered you
            t = w.subjects[e["target"]]["title"] if e["target"] in w.subjects else e["target"]
            out.append(f"   {persons.by(w, e)} commented on your \"{t}\"  [{e['id']}]")
        for by, groups in lines.items():
            top = sorted(groups.items(), key=lambda kv: -len(kv[1]))[:4]
            out.append(f"   {by}: " + ", ".join(f"{len(ids)} {verb} in {name}" if len(ids) > 1 else f"{verb} in {name}" for (verb, name), ids in top)
                       + (f", +{len(groups) - 4} more kinds" if len(groups) > 4 else "")
                       + ((", now " if groups else "now ") + f"in {moved[by]}" if by in moved else ""))
        return "\n".join(out) + "\n" + yours

    def edits_to_yours(self, evs):
        """a1471 (sketch2, c1439 c1450): a note or task is something its maker stands behind, so when someone else
        changes its text or title the maker hears it in a line of its own: who, which line, the event, and its undo.
        Several edits by one person to one note within an hour are one line with a count. Chats, comments and what the
        maker's own rule did (rule_did_unseen) are not told here: those were already the maker's or the room's.
        -> (lines, ids of the events they tell)."""
        w, me = self.world, self.world.me
        cand = []
        for e in evs:
            if e["verb"] not in ("edit", "check") or e.get("undone") or persons.mine(w, e):
                continue
            sid = e["target"] if e["target"] in w.subjects else (w.nodes.get(e["target"]) or {}).get("subject")
            if sid in w.subjects and w.subjects[sid]["kind"] in ("note", "task"):
                cand.append((e, sid))
        if not cand:
            return [], set()
        want = {sid for _, sid in cand}
        maker = {}
        for e in w.events:
            u = e.get("undo")
            if e["verb"] == "create" and isinstance(u, dict) and u.get("delete_subject") in want:
                maker[u["delete_subject"]] = e
        runs = []          # [(by, sid, [events])], one per person, note and hour
        for e, sid in cand:
            if sid not in maker or not persons.mine(w, maker[sid]):      # a1568: made by me, the person, not the name
                continue
            run = next((r for r in runs if r[0] == persons.by(w, e) and r[1] == sid and _within_hour(r[2][0], e)), None)
            if run:
                run[2].append(e)
            else:
                runs.append((persons.by(w, e), sid, [e]))
        lines, told = [], set()
        for by, sid, run in runs:
            s, last = w.subjects[sid], run[-1]
            aid = last["target"] if last["target"] in w.nodes else next(iter(w.appearances_of(sid)), sid)
            rule = str(last.get("via") or "")
            who = by + (f"'s rule {rule.split(' ', 1)[-1]}" if rule.startswith("rule") else "")
            title = s["title"] if len(s["title"]) <= 60 else s["title"][:57] + "…"
            told |= {e["id"] for e in run}
            if len(run) == 1:
                word, nums, was = self._edit_said(last)
                if was is not None:
                    lines.append(f'~ {who} retitled your {aid} "{title}" (was "{was}"; {last["id"]}; undo {last["id"]})')
                    continue
                prep = {"added": "to", "appended": "to", "removed": "from"}.get(word, "of")
                lines.append(f"~ {who} {word} " + (f"{nums} {prep} " if nums else "") + f'your {aid} "{title}" '
                             f'({last["id"]}; undo {last["id"]})')
                continue
            said = {}
            for e in run:
                word, nums, _ = self._edit_said(e, bare=True)
                said.setdefault(word, set()).update(nums or ())
            what = ", ".join(word + (" " + _numbered("line" if word not in ("checked", "unchecked") else "item", sorted(n))
                                     if n else "") for word, n in said.items())
            lines.append(f'~ {who} edited your {aid} "{title}" {len(run)} times ({what}; {run[0]["id"]}..{last["id"]}; '
                         f'undo {last["id"]} takes back the latest)')
        return lines, told

    def _edit_said(self, e, bare=False):
        """What one edit did, as its maker would want it said -> (word, "line 8" | numbers if bare | None, old title | None)."""
        a = e.get("args") or {}
        import kept
        before = kept.copy_of(e) or {}
        old = str(before.get("text", ""))
        noun = "line"
        if e["verb"] == "check":
            k = str(a.get("item", ""))
            items = self.world.checklist(old)
            try:
                word = "checked" if "- [ ]" in items[int(k) - 1][1] else "unchecked"
            except (ValueError, IndexError):
                word = "checked"
            nums, noun = ([int(k)] if k.isdigit() else []), "item"
        elif "append" in a:
            n = len(old.rstrip("\n").splitlines()) + 1
            word, nums = "appended", list(range(n, n + len(str(a["append"]).splitlines() or [""])))
        elif "text" in a:
            word, nums = _line_change(old, str(a["text"]))
        else:
            return "retitled", None, (None if bare else str(before.get("title", "")))
        if bare:
            return word, nums, None
        return word, (_numbered(noun, nums) if nums else None), None

    # ---- commands ---------------------------------------------------
    def cmd_look(self, target, level):
        rec = self.record_text(target) if target else None
        if rec:
            return rec
        nid = self._resolve(target or "desk")
        header = ""
        if nid in self.world.subjects:
            return header + self.cmd_pivot(nid)
        if level >= 3:
            # look's suffix is containment depth: :3 on a surface walks everything under it, open or not.
            # An appearance has nothing under it, so :3 there is examine (the plain desk keeps its focus form).
            if self.world.nodes[nid]["type"] == "surface":
                return header + self.outline(nid, 2, deep=True, full=level >= 4)
            return header + (self.cmd_examine(nid) if hasattr(self, "cmd_examine") else self.focus(nid))
        if level <= 1:
            return header + self.line(nid, 1)
        return header + self.outline(nid, 2)

    def focus(self, nid):
        w = self.world
        n = w.nodes[nid]
        out = [self.line(nid, 1)]
        if n["type"] == "appearance":
            s = w.subjects[n["subject"]]
            text = s["text"].strip()
            words = text.split()
            if len(words) > 250:
                text = " ".join(words[:250]) + " …(read {} for all)".format(nid)
            out.append("  subject " + s["id"] + (f" tags {','.join(s['tags'])}" if s["tags"] else ""))
            if text:
                out.append("  ---\n  " + text.replace("\n", "\n  ") + "\n  ---")
            out.append("  where: " + self._where_line(nid))
            out.append("  verbs: " + "  ".join(f"{v} {sig}".strip() for v, sig in w.verbs_for(nid).items()))
        else:
            # :3 on a surface: everything under it, whether or not it is open, then its verbs
            out = [self.outline(nid, 2, deep=True)]
            out.append("  verbs: " + " ".join(w.verbs_for(nid)) + f"   (verbs {nid} for argument forms)")
        return "\n".join(out)

    def cmd_fold(self, ident, opening):
        nid = self._resolve(ident, allow_subject=False)
        if self.world.nodes[nid]["type"] != "surface":
            raise Refusal(f"{nid} is not a surface; read {nid} for its content")
        if opening:
            self.open.add(nid)
            # a look walks from the root and only descends into open surfaces, so an open
            # surface inside a closed one would never be reached: open the ancestors too, and say so
            also = []
            p = self.world.nodes[nid]["parent"]
            while p and p != self.world.root:
                if p not in self.open:
                    self.open.add(p)
                    also.append(p)
                p = self.world.nodes[p]["parent"]
            note = ("\n(also opened " + ", ".join(also) + f" so that look reaches {nid})") if also else ""
            return self.outline(nid, 2) + note
        self.open.discard(nid)
        return self.outline(self.world.nodes[nid]["parent"] or nid, 2)

    def cmd_read(self, ident, section=None, full=False, tail=None):
        rec = self.record_text(ident) if ident else None
        if rec:
            return rec
        nid = self._resolve(ident)
        w = self.world
        if nid in w.subjects:
            s = w.subjects[nid]
        elif w.nodes[nid]["type"] == "appearance":
            s = w.subjects[w.nodes[nid]["subject"]]
        else:
            raise Refusal(f"{nid} is a surface; look {nid} :2 shows what is inside")
        apps = w.appearances_of(s["id"])
        head = f"{s['id']} {s['kind']} \"{s['title']}\" · appears at {', '.join(apps)}"
        if s["tags"]:
            head += f" · tags {','.join(s['tags'])}"
        if s.get("due"):
            head += f" · due {s['due']}"
        props = s.get("props") or {}
        if props:        # Astra awareness, Juniper (juniper-8 c): read hid a task's status and awaiting; it prints them, and so has read them
            head += " · " + " ".join(f"{k}={v}" for k, v in persons.shown_props(w, props).items())
        secs = w.sections(s["text"])
        named = [(h, b) for h, b in secs if h]
        body = s["text"]
        whole = None
        if s["kind"] == "chat" and section is None:
            body, whole = self._chat_body(nid, s, full, tail)
            # Juniper (trip D step 11): fold-as-budget is for long texts; a short sectioned plan prints whole, so reading it is reading it
        elif named and section is None and not full and not tail and (len(s["text"].split()) > 300 or s["text"].count("\n") >= 40):   # tail= wants the end of the text, not its outline
            # fold-as-budget for text: the outline of sections, each with its word count
            pre = next((b for h, b in secs if h is None), "")
            lines = ([pre] if pre else []) + [f"## {h}  ({len(b.split())}w)" for h, b in named]
            body = "\n".join(lines) + f"\n(this is the outline, not the text: read {nid} :3 shows all of it, which replacing the text needs; read {nid} #<n> or #<name> for one section)"
        elif named and section is not None:
            pick = None
            if section.isdigit() and 1 <= int(section) <= len(named):
                pick = named[int(section) - 1]
            else:
                pick = next(((h, b) for h, b in named if h.lower() == section.lower()), None)
            if not pick:
                raise Refusal(f"no section {section!r}; sections: " + ", ".join(f"#{i + 1} {h}" for i, (h, _) in enumerate(named)))
            body = f"## {pick[0]}\n{pick[1]}"
        if tail and whole is None:
            bl = body.splitlines()
            if len(bl) > tail:
                cut = bl[:-tail]
                heading = next((l for l in reversed(cut) if l.startswith("## ")), None)   # the section the tail lines belong to
                keep = [heading] if heading else []
                body = "\n".join(keep + [f"(… {len(cut) - len(keep)} earlier line(s) folded; without tail= for all)"] + bl[-tail:])
        if whole is None:              # a section outline, one section or a tail is a partial read: the text is not seen
            whole = body == (self._chat_text_shown(s) if s["kind"] == "chat" else s["text"])
        shown = ["title", "tags", "due", "comments", "links", "prop:*"] + [f"prop:{k}" for k in props] + (["text"] if whole else [])
        self._mark_seen(nid, shown)
        self._mark_seen(s["id"], shown)
        out = f"{head}\n---\n{body}\n---"
        if s.get("comments"):
            out += "\ncomments:"
            for c in s["comments"]:
                out += f"\n  {c['id']} {persons.comment_by(w, c)}: {c['text']}" + (" (resolved" if c["resolved"] else " (open") \
                    + (f", mark={c['mark']})" if c.get("mark") else ")")          # a5007: mark=ask, a question
                if c.get("image"):
                    from image_comments import describe
                    out += "\n      " + describe(c["image"])
                for i, r in enumerate(c["replies"]):
                    out += f"\n      {persons.reply_by(w, c, i)}: {r['text']}" + (f" (mark={r['mark']})" if r.get("mark") else "")
                self._thread_shown(c)          # a5068: this thread is seen up to here
        links = w.links_of(s["id"])
        if links:
            out += "\nlinks:"
            for l in links:
                other = l["to"] if l["from"] == s["id"] else l["from"]
                ot = w.subjects[other]["title"] if other in w.subjects else other
                arrow = f"{l['kind']} →" if l["from"] == s["id"] else f"← {l['kind']} from"
                out += f"\n  {l['id']} {arrow} {other} \"{ot}\""
        return out

    CHAT_FIRST = 10       # lines a first read of a chat shows

    def _chat_body(self, nid, s, full, tail):
        """Sable a744 (talk, 3a): a plain read of a chat prints the lines added since this reader last read it, their own
        included (appending is not reading, a656), under one header; a first read, the last CHAT_FIRST. Each reader keeps
        the run of lines it has been shown, lo..hi, with a digest of lines[:hi], so a rewrite of what was shown starts
        over. The text counts as seen only when the run reaches line 0: folding lines you never saw does not unlock a
        rewrite. :3 and tail= print as before and extend the run. Returns (body, whole) or (text, None) for the old path.
        a951: a run may hold holes, lines inside it a room's look cut or skipped past (_chat_shown); a plain read starts
        at the first."""
        import hashlib
        lines = s["text"].splitlines()
        n = len(lines)
        dig = lambda k: hashlib.sha1("\n".join(lines[:k]).encode()).hexdigest()
        reads = getattr(self, "_chat_reads", None)
        if reads is None:
            reads = self._chat_reads = {}
        obs = self._observer()
        rec = self._chat_run(s)             # None when rewritten since: what you were shown is gone
        shown = self._chat_lines_shown(s)
        if full or tail:
            self._chat_shown(s, 0 if full else max(0, n - tail), ())
            return self._chat_text_shown(s), None
        start =min((rec[1],) + rec[3]) if rec else max(0, n - self.CHAT_FIRST)
        lo = rec[0] if rec else start
        reads[(obs, s["id"])] = (lo, n, dig(n), (), ())
        if rec and start == n:
            return f"(nothing new since you last read; {n} lines; read {nid} :3 or tail=<n>)", lo == 0
        if start == 0:
            return self._chat_text_shown(s), True
        return "\n".join([f"({start} earlier lines folded; read {nid} :3 for all)"] + shown[start:]), lo == 0

    @staticmethod
    def _chat_lines_shown(s):
        """a1581: the chat's text lines as a reader is shown them: a line someone changed ends '(edited, m<n>)', so a
        change to what was said is never silent (examine m<n> keeps its words before). Others are as stored."""
        lines = s["text"].splitlines()
        k = 0
        for l in s.get("lines") or ():
            k += len(l["text"].split("\n"))
            if l.get("edited") and 0 < k <= len(lines):
                lines[k - 1] += f"  (edited, {l['id']})"
        return lines

    def _chat_text_shown(self, s):
        return "\n".join(self._chat_lines_shown(s)) if any(l.get("edited") for l in s.get("lines") or ()) else s["text"]

    def _chat_made(self, cid):
        """a834: whoever makes a chat wrote its first lines, so they start that reader's run (else the maker's first
        append says they have not read it)."""
        import hashlib
        n = self.world.nodes.get(cid)
        s = self.world.subjects.get(n.get("subject") if n else cid)
        if not s or s["kind"] != "chat" or getattr(self, "_in_rules", False):
            return
        lines = s["text"].splitlines()
        if getattr(self, "_chat_reads", None) is None:
            self._chat_reads = {}
        self._chat_reads[(self._observer(), s["id"])] = (0, len(lines), hashlib.sha1("\n".join(lines).encode()).hexdigest(), ())

    def _chat_run(self, s):
        """This reader's run of chat `s` (a744) as (lo, hi, digest of lines[:hi], holes), or None when they have none or
        it was rewritten since. Holes (a951) are lines inside lo..hi that were printed cut, so not read."""
        import hashlib
        lines = s["text"].splitlines()
        obs = self._observer()
        reads = getattr(self, "_chat_reads", None) or {}
        rec = reads.get((obs, s["id"])) or reads.get((obs.split("/")[0], s["id"]))
        if rec and (rec[1] > len(lines) or rec[2] != hashlib.sha1("\n".join(lines[:rec[1]]).encode()).hexdigest()):
            return None
        if not rec:
            return None
        return tuple(rec[:3]) + tuple(tuple(rec[k]) if len(rec) > k else () for k in (3, 4))

    def _chat_shown(self, s, start, cut):
        """Sable a951 (talk, 3a3): a room's look (or a tail= read, with nothing cut) printed lines[start:] of chat `s`,
        the lines in `cut` cut with '…'. They extend this reader's run, except that a cut line is not read: it is a hole
        in the run, which the receipt counts and a plain read shows again, unless the run already held it whole.
        a986 (3a4): lines between the end of the run and `start` are holes too, never shown at all (the run's fifth
        field, which the receipt counts as unseen), so a plain read starts at them instead of skipping past; nothing
        is ever skipped. Only with no run (or one rewritten since) does the run start over at `start`.
        -> True when the run now holds the whole text (it counts as seen)."""
        import hashlib
        lines = s["text"].splitlines()
        n = len(lines)
        rec = self._chat_run(s)
        if start < n or start == 0:
            if rec:
                gap = set(range(rec[1], start))
                lo = min(start, rec[0])
                holes = {h for h in rec[3] if h < start} | {c for c in cut if not rec[0] <= c < rec[1] or c in rec[3]} | gap
                unseen = {h for h in rec[4] if h < start} | gap
            else:
                lo, holes, unseen = start, set(cut), set()
            if getattr(self, "_chat_reads", None) is None:
                self._chat_reads = {}
            rec = self._chat_reads[(self._observer(), s["id"])] = (lo, n, hashlib.sha1("\n".join(lines).encode()).hexdigest(),
                                                                   tuple(sorted(holes)), tuple(sorted(unseen)))
        return bool(rec) and rec[0] == 0 and rec[1] >= n and not rec[3]

    def _chat_behind(self, nid):
        """Sable a834: what an append's receipt says about the lines this reader has not been shown, or "". Counts only
        lines by others added after the end of this reader's run (a744): your own never count, and lines a first read
        folded were there when you read and the read said so. A chat you have no read of, or one rewritten since, says
        so instead of counting; a receipt is testimony, and one that cries wolf stops being read."""
        import hashlib
        w = self.world
        n = w.nodes.get(nid)
        s = w.subjects.get(n.get("subject") if n else nid)
        if not s or s["kind"] != "chat":
            return ""
        lines = s["text"].splitlines()
        obs = self._observer()
        reads = getattr(self, "_chat_reads", None) or {}
        if (reads.get((obs, s["id"])) or reads.get((obs.split("/")[0], s["id"]))) is None:
            return f"you haven't read this chat; read {nid} to see it"
        rec = self._chat_run(s)
        if rec is None:
            return f"this chat was rewritten since you last read it; read {nid} to see it"
        me = w.display_name(w.me).casefold()
        who, count, part = None, 0, 0
        for k, l in enumerate(lines):
            said = w.SPEAKER.match(l)
            if said:
                who = said.group(1).casefold()     # an unsigned line goes with the line above it (a multi-line append)
            if l.strip() and who != me:
                count += k >= rec[1] or k in rec[4]      # a986: a hole never shown at all is simply unseen
                part += k in rec[3] and k not in rec[4]  # a951: shown cut by a room's look, so not read; said as such
        if not count and not part:
            return ""
        bits = ([f"{count} line{'s' if count > 1 else ''} from others you haven't seen"] if count else []) + (
            [f"{part} line{'s' if part > 1 else ''} from others you were shown cut"] if part else [])
        return "; ".join(bits) + f"; read {nid}"

    # ---- a5068: an agent's line waits if the thread moved -------------------------------------------------------
    # Alex, 14 Oct (a4708, e9790): 'when someone sends a message under you, you get that as a response before your
    # tool call to send a message goes out. that way you never send and then have to send again.' A chat line or a
    # reply under a comment carries what its sender had seen there; a line by someone else added since holds it, the
    # receipt prints those lines whole, and the same line sent again goes as written (they are shown now). A person at
    # a window is never held (their painter shows lines as they arrive), nor is a rule, nor the house.
    HOLD_SHOWN = 10       # lines a hold prints whole at most; the earlier are counted and named

    def _never_held(self):
        w = self.world
        me = str(w.me or "").split("/")[0].lower()
        if getattr(self, "_in_rules", False) or not me or me == "house" or getattr(w, "through_gate", None):
            return True
        import persons
        import rooms
        pid = persons.today(w, me) if persons.on(w) else None
        if pid and ((w.subjects.get(pid) or {}).get("props") or {}).get("kind") == "human":
            return True
        return rooms.kind_of(w, me) == "person"

    def _turn_at(self):
        """A resident's view is fixed at the start of its turn (a2870 Revision 2): the house says where (as_of, the
        event count its news had reached when this turn's input was sent). None for anyone else, or when not said."""
        at = getattr(self, "_as_of", None)
        if at is None:
            return None
        import rooms
        return int(at) if rooms.kind_of(self.world, str(self.world.me).split("/")[0]) == "resident" else None

    def _before_turn(self, e, at):
        """Did event `e` come before the turn began at event count `at`? Event numbers rise and are never issued
        again, so it is the number of the last event the turn's input had reached that decides."""
        w = self.world
        last = w.events[min(at, len(w.events)) - 1]["id"] if at > 0 and w.events else "e0"
        return int(e["id"][1:]) <= int(last[1:])

    def _thread_seen(self, cid):
        recs = getattr(self, "_thread_reads", None) or {}
        obs = self._observer()
        return recs.get((obs, cid), recs.get((obs.split("/")[0], cid)))

    def _thread_shown(self, c):
        """A print of comment `c` with its replies whole (read, examine c<n>): this reader has seen the thread up to
        its latest message, by event number (an event number is never issued again)."""
        if getattr(self, "_receipt", False):
            return
        import persons
        import rooms
        w = self.world
        evs = [persons.comment_events(w).get(c["id"])] + list(rooms.reply_events(w).get(c["id"], []))
        top = max((int(e["id"][1:]) for e in evs if e), default=0)
        if getattr(self, "_thread_reads", None) is None:
            self._thread_reads = {}
        key = (self._observer(), c["id"])
        self._thread_reads[key] = max(top, self._thread_reads.get(key) or 0)

    def _hold_line(self, nid, verb, kv):
        """a5068: refuse (hold) an agent's chat line or thread reply when someone else has spoken there since what it
        had seen, printing what they said; marks it shown, so the same line sent again goes through."""
        if getattr(self, "_in_rules", False):
            return
        if self._adds_line(nid, verb, kv):
            said = self._chat_moved(nid, kv)
        elif verb == "comment" and str((kv or {}).get("id", "")).strip():
            said = self._thread_moved(str(kv["id"]).strip())
        else:
            return
        if said:
            raise Refusal(said)

    def _chat_moved(self, nid, kv):
        import hashlib
        import rooms
        w = self.world
        n = w.nodes.get(nid)
        s = w.subjects.get(n.get("subject") if n else nid)
        if not s or s["kind"] != "chat" or s.get("lines") is None:
            return ""             # a chat whose lines are not things (none live today) keeps the old rule
        at = self._turn_at()
        if at is None:
            obs, reads = self._observer(), getattr(self, "_chat_reads", None) or {}
            raw = reads.get((obs, s["id"])) or reads.get((obs.split("/")[0], s["id"]))
            if raw is None or raw[1] >= s["text"].count("\n") + 1:
                return ""         # no read, or a run to the end (rewritten or not, nothing is new): no digest needed
        text_lines = s["text"].splitlines()
        rec = self._chat_run(s)
        me = str(w.me).split("/")[0]
        if at is None and (rec is None or rec[1] >= len(text_lines)):
            # the run reaches the end: nothing new to this reader (the common case, and cheap). With no read at all
            # there is no view to be behind: the line goes, and its receipt says the chat is unread (a834)
            return ""
        reply =str((kv or {}).get("reply_to", "")).strip()
        rk = next((k for k, l in enumerate(s["lines"]) if l["id"] == reply), None) if reply else None
        corner = rooms.corner_of(w, me) if at is not None else None
        mine = corner is not None and any(a["type"] == "appearance" and a.get("subject") == s["id"]
                                           and rooms._within(w, a, corner) for a in w.nodes.values())
        member = at is not None and (mine or rooms.member(w, s, me))
        new, k = [], 0
        for i, l in enumerate(s["lines"]):
            start, k = k, k + len(l["text"].split("\n"))
            e = w.event_by_id(l.get("ev"))
            by = str((e or {}).get("by") or "").split("/")[0]
            if not e or not by or by == "house" or rooms.same_person(w, by, me):
                continue
            if rk is not None and i <= rk:
                continue          # the line you answer you were shown, and what came before it was there
            # a line inside the run was there when you read, even one a look skipped past or cut (a951, a986): the
            # receipt still counts those. Only a line added after your read is new to your view, and waits
            ran = rec is None or start < rec[1]
            if at is None:
                if ran:
                    continue
            else:
                if self._before_turn(e, at) and (ran or member or rooms.calls(w, s, rooms.line_to(e)[0], me)):
                    continue      # a resident was shown it before this turn: read, or told by the house
            new.append((l, e))
        if not new or self._never_held():     # asked last: it walks the world's surfaces, and most lines need none of it
            return ""
        # shown now: the run reaches the end, so the same line sent again is judged on what came after this
        if getattr(self, "_chat_reads", None) is None:
            self._chat_reads = {}
        self._chat_reads[(self._observer(), s["id"])] = (rec[0] if rec else 0, len(text_lines),
                                                         hashlib.sha1("\n".join(text_lines).encode()).hexdigest(),
                                                         tuple(rec[3]) if rec else (), tuple(rec[4]) if rec else ())
        return self._held_words(nid, f"in chat \"{s['title']}\" ({nid})", [
            (l["id"], e, l["text"]) for l, e in new], "line")

    def _thread_moved(self, cid):
        import persons
        import rooms
        w = self.world
        owner, c = w.find_comment(cid)
        if c is None:
            return ""             # the world says what is wrong with the id
        me = str(w.me).split("/")[0]
        seen = self._thread_seen(cid)
        at = self._turn_at()
        if seen is None and at is None:
            return ""             # never shown this thread: no view to be behind, as with a chat never read
        opening = persons.comment_events(w).get(cid)
        base = seen if seen is not None else (int(opening["id"][1:]) if opening else 0)   # you name the comment you answer
        evs =rooms.reply_events(w).get(cid, [])
        new = []
        for r, e in zip(c.get("replies") or [], evs):
            by = str(e.get("by") or "").split("/")[0]
            if not by or by == "house" or rooms.same_person(w, by, me):
                continue
            num = int(e["id"][1:])
            if at is None:
                if num <= base:
                    continue
            else:
                told = any(rooms.same_person(w, x, me) for x in
                           (rooms.named_to(e) if rooms.builder_quiet(w, e, owner) else rooms.comment_to(e)))
                if self._before_turn(e, at) and (num <= base or told):
                    continue
            new.append((f"reply under {cid},", e, r["text"]))
        if not new or self._never_held():
            return ""
        if getattr(self, "_thread_reads", None) is None:
            self._thread_reads = {}
        self._thread_reads[(self._observer(), cid)] = max([int(e["id"][1:]) for _, e, _ in new] + [base])
        where = next(iter(w.appearances_of(owner["id"])), owner["id"])
        return self._held_words(where, f"in the thread under {cid} on \"{owner['title']}\" ({where})", new, "reply")

    def _held_words(self, nid, where, new, what):
        """The hold's receipt, written for a resident reading it cold: what waits, what was said, what to do next."""
        import persons
        w = self.world
        many = len(new) > 1
        out = [f"held, not sent: {len(new)} new {what}{'s' if many else ''} by others {where} since you last saw it. "
               f"Your {'line' if what == 'line' else 'reply'} was not added. {'They say' if many else 'It says'}:"]
        if len(new) > self.HOLD_SHOWN:
            out.append(f"  ({len(new) - self.HOLD_SHOWN} earlier not printed here; read {nid} shows them)")
        for ident, e, text in new[-self.HOLD_SHOWN:]:
            out.append(f"  {ident} {persons.by(w, e)} ({e['id']}): " + str(text).replace("\n", "\n    "))
        out.append("To send yours as written, send the same command again: you have been shown these now, so it goes "
                   "through. To answer them instead, change it; a changed line is judged afresh, on what is said after this.")
        return "\n".join(out)

    def _chat_waits(self, nid, kv):
        """a1062, a1566: what a chat line's receipt says about whom it took and what happened to each (rooms)."""
        import rooms
        text = str((kv or {}).get("line", (kv or {}).get("append", "")))
        try:
            return rooms.waiting_note(self, nid, text)
        except Exception as e:      # a receipt's aside must never cost the line that already landed
            return f"(who this line reaches could not be told: {type(e).__name__})"

    def _written_calls(self, eids):
        """a2733: what a comment's or note edit's receipt says about whom its words call, as a line's does: 'to: pike',
        or 'to: nobody', and the mid-line @s it only mentions (world.written, the house's own reading). "" when what it
        wrote has no @ to speak of, or when it made a chat line (that line's receipt says its address)."""
        import rooms
        from world import MENTION_NOTE, to_names, written
        w = self.world
        calls, heard, directed = [], [], False
        for e in (x for x in w.events if x["id"] in set(eids)):
            c, m = written(e)
            args = e.get("args") or {}
            if e.get("verb") == "comment":
                if "to" in args:
                    c, m, directed = to_names(args["to"]), [], True
                elif args.get("id"):
                    c, directed = rooms.comment_to(e), True
                c = [n for n in c if not rooms.same_person(w, n, str(e.get("by", "")).split("/")[0])]
            calls += [n for n in c if n not in calls]
            heard += [n for n in m if n not in heard]
        heard = [n for n in heard if n not in calls]
        if not calls and not heard and not directed:
            return ""
        everyone = [n for n in calls if n in rooms.EVERYONE]
        no_one = [n for n in calls if n not in everyone and not rooms.someone(w, n)]
        to = [n for n in calls if n not in everyone and n not in no_one]
        out = "to: " + (", ".join(to) or "nobody") + ("; " + MENTION_NOTE.format(", ".join("@" + n for n in heard)) if heard else "")
        if everyone:
            out += f"\n  @{everyone[0]}: reaches no one outside a chat line (a916); a chat line is the place for it"
        for n in no_one:
            out += f"\n  {n}: no one by that name"
        return out

    def _where_line(self, nid):
        w = self.world
        n = w.nodes[nid]
        x, y, wd, h = w.abs_rect(nid)
        parent = n["parent"]
        pl = w.nodes[parent]["layout"] if parent else "-"
        rel = w.relations(nid)
        s = f"screen {x},{y} {wd}x{h} · in {parent or '-'} ({pl})"
        if parent:
            s += f" local {n['x']},{n['y']} z{n['z']}"
        if rel:
            s += " · " + ", ".join(rel)
        hid = w.hidden_fraction(nid)
        if hid:
            s += f" · {int(hid * 100)}% hidden"
        if not rel and not hid:
            s += " · clear"
        return s

    def cmd_where(self, ident):
        nid = self._resolve(ident, allow_subject=False)
        self._mark_seen(nid, ["place"])
        return f"{nid}: " + self._where_line(nid)

    def cmd_verbs(self, ident):
        nid = self._resolve(ident)
        self._mark_seen(nid, [])          # verbs show what can be done, no value
        v = self.world.verbs_for(nid)
        return f"{nid} verbs:\n" + "\n".join(f"  {k} {sig}".rstrip() for k, sig in v.items())

    def cmd_pivot(self, ident):
        rec = self.record_text(ident) if ident else None
        if rec:
            return rec
        nid = self._resolve(ident)
        w = self.world
        if persons.is_person(w, nid):
            note, self._person_note = getattr(self, "_person_note", ""), ""
            return persons.card(w, nid, note)
        if nid in w.subjects:
            sid = nid
        elif w.nodes[nid]["type"] == "appearance":
            sid = w.nodes[nid]["subject"]
        else:
            n = w.nodes[nid]
            return f"{nid} is a surface in {n['parent'] or '-'}; surfaces have no subject"
        s = w.subjects[sid]
        self._mark_seen(sid)
        out = [f"{sid} {s['kind']} \"{s['title']}\" · {len(s['text'].split())}w" + (f" · tags {','.join(s['tags'])}" if s["tags"] else "")]
        for a in w.appearances_of(sid):
            n = w.nodes[a]
            out.append(f"  {self.line(a, 1)}  in {n['parent']} \"{w.title(w.nodes[n['parent']])}\"")
        out.append(self.subject_verbs_line(sid))
        return "\n".join(out)

    def subject_verbs_line(self, sid):
        """The verbs a subject answers to. The plain desk uses the world's table; verb-registry desks override."""
        return "  verbs: " + "  ".join(f"{v} {sig}".strip() for v, sig in self.world.verbs_for(sid).items())

    def cmd_find(self, words):
        q = words.lower().strip()
        if not q:
            raise Refusal("find needs words")
        w = self.world
        hits = []
        scored = []
        for s in w.subjects.values():
            hay = (s["title"] + " " + s["text"] + " " + " ".join(s["tags"])).lower()
            if all(t in hay for t in q.split()):
                # things named by the words come before things that merely mention them (Terra's friction note)
                rank = 0 if all(t in s["title"].lower() for t in q.split()) else 1 if all(t in " ".join(s["tags"]).lower() for t in q.split()) else 2
                scored.append((rank, s))
        for _, s in sorted(scored, key=lambda x: x[0]):
            apps = w.appearances_of(s["id"])
            for a in apps:
                hits.append(f"  {self.line(a, 1)}  in {w.nodes[a]['parent']}")
            if not apps:
                hits.append(f"  {s['id']} {s['kind']} \"{s['title']}\" (not on the desk)")
        for n in w.nodes.values():
            if n["type"] == "surface" and q in n["title"].lower():
                hits.append(f"  {self.line(n['id'], 1)}")
        return f"find {words!r}: {len(hits)} hit(s)\n" + "\n".join(hits) if hits else f"find {words!r}: nothing"

    def cmd_history(self, ident):
        evs = self.world.events
        if ident and self._record(ident):
            evs = self._record_events(ident)          # a1308: history takes back the ids it prints
        elif ident:
            try:
                nid = self._resolve(ident)
            except Refusal:
                nid = ident.strip().lstrip("@")       # a thing no longer here still has its history
                if not any(e["target"] == nid for e in evs):
                    raise
            if persons.is_person(self.world, nid):
                # a1568: a person's history is what they did (who=), and what was done to them (made, renamed)
                note, self._person_note = getattr(self, "_person_note", ""), ""
                evs = [e for e in evs if e.get("who") == nid or e["target"] == nid]
                head = (f"history of {persons.label(self.world, nid)} ({nid}): " + (f"the latest 12 of {len(evs)} events"
                        if len(evs) > 12 else f"{len(evs)} event(s)") + (f"; {note}" if note else ""))
                return "\n".join([head] + [self._history_line(e) for e in evs[-12:]])
            # a3150: a corner's history lists the knocks the house recorded for its resident
            evs =[e for e in evs if e["target"] == nid or nid in (e.get("args") or {}).values()
                  or nid in (e.get("knocked") or ())]
        evs = evs[-12:]
        if not evs:
            return "no events yet"
        return "\n".join(self._history_line(e) for e in evs)

    def _history_line(self, e):
        return (f"{e['id']} {e['verb']} {e['target']} {self._fmt_args(e['args'])} by {persons.by(self.world, e)}"
                + (f" via {e['via']}" if e.get("via") and e["via"] != e["verb"] else "")
                + (f" (verb {e['verb_run']})" if e.get("verb_run") else "") + (" (undone)" if e.get("undone") else ""))

    # ---- a1308: the ids the house prints that name no thing: events, comments, links ------------------------------
    def _record(self, ident):
        """-> (kind, the record or None, the event that made or removed it or None) for an e/c/l id this world has
        printed, or None. A comment or link that was undone or unlinked is still known, by the event that took it away."""
        m = RECORD_ID.match(str(ident or "").strip().lstrip("@"))
        if not m:
            return None
        w, rid, kind = self.world, m.group(0), m.group(1)
        if kind == "e":
            ev = next((e for e in reversed(w.events) if e["id"] == rid), None)
            return ("e", ev, ev) if ev else None
        if kind == "c":
            owner, c = w.find_comment(rid)
            made = next((e for e in w.events if (e.get("undo") or {}).get("drop_comment") == rid), None)
            if c is not None:
                return "c", (owner, c), made
            return ("c", None, made) if made else None
        if kind == "m":
            # a1581: a chat line; one that is gone (its append undone) is still known by the event that made it
            chat, line = w.find_line(rid)
            if line is not None:
                return "m", (chat, line), w.event_by_id(line.get("ev"))
            made = next((e for e in reversed(w.events) if (e.get("args") or {}).get("line_id") == rid), None)
            return ("m", None, made) if made else None
        link =next((l for l in w.links if l["id"] == rid), None)
        made = next((e for e in w.events if (e.get("undo") or {}).get("drop_link") == rid), None)
        if link is not None:
            return "l", link, made
        gone = next((e for e in reversed(w.events) if ((e.get("undo") or {}).get("restore_link") or {}).get("id") == rid), None)
        return ("l", None, gone or made) if (gone or made) else None

    def _record_events(self, ident):
        """The events about an e/c/l id: an event with what it caused and its undo; a comment's or link's making,
        closing and removal."""
        w, rid = self.world, ident.strip().lstrip("@")
        if rid.startswith("e"):
            return [e for e in w.events if e["id"] == rid or e.get("cause") == rid
                    or (e["verb"] == "undo" and e["target"] == rid)]
        if rid.startswith("m"):
            # a1581: the line's making, every edit of it, and the event that made old lines things
            chat, line = w.find_line(rid)
            own = {line.get("ev"), line.get("edited")} | {x.get("ev") for x in line.get("was") or ()} if line else set()
            own |= {e["id"] for e in w.events if (e.get("args") or {}).get("line_id") == rid}
            ids = own - {None}
            return [e for e in w.events if e["id"] in ids or (e["verb"] == "undo" and e["target"] in ids)
                    or (e["verb"] == "knock" and e.get("cause") in ids)      # a3150: whom the line knocked
                    or (chat is not None and e["verb"] == "lines" and chat["id"] in (e.get("changed") or ()))]
        mine, ids = [], set()
        for e in w.events:
            u, a = e.get("undo") or {}, e.get("args") or {}
            if (rid in (u.get("drop_comment"), u.get("reopen"), u.get("drop_link")) or a.get("id") == rid
                    or (u.get("restore_link") or {}).get("id") == rid or (e["verb"] == "undo" and e["target"] in ids)):
                mine.append(e)
                ids.add(e["id"])
        return mine

    def _title_line(self, ident):
        """`a12 note "Title"` for any node or subject id, or the id alone when it is gone."""
        w = self.world
        if ident in w.nodes:
            n = w.nodes[ident]
            return f"{ident} {w.subjects[n['subject']]['kind'] if n.get('subject') else 'surface'} \"{w.title(n)}\""
        if ident in w.subjects:
            s = w.subjects[ident]
            apps = w.appearances_of(ident)
            return f"{ident} {s['kind']} \"{s['title']}\"" + (f" (at {', '.join(apps)})" if apps else " (on no surface)")
        return f"{ident} (no longer here)"

    def record_text(self, ident):
        """a1308: what look, read and examine of an event, comment or link id print, or None for any other id.
        An event: the line history prints for it, then when, on what, why, what it caused and how to take it back."""
        rec = self._record(ident)
        if not rec:
            return None
        kind, obj, ev = rec
        w = self.world
        rid = ident.strip().lstrip("@")
        out = []
        if kind == "e":
            e = obj
            out.append(self._history_line(e))
            out.append(f"  an event: {persons.by(w, e)} did {e['verb']}" + (f" at {str(e.get('at'))[:16].replace('T', ' ')}"
                                                                  if e.get("at") else "") + f", on {self._title_line(e['target'])}")
            if persons.of_event(w, e):
                # a1568: the person, and the name the act was signed with when it differs from how they are printed now
                pid = e["who"]
                out.append(f"  by the person {pid} (examine {pid})" + (f"; signed {e['by']}" if persons.label(w, pid) != e["by"] else ""))
            for k, v in (e.get("args") or {}).items():
                v = str(v)
                out.append(f"    {k}: " + (v if len(v) <= 400 else v[:400] + f"… ({len(v.split())} words; read {e['target']})"))
            if e.get("tripped_by") and e["tripped_by"] != e["by"]:
                out.append(f"  tripped by {persons.tripped(w, e)} (a rule acting as {persons.by(w, e)})")
            if e.get("cause"):
                out.append(f"  because of {e['cause']} (examine {e['cause']})")
            out += self._knock_lines(rid)
            caused = [x["id"] for x in w.events if x.get("cause") == rid]
            if caused:
                out.append("  it caused: " + " ".join(caused[:12]) + (f" (+{len(caused) - 12})" if len(caused) > 12 else ""))
            changed = [c for c in (e.get("changed") or []) if c != e["target"]]
            if changed:
                out.append("  it also changed: " + " ".join(changed[:12]))
            if e.get("undone"):
                out.append("  undone since (history " + rid + " shows the undo)")
            elif e["verb"] != "undo":
                out.append(f"  undo {rid} takes it back; history {rid} lists it with what it caused")
            return "\n".join(out)
        if kind == "c":
            if obj is None:
                return (f"{rid}: a comment that is no longer here; it was made by {ev['id']} ({persons.by(w, ev)} on "
                        f"{self._title_line(ev['target'])}), then undone. history {rid} shows both")
            owner, c = obj
            out.append(f"{rid} comment by {persons.comment_by(w, c, ev)} on {self._title_line(owner['id'])} · "
                       + ("resolved" if c["resolved"] else "open") + (f" · mark={c['mark']}" if c.get("mark") else ""))
            out.append("  " + c["text"].replace("\n", "\n  "))
            if c.get("image"):
                from image_comments import describe
                out.append("  " + describe(c["image"]))
            for i, r in enumerate(c.get("replies") or []):
                out.append(f"    {persons.reply_by(w, c, i)}: {r['text']}")
            self._thread_shown(c)              # a5068: this thread is seen up to here
            if ev:
                out.append(f"  made by {ev['id']}" + (f" at {str(ev.get('at'))[:16].replace('T', ' ')}" if ev.get("at") else ""))
            out.append(f"  read {(w.appearances_of(owner['id']) or [owner['id']])[0]} shows every comment on it"
                       + ("" if c["resolved"] else f"; do resolve {rid} line=\"...\" answers and closes it"))
            return "\n".join(out)
        if kind == "m":
            return self._line_text(rid, obj, ev)
        if obj is None:
            return (f"{rid}: a link that is no longer here (" + (f"{ev['verb']} {ev['id']} by {persons.by(w, ev)}" if ev else "?")
                    + f"). history {rid} shows what happened to it")
        out.append(f"{rid} link: {self._title_line(obj['from'])} {obj['kind']} → {self._title_line(obj['to'])}")
        if ev:
            out.append(f"  made by {ev['id']} ({persons.by(w, ev)}" + (f", {str(ev.get('at'))[:16].replace('T', ' ')}" if ev.get("at") else "") + ")")
        end = (w.appearances_of(obj["from"]) or [obj["from"]])[0]
        out.append(f"  do unlink {end} id={rid} removes it; find links:{end} lists what {end} is linked to")
        return "\n".join(out)

    def _line_text(self, rid, obj, ev):
        """a1581: what examine, read and look print for a chat line: its chat, by and at (read from the event that made
        it, or 'by unknown, at unknown'), who it addresses, its words, and, if it was changed, every earlier wording."""
        w = self.world
        when = lambda e: str(e.get("at"))[:16].replace("T", " ") if e and e.get("at") else "unknown"     # noqa: E731
        if obj is None:
            return (f"{rid}: a chat line that is no longer here; it was made by {ev['id']} ({persons.by(w, ev)} on "
                    f"{self._title_line(ev['target'])}), then undone. history {rid} shows both")
        chat, line = obj
        apps = w.appearances_of(chat["id"])
        by = f"by {persons.by(w, ev)} · at {when(ev)}" if ev else "by unknown, at unknown"    # a1568: the event's person
        out = [f"{rid} a chat line in \"{chat['title']}\" ({chat['id']}" + (f", at {apps[0]}" if apps else "") + f") · {by}"
               f" · to: {', '.join(line.get('to') or []) or 'nobody'}" + (" · edited" if line.get("edited") else "")]
        out.append("  " + line["text"].replace("\n", "\n  "))
        if ev:
            out.append(f"  made by {ev['id']} ({ev['verb'] if ev['verb'] != 'edit' else 'append'})"
                       + (f", from press {line['intent']}" if line.get("intent") else ""))
        else:
            out.append("  no event that made it could be found, so who said it and when are not known (a1581 kept it as it was)")
        if ev:
            out += self._knock_lines(ev["id"])
        if line.get("reply_to"):
            out.append(f"  in reply to {line['reply_to']} (examine {line['reply_to']})")
        if line.get("was"):
            e2 = w.event_by_id(line.get("edited"))
            out.append(f"  edited by {persons.by(w, e2) if e2 else 'unknown'} at {when(e2)} ({line.get('edited')}); its words before, oldest first:")
            for x in line["was"]:
                out.append(f"    ({x.get('ev') or 'unknown'}) " + x["text"].replace("\n", "\n    "))
        out.append(f"  read {apps[0] if apps else chat['id']} shows the chat; history {rid} lists what happened to this line")
        return "\n".join(out)

    def _knock_lines(self, eid):
        """a3150: what the house recorded about whom the line made by event `eid` knocked: one line, or none."""
        import rooms
        import listeners
        k = rooms.knock_of(self.world, eid)
        if k is None:
            return []
        session = getattr(self, "_session", "") or ""

        def told(a, v):
            # a5267: a listener that carried the call says so in its witnessed row, while it runs; not in the world
            if not str(v).startswith(listeners.KNOCKED):
                return ""
            return "; it says delivered" if listeners.delivered(session, a, eid) else ""
        return [f"  knock ({k['id']}, the house's record): " + "; ".join(
            f"{self.world.display_name(a)}: {v}{told(a, v)}" for a, v in (k.get("args") or {}).items() if a != "line")]

    def _fmt_args(self, args):
        def one(k, v):
            v = str(persons.shown(self.world, v))      # a1590: a person id prints as the person's name
            if len(v) > 200:     # Moss: the receipt echoed the whole document back. Say its size; `read` has the rest.
                return f"{k}=<{len(v.split())} words, {len(v.splitlines())} lines, begins {v[:40]!r}>"
            return f"{k}={v!r}" if " " in v else f"{k}={v}"
        return " ".join(one(k, v) for k, v in (args or {}).items())

    def cmd_undo(self, eid):
        if not eid:
            mine = [e for e in self.world.events if persons.mine(self.world, e) and e["verb"] != "undo" and not e.get("undone")
                    and not rule_did_unseen(e, self.world.me)   # a687: your rule's firing, tripped by another, undoes their command
                    and not (e.get("undo") or {}).get("refuse")]   # a678: walking is not a change; bare undo passes over it
            if not mine:
                raise Refusal("nothing of yours to undo")
            eid = mine[-1]["id"]   # bare undo: your latest change
        ev = next((e for e in self.world.events if e["id"] == eid), None)
        if ev is None:
            raise Refusal(f"no event {eid}")
        if ev.get("cause"):
            # a rule's consequence: undo the command that caused it, and everything it caused
            eid = ev["cause"]
            ev = next(e for e in self.world.events if e["id"] == eid)
        # 7 Oct: in a world with a log, a command is put back whole by the facts its record holds (store.undo_plan):
        # one way for every verb, judged fact by fact, so an old change comes back when nothing changed the same
        # facts since. A world without a log, and the one-time migrations, go the verbs' own way below.
        back = self._undo_record(ev)
        if back:
            return back
        group = [ev]
        if ev.get("verb_use"):
            # a world verb's use is undone whole, all its steps (each step was its own command)
            group = [e for e in self.world.events if e.get("verb_use") == ev["verb_use"] and not e.get("undone")]
        elif ev.get("via"):
            # a composed verb (sort, move <selection>, group ...) is undone as a whole: its contiguous steps,
            # on both sides of the named one
            evs = self.world.events
            at = evs.index(ev)
            same = lambda e: (e.get("via") == ev["via"] and e.get("cmd") == ev.get("cmd") and not e.get("undone")
                              and e["by"] == ev["by"] and not e.get("cause"))
            j = at - 1
            while j >= 0 and same(evs[j]):
                group.insert(0, evs[j])
                j -= 1
            j = at + 1
            while j < len(evs) and same(evs[j]):
                group.append(evs[j])
                j += 1
        caused = [e for e in self.world.events if e.get("cause") in {g["id"] for g in group} and not e.get("undone")]
        group = sorted(group + caused, key=lambda e: int(e["id"][1:]))
        done = []
        revs0 = {k: v["rev"] for k, v in list(self.world.nodes.items()) + list(self.world.subjects.items())}
        for e in reversed(group):
            r = self.world.undo(e["id"])
            done.append(e["id"])
        for k, v in list(self.world.nodes.items()) + list(self.world.subjects.items()):
            if revs0.get(k) != v["rev"]:
                self._mark_seen(k)   # an undo is your own change; what it touched stays seen
        self._after_mutation()
        if len(done) > 1:
            what = (f"{len(done)} steps of the verb {ev.get('verb_run')}" if ev.get("verb_use")
                    else f"{len(done) - len(caused)} steps of {ev['via']}" if ev.get("via") and len(done) - len(caused) > 1
                    else f"{eid}")
            if caused:
                what += f", and {len(caused)} rule consequence(s): " + ", ".join(sorted({c.get('via', 'rule')[5:] for c in caused}))
            return f"ok {r['event']}: reverted {done[-1]}..{done[0]} ({what})"
        # Jeff lost a lens to this: a refused command, then a bare undo, which reverted something minutes older and said only its number
        said = f"{ev['verb']} {ev['target']}" + (f" {self._fmt_args(ev.get('args'))}" if ev.get("args") else "")
        return f"ok {r['event']}: reverted {eid}, which was: {said[:160]}" + (f"  (made {ev['at'][11:16]})" if ev.get("at") else "")

    def _merge_text(self, nid, verb, kv):
        """7 Oct: someone changed this text since I read it, and I am changing it too. In a world with a log, what I
        read is known (store.text_at_event), so the two changes can be compared line by line: when they touch
        different lines, mine goes into the text as it is now and nothing of theirs is lost. -> (verb, kv, note) to act
        with, or (None, None, why) when it cannot be done (the same lines; no log; read before the log began)."""
        ctx = getattr(self, "_store", None)
        if ctx is None or verb not in ("rewrite", "replace"):
            return None, None, ""
        import store
        w = self.world
        n = w.nodes.get(nid)
        sid = n.get("subject") if n else nid
        s = w.subjects.get(sid)
        if s is None or s.get("lines") is not None:
            return None, None, ""
        seen = self._seen_index(nid)
        base = store.text_at_event(ctx.log, w, sid, max(seen.get("text", 0), seen.get("*", 0)))
        if base is None:
            return None, None, ""
        theirs = s.get("text") or ""
        if verb == "replace":
            old = kv.get("old")
            if not old or base.count(old) != 1:
                return None, None, ""
            mine = base.replace(old, kv.get("new", ""), 1)
        else:
            mine = kv.get("text")
            if mine is None:
                return None, None, ""
        merged, clash = store.merge3(base, theirs, mine)
        if merged is None:
            return None, None, f"; you and they both changed {clash}"
        import kinds
        if kinds.is_lens(s):
            import lens_ir
            good = getattr(self, "_lens_good", None)
            kept = dict(good) if good is not None else None
            try:          # asked of a text not saved yet: the last-good record must not learn it
                broke = lens_ir.check(self, s)[0] and not lens_ir.check(self, dict(s, text=merged))[0]
            finally:
                if kept is not None:
                    self._lens_good = kept
            if broke:
                return None, None, "; your change and theirs are on different lines, but together the lens does not compile"
        d_theirs, d_mine = _line_change(base, theirs), _line_change(theirs, merged)
        said = lambda d: (f"{d[0]} {_numbered('line', d[1])}" if d[1] else d[0])     # noqa: E731
        # Juniper and Sable, 7 Oct (a3474): 'theirs' named neither who nor which event; and a text that joined is not
        # a lens that still means what each intended, which the receipt can say though it cannot check
        since = max(seen.get("text", 0), seen.get("*", 0))
        them = [e for e in w.events[since:] if e.get("target") in (nid, sid) and e.get("by") != w.me and not e.get("undone")
                and aspects_meet({"text"}, event_aspects(e))]
        by = {}
        for e in them:
            by.setdefault(persons.by(w, e), []).append(e["id"])
        who = "; ".join(f"{name} {', '.join(ids[-3:])}" for name, ids in by.items())
        note = (f"~ joined: this text was changed since you read it ({said(d_theirs)}" + (f", by {who}" if who else "") + f"); your "
                f"change ({said(d_mine)}, as numbered now) went into the text as it is now, and theirs is kept. You have not "
                f"read theirs: read {nid} shows the whole" + (". The lines joined and the lens compiles; whether it still "
                f"means what you each intended, only the scene shows" if kinds.is_lens(s) else ""))
        if verb == "replace" and theirs.count(kv["old"]) == 1:
            return verb, kv, note
        return "rewrite", {"text": merged}, note

    ONCE = {"persons_begin", "persons_migrate", "promises_migrate", "lines_declined", "restore_binds", "external", "refuse"}

    def _undo_record(self, ev):
        """Put back the whole record `ev` belongs to, by its facts. -> the receipt, or None when this world has no
        log, the event has no record (it is older than the log), or it is one of the once-only changes."""
        ctx = getattr(self, "_store", None)
        if ctx is None:
            return None
        import store
        w = self.world
        rec = ctx.log.record_of_event(ev["id"])
        if rec is None or not store.facts_of(rec):
            return None
        evs = [e for e in (w.event_by_id(p.get("e")) for p in rec["parts"]) if e is not None]
        if any(self.ONCE & set(e.get("undo") or {}) for e in evs):
            return None
        if ev.get("undone") or ev["verb"] == "undo" or any(e.get("undone") for e in evs):
            raise Refusal(f"{ev['id']} cannot be undone (already undone or is an undo)")
        words = (rec.get("words") or "")[:120]
        try:
            plan = store.undo_plan(ctx.log, rec, store.flatten(w))
        except store.CannotUndo as e:
            raise Refusal(f"{ev['id']} cannot be put back: {e}. It was the command `{words}` (record {rec['seq']}); "
                          "undo what came after it first, or act on the world as it is")
        touched = store.apply(w, plan)
        last = None
        for e in reversed(evs):
            e["undone"] = True
            last = w._event("undo", e["id"], {}, {}, note=f"reverted {e['id']}")
        for t in touched:
            if t in w.nodes or t in w.subjects:
                self._mark_seen(t)       # an undo is your own change; what it touched stays seen
        self._after_mutation()
        ids = [e["id"] for e in evs]
        rules = sorted({str(e.get("via"))[5:] for e in evs if str(e.get("via") or "").startswith("rule ")})
        what = f"{ids[0]}" if len(ids) == 1 else f"{ids[0]}..{ids[-1]} ({len(ids)} events of one command"
        if len(ids) > 1:
            what += (f", {len(rules)} rule consequence(s): " + ", ".join(rules) if rules else "") + ")"
        return (f"ok {last['id']}: reverted {what}, which was: {words}"
                + (f"  (made {rec['at'][11:16]})" if rec.get("at") else ""))

    def cmd_do(self, verb, target, kv):
        if not verb or not target:
            raise Refusal("do needs a verb and an id")
        verb = verb.lower()
        w = self.world
        if verb not in self._verb_names():
            try:
                hint = self._resolve(target)
                raise Refusal(f"{verb} is not a verb; {hint} has: " + "  ".join(
                    f"{v} {sig}".strip() for v, sig in w.verbs_for(hint).items()))
            except Refusal as r:
                if "is not a verb" in str(r):
                    raise
                raise Refusal(f"{verb} is not a verb (form: do <verb> <id> key=value); try verbs <id>")
        nid = self._resolve(target)
        kv = dict(kv)   # values were unescaped where they were parsed
        cur = w.nodes[nid]["rev"] if nid in w.nodes else w.subjects[nid]["rev"]
        seen = cur if getattr(self, "_in_rules", False) else self.seen.get(nid)   # a rule is the desk's own hands: no fence
        adds = self._adds_line(nid, verb, kv)
        self._hold_line(nid, verb, kv)    # a5068: a line on an old view of its chat or thread waits
        if seen is None and not adds:     # a834: an added line overwrites nothing, so looking first protects nothing
            raise Refusal(f"you have not looked at {nid} yet; look, read or where it first")
        behind = (seen != cur and adds) or seen is None     # a chat line lands; what I missed stays unread, and nothing is marked seen
        if seen != cur and not behind:
            recent = [e for e in w.events if e["target"] == nid or nid in (e.get("changed") or [])]
            why = f"; last change {recent[-1]['id']} {recent[-1]['verb']} by {persons.by(w, recent[-1])}" if recent else ""
            raise Refusal(f"stale: {nid} changed since you last saw it{why}; {self._again(nid, aspects_of(verb, kv))} before acting")
        blind = self._blind(nid, verb, kv)
        if blind:
            raise Refusal(f"you have not seen {nid}'s {blind}; {self._read_hint(nid, blind)} before you replace it")
        kv = {k: self._resolve(v, allow_subject=False) if k in ("into", "before", "after") else v for k, v in kv.items()}
        r = w.apply(verb, nid, None, kv)
        for c in r.get("changed", []):
            if c in w.events[-1].setdefault("changed", []):
                pass
            w.events[-1].setdefault("changed", []).append(c)
        self._after_mutation()
        for c in {nid, *r.get("changed", [])} if not behind else ():      # you did it, you saw the result of what you touched
            self._note_seen(c, len(w.events), sorted(aspects_of(verb, kv)) if aspects_of(verb, kv) is not None else None)
            if c in w.nodes:
                self.seen[c] = w.nodes[c]["rev"]
            elif c in w.subjects:
                self.seen[c] = w.subjects[c]["rev"]
        out = f"ok {r['event']}: {verb} {nid} {self._fmt_args(kv)}".rstrip()
        if r.get("created"):
            out += f" → created {r['created']}"
        if r.get("note"):
            out += f"\n  {r['note']}"
        said = self._chat_behind(nid) if adds and not getattr(self, "_in_rules", False) else ""
        if said:
            out += f"\n  {said}"     # a834: counted from what this reader was shown, not from who touched it since
        waits = self._chat_waits(nid, kv) if adds and not getattr(self, "_in_rules", False) else ""
        if waits:
            out += f"\n  {waits}"    # a1566: whom this line took ('to: pike'), and for each what happened ('Pike: woken')
        calls = self._written_calls([r["event"]]) if r.get("event") and not adds and not getattr(self, "_in_rules", False) else ""
        if calls:
            out += f"\n  {calls}"    # a2733: whom a comment or note edit called by its header, and what it only mentioned
        if r.get("created") in w.nodes:
            self._mark_seen(r["created"])
            if verb == "create":
                self._chat_made(r["created"])
            out += "\n  now: " + self.line(r["created"], 1) + self.position_note(r["created"])
        for c in r.get("changed", []) if not behind else ():
            if c in w.nodes and c != nid:
                self._mark_rev(c, aspects_of(verb, kv))    # your own change: the aspects you wrote are seen, the others are not
        if nid in w.nodes:
            if not behind:
                self._mark_rev(nid, aspects_of(verb, kv))
            self._receipt = True
            try:
                if not adds:      # a3806: a line added to a chat changes nothing else about the chat worth a line
                    out += "\n  now: " + self.line(nid, 1) + self.position_note(nid)
            finally:
                self._receipt = False
        return out

    FOLD_OVER = 12

    def _settled_fold(self, holder, ids):
        """Which of `ids` (the things a place lists) are left out of its listing as settled. 9 Oct (a3806): finished
        work never left: 176 of 785 things were done, cured or answered and still listed, and every row costs its
        reader. Nothing moves: a listing of more than FOLD_OVER things that mixes live and settled shows the live ones
        and says how many it left out and how to see them. A place whose things are all settled is a shelf and shows
        them; so does one whose prop says settled=shown. -> the ids left out."""
        import knife
        w = self.world
        if len(ids) <= self.FOLD_OVER or str((w.nodes[holder].get("props") or {}).get("settled", "")).lower() == "shown":
            return []
        out = [i for i in ids if w.nodes[i]["type"] == "appearance" and knife.is_settled(w, i)]
        return out if 0 < len(out) < len(ids) else []

    def _geometry_said(self):
        """Does a thing's line say how it sits on a screen (cramped, past the bottom, offscreen-part, spills-parent)?
        Where the layout verbs are at hand (rooms.layout_at_hand: the Desktop and the rooms inside it; everywhere in a
        world where no room says verbs=layout). Elsewhere the reader is not laying anything out and paid for those
        words on every row (9 Oct, a3806: 2,496 of the 15,824 characters of one look); `where <id>` says them, always."""
        key = (len(self.world.events), self.world.me)
        if getattr(self, "_geo_key", None) != key:
            import rooms
            self._geo_key, self._geo_said = key, rooms.layout_at_hand(self)
        return self._geo_said

    def position_note(self, nid):
        n = self.world.nodes.get(nid)
        if not n or not n["parent"] or self.world.nodes[n["parent"]]["layout"] == "free":
            return ""
        kids = [k["id"] for k in self.world.children(n["parent"])]
        i = kids.index(nid) + 1
        suffix = 'th' if 10 <= i % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(i % 10, 'th')
        return f"  ({i}{suffix} of {len(kids)} in {n['parent']})"

    def _after_mutation(self):
        for h in list(self.hooks):
            h(self)

    # ---- apply variant: edit the outline ----------------------------
    LINE = re.compile(r"^(\s*)([fa]\d\d)\b(?:\s+\w+)?(?:\s+\"([^\"]*)\")?")

    def cmd_apply(self, body, dry):
        w = self.world
        body = body.strip("\n")
        if not body:
            raise Refusal("apply needs the edited outline on the following lines (first line must be a surface)")
        rows = []
        for raw in body.splitlines():
            if not raw.strip() or raw.strip().startswith(">") or raw.strip().startswith("verbs"):
                continue
            m = self.LINE.match(raw.replace("├", " ").replace("└", " ").replace("│", " "))
            if not m:
                raise Refusal(f"could not read line: {raw!r} (each line must start with an id)")
            rows.append((len(m.group(1)), m.group(2), m.group(3)))
        if not rows:
            raise Refusal("nothing to apply")
        root = rows[0][1]
        if root not in w.nodes or w.nodes[root]["type"] != "surface":
            raise Refusal("first line must be the surface you are editing")
        # infer parent by indentation
        stack = [(rows[0][0], root)]
        parent_of, order_in, titles = {}, {}, {}
        for ind, nid, title in rows[1:]:
            while stack and ind <= stack[-1][0]:
                stack.pop()
            if not stack:
                raise Refusal(f"{nid} is indented less than the root")
            p = stack[-1][1]
            parent_of[nid] = p
            order_in.setdefault(p, []).append(nid)
            if title is not None:
                titles[nid] = title
            if nid in w.nodes and w.nodes[nid]["type"] == "surface":
                stack.append((ind, nid))
        # which nodes are in scope: everything under root that the caller has seen
        def subtree(nid):
            out = [nid]
            if w.nodes[nid]["type"] == "surface":
                for k in w.children(nid):
                    out += subtree(k["id"])
            return out
        scope = set(subtree(root)) - {root}
        listed = set(parent_of)
        ops = []
        for nid in listed:
            if nid not in w.nodes:
                raise Refusal(f"{nid} does not exist")
            if nid not in scope and self.seen.get(nid) is None:
                raise Refusal(f"{nid} is outside {root} and you have not looked at it")
        for nid in sorted(scope - listed):
            if self.seen.get(nid) is None:
                raise Refusal(f"{nid} is inside {root} but not in your outline; you have not seen it (open its surface first)")
            ops.append(("remove", nid, {}))
        for nid, p in parent_of.items():
            if w.nodes[nid]["parent"] != p:
                ops.append(("move", nid, {"into": p}))
        for p, ids in order_in.items():
            if w.nodes[p]["layout"] != "free":
                current = [k["id"] for k in w.children(p) if k["id"] in ids]
                if [i for i in ids if i in w.nodes] != current:
                    for i, nid in enumerate(ids):
                        ops.append(("move", nid, {"into": p, "at": i}))
        for nid, t in titles.items():
            if w.title(w.nodes[nid]) != t:
                ops.append(("rename" if w.nodes[nid]["type"] == "surface" else "edit", nid, {"title": t}))
        for _, nid, _ in ops:
            if nid in w.nodes and self.seen.get(nid) not in (None, w.nodes[nid]["rev"]):
                raise Refusal(f"stale: {nid} changed since you last saw it; look again")
        if not ops:
            return "nothing to change: the outline already matches the desk"
        desc = "\n".join(f"  {v} {nid} {self._fmt_args(a)}".rstrip() for v, nid, a in ops)
        if dry:
            return f"plan ({len(ops)} op(s)):\n{desc}\nsend the same outline with apply to do it"
        snap = deepcopy((w.nodes, w.subjects, w.events))
        done = []
        try:
            for v, nid, a in ops:
                r = w.apply(v, nid, None, a)
                done.append(r["event"])
        except Refusal as e:
            w.nodes, w.subjects, w.events = snap
            raise Refusal(f"apply aborted, nothing changed: {e}")
        self._after_mutation()
        for nid in listed:
            self.seen.pop(nid, None)
        return f"applied {len(ops)} op(s) (events {done[0]}..{done[-1]}):\n{desc}\n" + self.outline(root, 2)
