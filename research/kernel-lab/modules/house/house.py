"""EDITING A MODULE (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
A module is a seam to something outside the kernel (a model provider, git, Twitch, the media session, a map server) and
turns it into world facts and words. What the world does with them (who is told, when, in what words, how it looks)
belongs in rules, lenses and this module's settings thing, read at each use. Names (JEFF, Alex), ids (dk...), models,
counts, timeouts and message text in this file are debt: move them to settings when you touch them, and never add more.

house: the module that runs the world's agents (MOVING-IN D3). Python, the kernel's module protocol (SHAPE 11).

An agent is a person in the world with a `house-agent` thing saying how it runs:
    make kind=house-agent name=JEFF person=<person> signer=jeff provider=claude model=claude-opus-5-5 reasoning=medium
         fallback_provider=codex fallback_model=gpt-6-astra soul=<thing> charter=<thing> speaks=text want=awake
    Its system prompt is prompt=<thing> (its own, optional) followed by charter=<thing> (the standing rules), both read
    again at every wake: an edit to either restarts its process under the new prompt, keeping the conversation.
    wake_policy=addressed skips warm starts and task-change wakes while retaining next_steps=on context.
    Chat addresses and explicit house.wake still reach it; compaction continues its addressed conversation.

It is woken only when addressed: a said line whose `to` names its person (an @name, or any line in a closed chat it is
in, such as the Conversation), a task card given to it (`who=` its name), or house.wake. Never by a timer. Each agent
keeps a durable cursor (the last record it was told about) in this module's home folder; the happenings stream is
in memory only, so at start the house catches up with `rows said` past the cursor.

The words answer at once and never wait on a model turn (the kernel gives a module word 10 s, modules.py:34):
    house.who                     who the house runs, and what each is doing         (see)
    house.wake <person> [words]   wake one now, with your words                      (do, outside the world)
    house.stop <person>           end its process; the next call starts it again     (do, outside the world)
    house.refresh <person>        replace its conversation, retaining its history   (do, stewards)
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
import hashlib
import json
import re
import os
import subprocess
import queue
import sys
import threading
import time
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "window-lab" / "kernel-desktop"))
sys.path.insert(0, str(HERE.parents[2] / "text-desk-lab" / "notation"))
from modproto import Module, log            # noqa: E402
import transport as T                        # noqa: E402
import manager as BM                         # noqa: E402
from messages import message
import work_overview                         # noqa: E402
import task_board                            # noqa: E402

try:
    from quota_policy import quota_error     # noqa: E402  the old desk's own rule: what counts as a used-up plan
except ImportError:                          # pragma: no cover
    def quota_error(detail):
        return "limit" in str(detail).lower() and "reset" in str(detail).lower()

PORT = os.environ.get("AGORA_KDESK_PORT", "8810")
URL = f"http://127.0.0.1:{PORT}"
FAKE = os.environ.get("HOUSE_FAKE_MODEL")            # a scripted model's URL, for hidden tests (fake_model.py)
TASK_KINDS = ("taskboard-task", "task")
TASK_NEEDS = "kind=" + "|".join(TASK_KINDS)        # the shape house.build and its kin read (kernel kinds.py)
MESSAGE_WORDS = ("say",)


def now_s():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


RESETS = re.compile(r"resets\s+(?:(?P<mon>[A-Za-z]{3})[a-z]*\s+(?P<day>\d{1,2}),?\s+)?(?P<h>\d{1,2})(?::(?P<min>\d{2}))?"
                    r"\s*(?P<ap>am|pm)(?:\s*\((?P<tz>[^)]+)\))?", re.I)


def plan_resets_at(detail, since):
    """When a used-up plan comes back, from the provider's own words ("resets 6:30pm (America/Los_Angeles)",
    "resets Nov 6, 3pm"): the first such moment after `since` (epoch seconds). None when the words don't say."""
    import datetime as dt
    m = RESETS.search(str(detail or ""))
    if not m:
        return None
    tz = None
    if m["tz"]:
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo(m["tz"].strip())
        except Exception:                             # noqa: BLE001  no tz data here: the desktop's own clock
            tz = None
    start = dt.datetime.fromtimestamp(since, tz) if tz else dt.datetime.fromtimestamp(since)
    hour = int(m["h"]) % 12 + (12 if m["ap"].lower() == "pm" else 0)
    at = start.replace(hour=hour, minute=int(m["min"] or 0), second=0, microsecond=0)
    if m["mon"]:
        try:
            month = time.strptime(m["mon"][:3].title(), "%b").tm_mon
            at = at.replace(month=month, day=int(m["day"]))
        except ValueError:
            return None
        if at <= start:
            at = at.replace(year=at.year + 1)
    elif at <= start:
        at += dt.timedelta(days=1)
    return at.timestamp()


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
        """The provider in use: the fallback while the preferred one's plan is used up (quota_policy's rule).
        Alex, 4 Nov: the fallback holds only for the model whose plan ran out. Choosing another model on the
        house-agent thing ends it (JEFF sat on the fallback from 28 Oct to 4 Nov because nothing ever cleared it)."""
        if self.state.get("on_fallback") and self.state.get("fallback_from") != [
                self.cfg.get("provider", "claude"), self.cfg.get("model", "")]:
            self.state.pop("on_fallback", None)
            self.state.pop("fallback_from", None)
        # 5 Nov: and it ends when the plan comes back, at the reset the provider named (JEFF sat on Codex 15 hours
        # past a 6:30pm reset because only a model change cleared it)
        if self.state.get("on_fallback"):
            until = self.state.get("fallback_until")
            if until is None:
                try:
                    since = time.mktime(time.strptime(self.state["on_fallback"], "%Y-%m-%dT%H:%M:%S"))
                except (ValueError, TypeError):
                    since = time.time()
                until = plan_resets_at(self.state.get("quota"), since)
                if until is not None:
                    self.state["fallback_until"] = until
            if until is not None and time.time() >= until:
                self.log("fallback", "its plan has reset: back to " + " ".join(self.state.get("fallback_from") or []))
                for k in ("on_fallback", "fallback_from", "fallback_until"):
                    self.state.pop(k, None)
        if self.state.get("on_fallback") and self.cfg.get("fallback_provider"):
            return (self.cfg["fallback_provider"], self.cfg.get("fallback_model", ""),
                    self.cfg.get("fallback_reasoning") or self.cfg.get("reasoning", "medium"))
        return self.cfg.get("provider", "claude"), self.cfg.get("model", "claude-opus-5-5"), self.cfg.get("reasoning", "medium")

    def doing(self):
        if getattr(self, "refreshing", False):
            return "refreshing"
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
        charter = self.house.system_text(self)
        self.state["system_sha"] = hashlib.sha256(charter.encode("utf-8")).hexdigest()
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

    def request_refresh(self):
        """Queue a replacement without making a Lines call wait for process shutdown."""
        if getattr(self, "refreshing", False):
            return False
        with self.lock:
            if getattr(self, "refreshing", False):
                return False
            self.refreshing = True
            threading.Thread(target=self.refresh, daemon=True, name=f"refresh-{self.name}").start()
        return True

    def refresh(self):
        """Keep the old state and append-only transcript; start without a resume id."""
        with self.lock:
            try:
                archive = self.dir / "conversations" / (uuid.uuid4().hex + ".json")
                archive.parent.mkdir(exist_ok=True)
                archive.write_text(json.dumps(self.state, indent=1, ensure_ascii=False), encoding="utf-8")
                if self.child:
                    self.child.stop()
                    if self.child.alive():
                        raise RuntimeError("the old process has not ended")
                self.child, self.busy, self.turn = None, False, {}
                # Only conversation context is reset. Cursors, counters, fallback state,
                # configuration and queued addresses retain their existing meaning.
                for key in ("session", "system_sha", "next_steps_context", "next_steps_queued",
                            "last_sent", "last_acts", "error"):
                    self.state.pop(key, None)
                self.state["welcome_due"] = "a fresh conversation"
                self.inbox = self.said_again(self.state.pop("in_flight", None)) + self.inbox
                self.state["paused"] = list(self.inbox)
                self.save()                         # durable before any replacement can start
                self.log("refresh", {"previous_state": str(archive.relative_to(self.dir))})
                self.house.mark_turn(self, None)
                self.refreshing = False
                if self.cfg.get("want", "awake") != "asleep":
                    if self.inbox:
                        self._begin()
                    else:
                        self.start()                # warm only; welcome/soul are read at the next wake
            except Exception as exc:                # noqa: BLE001  visible failure, never a silent lost request
                self.state["error"] = f"could not refresh: {exc}"
                self.save()
                self.log("error", self.state["error"])
            finally:
                self.refreshing = False
                self.house.publish()

    # ---- waking
    def wake(self, text, chat=None, record=None, card_notes=None, first_record=None):
        """Something addressed to it. Said now if it is free, else at the end of its turn. Never blocks."""
        with self.lock:
            item = {"text": text, "chat": chat, "record": record, "at": time.time()}
            if first_record is not None:
                item["first_record"] = first_record
            if card_notes:
                item["card_signal_notes"] = list(card_notes)
            self.inbox.append(item)
            # the cursor moves when a line is said to the model, not when it is queued (`_begin`), so a restart with
            # lines waiting finds them again in catch-up (security review round 2: queued chats were lost)
            if not self.busy:
                self._begin()

    def _begin(self):
        self.house.refresh_card_signals(self)
        if getattr(self, "refreshing", False) or self.cfg.get("want", "awake") == "asleep" or not self.inbox:
            return
        try:
            # its system prompt (prompt= and charter=) is read at each wake: an edit ends the old process, and the
            # conversation resumes under the new prompt (Alex, 4 Nov: he writes JEFF's prompt in Writing)
            if self.child and self.child.alive():
                text = self.house.system_text(self)
                sha, known = hashlib.sha256(text.encode("utf-8")).hexdigest(), self.state.get("system_sha")
                if known is None:                     # a process started before the prompt was fingerprinted
                    self.state["system_sha"] = sha
                elif sha != known:
                    self.log("restart", "its system prompt changed")
                    self.child.stop()
                    self.child = None
                elif self.state.get("session_provider") and                         self.provider()[:2] != (self.state["session_provider"], self.state.get("session_model")):
                    self.log("restart", "its model changed (a fallback began or ended)")
                    self.child.stop()
                    self.child = None
            if not (self.child and self.child.alive()):
                self.start()
        except Exception as exc:                      # noqa: BLE001
            self.state["error"] = f"could not start: {exc}"
            self.save()
            self.log("error", self.state["error"])
            self.house.publish()
            return
        # one turn answers one chat: its reply is said into that chat, so lines from another chat (a closed one) must
        # never be in the same turn (security review H1, 28 Oct: a Conversation secret was answered into Shop talk).
        # Items with no chat (a task, house.wake) are their own turn too. The rest wait; a turn's end begins the next.
        first = self.inbox[0].get("chat")
        items = [i for i in self.inbox if i.get("chat") == first]
        self.inbox = [i for i in self.inbox if i.get("chat") != first]
        # busy from the moment its lines leave the inbox: building the message takes seconds, and an empty inbox with
        # busy unset looked idle to the House's restart check (5 Nov: a restart then cut off JEFF's turn on Alex's line)
        self.busy = True
        record = next((i["record"] for i in reversed(items) if i.get("record")), None)
        if record:
            self.house.mark_turn(self, record)          # its acts this turn say because=r<record> in the log
        chats = [i["chat"] for i in items if i.get("chat")]
        parts = []
        fresh = self.state.pop("welcome_due", None)
        try:
            if fresh:
                parts.append(self.house.welcome(self))
            context = self.house.next_steps(self)
            # Alex, 5 Nov: the task list is not resent every turn, only in a fresh conversation or when it changed
            if context and (fresh or context != self.state.get("next_steps_context")):
                parts.append(context)
            parts.append(self.house.message("The time"))
            parts += [i["text"] for i in items]
            text = "\n\n".join(parts)
            self.turn = {"chat": chats[-1] if chats else None, "woken": min(i["at"] for i in items), "first": None,
                         "receipts": [], "line": None, "woken_by": items[-1]["text"].splitlines()[0][:160]}
            said = self.child.send(text)
        except Exception as exc:                      # noqa: BLE001  never left busy with nothing running
            said = False
            self.log("error", f"could not build its message: {exc!r}")
        if said:
            # what this turn was told, until it ends: a House restart in between says it again when it is back
            self.state["in_flight"] = [{k: i[k] for k in ("text", "chat", "record", "first_record", "at", "said_again")
                                        if k in i} for i in items]
            if "paused" in self.state:
                # Refresh persists the waiting inbox before replacing its process.
                # Retire only the messages this new process actually received.
                if self.inbox:
                    self.state["paused"] = list(self.inbox)
                else:
                    self.state.pop("paused", None)
            signals = {n for i in items for n in i.get("card_signal_notes", [])}
            if signals:
                self.state["card_signals_seen"] = sorted(set(self.state.get("card_signals_seen", [])) | signals)
            sent = [int(i["record"]) for i in items if i.get("record")]
            if sent:
                # at least once, never lost: past what was said, but not past a line still waiting in another chat
                # A catch-up packet spans several records: protect its oldest
                # line, even when its newest line follows the delivered note.
                waiting = [int(i.get("first_record") or i["record"]) for i in self.inbox if i.get("record")]
                upto = min(max(sent), min(waiting) - 1) if waiting else max(sent)
                self.state["cursor"] = max(int(self.state.get("cursor", 0)), upto)
                self.save()
            if context:
                self.state["next_steps_context"] = context
            self.state.pop("next_steps_queued", None)
            self.state["last_sent"] = text[-4000:]
            self.log("sent", text)
        else:
            self.busy = False
            self.inbox = items + self.inbox
            if fresh:
                self.state["welcome_due"] = fresh
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
        # Refresh and child replacement share this lock with the identity check.
        # Otherwise an event can pass the check, wait for refresh, then mutate its successor.
        with self.lock:
            self._handle_event(ev)

    def _handle_event(self, ev):
        e = ev["e"]
        source = ev.get("child")
        if source is not None and source is not self.child:
            # No late output, tool receipt, compaction or result from a replaced
            # process may speak into or change the fresh conversation.
            self.log("stale", {"e": e, "code": ev.get("code")})
            return
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
                    self.wake(self.house.message("After a compaction", charter=self.cfg.get("charter", "")))
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
            self.house.mark_turn(self, None)            # the turn is over: later acts answer nothing it was told
            left = self.turn.get("receipts") or []
            if left and not self.turn.get("line") and self.turn.get("chat"):     # with no chat, each was kept as it came
                self.activity("acts", "\n".join(left))
            with self.lock:
                self.busy = False
                if getattr(self.house, "stopping", False):
                    # the House is going off and cut this turn: in_flight stays, and the House says it again on return
                    self.save()
                    return
                self.state.pop("in_flight", None)
                if ev["ok"]:
                    self.state["turns"] = self.state.get("turns", 0) + 1
                    self.state["last_turn"] = now_s()
                    self.state.pop("error", None)
                elif quota_error(ev["detail"]) and self.cfg.get("fallback_provider") and not self.state.get("on_fallback"):
                    # its plan is used up: the fallback takes over with a fresh conversation, and what it was told
                    # is said again there (quota_policy: only a verified limit switches, never an auth failure)
                    self.log("quota", ev["detail"])
                    self.state.update(on_fallback=now_s(), quota=ev["detail"][:200],
                                      fallback_from=[self.cfg.get("provider", "claude"), self.cfg.get("model", "")])
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
            try:
                self.house.builders.owner_turn_ended(self.cfg.get("person"))
            except Exception as exc:                  # noqa: BLE001
                self.log("error", f"workers after turn: {exc!r}")
            self.house.publish()
        elif e == "exit":
            with self.lock:
                self.busy = False
                self.child = None
                self.log("exit", ev.get("code"))
                if ev.get("code") and not getattr(self.house, "stopping", False):
                    tail = ""
                    try:
                        tail = (self.dir / "stderr.log").read_text(encoding="utf-8", errors="replace")[-1500:]
                    except OSError:
                        pass
                    if "No conversation found" in tail:
                        self.state.pop("session", None)       # its conversation is gone: the next start is fresh
                    self.state["error"] = f"its process ended ({ev.get('code')})"
                if not getattr(self.house, "stopping", False) and self.state.get("in_flight"):
                    # it died mid-turn: what it was told is said again, once, when it is next free
                    self.inbox = self.said_again(self.state.pop("in_flight")) + self.inbox
                self.save()
            self.house.publish()

    def said_again(self, items):
        """Items a cut-off turn was told, to be said again with a note saying why. Once only: an item already said
        again is dropped, so a turn that always dies can't loop."""
        note = self.house.message("When a restart cut off your turn")
        out = []
        for i in items or []:
            if i.get("said_again"):
                self.log("dropped", {"why": "cut off twice", "text": str(i.get("text"))[:200]})
                continue
            out.append(dict(i, text=note + "\n" + str(i.get("text") or ""), said_again=True,
                            at=i.get("at") or time.time()))
        return out

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
    stopping = False                      # going off: cut turns are paused, not failed, and resume at the next start
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
            if a.cfg.get("wake_policy") != "addressed" and a.cfg.get("want", "awake") == "awake" and not (a.child and a.child.alive()):
                try:
                    a.start()             # warm, no turn: the first line to it is answered at model speed
                except Exception as exc:  # noqa: BLE001
                    a.state["error"] = f"could not start: {exc}"
                    a.save()
        self.ready.set()
        for state in self.builders.states.values():
            BM.notify(self.builders, state)
        try:
            self.builders.wake_cut_off()
        except Exception as exc:                          # noqa: BLE001  a help, never a reason not to start
            print(f"house: cut-off wakes failed: {exc!r}", flush=True)
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

    snaps, snapping, snap_lock = {}, 0, threading.Lock()

    def snap(self, msg):
        """house.snap <thing> [from=<task>] | house.snap last (Alex, 3 Nov: residents check work visually, hidden, and
        tell JEFF "done and looks good"). The picture takes longer than a word may (10 s), so it is taken in the
        background; the asker is woken when it is ready, and `house.snap last` answers with it. The answer carries an
        [image: <path>] line, which the MCP door adapter turns into a picture the agent sees."""
        args, caller = msg.get("args") or {}, msg.get("caller") or {}
        kv, person = dict(args.get("kv") or {}), caller.get("person")
        target = str(args.get("target") or args.get("words") or "").strip().split(" ")[0]
        if target == "last":
            got = self.snaps.get(person)
            if not got:
                return {"text": "no picture yet: house.snap <thing> takes one"}
            if got.get("error"):
                return {"text": f"the picture of {got['label']} failed: {got['error']}"}
            if not got.get("path"):
                return {"text": f"still taking the picture of {got['label']}; you are woken when it is ready"}
            # A Codex resident calls this from inside its exec script: the picture reaches it only if the script
            # hands the image part on (snap subagent, 3 Nov: otherwise the base64 arrives as text).
            return {"text": f"{got['label']}, taken hidden at {got['at']}. The picture is attached. (Inside exec, "
                            f"pass it on: for (const c of r.content) if (c.type === 'image') image(c).)\n"
                            f"[image: {got['path']}]"}
        if not target:
            return {"refused": "house.snap <thing> [from=<task>], or house.snap last"}
        if not self.m.see("look " + target, use=msg.get("use")).get("rows"):
            return {"refused": f"you cannot see {target}"}
        card = kv.get("from") or kv.get("worker")
        source = None
        if card:
            state = self.builders.states.get(card)
            if not state or not state.get("tree") or not Path(state["tree"]).is_dir():
                return {"refused": f"{card} has no worker worktree to show"}
            if not self.m.see("look " + card, use=msg.get("use")).get("rows"):
                return {"refused": f"you cannot see {card}"}
            source = state["tree"]
        try:
            token = self.builders.session(person).token
        except RuntimeError:
            return {"refused": "you have no session the House can take a picture as"}
        try:
            w, h = (int(n) for n in str(kv.get("size") or "1280x800").lower().split("x"))
            size = (max(320, min(w, 2560)), max(240, min(h, 1600)))
        except ValueError:
            return {"refused": "size=<width>x<height>, e.g. size=1280x800"}
        with self.snap_lock:
            if self.snapping >= 2:
                return {"refused": "two pictures are being taken now; try again in a minute"}
            self.snapping += 1
        label = target + (f" from the worker on {card} (its unlanded code)" if card else "")
        at = time.strftime("%Y%m%dT%H%M%S")
        out = self.home / "snaps" / f"{at}-{target}{'-' + card if card else ''}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        self.snaps[person] = dict(label=label, at=time.strftime("%H:%M"), path=None)

        def go():
            try:
                import snap as S
                result = S.snap(target, token, out, door=URL, source=source, world=self.world, size=size)
                shown = label + (f"; {result['paint_status']}" if result.get("paint_status") else "")
                self.snaps[person].update(path=str(out), label=shown)
                text = self.message("A picture is ready", label=shown)
            except Exception as exc:                  # noqa: BLE001
                self.snaps[person].update(error=str(exc)[:500])
                text = self.message("A picture failed", label=label, detail=str(exc)[:500])
            finally:
                with self.snap_lock:
                    self.snapping -= 1
            agent = self.agents.get(person)
            if agent is not None:
                agent.wake(text)
        threading.Thread(target=go, daemon=True).start()
        return {"text": f"taking a hidden picture of {label}; you are woken when it is ready (house.snap last shows it)"}

    def restart(self, msg):
        """house.restart kernel|house (stewards; Alex, 28 Oct: JEFF must be able to unstick the system). The kernel
        restarts through the keeper, and the House and every module stay. The House is turned off and on by a detached
        helper, a few seconds later, so the asker's turn can end first. Other modules: `off <module>`, `on <module>`."""
        what = str((msg.get("args") or {}).get("target") or (msg.get("args") or {}).get("words") or "").strip().lower()
        if what == "kernel":
            sys.path.insert(0, str(T.REPO / "research" / "window-lab" / "kernel-desktop"))
            from kdesk_keeper import ask
            out = ask("restart-kernel")
            if out is None:
                return {"refused": "no keeper answers, so the kernel cannot restart without closing the desktop"}
            return {"text": str(out.get("text") or "the kernel restarts; windows and modules stay"), "external": True}
        if what == "house":
            caller = msg.get("caller") or {}
            agent = self.agents.get(caller.get("person"))
            token = self.token_for(agent.cfg.get("signer")) if agent else None
            if not token:
                try:                                  # Alex: his agent's session acts for him
                    token = self.builders.session(caller.get("person")).token
                except RuntimeError:
                    return {"refused": "house.restart house needs a session of the asker's own"}
            tok = self.home / f"restart-{int(time.time())}.token"
            tok.write_text(token, encoding="utf-8")
            line = f'"{T.PY}" "{HERE / "restart_house.py"}" --url {URL} --token-file "{tok}" --delay 5'
            ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = '"
                  + line.replace("'", "''") + "' }; $r.ReturnValue")
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=60,
                           creationflags=T.NO_WINDOW)
            return {"text": "the House turns off in 5 seconds and on again; every agent's turn ends then, and builders "
                            "come back as recovery-needed if they were mid-turn", "external": True}
        return {"refused": "house.restart kernel, or house.restart house; for another module: off <module>, then on <module>"}

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
            return self.message("No standing rules named")
        rows = self.m.see(f"look {cid}").get("rows") or [{}]
        text = str(rows[0].get("text") or "").strip()
        return (self.message("Standing rules header", charter=cid) + "\n\n" + text) if text else \
            self.message("Standing rules unavailable", charter=cid)

    def system_text(self, a):
        """An agent's system prompt: its own prompt=<thing> (written by Alex), then the standing rules (charter=)."""
        charter = self.charter_text(a.cfg.get("charter"))
        if not a.cfg.get("prompt"):
            return charter
        rows = self.m.see(f"look {a.cfg['prompt']}").get("rows") or [{}]
        own = str(rows[0].get("text") or "").strip()
        return (own + "\n\n" + charter) if own else charter

    def message(self, heading, **facts):
        return message(self.m.see, heading, **facts)

    def welcome(self, a):
        cfg = a.cfg
        soul = ""
        if cfg.get("soul"):
            rows = self.m.see(f"look {cfg['soul']}").get("rows") or [{}]
            soul = str(rows[0].get("text") or "").strip()
        own = self.message("Welcome", name=a.name, person=a.person)
        # Alex, 3 Nov: how work flows between JEFF, the residents and their workers is the world's, not the code's:
        # a house-agent's guide=<thing> is read at each start, so it changes by editing that thing.
        guide = ""
        if cfg.get("guide"):
            rows = self.m.see(f"look {cfg['guide']}").get("rows") or [{}]
            guide = str(rows[0].get("text") or "").strip()
        return own + ("\n\n" + self.message("Work guide header", guide=cfg["guide"]) + "\n\n" + guide if guide else "") \
            + ("\n\n" + self.message("Soul header", soul=cfg["soul"]) + "\n\n" + soul if soul else "")

    def next_steps(self, a):
        if a.cfg.get("next_steps") != "on":
            return ""
        out = a.door.post("/see", f"rows nextsteps:{a.person}")
        if not out.get("ok"):
            return self.message("Task list unavailable", person=a.person)
        return self.message("Task list header", person=a.person) + "\n" + out.get("text", "")

    def task_changes(self):
        """Event-driven reread, through each resident's own visibility fence."""
        for a in self.agents.values():
            if a.cfg.get("wake_policy") == "addressed":
                continue
            if a.cfg.get("next_steps") != "on" or not getattr(a, "door", None):
                continue
            with a.lock:
                context = self.next_steps(a)
                fresh = a.state.get("welcome_due") and not a.busy
                if context and (fresh or context != a.state.get("next_steps_context")) and context != a.state.get("next_steps_queued"):
                    a.state["next_steps_queued"] = context
                    a.wake(self.message("Their task list changed (JEFF only)"))

    # ---- catching up
    def catch_up(self, a):
        # Queue the whole durable backlog before any wake advances the shared
        # chat cursor. A crash between card and chat catch-up must not lose chat.
        with a.lock:
            busy = a.busy
            a.busy = True
            try:
                # a turn the last House cut off comes first, said again; then what waited for it then; then catch-up
                cut, paused = a.state.pop("in_flight", None), a.state.pop("paused", None)
                if cut or paused:
                    a.inbox = a.said_again(cut) + list(paused or []) + a.inbox
                    a.save()
                self._catch_up(a)
            finally:
                a.busy = busy
            if not busy and a.inbox:
                a._begin()

    def _catch_up(self, a):
        """Lines addressed to it while the house was away (past its cursor), as one wake."""
        cursor = int(a.state.get("cursor", 0))
        got = []
        self.card_signals(a, cursor=cursor)
        held = [(int(i.get("first_record") or i["record"]), int(i["record"])) for i in a.inbox if i.get("record")]
        for r in self.m.see("rows said").get("rows") or []:
            rev = int(r.get("rev") or 0)
            if any(lo <= rev <= hi for lo, hi in held):        # already waiting (a cut-off turn said again)
                continue
            if rev > cursor and a.person in str(r.get("to") or "").split() and r.get("made_by") != a.person \
                    and r.get("for") != a.person and self.sees_line(a, r.get("id"), r.get("chat")):
                got.append((rev, r))
        if not got:
            return
        got.sort(key=lambda x: x[0])
        by_chat = {}
        for rev, r in got:                                   # one wake per chat, oldest chat first (security review H1)
            by_chat.setdefault(r.get("chat"), []).append((rev, r))
        for chat, lines in by_chat.items():
            text = "\n".join(self.line_text(r.get("id"), dict(r, by_name=r.get("by")), chat,
                               heading="Lines that waited while the House was down") for _, r in lines)
            a.wake(text, chat=chat, record=lines[-1][0], first_record=lines[0][0])

    def chat_name(self, c):
        if c not in self.chat_names:
            rows = self.m.see(f"look {c}").get("rows") or [{}]
            self.chat_names[c] = rows[0].get("name") or c
        return self.chat_names[c]

    def line_for(self, a, sid):
        """Whether this agent may see a said line now, asked through its own door: covers closed chats, group-held
        chats, sees_when, and people who left (security review M3, 28 Oct: catch-up read with the house's sight).
        Without a door session for it, no: an agent with no session can't take a turn anyway, and the house's own
        sight is wider than the agent's (round 2: the fallback handed a removed member a group chat's line)."""
        door = getattr(a, "door", None)
        if door is None:
            try:
                tok = self.token_for(a.cfg.get("signer") or a.name.lower())
            except Exception:                         # noqa: BLE001  no session: hand nothing on
                tok = None
            door = Door(tok) if tok else None
        if door is None or not sid:
            return None
        try:
            out = door.post("/see", f"look {sid}")
        except Exception:                             # noqa: BLE001  a door that won't answer hands nothing on
            return None
        return (out.get("rows") or [None])[0] if out.get("ok", True) else None

    def sees_line(self, a, sid, chat):
        return self.line_for(a, sid) is not None

    def mark_turn(self, a, record):
        """Tell the kernel what an agent's acts now answer (kernel `turn`), so the log says why; done at its end."""
        who = a.cfg.get("person")
        if not who:
            return
        line = f"turn {who} r{record}" if record else f"turn {who} done"
        try:
            out = self.m.do(line, timeout=5)
            if out.get("refused") or out.get("ok") is False:
                a.log("turn", out.get("refused") or out.get("text"))
        except Exception as exc:                     # noqa: BLE001
            log(f"house: {line} failed: {exc!r}")

    def line_text(self, sid, row, chat, heading="A line said to them"):
        who = row.get("by_name") or row.get("speaker") or ""
        text = self.message(heading, by=who, chat=self.chat_name(chat), chat_id=chat,
                            line=sid, text=row.get("text", ""))
        about = row.get("about")
        if about:
            # what the line is about, read with the House's sight: a right-click ask says where it was asked and on
            # what (Ask reaches JEFF, 3 Nov 2026); anything else at least says its kind and id
            seen = (self.m.see(f"look {about}").get("rows") or [{}])[0]
            bits = [self.message("About target", kind=seen.get("kind") or "thing", target=about)]
            if seen.get("where"):
                bits.append(self.message("About where it was asked", where=seen["where"]))
            if seen.get("about"):
                bits.append(self.message("About what it was on", target=seen["about"]))
            text += " " + self.message("Line about annotation", details=", ".join(bits))
        return text

    def card_signals(self, agent=None, cursor=0, notice=None):
        """Deliver durable addressed card notes through the ordinary inbox."""
        revision = None
        if notice:
            found = self.m.see("look " + notice).get("rows") or []
            if not found or not (found[0].get("card_signal") or found[0].get("kind") == "notification"):
                return
            revision = int(found[0].get("rev") or 0)
        rows = self.m.see("rows taskboard-event").get("rows") or []
        # Generic world notifications use the same durable addressed-note inbox.
        # They may address their own maker; their recipient controls read/dismiss.
        rows += self.m.see("rows notification").get("rows") or []
        packets = {}
        for row in rows:
            if not (row.get("card_signal") or row.get("kind") == "notification"):
                continue
            if row.get("kind") == "notification" and row.get("state") != "unread":
                continue
            record = int(row.get("rev") or 0)
            if revision is not None and record != revision:
                continue
            for who in str(row.get("to") or "").split():
                a = self.agents.get(who)
                if a is None or (agent is not None and a is not agent):
                    continue
                if row["id"] in a.state.get("card_signals_seen", []) or any(
                    row["id"] in item.get("card_signal_notes", []) for item in a.inbox
                ):
                    continue
                current = self.line_for(a, row["id"])
                if (not current or not current.get("text") or not current.get("about")
                        or (current.get("kind") == "notification" and current.get("state") != "unread")):
                    continue
                # Source visibility can narrow after the note was written.
                if not self.sees_line(a, row.get("source"), None):
                    continue
                packets.setdefault((who, record), []).append(dict(current, id=row["id"]))
        for (who, record), notes in sorted(packets.items(), key=lambda item: item[0][1]):
            a = self.agents[who]
            with a.lock:
                queued = {sid for item in a.inbox for sid in item.get("card_signal_notes", [])}
                seen = set(a.state.get("card_signals_seen", []))
                notes = [r for r in notes if r["id"] not in queued | seen]
                if notes:
                    a.wake(self.card_signal_text(notes), record=record, card_notes=[r["id"] for r in notes])

    def card_signal_text(self, notes):
        return "\n".join(self.message("A card note addressed to them", text=r["text"],
                                      card=r["about"], note=r["id"]) for r in notes)

    def refresh_card_signals(self, a):
        """Re-read queued notes at delivery: undo/privacy changes may remove part of a packet."""
        if not any(i.get("card_signal_notes") for i in a.inbox):
            return
        kept = []
        for item in a.inbox:
            if not item.get("card_signal_notes"):
                kept.append(item)
                continue
            notes = []
            for sid in item["card_signal_notes"]:
                row = self.line_for(a, sid)
                if (row and row.get("text") and row.get("about")
                        and not (row.get("kind") == "notification" and row.get("state") != "unread")
                        and self.sees_line(a, row.get("source"), None)):
                    notes.append(dict(row, id=sid))
            if notes:
                kept.append(dict(item, text=self.card_signal_text(notes),
                                 card_signal_notes=[r["id"] for r in notes]))
        a.inbox[:] = kept

    def retract_card_signals(self):
        """Undo removes undelivered inbox entries too; a delivered wake is historical."""
        for a in self.agents.values():
            with a.lock:
                self.refresh_card_signals(a)

    # ---- hearing
    def happen(self, msg):
        if not self.ready.wait(15):
            return
        word = msg.get("word")
        self.builders.hear(msg)
        if word == "undo":
            self.retract_card_signals()
        if word == "make" and msg.get("target"):
            self.card_signals(notice=msg["target"])
        if word in MESSAGE_WORDS and msg.get("said"):
            to = [p for p in msg.get("to") or [] if p in self.agents and p != msg.get("by_id")]
            if not to:
                return
            rows = self.m.see(f"look {msg['said']}").get("rows") or [{}]
            r = dict(rows[0], by_name=msg.get("by"))
            for p in to:
                self.agents[p].wake(self.line_text(msg["said"], r, r.get("chat")),
                                    chat=r.get("chat"),
                                    record=msg.get("record"))
            return
        target = msg.get("target")
        if word in ("make", "set", "undo") and target:
            rows = self.m.see(f"look {target}").get("rows") or [{}]
            kind = rows[0].get("kind")
            if kind == "notification":
                self.retract_card_signals()
                return
            if kind in ("house-agent", "house-settings"):
                self.load()
                for a in self.agents.values():
                    if a.cfg.get("want") == "asleep" and a.child:
                        a.stop("want=asleep")
                    elif a.cfg.get("want", "awake") == "awake":
                        with a.lock:
                            if a.inbox and not a.busy:
                                a._begin()
                            elif a.cfg.get("wake_policy") != "addressed" and not (a.child and a.child.alive()):
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
                    if a.cfg.get("wake_policy") != "addressed" and a.cfg.get("next_steps") != "on" and str(r.get("who", "")).casefold() == a.name.casefold():
                        a.wake(self.message("Their task list changed (JEFF only)",
                                            by=msg.get("by", ""), title=r.get("title", ""),
                                            card=target) + "\n" + json.dumps(
                                                {"card": target, "title": r.get("title", ""), "by": msg.get("by", "")},
                                                ensure_ascii=False), record=msg.get("record"))

    # ---- words
    def call(self, msg):
        word, args = msg.get("word"), msg.get("args") or {}
        if not self.ready.wait(5):
            return {"refused": "the house is still starting; try again in a moment"}
        if word in ("house.build", "house.work"):
            self.m.accept(msg)
            return self.builders.start_request(msg)
        if word == "house.manage":
            return BM.dispatch(self.builders, msg)
        if word == "house.restart":
            return self.restart(msg)
        if word == "house.retry":
            return self.builders.retry(msg)
        if word == "house.tell":
            return self.builders.tell(msg)
        if word == "house.hand":
            self.m.accept(msg)
            return self.builders.hand_request(msg)
        if word == "house.snap":
            return self.snap(msg)
        if word == "house.review":
            return self.builders.request_review(msg)
        if word == "house.land":
            return self.builders.land(msg)
        if word == "house.import":
            import imports
            return imports.call(self, msg)
        if word == "house.release":
            return self.builders.release(msg)
        if word == "house.stop" and args.get("target") in self.builders.states:
            return self.builders.halt(msg)           # a card: stop its worker (owner, steward or Alex)
        if word in ("house.log", "house.activity") and args.get("target") in self.builders.states:
            state = self.builders.states[args["target"]]
            if not self.m.see("look " + (state.get("chat") or state["task"]), use=msg.get("use")).get("rows"):
                return {"refused": "this worker log belongs to its requester"}
            return self.builders.log(args["target"])
        if word == "house.board":
            return {"rows": task_board.rows(self.m, self.agents, self.builders, msg.get("use"))}
        if word == "house.active":
            rows = work_overview.rows(self.m, self.agents, self.builders, msg.get("use"))
            return {"text": f"{len(rows)} active or blocked cards", "rows": rows}
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
            rows = a.recent_activity(min(int(n), 100) if n.isdecimal() else 10)
            for r in rows:
                r["line"] = f"{r['at'][11:16]}  {r['what']:<5} {' '.join(str(r['text']).split())[:240]}"
            return {"text": (f"{a.name}'s activity outside any chat, latest last:\n" + "\n".join(
                f"  {r['at'][11:16]} {r['what']}: {r['text'][:300]}" for r in rows)) if rows else
                f"{a.name} has done nothing outside a chat yet", "rows": rows}
        if word == "house.log" and a is not None:
            n = str((args.get("kv") or {}).get("limit", "60"))
            log = self.log_of(a, min(int(n), 300) if n.isdecimal() else 60)
            return {"text": "\n".join(" ".join(x.split("\t")) for x in log) or f"{a.name} has no log yet",
                    "rows": [{"person": a.person, "name": a.name, "log": "\n".join(log), "lines": len(log)}]}
        if a is None:
            return {"refused": f"{word} <person>: the house runs {', '.join(x.name for x in self.agents.values()) or 'no one'}"}
        if word == "house.refresh":
            caller = (msg.get("caller") or {}).get("person")
            if not (self.builders.steward(caller) or self.builders.alex(caller)):
                return {"refused": "house.refresh <person> is for stewards"}
            requested = a.request_refresh()
            return {"text": f"{a.name}'s conversation refresh is {'requested' if requested else 'already underway'}; "
                            "house.who shows its state or any error. History and configuration are kept; "
                            "its next wake uses fresh context.", "external": True}
        if word == "house.wake":
            by = (msg.get("caller") or {}).get("name") or "someone"
            words = (args.get("words") or "").strip()
            a.wake(self.message("Someone woke them", by=by, words=words))
            return {"text": f"{a.name} is {'woken' if a.busy else 'told'}; it answers in its own time", "external": True}
        if word == "house.stop":
            caller = (msg.get("caller") or {}).get("person")
            if not (self.builders.steward(caller) or self.builders.alex(caller)):
                return {"refused": "house.stop <person> is for stewards; house.stop <card> stops a worker you own"}
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
               "refreshing": "replacing its conversation",
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
            if self.builders:
                self.builders.deliver_outcomes()
            time.sleep(5)

    def off(self):
        """Every agent pauses: the turn it is in (in_flight) and what waits for it with no record behind it (house.wake,
        worker reports, task wakes) are kept, and the next start says them again. Lines with a record come back
        through catch-up, past the cursor."""
        self.stopping = True
        if self.builders:
            self.builders.off()
        for a in list(self.agents.values()):
            with a.lock:
                waiting = [{k: i[k] for k in ("text", "chat", "at", "said_again") if k in i}
                           for i in a.inbox if not i.get("record")]
                if "paused" in a.state:
                    # Refresh may have put a cut-off recorded turn back in the
                    # inbox, behind a cursor that already consumed that record.
                    waiting = list(a.inbox)
                if waiting or "paused" in a.state:
                    a.state["paused"] = waiting
                    a.save()
            a.stop("off house")
        os._exit(0)


OFFER = [
    {"word": "house.import", "kind": "do", "may": "stewards", "undo": "yes",
     "takes": "<id> field=code|text from=<landed-card> path=<repository-file>",
     "help": "house.import <thing> field=code|text from=<landed-card> path=<file>: copy a regular UTF-8 "
             "file from the House-recorded landing into component.code or lens.text. It must be touched by "
             "that landing and still match committed main. Direct steward/agent calls only. Gaming gate first; ordinary field permissions "
             "and revision fences apply. Equal bytes do nothing. Does not review, grant, install or open windows."},
    {"word": "house.manage", "kind": "do", "needs": "kind=taskboard-task|task", "takes": "<id> [action=<word>] [<words>]", "undo": "external", "may": "members",
     "help": "house.manage <task> action=build|tell|retry|report|review|land|note [words]: only the explicitly approved resident person, for its three locally approved tasks. Builders and other people are refused before effects."},
    {"word": "house.retry", "kind": "do", "needs": TASK_NEEDS, "takes": "<id>", "undo": "external", "may": "members",
     "help": "house.retry <task>: retry a proven terminal startup failure before any model thread. Preserves its existing claim and worktree; refuses uncertain or changed work."},
    {"word": "house.tell", "kind": "do", "needs": TASK_NEEDS, "takes": "<id> <words>", "undo": "external", "may": "members",
     "help": "house.tell <task> <words>: give a card's worker your words as its next instruction, continuing its same "
             "thread and worktree. Its owner, the card's lead, a steward or Alex may tell it; others are refused. A "
             "running worker reads them at its next turn boundary; a stopped one (received, blocked, reviewed) resumes "
             "with them in a new turn. Its owner is still woken at each turn end, and so is anyone else who told it. "
             "Landed or released work does not restart (house.build starts a new run). When every slot is busy, it "
             "starts with your words by itself as soon as one frees. A paused (held) card and work being landed "
             "are refused."},
    {"word": "house.hand", "kind": "do", "needs": TASK_NEEDS, "takes": "<id> <name>", "undo": "external", "may": "members",
     "help": "house.hand <task> <name>: give a card's worker, and the card, to another resident, who is in charge of it "
             "from then on: woken at its turn ends, answers it with house.tell, reviews and lands it. Its owner, a "
             "steward or Alex may hand it on once it stops. The new owner is woken with where it stands and its "
             "last words. A slow request says starting; its caller hears the result. An unresolved card write "
             "blocks worker actions until read-back confirms it; repeat the same handoff to reconcile. "
             "house.who shows the saved owner and any unresolved handoff."},
    {"word": "house.snap", "kind": "see", "takes": "<thing> [from=<task>] [size=<w>x<h>]", "may": "members",
     "help": "house.snap <thing> [from=<task>]: a picture of a thing (a lens, an app, a chat, a card) the way it shows in "
             "a window, taken hidden, never on Alex's screen. from=<task> shows a worker's unlanded code, in a hidden "
             "copy of the world started from its worktree. Use it to check work looks right before saying it is done."},
    {"word": "house.work", "kind": "do", "takes": "<words> [with=claude|codex]", "undo": "external", "may": "members",
     "help": "house.work <what to do, in plain words> [with=claude|codex]: make a card for it and start a worker on it, in "
             "your charge. You are woken each time it finishes a turn (its words also go in its chat); answer it with "
             "house.tell <card> <words>. Then house.review <card> and house.land <card>. Up to four Claude and four Codex "
             "workers run at once (house-settings claude_workers, codex_workers). Only Alex, JEFF and the residents "
             "have workers."},
    {"word": "house.restart", "kind": "do", "takes": "<kernel|house>", "undo": "external", "may": "stewards",
     "help": "house.restart kernel|house: unstick the desktop. kernel: the kernel restarts through the keeper; windows, "
             "the House and every module stay. house: the House turns off and on again 5 seconds later (every agent's "
             "turn ends). Any other module: off <module>, then on <module>."},
    {"word": "house.build", "kind": "do", "needs": TASK_NEEDS, "takes": "<id>", "undo": "external", "may": "members",
     "help": "house.build <task> [with=claude|codex]: claim a ready task and start a worker on it in your charge (Codex unless with=claude), within that kind's pool (four each by default). Uses your existing agent session; never creates credentials. Result receipt is not task completion."},
    {"word": "house.review", "kind": "do", "needs": TASK_NEEDS, "takes": "<id>", "undo": "external", "may": "members",
     "help": "house.review <task>: independently check a received result against current main. Runs the House baseline "
             "and the card's test_suites JSON list: {name, runner: pytest|python|node, paths: [worktree-relative paths], "
             "timeout: seconds, desktop: boolean}. Desktop scripts must use the guarded hidden desktop; the gaming "
             "gate runs first. Each suite has a named result and evidence. Does not land or close the card."},
    {"word": "house.land", "kind": "do", "needs": TASK_NEEDS, "takes": "<id>", "undo": "external", "may": "members",
     "help": "house.land <task>: one step. The House commits what the worker left, runs the checks, lands it on main "
             "and switches it on (restarts what it touched; a change to the House itself restarts the House once "
             "nobody is busy). You hear once, when it is live or what stopped it. One landing at a time; the next "
             "waits its turn. Runs the card's test_suites as well as the baseline, reports every result, and checks "
             "again if its suite definition changed since review (see help house.review)."},
    {"word": "house.release", "kind": "do", "needs": TASK_NEEDS, "takes": "<id> [<why>]", "undo": "external", "may": "members",
     "help": "house.release <task> [why]: the card's worker ends for good (stopped first if running). Its worktree and "
             "branch are kept; the card is free for a new worker. Its owner, a steward or Alex may release it."},
    {"word": "house.board", "kind": "see", "takes": "", "help": "house.board: visible tasks joined with live execution, blockers and delivery."},
    {"word": "house.active", "kind": "see", "takes": "",
     "help": "house.active: visible cards being worked on or blocked, with holder, blocker and resolver. Finished, queued and released work hides automatically."},
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
    {"word": "house.refresh", "kind": "do", "takes": "<id>", "needs": "kind=person", "undo": "external", "may": "stewards",
     "help": "house.refresh <person>: end an agent's process and replace its conversation with fresh context. "
             "The next wake reads its current prompt, charter, welcome, guide and soul. Keeps transcript history, "
             "configuration and waiting messages; an interrupted turn is said again. A sleeping agent stays asleep. "
             "Returns when requested; house.who shows its state or any error. Stewards only."},
    {"word": "house.stop", "kind": "do", "takes": "<id>", "undo": "external", "may": "members",
     "help": "house.stop <card>: stop that card's worker mid-turn; it keeps its worktree, and house.tell starts it again "
             "with new words (its owner, a steward or Alex). house.stop <person> (stewards): end an agent's process "
             "now; the next line to it starts it again; set its house-agent want=asleep to keep it asleep."},
]


def main():
    h = House()
    t = threading.Thread(target=h.m._read, daemon=True)
    t.start()
    h.m.closed.wait()
    h.off()


if __name__ == "__main__":
    main()
