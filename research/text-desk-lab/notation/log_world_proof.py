"""Copy-only audit/latency receipt. Prints counts, never raw log contents.

python log_world_proof.py --fixture <house-export directory> --out <receipt.json>
python log_world_proof.py --benchmark-copy frontier-try --out <receipt.json>
"""
import argparse
import json
import statistics
import time
from pathlib import Path

import log_world
import store


def run(args):
    report = {}
    if args.fixture:
        import log_world_fixture
        manifest, flat, boxes, replay = log_world_fixture.load(args.fixture)
        rec = {"seq": replay.seq, "eseq": int(manifest["event"][1:]), "parts": [], "words": "paired full check",
               "by": "house"}
        replay.compare(rec, flat, full=True)
        for nid, row in boxes.items():
            node = replay.world.nodes.get(nid, {})
            logged = [node.get(k) for k in ("x", "y", "w", "h")]
            if row["live"] != logged:
                replay.boxes.append(dict(row, thing=nid, log=logged,
                                         derived=bool(row["parent"] and row["layout"] != "free")))
        report = replay.report()
        report["manifest"] = manifest
        world = store.materialize(flat)
    else:
        # Public copy loader; no direct pickle/session-file access.
        import export_docs
        world = export_docs.load(args.benchmark_copy).world
        flat = store.flatten(world)
        rebuilt = store.materialize(flat)
        report.update(copy_only=True, checked_event=f"e{world._eseq}", facts=len(flat),
                      boxes=log_world.box_audit(world, rebuilt),
                      roundtrip_differences=len(store.diff(flat, store.flatten(rebuilt))))
    full, partial, ordinary = [], [], []
    tid = next(iter(world.subjects))
    for _ in range(20):
        t0 = time.perf_counter()
        log_world.freeze_world(world)
        ms = (time.perf_counter() - t0) * 1000
        full.append(ms)
        _, ms = log_world.observation(world, {tid})
        partial.append(ms)
        ordinary.append(full[-1] + partial[-1])
    report["capture_benchmark_ms"] = {
        "full": {"median": statistics.median(full), "max": max(full)},
        "one_subject": {"median": statistics.median(partial), "max": max(partial)},
        "ordinary_preimage_plus_one_subject": {"median": statistics.median(ordinary), "max": max(ordinary)},
        "samples_each": 20, "scope": "copy; locked-phase capture only (full uses frozen bytes), not live end-to-end lock holds",
    }
    report["facts"] = len(flat)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"receipt": str(path), "event": report.get("manifest", {}).get("event", report.get("checked_event")),
                      "facts": len(flat), "records": report.get("records"),
                      "state": report.get("state", "benchmark only"),
                      "differences": len(report.get("divergences", [])),
                      "box_differences": len(report["boxes"]),
                      "derived_boxes": sum(b["derived"] for b in report["boxes"]),
                      "capture_benchmark_ms": report["capture_benchmark_ms"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--fixture")
    group.add_argument("--benchmark-copy")
    parser.add_argument("--out", required=True)
    run(parser.parse_args())
