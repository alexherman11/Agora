"""adapters.py: the one source for every adapter module (Claude, 4 Nov 2026; after the old desk's
text-desk/notation/adapters.py of 22 Oct, card a12473, which Alex approved as "the feed word").

EDITING A MODULE (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
A module is a seam to something outside the kernel (a model provider, git, Twitch, the media session) and turns it into
world facts and words. What the world does with them (who is told, when, in what words, how it looks) belongs in rules,
lenses and this module's settings thing, read at each use. Names (JEFF, Alex), ids (dk...), models, counts, timeouts and
message text found in this file are debt: move them to settings when you touch them, and never add more.

No adapter needs a source file of its own. An adapter is two things in the world:
  - a module whose run is this file (`module <name> run='["<python>", "<this file>"]' grants="rows <words it uses>"`).
    The kernel already gives a module its off switch (off <name>), its status (status <name>) and its grants, so each
    adapter keeps those of its own: Twitch may only chat.receive into its own chat, a mail adapter only what it needs.
  - an `adapter` thing with the same name, made by the person the module is for. Its text says, in world words, where
    to connect and what each arrival becomes; its other facts are its settings (channel=, into=, ...), read again every
    few seconds, so changing one is a `set` and the adapter follows.

The old desk ran every adapter in one process; here each runs as its own module, because the new kernel's grants,
off and status are per module. What that protects: an adapter can do only what its own grant says.

An adapter's text, one statement a line (indented lines belong to the `on open` or `each` above them):

  connect wss://host/path            a socket; each message is split into lines (\\r\\n or \\n)
  poll https://host/path every 60    fetch every N seconds (at least 30); JSON is records, anything else lines
  items data.children                with poll: where the list of records is in the JSON (dotted path)
  header Name "value"                with poll: a request header; "env:NAME" is a secret from the environment or
                                     the repository's .env (Alex writes it), never written to the world
  imap imap.gmail.com every 60       mail, read-only: headers of mail that arrives after the adapter starts become
                                     records (from, from_name, from_address, subject, date, id, uid, folder)
  login "env:NAME" "env:NAME"        with imap: the address and password, named in .env, never written here
  folder INBOX                       with imap: which folder (default INBOX)
  on open                            lines sent when the socket opens:
    send "words $setting"
  answer 'regex' with "words $group" a reply on the socket to a matching line (a keep-alive)
  ready 'regex' "words $setting"     a matching line means the source is really there: status says the words
  reconnect 'regex'                  a matching line ends the session; it starts again with back-off
  each 'regex'                       for a matching line (named groups become fields; for a record, the regex is
                                     matched against its `match` field, or the whole record's JSON)
    pairs field ";" "="              split a field into more fields (k=v;k=v)
    replace field "from" "to"        literal replace inside one field
    default field "$other"           when field is empty, fill it from other fields
    key "$id"                        what makes this item itself: seen once, never written twice; an item whose
                                     key comes out empty is dropped (there is no safe replay key for it)
    chat.receive $into text="$words" any other line is a world line, said on the module's own grants

A $setting inside a regex is the adapter's own setting, escaped (so `PRIVMSG #$channel ` matches one channel).

What keeps it safe, the rules this file enforces:
- Only an adapter thing made by the person the module is for (or by their agent) is run.
- What arrives from outside only ever fills a "quoted value". A $ outside quotes may name only the adapter's own
  settings, and only an id or a selection. So a message can never become a word, a target or a second line.
- Values reach the world escaped (\\ "), on one line. A world line that would open with @ is not said.
- Sends and answers use only the adapter's settings and the matched line; secrets go only into poll headers and an
  imap login.
- At most 40 items a second are written; the rest of a flood is counted and dropped.
- State (connected, waiting, ...) is kept in memory and answered by `status <name>` and `<name>.now`; it never
  becomes world facts, so a flapping connection writes nothing.

Run: python adapters.py [--headless]   (as a module; --headless never connects)
"""

import hashlib
import json
import os
import random
import re
import shlex
import sys
import threading
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src" / "desktop" / "kernel-desktop"))
from modproto import Module, log  # noqa: E402

CHECK_S = 2.0
MAX_BATCH = 40
MIN_POLL = 30
NAME_OK = re.compile(r"[a-z][a-z0-9_-]{0,30}")
KEPT = {"id", "rev", "kind", "made", "changed", "made_by", "via_actor", "for", "groups", "by", "text", "name"}


class Refused(Exception):
    pass


# --- reading an adapter's text --------------------------------------------------------------------------------

def words_of(line):
    lex = shlex.shlex(line, posix=True)
    lex.whitespace_split, lex.escape, lex.commenters = True, "", ""   # backslashes stay: regexes keep \S
    return list(lex)


SETTING = re.compile(r"\$([A-Za-z_][\w-]*[A-Za-z0-9_]|[A-Za-z_])")


def pattern(src, props):
    """A regex in the world's spelling: (?<name>...) is Python's (?P<name>...); $setting is that setting, escaped."""
    def one(m):
        if m.group(1) not in props or not str(props[m.group(1)]):
            raise Refused(f"the pattern needs the setting {m.group(1)}= (set it on the adapter thing)")
        return re.escape(str(props[m.group(1)]))
    src = SETTING.sub(one, src)
    try:
        return re.compile(re.sub(r"\(\?<(?=[A-Za-z_])", "(?P<", src))
    except re.error as e:
        raise Refused(f"the pattern {src!r} does not read: {e}") from None


def parse(text, props=None):
    """An adapter's text into its plan. Refuses (Refused) with the line it could not read."""
    props = props or {}
    plan = {"connect": "", "poll": "", "imap": "", "login": None, "folder": "", "every": 60, "items": "",
            "headers": {}, "open": [], "answers": [], "ready": [], "reconnect": [], "each": []}
    block = None
    for n, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        inner = raw[:1] in (" ", "\t")
        line = raw.strip()
        head = line.split(None, 1)[0]
        try:
            if not inner:
                block = None
                w = words_of(line)
                if head == "connect" and len(w) == 2 and re.match(r"wss?://", w[1]):
                    plan["connect"] = w[1]
                elif head in ("poll", "imap") and len(w) in (2, 4):
                    if head == "poll" and not re.match(r"https?://", w[1]):
                        raise Refused("poll <http(s) url> every <seconds>")
                    if head == "imap" and not re.fullmatch(r"[\w.-]+", w[1]):
                        raise Refused("imap <host> every <seconds>")
                    plan[head] = w[1]
                    if len(w) == 4:
                        if w[2] != "every" or not w[3].isdigit():
                            raise Refused(f"{head} <where> every <seconds>")
                        plan["every"] = max(MIN_POLL, int(w[3]))
                elif head == "login" and len(w) == 3:
                    if not all(x.startswith("env:") for x in w[1:]):
                        raise Refused('login "env:NAME" "env:NAME": a login is named, never written here')
                    plan["login"] = (w[1], w[2])
                elif head == "folder" and len(w) == 2:
                    plan["folder"] = w[1]
                elif head == "items" and len(w) == 2:
                    plan["items"] = w[1]
                elif head == "header" and len(w) == 3:
                    plan["headers"][w[1]] = w[2]
                elif line == "on open":
                    block = plan["open"]
                elif head == "answer" and len(w) == 4 and w[2] == "with":
                    plan["answers"].append((pattern(w[1], props), w[3]))
                elif head == "ready" and len(w) == 3:
                    plan["ready"].append((pattern(w[1], props), w[2]))
                elif head == "reconnect" and len(w) == 2:
                    plan["reconnect"].append(pattern(w[1], props))
                elif head == "each" and len(w) == 2:
                    rule = {"match": pattern(w[1], props), "steps": [], "key": None, "acts": []}
                    plan["each"].append(rule)
                    block = rule
                else:
                    raise Refused(f"no statement {head!r} here")
            elif isinstance(block, list):
                w = words_of(line)
                if head != "send" or len(w) != 2:
                    raise Refused("under on open, only send \"...\"")
                block.append(w[1])
            elif isinstance(block, dict):
                if head in ("pairs", "replace"):
                    w = words_of(line)
                    if len(w) != 4:
                        raise Refused(f"{head} <field> \"a\" \"b\"")
                    block["steps"].append((head, w[1], w[2], w[3]))
                elif head == "default":
                    w = words_of(line)
                    if len(w) != 3:
                        raise Refused('default <field> "$other"')
                    block["steps"].append((head, w[1], w[2], ""))
                elif head == "key":
                    w = words_of(line)
                    if len(w) != 2:
                        raise Refused('key "$field"')
                    block["key"] = w[1]
                else:
                    spans(line)
                    block["acts"].append(line)
            else:
                raise Refused("an indented line belongs under on open or each")
        except Refused as e:
            raise Refused(f"line {n}: {e}") from None
        except ValueError as e:           # shlex: an open quote
            raise Refused(f"line {n}: {e}") from None
    if sum(bool(plan[k]) for k in ("connect", "poll", "imap")) != 1:
        raise Refused("an adapter says one connect, one poll or one imap")
    if plan["imap"] and not plan["login"]:
        raise Refused('imap needs login "env:NAME" "env:NAME"')
    if not plan["each"]:
        raise Refused("an adapter needs at least one each")
    return plan


# --- filling templates ------------------------------------------------------------------------------------

NAME = r"\$(?:\((?P<p>[A-Za-z_][\w-]*)\)|(?P<n>[A-Za-z_][\w-]*[A-Za-z0-9_]|[A-Za-z_]))"
TARGET = re.compile(r"^[A-Za-z0-9_:,=.+-]+$")


def spans(template):
    """(text, quoted) pieces of a world line, by double quotes (templates hold no escaped quotes)."""
    out, quoted = [], False
    for k, piece in enumerate(template.split('"')):
        if k:
            out.append(('"', None))
        out.append((piece, quoted))
        quoted = not quoted
    if not quoted:
        raise Refused(f"an open quote in {template!r}")
    return out


def escape(value):
    """One literal value inside the kernel's double quotes: one line, backslash and quote escaped."""
    v = re.sub(r"[\r\n]+", " ", str(value))
    return v.replace("\\", "\\\\").replace('"', '\\"')


def fill(template, fields, props):
    """A world line from a template. Inside quotes: a field or setting, escaped. Outside: a setting only, an id or
    selection only. Anything else refuses the line."""
    out = []
    for piece, quoted in spans(template):
        if quoted is None:
            out.append(piece)
            continue

        def one(m, quoted=quoted):
            name = m.group("p") or m.group("n")
            if quoted:
                return escape(fields.get(name, props.get(name, "")))
            if name in fields and name not in props:
                raise Refused(f"${name} comes from outside and may only fill a quoted value")
            v = str(props.get(name, ""))
            if not TARGET.match(v):
                raise Refused(f"${name} outside quotes must be an id or a selection, not {v!r}")
            return v
        out.append(re.sub(NAME, one, piece))
    line = "".join(out)
    if line.lstrip().startswith("@"):
        raise Refused("an adapter's line may not open with @ (that would call people)")
    return line


def send_text(template, values):
    """A send, an answer or a key: only the values given (settings, $random, the matched groups), each on one line,
    so a value can never add a second command to a socket."""
    return re.sub(NAME, lambda m: re.sub(r"[\r\n]+", " ", str(values.get(m.group("p") or m.group("n"), ""))),
                  template)


def items_of(rule, text, record=None):
    """Fields of one arrival under one rule, or None when the rule does not match."""
    src = text if record is None else str(record.get("match", json.dumps(record, ensure_ascii=False)))
    m = rule["match"].search(src)
    if not m:
        return None
    fields = {} if record is None else {k: (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
                                        for k, v in record.items()}
    fields.update({k: v or "" for k, v in m.groupdict().items()})
    for step, name, a, b in rule["steps"]:
        v = fields.get(name, "")
        if step == "pairs":
            for part in v.split(a):
                k, _, val = part.partition(b)
                if k:
                    fields[k] = val
        elif step == "replace":
            fields[name] = v.replace(a, b)
        elif step == "default" and not v:
            fields[name] = send_text(a, fields)
    return fields


def dig(doc, path):
    for part in [p for p in path.split(".") if p]:
        doc = doc[int(part)] if isinstance(doc, list) else doc.get(part, [])
    return doc if isinstance(doc, list) else []


def flat(record, prefix=""):
    out = {}
    for k, v in (record.items() if isinstance(record, dict) else []):
        if isinstance(v, dict):
            out.update(flat(v, f"{prefix}{k}."))
        else:
            out[f"{prefix}{k}"] = v
    return out


ENV_FILE = ROOT / ".env"


def secret(value):
    """env:NAME from the environment, else from the repository's .env (which Alex writes; never committed). The value
    goes only to the transport that asked; it is never logged, written to the world or put in a status."""
    if not value.startswith("env:"):
        return value
    name = value[4:]
    if name in os.environ:
        return os.environ[name]
    try:
        for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
            k, sep, v = raw.strip().partition("=")
            if sep and k.strip() == name:
                return v.strip().strip('"').strip("'")
    except OSError:
        pass
    raise Refused(f"no {name} yet (Alex writes it in .env)")


# --- one adapter ---------------------------------------------------------------------------------------------

class Session(Exception):
    """The session ends here and starts again with back-off (a reconnect line, a refused write, a changed setting)."""


class Adapter:
    """The adapter thing this module is named after, run until off. m is a modproto.Module (or a test's stand-in
    with hello, see and do)."""

    def __init__(self, m=None, headless=False, connect=None):
        self.headless, self.connect = headless, connect
        self.state = "starting"
        self.socket = None
        self.seen, self.seen_path = [], None
        self.queue, self.lock, self.dropped = [], threading.Lock(), 0
        self.m = m or Module(offer=[], on_call=self.call, on_status=lambda: self.state, on_off=self.close,
                             on_hello=self.hello)

    # the module's own name, from the kernel's hello
    @property
    def name(self):
        return str(self.m.hello.get("module") or "")

    def hello(self, msg):
        self.m.offer = [{"word": f"{self.name}.now", "kind": "see", "takes": "", "may": "anyone",
                         "help": f"{self.name}.now: what the {self.name} adapter is doing, kept in memory. "
                                 f"off {self.name} stops it; its settings are the adapter thing named {self.name}."}]
        home = msg.get("home")
        if home:
            self.seen_path = Path(home) / "seen.json"
            try:
                self.seen = json.loads(self.seen_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self.seen = []

    def call(self, msg):
        return {"text": f"{self.name}: {self.state}", "rows": [{"kind": "adapter-now", "name": self.name,
                                                                "state": self.state}]}

    def close(self):
        if self.socket is not None:
            try:
                self.socket.close()
            except Exception:
                pass

    def config(self):
        """-> (plan, settings, fingerprint) of this module's adapter thing, or None (with why in state)."""
        r = self.m.see(f"rows adapter name={self.name}")
        if not r.get("ok", True):
            # Not a lasting stop: a kernel restart refuses reads for a moment (3 Nov: Twitch stayed off after one).
            self.state = "waiting: the adapter reading was refused; retrying"
            return None
        whose = {self.m.hello.get("for"), self.m.hello.get("owner")} - {None, ""}
        rows = [a for a in r.get("rows", []) if a.get("made_by") in whose or a.get("for") in whose]
        if len(rows) != 1:
            self.state = (f"waiting: no adapter thing named {self.name} made by this module's person" if not rows
                          else f"waiting: {len(rows)} adapter things named {self.name}; keep one")
            return None
        a = rows[0]
        props = {k: (v if isinstance(v, str) else json.dumps(v)) for k, v in a.items() if k not in KEPT}
        fp = hashlib.sha1((json.dumps(props, sort_keys=True) + str(a.get("text", ""))).encode()).hexdigest()
        if str(a.get("on", "yes")).lower() in ("no", "off", "false"):
            self.state = f"off (set on=yes on the {self.name} adapter)"
            return None
        try:
            plan = parse(str(a.get("text", "")), props)
        except Refused as e:
            self.state = f"does not read: {e}"
            return None
        props["random"] = str(random.randint(100000, 999999))
        return plan, props, fp

    def unchanged(self, fp):
        cur = self.config()
        return cur is not None and cur[2] == fp

    def arrive(self, plan, props, line=None, record=None):
        for rule in plan["each"]:
            fields = items_of(rule, line, record)
            if fields is None:
                continue
            key = send_text(rule["key"], {**props, **fields}) if rule["key"] is not None else ""
            if rule["key"] is not None and not key:
                return                           # no safe replay key: dropped
            if key and key in self.seen:
                return
            try:
                acts = [fill(a, fields, props) for a in rule["acts"]]
            except Refused as e:
                log(f"{self.name}: an arrival refused: {e}")
                return
            with self.lock:
                if len(self.queue) >= MAX_BATCH:
                    self.dropped += 1
                    return
                self.queue.append((key, acts))
            return

    def flush(self):
        """Write what arrived, one line at a time on the module's own grants. A refused line ends the session (it
        reconnects with back-off); keys are kept only for what was written, so nothing is doubled or skipped."""
        with self.lock:
            batch, self.queue = self.queue, []
            dropped, self.dropped = self.dropped, 0
        if dropped:
            log(f"{self.name}: a flood; {dropped} item(s) dropped")
        wrote = False
        for n, (key, acts) in enumerate(batch):
            for line in acts:
                out = self.m.do(line)
                if not out.get("ok", False):
                    self.state = "reconnecting: a line was refused or unconfirmed"
                    raise Session()
            if key:
                self.seen = (self.seen + [key])[-2000:]
                wrote = True
        if wrote and self.seen_path:
            try:
                self.seen_path.parent.mkdir(parents=True, exist_ok=True)
                self.seen_path.write_text(json.dumps(self.seen), encoding="utf-8")
            except OSError:
                pass

    def receive(self, ws, plan, props, msg):
        """One socket message: answers, ready and reconnect lines, then arrivals."""
        text = msg if isinstance(msg, str) else msg.decode("utf-8", "replace")
        for line in re.split(r"\r?\n", text):
            if not line:
                continue
            if any(rx.search(line) for rx in plan["reconnect"]):
                raise Session()
            for rx, reply in plan["answers"]:
                m = rx.search(line)
                if m:
                    ws.send(send_text(reply, {**props, **m.groupdict()}))
                    break
            else:
                for rx, words in plan["ready"]:
                    if rx.search(line):
                        self.state = send_text(words, props)
                self.arrive(plan, props, line=line)

    def session(self, plan, props, fp):
        if plan["connect"]:
            self.socket_session(plan, props, fp)
        elif plan["imap"]:
            self.mail(plan, props, fp)
        else:
            self.polling(plan, props, fp)

    def socket_session(self, plan, props, fp):
        connect = self.connect
        if connect is None:
            from websockets.sync.client import connect
        url = send_text(plan["connect"], props)
        host = url.split("/")[2]
        ws = self.socket = connect(url, open_timeout=10, close_timeout=2, max_size=2 ** 20)
        try:
            for s in plan["open"]:
                ws.send(send_text(s, props))
            self.state = f"joining {host}" if plan["ready"] else f"connected to {host}"
            checked = time.monotonic()
            while not self.m.closed.is_set():
                if time.monotonic() - checked >= CHECK_S:
                    if not self.unchanged(fp):
                        return
                    checked = time.monotonic()
                try:
                    msg = ws.recv(timeout=1)
                except TimeoutError:
                    self.flush()
                    continue
                if not msg:
                    return
                self.receive(ws, plan, props, msg)
                self.flush()
        finally:
            self.flush_quietly()
            ws.close()
            self.socket = None

    def flush_quietly(self):
        try:
            self.flush()
        except Session:
            pass

    def polling(self, plan, props, fp):
        url = send_text(plan["poll"], props)
        headers = {k: secret(send_text(v, props)) for k, v in plan["headers"].items()}
        headers.setdefault("User-Agent", "Agora adapters (read-only)")
        while not self.m.closed.is_set():
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
                body = r.read().decode("utf-8", "replace")
            try:
                doc = json.loads(body)
                for rec in reversed(dig(doc, plan["items"]) if plan["items"] else
                                    (doc if isinstance(doc, list) else [doc])):
                    self.arrive(plan, props, record=flat(rec))
            except json.JSONDecodeError:
                for line in body.splitlines():
                    self.arrive(plan, props, line=line)
            self.flush()
            self.state = f"reading {url.split('/')[2]} every {plan['every']} s"
            end = time.monotonic() + plan["every"]
            while time.monotonic() < end and not self.m.closed.is_set():
                self.m.closed.wait(CHECK_S)
                if not self.unchanged(fp):
                    return

    def mail(self, plan, props, fp):
        """IMAP, read-only: the folder is opened read-only and only headers are fetched (BODY.PEEK), so nothing is
        marked read, moved or deleted. Only mail that arrives after the adapter starts is written."""
        import email.header
        import email.parser
        import imaplib
        host = send_text(plan["imap"], props)
        user = secret(send_text(plan["login"][0], props))
        password = secret(send_text(plan["login"][1], props))
        box = imaplib.IMAP4_SSL(host, timeout=60)
        try:
            box.login(user, password)
            folder = send_text(plan["folder"], props) or "INBOX"
            typ, _ = box.select(f'"{folder}"', readonly=True)
            if typ != "OK":
                raise Refused(f"no folder {folder}")
            last = None
            self.state = f"reading {folder} every {plan['every']} s"
            while not self.m.closed.is_set():
                box.noop()
                typ, data = box.uid("SEARCH", None, "ALL")
                uids = [int(u) for u in (data[0] or b"").split()]
                if last is None:
                    last = max(uids, default=0)
                for uid in [u for u in uids if u > last][-MAX_BATCH:]:
                    typ, got = box.uid("FETCH", str(uid),
                                       "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE MESSAGE-ID)])")
                    raw = next((part[1] for part in got if isinstance(part, tuple)), b"")
                    h = email.parser.BytesHeaderParser().parsebytes(raw)

                    def text(v):
                        return str(email.header.make_header(email.header.decode_header(v or "")))
                    sender = text(h.get("From"))
                    name, _, addr = sender.rpartition("<")
                    self.arrive(plan, props, record={
                        "uid": str(uid), "folder": folder, "from": sender,
                        "from_name": (name.strip().strip('"') or addr.rstrip(">")),
                        "from_address": addr.rstrip(">") if addr else sender,
                        "subject": text(h.get("Subject")), "date": text(h.get("Date")),
                        "id": text(h.get("Message-ID")) or f"{folder}-{uid}"})
                last = max(uids + [last])
                self.flush()
                end = time.monotonic() + plan["every"]
                while time.monotonic() < end and not self.m.closed.is_set():
                    self.m.closed.wait(CHECK_S)
                    if not self.unchanged(fp):
                        return
        finally:
            try:
                box.logout()
            except Exception:
                pass

    def run(self):
        self.m.run_reader()
        self.m.ready.wait(30)
        retry = 1
        while not self.m.closed.is_set():
            if self.headless:
                self.state = "headless (no connection)"
                self.m.closed.wait(1)
                continue
            cur = self.config()
            if cur is None:
                self.m.closed.wait(CHECK_S)
                continue
            try:
                self.session(*cur)
                retry = 1
            except Session:
                pass
            except Refused as e:
                self.state = f"stopped: {e}; change the adapter thing to try again"
                while not self.m.closed.is_set() and self.unchanged(cur[2]):
                    self.m.closed.wait(CHECK_S)
                continue
            except Exception as e:
                # Never the raw exception text: it can carry a server's words or a credential.
                self.state = f"disconnected ({e.__class__.__name__}); retrying"
            if not self.m.closed.is_set():
                self.m.closed.wait(retry)
                retry = min(retry * 2, 30)
        self.close()


if __name__ == "__main__":
    Adapter(headless="--headless" in sys.argv).run()
