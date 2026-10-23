"""Plan quotas, distinct from context tokens. Only CLI events and turn-boundary reads.

No credential access, account changes, model requests or polling. Native Usage notes
retain the last observation across house restarts; an expired reading is unknown.
"""
import json
import math
import re
import time


def q(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n") + '"'


def number(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def readings(event, at):
    """Whitelist quota fields; never infer quota from thread/tokenUsage context."""
    if event.get("type") == "rate_limit_event":
        windows = (event.get("rate_limit_info") or {}).get("unifiedWindows") or {}
        return [dict(provider="claude", window=key, label=label,
                     percent=value["utilization"] * 100, resets=value.get("resetsAt"),
                     asof=at, source="Claude CLI rate_limit_event")
                for key, label in (("five_hour", "5 hours"), ("seven_day", "7 days"))
                if isinstance(value := windows.get(key), dict) and number(value.get("utilization"))]
    if event.get("type") == "codex_event" and event.get("method") in (
            "account/rateLimits/read", "account/rateLimits/updated"):
        data = event.get("data") or {}
        buckets = data.get("rateLimitsByLimitId") or {}
        if not buckets and data.get("rateLimits"):
            bucket = data["rateLimits"]
            buckets = {bucket.get("limitId") or "codex": bucket}
        out = []
        for key, bucket in buckets.items():
            for slot in ("primary", "secondary"):
                value = bucket.get(slot) or {}
                if not number(value.get("usedPercent")):
                    continue
                minutes = value.get("windowDurationMins")
                label = {300: "5 hours", 10080: "7 days"}.get(minutes, f"{minutes} minutes" if minutes else slot)
                out.append(dict(provider="codex", window=f"{key}_{slot}", label=label,
                                percent=value["usedPercent"], resets=value.get("resetsAt"),
                                asof=at, source="Codex CLI " + event["method"]))
        return out
    return []


class Plans:
    def __init__(self, house, clock=time.time):
        self.house, self.clock = house, clock
        self.path = house.dir / "plan-usage.json"
        try:
            self.state = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.state = {}
        self.state.setdefault("windows", {})
        self.state.setdefault("pauses", {})
        self.dirty = True

    def save(self):
        from workshop import atomic_state
        atomic_state(self.path, self.state)

    def observe(self, event, at=None):
        rows = readings(event, self.clock() if at is None else at)
        changed = False
        for row in rows:
            if row["percent"] < 0 or row["percent"] > 100:
                continue
            if not number(row["resets"]):
                row["resets"] = None
            key = row["provider"] + "_" + row["window"]
            if row["asof"] >= self.state["windows"].get(key, {}).get("asof", 0):
                self.state["windows"][key] = row
                self.dirty = changed = True
        if event.get("type") == "plan_usage_unavailable":
            self.state.setdefault("unavailable", {})[event["provider"]] = dict(
                at=self.clock(), reason=event.get("reason", "CLI did not report plan usage"))
            self.dirty = True
            changed = True
        if changed:
            self.save()

    def current(self, provider):
        return [r for r in self.state["windows"].values() if r["provider"] == provider
                and r.get("resets") and r["resets"] > self.clock()]

    def reset(self, provider):
        # Only an exhausted window determines the retry, not a later, unspent weekly window.
        return max((r["resets"] for r in self.current(provider) if r["percent"] >= 100), default=0)

    def wait_until(self, provider):
        return self.state["pauses"].get(provider, {}).get("retry_at", 0)

    def fuel_reason(self, provider, cfg):
        if provider != "claude":
            return ""
        setting = cfg.get("claude_start_threshold", "off")
        try:
            threshold = float(setting)
        except (ValueError, TypeError):
            return ""
        if not 0 < threshold <= 100:
            return ""
        high = max(self.current("claude"), key=lambda r: r["percent"], default=None)
        if high and high["percent"] >= threshold:
            return f'Queued: Claude {high["percent"]:g}% used ({high["label"]}); start threshold {threshold:g}%.'
        return ""

    def queue_reason(self, provider, cfg):
        if self.wait_until(provider) > self.clock():
            return (f"Queued: {provider.title()} paused until "
                    + time.strftime("%H:%M", time.localtime(self.wait_until(provider))) + "; will start after reset.")
        return self.fuel_reason(provider, cfg)

    def target(self, target, text):
        # Deliberately separate from commission= so existing parked/handoff recovery remains authoritative.
        w = self.house.load()
        if target in w.subjects:
            target = next(iter(w.appearances_of(target)), target)
        node = w.nodes.get(target) or w.subjects.get(target) or {}
        props = node.get("props") or {}
        if node.get("subject"):
            props = (w.subjects.get(node["subject"]) or {}).get("props") or props
        if props.get("usage_state", "") != text:
            self.house.act("house", f"look {target} :1; do prop {target} usage_state={q(text)}")

    def paused(self, provider, target, retry_at):
        entry = self.state["pauses"].get(provider)
        # A first successful response does not mean every held card recovered.
        # Keep remaining targets and their notice outbox until the episode drains.
        first = not entry or (entry.get("resumed") and not entry["targets"]
                              and self.clock() >= entry["retry_at"])
        if first:
            stamp = time.strftime("%d %b %H:%M:%S", time.localtime(self.clock()))
            entry = dict(retry_at=retry_at, targets=[], resumed=False, notices=[dict(
                text=f"{provider.title()} limit reached at {stamp}. Work is kept and will resume after reset.",
                sent=False)])
            self.state["pauses"][provider] = entry
        entry["retry_at"] = max(entry["retry_at"], retry_at)
        if target not in entry["targets"]:
            entry["targets"].append(target)
        # Durable outbox: a restart checks the native notification record before
        # resending an intent whose acknowledgement was lost.
        self.save()
        for held in entry["targets"]:
            actual = self.actual_provider(held)
            if actual and actual != provider:
                continue  # an old provider episode cannot label a new runtime paused
            self.target(held, "Paused until "
                        + time.strftime("%d %b %H:%M %Z", time.localtime(entry["retry_at"])))
        self.flush_notices()

    def resumed(self, provider, target):
        # A model response proves work resumed; accepting stdin alone does not.
        for held_provider, entry in self.state["pauses"].items():
            if target not in entry["targets"]:
                continue
            self.target(target, "")
            entry["targets"].remove(target)
            first = not entry.get("resumed")
            entry["resumed"] = True
            if first:
                entry.setdefault("notices", []).append(dict(
                    text=held_provider.title() + " work resumed" +
                    (" with " + provider.title() if provider != held_provider else "") +
                    " at " + time.strftime("%d %b %H:%M:%S", time.localtime(self.clock())) + ".", sent=False))
            self.save()
        self.flush_notices()

    def restarting(self, target):
        if any(target in entry["targets"] for entry in self.state["pauses"].values()):
            self.target(target, "Resuming")

    def actual_provider(self, target):
        resident = getattr(self.house, "residents", {}).get(target)
        if resident:
            return resident.state.get("session_provider")
        workshop = getattr(self.house, "workshop", None)
        if workshop and target in workshop.workers:
            return workshop.workers[target].state.get("session_provider")
        return None

    def announce(self, key, text):
        outbox = self.state.setdefault("announcements", {})
        if key not in outbox:
            outbox[key] = {"notices": [{"text": text, "sent": False}]}
            self.save()
        self.flush_notices()

    def flush_notices(self):
        entries = (list(self.state["pauses"].values())
                   + list(self.state.get("announcements", {}).values()))
        for entry in entries:
            for notice in entry.get("notices", []):
                if notice["sent"]:
                    continue
                def recorded():
                    w = self.house.load()
                    for subject in w.subjects.values():
                        if (subject.get("props") or {}).get("role") != "notifications":
                            continue
                        for line in subject.get("lines", []):
                            event = w.event_by_id(line.get("ev")) or {}
                            if event.get("by") != "house":
                                continue
                            text = line.get("text", "").removeprefix("House:").strip()
                            # notify's $* preserves the enclosing quoted argument.
                            if text == notice["text"] or text == json.dumps(notice["text"], ensure_ascii=False):
                                return True
                    return False
                if recorded():
                    notice["sent"] = True
                    notice["delivery"] = "recorded"
                    self.save()
                    continue
                # Persist before dispatch: an interrupted/unknown acknowledgement
                # must not become a second append, even across a house restart.
                if notice.get("attempted"):
                    continue
                notice.update(attempted=True, delivery="unknown")
                self.save()
                try:
                    result = self.house.act("house", "notify " + q(notice["text"]))
                except Exception as exc:
                    notice["failure"] = type(exc).__name__
                    self.save()
                    continue
                # notify is an ordinary world verb. Its native append receipt is
                # authoritative; House.load may still hold the pre-append pickle.
                # Do not accept a generic "ok" or the verb's command echo.
                receipt = re.search(
                    r"^ok append 1 thing\(s\) matching prop:role=notifications: "
                    r"[as]\d+\s+\[(e\d+)\]\s*$", str(result or ""), re.MULTILINE)
                if receipt or recorded():
                    notice.update(sent=True, delivery="acknowledged" if receipt else "recorded")
                    if receipt:
                        notice["receipt"] = receipt.group(1)
                    self.save()

    def publish(self):
        """Dirty event/turn publication, using native facts, not a separate polling feed."""
        self.flush_notices()
        if not getattr(self, "_seeded", False):
            self._seeded = True
            # Reuse the house's existing metadata parser once on restart. Never
            # manufacture a fresh as-of time for an old stream observation.
            usage = getattr(self.house, "usage", None)
            if usage:
                usage.rows()
                for track in usage.tracks.values():
                    if track.limit:
                        at, info = track.limit
                        self.observe({"type": "rate_limit_event", "rate_limit_info": info}, at=at)
        expired = sorted(k for k, r in self.state["windows"].items()
                         if r.get("resets") and r["resets"] <= self.clock())
        if expired != getattr(self, "_expired", []):
            self._expired, self.dirty = expired, True
        if not self.dirty:
            return
        w = self.house.load()
        surfaces = [n for n in w.nodes.values() if (n.get("props") or {}).get("role") == "plan-usage"]
        if not surfaces:
            self.house.act("house", f'look {w.root} :1; do create {w.root} kind=surface title=Usage')
            w = self.house.load()
            made = [n for n in w.nodes.values() if n.get("title") == "Usage" and n["type"] == "surface"]
            if made:
                target = made[-1]["id"]
                self.house.act("house", f"look {target} :1; do prop {target} role=plan-usage")
            w = self.house.load()
            surfaces = [n for n in w.nodes.values() if (n.get("props") or {}).get("role") == "plan-usage"]
        if not surfaces:
            return
        surface = surfaces[0]["id"]
        rows = list(self.state["windows"].values())
        for provider in ("claude", "codex"):
            if not any(r["provider"] == provider for r in rows):
                missing = self.state.get("unavailable", {}).get(provider, {})
                rows.append(dict(provider=provider, window="unavailable", label="plan", percent=None,
                                 resets=None, asof=missing.get("at"), source=missing.get("reason", "Waiting for CLI quota report")))
        for row in rows:
            key = row["provider"] + "_" + row["window"]
            w = self.house.load()
            found = [s for s in w.subjects.values() if (s.get("props") or {}).get("usage_key") == key]
            if not found:
                self.house.act("house", f'look {surface} :1; do create {surface} kind=note '
                               f'title={q(row["provider"].title() + " · " + row["label"])} role=usage-window usage_key={q(key)}')
                w = self.house.load()
                found = [s for s in w.subjects.values() if (s.get("props") or {}).get("usage_key") == key]
            if not found:
                continue
            subject = found[0]
            target = next(iter(w.appearances_of(subject["id"])), None)
            if not target:
                continue
            valid = row["percent"] is not None and row["resets"] and row["resets"] > self.clock()
            value = f'{row["percent"]:g}%' if valid else "unavailable"
            reset = time.strftime("%d %b %H:%M", time.localtime(row["resets"])) if row["resets"] else "not reported"
            asof = time.strftime("%d %b %H:%M", time.localtime(row["asof"])) if row["asof"] else "not yet"
            text = f'{row["provider"].title()} · {row["label"]}: {value}. Resets {reset}. As of {asof}. Source: {row["source"]}.'
            props = dict(provider=row["provider"], window=row["label"], percent=row["percent"] if valid else "",
                         usage_available="yes" if valid else "no",
                         usage_visible="yes",
                         resets_at=row["resets"] or "", as_of=row["asof"] or "", source=row["source"],
                         usage_label=f'{row["provider"].title()} {value}', usage_detail=text)
            args = " ".join(f"{k}={q(v)}" for k, v in props.items()
                            if str((subject.get("props") or {}).get(k, "")) != str(v))
            if args:
                self.house.act("house", f'look {target} :1; do prop {target} {args}')
            if subject.get("text") != text:
                self.house.act("house", f'look {target} :1; do rewrite {target} text={q(text)}')
        active = {r["provider"] + "_" + r["window"] for r in rows}
        w = self.house.load()
        for subject in w.subjects.values():
            props = subject.get("props") or {}
            if props.get("role") == "usage-window" and props.get("usage_key") not in active:
                target = next(iter(w.appearances_of(subject["id"])), None)
                if target and props.get("usage_visible") != "no":
                    self.house.act("house", f'look {target} :1; do prop {target} usage_visible=no')
        self.dirty = False
