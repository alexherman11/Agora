"""Run a fresh Terra session, retaining exact inputs, outputs and state assertions."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import time

from scenarios import TASKS, assess, build
from transport import INSTRUCTIONS, MODEL, NATIVE, TextJeff, tools_for

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task", choices=list(TASKS))
    parser.add_argument("--variant", default="outline")
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
    start_time = time.monotonic()

    def dispatch(name, args):
        at = time.monotonic()
        result = desk.dispatch(name, args)
        entry = {
            "index": len(traces) + 1,
            "at_seconds": at - start_time,
            "name": name,
            "arguments": deepcopy(args),
            "result": deepcopy(result),
            "seconds": time.monotonic() - at,
        }
        traces.append(entry)
        with (out / "tools.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(
            json.dumps(
                {
                    "trial": options.label,
                    "call": entry["index"],
                    "name": name,
                    "target": args.get("target"),
                    "verb": args.get("verb"),
                    "error": result.get("error"),
                }
            ),
            flush=True,
        )
        return result

    report = {
        "task": options.task,
        "variant": options.variant,
        "label": options.label,
        "model": MODEL,
        "reasoning": "medium",
        "prompt": TASKS[options.task],
        "instructions": INSTRUCTIONS,
        "tools": tools_for(options.variant),
        "source_sha256": hashes,
        "native_transport": str(NATIVE),
        "transport_sha256": hashlib.sha256((NATIVE / "agora3/jeff.py").read_bytes()).hexdigest(),
    }
    jeff = TextJeff(out, dispatch, options.variant)
    try:
        report["account_status"] = jeff.status()
        inference_start = time.monotonic()
        report["reply"] = jeff.send(TASKS[options.task])
        report["elapsed_seconds"] = time.monotonic() - inference_start
        report["outcome"] = jeff.last_outcome
    except Exception as exc:
        report["error"] = str(exc)
        raise
    finally:
        jeff.close()
        report["assessment"] = assess(options.task, desk)
        report["calls"] = len(traces)
        report["refusals"] = sum("error" in t["result"] for t in traces)
        report["projection_chars"] = sum(
            len(json.dumps(t["result"])) for t in traces if t["name"] == "look"
        )
        report["mutations"] = sum(t["name"] == "act" and "error" not in t["result"] for t in traces)
        for filename, value in [
            ("report.json", report),
            ("initial.json", start),
            ("final.json", desk.snapshot()),
            ("events.json", desk.events),
            ("external-edits.json", desk.injections),
        ]:
            (out / filename).write_text(
                json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        print(
            json.dumps(
                {
                    "finished": options.label,
                    "assessment": report["assessment"],
                    "calls": report["calls"],
                    "seconds": report.get("elapsed_seconds"),
                    "error": report.get("error"),
                }
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
