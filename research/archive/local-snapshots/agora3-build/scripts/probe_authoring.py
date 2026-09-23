"""Explicitly run a live Astra/account + Linux native-package authorship check.

This spends model usage and executes newly authored Python in the configured VM.
The native world is new; candidates use the resettable yard and installed actions
use the operator's live Linux guest. This command does not reconnect its bridge.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from agora3.gateway import Gateway
from agora3.guest import Guest
from agora3.jeff import Jeff
from agora3.world import Refusal
from agora3.yard import Yard

PROMPT = """This is a real native-development acceptance task in an empty disposable
Agora world. You have a running Linux guest and authorized native package tools.
Create the missing capability yourself. Discover and inspect the real tools;
do not assume a special counter helper already exists.

Define an application facet named alex.counter.state with an integer value.
Create one counter object named counter-main starting at zero. Author a Python
native package alex.counter exporting an increment action that adds one to the
specified counter's current value through proposed native changes. Use the
documented runtime interfaces and revision checks; invent the implementation.

Save and build the package, exercise the increment candidate against the counter,
and verify candidate testing leaves the live counter at zero. Then install it,
discover its installed action, and invoke that installed increment exactly twice
in this same conversation. Verify the durable counter is two. Do not replace the
increments with direct data writes. Report the installed revision and observed
test results. Do not run guest.execute or modify any shell or other application.
Keep all authored code free of filesystem, network or process side effects; this
test only exercises proposed native counter changes. No host filesystem or
source-code changes are part of this acceptance task.
"""


def emit(event):
    if event["type"] == "tool.started":
        print(json.dumps({"type": "tool.started", "name": event["name"]}), flush=True)
    elif event["type"] == "text.delta":
        print(event["text"], end="", flush=True)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def run(machine: Path, yard_config: Path, output: Path) -> bool:
    # Never reuse or overwrite a previous evidence directory or private world.
    output.mkdir(parents=True, exist_ok=False)
    trace_path = output / "trace.jsonl"
    trace_path.touch()
    report = {"passed": False, "world": str(output / "world"), "model": "gpt-6-astra"}
    jeff = None
    trace = []
    sentinel = output / "host-sentinel.txt"
    sentinel.write_text("Host sentinel: native authorship must leave this file unchanged.\n")
    sentinel_hash = hashlib.sha256(sentinel.read_bytes()).hexdigest()

    def record(entry):
        trace.append(entry)
        with trace_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    try:
        guest = Guest(machine)
        yard = Yard(yard_config, guest)
        report["guest"] = guest.status()
        report["yard"] = yard.status()
        require(report["guest"].get("state") == "running", "Start the configured Linux VM first.")
        require(
            report["yard"].get("available"), "Configure a separate resettable candidate yard first."
        )
        gateway = Gateway(output / "world", guest=guest, yard=yard)
        actor = gateway.principal("jeff")

        def dispatch(name, arguments):
            before = gateway.world.query(limit=1)["watermark"]
            entry = {"name": name, "arguments": arguments, "before": before}
            try:
                if name == "guest.execute":
                    raise Refusal(
                        "This probe permits native package execution only, no shell calls."
                    )
                result = gateway.dispatch(actor, name, arguments)
                entry.update(result=result, after=gateway.world.query(limit=1)["watermark"])
                if name == "candidate.exercise":
                    require(entry["after"] == before, "Candidate mutated the native world.")
                    require(
                        result.get("native_writes") == 0, "Candidate did not report zero writes."
                    )
                    require(
                        gateway.world.get("counter-main")["facets"]["alex.counter.state"]["value"]
                        == 0,
                        "Candidate testing must leave the live counter at zero.",
                    )
                return result
            except Exception as exc:
                entry["error"] = str(exc)
                raise
            finally:
                record(entry)

        jeff = Jeff(output / "world", dispatch, gateway.describe)
        require(jeff.model == "gpt-6-astra", "This probe requires Astra; unset AGORA_JEFF_MODEL.")
        report["account"] = jeff.status()
        require(report["account"]["signed_in"], "Sign in to your OpenAI account before this probe.")
        print(
            "Running live Astra authorship with a new world, candidate yard and live guest.",
            flush=True,
        )
        report["reply"] = jeff.send(PROMPT, emit)
        report["counter"] = gateway.world.get("counter-main")
        report["installation"] = gateway.packages.installation("alex.counter")
        report["replay"] = gateway.world.verify()
        report["events"] = gateway.world.query(limit=1)["watermark"]
        candidates = [t for t in trace if t["name"] == "candidate.exercise" and "error" not in t]
        invocations = [t for t in trace if t["name"] == "action.invoke" and "error" not in t]
        report["candidate_exercises"] = len(candidates)
        report["installed_invocations"] = len(invocations)
        report["host_sentinel_unchanged"] = (
            hashlib.sha256(sentinel.read_bytes()).hexdigest() == sentinel_hash
        )
        require(
            report["counter"]["facets"]["alex.counter.state"]["value"] == 2, "Counter is not two."
        )
        require(
            report["counter"]["revision"] == 3, "Expected creation and exactly two counter writes."
        )
        require(candidates, "No successful candidate exercise was observed.")
        require(len(invocations) == 2, "Expected exactly two successful installed invocations.")
        committed_values = []
        for invocation in invocations:
            transaction = invocation["result"].get("transaction") or {}
            changes = [
                item for item in transaction.get("items", []) if item["id"] == "counter-main"
            ]
            require(len(changes) == 1, "Each installed increment must commit the counter itself.")
            committed_values.append(changes[0]["facets"]["alex.counter.state"]["value"])
        require(committed_values == [1, 2], "Installed actions did not commit the two increments.")
        require(
            all(t["arguments"].get("package") == "alex.counter" for t in invocations),
            "Installed invocations must use the authored counter package.",
        )
        require(report["installation"]["revision"] >= 1, "Package was not installed.")
        require(
            report["events"] >= 7,
            "Expected schema, counter, source, build, install and two writes.",
        )
        require(report["replay"]["ok"], "Replay does not match current state.")
        require(report["host_sentinel_unchanged"], "Host sentinel changed.")
        require(not any(t["name"] == "guest.execute" for t in trace), "A shell call was attempted.")
        report["passed"] = True
    except Exception as exc:
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        if jeff is not None:
            try:
                jeff.close()
            except Exception as exc:
                report["close_error"] = {"type": type(exc).__name__, "message": str(exc)}
        (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(
            "\n" + json.dumps({"report": str(output / "report.json"), "passed": report["passed"]})
        )
    return report["passed"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--machine", type=Path, default=Path("worlds/dev/machine.json"))
    parser.add_argument(
        "--yard",
        type=Path,
        default=None,
        help="Candidate yard configuration; defaults to yard.json beside --machine.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("local/acceptance") / datetime.now(UTC).strftime("authoring-%Y%m%d-%H%M%S-%f"),
        help="New evidence directory; refuses an existing path.",
    )
    args = parser.parse_args()
    try:
        passed = run(args.machine, args.yard or args.machine.with_name("yard.json"), args.output)
    except OSError as exc:
        parser.exit(1, f"Could not create the new evidence directory: {exc}\n")
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
