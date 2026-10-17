"""Scripts (a6249) as desk lines: the world half, kept as files so it can be tried on a copy and then applied live.

    python research/window-lab/scripts/apply.py surface <out.desk>          the surface (explore.py <world> --as <me> < out.desk)
    python research/window-lab/scripts/apply.py lines <out.desk> <f-id>     the rest, into that surface
    python research/window-lab/scripts/apply.py update <out.desk>           only the two lenses, rewritten from their files
    python research/window-lab/scripts/apply.py door [--as <name>]          both, to the live door, line by line, stopping
                                                                            at a refusal

What the lines make, all world data anyone may change afterwards:
  - a surface "Scripts" in Home, with a note saying what it is;
  - the note "Rocket League timer" (role=script): file= where it lives on Alex's PC, does=/runs=/why_not= in plain
    sentences, panel=rocket-settings, settings= its two numbers (weekday_minutes, weekend_minutes, carried to
    settings_file=), and first=note with the weekend version as its text: the house (scripts_mirror.py, once landed)
    backs the original up beside the file, checks the new text parses, and writes it;
  - two lenses in the Home base room (scripts-page, rocket-settings) and their roles appended to home-style.
Applying twice makes everything twice: it is for a world that has none of it yet."""
import json
import pathlib
import re
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
HOME, LENSES = "f149", "f5204"
FILE = r"C:\Users\Alex\RocketLeagueTimer\RocketLeagueTimer.ps1"
ABOUT = ("Alex's own scripts, each a note the house keeps in step with its file on his PC (a6249, 17 Oct). Edit a "
         "script's words or settings here and the house checks them and writes the file within seconds, keeping the old "
         "one in agora-history beside it; change the file on the PC and the note follows. If both change at once neither "
         "is written and the note says so. The house never runs a script from here. To bring another one in: a note "
         "here with role=script, file=<its path>, does=<one plain sentence>, runs=<how it is started>; the house fills "
         "in its words. Open the lens scripts-page to see them as Alex does.")
DOES = ("Lets Rocket League run for a set time each day, warns you 7 minutes before the end with a small note over "
        "the game that never takes it away from you, lets a match you are in finish, then closes the game until "
        "tomorrow.")
RUNS = ("Windows starts it quietly in the background and one copy watches all day. A new version starts working the "
        "next time you sign in; after that a changed setting counts within seconds.")
WHY_NOT = "Never run from here: it closes a game."
LENS_FILES = {"scripts-page": "scripts.lens", "rocket-settings": "rocket-settings.lens"}


def q(s):
    """A value as the desk reads it: in double quotes, with backslash, quote and dollar escaped and newlines as \\n."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def text(name):
    return (HERE / name).read_text(encoding="utf-8").replace("\r\n", "\n").rstrip("\n")


def surface():
    return [f"look {HOME}", f"do create {HOME} kind=surface title=Scripts layout=column"]


def lines(s):
    """Everything after the surface, which is `s` (an id: the world already has a note called scripts, a1771, so the
    title alone names two things)."""
    # one command a line: the door reads each request whole, so a `;` there does not split it (a5659, 15 Oct)
    script = (HERE / "RocketLeagueTimer.ps1").read_text(encoding="utf-8").replace("\r\n", "\n")
    return [f"look {s} :1",
            f"do create {s} kind=note title=\"About Scripts\" text={q(ABOUT)}",
            f"do create {s} kind=note title=\"Rocket League timer\" role=script file={q(FILE)} first=note "
            f"does={q(DOES)} runs={q(RUNS)} why_not={q(WHY_NOT)} run_here=never panel=rocket-settings "
            f"settings=\"weekday_minutes weekend_minutes\" settings_file=RocketLeagueTimer.settings.json "
            f"weekday_minutes=30 weekend_minutes=60 text={q(script)}",
            'read "home-style"',
            f'do append "home-style" line={q(text("scripts.style"))}',
            f"look {LENSES}",
            f"do create {LENSES} kind=note title=scripts-page tags=lens style=home-style text={q(text('scripts.lens'))}",
            f"do create {LENSES} kind=note title=rocket-settings tags=lens style=home-style "
            f"text={q(text('rocket-settings.lens'))}"]


def door(line, who):
    body = json.dumps({"session": "frontier", "as": who, "line": line, "whole": True}).encode()
    r = urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8794/api/do", data=body, method="POST"), timeout=60)
    return json.loads(r.read()).get("text", "")


def main(argv):
    who = argv[argv.index("--as") + 1] if "--as" in argv else "worker-a6249"
    if argv[:1] == ["surface"] and len(argv) > 1:
        out = surface()
    elif argv[:1] == ["lines"] and len(argv) > 2:
        out = lines(argv[2])
    elif argv[:1] == ["update"] and len(argv) > 1:          # the two lenses again, from their files
        out = [x for name in ("scripts-page", "rocket-settings")
               for x in (f'read "{name}"', f'do rewrite "{name}" text={q(text(LENS_FILES[name]))}')]
    elif argv[:1] == ["door"]:
        made = ""
        for line in surface():
            said = door(line, who)
            print(said[:400])
            made = (re.search(r"created (f\d+)", said) or [None, made])[1]
        if not made:
            print("stopped: no surface was made")
            return 1
        for line in lines(made):
            said = door(line, who)
            print(said[:400])
            if said.startswith("ERR") or "refused" in said[:200]:
                print("stopped: the line above was refused")
                return 1
        return 0
    else:
        print(__doc__)
        return 0
    pathlib.Path(argv[1]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {len(out)} lines to {argv[1]}")
    return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
