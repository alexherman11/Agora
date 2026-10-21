"""Typed navigation reducer. No renderer, I/O, host calls or authority.

Callers must authorize resolution separately: viewer_tabs permits current-world
Agora only. Local refs are placeholders, never file grants. See
research/window-lab/browsing/DESIGN.md for future engine/storage boundaries.
"""

from dataclasses import asdict, dataclass, field
import json
import re
from urllib.parse import parse_qsl, urlsplit, urlunsplit


class NavigationError(ValueError):
    pass


def need(ok, message):
    if not ok:
        raise NavigationError(message)


@dataclass(frozen=True)
class Target:
    kind: str
    address: str

    @classmethod
    def parse(cls, address):
        need(isinstance(address, str) and 0 < len(address) <= 8192, "Invalid address")
        need(not re.search(r"[\x00-\x20\x7f\\]", address), "Use a complete address")
        try:
            u = urlsplit(address)
            if u.scheme in ("http", "https"):
                need(bool(u.hostname) and u.username is None and u.password is None, "No URL credentials")
                port = u.port  # validate even though this experiment never connects
                host = u.hostname.encode("idna").decode("ascii").lower()
                need("%" not in host, "Invalid host")
                host = "[" + host + "]" if ":" in host else host
                authority = host + (":" + str(port) if port is not None else "")
                return cls("web", urlunsplit((u.scheme, authority, u.path or "/", u.query, u.fragment)))
            if u.scheme == "agora":
                need(bool(re.fullmatch(r"[a-z0-9][a-z0-9-]*", u.netloc)), "Invalid world")
                need(bool(re.fullmatch(r"/(?:item|lens)/[A-Za-z0-9_-]+", u.path)), "Invalid Agora target")
                pairs = parse_qsl(u.query, keep_blank_values=True, strict_parsing=True)
                need(len(pairs) <= 1 and all(k == "lens" and re.fullmatch(r"[a-z][a-z0-9-]*", v)
                                           for k, v in pairs), "Invalid lens")
                return cls("agora", address)
            if u.scheme == "local":
                need(u.netloc == "selection" and not u.query and not u.fragment, "Select a file first")
                need(bool(re.fullmatch(r"/[a-zA-Z0-9_-]{1,128}", u.path)), "Invalid local reference")
                return cls("local", address)
        except (ValueError, UnicodeError) as exc:
            if isinstance(exc, NavigationError):
                raise
            raise NavigationError("Invalid address") from exc
        raise NavigationError("Unsupported address; choose a file to open local content")


@dataclass
class Entry:
    target: Target
    title: str
    # Deliberately only reading position/zoom. No composer, DOM, passwords or forms.
    view: dict = field(default_factory=lambda: {"scroll": 0, "zoom": 1})


@dataclass
class Tab:
    entries: list = field(default_factory=list)
    index: int = -1
    generation: int = 0
    pending: tuple | None = None
    error: str = ""
    failed: Target | None = None


class Browser:
    """State reducer; callers must authorize targets before committing."""

    def __init__(self):
        self.tabs = {}
        self.active = None
        self.serial = 0
        self.visits = []  # separate, optional future PRIVATE history log

    def new_tab(self):
        self.serial += 1
        key = "tab-" + str(self.serial)
        self.tabs[key] = Tab()
        self.active = key
        return key

    def select(self, key):
        need(key in self.tabs, "Tab is closed")
        self.active = key

    def close(self, key):
        need(key in self.tabs, "Tab is closed")
        keys = list(self.tabs)
        index = keys.index(key)
        del self.tabs[key]
        if self.active == key:
            remaining = list(self.tabs)
            self.active = remaining[min(index, len(remaining) - 1)] if remaining else None

    def begin(self, key, address, mode="push"):
        target = Target.parse(address)  # rejection leaves all state untouched
        need(mode in ("push", "replace", "reload"), "Invalid navigation mode")
        t = self.tabs[key]
        need(mode == "push" or t.index >= 0, "No page to replace")
        if mode == "reload":
            need(target == t.entries[t.index].target, "Reload must keep the current address")
        t.generation += 1
        t.pending = (t.generation, target, mode)
        t.error = ""
        t.failed = None
        return t.generation

    def commit(self, key, generation, title, final_address=None):
        """Call on a successful, authenticated controller completion, not on request.

        One redirect chain commits one entry. Real same-document/native history
        synchronization needs the engine adapter described in DESIGN.md.
        """
        t = self.tabs.get(key)
        if t is None or t.pending is None or t.pending[0] != generation:
            return False
        _, target, mode = t.pending
        if final_address is not None:
            final = Target.parse(final_address)
            need(final.kind == target.kind, "Renderer cannot change target kind")
            target = final
        need(isinstance(title, str) and len(title) <= 512, "Invalid title")
        entry = Entry(target, title)
        if mode == "push":
            t.entries[t.index + 1:] = [entry]
            t.index += 1
        elif mode == "replace":
            t.entries[t.index] = entry
        else:
            # Reload retains entry view state and does not create a Back entry.
            t.entries[t.index].title = title
            t.entries[t.index].target = target
        t.pending = None
        self.visits.append({"tab": key, "address": target.address})
        return True

    def fail(self, key, generation):
        t = self.tabs.get(key)
        if t is None or t.pending is None or t.pending[0] != generation:
            return False
        # Static error copy: do not echo a remote HTML error into trusted chrome.
        t.failed = t.pending[1]
        t.error = {
            "web": "Could not open this page. Retry, or choose Open in browser.",
            "agora": "Could not open this Agora page. Retry or go back.",
            "local": "Could not open this selected file. Choose the file again.",
        }[t.failed.kind]
        t.pending = None
        return True

    def move(self, key, delta):
        """Fixture history traversal, not a claim to restore a running web DOM."""
        t = self.tabs[key]
        need(delta in (-1, 1) and 0 <= t.index + delta < len(t.entries), "No history in that direction")
        t.generation += 1
        t.pending = None
        t.error = ""
        t.failed = None
        t.index += delta
        return t.entries[t.index].target

    def position(self, key, scroll=0, zoom=1):
        need(type(scroll) is int and 0 <= scroll <= 10**9, "Invalid position")
        need(type(zoom) in (int, float) and .25 <= zoom <= 5, "Invalid zoom")
        t = self.tabs[key]
        need(t.index >= 0, "No page")
        t.entries[t.index].view = {"scroll": scroll, "zoom": zoom}

    def snapshot(self):
        """Return plain data; the embedding controller chooses its storage.

        No pending navigation, generation or visit log survives restore. The
        caller must authorize every target before using it. The Agora-only
        adapter permits world storage; future web/local history must be private.
        """
        return {"version": 1, "serial": self.serial, "active": self.active,
                "tabs": [{"key": k, "index": t.index,
                          "entries": [asdict(e) for e in t.entries]} for k, t in self.tabs.items()]}

    @classmethod
    def restore(cls, value):
        try:
            return cls._restore(value)
        except (KeyError, TypeError, ValueError, OverflowError, RecursionError) as exc:
            if isinstance(exc, NavigationError):
                raise
            raise NavigationError("Invalid saved state") from exc

    @classmethod
    def _restore(cls, value):
        # Stored data is untrusted too. Bound the whole fixture input.
        need(isinstance(value, dict) and len(json.dumps(value)) <= 1024 * 1024, "Invalid saved state")
        need(value.get("version") == 1 and isinstance(value.get("tabs"), list)
             and len(value["tabs"]) <= 100, "Invalid saved state")
        b = cls()
        need(type(value.get("serial")) is int and 0 <= value["serial"] <= 10**9, "Invalid serial")
        b.serial = value["serial"]
        for saved in value["tabs"]:
            key = saved["key"]
            need(isinstance(key, str) and re.fullmatch(r"tab-[1-9][0-9]*", key)
                 and int(key[4:]) <= b.serial and key not in b.tabs, "Invalid tab key")
            need(isinstance(saved["entries"], list) and len(saved["entries"]) <= 1000, "Invalid entries")
            t = Tab()
            for e in saved["entries"]:
                target = Target.parse(e["target"]["address"])
                need(target.kind == e["target"]["kind"], "Target kind mismatch")
                need(isinstance(e["title"], str) and len(e["title"]) <= 512, "Invalid title")
                t.entries.append(Entry(target, e["title"]))
                t.index = len(t.entries) - 1
                b.tabs[key] = t
                b.position(key, **e["view"])
            need(type(saved["index"]) is int and
                 (-1 == saved["index"] if not t.entries else 0 <= saved["index"] < len(t.entries)),
                 "Invalid history cursor")
            t.index = saved["index"]
            b.tabs[key] = t
        need(value["active"] is None if not b.tabs else value["active"] in b.tabs, "Invalid selected tab")
        b.active = value["active"]
        return b
