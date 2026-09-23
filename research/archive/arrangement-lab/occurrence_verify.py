"""Finish adversarial and UI checks in the retained, isolated occurrence candidate."""

import json
import socket
import sys
import threading
from copy import deepcopy
from pathlib import Path

from occurrence_trial import ROOT, Browser, Gateway, Guest, Yard, server_module


def main():
    out = ROOT / "occurrence-candidate-2"
    prior = json.loads((out / "report.json").read_text())
    world = out / "world"
    report = {"checks": {}, "probes": []}
    report_path = out / "verification.json"
    if report_path.exists():
        raise RuntimeError("Preserve prior verification evidence; choose a new output name.")
    guest = Guest(world / "machine.json")
    assert guest._config()["vm_id"] == "d0b8ac83-1217-4834-bfeb-703801221a45"
    server = app = browser = None
    try:
        guest.start()
        Yard._ready(guest)
        g = Gateway(world)
        review = deepcopy(g.world.get("trial-review"))
        note = deepcopy(g.world.get("trial-note-a"))
        board = g.world.get("trial-planning")
        other = next(
            p
            for p in board["facets"]["notes.board"]["items"]
            if p["note_id"] == "trial-note-a" and p["id"] != "trial-note-a"
        )

        def invoke(action, args, accept):
            before = deepcopy(g.world.get("trial-planning"))
            args = {"board_id": before["id"], "board_revision": before["revision"], **args}
            result = g.dispatch(
                g.principal("human"),
                "action.invoke",
                {"package": "studio.boards", "revision": 2, "action": action, "args": args},
            )
            report["probes"].append({"action": action, "args": args, "result": result})
            assert result["result"]["ok"] is accept, result
            if not accept:
                assert result["transaction"] is None
                assert g.world.get("trial-planning") == before
            assert g.world.get("trial-note-a") == note
            assert g.world.get("trial-review") == review

        invoke("layout", {"board_revision": 1, "patches": [{"id": other["id"], "x": 999}]}, False)
        invoke(
            "layout", {"patches": [{"id": other["id"], "x": 999}, {"id": "missing", "x": 7}]}, False
        )
        invoke(
            "add_note",
            {"note_id": note["id"], "occurrence_id": other["id"], "x": 0, "y": 0, "color": "blue"},
            False,
        )
        invoke("remove_note", {"note_id": note["id"]}, False)
        report["checks"]["stale_unknown_member_duplicate_id_ambiguous_removal_atomic_refusals"] = (
            True
        )
        invoke("remove_note", {"note_id": note["id"], "occurrence_id": other["id"]}, True)
        assert len(g.world.get("trial-planning")["facets"]["notes.board"]["items"]) == 2
        report["checks"]["explicit_removal_retains_original_note_and_review"] = True

        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        server, app = server_module.serve(world, port)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        g = app.gateway
        assert app.connect_guest()["connected"]
        browser = Browser(out)
        browser.call(op="open", url=f"http://127.0.0.1:{port}/#" + g.keep["operator"])
        browser.call(op="interact", action="resize", width=1900, height=1200)
        first = prior["views"][0]
        browser.call(op="interact", action="click", selector=f'[data-tab="{first}"]')
        browser.call(op="interact", view=first, action="click", name="Add existing")
        browser.call(
            op="interact",
            view=first,
            action="select",
            selector='select[aria-label="Existing note"]',
            value=note["id"],
        )
        browser.call(op="interact", view=first, action="click", name="Add to board", wait=1500)
        items = g.world.get("trial-planning")["facets"]["notes.board"]["items"]
        new = next(p for p in items if p["note_id"] == note["id"] and p["id"] != note["id"])
        assert new["id"] != other["id"] and g.world.get(note["id"]) == note
        report["checks"]["human_add_existing_creates_distinct_occurrence"] = True
        report["visible_views"] = {}
        for view in prior["views"]:
            browser.call(op="interact", action="click", selector=f'[data-tab="{view}"]')
            observed = browser.call(
                op="observe", view=view, selectors=['[data-note="trial-note-a"]'], wait=1200
            )
            assert observed["viewport"]["width"] > 0
            assert len(observed["selected"]['[data-note="trial-note-a"]']) == 2
            report["visible_views"][view] = observed
            browser.call(op="screenshot", path=str(out / (view + ".png")))
        report["checks"]["both_tabs_render_two_occurrences_when_visible"] = True

        browser.call(op="interact", action="click", selector=f'[data-tab="{first}"]')
        one = '[data-occurrence="trial-note-a"] .note-text'
        two = f'[data-occurrence="{new["id"]}"] .note-text'
        result = browser.call(
            op="sequence",
            view=first,
            steps=[
                {
                    "action": "fill",
                    "selector": one,
                    "value": "EDIT FROM FIRST OCCURRENCE",
                    "wait": 0,
                },
                {
                    "action": "fill",
                    "selector": two,
                    "value": "EDIT FROM SECOND OCCURRENCE",
                    "wait": 0,
                },
                {"action": "wait", "ms": 2800},
            ],
            selectors=[one, two, ".note-conflict"],
        )
        report["concurrent_edit"] = result
        assert result["failure"] is None
        values = {
            result["observation"]["selected"][selector][0]["value"] for selector in (one, two)
        }
        assert values == {"EDIT FROM FIRST OCCURRENCE", "EDIT FROM SECOND OCCURRENCE"}
        state = g.world.get(first)["facets"]["agora.application-view"]["state"]["board"]
        report["retained_drafts"] = state["drafts"]
        assert len(state["drafts"]) == 1 and set(state["drafts"]) <= {note["id"], new["id"]}
        browser.call(op="interact", action="reload", wait=2000)
        browser.call(op="interact", action="click", selector=f'[data-tab="{first}"]')
        observed = browser.call(op="observe", view=first, selectors=[one, two, ".note-conflict"])
        assert {observed["selected"][selector][0]["value"] for selector in (one, two)} == values
        report["restored_drafts"] = observed
        report["checks"]["concurrent_occurrence_edits_preserve_conflicting_draft_across_reload"] = (
            True
        )
        browser.call(op="screenshot", path=str(out / "draft-conflict.png"))
        assert g.world.get("trial-review") == review
        report["replay"] = g.world.verify()
        assert report["replay"]["ok"]
        report["native_module_paths"] = {
            name: module.__file__
            for name, module in sys.modules.items()
            if name.startswith("agora3") and getattr(module, "__file__", None)
        }
        assert all(
            Path(p).is_relative_to(ROOT / "native/src")
            for p in report["native_module_paths"].values()
        )
    except Exception as exc:
        report["error"] = str(exc)
        raise
    finally:
        if browser:
            browser.close()
        if server:
            server.shutdown()
            server.server_close()
        if app:
            app.bridge.close()
        guest.stop()
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({"checks": report["checks"], "error": report.get("error")}))


if __name__ == "__main__":
    main()
