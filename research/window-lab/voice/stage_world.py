"""stage_world.py (a8901): the desk lines that put Voice with JEFF into a world: the lens note home-voice (from
home-voice.lens beside this file), placed in jeff-chat's dock, and the home base's switch. For a COPY only, in tests and
the sandbox demo; in the live world these are JEFF's activation, after Alex's word.

    python research/window-lab/voice/stage_world.py <out.desk> [--switch on|off]
then
    python research/text-desk-lab/notation/explore.py <copy>-try --as jeff < <out.desk>

Alex's consent is not staged: his own first press asks him.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME_BASE_SURFACE, JEFF_CHAT, HOME_BASE = "f5204", "a5210", "a5208"
OLD = "    footer : row\n      role urfooter\n      only when held = \"\""
NEW = "    voicebar : column\n      only when held = \"\"\n      lens home-voice\n" + OLD


def lines(switch="on"):
    lens = (HERE / "home-voice.lens").read_text(encoding="utf-8").rstrip("\n")
    q = lambda v: json.dumps(v, ensure_ascii=False)    # the desk reads \n in a value, never \u
    return [f"look {HOME_BASE_SURFACE} :1",
            f"do create {HOME_BASE_SURFACE} kind=note title=home-voice tags=lens style=home-style text={q(lens)}",
            f"read {JEFF_CHAT}",
            f"do replace {JEFF_CHAT} old={q(OLD)} new={q(NEW)}",
            f"look {HOME_BASE} :1",
            f"do prop {HOME_BASE} voice={switch}"]


if __name__ == "__main__":
    out = Path(sys.argv[1])
    switch = sys.argv[sys.argv.index("--switch") + 1] if "--switch" in sys.argv else "on"
    out.write_text("\n".join(lines(switch)) + "\n", encoding="utf-8")
    print(out)
