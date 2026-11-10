"""voice.py (a8901, Sable's Voice with JEFF step 3, 21 Oct): Alex speaks to JEFF from the home base, on his machine.

What it is: the home base's ears and mouth, nothing more. The world says what a press does (the lens home-voice: the
microphone, his words, the line it sends) and this module does only what the world cannot: listen with Windows' own
local recognizer, say words with Windows' own local voice, and report what it hears as the host's rows
(witnessed:voice, never the world log). It sends no line itself: the painter's `on spoken` act sends his final words as
one line, with a gesture id made from the utterance, so the door refuses a second (deskd: 'already done').

The engines (one interface: listen(source), stop(), say(id, text, target), hush(); they call back event(dict)):
    FakeEngine      tests: scripted words, no audio at all
    SapiEngine      voice/voice_host.ps1, a PowerShell child on System.Speech: the installed en-US dictation engine
                    and installed voices; from the default microphone and to the default device only in live use,
                    from and into WAV files for tests (files_probe.py)

Gates, all failing closed (Voice.gate): the switch (the home-base note's voice=on; off by default: JEFF activates),
Alex's consent on his own draft (voice=allowed; never asked here, never assumed from Windows' privacy setting), the home
base shown, and Windows saying a banner would be shown now (notify.state(): a full-screen game or app, a locked screen,
presentation mode or 'unknown' refuse, and stop a listening that is under way). Nothing schedules a wake.

Listening ends on a press of the microphone, Escape (the painter), SILENCE seconds with nothing heard, the home base
hidden, a game, or the child ending. Each finished utterance has its own id; it is kept as a row until KEEP seconds
have passed, so two said close together are two rows and two lines. Tentative words are a row field only: they never
act. The readback, 'Heard: <words>', is the desk's own, said at once; JEFF's answer is read when the painter asks
(voice.say <line id> <words>), once per line id. Any press of the microphone or the stop hushes the voice; his words
heard while it speaks hush it too, unless they are the voice's own words coming back through the microphone (echo()).

a9138: before it lights, a listen asks the engine for the microphone's name (engine.device(): Windows' name for the
endpoint a listen would use, read from its property store; nothing opened). The state row carries it (device, and mic
found / none / unknown), so the lens says 'Listening on <name>' and a wrong default reads as its name, not as silence.
With no input device it does not light: mic=none, and the lens says so.
"""
import json
import subprocess
import threading
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
SILENCE = 4.0           # seconds with nothing heard that end a listening
KEEP = 900.0            # seconds a final utterance stays a row (the painter sends it once; the door refuses repeats);
                        # while one is kept, JEFF's answers after it are read aloud (the lens home-voice)
ECHO = 0.6              # a heard line whose words are this share of what the voice is saying is the voice itself
MAX_WORDS = 600         # what the voice reads aloud at most, in characters' worth of words (a long answer is cut)

CONSENT_TEXT = ("Talk to JEFF by voice: it listens only while the microphone is lit, and your voice stays on this "
                "computer (Windows' own speech).",
                "Your words go to JEFF as a line of text, as if you had typed them; his answer is read aloud.")


def _words(text):
    return [w for w in "".join(c.lower() if c.isalnum() or c == "'" else " " for c in str(text)).split() if w]


def echo(heard, said):
    """Is `heard` the voice's own words `said` coming back through the microphone? Most of its words are among them."""
    h, s = _words(heard), set(_words(said))
    return bool(h) and bool(s) and sum(w in s for w in h) / len(h) >= ECHO


class FakeEngine:
    """Tests: what a recognizer and a voice would say, scripted. Nothing is listened to or played."""

    def __init__(self, mic="Microphone (Fake Headset)"):
        self.calls, self.event = [], None
        self.listening = False
        self.speaking = None
        self.mic = mic                        # the name device() reads; "" no input device, None unreadable

    def device(self):
        self.calls.append(("device",))
        return self.mic

    def listen(self, source="mic"):
        self.calls.append(("listen", source))
        self.listening = True
        self.event({"ev": "listening", "from": source})

    def stop(self):
        self.calls.append(("stop",))
        if self.listening:
            self.listening = False
            self.event({"ev": "stopped", "why": "stopped"})

    def say(self, sid, text, target="device"):
        self.calls.append(("say", sid, text, target))
        if self.speaking:
            self.event({"ev": "spoke", "id": self.speaking, "cancelled": True})
        self.speaking = sid
        self.event({"ev": "speaking", "id": sid})

    def hush(self):
        self.calls.append(("hush",))
        if self.speaking:
            sid, self.speaking = self.speaking, None
            self.event({"ev": "spoke", "id": sid, "cancelled": True})

    # what a test makes the engine hear or finish
    def hear(self, text):
        self.event({"ev": "hyp", "text": text})

    def finish(self, text, conf=0.9):
        self.event({"ev": "final", "text": text, "conf": conf})

    def done_speaking(self):
        if self.speaking:
            sid, self.speaking = self.speaking, None
            self.event({"ev": "spoke", "id": sid, "cancelled": False})


class SapiEngine:
    """Windows' own speech through voice_host.ps1 (System.Speech, local). `source` is "mic" or a WAV path; `target`
    is "device" or a WAV path. The child ends when this process closes its stdin or ends."""

    def __init__(self, script=HERE / "voice" / "voice_host.ps1"):
        self.event, self.ready = None, threading.Event()
        self.info = {}
        self.named, self.name = threading.Event(), None
        self.proc = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(script)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
            errors="replace", bufsize=1, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for raw in self.proc.stdout:
            try:
                ev = json.loads(raw)
            except ValueError:
                continue
            if ev.get("ev") == "ready":
                self.info = ev
                self.ready.set()
            if ev.get("ev") == "device":
                self.name = ev.get("name")
                self.named.set()
            if self.event:
                self.event(ev)
        self.ready.set()
        if self.event:
            self.event({"ev": "stopped", "why": "the speech child ended"})

    def _send(self, cmd):
        try:
            self.proc.stdin.write(json.dumps(cmd) + "\n")
            self.proc.stdin.flush()
        except (OSError, ValueError):
            if self.event:
                self.event({"ev": "error", "where": "send", "why": "the speech child is gone"})

    def device(self, wait=3.0):
        """The name of the microphone a listen would use, read from Windows (voice_host.ps1 `device`: its property
        store only, nothing opened); "" when there is no input device, None when it could not be read in time."""
        self.ready.wait(wait * 5)
        self.named.clear()
        self._send({"do": "device"})
        return self.name if self.named.wait(wait) else None

    def listen(self, source="mic"):
        self._send({"do": "listen", "from": "mic" if source == "mic" else "file", "path": "" if source == "mic"
                    else str(source), "silence": SILENCE * 2})          # the controller's SILENCE ends it first

    def stop(self):
        self._send({"do": "stop"})

    def say(self, sid, text, target="device"):
        self._send({"do": "say", "id": sid, "text": text, "to": "device" if target == "device" else "file",
                    "path": "" if target == "device" else str(target)})

    def hush(self):
        self._send({"do": "hush"})

    def close(self):
        self._send({"do": "quit"})
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


class Voice:
    """One home base's voice. `engine` as above; `publish(rows)` keeps the rows (witnessed:voice); `gate()` -> None
    or why listening/speaking may not happen now; `clock` for tests. Every public call answers a short line or raises
    Refused, as host verbs do."""

    def __init__(self, engine, publish=None, gate=None, clock=time.time, source="mic", target="device", jeff=None):
        self.engine, self.publish, self.gate, self.clock = engine, publish or (lambda rows: None), gate, clock
        self.jeff = jeff or (lambda: "unknown")        # -> "working", "idle" or "unknown", as the house says now
        self.source, self.target = source, target
        self.lock = threading.RLock()
        self.state, self.why = "off", ""
        self.tentative = ""
        self.utterance = None
        self.finals = []                      # [{utterance, words, at, conf}]
        self.speaking, self.speaking_text, self.spoke_at, self.last_said = None, "", 0.0, ""
        self.said = set()                     # line ids read aloud once
        self.heard_at = 0.0
        self.device, self.mic = "", "unknown"  # a9138: the microphone's name, and found / none / unknown
        engine.event = self.event
        self._rows()

    # -- the rows the lens reads
    def rows(self):
        now = self.clock()
        self.finals = [f for f in self.finals if now - f["at"] < KEEP]
        jeff = self.jeff() if self.finals else "unknown"
        for f in self.finals:                 # what the house said of JEFF since the line was heard, never guessed
            if jeff == "idle":
                f["idle_since"] = True
            if jeff == "working" and (f["idle_since"] or not f["busy_at"]):
                f["answering"] = True
        out = [{"kind": "state", "state": self.state, "tentative": self.tentative, "aloud": "yes" if self.speaking else "no",
                "speaking": self.speaking or "", "why": self.why, "utterance": self.utterance or "",
                "device": self.device, "mic": self.mic,
                "consent_1": CONSENT_TEXT[0], "consent_2": CONSENT_TEXT[1]}]
        out += [{"kind": "final", "utterance": f["utterance"], "words": f["words"], "conf": round(f["conf"], 2),
                 "at": round(f["at"], 1), "jeff": self._jeff_word(f, jeff)} for f in self.finals]
        return out

    @staticmethod
    def _jeff_word(f, jeff):
        if jeff == "working":
            return "JEFF is answering" if f.get("answering") else "JEFF is finishing an answer; yours is next"
        if jeff == "idle":
            return "sent to JEFF" + (" · he has had a turn since" if f.get("answering") else "")
        return "sent to JEFF"

    def _rows(self):
        try:
            self.publish(self.rows())
        except Exception:                     # a rows file not written never stops the voice
            pass

    def _refuse_if_gated(self, what):
        why = self.gate() if self.gate else None
        if why:
            raise Refused(f"{what}: {why}")

    # -- presses
    def listen(self):
        with self.lock:
            self._refuse_if_gated("voice.listen")
            self.hush_now()                   # pressing the microphone stops the voice at once
            if self.state == "listening":
                return "already listening"
            # a9138: name the microphone before lighting, so a wrong default reads as its name, not as silence; with
            # no input device it says so and does not light. Read only: nothing is opened until engine.listen
            name = self.engine.device() if self.source == "mic" else f"the file {Path(str(self.source)).name}"
            if name == "":
                self.state, self.why, self.tentative = "off", "no microphone found", ""
                self.device, self.mic = "", "none"
                self._rows()
                return "not listening: no microphone found (Windows has no input device)"
            self.device, self.mic = name or "a microphone Windows did not name", "found"
            self.state, self.why, self.tentative = "listening", "", ""
            self.utterance = uuid.uuid4().hex[:12]
            self.heard_at = self.clock()
            self._rows()
            self.engine.listen(self.source)
            return "listening (the microphone is lit)"

    def stop(self, why="stopped"):
        with self.lock:
            self.hush_now()
            if self.state != "listening":
                self._rows()
                return "not listening"
            self.state, self.why, self.tentative = "off", why, ""
            self._rows()
            self.engine.stop()
            return f"stopped listening ({why})"

    def say(self, sid, text):
        """Read words aloud once per id (a JEFF line id, or heard-<utterance> for the readback)."""
        with self.lock:
            self._refuse_if_gated("voice.say")
            sid, text = str(sid).strip(), " ".join(str(text).split())
            if not sid or not text:
                raise Refused("voice.say takes an id and the words: voice.say <line id> <words>")
            if sid in self.said:
                return f"already read {sid}"
            self.said.add(sid)
            if len(text) > MAX_WORDS:
                text = text[:MAX_WORDS].rsplit(" ", 1)[0] + ". The rest is in the Conversation."
            self.speaking, self.speaking_text = sid, text
            self._rows()
            self.engine.say(sid, text, self.target)
            return f"reading {sid} aloud"

    def hush_now(self):
        if self.speaking:
            self.engine.hush()
            self.speaking = None
            self._rows()
            return "the voice stopped"
        return "the voice was quiet"

    def hush(self):
        with self.lock:
            return self.hush_now()

    def tick(self):
        """Each second while it runs (the home base's tend): silence and the gates end a listening."""
        with self.lock:
            if self.state != "listening":
                if self.finals:
                    self._rows()              # what JEFF is doing about his lines (the rows file changes only then)
                return
            why = self.gate() if self.gate else None
            if why:
                self.stop(why)
            elif self.clock() - self.heard_at >= SILENCE:
                self.stop("silence")

    # -- what the engine says
    def _is_echo(self, text):
        recent = self.speaking_text if self.speaking else (self.last_said if self.clock() - self.spoke_at < 1.5 else "")
        return bool(recent) and echo(text, recent)

    def event(self, ev):
        with self.lock:
            kind = ev.get("ev")
            if kind == "hyp":
                if self.state != "listening" or self._is_echo(ev.get("text", "")):
                    return
                self.heard_at = self.clock()
                if self.speaking:
                    self.hush_now()           # he speaks: the voice stops at once
                self.tentative = str(ev.get("text") or "")
                self._rows()
            elif kind == "detected":
                if self.state == "listening" and not self.speaking:
                    self.heard_at = self.clock()
            elif kind == "final":
                words = " ".join(str(ev.get("text") or "").split())
                if self.state != "listening" or not words or self._is_echo(words):
                    self.tentative = ""
                    self._rows()
                    return
                self.heard_at = self.clock()
                if self.speaking:
                    self.hush_now()
                u = self.utterance or uuid.uuid4().hex[:12]
                if not any(f["utterance"] == u for f in self.finals):
                    self.finals.append({"utterance": u, "words": words, "at": self.clock(),
                                        "conf": float(ev.get("conf") or 0), "busy_at": self.jeff() == "working",
                                        "idle_since": False, "answering": False})
                self.utterance = uuid.uuid4().hex[:12]        # the next utterance has its own id
                self.tentative = ""
                self._rows()
                try:
                    self.say(f"heard-{u}", f"Heard: {words}")   # the desk's own readback, at once
                except Refused:
                    pass
            elif kind == "stopped":
                if self.state == "listening":
                    self.state, self.why, self.tentative = "off", str(ev.get("why") or "stopped"), ""
                    self._rows()
            elif kind == "spoke":
                if ev.get("id") == self.speaking:
                    self.last_said, self.spoke_at = self.speaking_text, self.clock()
                    self.speaking, self.speaking_text = None, ""
                    self._rows()
            elif kind == "device":                # the child names it again as it starts listening
                if self.state == "listening" and ev.get("name"):
                    self.device = str(ev["name"])
                    self._rows()
            elif kind == "error":
                self.why = f"{ev.get('where')}: {ev.get('why')}"
                if ev.get("where") == "listen":
                    self.state = "off"
                    if ev.get("why") == "no microphone":   # unplugged between the name and the listen
                        self.device, self.mic, self.why = "", "none", "no microphone found"
                self._rows()


class Refused(Exception):
    pass


# -- the home base's own gates and verbs (host_verbs.py calls these) --------------------------------------------------
def consent_of(door, world, who):
    """Alex's own word, on his conversation draft: voice=allowed, never, or nothing yet. Read through the door each
    time; a door that does not answer is not a yes."""
    import urllib.request
    try:
        line = f"find prop:role=conversation-draft,prop:actor={who}"
        body = json.dumps({"session": world, "as": "hud", "line": line}).encode("utf-8")
        r = json.loads(urllib.request.urlopen(urllib.request.Request(door + "/api/do", data=body, method="POST"),
                                              timeout=3).read())
    except (OSError, ValueError):
        return "unknown"
    text = r.get("text") or ""
    for word in ("allowed", "never"):
        if f" voice={word}" in text:
            return word
    return ""


def gate_for(hud):
    """-> None, or why the home base may not listen or speak now."""
    import notify
    if (getattr(hud, "settings", {}) or {}).get("voice", "off") != "on":
        return "voice is off on the home base (its switch, voice=on, is JEFF's to set)"
    if not getattr(hud, "shown", False):
        return "the home base is hidden"
    try:
        st = notify.state()
    except Exception:
        st = "unknown"
    if st not in ("shown", "held back: quiet time (the first hour after Windows was set up)"):
        return f"Windows says {st}: no listening during a game, a full-screen app or a locked screen"
    kept = getattr(hud, "_voice_consent", None)          # a yes is read again after 5 s; anything else at once
    if kept and time.time() - kept < 5:
        said = "allowed"
    else:
        said = consent_of(hud.door, hud.a.world, hud.a.who)
        hud._voice_consent = time.time() if said == "allowed" else None
    if said != "allowed":
        return {"never": "Alex turned voice off for good", "unknown": "his consent could not be read"}.get(
            said, "Alex has not allowed it yet (the first press asks him)")
    return None


def jeff_doing(world, actor="jeff"):
    """What the house says JEFF is doing now, from its own heartbeat file (as the lens's house rows read it): working,
    idle, or unknown when the house is not beating (older than 30 s) or names no JEFF."""
    import witnessed
    try:
        st = json.loads((witnessed.ROOT / str(world) / "house.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "unknown"
    if time.time() - float(st.get("beat") or 0) > 30:
        return "unknown"
    for r in (st.get("residents") or {}).values():
        if str(r.get("actor") or "").lower() == actor:
            return "working" if r.get("doing") == "working" else "idle"
    return "unknown"


def of(hud):
    """The home base's one Voice, made at its first use (the speech child starts then, never before)."""
    v = getattr(hud, "voice", None)
    if v is None:
        import witnessed

        def publish(rows):
            if witnessed.write(hud.a.world, "voice", rows, by="hud", changed_only=True):
                threading.Thread(target=hud.tell_pages, daemon=True).start()     # never inside the voice's lock
        v = hud.voice = Voice(SapiEngine(), publish=publish, gate=lambda: gate_for(hud),
                              jeff=lambda: jeff_doing(hud.a.world))
    return v
