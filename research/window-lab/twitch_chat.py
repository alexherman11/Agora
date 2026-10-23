"""Twitch chat into the world: a read-only bridge (Claude, 22 Oct 2026, from Alex's ask).

Reads one channel's public chat and appends each message to a world chat, signed `twitch`.
The chat (role=twitch-chat) holds the settings, so they live in the world, not here:
  channel=<login>   which channel to read (empty: wait)
  feed=on|off       off: disconnect and wait (the off switch)
The bridge writes back status=, status_at= on the same chat.

How it reads Twitch: the chat IRC server, logged in anonymously (a justinfan nick, no token).
That is read-only by construction: an anonymous login cannot send, and no account,
key or app registration is involved. Twitch's IRC page documents only token logins
(read 22 Oct); anonymous reading is what public chat overlays use, so it may stop working.

Each line reads `Name: words`, so a viewer's line never opens with an @ and never calls
anyone in the world (an @ later in a line is only a mention). Lines carry user=, color=,
twitch_id= (and kind=notice for subs and raids).

Run:  python twitch_chat.py [--door http://127.0.0.1:8794] [--world frontier] [--with <pid>]
One bridge at a time (a lock in house-state; a second exits 76). `--with` exits when that
process does, the way docs_sync follows the keeper.
"""

import hashlib
import json
import os
import random
import re
import socket
import ssl
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE = HERE.parent / "text-desk-lab" / "notation" / "house-state"
ACTOR = "twitch"
# --role: point the bridge at a scratch chat when trying it
ROLE = sys.argv[sys.argv.index("--role") + 1] if "--role" in sys.argv[:-1] else "twitch-chat"
IRC = ("irc.chat.twitch.tv", 6697)
BATCH_S = 1.0          # gather messages this long before one write
CHECK_S = 15.0         # how often the world's settings are read again
MAX_BATCH = 40         # a flood is cut, and the cut is said


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv[:-1] else default


DOOR = arg("--door", os.environ.get("DESKD", "http://127.0.0.1:8794"))
WORLD = arg("--world", "frontier")
WITH = int(arg("--with", "0") or 0)


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
    print(line, flush=True)


# --- the world ---------------------------------------------------------------------------

def do(line, whole=True):
    body = json.dumps({"session": WORLD, "as": ACTOR, "line": line, "whole": whole}).encode()
    req = urllib.request.Request(DOOR + "/api/do", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def quote(v):
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def find_chat():
    """The chat tagged role=ROLE: (id, channel, feed). None when there is none."""
    r = do(f"find prop:role={ROLE}")
    m = re.search(r"\b(a\d+) chat ", r.get("text") or "")
    if not m:
        return None
    cid = m.group(1)
    head = (do(f"examine {cid}").get("text") or "").split("\n", 1)[0]
    ch = re.search(r"(?:^| )channel=(\S*)", head)
    fd = re.search(r"(?:^| )feed=(\S*)", head)
    channel = (ch.group(1) if ch else "").strip().lower().lstrip("#")
    channel = re.sub(r"^https?://(www\.)?twitch\.tv/", "", channel).strip("/")
    return cid, channel, (fd.group(1) if fd else "on").lower()


def status(cid, words):
    try:
        # the fence refuses a prop edit by one who has not looked since the thing changed
        out = do(f"examine {cid}\ndo prop {cid} status={quote(words)} "
                 f"status_at={quote(time.strftime('%d %b %H:%M'))}", whole=False)
        if out.get("error"):
            log(f"status refused: {out['error'][-200:]}")
    except Exception as e:  # the status is a courtesy; the feed goes on
        log(f"status not written: {e}")


def append(cid, msgs):
    """Write a batch as one /api/do, one append per line. The gesture id is made from Twitch's
    message ids, so a retry after a lost answer is answered `already done`, never written twice.
    Values are quoted, so a `;` or a verb inside a message stays words (tried 22 Oct)."""
    lines = []
    for m in msgs:
        extra = " kind=notice" if m.get("notice") else ""
        lines.append(f"do append {cid} line={quote(m['line'])} words={quote(m['words'])} "
                     f"user={quote(m['user'])} "
                     f"color={quote(m['color'])} twitch_id={quote(m['id'])}{extra}")
    gesture = "tw-" + hashlib.sha1("|".join(m["id"] for m in msgs).encode()).hexdigest()[:24]
    body = json.dumps({"session": WORLD, "as": ACTOR, "line": "\n".join(lines),
                       "gesture": gesture}).encode()
    req = urllib.request.Request(DOOR + "/api/do", body, {"Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                out = json.load(r)
            if out.get("error"):
                log(f"refused: {out['error'][:300]}")
            return
        except Exception as e:
            log(f"write failed ({e}); retry {attempt + 1}")
            time.sleep(2 * (attempt + 1))
    log(f"gave up on {len(msgs)} message(s)")


# --- Twitch ------------------------------------------------------------------------------

def tags_of(raw):
    out = {}
    for kv in raw.split(";"):
        k, _, v = kv.partition("=")
        out[k] = (v.replace("\\s", " ").replace("\\:", ";").replace("\\r", "").replace("\\n", "")
                  .replace("\\\\", "\\"))
    return out


def parse(line):
    """One IRC line into (command, tags, prefix, params, trailing)."""
    tags = {}
    if line.startswith("@"):
        raw, _, line = line.partition(" ")
        tags = tags_of(raw[1:])
    prefix = ""
    if line.startswith(":"):
        prefix, _, line = line.partition(" ")
        prefix = prefix[1:]
    line, _, trailing = line.partition(" :")
    parts = line.split()
    return (parts[0] if parts else ""), tags, prefix, parts[1:], trailing


def message(cmd, tags, prefix, trailing):
    """A chat or notice line for the world, or None."""
    who = tags.get("display-name") or prefix.split("!", 1)[0]
    mid = tags.get("id") or f"{time.time():.6f}"
    color = tags.get("color") or ""
    if cmd == "PRIVMSG":
        words = trailing
        if words.startswith("\x01ACTION ") and words.endswith("\x01"):   # /me
            words = "* " + words[8:-1]
        return {"line": f"{who}: {words}", "user": who, "color": color, "id": mid, "words": words}
    if cmd == "USERNOTICE":        # subs, gifts, raids, announcements: Twitch's own words for it
        system = tags.get("system-msg") or tags.get("msg-id") or "notice"
        said = f"{system} {trailing}".strip() if trailing else system
        return {"line": f"★ {said}", "user": who, "color": color, "id": mid, "notice": True,
                "words": f"★ {said}"}
    return None


def connect(channel):
    raw = socket.create_connection(IRC, timeout=30)
    s = ssl.create_default_context().wrap_socket(raw, server_hostname=IRC[0])
    nick = f"justinfan{random.randint(10000, 99999)}"
    s.sendall(("CAP REQ :twitch.tv/tags twitch.tv/commands\r\n"
               f"PASS SCHMOOPIIE\r\nNICK {nick}\r\nJOIN #{channel}\r\n").encode())
    s.settimeout(1.0)
    return s


def alive(pid):
    if not pid:
        return True
    try:
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)   # QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(h)
        return code.value == 259                                      # STILL_ACTIVE
    except Exception:
        return True


# --- the loop ----------------------------------------------------------------------------

def run():
    sock, joined, buf, pending = None, "", b"", []
    cid, channel, feed, checked, said = None, "", "on", 0.0, ""
    backoff, next_try, last_rx, first_at = 2.0, 0.0, time.time(), 0.0

    def say(words):
        nonlocal said
        if cid and words != said:
            said = words
            status(cid, words)
            log(words)

    while True:
        if not alive(WITH):
            log(f"process {WITH} is gone; stopping")
            break
        now = time.time()
        if now - checked >= CHECK_S:
            checked = now
            try:
                found = find_chat()
            except Exception as e:
                log(f"the door did not answer ({e})")
                found = (cid, channel, feed) if cid else None
            if found:
                cid, channel, feed = found
            want = channel if (cid and channel and feed != "off") else ""
            if want != joined and sock:
                try:
                    sock.close()
                except Exception:
                    pass
                sock, joined = None, ""
                say("off" if feed == "off" else
                    "waiting for a channel" if not channel else f"switching to #{want}")
            if not want:
                if cid:
                    say("off" if feed == "off" else "waiting for a channel")
                time.sleep(1)
                continue

        if not sock:
            if now < next_try:
                time.sleep(0.5)
                continue
            try:
                sock, joined, buf, last_rx = connect(want), want, b"", time.time()
                backoff = 2.0
                say(f"live: reading #{joined} (read-only)")
            except Exception as e:
                sock, next_try = None, time.time() + backoff
                say(f"cannot reach Twitch ({e.__class__.__name__}); "
                    f"trying again in {int(backoff)} s")
                backoff = min(backoff * 2, 120)
                continue

        try:
            data = sock.recv(8192)
            if not data:
                raise ConnectionError("closed")
            buf += data
            last_rx = time.time()
        except TimeoutError:
            if time.time() - last_rx > 330:            # Twitch pings every ~5 min
                sock.close()
                sock = None
                say("Twitch went quiet; reconnecting")
        except Exception as e:
            try:
                sock.close()
            except Exception:
                pass
            sock, next_try = None, time.time() + backoff
            say(f"disconnected ({e.__class__.__name__}); reconnecting")
            continue

        while sock and b"\r\n" in buf:
            raw, buf = buf.split(b"\r\n", 1)
            cmd, tags, prefix, params, trailing = parse(raw.decode("utf-8", "replace"))
            if cmd == "PING":
                sock.sendall(f"PONG :{trailing or 'tmi.twitch.tv'}\r\n".encode())
            elif cmd == "RECONNECT":
                sock.close()
                sock = None
                say("Twitch asked for a reconnect; reconnecting")
            elif cmd == "NOTICE" and params and params[0] == f"#{joined}":
                say(f"Twitch says: {trailing}")
            else:
                m = message(cmd, tags, prefix, trailing)
                if m:
                    if not pending:
                        first_at = time.time()
                    pending.append(m)

        if pending and time.time() - first_at >= BATCH_S:
            batch, pending = pending[:MAX_BATCH], []
            append(cid, batch)
            if len(batch) == MAX_BATCH:
                log(f"a flood: wrote {MAX_BATCH} messages and let the rest of that moment go")


def main():
    STATE.mkdir(parents=True, exist_ok=True)
    lock = STATE / ("twitch_chat.lock" if ROLE == "twitch-chat" else f"twitch_chat-{ROLE}.lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            other = int(lock.read_text().strip() or 0)
        except Exception:
            other = 0
        if other and other != os.getpid() and alive(other):
            log(f"another bridge ({other}) holds {lock}; exiting")
            sys.exit(76)
        lock.unlink(missing_ok=True)
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    log(f"twitch bridge: door {DOOR}, world {WORLD}, pid {os.getpid()}")
    try:
        run()
    except KeyboardInterrupt:
        pass
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
