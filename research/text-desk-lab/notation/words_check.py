"""words_check (a1308 (3)): the house's own words, typed back. Every word the house prints about itself should be a word
it answers to, or at least one help explains (s1286, Juniper: "if the house says it, you can ask about it").

    python words_check.py [world] [--as name]        default world: frontier; reads it, never saves it

It gathers the house's fixed strings and asks each one back, in memory, on a copy it never saves:
  - code: every string literal in the desk's own modules (receipts, refusals, !! lines, help): each `help <word>`
    they tell a reader to type must answer (not help's 'no command, verb or topic' fallback)
  - the world's own words: each room's description note, the notes on the Board, the door and the house notes, and
    the Handbook. In them: each `help <word>`, each id (a12 f3 s4 e5 c6 l7, and commit hashes), and each backticked
    command (`history`, `do card ...`): its first word must be a command, a verb (built-in or made in the world), or
    a verb's word after do
  - the house's nouns: each kind of thing in the world and the words it names itself by (card, room, corner, rule ...),
    as a newcomer would ask them: help <noun>
  - the desk's own command words (verbs.DESK_WORDS, house.py's COMMANDS): help <word> must explain each one
Prints one line per word that isn't answered, grouped, then a count. Exit 0 always: it is a report, not a gate (the
gate is test_house_words.py, on a world it builds).
"""
import ast
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

CODE = ("desk.py", "desk_knife.py", "desk_moo.py", "rooms.py", "verbs.py", "blanks.py", "house.py", "knife.py", "moo.py",
        "world.py", "scene.py", "workshop.py")
NOUNS = ("card", "cards", "room", "rooms", "corner", "rule", "rules", "lens", "verb", "verbs", "event", "events",
         "comment", "comments", "link", "links", "selection", "selections", "commission", "style", "resident",
         "house", "worker", "handbook", "board", "lounge", "desktop", "id", "ids", "misses", "wishes", "talk")
FALLBACK = "no command, verb or topic"
HELP_WORD = re.compile(r"(?:^|[\s(;:·`'\"])help ([a-z][a-z-]+)(?=$|[\s).;,:`'\"])")
PROSE = {"is", "or", "with", "for", "lists", "may", "the", "a", "an", "to", "you", "take", "shape", "themselves", "users",
         "topics", "explains", "knows", "answers", "says", "can", "will", "and", "it", "them", "us", "out", "each"}
ID = re.compile(r"(?<![\w/#.-])([afsecl]\d{2,})(?![\w])")
HASHISH = re.compile(r"(?<![\w/])([0-9a-f]{7,12})(?![\w])")
TICKED = re.compile(r"`([^`\n]{2,80})`")


def code_strings():
    """-> [(file:line, text)] for every string constant (f-string parts too) in the desk's modules."""
    out = []
    for name in CODE:
        tree = ast.parse((HERE / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                out.append((f"{name}:{node.lineno}", node.value))
    return out


def world_texts(w):
    """-> [(where, text)]: the house's own words in this world."""
    import rooms
    out, seen = [], set()

    def add(sid, why):
        s = w.subjects.get(sid)
        if s and sid not in seen:
            seen.add(sid)
            out.append((f"{why} {(w.appearances_of(sid) or [sid])[0]} \"{s['title']}\"", s["text"]))

    for f in rooms.all_rooms(w):
        d = (w.nodes[f].get("props") or {}).get("describe")
        n = w.nodes.get(d)
        add(n["subject"] if n and n.get("subject") else d, f"describe of {w.nodes[f]['title']}:")
    for s in w.subjects.values():
        if s["title"] in ("The door", "The house"):
            add(s["id"], "note")
    for n in w.nodes.values():
        if n["type"] != "surface" or n["title"] not in ("Board", "Handbook"):
            continue
        stack = [n["id"]]
        while stack:
            for k in w.children(stack.pop()):
                if k["type"] == "surface" and n["title"] == "Handbook":
                    stack.append(k["id"])
                elif k.get("subject") and (n["title"] == "Handbook" or w.subjects[k["subject"]]["kind"] == "note"):
                    add(k["subject"], f"{n['title']}:")
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    me = sys.argv[sys.argv.index("--as") + 1] if "--as" in sys.argv else "words-check"
    args = [a for a in args if a != me]
    world = args[0] if args else "frontier"
    import export_docs
    import verbs
    import house
    from world import Refusal
    d = export_docs.load(world)
    w = d.world
    w.me = me
    d.seen, d.open = {}, {w.root}

    def ask(line):
        """-> (answered, text). A refusal or help's fallback is not an answer."""
        n0 = len(w.events)
        r = d.dispatch("desk", {"line": line})
        del w.events[n0:]                     # asking changes nothing (a go would be an event); this copy is never saved
        text = r.get("text") or ""
        if "error" in r:
            return False, r["error"]
        return FALLBACK not in text, text

    def first_line(t):
        return (t or "").strip().splitlines()[0][:150] if (t or "").strip() else ""

    problems = {}

    def note(group, word, where, why):
        problems.setdefault(group, {}).setdefault(word, (where, why))

    checked = 0
    # 1. the desk's command words
    for word in sorted(verbs.DESK_WORDS | house.COMMANDS | {"rest"}):
        checked += 1
        ok, t = ask(f"help {word}")
        if not ok:
            note("help <command> doesn't explain it", word, "verbs.DESK_WORDS / house.COMMANDS", first_line(t))
    # 2. help <word> the code tells a reader to type
    for where, text in code_strings():
        for word in HELP_WORD.findall(text):
            if word in PROSE:
                continue
            if word in problems.get("help <word> named in the code", {}):
                continue
            checked += 1
            ok, t = ask(f"help {word}")
            if not ok:
                note("help <word> named in the code", word, where, first_line(t))
    # 3. the world's own words
    builtin = d._builtin_verbs()
    import scene
    lens_words = {x.strip().split()[0] for x in scene.vocabulary().replace("|", ",").split(",") if x.strip()}
    for where, text in world_texts(w):
        for word in [x for t in TICKED.findall(text) for x in HELP_WORD.findall(t)]:     # prose says 'help take care'
            if word in PROSE:
                continue
            checked += 1
            ok, t = ask(f"help {word}")
            if not ok:
                note("help <word> named in the world's own text", word, where, first_line(t))
        for rid in ID.findall(text):
            checked += 1
            ok, t = ask(f"examine {rid}")
            if not ok:
                note("an id the world's own text prints", rid, where, first_line(t))
        for h in HASHISH.findall(text):
            if not any(c.isdigit() for c in h) or h.isdigit() or not any(c.isalpha() for c in h):
                continue
            checked += 1
            ok, t = ask(f"examine {h}")
            if not ok and "looks like a commit" not in t:
                note("a commit hash the world's own text prints", h, where, first_line(t))
        for tick in TICKED.findall(text):
            words = tick.strip().lstrip(">").split()
            if not words or not re.match(r"^[a-z][a-z?]*$", words[0]):
                continue
            first = words[0]
            if first == "do" and len(words) > 1:
                v = words[1].lower()
                if v in builtin or v == "use" or verbs.visible(d, v, me) or "<" in v:      # do use <id>: verbs.try_line
                    continue
                checked += 1
                note("a do <verb> the world's own text shows", f"do {v}", where, "no built-in verb, and no world verb you could use")
                continue
            if first in verbs.DESK_WORDS or first in house.COMMANDS or first == "rest":
                continue
            if verbs.visible(d, first, me) or first in builtin or first in lens_words:
                continue      # a lens line's words (count <selection>, each <part>) are the lens grammar's, not commands
            # prose in backticks (`prop:status=done`, `role=room`, a lone prop name) is not a command; a word followed
            # by an id or a <placeholder>, or a line after >, reads as one
            if tick.strip().startswith(">") or (len(words) > 1 and (ID.match(words[1]) or words[1].startswith("<"))):
                checked += 1
                note("a command the world's own text shows", first, where, f"`{tick}`: nothing answers to its first word")
    # 4. the house's nouns, as a newcomer asks them
    kinds = sorted({s["kind"] for s in w.subjects.values()} | {"surface"})
    for word in sorted(set(NOUNS) | set(kinds)):
        checked += 1
        ok, t = ask(f"help {word}")
        if not ok:
            note("help <noun> (a word the house names itself by)", word, "kinds in the world, NOUNS", first_line(t))
    # 5. one id of each kind, as printed
    samples = {"a": next((n["id"] for n in w.nodes.values() if n["type"] == "appearance"), None),
               "f": w.root, "s": next(iter(w.subjects), None), "e": w.events[-1]["id"] if w.events else None,
               "c": next((c["id"] for s in w.subjects.values() for c in s["comments"]), None),
               "l": w.links[0]["id"] if w.links else None}
    for k, rid in samples.items():
        if not rid:
            continue
        for cmd in ("examine", "look", "read", "history"):
            checked += 1
            ok, t = ask(f"{cmd} {rid}")
            if not ok and not (cmd == "read" and k == "f"):      # a surface has no text: read names look instead
                note("an id kind, typed back", f"{cmd} {rid}", f"kind {k}", first_line(t))
    total = sum(len(v) for v in problems.values())
    print(f"words_check {world}: {checked} words asked back, {total} not answered")
    for group, words in problems.items():
        print(f"\n{group} ({len(words)}):")
        for word, (where, why) in sorted(words.items()):
            print(f"  {word:<22} {where}\n  {'':<22} -> {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
