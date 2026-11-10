"""Read-only receipt audit; never emits messages, prompts, arguments or reasoning.

Reads the house's own structured receipts, not CLI account directories.
Result counters and assistant-message counters are independent views, never added.
Assistant output usage can be preliminary; it is not used as generated-token total.
"""
import argparse
import collections
import datetime as dt
import json
from pathlib import Path


def stamp(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def audit(root, begin, end):
    groups = {}
    files = 0
    malformed = 0
    quota = []
    ledger = {}
    for path in sorted(root.glob("*/transcript.jsonl")):
        label = path.parent.name
        bucket = "JEFF" if label == "f5189" else (
            "workers" if label.startswith("worker-") or "builder-" in label else "other residents")
        group = groups.setdefault(bucket, dict(kinds=collections.Counter(), types=collections.Counter(),
            models=collections.Counter(), messages={}, first=None, last=None,
            active=set(), tools=collections.Counter(), max_context=0))
        active = False
        with path.open(encoding="utf-8", errors="replace") as source:
            for raw in source:
                try:
                    rec = json.loads(raw)
                except ValueError:
                    malformed += 1
                    continue
                at = rec.get("at", 0)
                if not isinstance(at, (int, float)) or at >= end:
                    continue
                ev = rec.get("data")
                if rec.get("kind") == "event" and isinstance(ev, dict) and ev.get("type") == "result":
                    sid = ev.get("session_id") or label
                    for model, usage in (ev.get("modelUsage") or {}).items():
                        numeric = {}
                        for key, value in usage.items():
                            if isinstance(value, (int, float)) and not isinstance(value, bool):
                                if key in ("inputTokens", "outputTokens", "cacheReadInputTokens",
                                           "cacheCreationInputTokens"):
                                    numeric[key] = value
                        ledger.setdefault((sid, model), []).append((at, bucket, numeric))
                if at < begin:
                    continue
                active = True
                group["active"].add(label)
                group["first"] = min(group["first"] or at, at)
                group["last"] = max(group["last"] or at, at)
                kind = rec.get("kind")
                group["kinds"][kind] += 1
                ev = rec.get("data")
                if kind != "event" or not isinstance(ev, dict):
                    continue
                typ = ev.get("type", "unknown")
                group["types"][typ] += 1
                if typ == "system":
                    group["types"]["system:" + str(ev.get("subtype"))] += 1
                if typ == "rate_limit_event":
                    info = ev.get("rate_limit_info") or {}
                    windows = info.get("unifiedWindows") or {}
                    quota.append(dict(at=stamp(at), bucket=bucket,
                        windows={k: {f: v.get(f) for f in ("utilization", "resetsAt")}
                                 for k, v in windows.items() if isinstance(v, dict)}))
                if typ == "result":
                    for model, usage in (ev.get("modelUsage") or {}).items():
                        group["models"][model] += 1
                if typ == "assistant":
                    msg = ev.get("message") or {}
                    usage = msg.get("usage") or {}
                    # Streaming updates can repeat an id. Retain component maxima.
                    identity = msg.get("id")
                    if not identity:
                        group["types"]["assistant_without_id"] += 1
                        continue
                    old = group["messages"].setdefault(identity, {})
                    for key, value in usage.items():
                        if isinstance(value, (int, float)) and not isinstance(value, bool):
                            old[key] = max(value, old.get(key, 0))
                    context = sum(usage.get(k, 0) or 0 for k in (
                        "input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
                    group["max_context"] = max(group["max_context"], context)
                    for block in msg.get("content", []):
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            # Only tool names; no command text, arguments or results.
                            group["tools"][block.get("name", "unknown")] += 1
        files += active
    windows = {}
    for row in sorted(quota, key=lambda r: r["at"]):
        v = row["windows"].get("five_hour", {})
        if v.get("resetsAt") is None or v.get("utilization") is None:
            continue
        entry = windows.setdefault(stamp(v["resetsAt"]), dict(observations=0, first=row,
            last=row, first_full=None))
        entry["observations"] += 1
        entry["last"] = row
        if v["utilization"] >= 1 and entry["first_full"] is None:
            entry["first_full"] = row
    out = dict(begin=stamp(begin), end_exclusive=stamp(end), active_receipt_files=files,
               malformed_lines=malformed, groups={}, quota_windows=windows)
    baselines_missing = collections.Counter()
    decreases = 0
    for observations in ledger.values():
        previous = None
        for at, bucket, counters in sorted(observations, key=lambda row: row[0]):
            if at >= begin:
                if previous is None:
                    baselines_missing[bucket] += 1
                else:
                    delta = {}
                    for key, value in counters.items():
                        if key in previous:
                            if value < previous[key]:
                                decreases += 1
                            else:
                                delta[key] = value - previous[key]
                    groups[bucket].setdefault("result_counter_deltas", collections.Counter()).update(delta)
            previous = counters
    out["result_session_models_missing_baseline"] = baselines_missing
    out["result_counter_decreases_skipped"] = decreases
    for key, group in groups.items():
        if not group["first"]:
            continue
        totals = collections.Counter()
        for usage in group["messages"].values():
            totals.update(usage)
        out["groups"][key] = dict(
            first=stamp(group["first"]), last=stamp(group["last"]),
            active_folders=len(group["active"]), kinds=group["kinds"], types=group["types"],
            result_models=group["models"],
            result_counter_deltas=group.get("result_counter_deltas", {}),
            unique_assistant_messages=len(group["messages"]), message_usage_totals=totals,
            max_message_context=group["max_context"], tool_names=group["tools"])
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    p.add_argument("--begin", default="2026-10-20T00:00:00-07:00")
    p.add_argument("--end", default="2026-10-20T16:52:00-07:00")
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    report = json.dumps(audit(args.root, dt.datetime.fromisoformat(args.begin).timestamp(),
                             dt.datetime.fromisoformat(args.end).timestamp()), indent=2)
    if args.out:
        args.out.write_text(report + "\n", encoding="utf-8")
        print("Wrote aggregate counters:", args.out)
    else:
        print(report)
