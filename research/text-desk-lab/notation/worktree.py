"""worktree: work apart from a shared desk, then come back as commands (prototype).

Inside any session, from the CLI or the shell (both route these lines here before the desk sees them):

    worktree                     list this session's worktrees (or say which one you are in)
    worktree fork <name>         copy this world into <session>@<name>; enter it with
                                   python explore.py <session>@<name> --as <you>      or  ?session=<session>@<name>
    worktree diff <name>         the commands made there, and what the base has done since (! = both touched it)
    worktree merge <name>        replay those commands here, each signed by who made it, all or nothing

A worktree is a whole world, not a patch: rules fire there, undo works there, the shell renders it. What comes
back is not state but the journal of command lines that changed it. Merge replays that journal against the base
as it is NOW. Ids made in the worktree are remapped to the ids the base hands out. The ordinary seen fence is the
conflict detector: a replayed command is refused when another actor's deed named its target after the fork point.
One refusal aborts the whole merge and the base is untouched; the refusal says which line and why.

Nothing here holds a lock while anyone thinks. A fork costs one pickle copy.
"""

import pickle
from desk import aspects_of, aspects_meet, event_aspects
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SESSIONS = HERE / "sessions"
ID = re.compile(r"(?<![\w$.])([afs]\d+)\b")
JOURNALLED = ("clock ",)     # changes the desk without making a world event (a1027: rules are notes; scripts retired)


def _aspects_of_line(cmd):
    """The aspects one journaled command line touches (Sable's spec 1: merge conflicts are per (referent, aspect))."""
    import shlex
    out = set()
    for seg in cmd.split(";"):              # a journaled line may be `look :3; do prop a06 beds=20`
        try:
            words = shlex.split(seg.strip())
        except ValueError:
            return None
        if not words or words[0].lower() in ("look", "read", "examine", "find", "where", "verbs", "pivot", "history", "help", "open", "close", "scene", "rows", "table"):
            continue
        if words[0].lower() == "go":         # a678: walking touches no thing, so it never conflicts
            out.add("presence")
            continue
        if len(words) < 2 or words[0].lower() != "do":
            return None
        kv = dict(w.partition("=")[::2] for w in words[2:] if "=" in w)
        a = aspects_of(words[1].lower(), kv)
        if a is None:
            return None
        out |= a
    return out


def _kin(w, ids):
    """Sable's lost update: a command names a06, the base edited the same subject through a05. The fence must see
    through appearances to the subject and back out to every appearance of it."""
    out = set(ids)
    for i in list(ids):
        subj = (w.nodes.get(i) or {}).get("subject") or (i if i in w.subjects else None)
        if subj:
            out.add(subj)
            out |= {nid for nid, n in w.nodes.items() if n.get("subject") == subj}
    return out


def ids_of(desk):
    w = desk.world
    return set(w.nodes) | set(w.subjects)


def _num(i):
    return int(re.sub(r"\D", "", i) or 0)


def record(desk, line, actor, before_ids, events_before):
    """Called after every dispatched line. In a worktree, remember the lines that changed the world."""
    wt = getattr(desk, "_wt", None)
    if wt is None:
        return
    w = desk.world
    head = line.strip().split(" ", 1)[0].lower()
    if head == "undo" and line.strip().lower() == "undo" and len(w.events) > events_before:
        mine = [k for k, j in enumerate(wt["journal"]) if j["by"] == actor]
        if mine:
            wt["journal"].pop(mine[-1])             # a bare undo takes back my latest command; so does the journal
            return
    if len(w.events) > events_before or line.strip().lower().startswith(JOURNALLED):
        # what the line actually changed, by id: a command may name its target by title, a handle or a selection,
        # and the merge must still see it (review 29 Sep: a title-named change merged over the base's and lost it)
        made = w.events[events_before:]
        touched = {e["target"] for e in made} | {c for e in made for c in (e.get("changed") or [])}
        wt["journal"].append({"line": line, "by": actor,
                              "created": sorted(ids_of(desk) - before_ids, key=_num),
                              "touched": sorted((touched & before_ids), key=_num)})


def _fork_path(base, name):
    return SESSIONS / f"{base}@{name}.pickle"


def _load(base, name):
    p = _fork_path(base, name)
    if not p.exists():
        raise ValueError(f"no worktree {name!r} of {base} (worktree lists them)")
    return pickle.loads(p.read_bytes())


def handle(line, session, desk, actor):
    """Returns (text, desk). The desk returned is the one the caller must save (merge builds a new one)."""
    words = line.strip().split()
    sub = words[1].lower() if len(words) > 1 else "list"
    name = words[2] if len(words) > 2 else None
    inside = getattr(desk, "_wt", None)
    try:
        if sub == "list":
            if inside:
                return (f"you are in worktree {session} · forked from {inside['base']} at event {inside['base_events']} by {inside['by']} · "
                        f"{len(inside['journal'])} command(s) journalled" + (" · merged" if inside.get("merged") else "")
                        + f"\n  to bring it back: in {inside['base']}, worktree diff {session.split('@', 1)[1]} then worktree merge {session.split('@', 1)[1]}"), desk
            rows = []
            for p in sorted(SESSIONS.glob(f"{session}@*.pickle")):
                wt = getattr(pickle.loads(p.read_bytes()), "_wt", None) or {}
                behind = len(desk.world.events) - wt.get("base_events", 0)
                rows.append(f"  {p.stem.split('@', 1)[1]} · by {wt.get('by')} · {len(wt.get('journal', []))} command(s) · base has moved {behind} event(s) since"
                            + (" · merged" if wt.get("merged") else ""))
            return ("worktrees of " + session + ":\n" + "\n".join(rows)) if rows else f"no worktrees of {session} yet (worktree fork <name>)", desk
        if not name or not re.fullmatch(r"[\w-]+", name):
            raise ValueError("a worktree needs a plain name: worktree fork sketch")
        if sub == "fork":
            if inside:
                raise ValueError("this is already a worktree; fork from the base")
            if _fork_path(session, name).exists():
                raise ValueError(f"worktree {name!r} exists (worktree lists them)")
            fork = pickle.loads(pickle.dumps(desk))
            fork._wt = {"base": session, "base_events": len(desk.world.events), "by": actor, "journal": []}
            _fork_path(session, name).write_bytes(pickle.dumps(fork))
            # 7 Oct: a fork takes its base's log with it (store.py), so it goes on from the same records: its own
            # are a tail after the base's, and what it changed can be read as facts
            import shutil
            import kept
            import store
            kept.fork(SESSIONS / f"{session}.pickle", _fork_path(session, name))
            base_log = store.log_path(SESSIONS / f"{session}.pickle")
            if base_log.exists():
                shutil.copyfile(base_log, store.log_path(_fork_path(session, name)))
            return (f"ok forked {session} at event {len(desk.world.events)} as {session}@{name}\n"
                    f"  enter: python explore.py {session}@{name} --as {actor}   or   ?session={session}@{name}&as={actor}\n"
                    f"  the base keeps moving without you; worktree diff {name} shows both sides"), desk
        if inside:
            raise ValueError(f"run worktree {sub} from the base ({inside['base']}), not from inside a worktree")
        fork = _load(session, name)
        wt = fork._wt
        if sub == "diff":
            named = _kin(desk.world, {m for j in wt["journal"] for m in ID.findall(j["line"]) + j.get("touched", [])})
            out = [f"worktree {name} · forked at event {wt['base_events']} by {wt['by']}" + (" · merged" if wt.get("merged") else ""),
                   f"there ({len(wt['journal'])} command(s)):"]
            out += [f"  + {j['by']}: {j['line']}" + (f"   (made {' '.join(j['created'])})" if j["created"] else "") for j in wt["journal"]] or ["  nothing yet"]
            since = [e for e in desk.world.events[wt["base_events"]:] if not e.get("undone")]
            out.append(f"here since the fork ({len(since)} event(s)):")
            for e in since[-20:]:
                n = desk.world.nodes.get(e["target"]) or {}
                both = e["verb"] not in ("create", "comment") and (e["target"] in named or n.get("subject") in named)
                out.append(f"  {'!' if both else ' '} {e['id']} {e['verb']} {e['target']} by {e['by']}")
            if any(l.startswith("  !") for l in out):
                out.append("  ! = the worktree also names this thing; merge will refuse there if someone else did it")
            return "\n".join(out), desk
        if sub == "merge":
            done = wt.get("merged_n", 0)                        # Moss lost work to a merge that closed the worktree for good:
            todo = wt["journal"][done:]                         # a worktree stays open, and merge takes what is new since last time
            if not todo:
                raise ValueError(f"nothing to merge from {name}: " + ("no commands there yet" if not done else f"all {done} command(s) are already here")
                                 + f". Work in {session}@{name}, then merge again")
            trial = pickle.loads(pickle.dumps(desk))
            w = trial.world
            keep = (trial.seen, trial.open, trial.last_event_seen, w.me)
            trial.seen = {nid: -1 for nid in w.nodes}           # force every act through the touched-by-others question
            idx = getattr(trial, "_seen_idx", None)
            if idx is None:
                idx = trial._seen_idx = {}
            for j in wt["journal"]:
                for nid in w.nodes:
                    idx[(j["by"], nid)] = wt["base_events"]     # "since you saw it" means since the fork
            mapping, first = dict(wt.get("mapping", {})), len(w.events)      # ids renamed by an earlier merge stay renamed
            for k, j in enumerate(todo, done + 1):
                cmd = ID.sub(lambda m: mapping.get(m.group(1), m.group(1)), j["line"])
                w.me = j["by"]
                # Lark: the fence asks "changed since YOU saw it", and lets you through when you were both hands.
                # A merge must ask "changed since the FORK saw it", whoever did it.
                named = _kin(w, set(ID.findall(cmd)) | {mapping.get(t, t) for t in j.get("touched", [])})
                mine = _aspects_of_line(cmd)
                for e in (w.events[wt["base_events"]:first] if mine != {"presence"} else []):
                    subj = (w.nodes.get(e["target"]) or {}).get("subject")
                    if not e.get("undone") and e.get("merged") != name and e["verb"] not in ("create", "comment") and (e["target"] in named or subj in named) \
                            and aspects_meet(mine, event_aspects(e)):
                        return (f"refused: merge of {name} stopped at command {k} of {len(wt['journal'])}; nothing was applied\n"
                                f"  {j['by']}: {cmd}\n  {e['target']} changed here since the fork ({e['id']} {e['verb']} by {e['by']})\n"
                                f"  worktree diff {name} shows both sides; redo that step in the worktree or here by hand"), desk
                before = ids_of(trial)
                r = trial.dispatch("desk", {"line": cmd})
                text = r.get("text") or ""
                if r.get("error") or text.startswith("ERR") or "\nERR" in text:
                    why = (r.get("error") or text).strip().splitlines()[0]
                    return (f"refused: merge of {name} stopped at command {k} of {len(wt['journal'])}; nothing was applied\n"
                            f"  {j['by']}: {cmd}\n  {why}\n"
                            f"  worktree diff {name} shows who touched what; redo that step in the worktree or here by hand"), desk
                made = sorted(ids_of(trial) - before, key=_num)
                mapping.update(dict(zip(j["created"], made)))
            trial.seen, trial.open, trial.last_event_seen, w.me = keep
            for e in w.events[first:]:
                e["merged"] = name                              # a merge is a bulk act; it should not wear ordinary clothes
            wt["merged"] = len(w.events)
            wt["merged_n"] = len(wt["journal"])
            wt["mapping"] = mapping
            _fork_path(session, name).write_bytes(pickle.dumps(fork))
            evs = w.events[first:]
            span = f"{evs[0]['id']}..{evs[-1]['id']}" if evs else "no events"
            renamed = " ".join(f"{a}→{b}" for a, b in mapping.items() if a != b)
            return (f"ok merged {name}: {len(todo)} command(s) replayed as {span}, each signed by who made it"
                    + (f"\n  ids renamed on the way in: {renamed}" if renamed else "")
                    + "\n  each is an ordinary event: undo works on them one command at a time"), trial
        raise ValueError("worktree fork|diff|merge <name>, or worktree alone to list")
    except ValueError as e:
        return f"ERR {e}", desk
