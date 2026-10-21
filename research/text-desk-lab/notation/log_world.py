"""An unserved, log-only World and an ordered, event-driven comparison worker.

No Desk, actor, verbs, session loader or live-world reference enters Replay.
The bridge supplies detached observations; the only output is a report.
DESK_LOG_WORLD=off disables it. There is no clock/polling thread.
"""
import copy
import json
import os
import pickle
import queue
import threading
import time
from pathlib import Path
from datetime import datetime
import log_world_accounting as accounting

import store

STATUS_TITLE = "Log world: is it in step with the live world?"
REPORT_WORDS = "log-world report"
EXCLUSIONS = (
    "Standing/presence; personal seen marks, folds and views; painter reports; "
    "undo revisions and indexes; joined chat text when derived from its lines; "
    "boxes and z-order inside a non-free flow (their stated order is checked). "
    "Free-surface boxes, definitions, links, comments, lines and all stated props ARE checked."
    " Checker-owned status/evidence records are replayed but never count as observations or advance observed time."
)

def dated(value):
    return datetime.fromtimestamp(value).astimezone().isoformat(timespec="seconds") if value is not None else None


def display_report(report):
    """Human-facing dates; internal numeric clocks stay outside world facts."""
    result = copy.deepcopy(report)
    if "at" in result:
        result["at"] = dated(result["at"])
    for gap in result.get("unavailable", []):
        for key in ("from", "to"):
            gap[key] = dated(gap.get(key))
    if "paired_fixture" in result and isinstance(result["paired_fixture"].get("at"), (int, float)):
        result["paired_fixture"]["at"] = dated(result["paired_fixture"]["at"])
    return result


def answer_key(report):
    return (report["state"], report["line"],
            json.dumps(report.get("divergences", [])[:1], sort_keys=True, ensure_ascii=False))


def freeze_world(w):
    """Fast, in-process serialization of stated data; never a Desk or undo events.

    These bytes are not a file format or external input. Flattening and box
    classification happen after releasing the live lock.
    """
    loose = {k: v for k, v in vars(w).items() if k not in store.OFF_WORLD}
    return pickle.dumps((w.subjects, w.nodes, w.links, loose), protocol=pickle.HIGHEST_PROTOCOL)


def thaw_observation(data):
    from world import World
    subjects, nodes, links, loose = pickle.loads(data)
    w = World.__new__(World)
    w.subjects, w.nodes, w.links = subjects, nodes, links
    w.events, w.injections = [], []
    vars(w).update(loose)
    return w


def box_samples(w):
    return {nid: {"name": w.title(n), "parent": n.get("parent"),
                  "layout": w.nodes.get(n.get("parent"), {}).get("layout", "free"),
                  "derived": bool(n.get("parent") and
                                  w.nodes.get(n.get("parent"), {}).get("layout", "free") != "free"),
                  "live": [n.get(k) for k in ("x", "y", "w", "h")]}
            for nid, n in w.nodes.items()}


def event_of(rec, fallback="e0"):
    events = [p["e"] for p in rec.get("parts", ()) if p.get("e")]
    return max(events, key=lambda x: int(x[1:])) if events else f"e{rec.get('eseq', fallback[1:])}"


def observation(w, touched=None):
    """Detached live facts, not the logger's cached flat_after. Caller holds its usual lock."""
    t0 = time.perf_counter()
    if touched is None:
        facts = store.flatten(w)
    else:
        _, facts = store.flatten_some(w, {}, touched & w.subjects.keys(), touched & w.nodes.keys())
    # Node plain fields may contain mutable lists; never hand them across the lock.
    return copy.deepcopy(facts), (time.perf_counter() - t0) * 1000


def box_audit(w, rebuilt):
    """A mismatch is excluded only if its parent's layout really makes the box derived."""
    rows = []
    for nid, n in w.nodes.items():
        other = rebuilt.nodes.get(nid)
        if other is None:
            continue
        before = [n.get(k) for k in ("x", "y", "w", "h")]
        after = [other.get(k) for k in ("x", "y", "w", "h")]
        if before != after:
            parent = w.nodes.get(n.get("parent"), {})
            rows.append({"thing": nid, "name": w.title(n), "parent": n.get("parent"),
                         "layout": parent.get("layout", "free"), "live": before, "log": after,
                         "derived": bool(n.get("parent") and parent.get("layout", "free") != "free")})
    return rows


class Replay:
    """Private replay state. Values come only from log records, never from observations."""

    def __init__(self):
        self.flat, self.world = {}, store.materialize({})
        self.digest = store.digest({})
        self.seq, self.event, self.records = 0, "e0", 0
        self.first_checked, self.full_event = None, "none"
        self.divergences, self.boxes = [], []
        self.checked_records = 0
        self.reason = "not checked since this checker started"

    def consume(self, rec, historical=False):
        if rec.get("shape") != store.SHAPE or rec.get("seq") != self.seq + 1:
            raise ValueError("unsupported shape or non-consecutive log record")
        rows = [r for p in rec.get("parts", ()) for r in p.get("facts", ())]
        for tid, aspect, before, *value in rows:
            if store.h(self.flat.get((tid, aspect), store.ABSENT)) != before:
                self.add(rec, tid, aspect, self.flat.get((tid, aspect), store.ABSENT),
                         value[0] if value else store.ABSENT, "broken before-value hash")
        facts = [(tid, aspect, store.whole(v, self.flat.get((tid, aspect), store.ABSENT)))
                 for tid, aspect, v in store.facts_of(rec)]
        # Outside records deliberately repair unlogged edits. Keep the original gap
        # even if the repair makes the final states equal.
        if not historical:
            for part in rec.get("parts", ()):
                if part.get("cause") == "outside":
                    for tid, aspect, value in store.dec(part.get("facts", ())):
                        old = self.flat.get((tid, aspect), store.ABSENT)
                        self.add(rec, tid, aspect, store.whole(value, old), old, "unlogged edit repaired by logger")
        expected = store._move(self.digest, self.flat, facts)
        store.patch(self.flat, facts)
        store.apply(self.world, facts, bump=False)
        self.digest = expected
        if rec.get("state") != expected:
            self.add(rec, "world", "record digest", rec.get("state"), expected, "broken state digest")
        self.seq, self.event = rec["seq"], event_of(rec, self.event)
        self.world._ids = rec.get("ids", self.world._ids)
        self.world._eseq = int(self.event[1:])
        self.records += 1

    def add(self, rec, tid, aspect, live, logged, reason="different facts"):
        def shown(v):
            return "(absent)" if v is store.ABSENT else store.plain(v)
        # No deduplication across records: a later discrepancy remains evidence.
        self.divergences.append({
            "seq": rec.get("seq", self.seq), "event": event_of(rec, self.event),
            "thing": tid, "aspect": aspect, "live": shown(live), "log": shown(logged),
            "command": rec.get("words", ""), "by": rec.get("by", "?"), "reason": reason,
        })

    def compare(self, rec, live, full=False):
        # Compare the materialized world, not merely our flat replay accumulator.
        if full:
            logged = store.flatten(self.world)
        else:
            scope = {tid for tid, _ in live}
            scope.update(tid for tid, _, _ in store.facts_of(rec))
            _, logged = store.flatten_some(self.world, {}, scope & self.world.subjects.keys(),
                                           scope & self.world.nodes.keys())
            # flatten_some expands neighbouring groups. Live capture already made
            # that expansion once; expanding the resulting scope again would
            # compare unrelated grandchildren only on the replay side.
            logged = {k: v for k, v in logged.items() if k[0] in scope or k[0] == "world" or k[1] == "link"}
        for tid, aspect, _ in store.diff(logged, live):
            self.add(rec, tid, aspect, live.get((tid, aspect), store.ABSENT),
                     logged.get((tid, aspect), store.ABSENT))
        self.reason = ""
        if self.first_checked is None:
            self.first_checked = self.event
        if full:
            self.full_event = self.event
        self.checked_records += 1

    def report(self):
        state = "unavailable" if self.reason else "diverged" if self.divergences else "in-step"
        if state == "unavailable":
            line = "unavailable: " + self.reason
        elif self.divergences:
            d = self.divergences[0]
            title = self.flat.get((d["thing"], "title"))
            if not title:
                subject = self.flat.get((d["thing"], "subject"))
                title = self.flat.get((subject, "title"), "A thing without a name")
            line = (f'diverged at {d["event"]}: {title} {d["aspect"]} is {d["live"]!r} live '
                    f'and {d["log"]!r} from the log; the record was {d["command"]!r} by {d["by"]}')
        else:
            line = f"in step since {self.first_checked}"
        return {"state": state, "checked_event": self.event if self.first_checked else "none",
                "line": line, "records": self.records, "checked_records": self.checked_records,
                "last_full": self.full_event, "divergences": copy.deepcopy(self.divergences),
                "boxes": copy.deepcopy(self.boxes), "exclusions": EXCLUSIONS}


class Checker:
    """One consumer per live writer. Queue never waits while the live lock is held."""

    def __init__(self, path, journal, publish=None, clock=time.time, monotonic=time.monotonic, world=None):
        self.path, self.journal = Path(path), Path(journal)
        self.publish, self.clock, self.monotonic = publish, clock, monotonic
        self.witness_world = world
        self.accounting_correction = None
        self.evidence_revision = 0
        self.evidence = None
        self.replay = Replay()
        self.offset = 0
        self.jobs = queue.Queue(maxsize=8)
        self.report_lock = threading.Lock()
        self.current = self.replay.report()
        self.stopped = False
        self.covered_seconds = 0.0
        self.covered_records = 0
        self.gaps, self.max_capture_ms = [], 0.0
        self.last_observation = None
        self.previous_at = None
        self.gap_start = self.clock()
        self.gap_reason = "not checked since checker start"
        self.full_generation = 0
        self.full_completed = 0
        self.needs_full = False
        self.covered_seq = 0
        self.fixture_receipt = None
        self.publish_lock_ms = {"last": 0.0, "max": 0.0}
        self.thread = threading.Thread(target=self._work, name="log-world", daemon=True)
        self.thread.start()

    def _load_receipts(self):
        if not self.journal.exists():
            return
        # Only our small checker receipts, never session transcripts.
        reports = []
        with self.journal.open(encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                if rec.get("kind") == "report":
                    reports.append(rec)
                    self.gaps = rec.get("unavailable", [])
                    self.previous_at = rec["at"]
                    self.covered_seq = rec.get("records", 0)
                elif rec.get("kind") == "divergence":
                    self.replay.divergences.append(rec["detail"])
        own = set()
        if reports and reports[-1].get("counting_version") != accounting.VERSION:
            # House-internal metadata reconciliation, off-lock. No raw log output.
            metadata = {rec["seq"]: accounting.self_record(rec) for rec, _ in store.Log(self.path).records()}
            own = {seq for seq, is_own in metadata.items() if is_own}
        else:
            metadata = None
        self.covered_seconds, self.covered_records, self.accounting_correction = accounting.reconcile(
            reports, own, set(metadata) if metadata is not None else None)
        if self.previous_at is not None:
            self.gap_start = self.previous_at
            self.gap_reason = "checker restart; no comparison coverage claimed"

    def submit(self, live, end, event, full=False, capture_ms=0, boxes=None, quiet=False, frozen=None,
               before=None, touched=(), words="", by="house"):
        if self.stopped:
            return False
        try:
            if full:
                self.full_generation += 1
            self.jobs.put_nowait({"live": live, "end": end, "event": event, "full": full,
                                 "capture_ms": capture_ms, "boxes": boxes, "quiet": quiet,
                                 "full_generation": self.full_generation,
                                 "frozen": frozen,
                                 "before": before, "touched": tuple(touched), "words": words, "by": by,
                                 "at": self.clock(), "mono": self.monotonic()})
            return True
        except queue.Full:
            self.unavailable("comparison queue overflow; full recovery follows when the queue drains")
            self.needs_full = True
            self.full_generation += 1
            return False

    def unavailable(self, why):
        with self.report_lock:
            self.current = dict(self.current, state="unavailable", line="unavailable: " + why)
            if self.gap_start is None:
                self.gap_start = self.current.get("at", self.clock())
            self.gap_reason = why
        self.last_observation = None
        self.witness()

    def snapshot(self):
        with self.report_lock:
            report = copy.deepcopy(self.current)
        if self.needs_full or (self.full_completed == 0 and self.full_completed < self.full_generation and not self.stopped):
            report.update(state="unavailable", line="unavailable: full comparison has not completed")
        if report["state"] == "unavailable":
            report["unavailable"] = copy.deepcopy(self.gaps) + [
                {"from": self.gap_start or self.clock(), "to": None, "why": report["line"]}]
        if self.fixture_receipt:
            report["paired_fixture"] = copy.deepcopy(self.fixture_receipt)
        report["accounting_correction"] = copy.deepcopy(self.accounting_correction)
        report["accounting_state"] = (self.accounting_correction or {}).get("status", "current")
        report["full_check_pending"] = self.full_completed < self.full_generation
        report["witness_error"] = getattr(self, "witness_error", None)
        return report

    def witness(self):
        if self.witness_world:
            import witnessed
            report = display_report(self.snapshot())
            # Large evidence lives in its note/receipt, never in the moving row.
            row = {k: v for k, v in report.items() if k not in ("boxes", "divergences", "exclusions", "paired_fixture")}
            try:
                witnessed.write(self.witness_world, "log-world", [row], by="house", changed_only=True)
                self.witness_error = None
            except OSError as e:
                # A failed output file cannot stop the independent comparison.
                self.witness_error = f"{type(e).__name__}: {e}"

    def _write(self, row):
        self.journal.parent.mkdir(parents=True, exist_ok=True)
        with self.journal.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def _work(self):
        try:
            self._load_receipts()       # disk/history work never takes the live lock
            init_error = None
        except Exception as e:
            init_error = f"cannot read checker receipts: {type(e).__name__}: {e}"
        while True:
            job = self.jobs.get()
            if job is None:
                self.jobs.task_done()
                return
            try:
                if self.stopped:
                    if self.jobs.empty():
                        return
                    continue
                if init_error:
                    raise ValueError(init_error)
                before = len(self.replay.divergences)
                if job["before"] is not None:
                    pre = thaw_observation(job["before"])
                    live_before, _ = observation(pre, set(job["touched"]))
                    trigger = {"seq": self.replay.seq + 1, "eseq": int(job["event"][1:]),
                               "words": job["words"], "by": job["by"], "parts": []}
                    self.replay.compare(trigger, live_before)
                if job["frozen"] is not None:
                    observed = thaw_observation(job["frozen"])
                    job["live"] = store.flatten(observed)
                    job["boxes"] = box_samples(observed)
                last = None
                compared = 0
                initial = self.offset == 0
                for rec, end in store.Log(self.path).records(self.offset):
                    if end > job["end"]:
                        break
                    self.replay.consume(rec, historical=initial)
                    self.offset, last = end, rec
                    compared += 1
                if self.offset != job["end"]:
                    raise ValueError("checkpoint ends inside a missing/torn record")
                last = last or {"seq": self.replay.seq, "eseq": int(job["event"][1:]), "parts": []}
                self.replay.event = job["event"]
                self.replay.compare(last, job["live"], job["full"])
                if job["full"]:
                    self.full_completed = job["full_generation"]
                    if self.full_completed == self.full_generation:
                        self.needs_full = False
                if job["boxes"] is not None:
                    # Box samples are evidence only, not an input to the replay.
                    rows = []
                    for nid, n in job["boxes"].items():
                        other = self.replay.world.nodes.get(nid, {})
                        logged = [other.get(k) for k in ("x", "y", "w", "h")]
                        if n["live"] != logged:
                            rows.append(dict(n, thing=nid, log=logged))
                    self.replay.boxes = rows
                report = self.replay.report()
                if self.needs_full:
                    report.update(state="unavailable",
                                  line="unavailable: observations were dropped; awaiting full recovery")
                now = self.clock()
                mono = self.monotonic()
                if self.gap_start is not None and report["state"] != "unavailable":
                    self.gaps.append({"from": self.gap_start, "to": now, "why": self.gap_reason})
                    self.gap_start = None
                eligible = (compared > 0 and not accounting.self_record(last)
                            and self.replay.seq > self.covered_seq)
                accounting_ok = (self.accounting_correction or {}).get("status") != "unavailable"
                if report["state"] == "in-step" and eligible and accounting_ok:
                    if self.last_observation is not None:
                        old_at, old_mono = self.last_observation
                        delta = mono - old_mono
                        # Never count an unobserved idle/sleep interval as proved time.
                        if 0 <= delta <= 60 and abs(now - old_at - delta) <= 1:
                            self.covered_seconds += delta
                        else:
                            self.gaps.append({"from": old_at, "to": now,
                                              "why": "over 60s without a checked observation, or clock discontinuity"})
                    if self.replay.seq > self.covered_seq:
                        # Historical replay checks hashes, not historical live states.
                        # Count only endpoints with an independent live observation.
                        self.covered_records += 1
                        self.covered_seq = self.replay.seq
                    self.last_observation = (now, mono)
                elif report["state"] != "in-step":
                    self.last_observation = None
                self.covered_seq = max(self.covered_seq, self.replay.seq)
                self.max_capture_ms = max(self.max_capture_ms, job["capture_ms"])
                report.update(observed_seconds=self.covered_seconds, observed_records=self.covered_records,
                              unavailable=self.gaps, capture_ms=job["capture_ms"],
                              max_capture_ms=self.max_capture_ms, at=now,
                              publication_lock_ms=dict(self.publish_lock_ms))
                for detail in self.replay.divergences[before:]:
                    self._write({"kind": "divergence", "at": now, "detail": detail})
                receipt = {k: report[k] for k in ("at", "state", "checked_event", "records", "last_full",
                                                  "observed_seconds", "observed_records", "unavailable",
                                                  "capture_ms", "max_capture_ms")}
                receipt.update(counting_version=accounting.VERSION,
                               accounting_correction=self.accounting_correction)
                self._write(dict(receipt, kind="report"))
                if job["full"]:
                    self._write({"kind": "full-check", "at": now, "event": self.replay.event,
                                 "seq": self.replay.seq, "facts": len(self.replay.flat),
                                 "boxes": self.replay.boxes})
                new_divergence = len(self.replay.divergences) > before
                changed_answer = answer_key(self.current) != answer_key(report)
                with self.report_lock:
                    if job["full"] or new_divergence:
                        self.evidence_revision += 1
                        self.evidence = {
                            "checked_event": report["checked_event"], "last_full": report["last_full"],
                            "boxes": report["boxes"], "divergences": report["divergences"],
                            "exclusions": EXCLUSIONS, "at": now,
                            "accounting_correction": self.accounting_correction,
                        }
                    self.current = report
                self.witness()
                if self.publish and (changed_answer or job["full"] or new_divergence):
                    self.publish()
            except Exception as e:
                self.unavailable(f"{type(e).__name__}: {e}")
                self.stopped = True
                self.witness()
                if self.publish:
                    self.publish()
            finally:
                self.jobs.task_done()
            if self.stopped and self.jobs.empty():
                return

    def close(self):
        self.stopped = True
        self.unavailable("checker stopped")
        self.jobs.put(None)
        self.thread.join(timeout=5)


_CHECKERS = {}


def enabled():
    return os.environ.get("DESK_LOG_WORLD", "").lower() != "off" and os.environ.get("DESK_LOG") != "off"


def checkpoint(desk, path, full=False, quiet=False, touched=None, before=None, words="", by="house", before_ms=0):
    t0 = time.perf_counter()
    checker = _CHECKERS.get(str(Path(path)))
    if checker is None or checker.stopped or not enabled():
        return
    if checker.needs_full:
        if not checker.jobs.empty():
            return                    # explicit unavailable span, never pretend skipped observations were checked
        full, quiet, before = True, False, None
    end = checker.path.stat().st_size
    # Events since the last capture identify touched entities even when facts did
    # not change (and allow detecting extra, unlogged aspects on those entities).
    n0 = getattr(checker, "event_index", 0)
    events = () if full else desk.world.events[n0:]
    touched = set(touched or ()) | {e.get("target") for e in events}
    touched.update(tid for e in events for tid in e.get("changed", ()))
    touched.discard(None)
    touched.update(desk.world.nodes[n].get("subject") for n in list(touched) if n in desk.world.nodes)
    touched.discard(None)
    frozen = freeze_world(desk.world) if full else None
    live, _ = (None, 0) if full else observation(desk.world, touched)
    checker.event_index = len(desk.world.events)
    event = f"e{getattr(desk.world, '_eseq', 0)}"
    ms = (time.perf_counter() - t0) * 1000 + before_ms
    checker.submit(live, end, event, full, ms, None, quiet, frozen, before, touched, words, by)


def status_node(w):
    return next((n["id"] for n in w.nodes.values() if n.get("type") == "appearance"
                 and w.subjects.get(n.get("subject"), {}).get("title") == STATUS_TITLE), None)


def attach(desk, path, publish=None, journal=None):
    """Called only by the writer's bridge, not when loading an arbitrary session."""
    key = str(Path(path))
    if key in _CHECKERS or not status_node(desk.world):
        return _CHECKERS.get(key)
    log = store.log_path(path)
    if not enabled() or not log.exists():
        return None
    journal = journal or Path(__file__).parent / "house-state" / Path(path).stem / "log-world.jsonl"
    checker = Checker(log, journal, publish, world=Path(path).stem)
    _CHECKERS[key] = checker
    checkpoint(desk, path, full=True)
    # House-owned, fixed per-card grant, not an actor-authorized host command.
    import log_world_fixture
    try:
        log_world_fixture.house_copy(desk, path, checker)
    except Exception as e:
        checker.fixture_receipt = {"state": "unavailable", "reason": f"{type(e).__name__}: {e}"}
    return checker


def project(desk, path, record=True):
    """Only changed answers reach the status note; evidence has a separate gate."""
    nid = status_node(desk.world)
    if not nid:
        return
    checker = _CHECKERS.get(str(Path(path)))
    if not enabled():
        if checker:
            checker.unavailable("checker switched off")
            checker.stopped = True
            report = checker.snapshot()
        else:
            report = {"state": "unavailable", "checked_event": "none", "line": "unavailable: checker switched off"}
    elif checker:
        report = checker.snapshot()
    else:
        report = {"state": "unavailable", "checked_event": "none",
                  "line": "unavailable: no running checker for this writer"}
    evidence_node = next((n["id"] for n in desk.world.nodes.values()
                          if n.get("type") == "appearance" and
                          desk.world.subjects.get(n.get("subject"), {}).get("props", {}).get("role")
                          == "log-world-evidence"), None)
    first = report.get("divergences", [])[:1]
    props = {"state": report["state"], "line": report["line"],
             "first_divergence": store.h(first), "evidence": evidence_node or ""}
    text = report["line"] + "\n\n" + EXCLUSIONS
    text += "\n\nLive observation counts and dated gaps: witnessed:log-world. Full-check/divergence detail: Evidence."
    subject = desk.world.subjects[desk.world.nodes[nid]["subject"]]
    old_props = subject.get("props", {})
    remove = [k for k in ("observed", "unavailable", "at", "capture_ms", "max_capture_ms") if k in old_props]
    status_changed = (subject.get("text") != text or bool(remove) or
                      any(old_props.get(k, "") != v for k, v in props.items()))
    evidence_text = None
    evidence, evidence_revision = None, None
    if evidence_node and checker:
        with checker.report_lock:
            if checker.evidence_revision != getattr(checker, "projected_evidence_revision", 0):
                evidence = copy.deepcopy(checker.evidence)
                evidence_revision = checker.evidence_revision
    if evidence is not None:
        detail = display_report(evidence)
        if checker.fixture_receipt:
            detail["paired_fixture"] = display_report({"paired_fixture": checker.fixture_receipt})["paired_fixture"]
        evidence_text = ("Last full comparison / retained divergences\n\n"
                         + json.dumps(detail, ensure_ascii=False, indent=2))
    if not status_changed and evidence_text is None:
        return
    ctx = store.safe_begin(desk, path) if record else None
    import moo
    if status_changed:
        if subject.get("text") != text:
            desk.world.apply("edit", subject["id"], None, {"text": text}, "house")
        changes = {k: v for k, v in props.items() if old_props.get(k, "") != v}
        changes["checked_event"] = report["checked_event"]  # event of this verdict, not a running counter
        if remove:
            changes["remove"] = ",".join(remove)
        moo.REGISTRY["prop"].run(desk.world, nid, dict(changes, _by="house"))
    if evidence_text is not None:
        evidence_subject = desk.world.subjects[desk.world.nodes[evidence_node]["subject"]]
        if evidence_subject.get("text") != evidence_text:
            desk.world.apply("edit", evidence_subject["id"], None, {"text": evidence_text}, "house")
        checker.projected_evidence_revision = evidence_revision
    if record:
        store.safe_commit(ctx, desk, REPORT_WORDS, "house")


def command(desk, argv):
    ctx = getattr(desk, "_store", None)
    if ctx is None:
        return "unavailable: this world has no active log"
    path = str(ctx.log.path)
    # Ctx holds the log path; registered bridges are indexed by the snapshot path.
    checker = next((c for c in _CHECKERS.values() if str(c.path) == path), None)
    if not checker or not enabled():
        return "unavailable: no running log-world checker; only the live writer hosts it"
    if checker.stopped:
        return checker.snapshot()["line"] + "; checker must restart before another check can run"
    if argv not in ([], ["check"], ["status"]):
        return "log-world takes check or status; DESK_LOG_WORLD=off is the off switch"
    if argv == ["check"]:
        snapshot_path = next(k for k, c in _CHECKERS.items() if c is checker)
        checkpoint(desk, snapshot_path, full=True)
        return "Full log-world comparison queued; the Log world status note will show the result."
    report = display_report(checker.snapshot())
    return (report["line"] + "\n" + json.dumps(
        {k: report.get(k) for k in ("checked_event", "observed_seconds", "observed_records",
                                   "at", "unavailable", "accounting_correction",
                                   "accounting_state", "witness_error")}, ensure_ascii=False))


def committed(ctx, desk, words, by=None):
    for path, checker in tuple(_CHECKERS.items()):
        if str(checker.path) == str(ctx.log.path):
            checkpoint(desk, path, quiet=words == REPORT_WORDS, touched=getattr(ctx, "touched", ()),
                       before=getattr(ctx, "observed_before", None), words=words, by=by or desk.world.me,
                       before_ms=getattr(ctx, "before_ms", 0))


def before(ctx, desk):
    for checker in tuple(_CHECKERS.values()):
        if str(checker.path) == str(ctx.log.path) and not checker.stopped and not checker.needs_full and enabled():
            t0 = time.perf_counter()
            ctx.observed_before = freeze_world(desk.world)
            ctx.before_ms = (time.perf_counter() - t0) * 1000


def failed(ctx, why):
    for checker in tuple(_CHECKERS.values()):
        if str(checker.path) == str(ctx.log.path):
            checker.unavailable(why)
            checker.stopped = True
            if checker.publish:
                # Never re-enter the writer while its current command holds the lock.
                threading.Thread(target=checker.publish, name="log-world-unavailable", daemon=True).start()


def detach(desk, path, why):
    checker = _CHECKERS.get(str(Path(path)))
    if checker:
        checker.publish = None
        checker.unavailable(why)
        checker.stopped = True
        project(desk, path)
        try:
            checker.jobs.put_nowait(None)
        except queue.Full:
            pass
