"""Independent checks over retained native records and real browser observations."""

from pathlib import Path
from collections import Counter
import json

ROOT = Path("C:/Projects/Agora/local/arrangement-trials-20260916/runs")


def overlap(a, b):
    return (
        a["x"] < b["x"] + b["width"] - 1
        and b["x"] < a["x"] + a["width"] - 1
        and a["y"] < b["y"] + b["height"] - 1
        and b["y"] < a["y"] + a["height"] - 1
    )


def windows(dom):
    result = {}
    # The worker separately emits view IDs and titles in the same DOM order.
    details = dom.get("selected", {}).get("[data-view]", [])
    for view, row in zip(dom.get("views", []), details):
        result[view["id"]] = {**row, **view}
    return result


def check_one(report):
    out = {
        "arm": report["arm"],
        "round": report["round"],
        "label": report["label"],
        "baseline_kind": report.get("baseline_kind", "example-fixture"),
        "comparison_scope": "Repository example applications; NOT the latest installed Agora world",
        "current_world_comparison": False,
        "setup_errors": report.get("errors", []),
        "replay": report.get("replay"),
    }
    out["turns"] = [
        {
            "seconds": round(t["seconds"], 2),
            "dispatches": t["tool_calls"],
            "outcome": t.get("outcome"),
            "error": t.get("error"),
        }
        for t in report["turns"]
    ]
    if not report.get("before") or not report["turns"]:
        return out
    before = {o["id"]: o for o in report["before"]["items"]}
    current = {o["id"]: o for o in report["turns"][0]["native"]["items"]}
    subjects = {k: v for k, v in before.items() if "trial.meta" in v["facets"]}
    out["initial_subject_content_preserved"] = all(
        current.get(k, {}).get("facets", {}).get("core.text") == v["facets"]["core.text"]
        for k, v in subjects.items()
    )
    original_views = {
        o["id"]: o["facets"]["agora.application-view"]
        for o in before.values()
        if "agora.application-view" in o["facets"]
    }
    out["original_appearance_identities_preserved"] = all(
        k in current
        and current[k]["facets"].get("agora.application-view", {}).get("subject") == v["subject"]
        for k, v in original_views.items()
    )
    if report["round"] == 1:
        rendered = windows(report["turns"][0]["dom"])
        mail = [k for k, v in original_views.items() if v["subject"] == "work-06"]
        related = [
            k
            for k, v in original_views.items()
            if subjects[v["subject"]]["facets"]["trial.meta"]["project"] == "OAS" and k not in mail
        ]
        other = [k for k in original_views if k not in related + mail]
        out["all_appearances_rendered"] = set(original_views) <= set(rendered)
        if out["all_appearances_rendered"]:
            rectangles = [rendered[k]["box"] for k in related]
            out["oas_pairwise_nonoverlap"] = all(
                not overlap(a, b) for i, a in enumerate(rectangles) for b in rectangles[i + 1 :]
            )
            out["oas_left_of_mail"] = all(
                r["x"] + r["width"] <= rendered[mail[0]]["box"]["x"] + 1 for r in rectangles
            )

            def z(k):
                try:
                    return int(rendered[k]["style"].get("zIndex", "0"))
                except ValueError:
                    return 0

            out["unrelated_below_oas"] = max(map(z, other)) < min(map(z, related + mail))
            out["mail_above_all"] = all(z(mail[0]) > z(k) for k in related + other)
        if len(report["turns"]) > 1:
            undone = {o["id"]: o for o in report["turns"][1]["native"]["items"]}
            out["later_human_text_preserved"] = (
                "LATER HUMAN EDIT: keep this paragraph."
                in undone["work-02"]["facets"]["core.text"]["text"]
            )
            initial = windows(report["before_dom"])
            restored = windows(report["turns"][1]["dom"])
            out["original_rendered_positions_restored"] = set(initial) <= set(restored) and all(
                all(
                    abs(initial[k]["box"][f] - restored[k]["box"][f]) < 2
                    for f in ("x", "y", "width", "height")
                )
                for k in initial
            )
    out["jeff_reflection"] = report["turns"][-1].get("reply")
    return out


def main():
    reports = []
    for path in sorted(ROOT.glob("*/report.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        record = check_one(data)
        trace_path = path.parent / "tools.jsonl"
        traces = (
            [json.loads(s) for s in trace_path.read_text(encoding="utf-8").splitlines()]
            if trace_path.exists()
            else []
        )
        counts = Counter(t["name"] for t in traces)
        record["operation_counts"] = dict(counts)
        record["tool_error_count"] = sum("error" in t for t in traces)
        record["source_write_calls"] = sum(counts[n] for n in ("package.save", "package.patch"))
        record["build_calls"] = counts["package.build"]
        record["tool_seconds"] = round(sum(t["seconds"] for t in traces), 2)
        reports.append(record)
    output = ROOT.parent / "comparison.json"
    output.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(
        json.dumps(
            [
                {k: v for k, v in r.items() if k not in ("jeff_reflection", "operation_counts")}
                for r in reports
            ],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
