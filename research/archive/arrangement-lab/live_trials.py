"""Real JEFF conversations in new native worlds; matched model, source and browser tools."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import time

ROOT = Path("C:/Projects/Agora/local/arrangement-trials-20260916")
FROZEN = ROOT / "baseline"
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(FROZEN / "src"), str(FROZEN / "scripts")]
os.environ["AGORA_WORKERS"] = "0"
os.environ["AGORA_JEFF_REASONING"] = "medium"
os.environ["AGORA_JEFF_TIMEOUT"] = "600"
os.environ["AGORA_JEFF_MAX_CALLS"] = "90"

from agora3.gateway import Gateway
from agora3.guest import Guest
from agora3.jeff import Jeff
from agora3.world import Refusal
from agora3.yard import Yard
from application_packages import bundle, desktop_source, install_source
import agora3.server as server_module

NODE = Path(
    "C:/Users/Alex/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
)
WORKER = Path("C:/Projects/Agora/worlds/parallel-desk/browser_worker.cjs")
SPEC_FILE = Path("C:/Projects/Agora/worlds/parallel-desk/browser_specs.py")

COMMON = """This is an authorized trial inside your own isolated Agora candidate world,
with a fresh JEFF conversation and synthetic work. Use your ordinary native tools.
You can author and install reusable packages and edit the shell when needed. You have
a dedicated Linux execution VM and a distinct candidate yard; neither is the resident's
guest. Stay within this world and those machines. Preserve subject identities, text,
unrelated arrangements and drafts. Do not contact anyone or access other worlds.
The experiment browser tools inspect and interact with this world's actual browser;
they are structured DOM observations, not screenshot vision. Verify rendered results
and durable state. Report honestly if part of the request is unsupported or unverified.
You do not need further permission for reversible work in this candidate world.
"""

REQUESTS = {
    1: """I'm about to join an OAS call. Arrange every OAS-related open appearance on the
left in a readable, non-overlapping grid. Keep the OAS mail thread on the right where
I can read it and above the other windows. Put everything unrelated behind the work.
The same note appears twice: keep both appearances and don't move the document's
content into a new object. Treat the whole rearrangement as one decision I can undo
later without losing edits to the documents. Make it persist across browser reload.
Please do it and verify the actual result. If the existing capabilities don't express
this directly, build a small reusable capability rather than merely describing one.""",
    2: """Build two saved configurations of the same OAS material: Planning is a freeform
board with two occurrences of the OAS risks note; Review is an ordered reading list.
Put the two risks occurrences beside one another in Planning, and order Review by
title. Move just one risks occurrence; Review and the other occurrence must stay put.
Show both configurations as actual application views. Reuse the available arrangement
machinery where possible. A future non-note subject should be able to participate
without conversion into a note. Verify independence, shared content, and persistence.""",
    3: """Add a reusable staircase arrangement that is not in the supplied layout catalog:
each successive appearance starts 44 pixels right and 60 pixels below the previous,
keeping current sizes. Apply it to the OAS appearances, in title order, then demonstrate
the same reusable planner on a separate reference-card board without converting its
subjects into notes. Keep unrelated items unchanged. Include an inspectable preview
and a way to undo the accepted arrangement. Use a small extension of the available
structure, rather than replacing the whole desktop. Verify real rendered behavior.""",
}


class Browser:
    def __init__(self, output):
        source = WORKER.read_text(encoding="utf-8")
        source = source.replace("if(req.op==='evaluate'){const f=await frame();",
                                "if(req.op==='evaluate'){const f=await frame(page,req.view);")
        source = source.replace(
            "fontSize:getComputedStyle(n).fontSize}",
            "fontSize:getComputedStyle(n).fontSize,zIndex:getComputedStyle(n).zIndex,position:getComputedStyle(n).position}",
        )
        path = output / "browser_worker.cjs"
        path.write_text(source, encoding="utf-8")
        self.process = subprocess.Popen(
            [str(NODE), str(path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=(output / "browser.stderr.log").open("w"),
            text=True,
            encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.lock = threading.RLock()

    def call(self, **args):
        with self.lock:
            self.process.stdin.write(json.dumps(args) + "\n")
            self.process.stdin.flush()
            result = json.loads(self.process.stdout.readline())
            if "error" in result:
                raise Refusal(result["error"])
            return result["result"]

    def close(self):
        try:
            self.call(op="close")
        finally:
            self.process.stdin.close()
            self.process.wait(timeout=15)


def native_snapshot(gateway):
    data = gateway.world.query(limit=1000)
    if not data["complete"]:
        raise RuntimeError("Fixture exceeds complete observation bound")
    return data


def seed(gateway, candidate):
    actor = gateway.principal("human")
    source = desktop_source()
    if candidate:
        from native_arrangement import render_source

        source = render_source(source)
    install_source(gateway, actor, source)
    for variant in ("notes", "documents"):
        gateway.dispatch(actor, "application.import", {"bundle": bundle(variant)})
    gateway.define_schema(
        actor,
        type="trial.meta",
        schema={
            "type": "object",
            "properties": {"project": {"type": "string"}, "kind": {"type": "string"}},
            "required": ["project", "kind"],
            "additionalProperties": False,
        },
    )
    subjects = []
    titles = [
        "OAS agenda",
        "OAS budget",
        "OAS risks",
        "OAS timeline",
        "OAS decisions",
        "OAS travel",
    ]
    for i in range(15):
        oid = f"work-{i:02}"
        title = titles[i] if i < 6 else ("OAS mail thread" if i == 6 else f"Unrelated work {i - 6}")
        facets = {
            "core.title": {"text": title},
            "core.text": {
                "text": f"# {title}\n\nRetained work for {title}.\n\nDo not lose this paragraph."
            },
            "text.format": {"kind": "markdown"},
            "trial.meta": {
                "project": "OAS" if i < 7 else "Other",
                "kind": "mail" if i == 6 else "note",
            },
        }
        subjects.append({"id": oid, "expected_revision": 0, "facets": facets})
    gateway.commit(actor, subjects)
    views = []
    for i in range(16):
        subject = f"work-{i:02}" if i < 15 else "work-02"
        package = "agora.documents" if i in (6, 15) else "agora.notes"
        views.append(
            gateway.dispatch(
                actor,
                "application.open",
                {
                    "package": package,
                    "subject": subject,
                    "bounds": {
                        "x": (i * 131) % 740,
                        "y": (i * 97) % 650,
                        "width": 310 if i != 6 else 460,
                        "height": 280 if i != 6 else 460,
                    },
                },
            )
        )
    if candidate:
        gateway.arrangements.seed(actor)
    return views


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=["baseline", "candidate"], required=True)
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument(
        "--baseline-kind", choices=["example-fixture", "installed-world"], required=True,
        help="Identify the application baseline explicitly; this runner currently supports only examples.",
    )
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--resume-from", help="Resume the retained resident in this exact trial world.")
    args = parser.parse_args()
    if args.baseline_kind != "example-fixture":
        parser.error(
            "This runner seeds repository examples, not installed world packages. "
            "It cannot run a current-world comparison. Implement and verify installed-package, "
            "state, runtime and rendered-baseline provenance before enabling that mode."
        )
    output = ROOT / "runs" / args.label
    output.mkdir(parents=True, exist_ok=False)
    for name in (
        "live_trials.py",
        "native_arrangement.py",
        "model.py",
        "planners.py",
        "surface_planning.py",
        "field_witnesses.py",
        "rendered_observation.py",
    ):
        path = HERE / name
        if path.exists():
            shutil.copy2(path, output / name)
    report = {
        "arm": args.arm,
        "round": args.round,
        "label": args.label,
        "baseline_kind": "example-fixture",
        "comparison_scope": "Frozen Agora4 native code plus repository example applications",
        "current_world_comparison": False,
        "model": "gpt-6-astra",
        "reasoning": "medium",
        "turns": [],
        "errors": [],
        "source_hashes": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob("*.py")
        },
    }
    world = ROOT / "runs" / args.resume_from / "world" if args.resume_from else output / "world"
    if args.resume_from:
        if not (world / "world.db").exists():
            raise RuntimeError("Missing retained trial world")
        report["resumed_from"] = args.resume_from
    else:
        world.mkdir()
    shutil.copy2(ROOT / "machines/execution/machine.json", world / "machine.json")
    shutil.copy2(ROOT / "yard.json", world / "yard.json")
    guest = Guest(world / "machine.json")
    baseline = json.loads((ROOT / "machines/execution/baseline.json").read_text())
    vm_config = guest._config()
    if vm_config["vm_id"] != baseline["vm_id"]:
        raise RuntimeError("Trial VM identity mismatch")
    guest.stop()
    guest._vbox("snapshot", vm_config["vm_id"], "restore", baseline["snapshot_id"])
    guest.start()
    Yard._ready(guest)
    browser = jeff = server = app = None
    try:
        GatewayClass = Gateway
        if args.arm == "candidate":
            from native_arrangement import ArrangementGateway, SPECS

            GatewayClass = ArrangementGateway
            # Admit only the new registered native operation names in the authored host bridge.
            extra = (
                "\n" + "".join("allowed.add(" + json.dumps(s["name"]) + ");" for s in SPECS) + "\n"
            )
            server_module.FRAME = server_module.FRAME.replace(
                "for(const method of [", extra + "for(const method of [", 1
            )
        gateway = GatewayClass(world)
        report["initial_views"] = (gateway.applications.list()["views"] if args.resume_from
                                   else seed(gateway, args.arm == "candidate"))
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        server_module.Gateway = GatewayClass
        server, app = server_module.serve(world, port)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        gateway = app.gateway
        report["bridge"] = app.connect_guest()
        if not report["bridge"].get("connected"):
            raise RuntimeError("Trial native bridge failed")
        browser = Browser(output)
        browser.call(op="open", url=f"http://127.0.0.1:{port}/#" + gateway.keep["operator"])
        browser.call(op="interact", action="resize", width=1900, height=1200)
        # Browser publications finish before the timed request begins.
        if args.arm == "candidate":
            gateway.arrangements.browser = browser
        ns = {}
        exec(SPEC_FILE.read_text(), ns)
        extras = ns["extra_specs"]
        traces = []
        actor = gateway.principal("jeff")

        def describe():
            return gateway.describe() + extras

        def dispatch(name, arguments):
            entry = {
                "at": time.time(),
                "name": name,
                "arguments": arguments,
                "before": gateway.world.query(limit=1)["watermark"],
            }
            start = time.monotonic()
            try:
                if name == "experiment.observe":
                    result = browser.call(op="observe", **arguments)
                elif name == "experiment.interact":
                    result = browser.call(op="interact", **arguments)
                elif name == "experiment.sequence":
                    result = browser.call(op="sequence", **arguments)
                elif name == "experiment.inspect_candidate":
                    receipt = gateway.packages.receipt(arguments["build"])
                    result = browser.call(op="candidate", html=receipt["browser_artifact"])
                else:
                    result = gateway.dispatch(actor, name, arguments)
                entry["result"] = result
                return result
            except Exception as exc:
                entry["error"] = str(exc)
                raise
            finally:
                entry["seconds"] = time.monotonic() - start
                entry["after"] = gateway.world.query(limit=1)["watermark"]
                traces.append(entry)
                with (output / "tools.jsonl").open("a", encoding="utf-8") as file:
                    file.write(json.dumps(entry, ensure_ascii=False) + "\n")
                print(
                    json.dumps(
                        {
                            "tool": name,
                            "seconds": round(entry["seconds"], 2),
                            "error": entry.get("error"),
                            "events": entry["after"] - entry["before"],
                        }
                    ),
                    flush=True,
                )

        # Later paired rounds also retain the model-session binding and chat in the world.
        if args.round >= 2:
            jeff = Jeff(
                world,
                dispatch,
                describe,
                continuity=app.resident,
                bind_session=lambda thread, model: app.resident.bind(actor, thread, model),
            )
            app.jeff = jeff
            app.jeff_identity = actor
        else:
            jeff = Jeff(world, dispatch, describe)
        report["resident_bound"] = args.round >= 2
        report["account"] = jeff.status()
        if not report["account"]["signed_in"]:
            raise RuntimeError("Managed account unavailable")
        prompts = [
            COMMON
            + "\nRequest:\n"
            + (args.prompt_file.read_text() if args.prompt_file else REQUESTS[args.round])
        ]
        if args.round == 1:
            prompts.append(
                "I added a paragraph to OAS risks after your arrangement. Undo only the desk-arrangement decision you just made. Preserve that new paragraph, all subjects and appearances. Verify the result. If complete undo is not supported, be precise about what you can safely restore."
            )
        prompts.append(
            "Reflect briefly on the work you actually performed: which operations felt direct, where did you need to inspect internals or invent machinery, and what small change to the exposed structure would make the next similar request easier? Distinguish observed friction from speculation. Do not change anything in this reply."
        )
        report["before"] = native_snapshot(gateway)
        report["before_dom"] = browser.call(op="observe", selectors=["#board", "[data-view]"])
        for index, prompt in enumerate(prompts):
            if index == 1 and args.round == 1:
                obj = gateway.world.get("work-02")
                gateway.commit(
                    gateway.principal("human"),
                    [
                        {
                            "id": obj["id"],
                            "expected_revision": obj["revision"],
                            "facets": {
                                "core.text": {
                                    "text": obj["facets"]["core.text"]["text"]
                                    + "\n\nLATER HUMAN EDIT: keep this paragraph."
                                }
                            },
                        }
                    ],
                )
            first_tool = [None]
            start = time.monotonic()
            trace_start = len(traces)

            def emit(event):
                if event["type"] == "tool.started" and first_tool[0] is None:
                    first_tool[0] = time.monotonic() - start
                with (output / f"turn-{index + 1}-stream.jsonl").open(
                    "a", encoding="utf-8"
                ) as file:
                    file.write(json.dumps(event, ensure_ascii=False) + "\n")
                if event["type"] == "text.completed":
                    print(json.dumps({"jeff": event.get("text", "")}), flush=True)

            print(
                json.dumps({"turn": index + 1, "started": datetime.now(UTC).isoformat()}),
                flush=True,
            )
            if args.round >= 2:
                gateway.record_message(gateway.principal("human"), "user", prompt)
            turn = {"prompt": prompt}
            try:
                turn["reply"] = jeff.send(prompt, emit)
            except Exception as exc:
                turn["error"] = str(exc)
            if args.round >= 2 and "reply" in turn:
                gateway.record_message(actor, "assistant", turn["reply"])
            turn.update(
                seconds=time.monotonic() - start,
                first_tool_seconds=first_tool[0],
                outcome=getattr(jeff, "last_outcome", None),
                tool_calls=len(traces) - trace_start,
            )
            turn["native"] = native_snapshot(gateway)
            turn["dom"] = browser.call(op="observe", selectors=["#board", "[data-view]"])
            turn["application_doms"] = {}
            for obj in turn["native"]["items"]:
                view = obj["facets"].get("agora.application-view", {})
                if view.get("open") and view.get("package") not in (
                    "agora.notes",
                    "agora.documents",
                ):
                    try:
                        turn["application_doms"][obj["id"]] = browser.call(
                            op="observe",
                            view=obj["id"],
                            selectors=["[data-occurrence]", "[data-subject]", "[data-id]"],
                            text_limit=16000,
                        )
                    except Exception as exc:
                        turn["application_doms"][obj["id"]] = {"observation_error": str(exc)}
            browser.call(op="screenshot", path=str(output / f"turn-{index + 1}.png"))
            report["turns"].append(turn)
            (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        browser.call(op="interact", action="reload")
        report["after_reload_dom"] = browser.call(op="observe", selectors=["#board", "[data-view]"])
        report["replay"] = gateway.world.verify()
        report["thread_id"] = jeff._thread
    except Exception as exc:
        report["errors"].append({"type": type(exc).__name__, "message": str(exc)})
        raise
    finally:
        if jeff:
            jeff.close()
        if browser:
            browser.close()
        if server:
            server.shutdown()
            server.server_close()
        if app:
            app.bridge.close()
        guest.stop()
        (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(
            json.dumps(
                {
                    "finished": args.label,
                    "report": str(output / "report.json"),
                    "errors": report["errors"],
                }
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
