"""Synthetic forty-appearance desk plus independently arranged shared content."""

from model import Lab, key


def make_lab():
    initial = {}
    surfaces = {
        "desk": [f"oas-{i}" for i in range(8)] + ["mail"] + [f"other-{i}" for i in range(31)],
        "review": ["review-a", "review-b", "review-c"],
        "board": ["duplicate-a", "duplicate-b"],
    }
    for surface, members in surfaces.items():
        initial[key("surface", surface, "contract")] = "arrangement-v1:immutable-demo"
        initial[key("surface", surface, "members")] = members
        initial[key("surface", surface, "parent")] = None
        initial[key("surface", surface, "stack:normal")] = list(reversed(members))
        if surface == "review":
            initial[key("surface", surface, "reading_order")] = members
        for i, item in enumerate(members):
            subject = "subject-oas-0" if surface != "desk" else "subject-" + item
            initial[key("subject", subject, "tags")] = (
                ["oas"] if "oas" in subject or item == "mail" else []
            )
            initial[key("subject", subject, "text")] = "Original text"
            initial[key("subject", subject, "status")] = "todo"
            initial[key("occurrence", item, "binding")] = {
                "surface": surface,
                "subject": subject,
                "incarnation": 1,
            }
            initial[key("occurrence", item, "placement")] = {
                "mode": "free",
                "rect": [i * 13, i * 11, 240, 200],
            }
            initial[key("occurrence", item, "minimum")] = [220, 180]
            initial[key("occurrence", item, "stratum")] = "normal"
    initial[key("session", "window-a", "camera")] = [0, 0, 1]
    initial[key("session", "window-b", "camera")] = [0, 0, 1]
    lab = Lab(initial)
    lab.grant(
        "alex",
        set(surfaces)
        | {"subject:" + a[1] for a in initial if a[0] == "subject"}
        | {"session:window-a", "session:window-b"},
    )
    lab.observe(
        "human",
        {
            "surface": "desk",
            "active": True,
            "width": 1600,
            "height": 1200,
            "transform": [1, 0, 0, 1, 0, 0],
        },
    )
    return lab


def edit(lab, changes, request_id):
    builder = lab.builder()
    for address, value in changes.items():
        builder.effect(address, value)
    builder.describe("test-native-edit", "explicit", [], request=request_id)
    plan = builder.finish()
    return lab.commit(plan.digest, actor="alex", request_id=request_id)
