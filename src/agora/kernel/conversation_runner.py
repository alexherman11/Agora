"""Provider-neutral, host-side conversation runner; not wired into a live host.

Only the authenticated host calls enter/respond with a person Actor. Models
return data, not Lines or actors. This seam does not create provider processes.
"""
from copy import deepcopy
from dataclasses import dataclass, field
import re
import shlex
import threading
from typing import Protocol

from .kernel import Actor, Refused
from .conversations import conversation, require_person
from .lines import ID


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ModelReply:
    text: str = ""
    calls: tuple[ToolCall, ...] = ()


class ModelSession(Protocol):
    def respond(self, messages: tuple[dict, ...], results: tuple[dict, ...]) -> ModelReply: ...


class ModelFactory(Protocol):
    def open(self) -> ModelSession: ...


class FakeModel:
    """Scripted fixture factory: each open gets an independent script cursor."""
    def __init__(self, replies=()):
        self.replies = tuple(replies)
        self.sessions = []

    def open(self):
        session = FakeSession(deepcopy(self.replies))
        self.sessions.append(session)
        return session


class FakeSession:
    def __init__(self, replies):
        self.replies, self.turn, self.inputs = replies, 0, []

    def respond(self, messages, results):
        self.inputs.append(deepcopy((messages, results)))
        answer = self.replies[self.turn] if self.turn < len(self.replies) else ModelReply("Fixture answer.")
        self.turn += 1
        return answer


def _id(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise Refused("a tool object must be a thing id")
    return value


def _text(value):
    if not isinstance(value, str) or not value.strip():
        raise Refused("a tool text must be a nonempty string")
    return value


class ConversationRunner:
    """An instance belongs to one kernel, never shared across worlds.

    Session key = (agent module, authenticated person, server-resolved chat).
    The caller Actor is a trusted host input, never deserialized model output.
    A per-runner lock serializes turns and fresh-chat requests in this fixture.
    """
    def __init__(self, kernel, agent, model: ModelFactory, *, max_rounds=8):
        self.k, self.agent, self.model = kernel, _id(agent), model
        self.sessions = {}
        self.lock = threading.RLock()
        self.max_rounds = max_rounds

    def entry(self, caller):
        require_person(self.k, caller)
        # Data for a host/UI, not a world button to execute without review.
        with self.k.lock:
            module = self.k.shown(caller.person, self.agent)
            e = self.k.entry(self.k.find_entry("conversation.open"))
            if (not module or module.get("kind") != "module" or not module.get("on")
                    or not self.k.may(caller, e, self.agent, self.k.place)):
                raise Refused("conversation entry unavailable")
            return {"label": module.get("name", "Conversation"), "kind": "conversation-entry",
                    "action": {"word": "conversation.open", "target": self.agent},
                    "scope": "signed-in-person", "fresh": {"fresh": "yes"}}

    def enter(self, caller, *, fresh=False):
        require_person(self.k, caller)
        with self.lock, self.k.lock:
            suffix = " fresh=yes" if fresh else ""
            group = (self.k.groups_of(self.agent) or [self.k.place])[0]
            eid = self.k.find_entry("conversation.open", group)
            if not eid or self.k.source(self.k.entry(eid)) != ("kernel", "conversation.open"):
                raise Refused("entry requires its kernel word")
            return self.k.step(caller, f"conversation.open {self.agent}{suffix}")["rows"][0]["id"]

    def _author(self, caller):
        require_person(self.k, caller)
        return Actor(self.agent, caller.person, "module", module=self.agent, caller=caller)

    def _read(self, caller, word, line, target=None):
        # Do not allow a shadowed word/verb/module to execute through this seam.
        with self.k.lock:
            group = (self.k.groups_of(target) or [self.k.place])[0] if target else self.k.place
            eid = self.k.find_entry(word, group)
            if not eid or self.k.source(self.k.entry(eid)) != ("kernel", word):
                raise Refused("tool requires its kernel reading")
            author = self._author(caller)
            if target:
                if self.k.shown(caller.person, target) is None:
                    raise self.k.no_such(target)
                self.k.reaches(author, word, self.k.state.get(target, "kind"), target=target, group=group)
            else:
                grants = self.k.scope_grants(author, word, group)
                if not any(not self.k.state.get(g, "only") for g in grants):
                    # Aggregate readings cannot safely apply kind/thing/field
                    # restrictions to their prose. Refuse, never return raw text.
                    raise Refused("aggregate reading requires an unrestricted grant for this reading")
            return self.k.module_see(self.agent, caller, line)

    def _write(self, caller, chat, word, **kv):
        with self.k.lock:
            author = self._author(caller)
            conversation(self.k, author, chat)
            group = (self.k.groups_of(chat) or [self.k.place])[0]
            eid = self.k.find_entry(word, group)
            if not eid or self.k.source(self.k.entry(eid)) != ("kernel", word):
                raise Refused("tool requires its kernel word")
            # step, not run: one line only; values are quoted and never expanded.
            line = f"{word} {chat} " + " ".join(f"{k}={shlex.quote(v)}" for k, v in kv.items())
            return self.k.step(author, line)

    def _dispatch(self, caller, chat, call):
        """Closed typed vocabulary; no generic do, send, post, notify or web."""
        schemas = {"look": {"id"}, "search": {"query"}, "help": {"topic"},
                   "draft": {"text", "destination"}}
        if not isinstance(call, ToolCall) or not isinstance(call.name, str) or call.name not in schemas:
            raise Refused("tool is not available")
        a = call.arguments
        if not isinstance(a, dict) or set(a) != schemas[call.name]:
            raise Refused("unexpected tool arguments")
        with self.k.lock:
            conversation(self.k, self._author(caller), chat)
            if call.name == "look":
                target = _id(a["id"])
                return self._read(caller, "look", f"look {target}", target)
            if call.name == "search":
                return self._read(caller, "search", "search q=" + shlex.quote(_text(a["query"])))
            if call.name == "help":
                topic = _text(a["topic"])
                if not re.fullmatch(r"[a-z][a-z0-9.-]*", topic):
                    raise Refused("help takes a topic name")
                return self._read(caller, "help", "help " + topic)
            return self._write(caller, chat, "draft.create", text=_text(a["text"]),
                               destination=_id(a["destination"]))

    def respond(self, caller, text):
        """No chat/person argument: route solely from the authenticated caller."""
        require_person(self.k, caller)
        text = _text(text)
        with self.lock:
            chat = self.enter(caller)
            with self.k.lock:
                # Recheck caller AND module grants for history before inference.
                history = self._read(caller, "chat", f"chat {chat} limit=200", chat)
                if history.get("refused"):
                    raise Refused(history["refused"])
                group = (self.k.groups_of(chat) or [self.k.place])[0]
                eid = self.k.find_entry("conversation.append", group)
                if not eid or self.k.source(self.k.entry(eid)) != ("kernel", "conversation.append"):
                    raise Refused("conversation requires its kernel word")
                self.k.step(caller, f"conversation.append {chat} text={shlex.quote(text)}")
                messages = tuple({"role": "assistant" if self.k.state.get(r["id"], "made_by") == self.agent
                                  else "user", "text": r["text"], "untrusted": True}
                                 for r in history.get("rows", []))
                messages += ({"role": "user", "text": text, "untrusted": True},)
            key = (self.agent, caller.person, chat)
            if key not in self.sessions:
                self.sessions[key] = self.model.open()
            results = []
            for _ in range(self.max_rounds):
                with self.k.lock:
                    author = self._author(caller)
                    conversation(self.k, author, chat)
                    eid = self.k.find_entry("chat", group)
                    if not eid or not self.k.may(author, self.k.entry(eid), chat, group):
                        raise Refused("conversation access changed")
                answer = self.sessions[key].respond(deepcopy(messages), deepcopy(tuple(results)))
                if (not isinstance(answer, ModelReply) or not isinstance(answer.text, str)
                        or not isinstance(answer.calls, tuple) or len(answer.calls) > self.max_rounds):
                    raise Refused("invalid model reply")
                if not answer.calls:
                    saved = self._write(caller, chat, "conversation.append", text=_text(answer.text))
                    return {"chat": chat, "text": answer.text, "message": saved["made"][0],
                            "tools": results}
                for call in answer.calls:
                    try:
                        result = self._dispatch(caller, chat, call)
                    except Refused as exc:
                        result = {"refused": str(exc)}
                    results.append({"tool": call.name if isinstance(call, ToolCall) and isinstance(call.name, str)
                                    else "invalid",
                                    "untrusted": True, "result": result})
            raise Refused("conversation tool limit reached")
