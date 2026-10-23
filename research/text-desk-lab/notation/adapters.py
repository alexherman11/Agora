"""adapters.py: the one runner for every adapter in the world (Claude, 22 Oct 2026, card a12473).

Alex approved this as "the feed word" and then asked for "a general adapter for things like gmail and text too", whose
lines can make notifications and tasks as well as chat. It is called adapter because feeds.py is already the house's
own word for an agent's live activity feed.

An adapter is a note with prop role=adapter. Its text says, in world words, where to connect and what each thing that
arrives becomes; its props hold its settings. No adapter needs a source file of its own: Twitch chat, mail, an RSS
list or a JSON API are all adapter notes. This runner is the only source, started by the keeper beside the house.

An adapter's text, one statement a line (indented lines belong to the `on open` or `each` above them):

  connect wss://host/path            a socket; each message is split into lines (\\r\\n or \\n)
  poll https://host/path every 60    fetch every N seconds (at least 30); JSON is records, anything else lines
  items data.children                with poll: where the list of records is in the JSON (dotted path)
  header Name "value"                with poll: a request header; "env:NAME" is a secret from the house's
                                     environment, used here and nowhere else, never written to the world
  imap imap.gmail.com every 60       mail, read-only: headers of mail that arrives after the adapter starts become
                                     records (from, from_name, from_address, subject, date, id, uid, folder)
  login "env:NAME" "env:NAME"        with imap: the address and password, named in .env, never written here
  folder INBOX                       with imap: which folder (default INBOX)
  on open                            lines sent when the socket opens:
    send "words $prop"
  answer 'regex' with "words $group"  a reply on the socket to a matching line (a keep-alive)
  each 'regex'                       for a matching line (named groups become fields; for a record, the
                                     regex is matched against its `match` field, or the whole record's JSON)
    pairs field ";" "="              split a field into more fields (k=v;k=v)
    replace field "from" "to"        literal replace inside one field
    key "$id"                        what makes this item itself: seen once, never posted twice
    do append $into line="$user: $words" ...
    notify "..."                     any world line: what the adapter does is ordinary world words

Settings (props): name (who the adapter signs as: lower case, letters, digits, -), on=yes|no, and anything the text
reads as $prop. The runner writes status= and status_at=.

What keeps it safe, the rules this file enforces:
- An adapter runs only while on=yes and the last change to it by anyone but itself was Alex's. Anyone may turn one
  off; any change by someone else stops it until Alex turns it on again (one click in its lens).
- What arrives from outside only ever fills a "quoted value". A $ outside quotes may name only the adapter's own props,
  and only an id or a selection. So a message can never become a verb, a target or a second command.
- Values reach the world escaped (\\ " $), on one line. A world line that would open with @ is not run.
- Sends and answers use only the adapter's props and the matched line; secrets go only into poll headers and an
  imap login, and only from .env or the house's environment.
- At most 40 items a second per adapter are written; the rest of a flood is counted and dropped.

Run: python adapters.py [--door URL] [--world frontier] [--with PID] [--role adapter]   (a second runner exits 76)
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
STATE = HERE / "house-state"
CHECK_S = 15.0
MAX_BATCH = 40
MIN_POLL = 30
OWNER = "alex"


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv[:-1] else default


def log(msg):
    print(time.strftime("%Y-%m-%d %H:%M:%S ") + msg, flush=True)


class Refused(Exception):
    pass


# --- reading an adapter's text --------------------------------------------------------------------------------

def words_of(line):
    lex = shlex.shlex(line, posix=True)
    lex.whitespace_split, lex.escape, lex.commenters = True, "", ""   # backslashes stay: regexes keep \S
    return list(lex)


def pattern(src):
    """A regex in the world's spelling: (?<name>...) is Python's (?P<name>...)."""
    try:
        return re.compile(re.sub(r"\(\?<(?=[A-Za-z_])", "(?P<", src))
    except re.error as e:
        raise Refused(f"the pattern {src!r} does not read: {e}") from None


def parse(text):
    """An adapter's text into its plan. Refuses (Refused) with the line it could not read."""
    plan = {"connect": "", "poll": "", "imap": "", "login": None, "folder": "", "every": 60, "items": "",
            "headers": {}, "open": [], "answers": [], "each": []}
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
                elif head == "poll" and len(w) in (2, 4) and re.match(r"https?://", w[1]):
                    plan["poll"] = w[1]
                    if len(w) == 4:
                        if w[2] != "every" or not w[3].isdigit():
                            raise Refused("poll <url> every <seconds>")
                        plan["every"] = max(MIN_POLL, int(w[3]))
                elif head == "imap" and len(w) in (2, 4) and re.fullmatch(r"[\w.-]+", w[1]):
                    plan["imap"] = w[1]
                    if len(w) == 4:
                        if w[2] != "every" or not w[3].isdigit():
                            raise Refused("imap <host> every <seconds>")
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
                    plan["answers"].append((pattern(w[1]), w[3]))
                elif head == "each" and len(w) == 2:
                    rule = {"match": pattern(w[1]), "steps": [], "key": "", "acts": []}
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
                elif head == "key":
                    w = words_of(line)
                    if len(w) != 2:
                        raise Refused('key "$field"')
                    block["key"] = w[1]
                else:
                    check_template(line)
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


def check_template(template):
    spans(template)


def escape(value):
    v = re.sub(r"[\r\n\t]+", " ", str(value))
    return v.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$")


def fill(template, fields, props):
    """A world line from a template. Inside quotes: a field or prop, escaped. Outside: a prop only, an id or
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


def send_text(template, props):
    """A send or answer: only the adapter's props and $random; no secrets, no quotes needed."""
    return re.sub(NAME, lambda m: str(props.get(m.group("p") or m.group("n"), "")), template)


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
        else:
            fields[name] = v.replace(a, b)
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


ENV_FILE = HERE.parents[2] / ".env"


def secret(value):
    """env:NAME from the house's environment, else from the repository's .env (which Alex writes; never committed).
    The value goes only to the transport that asked; it is never logged, written to the world or put in a status."""
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


def write_status(w, fid, actor, words):
    w.post(f"examine {fid}\ndo prop {fid} status=\"{escape(words)}\" "
           f"status_at=\"{time.strftime('%d %b %H:%M')}\"", actor, whole=False)


# --- the world --------------------------------------------------------------------------------------------

class World:
    def __init__(self, door, world):
        self.door, self.world = door, world

    def post(self, line, who, whole=True, gesture=None):
        body = {"session": self.world, "as": who, "line": line, "whole": whole}
        if gesture:
            body["gesture"] = gesture
        req = urllib.request.Request(self.door + "/api/do", json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)

    def text(self, line, who="adapters"):
        out = self.post(line, who)
        return out.get("text") or out.get("error") or ""


def head_props(head):
    """props from an examine/find head line: key=value up to the next ' key=' or ' · '."""
    props = {}
    for m in re.finditer(r"(?:^| )([A-Za-z_][\w-]*)=(.*?)(?= [A-Za-z_][\w-]*=| · |$)", head):
        props[m.group(1)] = m.group(2)
    return props


def read_adapter(w, fid):
    head = next((ln for ln in w.text(f"examine {fid}").splitlines() if ln.startswith(fid + " ")), "")
    t = w.text(f"read {fid}")
    body = t.split("\n---\n", 1)[1].rsplit("\n---", 1)[0] if "\n---\n" in t else ""
    return head_props(head), body


def approved(w, fid, actor):
    """on=yes, and the last change by anyone but the adapter itself was Alex's."""
    for ln in reversed(w.text(f"history {fid}").splitlines()):
        m = re.match(r"^e\d+ .* by (\S+)$", ln.strip())
        if not m or m.group(1) == actor:
            continue
        return m.group(1) == OWNER
    return False


# --- one adapter ---------------------------------------------------------------------------------------------

class Adapter:
    def __init__(self, w, fid, props, text):
        self.w, self.fid, self.props, self.text = w, fid, dict(props), text
        self.actor = props.get("name", "")
        self.plan = parse(text)
        self.stop = threading.Event()
        self.queue, self.lock = [], threading.Lock()
        self.dropped, self.said = 0, ""
        self.props["random"] = str(random.randint(10000, 99999))
        self.seen_path = STATE / "adapters" / f"{fid}.json"
        try:
            self.seen = json.loads(self.seen_path.read_text(encoding="utf-8"))
        except Exception:
            self.seen = []
        self.thread = threading.Thread(target=self.run, daemon=True)

    def status(self, words):
        if words == self.said:
            return
        self.said = words
        log(f"{self.fid} {self.actor}: {words}")
        try:
            write_status(self.w, self.fid, self.actor, words)
        except Exception as e:
            log(f"{self.fid}: status not written ({e})")

    def arrive(self, line=None, record=None):
        for rule in self.plan["each"]:
            fields = items_of(rule, line, record) if record is None else items_of(rule, None, record)
            if fields is None:
                continue
            key = send_text(rule["key"], {**self.props, **fields}) if rule["key"] else ""
            if key and key in self.seen:
                return
            try:
                acts = [fill(a, fields, self.props) for a in rule["acts"]]
            except Refused as e:
                log(f"{self.fid}: an arrival refused: {e}")
                return
            with self.lock:
                if len(self.queue) >= MAX_BATCH:
                    self.dropped += 1
                    return
                self.queue.append((key or hashlib.sha1(repr(acts).encode()).hexdigest()[:16], acts))
            if key:
                self.seen = (self.seen + [key])[-2000:]
            return

    def flush(self):
        with self.lock:
            batch, self.queue = self.queue, []
            dropped, self.dropped = self.dropped, 0
        if dropped:
            log(f"{self.fid}: a flood; {dropped} item(s) dropped")
        if not batch:
            return
        lines = [a for _, acts in batch for a in acts]
        gesture = "adapter-" + hashlib.sha1("|".join(k for k, _ in batch).encode()).hexdigest()[:24]
        for attempt in range(3):
            try:
                out = self.w.post("\n".join(lines), self.actor, whole=False, gesture=gesture)
                if out.get("error"):
                    log(f"{self.fid}: refused: {out['error'][-300:]}")
                break
            except Exception as e:
                log(f"{self.fid}: write failed ({e}); retry {attempt + 1}")
                time.sleep(2 * (attempt + 1))
        try:
            self.seen_path.parent.mkdir(parents=True, exist_ok=True)
            self.seen_path.write_text(json.dumps(self.seen), encoding="utf-8")
        except Exception:
            pass

    def run(self):
        backoff = 2.0
        while not self.stop.is_set():
            try:
                if self.plan["connect"]:
                    self.socket()
                elif self.plan["imap"]:
                    self.mail()
                else:
                    self.polling()
                backoff = 2.0
            except Refused as e:
                self.status(f"stopped: {e}")
                return
            except Exception as e:
                self.status(f"disconnected ({e.__class__.__name__}); trying again in {int(backoff)} s")
                self.stop.wait(backoff)
                backoff = min(backoff * 2, 120)

    def socket(self):
        from websockets.sync.client import connect
        url = send_text(self.plan["connect"], self.props)
        with connect(url, open_timeout=30, max_size=2 ** 20) as ws:
            for s in self.plan["open"]:
                ws.send(send_text(s, self.props))
            self.status(f"live: connected to {url.split('/')[2]}")
            while not self.stop.is_set():
                try:
                    msg = ws.recv(timeout=1)
                except TimeoutError:
                    continue
                for line in re.split(r"\r?\n", msg if isinstance(msg, str) else msg.decode("utf-8", "replace")):
                    if not line:
                        continue
                    for rx, reply in self.plan["answers"]:
                        m = rx.search(line)
                        if m:
                            ws.send(send_text(reply, {**self.props, **m.groupdict()}))
                            break
                    else:
                        self.arrive(line=line)

    def polling(self):
        url = send_text(self.plan["poll"], self.props)
        headers = {k: secret(send_text(v, self.props)) for k, v in self.plan["headers"].items()}
        headers.setdefault("User-Agent", "Agoran adapters (read-only)")
        while not self.stop.is_set():
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
                body = r.read().decode("utf-8", "replace")
            try:
                doc = json.loads(body)
                for rec in reversed(dig(doc, self.plan["items"]) if self.plan["items"] else
                                    (doc if isinstance(doc, list) else [doc])):
                    self.arrive(record=flat(rec))
            except json.JSONDecodeError:
                for line in body.splitlines():
                    self.arrive(line=line)
            # steady words: a status that changed each poll would be a world event each poll
            self.status(f"live: reading {url.split('/')[2]} every {self.plan['every']} s")
            self.stop.wait(self.plan["every"])

    def mail(self):
        """IMAP, read-only: the folder is opened read-only and only headers are fetched (BODY.PEEK), so nothing is
        marked read, moved or deleted. Only mail that arrives after the adapter starts is posted."""
        import email.header
        import email.parser
        import imaplib
        host = send_text(self.plan["imap"], self.props)
        user = secret(send_text(self.plan["login"][0], self.props))
        password = secret(send_text(self.plan["login"][1], self.props))
        box = imaplib.IMAP4_SSL(host, timeout=60)
        try:
            box.login(user, password)
            folder = send_text(self.plan["folder"], self.props) or "INBOX"
            typ, _ = box.select(f'"{folder}"', readonly=True)
            if typ != "OK":
                raise Refused(f"no folder {folder}")
            last = None
            self.status(f"live: reading {folder} every {self.plan['every']} s")
            while not self.stop.is_set():
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
                    self.arrive(record={"uid": str(uid), "folder": folder, "from": sender,
                                        "from_name": (name.strip().strip('"') or addr.rstrip(">")),
                                        "from_address": addr.rstrip(">") if addr else sender,
                                        "subject": text(h.get("Subject")), "date": text(h.get("Date")),
                                        "id": text(h.get("Message-ID")) or f"{folder}-{uid}"})
                last = max(uids + [last])
                self.stop.wait(self.plan["every"])
        finally:
            try:
                box.logout()
            except Exception:
                pass


# --- the runner -------------------------------------------------------------------------------------------

def alive(pid):
    if not pid:
        return True
    try:
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not h:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(h)
        return code.value == 259
    except Exception:
        return True


def adapters_in(w, role):
    return re.findall(r"^\s*(a\d+) note ", w.text(f"find prop:role={role}"), re.M)


def run(w, role, with_pid):
    running = {}                         # fid -> (Adapter, fingerprint)
    checked = 0.0
    while alive(with_pid):
        if time.time() - checked >= CHECK_S:
            checked = time.time()
            try:
                wanted = {}
                for fid in adapters_in(w, role):
                    props, text = read_adapter(w, fid)
                    actor = props.get("name", "")
                    if not re.fullmatch(r"[a-z][a-z0-9-]{1,30}", actor) or actor == OWNER:
                        wanted[fid] = (None, f"needs name= (lower case, not {OWNER})", props, text)
                        continue
                    if props.get("on") != "yes":
                        wanted[fid] = (None, "off", props, text)
                    elif not approved(w, fid, actor):
                        wanted[fid] = (None, "waiting for Alex to turn it on", props, text)
                    else:
                        wanted[fid] = ("run", "", props, text)
            except Exception as e:
                log(f"the door did not answer ({e})")
                time.sleep(2)
                continue
            for fid, (want, why, props, text) in wanted.items():
                live = {k: v for k, v in props.items() if k not in ("status", "status_at")}
                fp = hashlib.sha1((json.dumps(live, sort_keys=True) + text).encode()).hexdigest()
                cur = running.get(fid)
                if cur and (want != "run" or cur[1] != fp):
                    cur[0].stop.set()
                    running.pop(fid)
                    cur = None
                if want == "run" and not cur:
                    try:
                        f = Adapter(w, fid, props, text)
                    except Refused as e:
                        if props.get("status") != f"does not read: {e}":
                            write_status(w, fid, props["name"], f"does not read: {e}")
                        continue
                    running[fid] = (f, fp)
                    f.thread.start()
                elif want != "run" and props.get("status") != why:
                    name = props.get("name", "")
                    try:
                        write_status(w, fid, name if re.fullmatch(r"[a-z][a-z0-9-]{1,30}", name) else "adapters", why)
                    except Exception:
                        pass
            for fid in [f for f in running if f not in wanted]:
                running.pop(fid)[0].stop.set()
        for f, _ in list(running.values()):
            f.flush()
        time.sleep(1.0)
    for f, _ in running.values():
        f.stop.set()


def main():
    door = arg("--door", os.environ.get("DESKD", "http://127.0.0.1:8794"))
    world, role = arg("--world", "frontier"), arg("--role", "adapter")
    with_pid = int(arg("--with", "0") or 0)
    global OWNER
    if role != "adapter":            # a scratch role for trying an adapter may name its approver; the real one never
        OWNER = arg("--owner", OWNER)
    STATE.mkdir(parents=True, exist_ok=True)
    lock = STATE / ("adapters.lock" if role == "adapter" else f"adapters-{role}.lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            other = int(lock.read_text().strip() or 0)
        except Exception:
            other = 0
        if other and other != os.getpid() and alive(other):
            log(f"another adapters runner ({other}) holds {lock}; exiting")
            sys.exit(76)
        lock.unlink(missing_ok=True)
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    log(f"adapters: door {door}, world {world}, role {role}, pid {os.getpid()}")
    try:
        run(World(door, world), role, with_pid)
    except KeyboardInterrupt:
        pass
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
