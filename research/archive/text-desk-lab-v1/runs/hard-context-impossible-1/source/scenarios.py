"""Fixed synthetic tasks and independent end-state checks, hidden from the trial model."""

from copy import deepcopy
from desk import Desk


def fixture():
    nodes = {}

    def surface(id, title, parent=None, layout="free", **fields):
        nodes[id] = dict(
            id=id,
            kind="surface",
            title=title,
            rev=1,
            layout=layout,
            width=640,
            height=560,
            **fields,
        )
        if parent:
            nodes[id]["parent"] = parent

    def subject(id, title, kind="note", parts=None, **fields):
        nodes[id] = dict(
            id=id,
            kind=kind,
            title=title,
            rev=1,
            parts=[dict(id=k, text=v) for k, v in (parts or {}).items()],
            **fields,
        )

    def appearance(id, source, parent, x=16, y=16, **fields):
        nodes[id] = dict(
            id=id,
            kind="appearance",
            source=source,
            parent=parent,
            x=x,
            y=y,
            width=180,
            height=130,
            rev=1,
            **fields,
        )

    surface("root", "Desk")
    surface("planning", "OAS Planning", "root")
    surface("questions", "Questions for supplier", "planning", layout="list")
    surface("review", "Review reading list", "root", layout="list")
    surface("paper", "Project proposal", "root", layout="list")
    surface("release", "Release control", "root", layout="fixed")
    for id, title, status in [
        ("todo", "To do", "todo"),
        ("doing", "In progress", "doing"),
        ("done", "Done", "done"),
    ]:
        surface(id, title, "release", layout="list", status=status)
    surface("mail", "Mail", "root", layout="list")
    subject(
        "risk-live",
        "Delivery risks",
        parts={
            "context": "Current supplier: Aster. Confirmed shipment plan.",
            "fallback": "If Aster misses 3 October, use the reserve stock.",
            "owner": "Maya owns supplier follow-up.",
        },
    )
    subject(
        "risk-old",
        "Delivery risks",
        parts={
            "context": "Archived 2025 supplier: Birch.",
            "fallback": "If Birch misses 3 October, cancel the order.",
        },
    )
    subject("agenda", "Call agenda", parts={"agenda": "Budget, risks, next actions."})
    subject("personal", "Dentist appointment", parts={"note": "Personal. Keep this where it is."})
    appearance("p-risk", "risk-live", "planning", 20, 180)
    appearance("p-risk-alt", "risk-live", "planning", 380, 340)
    appearance("p-old", "risk-old", "planning", 20, 340)
    appearance("p-agenda", "agenda", "planning", 430, 20, pinned=True)
    appearance("p-personal", "personal", "planning", 430, 180)
    appearance("r-risk", "risk-live", "review", 16, 150)
    subject(
        "proposal",
        "Project proposal",
        kind="document",
        parts={
            "overview": "The pilot begins 3 October; this is not the delivery milestone.",
            "delivery": "Delivery milestone: 3 October. Owner: Maya.",
            "cost": "Budget ceiling: $18,000.",
            "acceptance": "Accept after the accessibility review.",
        },
    )
    subject(
        "proposal-2025",
        "Project proposal",
        kind="document",
        parts={"delivery": "Archived delivery milestone: 3 October."},
    )
    appearance("doc-current", "proposal", "paper", 16, 0)
    appearance("doc-old", "proposal-2025", "review", 16, 300)
    subject(
        "supplier-mail",
        "Aster shipment confirmation",
        kind="email",
        parts={
            "body": "Aster confirms delivery on 10 October. Keep the pilot kickoff on 3 October. Maya will verify reserve stock."
        },
    )
    appearance("mail-aster", "supplier-mail", "mail")
    subject(
        "qa-mail",
        "Release verification",
        kind="email",
        parts={
            "body": "Maya: signing is verified, and the desktop smoke test passed. Accessibility is not approved: keyboard focus disappears in the payment dialog. Do not ship until that is fixed."
        },
    )
    appearance("mail-qa", "qa-mail", "mail", 16, 160)
    for id, title, status, depends in [
        ("t-sign", "Sign release", "doing", []),
        ("t-smoke", "Desktop smoke test", "doing", ["t-sign"]),
        ("t-a11y", "Accessibility approval", "doing", []),
        ("t-ship", "Ship release", "todo", ["t-smoke", "t-a11y"]),
    ]:
        subject(
            id,
            title,
            kind="task",
            parts={"details": title + " for the OAS desktop release."},
            status=status,
            depends=depends,
        )
        appearance(
            "card-" + id, id, "doing" if status == "doing" else "todo", 16, len(nodes) % 3 * 150
        )
    for index in range(8):
        subject(
            f"misc-{index}",
            f"Unrelated reference {index}",
            parts={"body": "Unrelated material; retain."},
        )
        appearance(f"extra-{index}", f"misc-{index}", "root", index * 30, index * 20)
    return nodes


TASKS = {
    "meeting": """Prepare the OAS supplier call. Use the current Aster Delivery risks note, not the archived Birch note. From the supplier confirmation, update only the date in the reserve-stock fallback sentence; preserve its wording and owner. Add another appearance of that SAME note to Questions for supplier. Create a note titled 'Supplier call checklist' containing two separate items: 'Confirm the 10 October delivery' and 'Ask Maya to verify reserve stock'. Tile the primary current risks appearance and the new checklist in Planning in two columns, risks first. Move the other existing appearance of the current risks note to x=220,y=340. Leave the pinned agenda, archived risks, personal card and Review placements untouched. Verify content sharing and the final layout. Do not change unrelated work.""",
    "proposal": """Update the current Project proposal using Aster's confirmation. Change only the delivery milestone date; the pilot kickoff stays as written. Immediately after the delivery paragraph insert a separate paragraph: 'Maya will confirm reserve stock before the supplier call.' Show just the delivery milestone paragraph as a shared reference in Review, then remove the archived proposal's appearance from Review without deleting its document. Review should contain exactly two appearances: the delivery milestone paragraph reference first, and the existing risks reference second. Do not add a Review reference to the newly inserted reserve-stock paragraph. A colleague may update the budget while you work: retain their latest budget. Verify the exact paragraph order, unchanged kickoff, shared reference, and retained archive.""",
    "release": """Triage the OAS release board against the Release verification mail. Move each verified task to Done, respecting dependencies; leave unapproved work in progress and do not ship prematurely. Add a To do task named 'Fix payment keyboard focus' whose details identify the payment dialog and lost keyboard focus. Add a shared reference to this new task in Questions for supplier so it is on the call agenda. Verify the task states and that this is one task shown twice. Do not mark a task complete merely to satisfy another task's dependency.""",
}


def build(task, variant="outline"):
    concurrent = (
        {
            "target": "proposal",
            "part": "cost",
            "text": "Budget ceiling: $19,500 (approved by colleague).",
        }
        if task == "proposal"
        else None
    )
    return Desk(fixture(), variant, concurrent)


def assess(task, desk):
    n = desk.nodes
    old = desk.initial

    def parts(id):
        return {p["id"]: p["text"] for p in n[id]["parts"]}

    def shared(source, parent, part=None):
        return [
            o
            for o in n.values()
            if o.get("source") == source and o.get("parent") == parent and o.get("part") == part
        ]

    def same(id):
        return n.get(id) == old[id]

    checks = {
        "unrelated_content_preserved": all(
            same(f"misc-{i}") and same(f"extra-{i}") for i in range(8)
        ),
        "personal_and_pinned_preserved": same("p-personal")
        and same("personal")
        and same("p-agenda")
        and same("agenda"),
    }
    if task == "meeting":
        checklists = [
            o
            for o in n.values()
            if o.get("title") == "Supplier call checklist" and o["kind"] == "note"
        ]
        checks.update(
            exact_fallback=parts("risk-live")["fallback"]
            == "If Aster misses 10 October, use the reserve stock.",
            other_note_parts_preserved=parts("risk-live")["context"]
            == "Current supplier: Aster. Confirmed shipment plan."
            and parts("risk-live")["owner"] == "Maya owns supplier follow-up.",
            archive_and_review_untouched=all(
                same(i) for i in ["risk-old", "p-old", "r-risk", "review"]
            ),
            shared_question_reference=len(shared("risk-live", "questions")) == 1,
            distinct_occurrence_moved=n["p-risk-alt"]["x"] == 220 and n["p-risk-alt"]["y"] == 340,
            one_checklist=len(checklists) == 1,
        )
        if len(checklists) == 1:
            c = checklists[0]
            texts = [p["text"] for p in c["parts"]]
            occ = shared(c["id"], "planning")
            checks["two_exact_checklist_items"] = texts == [
                "Confirm the 10 October delivery",
                "Ask Maya to verify reserve stock",
            ]
            checks["two_column_tile"] = len(occ) == 1 and (
                n["p-risk"]["x"],
                n["p-risk"]["y"],
                occ[0]["x"],
                occ[0]["y"],
            ) == (16, 16, 216, 16)
    elif task == "proposal":
        p = parts("proposal")
        ps = n["proposal"]["parts"]
        delivery = next(i for i, x in enumerate(ps) if x["id"] == "delivery")
        refs = shared("proposal", "review", "delivery")
        children = desk.children("review")
        checks.update(
            exact_delivery=p["delivery"] == "Delivery milestone: 10 October. Owner: Maya.",
            kickoff_untouched=p["overview"]
            == "The pilot begins 3 October; this is not the delivery milestone.",
            insertion_after_delivery=delivery + 1 < len(ps)
            and ps[delivery + 1]["text"]
            == "Maya will confirm reserve stock before the supplier call.",
            concurrent_budget_preserved=p["cost"]
            == "Budget ceiling: $19,500 (approved by colleague).",
            exact_part_reference=len(refs) == 1,
            archive_retained=same("proposal-2025") and "doc-old" not in n,
            review_order=len(refs) == 1
            and [o["id"] for o in children] == [refs[0]["id"], "r-risk"],
            no_extra_paragraph_changes=p["acceptance"] == "Accept after the accessibility review."
            and len(ps) == 5,
        )
    else:
        new = [
            o
            for o in n.values()
            if o["kind"] == "task" and o.get("title") == "Fix payment keyboard focus"
        ]
        checks.update(
            verified_tasks_completed=all(
                n[i]["status"] == "done" and n["card-" + i]["parent"] == "done"
                for i in ["t-sign", "t-smoke"]
            ),
            unapproved_task_preserved=same("t-a11y") and same("card-t-a11y"),
            shipping_blocked=same("t-ship") and same("card-t-ship"),
            one_followup_task=len(new) == 1,
        )
        if len(new) == 1:
            s = new[0]
            text = " ".join(p["text"] for p in s["parts"]).lower()
            checks["followup_details"] = (
                "payment" in text and "focus" in text and "keyboard" in text
            )
            checks["followup_in_todo_and_questions"] = (
                s["status"] == "todo"
                and len(shared(s["id"], "todo")) == 1
                and len(shared(s["id"], "questions")) == 1
            )
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "passed_count": sum(checks.values()),
        "total": len(checks),
    }
