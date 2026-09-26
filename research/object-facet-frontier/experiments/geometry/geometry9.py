"""sable-9 as a standalone model: geometry held as choices only, layout as a pure function. Not wired into the desk.

    model = convert(world)        from today's stored boxes: place {parent, order key}, share, geom:pos/size, folded
    boxes = layout(model)         every appearance's and surface's box, derived; stored only for free children
    rows  = act(model, ...)       a verb on the model, returning the (referent, aspect) rows it writes

    python geometry9.py           checks (1) layout(convert(w)) against today's boxes on the suite worlds and a walk,
                                  (2) rows per act, model against today, (3) S12's two writers in one column

The arithmetic of layout() is world.reflow()'s, so the only differences are what reflow's history left behind.
"""

import copy
import importlib.util
import random
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2] / "text-desk-lab" / "notation"
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(HERE))
import explore  # noqa: E402

D = "0123456789abcdefghijklmnopqrstuvwxyz"
GAP = 8


def between(a, b):
    """A key that sorts strictly between a and b (None = open end). Fractional indexing over base 36."""
    a, out, i, tight = a or "", "", 0, b is not None
    while True:
        ca = D.index(a[i]) if i < len(a) else 0
        cb = D.index(b[i]) if tight and i < len(b) else len(D)
        if cb - ca > 1:
            return out + D[(ca + cb) // 2]
        out += D[ca]
        if tight and (i >= len(b) or D[ca] != b[i]):
            tight = False
        i += 1


# ---- the model ------------------------------------------------------------------------------------------------------------
def convert(w):
    """Today's world -> choices. Order from today's children() order; share from each child's size along the flow."""
    m = {"root": w.root, "equal": w.equal_share, "nodes": {}}
    for nid, n in w.nodes.items():
        m["nodes"][nid] = {"type": n["type"], "parent": n["parent"], "layout": n.get("layout"),
                           "folded": n.get("folded", False), "order": None, "share": None, "pos": None, "size": None}
    m["nodes"][w.root]["size"] = (w.nodes[w.root]["w"], w.nodes[w.root]["h"])
    m["nodes"][w.root]["pos"] = (w.nodes[w.root]["x"], w.nodes[w.root]["y"])
    for fid, f in w.nodes.items():
        if f["type"] != "surface":
            continue
        key = None
        for k in w.children(fid):
            key = between(key, None)
            mk = m["nodes"][k["id"]]
            mk["order"] = key
            if f["layout"] == "free":
                mk["pos"], mk["size"] = (k["x"], k["y"]), (k["w"], k["h"])
            else:
                mk["share"] = max(1, k["h"] if f["layout"] == "column" else k["w"])
    return m


def kids(m, fid):
    return sorted((n for n, x in m["nodes"].items() if x["parent"] == fid), key=lambda n: (m["nodes"][n]["order"], n))


def layout(m):
    """-> {nid: (x, y, w, h)} for every node, derived for flow children, held for free ones. reflow()'s arithmetic."""
    boxes = {m["root"]: (*m["nodes"][m["root"]]["pos"], *m["nodes"][m["root"]]["size"])}

    def lay(fid):
        f, (fx, fy, fw, fh) = m["nodes"][fid], boxes[fid]
        ks = kids(m, fid)
        if f["layout"] == "free":
            for k in ks:
                boxes[k] = (*m["nodes"][k]["pos"], *m["nodes"][k]["size"])
        elif ks:
            n = len(ks)
            total = (fh if f["layout"] == "column" else fw) - GAP * (n + 1)
            weights = [1] * n if m["equal"] else [max(1, m["nodes"][k]["share"] or 1) for k in ks]
            wsum = float(sum(weights))
            shares = [max(24, int(total * wt / wsum)) for wt in weights]
            if sum(shares) > total:
                shares = [max(24, total // n)] * n
            at = GAP
            for k, sh in zip(ks, shares):
                boxes[k] = (GAP, at, fw - 2 * GAP, sh) if f["layout"] == "column" else (at, GAP, sh, fh - 2 * GAP)
                at += sh + GAP
        for k in ks:
            if m["nodes"][k]["type"] == "surface":
                lay(k)
    lay(m["root"])
    return boxes


# ---- acts on the model: each returns the rows it writes ----------------------------------------------------------------
def _place_at(m, nid, parent, before=None, after=None):
    ks = [k for k in kids(m, parent) if k != nid]
    if before is not None:
        i = ks.index(before)
        lo, hi = (m["nodes"][ks[i - 1]]["order"] if i else None), m["nodes"][before]["order"]
    elif after is not None:
        i = ks.index(after)
        lo, hi = m["nodes"][after]["order"], (m["nodes"][ks[i + 1]]["order"] if i + 1 < len(ks) else None)
    else:
        lo, hi = (m["nodes"][ks[-1]]["order"] if ks else None), None
    x = m["nodes"][nid]
    x["parent"], x["order"] = parent, between(lo, hi)
    return [(nid, "place")]


def create(m, nid, parent, kind="appearance"):
    """A new thing at the end of its parent. In a flow its share is the mean of its siblings' (world._fair_share)."""
    m["nodes"][nid] = {"type": kind, "parent": None, "layout": None, "folded": False, "order": None,
                       "share": None, "pos": None, "size": None}
    rows = _place_at(m, nid, parent)
    p = m["nodes"][parent]
    if p["layout"] == "free":
        m["nodes"][nid]["pos"], m["nodes"][nid]["size"] = (16, 16), (300, 160)
        rows += [(nid, "geom:pos"), (nid, "geom:size")]
    else:
        sib = [m["nodes"][k]["share"] for k in kids(m, parent) if k != nid and m["nodes"][k]["share"]]
        m["nodes"][nid]["share"] = int(sum(sib) / len(sib)) if sib else 160
        rows.append((nid, "share"))
    return rows


def move(m, nid, into=None, before=None, after=None):
    parent = into or m["nodes"][before or after]["parent"]
    rows = _place_at(m, nid, parent, before, after)
    if m["nodes"][parent]["layout"] != "free" and not m["nodes"][nid]["share"]:
        m["nodes"][nid]["share"] = 160
        rows.append((nid, "share"))
    return rows


def remove(m, nid):
    m["nodes"][nid]["parent"] = None
    return [(nid, "place")]


def resize(m, nid, w, h):
    p = m["nodes"][m["nodes"][nid]["parent"]]
    if p["layout"] == "free":
        m["nodes"][nid]["size"] = (w, h)
        return [(nid, "geom:size")]
    m["nodes"][nid]["share"] = h if p["layout"] == "column" else w
    return [(nid, "share")]


# ---- checks -----------------------------------------------------------------------------------------------------------------
def compare(w):
    """layout(convert(w)) against today's stored boxes. -> (nodes compared, differing, worst px)."""
    boxes = layout(convert(w))
    diff, worst = 0, 0
    for nid, n in w.nodes.items():
        if nid not in boxes:
            continue
        d = max(abs(a - b) for a, b in zip(boxes[nid], (n["x"], n["y"], n["w"], n["h"])))
        if d:
            diff += 1
            worst = max(worst, d)
    return len(boxes), diff, worst


def main():
    import layout9
    print("(1) layout(convert(world)) against today's stored boxes")
    for label, w in layout9.suite_worlds():
        total, diff, worst = compare(w)
        print(f"- {label}: {diff} of {total} boxes differ, worst {worst}px")
    w, rows = layout9.home_walk()
    total, diff, worst = compare(w)
    print(f"- home walk (60 acts): {diff} of {total} boxes differ, worst {worst}px")

    print("(2) S12 on the model: Alex adds at the bottom of a column while the agent adds one and moves it to the top")
    d = explore.fresh()
    run = lambda line: d.dispatch("desk", {"line": line}).get("text") or ""   # noqa: E731
    run("look")
    run("do create f01 kind=surface title=Tasks layout=column")
    col = next(n for n, x in d.world.nodes.items() if x.get("title") == "Tasks")
    for i in range(5):
        run(f"do create {col} kind=task title=T{i}")
    base = convert(d.world)
    tasks = kids(base, col)
    a, b = copy.deepcopy(base), copy.deepcopy(base)
    rows_a = create(a, "g-alex", col)
    rows_b = create(b, "g-agent", col) + move(b, "g-agent", before=tasks[0])
    both = set(rows_a) & set(rows_b)
    print(f"- Alex writes {rows_a}; the agent writes {rows_b}; rows written by both: {sorted(both) or 'none'}")
    merged = copy.deepcopy(base)
    for k in ("g-alex",):
        merged["nodes"][k] = a["nodes"][k]
    merged["nodes"]["g-agent"] = b["nodes"]["g-agent"]
    order = [n for n in kids(merged, col)]
    print(f"- merged by assigning both rows: column order {order}")
    boxes, before_boxes = layout(merged), layout(base)
    moved = [t for t in tasks if boxes[t] != before_boxes[t]]
    print(f"- the five untouched tasks' boxes are derived: {len(moved)} of 5 move on screen, and none of them was written")

    print("(3) rows per act, model against today (today's numbers from experiments/journal/working_copy.txt)")
    m = convert(d.world)
    t = kids(m, col)
    print(f"- move into another column: {move(m, t[1], into=d.world.root)}")
    print(f"- move before a sibling: {move(m, t[3], before=t[0])}")
    print(f"- resize in a column: {resize(m, t[2], 300, 200)}")
    print(f"- remove: {remove(m, t[4])}")

    print("(4) between(): 2000 random insertions keep a strict order")
    rnd, keys = random.Random(3), []
    for _ in range(2000):
        i = rnd.randint(0, len(keys))
        k = between(keys[i - 1] if i else None, keys[i] if i < len(keys) else None)
        keys.insert(i, k)
    ok = all(keys[j] < keys[j + 1] for j in range(len(keys) - 1))
    print(f"- strictly ordered: {ok}; longest key {max(map(len, keys))} chars")


if __name__ == "__main__":
    main()
