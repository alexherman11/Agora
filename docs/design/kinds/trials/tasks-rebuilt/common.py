"""Shared helpers for the tasks-rebuilt trial. Opens a private copy of the desktop log; never the live world."""
import json
import shutil
import sys
import time
from pathlib import Path

KL = Path("C:/Projects/Agora4/src/agora")
sys.path.insert(0, str(KL))
from kernel.kernel import Kernel, Refused, Actor  # noqa: E402

SCRATCH = Path("C:/Users/Alex/AppData/Local/Temp/claude/C--Projects-Agora4/e6d17725-6072-416c-9336-f572113f9a0e/scratchpad/trial-tasks")
BASE_LOG = SCRATCH / "base" / "log" / "0001.jsonl"


def fresh_copy(name):
    """A new world directory holding only a copy of the base log."""
    d = SCRATCH / name
    if d.exists():
        shutil.rmtree(d)
    (d / "log").mkdir(parents=True)
    shutil.copy(BASE_LOG, d / "log" / "0001.jsonl")
    return d


def open_world(name):
    d = fresh_copy(name)
    t = time.perf_counter()
    k = Kernel(d)
    return k, time.perf_counter() - t


def steward(k):
    p = next(t for t in k.things("person") if k.is_steward(t))
    return Actor(p, p, "person")


def say(k, actor, line, mode="do"):
    out = k.run(actor, line, mode=mode)
    return out


def short(out, n=300):
    txt = str(out.get("text", ""))
    return ("ok " if out.get("ok") else "REFUSED ") + txt[:n].replace("\n", " | ")


def timed(fn, *a, reps=1, **kw):
    best, out = None, None
    for _ in range(reps):
        t = time.perf_counter()
        out = fn(*a, **kw)
        dt = time.perf_counter() - t
        best = dt if best is None else min(best, dt)
    return out, best
