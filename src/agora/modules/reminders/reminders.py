"""EDITING A MODULE (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
A module is a seam to something outside the kernel (a model provider, git, Twitch, the media session, a map server) and
turns it into world facts and words. What the world does with them (who is told, when, in what words, how it looks)
belongs in rules, lenses and this module's settings thing, read at each use. Names (JEFF, Alex), ids (dk...), models,
counts, timeouts and message text in this file are debt: move them to settings when you touch them, and never add more.

reminders: a personal module in Python, installed for one person (SHAPE section 11, and what the desktop asked for).

    reminder.add <words>    do:  a reminder only its person sees (make kind=reminder … sees=me)
    reminder.note <words>   do:  tries to make a note; its grant reaches only reminders, so the kernel refuses it
    reminder.mine           see: its person's reminders

On its own, when it starts, it makes one reminder (a module acting on its own: its grants and its person's rights). It
hears `make` and `post` (only what its person may see), learns from `done` what its answers made, and says all of that
in `status`. It keeps nothing but counts; its home folder (from hello) holds one line saying when it last started.
"""
import json
import sys
import threading
import time
import uuid
from pathlib import Path

lock = threading.Lock()
waiting = {}
state = {"hello": None, "heard": [], "done": [], "own": None}


def send(msg):
    with lock:
        sys.stdout.write(json.dumps(msg) + "\n")
        sys.stdout.flush()


def ask(msg, key):
    ev = threading.Event()
    waiting[key] = [ev, None]
    send(msg)
    ev.wait(10)
    return waiting.pop(key)[1] or {"ok": False, "refused": "the kernel did not answer"}


def q(text):
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def on_call(msg):
    word, args = msg["word"], msg.get("args") or {}
    words = (args.get("words") or "").strip()
    if word == "reminder.add":
        if not words:
            return {"refused": "reminder.add needs words: reminder.add buy stamps"}
        return {"lines": [f"make kind=reminder text={q(words)} sees=me"]}
    if word == "reminder.note":
        return {"lines": [f"make kind=note text={q(words or 'a note')}"]}
    if word == "reminder.mine":
        r = ask({"t": "see", "use": msg["use"], "line": "rows reminder"}, msg["use"])
        rows = r.get("rows") or []
        return {"text": "\n".join(f"  {x['id']} · {x.get('text')}" for x in rows) or "no reminders", "rows": rows}
    return {"refused": f"reminders has no word {word}"}


def start_own():
    """On its own: one reminder for its person, made when it starts."""
    i = uuid.uuid4().hex[:8]
    state["own"] = ask({"t": "do", "id": i, "line": "make kind=reminder text=\"the module started\" sees=me"}, i)


def main():
    for line in sys.stdin:
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = msg.get("t")
        if t == "hello":
            state["hello"] = msg
            print(f"reminders: started for {msg.get('for')}", file=sys.stderr, flush=True)
            try:
                Path(msg["home"], "started.txt").write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
            except (KeyError, OSError):
                pass
            send({"t": "offer", "words": [
                {"word": "reminder.add", "kind": "do", "takes": "<words>",
                 "help": "reminder.add <words>: a reminder only you see."},
                {"word": "reminder.note", "kind": "do", "takes": "<words>",
                 "help": "reminder.note <words>: try to make a note (this module may make only reminders)."},
                {"word": "reminder.mine", "kind": "see", "takes": "",
                 "help": "reminder.mine: your reminders."}]})
            threading.Thread(target=start_own, daemon=True).start()
        elif t in ("rows", "done") and (msg.get("id") in waiting or msg.get("use") in waiting):
            slot = waiting[msg.get("id") if msg.get("id") in waiting else msg.get("use")]
            slot[1] = msg
            slot[0].set()
        elif t == "done":
            state["done"].append({k: msg.get(k) for k in ("ok", "record", "made", "refused")})
        elif t == "call":
            def answer(m=msg):
                send(dict(on_call(m), t="answer", use=m["use"]))
            threading.Thread(target=answer, daemon=True).start()
        elif t == "happen":
            state["heard"].append([msg.get("word"), msg.get("target")])
        elif t == "status?":
            h = state["hello"] or {}
            send({"t": "status", "use": msg.get("use"), "doing": json.dumps({
                "id": h.get("id"), "owner": h.get("owner"), "for": h.get("for"), "home": h.get("home"),
                "own": state["own"], "done": state["done"], "heard": state["heard"]})})
        elif t == "off":
            return


if __name__ == "__main__":
    main()
