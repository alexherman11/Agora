"""House-owned paired proof export. No pickle/session export and no model calls.

freeze() is the short locked phase. export() copies an immutable whole-record
prefix outside the lock, writes hashes and publishes a manifest LAST.
"""
import hashlib
import json
import os
import threading
import time
import uuid
from pathlib import Path

import store


def freeze(desk, path):
    import log_world
    t0 = time.perf_counter()
    log = store.Log(store.log_path(path))
    head = log.head()
    if not head:
        raise ValueError("missing log; paired export refused")
    end = log.path.stat().st_size
    frozen = log_world.freeze_world(desk.world)
    event = next((e["id"] for e in reversed(desk.world.events) if e.get("verb") not in store.OFF_VERBS),
                 f"e{getattr(desk.world, '_eseq', 0)}")
    return {"frozen": frozen, "event": event, "seq": head[0], "state": head[1], "end": end,
            "log": str(log.path), "at": time.time(), "capture_ms": (time.perf_counter() - t0) * 1000,
            }


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for data in iter(lambda: f.read(1 << 20), b""):
            digest.update(data)
    return digest.hexdigest()


def export(frozen, target):
    """Target is new and house-selected, never an arbitrary path supplied by a visitor."""
    target = Path(target)
    target.mkdir(parents=True, exist_ok=False)
    try:
        source = Path(frozen["log"])
        log = target / "live.log.jsonl"
        remaining = frozen["end"]
        with source.open("rb") as src, log.open("xb") as dst:
            while remaining:
                data = src.read(min(remaining, 1 << 20))
                if not data:
                    raise ValueError("log shortened during paired export")
                dst.write(data)
                remaining -= len(data)
            dst.flush()
            os.fsync(dst.fileno())
        # Parsing the WHOLE prefix also detects torn records and unsupported shape.
        from log_world import Replay
        replay = Replay()
        end = 0
        for rec, end in store.Log(log).records():
            replay.consume(rec, historical=True)
        if (end != frozen["end"] or replay.seq != frozen["seq"] or replay.event != frozen["event"]
                or replay.digest != frozen["state"] or replay.divergences):
            raise ValueError("event/sequence/state mismatch, malformed chain, or truncated paired copy")
        import log_world
        observed = log_world.thaw_observation(frozen["frozen"])
        facts = target / "live.facts.json"
        facts.write_text(json.dumps([[tid, aspect, v] for (tid, aspect), v in store.flatten(observed).items()],
                                   ensure_ascii=False), encoding="utf-8")
        boxes = target / "boxes.json"
        boxes.write_text(json.dumps(log_world.box_samples(observed), ensure_ascii=False), encoding="utf-8")
        manifest = {k: frozen[k] for k in ("event", "seq", "state", "end", "at", "capture_ms")}
        manifest.update(shape=1, log_sha256=_sha(log), facts_sha256=_sha(facts), boxes_sha256=_sha(boxes))
        # A failed/partial directory has no manifest and must never be consumed.
        (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest
    except Exception as e:
        (target / "FAILED.txt").write_text(f"{type(e).__name__}: {e}", encoding="utf-8")
        raise


def load(target):
    """Refuse partial, modified, wrong-event or unsupported fixtures before returning facts."""
    target = Path(target)
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("shape") != 1:
        raise ValueError("unsupported paired fixture")
    for name, key in (("live.log.jsonl", "log_sha256"), ("live.facts.json", "facts_sha256"),
                      ("boxes.json", "boxes_sha256")):
        if _sha(target / name) != manifest.get(key):
            raise ValueError("paired fixture hash mismatch: " + name)
    from log_world import Replay
    replay = Replay()
    end = 0
    for rec, end in store.Log(target / "live.log.jsonl").records():
        replay.consume(rec, historical=True)
    if (end != manifest["end"] or replay.seq != manifest["seq"] or replay.event != manifest["event"]
            or replay.digest != manifest["state"] or replay.divergences):
        raise ValueError("paired fixture event/record mismatch")
    flat = {(tid, aspect): value for tid, aspect, value in
            json.loads((target / "live.facts.json").read_text(encoding="utf-8"))}
    boxes = json.loads((target / "boxes.json").read_text(encoding="utf-8"))
    return manifest, flat, boxes, replay


def house_copy(desk, path, checker):
    """Internal writer-start hook, not a Desk command or network export API.

    The fixed destination/source are the per-card grant c7602. `as=house` is
    claim-based, so it must NOT authorize filesystem export.
    """
    commission = "a7573"
    if Path(path).stem != "frontier":
        return
    root = Path(__file__).resolve().parents[3]
    if root.parent.name == ".worktrees":
        root = root.parent.parent
    allowed = root / ".worktrees" / commission
    if not allowed.is_dir() or allowed.resolve() != allowed:
        return
    output = allowed / ".agora-tmp" / "log-world-proof"
    # One immutable fixture per grant, across restarts. No repeated large copies.
    existing = next(output.glob("*/manifest.json"), None)
    if existing:
        checker.fixture_receipt = {"manifest": str(existing), "state": "existing; verify with log_world_proof.py"}
        return
    frozen = freeze(desk, path)
    target = output / (frozen["event"] + "-" + uuid.uuid4().hex[:8])

    def run():
        try:
            manifest = export(frozen, target)
            checker.fixture_receipt = {"manifest": str(target / "manifest.json"), "event": manifest["event"],
                                       "manifest_sha256": _sha(target / "manifest.json"), "state": "exported"}
        except Exception as e:
            checker.fixture_receipt = {"state": "unavailable", "reason": f"{type(e).__name__}: {e}",
                                       "failed": str(target / "FAILED.txt")}
        if checker.publish:
            checker.publish()
    checker.fixture_receipt = {"state": "export pending", "event": frozen["event"], "target": str(target)}
    threading.Thread(target=run, name="paired-log-proof", daemon=True).start()
