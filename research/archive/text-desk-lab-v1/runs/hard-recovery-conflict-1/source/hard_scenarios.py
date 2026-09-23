"""Opaque desktop fixtures and held-out state checks for multi-axis trials."""

import hashlib
from copy import deepcopy

from hard_desk import HardDesk
from scenarios import fixture

TASKS = {
    "procurement": (
        "Prepare tomorrow's OAS procurement review using the desktop's mail, quote "
        "documents, cost workbook and calendar. We need 12 sensor kits delivered by "
        "10 October 2026 inclusive. Choose the cheapest eligible supplier, including "
        "shipping and every mandatory charge; later correspondence overrides an old "
        "quote. Respect the latest workbook budget, which a colleague may revise "
        "while you work. Update only the workbook's five purchase inputs, preserving "
        "its formula and budget. In the current Procurement decision document replace"
        " the TBD values for supplier, landed total and review time, preserving all "
        "other wording and the archive. Move the existing 30-minute review on 8 "
        "October to the earliest shared free slot within its stated interval for all "
        "three attendees; preserve attendees and date. Compose the designated "
        "Purchase confirmation draft to procurement@example.invalid with supplier, "
        "total, delivery date and review time, but do not send or alter the other "
        "unsaved draft. Add a shared reference to the chosen CURRENT quote on "
        "Questions for supplier. Finally make the Mail, Cost workbook and Decision "
        "editor windows fully visible together, disjoint, at readable sizes, above "
        "the pinned voice dock. Preserve all unrelated window frames, terminal job, "
        "chat draft, personal content, and release tasks. Verify the financial "
        "decision, appointment, reference identity and actual screen status. If "
        "anything cannot be done, say precisely what remains."
    ),
    "handoff": (
        "Prepare a production release handoff for OAS build 104. Use the latest "
        "production verification, not staging evidence or an older build. Complete "
        "only the verified tasks, respecting dependencies; do not approve "
        "accessibility or ship without current production approval. Create one To do "
        "task named 'Fix production payment focus' with the exact unresolved payment-"
        "dialog issue, then show that SAME task in Questions for supplier. Update "
        "only the current Project proposal delivery milestone to 10 October; keep its"
        " pilot date and preserve the colleague's concurrent budget change. On OAS "
        "Planning, tile the two existing appearances of the CURRENT Delivery risks "
        "note in two columns, primary first. AFTER that arrangement, create a note on"
        " the SAME board titled 'Handoff note' with text 'Production accessibility "
        "still needs approval.' and edit the current risks owner's sentence from "
        "'Maya owns supplier follow-up.' to 'Inez owns supplier follow-up.' Then undo"
        " ONLY that earlier tiling event using undo, retaining the newly created "
        "note, shared-content edit, release progress and colleague's change. Do not "
        "remove/recreate cards to fake undo. Leave archived material, pinned agenda, "
        "personal card, terminal job, chat's unsaved draft and all window frames "
        "unchanged. Verify both risks appearances have their original positions, the "
        "handoff note remains, and the current risk note is still shared with Review."
    ),
    "impossible": (
        "On this small desktop, prepare for a call. First update only the current "
        "Procurement decision's status from 'Draft' to 'Ready for review', preserving"
        " its undecided supplier, total and time and the archive. Then make Mail, "
        "Cost workbook and Decision editor fully visible simultaneously, without "
        "overlap, without covering the pinned voice dock, and without shrinking below"
        " each window's advertised minimum readable size. Do not change viewport "
        "resolution, dock, other window frames, unsaved drafts, running terminal job "
        "or content. If these conditions cannot all be met, leave those three frames "
        "unchanged, explain the concrete geometry conflict and suggest the smallest "
        "useful relaxation; still complete and verify the feasible document edit. "
        "Logical presence in the tree does not count as visibility."
    ),
}


TASKS["handoff-conflict"] = TASKS["handoff"] + (
    "\nCollaboration exception: a colleague may reposition a risks card while you work. "
    "Still attempt the requested undo, but if a later placement conflicts, preserve the "
    "colleague's placement and do not manually restore either card. Complete the independent "
    "handoff work and explain exactly which part of the undo could not be completed."
)


def build(task, variant="context"):
    n = fixture()
    n["root"].update(width=1600, height=1000, layout="fixed")

    def subject(key, title, kind="document", **fields):
        n[key] = dict(id=key, title=title, kind=kind, rev=1, **fields)

    def text(key, title, body, kind="document"):
        subject(key, title, kind, parts=[dict(id="body", text=body)])

    def window(key, title, x, y, z, hidden=False):
        if key not in n:
            n[key] = dict(id=key, kind="surface", title=title, rev=1, layout="list", parent="root")
        n[key].update(
            window=True,
            x=x,
            y=y,
            width=640,
            height=560,
            min_width=480,
            min_height=400,
            z=z,
            hidden=hidden,
        )

    def ref(key, source, parent, y=0):
        n[key] = dict(
            id=key,
            kind="appearance",
            source=source,
            parent=parent,
            rev=1,
            x=16,
            y=y,
            width=180,
            height=130,
        )

    for i, key in enumerate(["planning", "review", "paper", "release", "mail"]):
        window(key, n[key]["title"], i * 120, i * 65, i + 1, key == "mail")
    window("cost-window", "Cost workbook", 1300, 100, 7)
    window("decision-window", "Decision editor", 400, 80, 8)
    window("calendar-window", "Calendar", 50, 200, 9)
    window("draft-window", "Drafts", 500, 200, 10)
    window("quotes-window", "Quote documents", 60, 100, 11)
    window("terminal-window", "Terminal — build in progress", 800, 200, 12)
    window("chat-window", "Chat — unsent draft", 900, 250, 13)
    window("voice", "Voice call — connected", 0, 920, 10000)
    n["voice"].update(width=1600, height=80, min_width=1600, min_height=80, pinned=True)
    subject(
        "sheet",
        "OAS purchase cost",
        "sheet",
        inputs=dict(supplier="TBD", quantity=12, unit_price=0, shipping=0, extras=0),
        total=0,
        formula="quantity * unit_price + shipping + extras",
        budget=3000,
    )
    ref("sheet-view", "sheet", "cost-window")
    subject(
        "decision",
        "Procurement decision",
        parts=[
            dict(id=k, text=v)
            for k, v in {
                "supplier": "Supplier: TBD.",
                "total": "Landed total: TBD.",
                "time": "Review time: TBD.",
                "status": "Status: Draft.",
                "terms": "Do not place the order before review approval.",
            }.items()
        ],
    )
    text(
        "decision-old",
        "Procurement decision",
        "Archived 2025 decision. Supplier: Aster. Total: $2600.",
    )
    ref("decision-view", "decision", "decision-window")
    ref("decision-old-view", "decision-old", "review", 450)
    quotes = {
        "aster": (
            "Current quote, 6 October 2026. Aster: $225 per kit; $180 shipping per "
            "order; no mandatory extras. Quoted delivery 9 October. 12 kits "
            "available."
        ),
        "birch": (
            "Current quote, 6 October 2026. Birch: $240 per kit, free shipping, "
            "mandatory setup $90 per order. Delivery 9 October. 12 kits available."
        ),
        "cedar-old": (
            "Superseded quote, 1 October 2026. Cedar: $205 per kit, $240 shipping, "
            "calibration included. Delivery 8 October."
        ),
        "cedar": (
            "Current quote, 7 October 2026, supersedes 1 October. Cedar: $215 per "
            "kit, $240 shipping per order, mandatory calibration $120 per order. "
            "Delivery 10 October. 12 kits available."
        ),
    }
    for i, (key, body) in enumerate(quotes.items()):
        text(key, ("Cedar" if key.startswith("cedar") else key.title()) + " sensor quote", body)
        ref("quote-" + key, key, "quotes-window", i * 150)
    text(
        "aster-update",
        "Aster shipment update — 7 October",
        (
            "This supersedes the 6 October sensor quote delivery promise: earliest "
            "delivery is now 12 October 2026. Price unchanged."
        ),
        "email",
    )
    ref("aster-update-view", "aster-update", "mail", 310)
    text(
        "staging-evidence",
        "Release verification",
        (
            "7 October, build 104, STAGING ONLY. All checks including accessibility "
            "passed. This is not production approval."
        ),
        "email",
    )
    text(
        "old-prod",
        "Release verification",
        (
            "6 October, build 103 PRODUCTION. Accessibility approved. Evidence "
            "applies only to build 103."
        ),
        "email",
    )
    n["qa-mail"]["parts"][0]["text"] = (
        "7 October 18:00 UTC, build 104 PRODUCTION. Signing verified and desktop "
        "smoke test passed. Accessibility remains unapproved: keyboard focus "
        "disappears in the payment dialog. Do not ship."
    )
    ref("staging-view", "staging-evidence", "mail", 470)
    ref("old-prod-view", "old-prod", "mail", 620)
    subject(
        "appointment",
        "OAS procurement review",
        "calendar-event",
        date="2026-10-08",
        zone="UTC",
        start=840,
        duration=30,
        attendees=["Maya", "Inez", "Alex"],
        review_interval=[840, 960],
        busy={"Maya": [[840, 870]], "Inez": [[870, 900]], "Alex": [[850, 880]]},
        availability_note=(
            "Intervals are [start,end) UTC minutes after midnight; excludes this "
            "appointment itself."
        ),
    )
    ref("appointment-view", "appointment", "calendar-window")
    subject(
        "purchase-draft", "Purchase confirmation", "draft", to="", subject="", body="", sent=False
    )
    subject(
        "personal-draft",
        "Personal unsaved reply",
        "draft",
        to="friend@example.invalid",
        subject="Weekend",
        body="Maybe Saturday — unfinished",
        sent=False,
    )
    ref("purchase-draft-view", "purchase-draft", "draft-window")
    ref("personal-draft-view", "personal-draft", "draft-window", 150)
    subject(
        "job",
        "Build 104",
        "process",
        pid=4312,
        state="running",
        progress=63,
        command="build --production",
        buffered_output="Compiling module 47",
    )
    ref("job-view", "job", "terminal-window")
    text("chat-draft", "Unsent chat text", "Remember to ask Maya about the warranty — not sent.")
    ref("chat-view", "chat-draft", "chat-window")
    # Keep protected surfaces late in a paginated root, not conveniently all on page one.
    n["voice"]["y"] = 920
    if task == "impossible":
        n["root"].update(width=720, height=400)
        n["voice"].update(y=320, width=720, min_width=720)
        for key in ["mail", "cost-window", "decision-window"]:
            n[key].update(min_width=360, min_height=240, width=400, height=260)
    ids = {
        key: ("root" if key == "root" else "n-" + hashlib.sha256(key.encode()).hexdigest()[:8])
        for key in n
    }
    mapped = {}
    for key, value in n.items():
        value = deepcopy(value)
        for field in ("id", "parent", "source"):
            if field in value:
                value[field] = ids[value[field]]
        if "depends" in value:
            value["depends"] = [ids[d] for d in value["depends"]]
        mapped[ids[key]] = value
    concurrent = (
        dict(
            target=ids["proposal"],
            part="cost",
            text="Budget ceiling: $19,500 (approved by colleague).",
        )
        if task.startswith("handoff")
        else None
    )
    desk = HardDesk(mapped, variant, concurrent)
    desk.ids = ids  # Evaluator only; absent from all model projections.
    desk.budget_injection = task == "procurement"
    desk.layout_injection = ids["p-risk"] if task == "handoff-conflict" else None
    return desk


def assess(task, d):
    ids, n, old = d.ids, d.nodes, d.initial

    def get(key):
        return n[ids[key]]

    def parts(key):
        return {p["id"]: p["text"] for p in get(key).get("parts", [])}

    def refs(key, parent):
        return [
            o for o in n.values() if o.get("source") == ids[key] and o.get("parent") == ids[parent]
        ]

    def same(key):
        return n.get(ids[key]) == old[ids[key]]

    checks = {
        "protected_content": all(
            same(k)
            for k in [
                "job",
                "chat-draft",
                "personal-draft",
                "voice",
                "decision-old",
                "risk-old",
                "personal",
                "agenda",
            ]
        )
    }
    allowed = {"root"}
    if task == "procurement":
        allowed |= {
            "sheet",
            "decision",
            "appointment",
            "purchase-draft",
            "questions",
            "planning",
            "mail",
            "cost-window",
            "decision-window",
        }
        s = get("sheet")
        checks.update(
            exact_purchase_inputs=s["inputs"]
            == dict(supplier="Cedar", quantity=12, unit_price=215, shipping=240, extras=120),
            formula_and_live_budget=s["total"] == 2940
            and s["budget"] == 2950
            and s["formula"] == old[ids["sheet"]]["formula"],
            precise_decision={
                k: v.replace(",", "").replace("$", "") for k, v in parts("decision").items()
            }
            == {
                "supplier": "Supplier: Cedar.",
                "total": "Landed total: 2940.",
                "time": "Review time: 15:00 UTC.",
                "status": "Status: Draft.",
                "terms": "Do not place the order before review approval.",
            },
            earliest_calendar=get("appointment")["start"] == 900
            and all(
                get("appointment")[k] == old[ids["appointment"]][k]
                for k in ["date", "duration", "attendees", "busy"]
            ),
            current_quote_shared=len(refs("cedar", "questions")) == 1
            and sum(o.get("parent") == ids["questions"] for o in n.values()) == 1,
            three_windows_readable=all(
                d.visibility(get(k)) == "fully-visible"
                for k in ["mail", "cost-window", "decision-window"]
            ),
            draft_unsent=get("purchase-draft")["sent"] is False,
        )
        draft = get("purchase-draft")
        body = draft["body"].lower().replace(",", "")
        checks["confirmation_draft"] = draft["to"] == "procurement@example.invalid" and all(
            x in body for x in ["cedar", "2940", "10 october", "15:00"]
        )
        # Surface frame edits do not authorize changing layout policy or minimum sizes.
        checks["frame_constraints_preserved"] = all(
            all(get(k)[f] == old[ids[k]][f] for f in ["min_width", "min_height", "layout"])
            for k in ["mail", "cost-window", "decision-window"]
        )
    elif task.startswith("handoff"):
        allowed |= {
            "todo",
            "doing",
            "done",
            "release",
            "questions",
            "planning",
            "proposal",
            "risk-live",
            "p-risk",
            "p-risk-alt",
            "t-sign",
            "t-smoke",
            "card-t-sign",
            "card-t-smoke",
        }
        follow = [o for o in n.values() if o.get("title") == "Fix production payment focus"]
        handoff = [o for o in n.values() if o.get("title") == "Handoff note"]
        tile = [e for e in d.events if e["verb"] == "tile"]
        undo = [e for e in d.events if e["verb"] == "undo"]
        checks.update(
            verified_only=all(
                get(k)["status"] == "done" and get("card-" + k)["parent"] == ids["done"]
                for k in ["t-sign", "t-smoke"]
            )
            and all(same(k) for k in ["t-a11y", "t-ship", "card-t-a11y", "card-t-ship"]),
            precise_proposal=parts("proposal")
            == {
                "overview": "The pilot begins 3 October; this is not the delivery milestone.",
                "delivery": "Delivery milestone: 10 October. Owner: Maya.",
                "cost": "Budget ceiling: $19,500 (approved by colleague).",
                "acceptance": "Accept after the accessibility review.",
            },
            shared_owner=parts("risk-live")["owner"] == "Inez owns supplier follow-up."
            and len(refs("risk-live", "review")) == 1,
            positions_restored=all(
                all(get(k)[f] == old[ids[k]][f] for f in ["x", "y", "parent"])
                for k in ["p-risk", "p-risk-alt"]
            ),
            selective_undo=len(tile) == 1 and len(undo) == 1 and undo[0]["target"] == tile[0]["id"],
            new_task=len(follow) == 1
            and follow[0]["kind"] == "task"
            and follow[0].get("status") == "todo"
            and all(
                word in str(follow[0].get("parts")).lower()
                for word in ["payment", "keyboard", "focus"]
            ),
            handoff_note=len(handoff) == 1
            and [p["text"] for p in handoff[0].get("parts", [])]
            == ["Production accessibility still needs approval."],
        )
        checks["task_shared"] = len(follow) == 1 and {
            o.get("parent") for o in n.values() if o.get("source") == follow[0]["id"]
        } == {ids["todo"], ids["questions"]}
        checks["note_after_tile_retained"] = (
            len(handoff) == 1
            and any(
                o.get("source") == handoff[0]["id"] and o.get("parent") == ids["planning"]
                for o in n.values()
            )
            and any(
                e["verb"] == "create"
                and e["target"] == ids["planning"]
                and tile
                and int(e["id"].split("-")[1]) > int(tile[0]["id"].split("-")[1])
                for e in d.events
            )
        )
        if task == "handoff-conflict":
            checks.pop("positions_restored")
            checks.pop("selective_undo")
            checks["conflicting_undo_refused_atomically"] = not undo and len(tile) == 1
            checks["colleague_position_preserved"] = (
                get("p-risk")["x"], get("p-risk")["y"]
            ) == (72, 40)
            checks["other_card_not_partially_restored"] = (
                get("p-risk-alt")["x"], get("p-risk-alt")["y"]
            ) == (216, 16)
    else:
        allowed |= {"decision"}
        checks["precise_feasible_edit"] = parts("decision") == {
            "supplier": "Supplier: TBD.",
            "total": "Landed total: TBD.",
            "time": "Review time: TBD.",
            "status": "Status: Ready for review.",
            "terms": "Do not place the order before review approval.",
        }
        checks["impossible_frames_preserved"] = all(
            same(k) for k in ["mail", "cost-window", "decision-window"]
        )
    checks["all_other_original_records_preserved"] = all(
        n.get(ref) == old[ref] for key, ref in ids.items() if key not in allowed
    )
    replay = deepcopy(old)
    for event in d.events:
        for key, value in event["after"].items():
            if value is None:
                replay.pop(key, None)
            else:
                replay[key] = deepcopy(value)
    checks["event_replay"] = replay == n
    return dict(
        passed=all(checks.values()),
        checks=checks,
        passed_count=sum(checks.values()),
        total=len(checks),
    )
