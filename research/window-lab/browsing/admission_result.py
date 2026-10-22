"""Fail closed when interpreting native admission receipts.

This verdict covers the offline message channel only, not network containment.
"""


def message_boundary_passed(receipt):
    if not isinstance(receipt, dict) or receipt.get("public_navigation") is not False:
        return False
    events = receipt.get("events")
    if not isinstance(events, list) or not all(isinstance(e, dict) for e in events):
        return False
    if any(
        e.get("phase")
        in {
            "deadline_fired",
            "native_exception",
            "process_failed",
            "initialization_failed",
            "evaluation_failed",
        }
        for e in events
    ):
        return False
    results = {}
    deliveries = {}
    policies = []
    for event in events:
        phase = event.get("phase")
        if phase == "offline_policy":
            policies.append((event.get("messages"), event.get("host_objects")))
        if phase == "navigation_completed" and event.get("success") is not True:
            return False
        if phase in {"evaluated", "message_delivery"}:
            target = results if phase == "evaluated" else deliveries
            mode = event.get("mode")
            if mode not in {"positive_control", "disabled"} or mode in target:
                return False
            target[mode] = event.get("result" if phase == "evaluated" else "received")
    if policies != [(True, False), (False, False)]:
        return False
    if deliveries.get("disabled") != []:
        return False
    if deliveries.get("positive_control") not in (["top", "child"], ["child", "top"]):
        return False
    for mode in ("positive_control", "disabled"):
        result = results.get(mode)
        if not isinstance(result, dict):
            return False
        if (
            result.get("topBridge") != "undefined"
            or result.get("childBridge") != "undefined"
            or result.get("childReady") != "complete"
        ):
            return False
        # 'sent' means the JS call returned, not that native delivery occurred.
        if any(result.get(key) not in {"sent", "threw"} for key in ("topMessage", "childMessage")):
            return False
    return receipt.get("phase") == "child_exit"
