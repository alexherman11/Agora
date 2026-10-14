"""Snappy Desk stage 2: a scene built with instances kept from the last build is the scene built whole.

    python test_lens_reuse.py [--quick]

Every lens of every frozen world (suite/golden/worlds) is built once, then the world is changed the ways people change
it, one at a time, and after each change the lens is built twice: keeping what it can from its last build
(lens_ir._REUSE), and whole. The two must be the same, field for field, fences and binds included (lens_ir._first_diff;
the reads list R aside). The changes are made to things the lens shows: words rewritten, a prop set (a block, a
status, an indent), a paragraph split, a thing added beside one, one removed, one moved, a talk line appended. Also
said: how much was kept, so a cache that never keeps anything does not pass as one that is right.

The frozen worlds are copies in memory; nothing is saved.
"""
import io
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "suite"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import lens_ir           # noqa: E402
import scene as S        # noqa: E402
import sessions as frozen   # noqa: E402

QUICK = "--quick" in sys.argv
fails, kept, made, changes, builds = [], 0, 0, 0, 0


def build(desk, title, whole):
    lens_ir._OFF[0] = whole
    try:
        sc, _ = lens_ir.scene_for(desk, title)
    finally:
        lens_ir._OFF[0] = False
    return sc


def items_of(sc):
    out, stack = [], [sc]
    while stack:
        n = stack.pop()
        if n.get("item"):
            out.append(n["item"])
        stack += n.get("kids") or []
    return sorted(set(out))


def esc(t):
    return t.replace("\\", "\\\\").replace('"', '\\"')


def changes_for(desk, rnd, items):
    """Lines a person might send, about things this lens shows."""
    w = desk.world
    out = []
    for i in rnd.sample(items, min(len(items), 4)):
        n = w.nodes.get(i)
        if not n:
            continue
        sid = n.get("subject")
        s = w.subjects.get(sid) if sid else None
        kind = (s or {}).get("kind") or n.get("type")
        if s is not None and kind in ("note", "task", "doc", "chat") and kind != "chat":
            out.append(f'do rewrite {i} text="{esc((s.get("text") or "")[:40])} changed {rnd.randint(1, 999)}"')
            out.append(f"do prop {i} block={rnd.choice(['bullet', 'number', 'h2', 'check'])}")
            out.append(f"do prop {i} status={rnd.choice(['open', 'done', 'doing'])} indent={rnd.randint(0, 3)}")
            if (s.get("text") or "").strip():
                t = s["text"]
                k = max(1, len(t) // 2)
                out.append(f'do split {i} p "{esc(t[:k])}" "{esc(t[k:])}"')
        if s is not None and kind == "chat":
            out.append(f'do append {i} line="a new line {rnd.randint(1, 999)}" about={rnd.choice(items)}')
        if n.get("parent") in w.nodes and n["parent"] != w.root:
            out.append(f'do create {n["parent"]} kind=note title="added {rnd.randint(1, 999)}" text="new words"')
            out.append(f"do up {i}")
        out.append(f"do remove {i}")
    rnd.shuffle(out)
    return out[:3 if QUICK else 6]


t0 = time.time()
for path in frozen.worlds():
    world = frozen.load_world(path)
    desk = frozen.desk_for(world, path.stem)
    titles = frozen.lens_titles(world)
    rnd = random.Random(path.stem)
    for title in (titles[:6] if QUICK else titles):
        try:
            first = build(desk, title, False)
        except S.LensRefusal:
            continue
        except Exception as e:      # noqa: BLE001  (a lens of the corpus that crashes is the golden prints' business)
            continue
        for line in changes_for(desk, rnd, items_of(first)):
            target = line.split()[2]
            desk.dispatch("desk", {"line": f"look {target} :1"})        # a person looks before they change a thing
            desk.dispatch("desk", {"line": f"read {target}"})
            r = desk.dispatch("desk", {"line": line})
            if r.get("error"):
                continue
            changes += 1
            k0, m0 = lens_ir._STATS["kept"], lens_ir._STATS["made"]
            outcome = []
            for whole in (False, True):          # both ways: a scene, or the same refusal
                try:
                    outcome.append(build(desk, title, whole))
                except Exception as e:      # noqa: BLE001
                    outcome.append(f"{type(e).__name__}: {e}")
            a, b = outcome
            if isinstance(a, str) or isinstance(b, str):
                if a != b:
                    fails.append(f"{path.stem} / {title} after {line!r}: kept gave {str(a)[:100]!r}, whole gave {str(b)[:100]!r}")
                continue
            kept += lens_ir._STATS["kept"] - k0
            made += lens_ir._STATS["made"] - m0
            builds += 2
            S.emit(a)
            S.emit(b)
            d = lens_ir._first_diff(a, b)
            if d:
                fails.append(f"{path.stem} / {title} after {line!r}: {d}")

print(f"{changes} changes over the frozen worlds' lenses, each lens built kept and whole after each ({time.time() - t0:.0f} s)")
print(f"instances kept {kept}, made {made} ({100 * kept / max(1, kept + made):.0f}% kept)")
for f in fails[:15]:
    print("FAIL", f)
check_kept = kept > 0
if not check_kept:
    print("FAIL nothing was ever kept: the cache does nothing")
print(f"{len(fails) + (0 if check_kept else 1)} failed" if fails or not check_kept else "all passed")
sys.exit(1 if fails or not check_kept else 0)
