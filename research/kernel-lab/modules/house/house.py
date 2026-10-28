"""house: the module that runs the world's agents (MOVING-IN D3). Python, the kernel's module protocol (SHAPE 11).

An agent is a person in the world with a `house-agent` thing saying how it runs:
    make kind=house-agent name=JEFF person=<person> signer=jeff provider=claude model=claude-opus-5-5 reasoning=medium
         fallback_provider=codex fallback_model=gpt-6-astra soul=<thing> charter=<thing> speaks=text want=awake

It is woken only when addressed: a said line whose `to` names its person (an @name, or any line in a closed chat it is
in, such as the Conversation), a task card given to it (`who=` its name), or house.wake. Never by a timer. Each agent
keeps a durable cursor (the last record it was told about) in this module's home folder; the happenings stream is
in memory only, so at start the house catches up with `rows said` past the cursor.

The words answer at once and never wait on a model turn (the kernel gives a module word 10 s, modules.py:34):
    house.who                     who the house runs, and what each is doing         (see)
    house.wake <person> [words]   wake one now, with your words                      (do, outside the world)
    house.stop <person>           end its process; the next call starts it again     (do, outside the world)
    house.activity <person>       what it said and did outside any chat              (see)
    house.log <person>            its chat, its acts and its activity, as one log      (see)
What an agent is doing changing (idle to working, a new act) is announced as the happening house.doing about its
house-agent thing, so a painted page (apps/work) rereads; it is never recorded.

An agent acts through MCP (see, do, lines) with its own session, as itself. With speaks=text (the default), each text
block of its turn is said into the chat that woke it, as it, the moment it arrives, and its tool calls become small
receipts under that line (`acts`); thinking is never posted. Woken by no chat (a task, house.wake), its words and acts
go to its own activity record (house.activity) instead. speaks=say leaves the chat to its own `say` lines. What it is doing (asleep, idle, working) is not a fact: it goes to live.json (the desktop's live layer,
live.py), never into the log. Transcripts and state stay in <world>/modules/house/<name>/, outside git.

Off switch: off house (every agent's process ends with it).
"""
import json
import re
import os
import queue
import sys
import threading
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "window-lab" / "kernel-desktop"))
sys.path.insert(0, str(HERE.parents[2] / "text-desk-lab" / "notation"))
from modproto import Module, log            # noqa: E402
import transport as T                        # noqa: E402

try:
    from quota_policy import quota_error     # noqa: E402  the old desk's own rule: what counts as a used-up plan
except ImportError:                          # pragma: no cover
    def quota_error(detail):
        return "limit" in str(detail).lower() and "reset" in str(detail).lower()

PORT = os.environ.get("AGORA_KDESK_PORT", "8810")
URL = f"http://127.0.0.1:{PORT}"
FAKE = os.environ.get("HOUSE_FAKE_MODEL")            # a scripted model's URL, for hidden tests (fake_model.py)
TASK_KINDS = ("taskboard-task", "task")
MESSAGE_WORDS = ("say",)


def now_s():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def it_is():
    return time.strftime("%a %d %b, %H:%M")


class Door:
    """The agent's own door session, for its spoken words (the house never speaks as the house in a chat)."""

    def __init__(self, token):
        self.token = token
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def post(self, route, line):
        req = urllib.request.Request(URL + route, json.dumps({"line": line}).encode("utf-8"),
                                     {"Content-Type": "application/json", "Authorization": "Bearer " + self.token})
        try:
            with self.opener.open(req, timeout=15) as r:
                return json.load(r)
        except Exception as exc:                     # noqa: BLE001
            return {"ok": False, "text": f"the door did not answer ({type(exc).__name__})"}


def quoted(text):
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


class Agent:
    def __init__(self, house, cfg):
        self.house, self.cfg = house, cfg
        self.name = cfg.get("name") or cfg["person"]
        self.dir = house.home / self.name.lower()
        self.dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.dir / "state.json"
        try:
            self.state = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.state = {}
        self.lock = threading.RLock()
        self.events = queue.Queue()
        self.child = None
        self.busy = False
        self.inbox = []                   # what is waiting to be said to it: {text, chat, record, at_s}
        self.turn = {}                    # the turn in progress: its chat, when it was woken, its first words
        threading.Thread(target=self._loop, daemon=True, name=f"agent-{self.name}").start()

    # ---- persistence
    def save(self):
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, indent=1, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.state_path)

    def log(self, kind, data):
        try:
            with (self.dir / "transcript.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps({"at": now_s(), "kind": kind, "data": data}, ensure_ascii=False) + "\n")
        except OSError:
            pass

    @property
    def person(self):
        return self.cfg["person"]

    def provider(self):
        """The provider in use: the fallback while the preferred one's plan is used up (quota_policy's rule)."""
        if self.state.get("on_fallback") and self.cfg.get("fallback_provider"):
            return (self.cfg["fallback_provider"], self.cfg.get("fallback_model", ""),
                    self.cfg.get("fallback_reasoning") or self.cfg.get("reasoning", "medium"))
        return self.cfg.get("provider", "claude"), self.cfg.get("model", "claude-opus-5-5"), self.cfg.get("reasoning", "medium")

    def doing(self):
        if self.cfg.get("want", "awake") == "asleep":
            return "asleep"
        if self.state.get("error") and not self.busy:
            return "error"
        if self.busy:
            return "working"
        return "idle" if self.child and self.child.alive() else "resting"

    # ---- the process
    def token_file(self):
        return self.dir / "token"

    def start(self):
        """Start its process (no turn yet: a warm process makes the first answer fast)."""
        provider, model, effort = self.provider()
        token = self.house.token_for(self.cfg.get("signer") or self.name.lower())
        if not token:
            raise RuntimeError(f"no door session for {self.name} (signer {self.cfg.get('signer')})")
        self.token_file().write_text(token, encoding="utf-8")
        self.door = Door(token)
        charter = self.house.charter_text(self.cfg.get("charter"))
        (self.dir / "charter.txt").write_text(charter, encoding="utf-8")
        mcp = T.mcp_config(URL, self.token_file(), self.dir / "mcp.json")
        session = self.state.get("session") if self.state.get("session_provider") == provider else None
        if provider == "claude":
            hook = T.compact_hook(URL, self.token_file(), self.cfg.get("charter"), self.cfg.get("id"))
            cmd = T.claude_cmd(T.find_claude(), model, effort, charter, mcp, hook, session)
            env = T.clean_env(self.house.compact_at(), FAKE)
        elif provider == "codex":
            cmd = T.codex_cmd(model, effort, self.dir / "charter.txt", mcp, session,
                              context={"url": URL, "token_file": str(self.token_file()),
                                       "charter": self.cfg.get("charter"), "agent": self.cfg.get("id")})
            env = dict(os.environ)
        else:
            raise RuntimeError(f"{self.name}: unknown provider {provider}")
        if not session:
            self.state["welcome_due"] = "a fresh conversation"
        self.state.update(session_provider=provider, session_model=model, session_reasoning=effort)
        self.state.pop("error", None)
        self.save()
        self.child = T.Child(cmd, self.dir, env, self.events, self.log)
        self.log("start", {"provider": provider, "model": model, "effort": effort, "resume": bool(session),
                           "pid": self.child.proc.pid})
        self.house.publish()

    def stop(self, why="stopped"):
        with self.lock:
            if self.child:
                self.child.stop()
            self.child, self.busy = None, False
            self.log("stop", why)
        self.house.publish()

    # ---- waking
    def wake(self, text, chat=None, record=None):
        """Something addressed to it. Said now if it is free, else at the end of its turn. Never blocks."""
        with self.lock:
            self.inbox.append({"text": text, "chat": chat, "record": record, "at": time.time()})
            if record:
                self.state["cursor"] = max(int(self.state.get("cursor", 0)), int(record))
                self.save()
            if not self.busy:
                self._begin()

    def _begin(self):
        if self.cfg.get("want", "awake") == "asleep" or not self.inbox:
            return
        try:
            if not (self.child and self.child.alive()):
                self.start()
        except Exception as exc:                      # noqa: BLE001
            self.state["error"] = f"could not start: {exc}"
            self.save()
            self.log("error", self.state["error"])
            self.house.publish()
            return
        items, self.inbox = self.inbox, []
        chats = [i["chat"] for i in items if i.get("chat")]
        parts = []
        if self.state.pop("welcome_due", None):
            parts.append(self.house.welcome(self))
        context = self.house.next_steps(self)
        if context:
            parts.append(context)
        parts.append(f"~ it is {it_is()}")
        parts += [i["text"] for i in items]
        text = "\n\n".join(parts)
        self.turn = {"chat": chats[-1] if chats else None, "woken": min(i["at"] for i in items), "first": None,
                     "receipts": [], "line": None, "woken_by": items[-1]["text"].splitlines()[0][:160]}
        if self.child.send(text):
            self.busy = True
            if context:
                self.state["next_steps_context"] = context
            self.state.pop("next_steps_queued", None)
            self.state["last_sent"] = text[-4000:]
            self.log("sent", text)
        else:
            self.inbox = items + self.inbox
        self.save()
        self.house.publish()

    # ---- what the process says
    def _loop(self):
        while True:
            ev = self.events.get()
            try:
                self._event(ev)
            except Exception as exc:                  # noqa: BLE001  one bad event never stops the agent
                log(f"house: {self.name}: {ev.get('e')} failed: {exc!r}")

    def _event(self, ev):
        e = ev["e"]
        if e == "init":
            with self.lock:
                self.state["session"] = ev["session"]
                self.save()
        elif e == "compacted":
            with self.lock:
                self.state["welcome_due"] = "the conversation was compacted"
                self.state["compactions"] = self.state.get("compactions", 0) + 1
                self.save()
                # Claude's read-only hook reinjects within this turn. The shared
                # continuation also covers transports without a SessionStart hook.
                if self.cfg.get("next_steps") == "on":
                    self.wake("~ the conversation was compacted; reconcile your current next steps.")
        elif e == "text":
            self._spoke(ev["text"])
        elif e == "tool":
            lines = ev["input"].get("lines") or [ev["input"].get("line", "")]
            self.state["last_acts"] = [str(x)[:120] for x in lines][-6:]
            name = ev["name"].rsplit("__", 1)[-1]
            receipt = ("" if name == "lines" else name + ": ") + " · ".join(str(x)[:80] for x in lines)
            self.turn.setdefault("receipts", []).append(receipt)
            self._receipts()
            self.house.publish()
        elif e == "toolresult":
            if ev.get("refused") and self.turn.get("receipts"):
                self.turn["receipts"][-1] += f" ({ev['refused']} refused)"
                self._receipts()
        elif e == "result":
            left = self.turn.get("receipts") or []
            if left and not self.turn.get("line") and self.turn.get("chat"):     # with no chat, each was kept as it came
                self.activity("acts", "\n".join(left))
            with self.lock:
                self.busy = False
                if ev["ok"]:
                    self.state["turns"] = self.state.get("turns", 0) + 1
                    self.state["last_turn"] = now_s()
                    self.state.pop("error", None)
                elif quota_error(ev["detail"]) and self.cfg.get("fallback_provider") and not self.state.get("on_fallback"):
                    # its plan is used up: the fallback takes over with a fresh conversation, and what it was told
                    # is said again there (quota_policy: only a verified limit switches, never an auth failure)
                    self.log("quota", ev["detail"])
                    self.state.update(on_fallback=now_s(), quota=ev["detail"][:200])
                    self.inbox.insert(0, {"text": "~ (said again: your other model's plan ran out mid-turn)\n"
                                                  + self.state.get("last_sent", ""), "chat": self.turn.get("chat"),
                                          "at": self.turn.get("woken", time.time())})
                    self.stop("quota")
                else:
                    self.state["error"] = ev["detail"][:300] or "the turn failed"
                    self.log("error", self.state["error"])
                self.save()
                if self.inbox:
                    self._begin()
            self.house.publish()
        elif e == "exit":
            with self.lock:
                self.busy = False
                self.child = None
                self.log("exit", ev.get("code"))
                if ev.get("code"):
                    tail = ""
                    try:
                        tail = (self.dir / "stderr.log").read_text(encoding="utf-8", errors="replace")[-1500:]
                    except OSError:
                        pass
                    if "No conversation found" in tail:
                        self.state.pop("session", None)       # its conversation is gone: the next start is fresh
                    self.state["error"] = f"its process ended ({ev.get('code')})"
                self.save()
            self.house.publish()

    def _spoke(self, text):
        if self.turn.get("first") is None:
            ms = int((time.time() - self.turn.get("woken", time.time())) * 1000)
            self.turn["first"] = ms
            fw = self.state.setdefault("first_words_ms", [])
            fw.append(ms)
            del fw[:-20]
            self.save()
        chat = self.turn.get("chat")
        if self.cfg.get("speaks", "text") == "text" and chat:
            # one text block, one line, the moment it arrives; acts done before any line of this turn go under it
            # receipts already under the previous line stay there; only those made before any line come with this one
            early = [] if self.turn.get("line") else self.turn.get("receipts", [])
            acts = f" acts={quoted(chr(10).join(early))}" if early else ""
            out = self.door.post("/do", f"say {chat} text={quoted(text.strip())}{acts}")
            if out.get("ok") and out.get("made"):
                self.turn["line"], self.turn["receipts"] = out["made"][0], []
            else:
                self.log("unsaid", out.get("text"))
        else:
            # woken by no chat (a task, house.wake), or speaks=say: his own activity record, never a chat
            self.activity("text", text)

    def _receipts(self):
        """His tool calls since his last line, as small receipts under it (`acts`). Before any line, or with no chat,
        they wait for the next line, or go to his activity record when the turn ends."""
        line, receipts = self.turn.get("line"), self.turn.get("receipts") or []
        if line and receipts and self.cfg.get("speaks", "text") == "text":
            out = self.door.post("/do", f"look {line}; set {line} acts={quoted(chr(10).join(receipts))}")
            if not out.get("ok"):
                self.log("receipt", out.get("text"))
        elif receipts and not self.turn.get("chat"):
            self.activity("acts", receipts[-1])

    def activity(self, what, text):
        """His own record of what he did and said outside any chat (house.activity reads it; the work overview
        will). Beside the house's state, never in the world's log."""
        entry = {"at": now_s(), "what": what, "text": text, "woken_by": self.turn.get("woken_by", "")}
        try:
            with (self.dir / "activity.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            pass
        self.log("activity", entry)

    def recent_activity(self, n=10):
        try:
            rows = (self.dir / "activity.jsonl").read_text(encoding="utf-8").splitlines()[-n:]
            return [json.loads(r) for r in rows if r.strip()]
        except (OSError, ValueError):
            return []


class House:
    def __init__(self):
        self.m = Module(offer=OFFER, on_call=self.call, on_happen=self.happen, on_status=self.status,
                        on_hello=self.hello, on_off=self.off)
        self.agents = {}                  # person id -> Agent
        self.home = None
        self.chat_names = {}
        self.ready = threading.Event()
        self.builders = None
        self.builder_url = URL

    # ---- start
    def hello(self, msg):
        self.home = Path(msg.get("home") or HERE / "state")
        self.world = self.home.parent.parent
        threading.Thread(target=self.settle, daemon=True, name="house-settle").start()

    def settle(self):
        self.m.ready.wait(10)
        time.sleep(0.2)                   # the kernel publishes our words first
        self.load()
        from builders import Builders
        self.builders = Builders(self)
        for a in self.agents.values():
            self.catch_up(a)
            if a.cfg.get("want", "awake") == "awake" and not (a.child and a.child.alive()):
                try:
                    a.start()             # warm, no turn: the first line to it is answered at model speed
                except Exception as exc:  # noqa: BLE001
                    a.state["error"] = f"could not start: {exc}"
                    a.save()
        self.ready.set()
        self.task_changes()
        threading.Thread(target=self.ticker, daemon=True, name="house-live").start()

    def load(self):
        rows = self.m.see("rows house-agent").get("rows") or []
        seen = set()
        for r in rows:
            p = r.get("person")
            if not p:
                continue
            seen.add(p)
            if p in self.agents:
                self.agents[p].cfg = r
            else:
                self.agents[p] = Agent(self, r)
        for p in [p for p in self.agents if p not in seen]:
            self.agents.pop(p).stop("its house-agent thing is gone")

    def token_for(self, signer):
        try:
            sessions = json.loads((self.world / "keep" / "sessions.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return next((t for t, v in sessions.items() if v.get("signer") == signer), None)

    def compact_at(self):
        rows = self.m.see("rows house-settings").get("rows") or []
        return (rows[0].get("compact_at") if rows else None) or "400k"

    def charter_text(self, cid):
        if not cid:
            return "charter: none named on your house-agent thing; tell Alex."
        rows = self.m.see(f"look {cid}").get("rows") or [{}]
        text = str(rows[0].get("text") or "").strip()
        return ("## Alex's standing rules (look " + cid + " is the live one)\n\n" + text) if text else \
            f"charter: not read: {cid} is empty or gone; tell Alex."

    def welcome(self, a):
        cfg = a.cfg
        soul = ""
        if cfg.get("soul"):
            rows = self.m.see(f"look {cfg['soul']}").get("rows") or [{}]
            soul = str(rows[0].get("text") or "").strip()
        own = cfg.get("welcome") or (
            f"You are {a.name} ({a.person}), a person in Alex's desktop world (the kernel, Lines). Nothing here runs on "
            "a timer: you are woken when someone addresses you, and each message from the house says what reached "
            "you. Your tools are see, do and lines; each takes Lines (help, rows guide and help <word> teach them); "
            "lines takes a list and routes each line, and a refused line refuses only itself. "
            + ("Each block of your words in a turn is said, as you, into the chat that woke you the moment you write "
               "it, with your tool calls as small receipts under it, so write to the person, briefly, like texting; "
               "use say <chat> only to speak somewhere else. Woken by no chat (a task, house.wake), your words go to "
               "your own activity record, not to any chat. "
               if cfg.get("speaks", "text") == "text" else
               "Your words in a turn are your own thinking; say <chat> <words> is how anyone hears you. ")
            + "rows chat lists the chats; chat <chat> reads one.")
        return own + (f"\n\n# Your soul ({cfg['soul']}, yours to keep)\n\n{soul}" if soul else "")

    def next_steps(self, a):
        if a.cfg.get("next_steps") != "on":
            return ""
        out = a.door.post("/see", f"rows nextsteps:{a.person}")
        if not out.get("ok"):
            return "Next steps unavailable; read rows nextsteps:" + a.person + " before continuing task work."
        return out.get("text", "")

    def task_changes(self):
        """Event-driven reread, through each resident's own visibility fence."""
        for a in self.agents.values():
            if a.cfg.get("next_steps") != "on" or not getattr(a, "door", None):
                continue
            with a.lock:
                context = self.next_steps(a)
                fresh = a.state.get("welcome_due") and not a.busy
                if context and (fresh or context != a.state.get("next_steps_context")) and context != a.state.get("next_steps_queued"):
                    a.state["next_steps_queued"] = context
                    a.wake("~ your task projection changed; reconcile current next actions.")

    # ---- catching up
    def catch_up(self, a):
        """Lines addressed to it while the house was away (past its cursor), as one wake."""
        cursor = int(a.state.get("cursor", 0))
        got = []
        for r in self.m.see("rows said").get("rows") or []:
            rev = int(r.get("rev") or 0)
            if rev > cursor and a.person in str(r.get("to") or "").split() and r.get("made_by") != a.person \
                    and r.get("for") != a.person:
                got.append((rev, r))
        if not got:
            return
        got.sort(key=lambda x: x[0])
        text = "~ for you while the house was away:\n" + "\n".join(
            self.line_text(r.get("id"), dict(r, by_name=r.get("by")), r.get("chat")) for _, r in got)
        a.wake(text, chat=got[-1][1].get("chat"), record=got[-1][0])

    def chat_name(self, c):
        if c not in self.chat_names:
            rows = self.m.see(f"look {c}").get("rows") or [{}]
            self.chat_names[c] = rows[0].get("name") or c
        return self.chat_names[c]

    def line_text(self, sid, row, chat):
        who = row.get("by_name") or row.get("speaker") or ""
        return f"~ {who or 'someone'} in {self.chat_name(chat)} ({chat}, line {sid}): {row.get('text', '')}"

    # ---- hearing
    def happen(self, msg):
        if not self.ready.wait(15):
            return
        word = msg.get("word")
        self.builders.hear(msg)
        if word in MESSAGE_WORDS and msg.get("said"):
            to = [p for p in msg.get("to") or [] if p in self.agents and p != msg.get("by_id")]
            if not to:
                return
            rows = self.m.see(f"look {msg['said']}").get("rows") or [{}]
            r = dict(rows[0], by_name=msg.get("by"))
            for p in to:
                self.agents[p].wake(self.line_text(msg["said"], r, r.get("chat")), chat=r.get("chat"),
                                    record=msg.get("record"))
            return
        target = msg.get("target")
        if word in ("make", "set", "undo") and target:
            rows = self.m.see(f"look {target}").get("rows") or [{}]
            kind = rows[0].get("kind")
            if kind in ("house-agent", "house-settings"):
                self.load()
                for a in self.agents.values():
                    if a.cfg.get("want") == "asleep" and a.child:
                        a.stop("want=asleep")
                    elif a.cfg.get("want", "awake") == "awake":
                        with a.lock:
                            if a.inbox and not a.busy:
                                a._begin()
                            elif not (a.child and a.child.alive()):
                                try:
                                    a.start()             # awake again: warm, no turn
                                except Exception as exc:  # noqa: BLE001
                                    a.state["error"] = f"could not start: {exc}"
                                    a.save()
                self.task_changes()
                self.publish()
                return
        if word not in ("house.doing", "say") and (target or word == "undo"):
            self.task_changes()
        if target and (word in ("make", "set") or word.startswith("task.")) and "who=" in str(msg.get("text", "")):
            rows = self.m.see(f"look {target}").get("rows") or [{}]
            r = rows[0]
            if r.get("kind") in TASK_KINDS:
                for a in self.agents.values():
                    if a.cfg.get("next_steps") != "on" and str(r.get("who", "")).casefold() == a.name.casefold():
                        a.wake(f"~ {msg.get('by') or 'someone'} gave you a task: {r.get('title') or target} ({target}); "
                               f"look {target}", record=msg.get("record"))

    # ---- words
    def call(self, msg):
        word, args = msg.get("word"), msg.get("args") or {}
        if not self.ready.wait(5):
            return {"refused": "the house is still starting; try again in a moment"}
        if word == "house.build":
            return self.builders.start(msg)
        if word == "house.retry":
            return self.builders.retry(msg)
        if word == "house.tell":
            return self.builders.tell(msg)
        if word == "house.review":
            return self.builders.request_review(msg)
        if word == "house.land":
            return self.builders.land(msg)
        if word in ("house.log", "house.activity") and args.get("target") in self.builders.states:
            state = self.builders.states[args["target"]]
            if not self.m.see("look " + (state.get("chat") or state["task"]), use=msg.get("use")).get("rows"):
                return {"refused": "this worker log belongs to its requester"}
            return self.builders.log(args["target"])
        if word == "house.who":
            rows = [self.row(a) for a in self.agents.values()] + self.builders.rows(msg)
            text = (f"the house runs {len(rows)} agent{'' if len(rows) == 1 else 's'}:\n" + "\n".join(
                f"  {r['name']} ({r['person']}) · {r['doing']} · {r['provider']} {r['model']} {r['reasoning']} · "
                f"{r['turns']} turns" + (f" · first words {r['first_words_ms']} ms" if r['first_words_ms'] else "")
                + (f" · {r['error']}" if r['error'] else "") for r in rows)) if rows else \
                "the house runs no agents yet: make kind=house-agent person=<person> … adds one"
            return {"text": text, "rows": rows}
        a = self.agents.get(args.get("target") or "")
        if word == "house.activity" and a is not None:
            n = str((args.get("kv") or {}).get("limit", "10"))
            rows = a.recent_activity(min(int(n), 100) if n.isdigit() else 10)
            for r in rows:
                r["line"] = f"{r['at'][11:16]}  {r['what']:<5} {' '.join(str(r['text']).split())[:240]}"
            return {"text": (f"{a.name}'s activity outside any chat, latest last:\n" + "\n".join(
                f"  {r['at'][11:16]} {r['what']}: {r['text'][:300]}" for r in rows)) if rows else
                f"{a.name} has done nothing outside a chat yet", "rows": rows}
        if word == "house.log" and a is not None:
            n = str((args.get("kv") or {}).get("limit", "60"))
            log = self.log_of(a, min(int(n), 300) if n.isdigit() else 60)
            return {"text": "\n".join(" ".join(x.split("\t")) for x in log) or f"{a.name} has no log yet",
                    "rows": [{"person": a.person, "name": a.name, "log": "\n".join(log), "lines": len(log)}]}
        if a is None:
            return {"refused": f"{word} <person>: the house runs {', '.join(x.name for x in self.agents.values()) or 'no one'}"}
        if word == "house.wake":
            by = (msg.get("caller") or {}).get("name") or "someone"
            words = (args.get("words") or "").strip()
            a.wake(f"~ {by} woke you (house.wake)" + (f": {words}" if words else ""))
            return {"text": f"{a.name} is {'woken' if a.busy else 'told'}; it answers in its own time", "external": True}
        if word == "house.stop":
            a.stop("house.stop")
            return {"text": f"{a.name}'s process ended; the next line to it starts it again", "external": True}
        return {"refused": f"the house has no word {word}"}

    def log_of(self, a, n=60):
        """An agent's log, oldest first: its chat's lines and its own lines anywhere, the receipts under its lines, what
        it did outside any chat, and what it is doing now. Lines `kind<TAB>HH:MM<TAB>who<TAB>text` (the console
        component's format). Read fresh each time; the house keeps no copy."""
        import calendar
        names = {r["id"]: r.get("name") or r["id"] for r in self.m.see("rows person").get("rows") or []}
        chat = a.cfg.get("chat")
        entries = []

        def local(iso):
            try:
                return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(calendar.timegm(
                    time.strptime(iso, "%Y-%m-%dT%H:%M:%SZ"))))
            except (TypeError, ValueError):
                return iso or ""
        for r in self.m.see("rows said").get("rows") or []:
            speaker = r.get("for") or r.get("made_by")
            if not (r.get("chat") == chat or speaker == a.person or a.person in str(r.get("to") or "").split()):
                continue
            at = local(r.get("made"))
            kind = "said" if speaker == a.person else "heard"
            where = "" if r.get("chat") == chat else f"[{self.chat_name(r.get('chat'))}] "
            text = " ".join(str(r.get("text") or "").split())
            entries.append((at, kind, names.get(speaker, r.get("by") or ""), where + text))
            for act in str(r.get("acts") or "").splitlines():
                if act.strip():
                    entries.append((at, "act", "", act.strip()))
        for e in a.recent_activity(200):
            why = re.sub(r"\s*\([a-z]+\d+[^)]*\).*$", "", " ".join(str(e.get("woken_by") or "").split()).lstrip("~ "))
            why = f"[outside any chat · {why[:70]}{'…' if len(why) > 70 else ''}] " if why else "[outside any chat] "
            for i, line in enumerate(str(e.get("text") or "").splitlines() or [""]):
                acts = e.get("what") == "acts"
                entries.append((e.get("at", ""), "act" if acts else "own", a.name if i == 0 and not acts else "",
                                ("" if acts or i else why) + " ".join(line.split())))
        if a.busy:
            entries.append((now_s(), "now", a.name, "working · " + "; ".join(a.state.get("last_acts", [])[-3:])
                            if a.state.get("last_acts") else "working · thinking"))
        if a.state.get("error") and not a.busy:
            entries.append((now_s(), "error", a.name, a.state["error"]))
        entries = sorted(enumerate(entries), key=lambda ie: (ie[1][0], ie[0]))[-n:]
        return [f"{kind}\t{at[11:16]}\t{who}\t{text}" for _, (at, kind, who, text) in entries]

    def row(self, a):
        provider, model, effort = a.provider()
        fw = a.state.get("first_words_ms") or []
        doing, acts = a.doing(), a.state.get("last_acts", [])
        last = a.state.get("last_turn", "")
        now = {"working": "; ".join(acts[-2:]) or "thinking", "error": a.state.get("error", ""),
               "asleep": "asleep (want=asleep)"}.get(doing) or (f"last turn {last[11:16]}" if last else "not yet woken")
        colour = {"working": "sage", "error": "rose", "idle": "sky"}.get(doing, "paper")     # the card's, in apps/work
        return {"name": a.name, "person": a.person, "id": a.cfg.get("id", ""), "doing": doing, "now": now,
                "colour": colour,
                "role": a.cfg.get("role", "agent"), "chat": a.cfg.get("chat", ""), "task": a.cfg.get("task", ""),
                "provider": provider, "model": model, "reasoning": effort, "turns": a.state.get("turns", 0),
                "last_turn": last, "first_words_ms": fw[-1] if fw else None,
                "first_words": f"{fw[-1] / 1000:.1f} s" if fw else "", "error": a.state.get("error", ""),
                "acts": acts, "acts_text": "\n".join(acts), "waiting": len(a.inbox)}

    def status(self):
        return "; ".join(f"{a.name} {a.doing()}" for a in self.agents.values()) or "no agents"

    # ---- what it is doing, for the painter (live.py), never recorded
    def publish(self):
        if not self.home:
            return
        live = {"at": time.time()}
        said = getattr(self, "said_doing", {})
        self.said_doing = said
        for a in self.agents.values():
            r = self.row(a)
            if said.get(a.person) != (r["doing"], r["now"]) and a.cfg.get("id"):
                # what it is doing changed: a happening (delivered, never recorded), so painted pages reread
                said[a.person] = (r["doing"], r["now"])
                self.m.happen("house.doing", a.cfg["id"], f"{a.name} {r['doing']}")
            live[f"house:{a.name.lower()}"] = {"value": r["doing"], "detail": "; ".join(r["acts"][-2:]),
                                               "doing": r["doing"]}
        tmp = self.home / "live.tmp"
        try:
            tmp.write_text(json.dumps(live), encoding="utf-8")
            os.replace(tmp, self.home / "live.json")
        except OSError:
            pass

    def ticker(self):
        while not self.m.closed.is_set():
            self.publish()
            time.sleep(5)

    def off(self):
        if self.builders:
            self.builders.off()
        for a in list(self.agents.values()):
            a.stop("off house")
        os._exit(0)


OFFER = [
    {"word": "house.retry", "kind": "do", "takes": "<id>", "undo": "external", "may": "stewards",
     "help": "house.retry <task>: retry a proven terminal startup failure before any model thread. Preserves its existing claim and worktree; refuses uncertain or changed work."},
    {"word": "house.tell", "kind": "do", "takes": "<id> <words>", "undo": "external", "may": "stewards",
     "help": "house.tell <task> <words>: retain a follow-up for your active or received builder, continuing the same Codex thread. Held, uncertain, reviewed and landed work does not restart."},
    {"word": "house.build", "kind": "do", "takes": "<id>", "undo": "external", "may": "stewards",
     "help": "house.build <task>: claim a ready task and start an authenticated Codex builder asynchronously, two at most. Uses your existing agent session; never creates credentials. Result receipt is not task completion."},
    {"word": "house.review", "kind": "do", "takes": "<id>", "undo": "external", "may": "stewards",
     "help": "house.review <task>: independently check a received committed result against current main, including hidden desktop checks. Does not land or close it."},
    {"word": "house.land", "kind": "do", "takes": "<id>", "undo": "external", "may": "stewards",
     "help": "house.land <task>: publish the exact reviewed source if main and ownership still match. Activation and owner verification remain separate."},
    {"word": "house.who", "kind": "see", "takes": "",
     "help": "house.who: the agents the house runs (JEFF and others), what each is doing (asleep, resting, idle, "
             "working), its model, its turns and how fast its last first words came."},
    {"word": "house.activity", "kind": "see", "takes": "<id> [limit=<n>]",
     "help": "house.activity <person> [limit=10]: what an agent said and did outside any chat (woken by a task or "
             "house.wake): its own record, latest last. In a chat, its words are lines there, its acts receipts under them."},
    {"word": "house.log", "kind": "see", "takes": "<id> [limit=<n>]",
     "help": "house.log <person> [limit=60]: one agent's log, oldest first: its chat's lines and its own lines anywhere, "
             "the receipts of what it did under them, its record outside any chat, and what it is doing now."},
    {"word": "house.wake", "kind": "do", "takes": "<id> [<words>]", "undo": "external", "may": "members",
     "help": "house.wake <person> [words]: wake an agent now with your words. Usually you need not: saying @name in a "
             "chat, or any line in its closed chat, wakes it. It answers in its own time."},
    {"word": "house.stop", "kind": "do", "takes": "<id>", "undo": "external", "may": "stewards",
     "help": "house.stop <person>: end an agent's process now (mid-turn too). The next line to it starts it again; "
             "set its house-agent want=asleep to keep it asleep."},
]


def main():
    h = House()
    t = threading.Thread(target=h.m._read, daemon=True)
    t.start()
    h.m.closed.wait()
    h.off()


if __name__ == "__main__":
    main()
