"""scripts_mirror: Alex's own scripts, carried in the world and kept in step with their files (a6249, 17 Oct 2026).

Alex, 17 Oct: "figure out a way to get access to the scripts ... put some things and scripts into the world so you can
touch them easily". A script is a note with prop role=script and file=<where it lives on his PC>. Its text is the
file's text, and the two stay in step, both ways:

  - the file changed and the note did not: the note is rewritten from the file;
  - the note changed and the file did not: the old file is copied into agora-history/ beside it (dated), the text is
    checked (a PowerShell or Python script must parse), and the file is replaced, keeping its BOM and line endings;
  - both changed: nothing is written; the note's sync= says so in a plain sentence, until one side is put back.

A script's numbers live in its settings file, not in its code: settings=<prop names> lists note props carried to and
from settings_file=<a JSON file> the script reads (the Rocket League timer's weekday_minutes and weekend_minutes),
by the same rule; a setting that was a number must stay one. The first time a file is met it is copied whole into
agora-history/ as <name>.<date>.original<ext>, and the file is the truth: the note is filled from it, unless the note
says first=note (its text is the next version, written out like an edit made here, checked and kept the same way).
A note that seems to change back to the words it held before the house rewrote it is the world not yet showing the
rewrite, and is not carried out (agreed['stale']): make any other edit to send exactly those words back.

The mirror never runs a script. Running one from the world would be a separate house verb, for a script marked safe
(run_here=yes); none is, and one that ends a process, changes a setting or touches a password never will be.

Only the house that keeps the live world (frontier, under the keeper, with a real model) touches files: a copy of the
world (a worker's frontier-try) holds the same notes naming the same files, and must never write them. The last
agreed state of each note (hashes of its text, its file, its settings) is kept in house-state/<world>/scripts.json.
"""
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

HISTORY = "agora-history"


def sha(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def quote(text):
    """A desk value: backslash, quote and dollar escaped, newlines as \\n (a tab passes as itself)."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def read_file(path):
    """-> (text with \\n line ends and no BOM, form) where form says how to write it back as it was."""
    raw = Path(path).read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw[3 if bom else 0:].decode("utf-8")
    return text.replace("\r\n", "\n"), {"bom": bom, "crlf": "\r\n" in text}


def write_file(path, text, form):
    """Replace the file whole (a temp file beside it, then a rename), in its old form."""
    path = Path(path)
    body = text.replace("\r\n", "\n")
    if form.get("crlf"):
        body = body.replace("\n", "\r\n")
    data = (b"\xef\xbb\xbf" if form.get("bom") else b"") + body.encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    for i in range(10):                     # another program may hold the file a moment (Windows)
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.1 * (i + 1))
    os.unlink(tmp)
    raise PermissionError(f"could not replace {path.name}")


def keep(path, label, data=None):
    """Copy the file (or `data`, the bytes it held) into agora-history/ beside it as <stem>.<label><ext>; -> the
    copy's path."""
    path = Path(path)
    folder = path.parent / HISTORY
    folder.mkdir(exist_ok=True)
    dest = folder / f"{path.stem}.{label}{path.suffix}"
    if label.endswith(".original"):                 # one original, ever
        if not dest.exists():
            shutil.copy2(path, dest)
        return dest
    n = 1
    while dest.exists():                            # two writes in one second keep both
        n += 1
        dest = folder / f"{path.stem}.{label}-{n}{path.suffix}"
    if data is None:
        shutil.copy2(path, dest)
    else:
        dest.write_bytes(data)
    return dest


def replace(path, text, form):
    """Write the file and keep the version it replaced; -> that copy's path. Nothing is kept when the write fails (a
    file held open by another program), so a write retried every pass leaves no trail of copies."""
    old = Path(path).read_bytes()
    write_file(path, text, form)
    return keep(path, time.strftime("%Y-%m-%d-%H%M%S"), old)


def problem(path, text):
    """What stops this text being a working script, in one sentence, or None. PowerShell and Python are parsed (never
    run); other kinds are not checked."""
    ext = Path(path).suffix.lower()
    if ext == ".py":
        try:
            compile(text, str(path), "exec")
        except SyntaxError as e:
            return f"line {e.lineno}: {e.msg}"
        return None
    if ext in (".ps1", ".psm1"):
        fd, tmp = tempfile.mkstemp(suffix=ext)
        with os.fdopen(fd, "w", encoding="utf-8-sig") as f:
            f.write(text)
        try:
            cmd = ("$e = $null; [void][System.Management.Automation.Language.Parser]::ParseFile($env:AGORA_PARSE, "
                   "[ref]$null, [ref]$e); foreach ($x in $e) { 'line ' + $x.Extent.StartLineNumber + ': ' + $x.Message }")
            p = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", cmd],
                               capture_output=True, text=True, timeout=60, env={**os.environ, "AGORA_PARSE": tmp},
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except (OSError, subprocess.TimeoutExpired) as e:
            return f"it could not be checked ({type(e).__name__})"
        finally:
            os.unlink(tmp)
        said = p.stdout.strip()
        return said.splitlines()[0] if said else None
    return None


def setting_names(props):
    return [n for n in str(props.get("settings") or "").replace(",", " ").split() if n]


def read_settings(path):
    try:
        got = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        return got if isinstance(got, dict) else {}
    except (OSError, ValueError):
        return {}


def as_value(text, old):
    """A note prop's text as the settings file holds it: a number if it was one (refused if it no longer is)."""
    try:
        v = float(text)
    except ValueError:
        if isinstance(old, (int, float)) and not isinstance(old, bool):
            raise ValueError(f"must be a number, not '{text}'")
        return text
    if isinstance(old, str):
        return text                                       # a text that happens to look like a number stays text
    return int(v) if v == int(v) else v


def shown(v):
    return str(int(v)) if isinstance(v, float) and v == int(v) else str(v)


class Scripts:
    """One per house. step(w, act) once a pass; act(line) sends ONE desk command as the house, whole (a ; in a script's
    text is words), and returns the desk's text."""

    def __init__(self, world, state_dir, allowed=None, check=problem, clock=None):
        self.world, self.dir = world, Path(state_dir)
        self.path = self.dir / "scripts.json"
        self.check, self.clock = check, clock or (lambda: time.strftime("%d %b %Y %H:%M"))
        self.allowed = allowed if allowed is not None else (
            world == "frontier" and bool(os.environ.get("HOUSE_KEEPER"))
            and os.environ.get("AGORA_SCRIPTS", "").lower() != "off")
        self.log = []                                   # what each pass did, newest last (for tests and the console)

    def load(self):
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def save(self, st):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(st, indent=1), encoding="utf-8")
        os.replace(tmp, self.path)

    @staticmethod
    def notes(w):
        """The script notes that appear somewhere: (subject id, an appearance id, subject)."""
        for s in w.subjects.values():
            p = s.get("props") or {}
            if str(p.get("role") or "") == "script" and str(p.get("file") or "").strip():
                at = w.appearances_of(s["id"])
                if at:
                    yield s["id"], at[0], s

    def step(self, w, act):
        if not self.allowed:
            return
        st = self.load()
        before = json.dumps(st, sort_keys=True)
        for sid, aid, s in list(self.notes(w)):
            try:
                self.one(sid, aid, s, st.setdefault(sid, {}), act)
            except Exception as e:                       # one script never stops the others, or the pass
                self.say(f"{sid}: {type(e).__name__}: {e}")
        if json.dumps(st, sort_keys=True) != before:
            self.save(st)

    def say(self, what):
        self.log.append(what)
        print(f"house: scripts: {what}", flush=True)

    def props(self, aid, s, act, **want):
        """Set the props that differ (a prop set to the value it has is refused). -> whether the desk took them."""
        have = s.get("props") or {}
        diff = {k: v for k, v in want.items() if str(have.get(k) if have.get(k) is not None else "") != v}
        if not diff:
            return True
        act(f"look {aid} :1")
        got = act(f"do prop {aid} " + " ".join(f"{k}={quote(v)}" for k, v in diff.items())) or ""
        return "ok prop" in got

    def rewrite(self, aid, s, text, agreed, act):
        """Rewrite the note from its file. -> whether the desk took it. Until the world we read shows the new words,
        the old ones are 'stale' (agreed['stale']): seen again on the next pass they are the world lagging behind the
        desk's answer, not an edit to carry back to the file."""
        old = sha(str(s.get("text") or ""))              # before acting: an in-memory world changes s in place
        act(f"read {aid} :3")                            # a rewrite is fenced on the text its writer has read
        got = act(f"do rewrite {aid} text={quote(text)}") or ""
        if "ok rewrite" not in got:
            self.say(f"{s.get('title')}: the note could not be rewritten: {got.strip()[-200:]}")
            return False
        agreed["stale"] = old
        return True

    def one(self, sid, aid, s, agreed, act):
        p = s.get("props") or {}
        path = Path(str(p["file"]).strip())
        if not path.is_file():
            self.props(aid, s, act, sync="Its file is missing, so nothing is kept in step.")
            return
        text, form = read_file(path)
        note = str(s.get("text") or "")
        name = s.get("title") or path.stem
        if agreed.get("file_path") != str(path):          # met for the first time (or moved): the file is the truth
            keep(path, time.strftime("%Y-%m-%d") + ".original")
            if str(p.get("first") or "") == "note" and note.strip() and note != text:
                # unless the note says its text is the next version (first=note): then they agree on the file as it
                # was, and the note's text is carried out below like any edit made here
                agreed.clear()
                agreed.update(file_path=str(path), file=sha(text), text=sha(text))
                self.say(f"{name}: met; its note holds the next version")
                self.text(path, aid, s, name, text, note, form, agreed, act)
                self.settings(path, aid, s, name, agreed, act)
                return
            if note != text and not self.rewrite(aid, s, text, agreed, act):
                return
            stale = agreed.get("stale")
            agreed.clear()
            agreed.update(file_path=str(path), file=sha(text), text=sha(text), **({"stale": stale} if stale else {}))
            self.props(aid, s, act, edited=f"{self.clock()}, on the PC", sync="In step with its file.")
            self.say(f"{name}: carried in from its file")
        else:
            self.text(path, aid, s, name, text, note, form, agreed, act)
        self.settings(path, aid, s, name, agreed, act)

    def text(self, path, aid, s, name, text, note, form, agreed, act):
        if sha(note) == agreed.get("text"):
            agreed.pop("stale", None)
        elif sha(note) == agreed.get("stale"):
            return                                        # the world has not caught up with our rewrite yet
        moved_file, moved_note = sha(text) != agreed.get("file"), sha(note) != agreed.get("text")
        if not moved_file and not moved_note:
            return
        if text == note:                                  # both moved to the same words
            agreed.update(file=sha(text), text=sha(text))
            self.props(aid, s, act, sync="In step with its file.")
        elif moved_file and moved_note:
            self.props(aid, s, act, sync="Both the note and its file changed since they last agreed, so neither was "
                                         "written. Put one back (undo the note's edit, or restore the file) to go on.")
        elif moved_file:
            if not self.rewrite(aid, s, text, agreed, act):
                return
            agreed.update(file=sha(text), text=sha(text))
            self.props(aid, s, act, edited=f"{self.clock()}, on the PC", sync="In step with its file.")
            self.say(f"{name}: the file changed; note rewritten")
        else:
            bad = self.check(path, note)
            if bad:
                self.props(aid, s, act, sync=f"Not written to its file: the text has a mistake ({bad}). The file still "
                                             f"holds the last good version.")
                return
            try:
                kept = replace(path, note, form)
            except OSError as e:
                self.props(aid, s, act, sync=f"Not written yet: the file could not be replaced ({type(e).__name__}); "
                                             f"the house tries again.")
                return
            agreed.update(file=sha(note), text=sha(note))
            self.props(aid, s, act, edited=f"{self.clock()}, here", sync="In step with its file.")
            self.say(f"{name}: the note changed; file written (the old one kept as {kept.name})")

    def settings(self, path, aid, s, name, agreed, act):
        names = setting_names(s.get("props") or {})
        where = str((s.get("props") or {}).get("settings_file") or "").strip()
        if not names or not where:
            return
        where = Path(where) if Path(where).is_absolute() else path.parent / where
        p = s.get("props") or {}
        disk = read_settings(where)
        mine = {n: (str(p.get(n)) if p.get(n) is not None else "") for n in names}
        theirs = {n: shown(disk[n]) if n in disk else "" for n in names}
        key = lambda d: sha(json.dumps(d, sort_keys=True))
        key_m, key_t = key(mine), key(theirs)
        if key_m == agreed.get("settings_note"):
            agreed.pop("stale_settings", None)
        elif key_m == agreed.get("stale_settings"):
            return                                        # the world has not caught up with our props yet
        if "settings_note" not in agreed:                 # first meeting: the file is the truth where it says
            fill = {n: v for n, v in theirs.items() if v != "" and v != mine[n]}
            if fill:
                if not self.props(aid, s, act, **fill):
                    return
                agreed["stale_settings"] = key_m
                mine.update(fill)
                key_m = key(mine)
            if any(theirs[n] == "" and mine[n] != "" for n in names):
                self.write_settings(where, disk, mine, names)
                key_t = key_m
            agreed.update(settings_note=key_m, settings_file=key_t)
            return
        moved_t, moved_m = key_t != agreed["settings_file"], key_m != agreed["settings_note"]
        if not moved_t and not moved_m or mine == theirs:
            agreed.update(settings_note=key_m, settings_file=key_t)
            return
        if moved_t and moved_m:
            self.props(aid, s, act, sync="Both a setting here and its settings file changed since they last agreed, "
                                         "so neither was written.")
        elif moved_t:
            if not self.props(aid, s, act, **{n: v for n, v in theirs.items() if v != mine[n]}):
                return
            agreed.update(settings_note=key_t, settings_file=key_t, stale_settings=key_m)
            self.say(f"{name}: settings changed on the PC; props updated")
        else:
            try:
                self.write_settings(where, disk, mine, names)
            except (ValueError, OSError) as e:
                self.props(aid, s, act, sync=f"A setting was not written: {e}. Its file keeps the last good value.")
                return
            agreed.update(settings_note=key_m, settings_file=key_m)
            self.props(aid, s, act, edited=f"{self.clock()}, a setting here", sync="In step with its file.")
            self.say(f"{name}: settings changed here; settings file written")

    @staticmethod
    def write_settings(where, disk, mine, names):
        out = dict(disk)
        for n in names:
            if mine[n] == "":
                continue
            out[n] = as_value(mine[n], disk.get(n))
        body = json.dumps(out, indent=2) + "\n"
        if Path(where).exists():
            replace(where, body, {"bom": False, "crlf": False})
        else:
            write_file(where, body, {"bom": False, "crlf": False})
