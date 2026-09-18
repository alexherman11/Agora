"""Guest counterexample and repair check for occurrence IDs across both insertions."""

import argparse
import json
from copy import deepcopy

from occurrence_candidate import board_candidate
from occurrence_trial import ROOT, Gateway, Guest, Yard


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume-after-harness-error", action="store_true")
    args = parser.parse_args()
    out = ROOT / "occurrence-candidate-2"
    report_path = out / "collision-verification.json"
    prior = None
    if args.resume_after_harness_error:
        prior = json.loads(report_path.read_text())
        assert prior["counterexample"]["result"]["ok"]
        assert prior["error"] == "Packages.get() got an unexpected keyword argument 'id'"
        report_path = out / "collision-verification-2.json"
    if report_path.exists():
        raise RuntimeError("Do not overwrite the retained counterexample.")
    report = {}
    g = Gateway(out / "world")
    guest = Guest(out / "world/machine.json")
    assert guest._config()["vm_id"] == "d0b8ac83-1217-4834-bfeb-703801221a45"
    actor = g.principal("human")

    def fixture(oid, identity):
        g.commit(
            actor,
            [
                {
                    "id": oid,
                    "expected_revision": 0,
                    "facets": {
                        "notes.board": {
                            "version": 1,
                            "grid": 24,
                            "snap": False,
                            "items": [
                                {
                                    "id": identity,
                                    "note_id": "trial-note-a",
                                    "x": 0,
                                    "y": 0,
                                    "width": 280,
                                    "height": 240,
                                    "color": "yellow",
                                }
                            ],
                        }
                    },
                }
            ],
        )

    def create(oid, identity):
        return g.dispatch(
            actor,
            "action.invoke",
            {
                "package": "studio.boards",
                "revision": g.packages.installation("studio.boards")["revision"],
                "action": "create_note",
                "args": {
                    "board_id": oid,
                    "board_revision": 1,
                    "note_id": identity,
                    "title": "Collision probe",
                    "text": "Synthetic",
                    "x": 10,
                    "y": 10,
                    "color": "blue",
                },
            },
        )

    try:
        guest.start()
        Yard._ready(guest)
        if prior:
            report["counterexample"] = prior["counterexample"]
            report["resumed_from"] = "collision-verification.json"
        else:
            fixture("collision-before", "collision-note-before")
            report["counterexample"] = create("collision-before", "collision-note-before")
        assert report["counterexample"]["result"]["ok"]
        before = g.world.get("collision-before")["facets"]["notes.board"]["items"]
        assert len(before) == 2 and before[0]["id"] == before[1]["id"]

        source = board_candidate(
            json.loads((ROOT / "installed/studio.boards/source.json").read_text())
        )
        (out / "studio.boards-final.json").write_text(
            json.dumps(source, indent=2), encoding="utf-8"
        )
        package = g.packages.get("studio.boards")
        report["saved"] = g.dispatch(
            actor,
            "package.save",
            {
                "id": "studio.boards",
                "expected_revision": package["revision"],
                "files": source["files"],
                "manifest": source["manifest"],
            },
        )
        build = g.dispatch(
            actor,
            "package.build",
            {"id": "studio.boards", "expected_revision": package["revision"] + 1},
        )
        report["installed"] = g.dispatch(actor, "package.install", build["install_args"])
        fixture("collision-after", "collision-note-after")
        before = deepcopy(g.world.get("collision-after"))
        report["guarded"] = create("collision-after", "collision-note-after")
        assert report["guarded"]["result"]["ok"] is False
        assert report["guarded"]["transaction"] is None
        assert g.world.get("collision-after") == before
        assert not any(
            o["id"] == "collision-note-after" for o in g.world.query(limit=1000)["items"]
        )
        report["ordinary_creation"] = create("collision-after", "ordinary-note-after")
        assert report["ordinary_creation"]["result"]["ok"]
        report["replay"] = g.world.verify()
        assert report["replay"]["ok"]
        report["passed"] = True
    except Exception as exc:
        report["error"] = str(exc)
        raise
    finally:
        guest.stop()
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({"passed": report.get("passed"), "error": report.get("error")}))


if __name__ == "__main__":
    main()
