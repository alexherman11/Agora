"""check_numbers: do usage.py's rows match their sources? (a6265) Reads each agent's WHOLE transcript a second way (a plain
scan of every line, no offsets, no shared code) and prints, per agent, the writer's numbers beside the scan's.

    python src/desktop/at-work/check_numbers.py <house-state dir>

Only numbers and names are printed, never words of a transcript.
"""
import json
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parents[2] / "text-desk" / "notation"
sys.path.insert(0, str(LAB))
import usage  # noqa: E402


def scan(path):
    """-> (tokens in context, window, newest limit (five, week)) by the plainest reading of the file."""
    ctx = window = model = None
    lim = None
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None, None, None
    for line in lines:
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        d = rec.get("data") if isinstance(rec, dict) else None
        if not isinstance(d, dict):
            continue
        t = d.get("type")
        if t == "system" and d.get("subtype") == "init":
            model = d.get("model") or model
        if t == "assistant" and not d.get("parent_tool_use_id") and (d.get("message") or {}).get("usage"):
            u = d["message"]["usage"]
            ctx = u["input_tokens"] + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
        if t == "result":
            for name, m in (d.get("modelUsage") or {}).items():
                if name == model and m.get("contextWindow"):
                    window = m["contextWindow"]
        if t == "codex_event" and d.get("method") == "thread/tokenUsage/updated":
            tu = d["data"]["tokenUsage"]
            ctx, window = tu["last"]["totalTokens"], tu["modelContextWindow"]
        if t == "rate_limit_event":
            w = (d.get("rate_limit_info") or {}).get("unifiedWindows") or {}
            lim = (rec.get("at"), round(100 * w["five_hour"]["utilization"]), round(100 * w["seven_day"]["utilization"]))
    return ctx, window, lim


def main(a):
    base = Path(a[0])
    rows = usage.Usage("check", base).rows()
    st = json.loads((base / "house.json").read_text(encoding="utf-8"))
    newest = None
    print(f"{'actor':16} {'writer':>16} {'scan':>16}  agree")
    for r in rows[1:]:
        folder = r["corner"] if r["corner"] in (st.get("residents") or {}) else r["actor"]
        ctx, window, lim = scan(base / folder / "transcript.jsonl")
        if lim and (newest is None or lim[0] > newest[0]):
            newest = lim
        mine = f"{r.get('tokens', '-')}/{r.get('window', '-')}"
        theirs = f"{ctx if ctx is not None else '-'}/{window or '-'}"
        same = mine == theirs or ("tokens" not in r and (ctx is None or window is None or r.get("window_from") == "house"))
        if r.get("window_from") == "house":
            same = r.get("tokens") == ctx
            theirs += " (window: house)"
        print(f"{r['actor']:16} {mine:>16} {theirs:>16}  {'yes' if same else 'NO'}  {r.get('ctxpct', '')}")
    lim = rows[0]
    print(f"limit: writer five={lim.get('five')} week={lim.get('week')}  scan five={newest and newest[1]} "
          f"week={newest and newest[2]} (seen {time.strftime('%H:%M', time.localtime(newest[0])) if newest else '-'})")


if __name__ == "__main__":
    main(sys.argv[1:])
