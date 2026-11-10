# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_scripts_mirror (a6249, 17 Oct 2026): Alex's scripts as notes, kept in step with their files both ways.

    python test_scripts_mirror.py

Builds its own small world (roomworld.py) and works on copies of the Rocket League timer in a temp folder; never on
Alex's files and never through deskd. The house is played by dispatching each line as `house`. Also dry-runs the
weekend version of the timer for every day of a week (PowerShell -DryRun, which never watches or closes anything),
and parses both versions with PowerShell's own parser (never run).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import roomworld        # noqa: E402
import scripts_mirror   # noqa: E402

LAB = HERE.parents[1] / "desktop" / "scripts"
ORIGINAL = LAB / "originals" / "RocketLeagueTimer.2026-10-17.original.ps1"
NEW = LAB / "RocketLeagueTimer.ps1"

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build()
W = D.world
D._per = {}


def be(me):
    per = D._per
    W.me = me
    if me not in per:
        per[me] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[me]


def say(me, line):
    be(me)
    r = D.dispatch("desk", {"line": line, "whole": True, "reply": uuid.uuid4().hex})
    return (r.get("text") or "") + (r.get("error") or "")


def house(line):
    return say("house", line)


def make(parent, how):
    say("jeff", f"look {parent} :1")
    got = say("jeff", f"do create {parent} {how}")
    m = re.search(r"created (a\d+|f\d+)", got)
    if not m:
        raise RuntimeError(got)
    return m.group(1)


def subject(aid):
    return W.subjects[W.nodes[aid]["subject"]]


def edit(aid, text):
    say("alex", f"read {aid} :3")
    return say("alex", f"do rewrite {aid} text={scripts_mirror.quote(text)}")


TMP = Path(tempfile.mkdtemp(prefix="scripts-mirror-"))
STATE = TMP / "state"
STATE.mkdir()
PC = TMP / "RocketLeagueTimer"
PC.mkdir()
FILE = PC / "RocketLeagueTimer.ps1"
# the copy is written as Windows writes files (BOM, CRLF), so a write that loses either shows
orig_text = ORIGINAL.read_text(encoding="utf-8").replace("\r\n", "\n")
FILE.write_bytes(b"\xef\xbb\xbf" + orig_text.replace("\n", "\r\n").encode("utf-8"))

calls = []


def checker(path, text):
    calls.append(path)
    return "line 3: Missing closing '}'" if "BROKEN" in text else None


M = scripts_mirror.Scripts("roomworld", STATE, allowed=True, check=checker, clock=lambda: "17 Oct 2026 10:00")

shelf = make(R.HOME, 'kind=surface title="Scripts" layout=column')
note = make(shelf, f'kind=note title="Rocket League timer" role=script file="{FILE.as_posix()}" '
                   f'settings="weekday_minutes weekend_minutes" settings_file=RocketLeagueTimer.settings.json '
                   f'weekday_minutes=30 weekend_minutes=60')

# 1. first meeting: the file is the truth, the original is kept, the settings file is made from the note
M.step(W, house)
check("first meeting fills the note with the file's text, exactly", subject(note)["text"] == orig_text,
      repr(subject(note)["text"][:200]))
originals = list((PC / "agora-history").glob("RocketLeagueTimer.*.original.ps1"))
check("the original is kept beside the file, dated, byte for byte",
      len(originals) == 1 and originals[0].read_bytes() == FILE.read_bytes(), originals)
settings = json.loads((PC / "RocketLeagueTimer.settings.json").read_text(encoding="utf-8"))
check("the settings file is made from the note's props, as numbers",
      settings == {"weekday_minutes": 30, "weekend_minutes": 60}, settings)
p = subject(note)["props"]
check("the note says it is in step and when it was last edited",
      p.get("sync") == "In step with its file." and p.get("edited") == "17 Oct 2026 10:00, on the PC", p)
before = FILE.read_bytes()
M.step(W, house)
check("a second pass with nothing changed writes nothing", FILE.read_bytes() == before
      and len(list((PC / "agora-history").iterdir())) == 1)

# 2. an edit in the world writes the file, in its old form, keeping the old one
new_text = NEW.read_text(encoding="utf-8").replace("\r\n", "\n")
got = edit(note, new_text)
check("the edit is taken by the desk", "ok rewrite" in got, got)
M.step(W, house)
raw = FILE.read_bytes()
check("the file now holds the note's text", raw[3:].decode("utf-8").replace("\r\n", "\n") == new_text)
check("its BOM and CRLF line ends are kept", raw.startswith(b"\xef\xbb\xbf") and b"\r\n" in raw
      and b"\n" not in raw.replace(b"\r\n", b""))
history = sorted((PC / "agora-history").iterdir())
check("the version it replaced is kept in agora-history", len(history) == 2
      and any(h.read_bytes() == before for h in history if "original" not in h.name), [h.name for h in history])
check("the text was checked before it was written", calls and calls[-1] == FILE, calls)
check("edited says it was edited here", subject(note)["props"].get("edited") == "17 Oct 2026 10:00, here")

# 3. a change to the file is picked up
on_pc = new_text.replace("[double]$WarnMinutes        = 7,", "[double]$WarnMinutes        = 5,")
FILE.write_bytes(b"\xef\xbb\xbf" + on_pc.replace("\n", "\r\n").encode("utf-8"))
M.step(W, house)
check("a change made on the PC rewrites the note", subject(note)["text"] == on_pc)
check("and says so", subject(note)["props"].get("edited") == "17 Oct 2026 10:00, on the PC")

# 4. the world lagging behind the desk's answer is not an edit: a pass that still sees the old words writes nothing
lagging = type("Lag", (), {})()
old_subject = dict(subject(note), text=new_text)
lagging.subjects = {old_subject["id"]: old_subject}
lagging.appearances_of = lambda sid: [note]
FILE.write_bytes(b"\xef\xbb\xbf" + new_text.replace("\n", "\r\n").encode("utf-8"))      # the PC changes it back
M.step(W, house)                                                                         # note rewritten to new_text
FILE.write_bytes(b"\xef\xbb\xbf" + on_pc.replace("\n", "\r\n").encode("utf-8"))
M.step(W, house)                                                                         # and to on_pc again
stale_subject = dict(subject(note), text=new_text)
lagging.subjects = {stale_subject["id"]: stale_subject}
M.step(lagging, house)
check("a pass that sees the words from before the house's rewrite leaves the file alone",
      FILE.read_bytes()[3:].decode("utf-8").replace("\r\n", "\n") == on_pc)

# 5. both sides changed: nothing written, the note says so in plain words
edit(note, on_pc + "# a line written in the world\n")
FILE.write_bytes(b"\xef\xbb\xbf" + (on_pc + "# a line written on the PC\n").replace("\n", "\r\n").encode("utf-8"))
M.step(W, house)
check("both changed: the file keeps its own line", b"written on the PC" in FILE.read_bytes()
      and b"written in the world" not in FILE.read_bytes())
check("both changed: the note keeps its own line and says neither was written",
      "written in the world" in subject(note)["text"] and "neither was written" in subject(note)["props"].get("sync", ""))
edit(note, on_pc + "# a line written on the PC\n")                     # put one side back: they agree again
M.step(W, house)
check("once they match again the note is in step", subject(note)["props"].get("sync") == "In step with its file.")

# 6. a text that would not parse is never written
good = FILE.read_bytes()
edit(note, "BROKEN {\n")
M.step(W, house)
check("a broken text is not written to the file", FILE.read_bytes() == good)
check("the note says why, in a sentence", "has a mistake (line 3" in subject(note)["props"].get("sync", ""),
      subject(note)["props"].get("sync"))
edit(note, on_pc)
held, real = [0], scripts_mirror.write_file


def held_open(*a, **k):                     # another program holds the file: the replace fails, as on Windows
    held[0] += 1
    raise PermissionError("could not replace RocketLeagueTimer.ps1")


scripts_mirror.write_file = held_open
copies = len(list((PC / "agora-history").iterdir()))
M.step(W, house)
M.step(W, house)
scripts_mirror.write_file = real
check("a file held open is not written, and failed tries leave no copies behind",
      held[0] == 2 and FILE.read_bytes() == good and len(list((PC / "agora-history").iterdir())) == copies)
check("the note says it will try again", "tries again" in subject(note)["props"].get("sync", ""))
M.step(W, house)
check("fixed, it is written", FILE.read_bytes()[3:].decode("utf-8").replace("\r\n", "\n") == on_pc)
check("and the version it replaced is kept once", len(list((PC / "agora-history").iterdir())) == copies + 1)

# 7. settings both ways
say("alex", f"look {note} :1")
say("alex", f"do prop {note} weekend_minutes=75")
M.step(W, house)
check("a setting changed here is written to the settings file as a number",
      json.loads((PC / "RocketLeagueTimer.settings.json").read_text())["weekend_minutes"] == 75)
(PC / "RocketLeagueTimer.settings.json").write_text(json.dumps({"weekday_minutes": 20, "weekend_minutes": 75}))
M.step(W, house)
check("a setting changed on the PC reaches the note", str(subject(note)["props"].get("weekday_minutes")) == "20",
      subject(note)["props"])
say("alex", f"look {note} :1")
say("alex", f"do prop {note} weekday_minutes=lots")
M.step(W, house)
check("a setting that must be a number is refused, and the file keeps the last good value",
      json.loads((PC / "RocketLeagueTimer.settings.json").read_text())["weekday_minutes"] == 20
      and "must be a number" in subject(note)["props"].get("sync", ""), subject(note)["props"].get("sync"))

# 8. first=note: a note that holds the next version writes it out at the first meeting
FILE2 = PC / "Second.ps1"
FILE2.write_text(orig_text, encoding="utf-8")
second = make(shelf, f'kind=note title="Second" role=script first=note file="{FILE2.as_posix()}" '
                     f'text={scripts_mirror.quote(new_text)}')
M.step(W, house)
check("first=note: the note's text is written to the file", FILE2.read_text(encoding="utf-8") == new_text)
check("first=note: the file as it was is kept as the original",
      (PC / "agora-history" / f"Second.{__import__('time').strftime('%Y-%m-%d')}.original.ps1").read_text(
          encoding="utf-8") == orig_text)

# 9. only the live world's house touches files
quiet = scripts_mirror.Scripts("frontier-try", TMP / "state2")
check("a copy of the world (frontier-try) never writes files", quiet.allowed is False)
os.environ.pop("HOUSE_KEEPER", None)
check("nor does frontier without the keeper", scripts_mirror.Scripts("frontier", TMP / "state2").allowed is False)
FILE2.write_text("changed", encoding="utf-8")
quiet.step(W, house)
check("and a step there does nothing", FILE2.read_text(encoding="utf-8") == "changed")

# 10. the real parser: both versions parse, a broken one does not (PowerShell's parser; nothing is run)
if shutil.which("powershell.exe"):
    check("the original parses", scripts_mirror.problem(ORIGINAL, orig_text) is None)
    check("the weekend version parses", scripts_mirror.problem(NEW, new_text) is None,
          scripts_mirror.problem(NEW, new_text))
    bad = scripts_mirror.problem(NEW, new_text.replace("function Get-Today {", "function Get-Today ", 1))
    check("a broken version is caught with its line", bool(bad) and bad.startswith("line "), bad)

    # 11. the weekend rule, dry run: every day of a week, from a Monday
    def dry(*args):
        p = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                            str(NEW), "-DryRun", *args], capture_output=True, text=True, timeout=60)
        return p.stdout
    settings_file = TMP / "dry.settings.json"
    out = dry("-Clock", "2026-10-12", "-SettingsFile", str(settings_file))
    print(out.rstrip())
    want = {"Monday": 30, "Tuesday": 30, "Wednesday": 30, "Thursday": 30, "Friday": 30, "Saturday": 60, "Sunday": 60}
    got = {m.group(1): int(m.group(2)) for m in re.finditer(r"(\w+day)\s+limit (\d+) min", out)}
    check("dry run, no settings file: 30 on weekdays, 60 on Saturday and Sunday", got == want, got)
    warns = re.findall(r"after (\d+) min: '7 minutes of Rocket League left", out)
    check("dry run: each day says when its 7-minute notice comes (23 on weekdays, 53 at the weekend)",
          warns == ["23"] * 5 + ["53"] * 2, warns)
    check("dry run: each day says what the notices at the end say, and the wait for a match stays",
          out.count("closes when this match ends.' (waits up to 10 min for it)") == 7
          and out.count("not in a match: 'Rocket League time is up for today.") == 7, out[-600:])
    check("the notice is an overlay that takes no focus, not a message box",
          "WS_EX_NOACTIVATE" in new_text and ".Popup(" not in new_text)
    settings_file.write_text(json.dumps({"weekday_minutes": 45, "weekend_minutes": 90}), encoding="utf-8")
    out = dry("-Clock", "2026-10-17", "-SettingsFile", str(settings_file))
    print(out.rstrip())
    got = {m.group(1): int(m.group(2)) for m in re.finditer(r"(\w+day)\s+limit (\d+) min", out)}
    check("dry run from a Saturday with the settings file at 45/90: the file's numbers rule",
          got == {d: (90 if d in ("Saturday", "Sunday") else 45) for d in want}, got)
else:
    check("powershell.exe is here to parse and dry-run the timer", False)

shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{len(fails)} failed" if fails else "\nall passed")
sys.exit(1 if fails else 0)
