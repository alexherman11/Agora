"""Side probe: can a member's lens freeze a steward's kind, and does the refusal name a lens the steward can't see?
Runs on a scratch world made by trial.py (argv[1]); changes only that copy."""
import sys
from pathlib import Path

sys.path.insert(0, "C:/Projects/Agora4/research/kernel-lab")
from kernel.kernel import Kernel, Actor  # noqa: E402

k = Kernel(Path(sys.argv[1]))
A, S = Actor("dk2", "dk2", "person"), Actor("dk1148", "dk1148", "person")


def say(actor, line):
    out = k.run(actor, line)
    print(f"[{'ok' if out['ok'] else 'NO'}] {actor.person}: {line}\n   -> {out['text'][:300]}")
    return out


kd = say(A, 'make kind=kind name=chore needs="title"')["made"][0]
say(S, 'make kind=lens name=sables-private-chores sees=me painter=components text="root : column, of tag:chore as c"')
say(A, "rows lens name=sables-private-chores")
say(A, f'set {kd} needs="title lane"')
