"""try_house: run the house for real on a throwaway copy of a world, then clean up everything it made.

    python try_house.py [--from frontier] [--corners f571,f576] [--model M] [--turns 12] [--minutes 8]
                        [--say "a line from Alex" ...] [--porch "a line in Porch talk" ...] [--keep] [--name tag]

It copies sessions/<from>.pickle to a disposable world `try-<tag>`, wakes the chosen corners (default: the first
resident corner) and lets the others rest, and runs house.py on it with real `claude -p` residents. The --say and
--porch lines are said as Alex in the order given, one at a time, once every awake resident has been named, woken and
gone quiet: --say in the first awake resident's own chat, --porch in Porch talk (the chat with members=all). {0}, {1}
... in a line become the names the awake residents chose, so a line can say @{1}. Each resident's turn count when a
line is said goes in the report, which is how you see who a line reached. The run ends when every awake resident is quiet and every line has been said and answered, or when
the turn cap or the time limit is reached (these bound what a trial can cost).

It writes a readable report to research/command-center/trials/<tag>.md: for each resident, what the house sent,
what the resident wrote (its thinking included), and what the desk did; then what the residents did to the world.
After that, unless --keep, it deletes the disposable world, its house state and the residents' claude conversations
(claude keeps them in ~/.claude/projects/<the working directory, flattened>).

This spends real model calls. It never touches the world it copies.
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import desk_mcp      # noqa: E402
import export_docs   # noqa: E402
import house         # noqa: E402

REPORTS = HERE.parents[2] / "research" / "command-center" / "trials"
PROJECTS = pathlib.Path.home() / ".claude" / "projects"


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv[:-1] else default


def all_args(*names):
    return [(a, sys.argv[i + 1]) for i, a in enumerate(sys.argv[:-1]) if a in names]


def desk(world, who, line):
    return desk_mcp.run_desk({"line": line, "as": who, "session": world})[0]


def claude_folder(cwd):
    return PROJECTS / re.sub(r"[^A-Za-z0-9]", "-", str(cwd))


def quiet(res):
    """A resident is quiet when its process is up, no message is out, and it has had at least one turn."""
    return res and res.get("alive") and res.get("doing") == "resting" and res.get("turns", 0) > 0


def main():
    src = arg("--from", "frontier")
    tag = arg("--name") or time.strftime("%m%d-%H%M%S")
    world = f"try-{tag}"
    cap, minutes = int(arg("--turns", "12")), float(arg("--minutes", "8"))
    says = all_args("--say", "--porch")
    log = []
    shutil.copyfile(HERE / "sessions" / f"{src}.pickle", HERE / "sessions" / f"{world}.pickle")
    w = export_docs.load(world).world
    corners = sorted(n["id"] for n in w.nodes.values()
                     if n["type"] == "surface" and (n.get("props") or {}).get("role") == "resident")
    awake = (arg("--corners") or corners[0]).split(",")
    for rid in corners:
        extra = f" model={arg('--model')}" if arg("--model") and rid in awake else ""
        print(desk(world, "alex", f"look {rid} :1; do prop {rid} want={'awake' if rid in awake else 'rest'}{extra}").splitlines()[-2][:160])
    chat = next((s["id"] for s in w.subjects.values() if s["kind"] == "chat" and any(
        a.get("parent") == awake[0] for a in w.nodes.values() if a["type"] == "appearance" and a.get("subject") == s["id"])), None)
    chat_app = next((a["id"] for a in w.nodes.values() if a["type"] == "appearance" and a.get("subject") == chat), None)
    porch = next((s["id"] for s in w.subjects.values() if s["kind"] == "chat"
                  and "all" in str((s.get("props") or {}).get("members", "")).lower().split(",")), None)
    porch_app = next((a["id"] for a in w.nodes.values() if a["type"] == "appearance" and a.get("subject") == porch), None)

    state = house.STATE / world
    print(f"trial {world}: awake {','.join(awake)}, cap {cap} turns, {minutes:g} min, {len(says)} line(s) to say")
    proc = subprocess.Popen([sys.executable, str(HERE / "house.py"), world], cwd=HERE,
                            stdout=open(HERE / "house-test.log", "w", encoding="utf-8"), stderr=subprocess.STDOUT)
    start, said, ending = time.time(), 0, "?"
    try:
        while True:
            time.sleep(3)
            try:
                st = json.loads((state / "house.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            res = st.get("residents") or {}
            turns = sum(r.get("turns", 0) for r in res.values())
            if proc.poll() is not None:
                ending = f"the house exited ({proc.returncode})"
                break
            if turns >= cap:
                ending = f"turn cap ({turns} turns)"
                break
            if time.time() - start > minutes * 60:
                ending = f"time limit ({minutes:g} min, {turns} turns)"
                break
            if any((r.get("failures") or 0) >= 2 for r in res.values()):
                ending = "a resident failed twice"
                break
            if all(quiet(res.get(rid)) for rid in awake):
                names = [(res.get(rid) or {}).get("actor") for rid in awake]
                if said < len(says) and all(names):
                    kind, text = says[said]
                    text = text.format(*names)
                    where = chat_app if kind == "--say" else porch_app
                    counts = ", ".join(f"{n} {(res.get(rid) or {}).get('turns', 0)}" for n, rid in zip(names, awake))
                    print(f"  alex {'says' if kind == '--say' else 'in Porch talk'}: {text}   (turns: {counts})")
                    log.append(f"- {time.strftime('%H:%M:%S')} {'own chat' if kind == '--say' else 'Porch talk'}: {text!r}; turns so far: {counts}")
                    desk(world, "alex", f"read {where}; do append {where} line={json.dumps(text)}")
                    said += 1
                    time.sleep(6)                  # the house must see the line before quiet means answered
                    continue
                if said == len(says):
                    ending = f"everyone quiet ({turns} turns)"
                    break
    except KeyboardInterrupt:
        ending = "interrupted"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
    final = {}
    try:
        final = json.loads((state / "house.json").read_text(encoding="utf-8")).get("residents") or {}
    except (OSError, ValueError):
        pass
    log.append(f"- at the end, turns: " + ", ".join(f"{(final.get(rid) or {}).get('actor') or rid} {(final.get(rid) or {}).get('turns', 0)}" for rid in awake))
    report = write_report(world, src, awake, ending, said, says, log)
    print(f"ended: {ending}\nreport: {report}")
    if "--keep" not in sys.argv:
        cleanup(world, awake, corners)


def write_report(world, src, awake, ending, said, says, log):
    REPORTS.mkdir(parents=True, exist_ok=True)
    w = export_docs.load(world).world
    out = [f"# House trial {world}", "",
           f"Copied from `{src}` at {time.strftime('%Y-%m-%d %H:%M')}. Awake: {', '.join(awake)}. Ended: {ending}. "
           f"Alex said {said} of {len(says)} line(s). Real `claude -p` residents; this is a record of what they wrote.", "",
           "What Alex said, and each resident's turns at that moment:", ""] + log + [""]
    for rid in awake:
        props = (w.nodes.get(rid) or {}).get("props") or {}
        out += [f"## {rid}: {props.get('actor') or '(never named)'}", ""]
        path = house.STATE / world / rid / "transcript.jsonl"
        if not path.exists():
            out += ["(no transcript)", ""]
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            e = json.loads(line)
            k, d = e["kind"], e["data"]
            at = time.strftime("%H:%M:%S", time.localtime(e["at"]))
            if k == "sent":
                out += [f"**house → resident** {at}", "", "```text", d.strip(), "```", ""]
            elif k == "event" and d.get("type") == "assistant":
                for c in d.get("message", {}).get("content", []):
                    if c.get("type") == "text" and c["text"].strip():
                        out += [f"**resident** {at}", "", "```text", c["text"].strip(), "```", ""]
            elif k == "event" and d.get("type") == "result":
                u = d.get("usage") or {}
                out += [f"*turn ended {at}: {d.get('subtype')}{' (error)' if d.get('is_error') else ''}, "
                        f"{u.get('input_tokens', 0)} in + {u.get('cache_read_input_tokens', 0)} cached + "
                        f"{u.get('output_tokens', 0)} out, ${d.get('total_cost_usd', 0):.4f}*", ""]
            elif k in ("named", "lost", "failed", "unsent", "exit"):
                out += [f"*{k} {at}: {json.dumps(d)[:300]}*", ""]
    actors = {((w.nodes.get(r) or {}).get("props") or {}).get("actor") for r in awake} - {None, ""}
    out += ["## What the residents did to the world", ""]
    for e in w.events:
        if e.get("by") in actors:
            args = " ".join(f"{k}={str(v)[:120]!r}" for k, v in (e.get("args") or {}).items())
            out.append(f"- {e['id']} {e['by']} {e['verb']} {e['target']} {args}")
    path = REPORTS / f"{world}.md"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def cleanup(world, awake, corners):
    for rid in corners:
        shutil.rmtree(claude_folder(house.STATE / world / rid), ignore_errors=True)
    shutil.rmtree(house.STATE / world, ignore_errors=True)
    (HERE / "sessions" / f"{world}.pickle").unlink(missing_ok=True)
    print(f"removed world {world}, its house state and its residents' claude conversations")


if __name__ == "__main__":
    main()
