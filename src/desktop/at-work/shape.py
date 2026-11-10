"""Print the SHAPE of usage-bearing events in house transcripts: keys and numbers, never words.

    python src/desktop/at-work/shape.py <transcript.jsonl> [more ...]

For Claude: the last `result` (usage, modelUsage) and the last `rate_limit_event`, and
the last assistant message's usage. For Codex: every codex_event method name with a count,
and the last token-count-like notification's numeric fields.
"""
import collections
import json
import sys


def numbers(x, path="", out=None):
    """Every leaf that is a number, bool or short enum-ish string, by dotted path."""
    out = {} if out is None else out
    if isinstance(x, dict):
        for k, v in x.items():
            numbers(v, f"{path}.{k}" if path else k, out)
    elif isinstance(x, list):
        out[path] = f"[list {len(x)}]"
        for i, v in enumerate(x[:3]):
            numbers(v, f"{path}[{i}]", out)
    elif isinstance(x, (int, float, bool)) or x is None:
        out[path] = x
    elif isinstance(x, str):
        out[path] = x if len(x) <= 24 and " " not in x else f"<str {len(x)}>"
    return out


def main(paths):
    for p in paths:
        print("==", p)
        methods = collections.Counter()
        last = {}
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                ev = rec.get("data") if rec.get("kind") == "event" else None
                if not isinstance(ev, dict):
                    continue
                t = ev.get("type")
                if t == "codex_event":
                    m = ev.get("method")
                    methods[m] += 1
                    if m and ("token" in m.lower() or "rate" in m.lower() or "usage" in m.lower()):
                        last[f"codex:{m}"] = (rec.get("at"), ev.get("data"))
                elif t == "result":
                    last["result"] = (rec.get("at"), {k: ev.get(k) for k in ("usage", "modelUsage", "total_cost_usd", "num_turns", "subtype", "is_error")})
                elif t == "rate_limit_event":
                    last["rate_limit_event"] = (rec.get("at"), ev)
                elif t == "assistant":
                    msg = ev.get("message") or {}
                    last["assistant.usage"] = (rec.get("at"), {"model": msg.get("model"), "usage": msg.get("usage")})
                elif t == "system" and ev.get("subtype") == "init":
                    last["init"] = (rec.get("at"), {"model": ev.get("model")})
        if methods:
            print("codex methods:", dict(methods.most_common()))
        for k, (at, v) in last.items():
            print(f"-- {k} at {at}")
            for path, val in numbers(v).items():
                print(f"   {path} = {val}")


if __name__ == "__main__":
    main(sys.argv[1:])
