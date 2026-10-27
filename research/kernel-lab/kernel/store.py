"""The store: a plain, append-only log of records, each holding the facts one act made (SHAPE section 1).

A fact is [thing, aspect, hash of the value before, value]; a fact of length 3 says the aspect is gone. The facts are the
truth; a record's `words` are testimony and are never parsed on replay. Records chain: each holds the digest of the one
before, and its own digest is taken over the record with every value replaced by its hash, so a value can later be
redacted ({"redacted": <hash>}) without breaking the chain.
"""
import hashlib
import json
import os
from pathlib import Path

SHAPE = 1                      # the record shape this code writes; every shape it ever wrote stays readable (READERS)
GONE = object()                # an aspect that is absent


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def h(v):
    """The hash of a value as the log writes it. Absent is '0'; a redacted value hashes to the hash it keeps."""
    if v is GONE:
        return "0"
    if isinstance(v, dict) and set(v) >= {"redacted"} and len(v) <= 3 and isinstance(v.get("redacted"), str):
        return v["redacted"]
    return hashlib.sha256(canon(v).encode()).hexdigest()[:16]


def _hashed(rec):
    """The record as its digest sees it: every fact's value replaced by the value's hash."""
    out = {k: v for k, v in rec.items() if k != "digest"}
    out["parts"] = [dict(p, facts=[f[:3] + ([h(f[3])] if len(f) > 3 else []) for f in p.get("facts", [])])
                    for p in rec.get("parts", [])]
    return out


def digest(rec):
    return hashlib.sha256(canon(_hashed(rec)).encode()).hexdigest()[:24]


def _read_v1(rec):
    return rec


READERS = {1: _read_v1}        # a shape change is made here, at read time, never by rewriting the log


class BrokenLog(Exception):
    pass


class State:
    """What the log says now: things -> aspects -> values, plus the indexes undo and the fence read (all derived)."""

    def __init__(self):
        self.things = {}       # id -> {aspect: value}
        self.history = {}      # (thing, aspect) -> [(seq, value)], oldest first; GONE when removed
        self.rev = {}          # thing -> seq of the last record that touched it
        self.top = {}          # tag -> highest number minted

    def get(self, t, a, default=None):
        return self.things.get(t, {}).get(a, default)

    def apply(self, facts, seq):
        for f in facts:
            t, a = f[0], f[1]
            v = f[3] if len(f) > 3 else GONE
            now = self.things.get(t, {}).get(a, GONE)
            if h(now) != f[2]:
                raise BrokenLog(f"record {seq}: {t} {a} was {h(now)} where the fact says {f[2]}")
            if v is GONE:
                self.things.get(t, {}).pop(a, None)
            else:
                self.things.setdefault(t, {})[a] = v
            self.history.setdefault((t, a), []).append((seq, v))
            self.rev[t] = seq
            tag = t.rstrip("0123456789")
            num = t[len(tag):]
            if num and tag.isalpha():
                self.top[tag] = max(self.top.get(tag, 0), int(num))

    def before(self, t, a, seq):
        """The value (t, a) held just before record `seq` set it."""
        hist = self.history.get((t, a), [])
        prior = GONE
        for s, v in hist:
            if s >= seq:
                break
            prior = v
        return prior

    def last_seq(self, t, a):
        hist = self.history.get((t, a))
        return hist[-1][0] if hist else 0

    def snapshot(self):
        """The things as plain data, for comparing a replay with memory."""
        return json.loads(canon(self.things))


class Log:
    """One world's log: `<world>/log/0001.jsonl`. Appends are fsynced before the act is answered."""

    def __init__(self, world_dir):
        self.dir = Path(world_dir) / "log"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / "0001.jsonl"
        self.records = []      # every record, in order (the skeleton keeps them in memory)
        self.head = ""         # digest of the last record

    def replay(self):
        """Read the whole log, check the chain, and return the State it builds. Never runs a word."""
        state = State()
        self.records, self.head = [], ""
        if not self.path.exists():
            return state
        lines = self.path.read_text(encoding="utf-8").split("\n")
        if lines and lines[-1].strip():
            # a write cut short leaves half a last line, with no newline after it: it never happened, so it goes
            try:
                json.loads(lines[-1])
            except json.JSONDecodeError:
                lines = lines[:-1]
                self.path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        for n, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                raise BrokenLog(f"line {n} is not JSON")
            rec = READERS[raw.get("v", 1)](raw)
            if rec.get("prev", "") != self.head:
                raise BrokenLog(f"record {rec.get('seq')} does not follow the one before it")
            if digest(rec) != rec.get("digest"):
                raise BrokenLog(f"record {rec.get('seq')} does not match its digest")
            for p in rec.get("parts", []):
                state.apply(p.get("facts", []), rec["seq"])
            self.records.append(rec)
            self.head = rec["digest"]
        return state

    def append(self, rec):
        rec = dict(rec, v=SHAPE, seq=len(self.records) + 1, prev=self.head)
        rec["digest"] = digest(rec)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(canon(rec) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        self.records.append(rec)
        self.head = rec["digest"]
        return rec
