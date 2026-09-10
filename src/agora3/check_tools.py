"""Explicit build and bounded checks in one disposable guest session."""

import time
import uuid

from agora3.guest import GuestError
from agora3.world import Refusal, encoded

SPEC = {
    "name": "package.check",
    "description": (
        "Build saved Python source and exercise 1-10 named action cases in one fresh candidate VM "
        "session. Each case sees a fresh native snapshot and validates proposed changes against a "
        "separate disposable native copy; proposed changes are never applied live or chained "
        "between cases. Cases share guest filesystem/process state during this call only. "
        "Optional expect_result checks exact JSON equality; expect_error checks a nonempty error "
        "substring. Stops at first unexpected failure, retains build/check receipts, "
        "never installs. "
        "Returns exact install_args only when all requested checks pass. Browser interaction still "
        "requires a separate real-browser check."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "expected_revision": {"type": "integer", "minimum": 1},
            "cases": {
                "type": "array",
                "minItems": 1,
                "maxItems": 10,
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "minLength": 1, "maxLength": 120},
                        "action": {"type": "string"},
                        "args": {"type": "object"},
                        "expect_result": {},
                        "expect_error": {"type": "string", "minLength": 1, "maxLength": 500},
                    },
                    "required": ["action", "args"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["id", "expected_revision", "cases"],
        "additionalProperties": False,
    },
}


def check_package(gateway, actor, *, id, expected_revision, cases):
    package = gateway.packages.get(id)
    if package["revision"] != expected_revision:
        raise Refusal("Source revision changed; read it before checking.")
    source = package["facets"]["agora.package"]
    if source["manifest"]["runtime"] != "python-1":
        raise Refusal("package.check action cases require a python-1 package.")
    for case in cases:
        if "expect_result" in case and "expect_error" in case:
            raise Refusal("A case cannot expect both a result and an error.")
        if case["action"] not in source["manifest"].get("actions", {}):
            raise Refusal(f"Action is not exported: {case['action']}")
    started = time.monotonic()
    results = []
    with gateway.yard.session():
        built = gateway.packages.build(actor, id=id, expected_revision=expected_revision)
        receipt = gateway.packages.receipt(built["build"])
        for index, case in enumerate(cases):
            stamp = time.monotonic()
            row = {"name": case.get("name", str(index + 1)), "action": case["action"]}
            try:
                result = gateway.packages.invoke(
                    actor,
                    package=id,
                    revision=receipt["base_installation_revision"],
                    action=case["action"],
                    args=case["args"],
                    candidate=built["build"],
                )
                row["result"] = result["result"]
                row["proposed_changes"] = result["proposed_changes"]
                row["passed"] = "expect_error" not in case and (
                    "expect_result" not in case
                    or encoded(row["result"]) == encoded(case["expect_result"])
                )
                if not row["passed"]:
                    row["diagnostic"] = "Expected result/error did not match the observed result."
            except (Refusal, GuestError) as exc:
                row["error"] = str(exc)
                row["passed"] = "expect_error" in case and case["expect_error"] in str(exc)
            row["seconds"] = time.monotonic() - stamp
            results.append(row)
            if not row["passed"]:
                break
    gateway.check_authority(actor)
    passed = len(results) == len(cases) and all(r["passed"] for r in results)
    data = {
        "package": id,
        "build": built["build"],
        "source_revision": expected_revision,
        "passed": passed,
        "requested_cases": len(cases),
        "completed_cases": len(results),
        "cases": results,
        "seconds": time.monotonic() - started,
        "application_native_writes": 0,
        "installed": False,
        "isolation": "One fresh candidate VM per check call; guest state shared across cases; "
        "separate disposable native copy per case. Build/check receipts retained live.",
    }
    check_id = "agora.check." + uuid.uuid4().hex
    gateway.commit(
        actor,
        [{"id": check_id, "expected_revision": 0, "facets": {"agora.check": data}}],
        internal=True,
    )
    result = {k: v for k, v in data.items() if k != "cases"}
    result["check_receipt"] = check_id
    result["cases"] = [
        {k: v for k, v in row.items() if k != "proposed_changes"}
        | {"proposed_change_count": len(row.get("proposed_changes", []))}
        for row in results
    ]
    if passed:
        result["install_args"] = {
            "id": id,
            "build": built["build"],
            "expected_revision": receipt["base_installation_revision"],
        }
    return result
