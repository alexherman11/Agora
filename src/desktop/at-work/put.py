"""put: the improved At work (a6265) into a world. worker-a6265, 17 Oct.

    python src/desktop/at-work/put.py check [--world live|try]   what it would change; sends nothing
    python src/desktop/at-work/put.py try                        into frontier-try (a copy), through explore.py
    python src/desktop/at-work/put.py door                       live: check, keep what it replaces, then send
    python src/desktop/at-work/put.py lines <out>                the lines it would send to frontier-try

What it does, after LAMPLIT (a6057, src/desktop/directions/living/apply.py) is in the world, and never before
the round-3 assembly (worker-a5994) has landed (JEFF's commission a6265):
  1. home-style gains this lane's roles, at-work.style-roles, by LAMPLIT's rule for a role added later: one desk line
     each, appended (a role already there with other words has that line replaced). Its colours are the rule's tokens.
  2. the lenses house-at-work-row, house-at-work, house-at-work-small are written (made, or rewritten), style=home-style.
  3. Alex's At work panel (role=home-panel actor=alex, showing home-house or home-work) shows house-at-work with
     house-at-work-small beside its title, and is called At work. Its glance-work tag stays, so the glance and the bar
     timer still find it (the You row and its timer are in house-at-work, as in home-house).
door first saves home-style's text and the panel's props and title in src/desktop/at-work/kept/<when>/, with
undo.desk: the desk lines that put them back (run them with explore.py or the door).
"""
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
LAB = HERE.parents[1] / "text-desk" / "notation"
ROOM = "f5204"
ME = "worker-a6265"
LENSES = ["house-at-work-row", "house-at-work", "house-at-work-small"]
PANEL = "prop:role=home-panel,prop:actor=alex"
DOOR = "http://127.0.0.1:8794/api/do"
NL = "\n"     # between a read and its act: one explore run holds both; the door gets them one request each


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def roles():
    """-> [(name, line)] of this lane's role lines."""
    out = []
    for l in (HERE / "at-work.style-roles").read_text(encoding="utf-8").splitlines():
        m = re.match(r"role (\S+) :", l)
        if m:
            out.append((m.group(1), l.rstrip()))
    return out


def style_text(base=None):
    """home-style's text with this lane's roles laid in, as `plan` would leave it (for tests and copies)."""
    base = base if base is not None else (HERE.parent / "directions" / "living" / "direction-living.style").read_text(encoding="utf-8")
    lines = base.rstrip("\n").splitlines()
    have = {re.match(r"role (\S+) :", l).group(1): i for i, l in enumerate(lines) if re.match(r"role (\S+) :", l)}
    for name, line in roles():
        if name in have:
            lines[have[name]] = line
        else:
            lines.append(line)
    return "\n".join(lines)


class World:
    def __init__(self, where):
        self.where = where

    def do(self, line):
        if self.where == "live" and NL in line:          # the door reads one command a request; looks carry
            return "".join(self.do(part) for part in line.split(NL))
        if self.where == "live":
            req = urllib.request.Request(DOOR, data=json.dumps({"session": "frontier", "as": ME, "line": line,
                                                                "whole": True}).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode()).get("text", "")
        r = subprocess.run([sys.executable, str(LAB / "explore.py"), "frontier-try", "--as", ME, "--whole"],
                           input=line + "\n", capture_output=True, text=True, encoding="utf-8", cwd=LAB)
        return r.stdout + r.stderr


def body(text):
    return text.split("\n---\n", 1)[1].rsplit("\n---", 1)[0] if "\n---\n" in text else ""


def plan(w):
    """-> (lines to send, report, kept: {name: text}) after reading the world. Reads only."""
    lines, report, kept = [], [], {}
    room = w.do(f"look {ROOM} :2")
    notes = {m.group(2): m.group(1) for m in re.finditer(r'^\s+(a\d+) note "([^"]+)"', room, re.M)}
    sid = notes.get("home-style")
    if not sid:
        return [], ["ERR no home-style in the Home base room"], kept
    style = body(w.do(f"read {sid} :3"))
    kept["home-style"] = style
    have = {}
    for l in style.splitlines():
        m = re.match(r"role (\S+) :", l)
        if m:
            have[m.group(1)] = l.rstrip()
    added = changed = 0
    for name, line in roles():
        if have.get(name) == line:
            continue
        if name in have:
            lines.append(f"read {sid} :3{NL}do replace {sid} old={q(have[name])} new={q(line)}")
            changed += 1
        else:
            lines.append(f"read {sid} :3{NL}do append {sid} line={q(line)}")
            added += 1
    report.append(f"home-style ({sid}): {added} role lines appended, {changed} replaced, "
                  f"{len(roles()) - added - changed} already as written")
    for name in LENSES:
        text = (HERE / f"{name}.lens").read_text(encoding="utf-8").rstrip("\n")
        if name in notes:
            was = body(w.do(f"read {notes[name]} :3"))
            kept[name] = was
            if was.strip() != text.strip():
                lines.append(f"read {notes[name]} :3{NL}do rewrite {notes[name]} text={q(text)}")
                report.append(f"lens {name} ({notes[name]}): rewritten")
            else:
                report.append(f"lens {name}: already as written")
        else:
            lines.append(f"do create {ROOM} kind=note title={q(name)} tags=lens style=home-style text={q(text)}")
            report.append(f"lens {name}: made")
    found = w.do(f"find {PANEL}")
    panel = None
    for m in re.finditer(r'^\s+(a\d+) note "([^"]+)" · ([^\n]*)', found, re.M):
        if re.search(r"\blens=(home-house|home-work|house-at-work)\b", m.group(3)):
            panel = (m.group(1), m.group(2), m.group(3))
    if panel is None:
        report.append("panel: Alex has no At work / The house panel (lens=home-house or home-work): nothing placed")
    else:
        pid, title, props = panel
        kept["panel"] = f"{pid} \"{title}\" · {props}"
        if "lens=house-at-work " not in props + " " or "lesser=house-at-work-small" not in props:
            lines.append(f"read {pid}{NL}do prop {pid} lens=house-at-work lesser=house-at-work-small")
        if title != "At work":
            lines.append(f'read {pid}{NL}do retitle {pid} title="At work"')
        report.append(f"panel {pid} '{title}' ({props}): -> lens house-at-work, lesser house-at-work-small, called At work")
    return lines, report, kept


def undo_lines(kept, sid_style, panel):
    out = []
    if "home-style" in kept:
        out += [f"read {sid_style} :3", f"do rewrite {sid_style} text={q(kept['home-style'])}"]
    if panel:
        m = re.match(r'(a\d+) "([^"]*)" · (.*)', panel)
        if m:
            pid, title, props = m.groups()
            lens = re.search(r"\blens=(\S+)", props)
            lesser = re.search(r"\blesser=(\S*)", props)
            out += [f"read {pid}", f"do prop {pid} lens={lens.group(1) if lens else 'home-work'} "
                                   f"lesser={lesser.group(1) if lesser else ''}",
                    f"read {pid}", f"do retitle {pid} title={q(title)}"]
    return out


def main(a):
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    where = "live" if cmd == "door" or (cmd == "check" and "--world" in a and a[a.index("--world") + 1] == "live") else "try"
    w = World(where)
    lines, report, kept = plan(w)
    print(f"{where}: " + "\n".join(report))
    if cmd == "check":
        print(f"{len(lines)} lines would be sent")
        return 0
    if cmd == "lines":
        pathlib.Path(a[1]).write_text("\n".join(lines) + "\n", encoding="utf-8")
        return 0
    if any(r.startswith("ERR") for r in report):
        return 1
    if cmd == "door":
        d = HERE / "kept" / time.strftime("%Y%m%d-%H%M%S")
        d.mkdir(parents=True)
        for name, text in kept.items():
            (d / f"{name}.txt").write_text(text, encoding="utf-8")
        room = w.do(f"look {ROOM} :2")
        sid = re.search(r'^\s+(a\d+) note "home-style"', room, re.M)
        (d / "undo.desk").write_text("\n".join(undo_lines(kept, sid.group(1) if sid else "", kept.get("panel"))) + "\n",
                                     encoding="utf-8")
        print(f"kept in {d}")
    bad = 0
    for line in lines:
        out = w.do(line)
        if re.search(r"^(ERR|.*does not compile|.*refused)", out, re.M):
            bad += 1
            print(f"!! {line[:120]}\n   {out.strip()[:400]}")
    print(f"sent {len(lines)} lines, {bad} refused")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
