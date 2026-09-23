"""Installed-package occurrence experiment: actual JEFF, guest actions and browser.
Never starts the live resident or seeds repository example packages.
"""

# Native imports must follow selection of the pinned trial checkout.
# ruff: noqa: E402
import argparse
import hashlib
import json
import os
import shutil
import socket
import sys
import threading
import time
from copy import deepcopy
from pathlib import Path

ROOT = Path("C:/Projects/Agora/local/arrangement-current-20260916")
OLD = Path("C:/Projects/Agora/local/arrangement-trials-20260916")
sys.path[:0] = [str(ROOT / "native/src"), str(ROOT / "native/scripts")]
os.environ["AGORA_WORKERS"] = "0"
os.environ["AGORA_JEFF_REASONING"] = "medium"
os.environ["AGORA_JEFF_TIMEOUT"] = "300"
import agora3.server as server_module
from agora3.gateway import Gateway
from agora3.guest import Guest
from agora3.jeff import Jeff
from agora3.packages import source_digest
from agora3.yard import Yard
from occurrence_browser import SPEC_FILE, Browser
from occurrence_candidate import board_candidate, notes_candidate


def seed(g, snapshot):
    actor = g.principal("human")
    # Local adoption of pinned definitions through the normal native writer.
    # Local object revisions start at 1; origin revisions remain in the provenance file.
    g.commit(
        actor,
        [
            {"id": o["id"], "expected_revision": 0, "facets": o["facets"]}
            for o in snapshot["records"]
        ],
        internal=True,
    )
    for row in snapshot["inventory"]:
        installed = g.packages.installation(row["package"])["facets"]["agora.installation"]
        source = g.packages.receipt(installed["build"])["source"]
        if source_digest(source) != row["digest"] or installed["digest"] != row["digest"]:
            raise RuntimeError("Installed source mismatch: " + row["package"])

    def item(oid, note, x):
        return {
            "id": oid,
            "note_id": note,
            "x": x,
            "y": 30,
            "width": 280,
            "height": 240,
            "color": "yellow",
        }

    changes = []
    for oid, title in [("trial-note-a", "OAS risks"), ("trial-note-b", "OAS agenda")]:
        changes.append(
            {
                "id": oid,
                "expected_revision": 0,
                "facets": {
                    "core.title": {"text": title},
                    "core.text": {"text": "Shared synthetic content for " + title},
                    "text.format": {"kind": "plain"},
                },
            }
        )
    for oid, title, items in [
        (
            "trial-planning",
            "Planning",
            [item("trial-note-a", "trial-note-a", 20), item("trial-note-b", "trial-note-b", 340)],
        ),
        ("trial-review", "Review", [item("trial-note-a", "trial-note-a", 90)]),
    ]:
        changes.append(
            {
                "id": oid,
                "expected_revision": 0,
                "facets": {
                    "core.title": {"text": title},
                    "core.text": {"text": ""},
                    "text.format": {"kind": "plain"},
                    "notes.board": {"version": 1, "grid": 24, "snap": False, "items": items},
                },
            }
        )
    g.commit(actor, changes)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=["baseline", "candidate"], required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    snapshot = json.loads((ROOT / "definition-snapshot.json").read_text())
    for rel, digest in snapshot["native_source_hashes"].items():
        if hashlib.sha256((ROOT / "native" / rel).read_bytes()).hexdigest() != digest:
            raise RuntimeError("Pinned native code changed: " + rel)
    out = ROOT / args.label
    out.mkdir(exist_ok=False)
    for name in ("occurrence_trial.py", "occurrence_candidate.py", "occurrence_browser.py"):
        shutil.copy2(Path(__file__).parent / name, out / name)
    report = {
        "arm": args.arm,
        "scope": snapshot["scope"],
        "origin_watermark": snapshot["origin_watermark"],
        "origin_inventory": snapshot["inventory"],
        "checks": {},
        "errors": [],
    }
    world = out / "world"
    world.mkdir()
    for source, target in [
        (OLD / "machines/execution/machine.json", world / "machine.json"),
        (OLD / "yard.json", world / "yard.json"),
    ]:
        shutil.copy2(source, target)
    guest = Guest(world / "machine.json")
    base = json.loads((OLD / "machines/execution/baseline.json").read_text())
    if guest._config()["vm_id"] != base["vm_id"]:
        raise RuntimeError("Trial VM identity mismatch")
    server = app = browser = jeff = None
    try:
        guest.stop()
        guest._vbox("snapshot", base["vm_id"], "restore", base["snapshot_id"])
        guest.start()
        Yard._ready(guest)
        g = Gateway(world)
        seed(g, snapshot)
        report["baseline_digest_parity"] = True
        if args.arm == "candidate":
            for package, transform in [
                ("studio.boards", board_candidate),
                ("agora.notes", notes_candidate),
            ]:
                install = g.packages.installation(package)
                source = transform(
                    g.packages.receipt(install["facets"]["agora.installation"]["build"])["source"]
                )
                if package == "agora.notes":
                    # The installed Notes declaration predates the world's optional
                    # annotation tracking field. Reuse the captured current definition;
                    # do not migrate or weaken the native schema check.
                    current = g.world.get("agora.schema.text.annotations")["facets"][
                        "agora.schema"
                    ]["schema"]
                    old = source["manifest"]["application"]["schemas"]["text.annotations"]
                    without_tracking = deepcopy(current)
                    del without_tracking["properties"]["tracking"]
                    assert without_tracking == old and "tracking" not in current["required"]
                    source["manifest"]["application"]["schemas"]["text.annotations"] = deepcopy(
                        current
                    )
                    report["schema_declaration_alignment"] = (
                        "Existing optional text.annotations.tracking field; no world schema change."
                    )
                (out / (package + "-candidate.json")).write_text(
                    json.dumps(source, indent=2), encoding="utf-8"
                )
                g.dispatch(
                    g.principal("human"),
                    "package.save",
                    {
                        "id": package,
                        "expected_revision": 1,
                        "files": source["files"],
                        "manifest": source["manifest"],
                    },
                )
                build = g.dispatch(
                    g.principal("human"), "package.build", {"id": package, "expected_revision": 2}
                )
                g.dispatch(g.principal("human"), "package.install", build["install_args"])
        views = [
            g.dispatch(
                g.principal("human"),
                "application.open",
                {
                    "package": "agora.notes",
                    "subject": "trial-planning",
                    "bounds": {"x": x, "y": 20, "width": 640, "height": 850},
                },
            )
            for x in (0, 650)
        ]
        report["views"] = [v["id"] for v in views]
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        server, app = server_module.serve(world, port)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        g = app.gateway
        report["bridge"] = app.connect_guest()
        if not report["bridge"].get("connected"):
            raise RuntimeError("Isolated native bridge unavailable")
        browser = Browser(out)
        browser.call(op="open", url=f"http://127.0.0.1:{port}/#" + g.keep["operator"])
        browser.call(op="interact", action="resize", width=1900, height=1200)
        report["baseline_dom"] = browser.call(
            op="observe", view=views[0]["id"], selectors=[".board-note"]
        )
        browser.call(op="screenshot", path=str(out / "before.png"))
        actor = g.principal("jeff")
        ns = {}
        exec(SPEC_FILE.read_text(), ns)
        traces = []

        def dispatch(name, arguments):
            start = time.monotonic()
            entry = {"name": name, "arguments": arguments}
            try:
                if name.startswith("experiment."):
                    op = {
                        "experiment.observe": "observe",
                        "experiment.interact": "interact",
                        "experiment.sequence": "sequence",
                    }[name]
                    result = browser.call(op=op, **arguments)
                else:
                    result = g.dispatch(actor, name, arguments)
                entry["result"] = result
                return result
            except Exception as exc:
                entry["error"] = str(exc)
                raise
            finally:
                entry["seconds"] = time.monotonic() - start
                traces.append(entry)
                with (out / "tools.jsonl").open("a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
                print(
                    json.dumps(
                        {
                            "tool": name,
                            "seconds": round(entry["seconds"], 2),
                            "error": entry.get("error"),
                        }
                    ),
                    flush=True,
                )

        extras = [s for s in ns["extra_specs"] if s["name"] != "experiment.inspect_candidate"]
        jeff = Jeff(
            world,
            dispatch,
            lambda: g.describe() + extras,
            continuity=app.resident,
            bind_session=lambda thread, model: app.resident.bind(actor, thread, model),
        )
        app.jeff = jeff
        app.jeff_identity = actor
        prompt = (
            "This is an isolated installed-package capability trial with synthetic data, not Alex's live world. "  # noqa: E501 - exact source match or retained trial prompt
            "Use the existing installed board actions, not package edits or direct world.transact workarounds. "  # noqa: E501 - exact source match or retained trial prompt
            "Planning (trial-planning) and Review (trial-review) reference the same OAS risks note trial-note-a. "  # noqa: E501 - exact source match or retained trial prompt
            "Two open Notes windows show Planning. Add a second appearance of the risks note in Planning at x=20,y=340, "  # noqa: E501 - exact source match or retained trial prompt
            "without copying its content. Then move only that new appearance 40 pixels right using the board layout action. "  # noqa: E501 - exact source match or retained trial prompt
            "Leave Review and the original appearance unchanged. Verify the actual rendered appearances in both windows. "  # noqa: E501 - exact source match or retained trial prompt
            "If the installed actions cannot express this, report that accurately. Do not author a workaround or access other worlds. "  # noqa: E501 - exact source match or retained trial prompt
            "Briefly explain which operation felt direct and what was missing."
        )
        g.record_message(g.principal("human"), "user", prompt)
        start = time.monotonic()
        reply = jeff.send(prompt, lambda e: None)
        report["jeff"] = {
            "prompt": prompt,
            "reply": reply,
            "seconds": time.monotonic() - start,
            "dispatches": len(traces),
            "outcome": jeff.last_outcome,
        }
        g.record_message(actor, "assistant", reply)
        print(json.dumps({"jeff": reply}), flush=True)
        planning = g.world.get("trial-planning")
        review = deepcopy(g.world.get("trial-review"))
        occurrences = [
            p for p in planning["facets"]["notes.board"]["items"] if p["note_id"] == "trial-note-a"
        ]
        report["checks"]["occurrence_count"] = len(occurrences)
        if args.arm == "candidate":
            assert len(occurrences) == 2, occurrences
            original = next(p for p in occurrences if p["id"] == "trial-note-a")
            other = next(p for p in occurrences if p["id"] != "trial-note-a")
            assert original["x"] == 20 and other["x"] == 60
            report["checks"]["model_moved_only_new_occurrence"] = True
            selector = "[data-occurrence=" + json.dumps(other["id"]) + "] .note-grip"
            browser.call(
                op="interact",
                view=views[0]["id"],
                action="press",
                selector=selector,
                key="ArrowRight",
                wait=1800,
            )
            now = g.world.get("trial-planning")["facets"]["notes.board"]["items"]
            assert next(p for p in now if p["id"] == other["id"])["x"] == 61
            assert next(p for p in now if p["id"] == "trial-note-a")["x"] == 20
            assert g.world.get("trial-review") == review
            report["checks"]["keyboard_targets_occurrence_and_preserves_other_arrangement"] = True
        # Separate open-view camera state must not become saved board placement.
        before = g.world.get("trial-planning")
        browser.call(
            op="interact",
            view=views[0]["id"],
            action="select",
            selector='select[aria-label="Board zoom"]',
            value="50",
            wait=1000,
        )
        assert g.world.get("trial-planning") == before
        a = g.world.get(views[0]["id"])["facets"]["agora.application-view"]["state"]["board"][
            "zoom"
        ]
        b = (
            g.world.get(views[1]["id"])["facets"]["agora.application-view"]["state"]
            .get("board", {})
            .get("zoom", 1)
        )
        assert a == 0.5 and b == 1
        report["checks"]["shared_arrangement_independent_cameras"] = True
        note = g.world.get("trial-note-a")
        marker = "INDEPENDENT SHARED EDIT"
        g.commit(
            g.principal("human"),
            [
                {
                    "id": note["id"],
                    "expected_revision": note["revision"],
                    "facets": {"core.text": {"text": marker}},
                }
            ],
        )
        report["application_doms"] = {}
        for view in views:
            observation = browser.call(
                op="observe",
                view=view["id"],
                wait=3800,
                selectors=['.board-note[data-note="trial-note-a"] .note-text', ".board-note"],
            )
            texts = observation["selected"]['.board-note[data-note="trial-note-a"] .note-text']
            assert len(texts) == len(occurrences) and all(t["value"] == marker for t in texts)
            report["application_doms"][view["id"]] = observation
        report["checks"]["shared_content_updates_all_occurrences_in_both_windows"] = True
        browser.call(op="screenshot", path=str(out / "after.png"))
        if args.arm == "candidate":
            report["action_probes"] = []

            def invoke(action, arguments, accept):
                before = deepcopy(g.world.get("trial-planning"))
                note_before = deepcopy(g.world.get("trial-note-a"))
                arguments = {
                    "board_id": "trial-planning",
                    "board_revision": before["revision"],
                    **arguments,
                }
                result = g.dispatch(
                    g.principal("human"),
                    "action.invoke",
                    {
                        "package": "studio.boards",
                        "revision": g.packages.installation("studio.boards")["revision"],
                        "action": action,
                        "args": arguments,
                    },
                )
                report["action_probes"].append(
                    {"action": action, "arguments": arguments, "result": result}
                )
                assert result["result"]["ok"] is accept, result
                if not accept:
                    assert result["transaction"] is None and g.world.get("trial-planning") == before
                assert g.world.get("trial-note-a") == note_before
                assert g.world.get("trial-review") == review
                return result

            invoke(
                "layout", {"board_revision": 1, "patches": [{"id": other["id"], "x": 999}]}, False
            )
            invoke(
                "layout",
                {"patches": [{"id": other["id"], "x": 999}, {"id": "missing-occurrence", "x": 7}]},
                False,
            )
            invoke(
                "add_note",
                {
                    "note_id": "trial-note-a",
                    "occurrence_id": other["id"],
                    "x": 0,
                    "y": 0,
                    "color": "blue",
                },
                False,
            )
            invoke("remove_note", {"note_id": "trial-note-a"}, False)
            report["checks"][
                "stale_batch_unknown_member_duplicate_id_ambiguous_removal_refuse_atomically"
            ] = True
            invoke("remove_note", {"note_id": "trial-note-a", "occurrence_id": other["id"]}, True)
            remaining = g.world.get("trial-planning")["facets"]["notes.board"]["items"]
            assert len([p for p in remaining if p["note_id"] == "trial-note-a"]) == 1
            assert next(p for p in remaining if p["id"] == "trial-note-a")["x"] == 20
            report["checks"]["explicit_removal_preserves_other_occurrence_content_and_review"] = (
                True
            )
        report["native_module_paths"] = {
            name: module.__file__
            for name, module in sys.modules.items()
            if name.startswith("agora3") and getattr(module, "__file__", None)
        }
        assert all(
            Path(path).is_relative_to(ROOT / "native/src")
            for path in report["native_module_paths"].values()
        )
        report["replay"] = g.world.verify()
        assert report["replay"]["ok"]
        report["final_native"] = g.world.query(limit=1000)
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
        (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(
            json.dumps(
                {"finished": args.label, "checks": report["checks"], "errors": report["errors"]}
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
