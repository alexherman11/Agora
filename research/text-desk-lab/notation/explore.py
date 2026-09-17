"""Open-ended exploration: an empty tiled desk, the lean REPL, and a session that persists between runs.

    python explore.py <session> < commands      run commands against the saved session (created empty if new)
    python explore.py <session> --reset         start the session over
    python explore.py <session> --dump          print the world snapshot as JSON

Never touches the task worlds; this is for building a desk from nothing and finding friction.
"""

import json
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import pickle
import sys
from pathlib import Path

from desk_knife import DeskKnife
from world import World

HERE = Path(__file__).resolve().parent
SESSIONS = HERE / "sessions"


def fresh():
    w = World()
    w.nodes[w.root]["layout"] = "row"   # a tiled top level, the round-8 lesson
    w.equal_share = False
    d = DeskKnife(w, "lean")
    d.batch = True
    d.lean = True
    d.read_cap = 4
    d.ids = {}
    return d


def main():
    name = sys.argv[1]
    SESSIONS.mkdir(exist_ok=True)
    path = SESSIONS / f"{name}.pickle"
    if "--reset" in sys.argv or not path.exists():
        desk = fresh()
    else:
        desk = pickle.loads(path.read_bytes())
    if "--dump" in sys.argv:
        print(json.dumps(desk.snapshot(), indent=1))
        return
    if "--shape" in sys.argv:
        # the desk without ids: what a faithful replay must reproduce
        w = desk.world

        def walk(fid, depth):
            for k in w.children(fid):
                if k["type"] == "surface":
                    print("  " * depth + f"surface {k['title']!r} {k['layout']}" + (f" query={k['query']!r}" if k.get("query") else ""))
                    walk(k["id"], depth + 1)
                else:
                    s = w.subjects[k["subject"]]
                    bits = [s["kind"], repr(s["title"]), f"tags={s['tags']}", f"due={s.get('due')}", f"text={__import__('hashlib').md5(s['text'].encode()).hexdigest()[:6]}",
                            f"comments={[(c['by'], c['text'], c['resolved']) for c in s['comments']]}", "folded" if k["folded"] else "",
                            f"props={sorted((s.get('props') or {}).items())}" if s.get("props") else ""]
                    print("  " * depth + " ".join(b for b in bits if b))
        walk(w.root, 0)
        for l in w.links:
            print(f"link {w.subjects[l['from']]['title']!r} -> {w.subjects[l['to']]['title']!r} {l['kind']}")
        for r in desk.rules or []:
            print(f"rule {r['sel']} {r['verb']} {r['kv']}")
        for name, body in (desk.scripts or {}).items():
            print(f"script {name} = {body}")
        return
    if "--reset" in sys.argv and sys.stdin.isatty():
        path.write_bytes(pickle.dumps(desk))
        print("reset")
        return
    for raw in sys.stdin:
        line = raw.rstrip("\n")   # the desk's own grammar handles \n inside values; do not pre-convert
        if not line.strip() or line.startswith("#"):
            continue
        print(f"> {line}")
        if line.startswith("!"):
            # !priya append a10 line="..."   another actor writes to the world directly (a test injection)
            import shlex
            actor, verb, target, *rest = shlex.split(line[1:])
            kv = dict(a.partition("=")[::2] for a in rest)
            try:
                r = desk.world.apply(verb, target, None, kv, actor)
                desk._after_mutation()
                print(f"({actor} did {verb} {target}: {r.get('note') or r.get('event')})")
                desk._run_rules(cause=None)   # rules watch other actors' events too
                if desk._rule_notes:
                    print("\n".join(desk._rule_notes))
                    desk._rule_notes = None
            except Exception as e:
                print("ERR", e)
            print()
            continue
        r = desk.dispatch("desk", {"line": line})
        print(r.get("text") or ("ERR " + r["error"]))
        print()
    path.write_bytes(pickle.dumps(desk))


if __name__ == "__main__":
    main()
