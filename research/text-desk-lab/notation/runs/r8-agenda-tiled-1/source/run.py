"""Run one live Terra trial of the notation lab. Records everything under runs/<label>/."""

import argparse
import hashlib
import json
import shutil
import time
from copy import deepcopy
from pathlib import Path

from jeffx import INSTRUCTIONS, MODEL, NATIVE, TextJeff, tools_for
from tasks import TASKS, assess, build

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task", choices=list(TASKS))
    parser.add_argument("--variant", default="outline", choices=["outline", "relations", "tree", "structured", "apply", "moo", "acme", "knife", "tiled"])
    parser.add_argument("--label", required=True)
    options = parser.parse_args()
    out = HERE / "runs" / options.label
    out.mkdir(parents=True, exist_ok=False)
    source = out / "source"
    source.mkdir()
    hashes = {}
    for path in HERE.glob("*.py"):
        shutil.copy2(path, source / path.name)
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    desk = build(options.task, options.variant)
    start = desk.snapshot()
    traces = []
    t0 = time.monotonic()

    def dispatch(name, args):
        at = time.monotonic()
        result = desk.dispatch(name, args)
        entry = {"index": len(traces) + 1, "at_seconds": round(at - t0, 2), "name": name,
                 "arguments": deepcopy(args), "result": deepcopy(result), "seconds": round(time.monotonic() - at, 4)}
        traces.append(entry)
        with (out / "tools.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(json.dumps({"trial": options.label, "call": entry["index"], "name": name,
                          "line": args.get("line") or f"{args.get('verb', '')} {args.get('target', '')}".strip(),
                          "error": result.get("error")}), flush=True)
        return result

    report = {
        "task": options.task, "variant": options.variant, "label": options.label, "model": MODEL,
        "reasoning": "medium", "prompt": TASKS[options.task], "instructions": INSTRUCTIONS,
        "tools": tools_for(options.variant), "source_sha256": hashes, "native_transport": str(NATIVE),
        "transport_sha256": hashlib.sha256((NATIVE / "agora3/jeff.py").read_bytes()).hexdigest(),
    }
    jeff = TextJeff(out, dispatch, options.variant)
    try:
        report["account_status"] = jeff.status()
        t1 = time.monotonic()
        report["reply"] = jeff.send(TASKS[options.task])
        report["elapsed_seconds"] = round(time.monotonic() - t1, 1)
        report["outcome"] = jeff.last_outcome
    except Exception as exc:
        report["error"] = str(exc)
        raise
    finally:
        jeff.close()
        report["assessment"] = assess(options.task, desk)
        report["calls"] = len(traces)
        report["refusals"] = sum("error" in t["result"] for t in traces)
        report["reads"] = sum(1 for t in traces if not _is_mutation(t))
        report["mutations"] = sum(1 for t in traces if _is_mutation(t) and "error" not in t["result"])
        report["result_chars"] = sum(len(json.dumps(t["result"])) for t in traces)
        for filename, value in [("report.json", report), ("initial.json", start), ("final.json", desk.snapshot()),
                                ("events.json", desk.events), ("external-edits.json", desk.injections)]:
            (out / filename).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
        _transcript(out, traces, report)
        print(json.dumps({"finished": options.label, "assessment": report["assessment"], "calls": report["calls"],
                          "refusals": report["refusals"], "seconds": report.get("elapsed_seconds"),
                          "error": report.get("error")}), flush=True)


def _is_mutation(t):
    if t["name"] in ("do", "undo"):
        return True
    line = (t["arguments"].get("line") or "").strip().lower()
    return line.startswith(("do ", "undo ", "apply"))


def _transcript(out, traces, report):
    lines = [f"# {report['label']}  task={report['task']} variant={report['variant']}", f"prompt: {report['prompt']}", ""]
    for t in traces:
        a = t["arguments"]
        call = a.get("line") if "line" in a else json.dumps(a)
        lines.append(f"[{t['index']} @{t['at_seconds']}s] {t['name']}: {call}")
        r = t["result"]
        body = r.get("text") if "text" in r else "ERR " + str(r.get("error"))
        lines.append("\n".join("    " + l for l in str(body).splitlines()))
        lines.append("")
    lines.append("## reply\n" + str(report.get("reply", "")))
    lines.append("\n## assessment\n" + json.dumps(report.get("assessment"), indent=1))
    (out / "transcript.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
