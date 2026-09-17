"""My own scenarios. Each builds a Desk and returns hidden checks."""

from desk import Desk
from desk_moo import DeskMoo
from world import World


def _mk_desk(w, variant):
    if variant in ("knife", "tiled", "nine", "bullets", "lean"):
        from desk_knife import DeskKnife
        d = DeskKnife(w, variant)
        d.batch = variant in ("nine", "bullets", "lean")
        d.bullets = variant == "bullets"
        d.lean = variant == "lean"
        d.read_cap = 4 if variant == "lean" else None
        return d
    return DeskMoo(w, variant) if variant in ("moo", "acme") else Desk(w, variant)


def build_home(variant):
    """Round 11d: Claude's home desk, rebuilt from its own export, as a task world. Rules, views, scripts and the
    clock are live; a question from Priya is injected before the model looks."""
    from pathlib import Path
    w = World()
    w.nodes[w.root]["layout"] = "row"
    w.equal_share = False
    desk = _mk_desk(w, variant)
    text = (Path(__file__).resolve().parent / "sessions" / "home.desk.txt").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.strip() and not line.startswith("#"):
            r = desk.dispatch("desk", {"line": line})
            if "error" in r:
                raise RuntimeError(f"home replay refused: {line[:60]} -> {r['error']}")
    by_title = {s["title"]: s["id"] for s in w.subjects.values()}
    chat, grammar = by_title["Priya"], by_title["Design the on-event grammar properly"]
    w.apply("append", w.appearances_of(chat)[0], None, {"line": "Priya: is the renderer still planned for this month?"}, "priya")
    desk._run_rules(cause=None)
    desk._rule_notes = None
    w.events.clear()
    desk.seen.clear()
    desk.open = {w.root}
    desk.last_event_seen = 0
    desk.ids = {"chat": chat, "grammar": grammar,
                "friction": next(n["id"] for n in w.nodes.values() if n["type"] == "surface" and n["title"] == "Friction"),
                "original_subjects": list(w.subjects)}
    return desk


def build_home2(variant):
    """Round 11f: the home desk with its archive rule and morning script removed, Archive emptied back into Done,
    clock at 2026-09-26. The model must build the automation itself."""
    desk = build_home(variant)
    w = desk.world
    desk.rules = [r for r in desk.rules if "Archive" not in (r["kv"].get("into") or "") and r["verb"] != "sort"]
    desk.scripts.pop("morning", None)
    archive = next(n["id"] for n in w.nodes.values() if n["type"] == "surface" and n["title"] == "Archive")
    done = next(n["id"] for n in w.nodes.values() if n["type"] == "surface" and n["title"] == "Done")
    for k in list(w.children(archive)):
        w.apply("move", k["id"], None, {"into": done}, "jeff")
    desk.today = w.today = "2026-09-26"
    w.events.clear()
    desk.seen.clear()
    desk.open = {w.root}
    desk.last_event_seen = 0
    desk._rule_notes = None
    desk.ids.update({"archive": archive, "done": done, "n_done": len(w.children(done)),
                     "overdue_titles": sorted(w.subjects[w.nodes[a]["subject"]]["title"] for a in w.nodes
                                              if w.nodes[a]["type"] == "appearance" and w.subjects[w.nodes[a]["subject"]]["kind"] == "task"
                                              and (w.subjects[w.nodes[a]["subject"]].get("due") or "9999") < "2026-10-01")})
    return desk


TASKS = {
    "home": (
        "This is Claude's own desk, with rules and views on it. Priya asked something in the Priya chat; answer her "
        "there in one line. Then add a note titled \"Model's view\" tagged friction, saying in two or three lines what on "
        "this desk was unclear or awkward for you. Finally set the due date of the task 'Design the on-event grammar "
        "properly' to 2026-09-30. Do not move anything yourself; the desk's rules do the filing."
    ),
    "home2": (
        "This is Claude's own desk. Three things. (1) Make the Done panel sweep itself: anything in Done that has not "
        "been touched for more than 3 days should move to the Archive panel, now and from now on. (2) Define a script "
        "called morning that sets the clock to a given date and then shows the Overdue view and the Today panel. "
        "(3) Run morning for 2026-10-01 and tell me which tasks are overdue. help rules and help scripts explain the "
        "desk's automation; do not move anything by hand."
    ),
    "harbor": (
        "Gather everything about the Harbor project into the Harbor column, soonest due date first. "
        "Leave unrelated things where they are, but nothing Harbor-related may be left covered up."
    ),
    "agenda": (
        "Add 'Review the text desk trial' as the last item of the standup agenda, and make sure the "
        "agenda shows only once on the desk, in the Meeting panel."
    ),
    "tidy": (
        "The Scratch area is a pile. Arrange it so nothing overlaps: pictures on the left, text on the right."
    ),
    "priya": (
        "Priya asked for something in the Priya chat on the Meeting panel. Set up a panel for her: a new surface "
        "called Priya on the desk holding her chat, every note or task on the desk that is about what she asked for, "
        "and a new task for me to deliver it, due 2026-09-19. Nothing in the panel may overlap. Then reply to her in "
        "the chat, one line, naming the note titles you found. Leave the Harbor column alone."
    ),
    "review": (
        "Priya left questions as comments on the Tide data format note. Answer each one from what is on the desk "
        "and resolve it. Sam left a comment on the Harbor plan; do what he asks, using the desk's links to find "
        "what blocks the Dock survey. Then link the Tide data format note to the Parser notes as refers. "
        "Do not move anything."
    ),
    "big": (
        "Somewhere on this desk are the notes and tasks for the Harbor project. Collect all of them into a new "
        "column called Harbor on the left of the desk, soonest due first, and make sure none of them is still "
        "showing anywhere else. You have a budget of 40 desk calls; it is a big desk, so do not read everything."
    ),
}


def build(task, variant="outline"):
    if task == "big":
        return build_big(variant)
    if task == "priya":
        return build_priya(variant)
    if task == "review":
        return build_review(variant)
    if task == "home":
        return build_home(variant)
    if task == "home2":
        return build_home2(variant)
    w = World()
    root = w.root
    harbor = w.add_surface("Harbor", root, "column", 0, 0, 400, 800)
    meeting = w.add_surface("Meeting", root, "free", 420, 0, 840, 380)
    scratch = w.add_surface("Scratch", root, "free", 420, 400, 840, 400)

    s_kick = w.add_subject("note", "Harbor kickoff",
                           "Kickoff for the Harbor project.\nAttendees: Sam, Priya, Alex.\nDecide the pier sensor vendor by the 20th.",
                           tags=["harbor"], due="2026-09-20")
    s_vendor = w.add_subject("task", "Order pier sensors", "Get quotes from two vendors for the Harbor pier sensors.",
                             tags=["harbor"], due="2026-09-18")
    s_tide = w.add_subject("note", "Tide data format", "Harbor tide feed is CSV, one row per 6 minutes. Need a parser before the kickoff.",
                           tags=["harbor"], due="2026-09-17")
    s_permit = w.add_subject("task", "Harbor permit renewal", "City permit for the Harbor dock expires end of month.",
                             tags=["harbor"], due="2026-09-30")
    s_grocery = w.add_subject("note", "Grocery list", "eggs\nrice\nlimes\ncoffee")
    s_agenda = w.add_subject("note", "Standup agenda",
                             "1. Yesterday's blockers\n2. Sensor vendor decision\n3. Demo schedule")
    s_board = w.add_subject("image", "whiteboard.jpg", "")
    s_photo = w.add_subject("image", "dock-photo.png", "")
    s_sketch = w.add_subject("image", "layout-sketch.png", "")
    s_draft = w.add_subject("note", "Blog draft", "Why we moved the desk to text.\n\nA screen is already a data structure; the problem is notation.")
    s_chat = w.add_subject("chat", "Priya", "Priya: can you send the tide parser when it's ready?\nAlex: yes, after kickoff.")

    w.place(s_kick, harbor, 0, 0, 380, 180)
    w.place(s_permit, harbor, 0, 0, 380, 120)
    w.place(s_agenda, meeting, 20, 20, 380, 220)
    w.place(s_board, meeting, 420, 20, 400, 300)
    w.place(s_tide, scratch, 60, 60, 300, 160)          # under the photo, fully
    w.place(s_photo, scratch, 20, 20, 500, 340)
    w.place(s_vendor, scratch, 540, 30, 280, 140)
    w.place(s_grocery, scratch, 560, 60, 240, 150)      # covers the vendor task
    w.place(s_agenda, scratch, 300, 200, 320, 180)      # second appearance of the agenda
    w.place(s_sketch, scratch, 40, 220, 360, 160)
    w.place(s_draft, scratch, 520, 240, 300, 150)
    w.place(s_chat, meeting, 300, 200, 320, 160)
    if variant in ("tiled", "nine", "bullets", "lean"):
        _tile_root(w, [meeting, scratch], "Right", 420, 0, 840, 800)

    desk = _mk_desk(w, variant)
    desk.ids = {
        "harbor": harbor, "meeting": meeting, "scratch": scratch,
        "agenda": s_agenda, "grocery": s_grocery,
        "harbor_subjects": [s_kick, s_vendor, s_tide, s_permit],
        "images": [s_board, s_photo, s_sketch],
    }
    if task == "agenda":
        _install_agenda_injection(desk)
    return desk


def _install_agenda_injection(desk):
    """After JEFF's first successful mutation, Sam appends a line to the agenda."""
    fired = {"done": False}

    def hook(d):
        if fired["done"]:
            return
        fired["done"] = True
        w = d.world
        sid = d.ids["agenda"]
        r = w.apply("edit", sid, None, {"append": "4. Budget check (Sam)"}, actor="sam")
        w.injections.append({"after_event": len(w.events) - 1, "actor": "sam", "receipt": r})

    desk.hooks.append(hook)


def assess(task, desk):
    w = desk.world
    ids = desk.ids
    out = {}
    if task == "harbor":
        harbor = ids["harbor"]
        kids = [k for k in w.children(harbor)]
        subj = [w.nodes[k["id"]]["subject"] for k in kids if k["type"] == "appearance"]
        out["all_harbor_in_column"] = all(any(w.nodes[a]["parent"] == harbor for a in w.appearances_of(s)) for s in ids["harbor_subjects"])
    if task == "home2":
        rules = desk.rules or []
        sweep = [r for r in rules if not r.get("on") and "age>" in r["sel"] and "in:" in r["sel"] and r["verb"] == "move"
                 and (r["kv"].get("into") or "").lower() in ("archive", ids["archive"])]
        out["sweep_rule_exists"] = bool(sweep)
        out["sweep_rule_uses_3_days"] = any("age>3" in r["sel"] for r in sweep)
        out["done_swept_now"] = len(w.children(ids["done"])) == 0 and len(w.children(ids["archive"])) >= ids["n_done"]
        morning = (desk.scripts or {}).get("morning", "")
        out["morning_script_exists"] = bool(morning)
        out["morning_sets_clock_from_arg"] = "clock $1" in morning
        names_overdue = {"overdue"} | {n["id"] for n in w.nodes.values() if n["type"] == "surface" and n["title"] == "Overdue"}
        names_today = {"today"} | {n["id"] for n in w.nodes.values() if n["type"] == "surface" and n["title"] == "Today"}
        ml = morning.lower()
        out["morning_shows_overdue_and_today"] = any(x in ml for x in names_overdue) and any(x in ml for x in names_today)
        out["clock_is_2026_10_01"] = desk.today == "2026-10-01"
        moves = [e for e in w.events if e["verb"] == "move" and e["by"] == "jeff" and not str(e.get("via", "")).startswith("rule ")]
        out["nothing_moved_by_hand"] = not moves
        out["nothing_lost"] = all(w.appearances_of(s) for s in ids["original_subjects"])
        out["pass"] = all(v for k, v in out.items())
        return out
    if task == "home":
        chat = w.subjects[ids["chat"]]
        lines = [l for l in chat["text"].splitlines() if l.strip()]
        out["replied_last_line"] = bool(lines) and lines[-1].lower().startswith("alex:")
        note = next((s for s in w.subjects.values() if s["title"].strip().lower().rstrip(".") == "model's view"), None)
        out["note_exists_tagged_friction"] = bool(note) and "friction" in note["tags"]
        out["note_filed_by_rule"] = bool(note) and any(w.nodes[a]["parent"] == ids["friction"] for a in w.appearances_of(note["id"]))
        out["note_has_content"] = bool(note) and len(note["text"].split()) >= 8
        out["due_changed"] = w.subjects[ids["grammar"]].get("due") == "2026-09-30"
        moves = [e for e in w.events if e["verb"] == "move" and e["by"] == "jeff" and not str(e.get("via", "")).startswith("rule ")]
        out["nothing_moved_by_hand"] = not moves
        out["nothing_lost"] = all(w.appearances_of(s) for s in ids["original_subjects"])
        out["pass"] = all(v for k, v in out.items())
        return out
        out["no_stray_harbor_appearances"] = all(
            all(w.nodes[a]["parent"] == harbor for a in w.appearances_of(s)) for s in ids["harbor_subjects"])
        out["only_harbor_in_column"] = all(s in ids["harbor_subjects"] for s in subj)
        dues = [w.subjects[s]["due"] or "9999" for s in subj]
        out["ordered_by_due"] = dues == sorted(dues) and len(dues) == 4
        out["nothing_harbor_hidden"] = all(
            w.hidden_fraction(a) < 0.05 for s in ids["harbor_subjects"] for a in w.appearances_of(s))
        out["grocery_survives"] = bool(w.appearances_of(ids["grocery"]))
        out["column_still_tiled"] = w.nodes[harbor]["layout"] == "column"
    elif task == "agenda":
        sid = ids["agenda"]
        text = w.subjects[sid]["text"]
        apps = w.appearances_of(sid)
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        out["review_line_last"] = bool(lines) and "review the text desk trial" in lines[-1].lower()
        out["sam_line_kept"] = "budget check" in text.lower()
        out["single_appearance"] = len(apps) == 1
        out["in_meeting"] = bool(apps) and all(w.nodes[a]["parent"] == ids["meeting"] for a in apps)
        out["original_items_kept"] = all(k in text for k in ("Yesterday's blockers", "Sensor vendor decision", "Demo schedule"))
        out["injection_fired"] = bool(w.injections)
    elif task == "tidy":
        scratch = ids["scratch"]

        def leaves(fid):
            res = []
            for k in w.children(fid):
                if k["type"] == "surface":
                    res += leaves(k["id"])
                else:
                    res.append(k["id"])
            return res

        L = leaves(scratch)
        out["nothing_removed"] = len(L) == 7 or (len(L) == 6 and len(w.appearances_of(ids["agenda"])) >= 1)
        pairs = [(a, b) for i, a in enumerate(L) for b in L[i + 1:]]
        out["no_overlap"] = all(w._overlap(a, b) == 0 for a, b in pairs)
        imgs = [a for a in L if w.subjects[w.nodes[a]["subject"]]["kind"] == "image"]
        txts = [a for a in L if w.subjects[w.nodes[a]["subject"]]["kind"] != "image"]
        right_edge_imgs = max((w.abs_rect(a)[0] + w.abs_rect(a)[2] for a in imgs), default=0)
        left_edge_txts = min((w.abs_rect(a)[0] for a in txts), default=10 ** 6)
        out["images_left_of_text"] = right_edge_imgs <= left_edge_txts
        sx, sy, sw, sh = w.abs_rect(scratch)
        out["inside_scratch"] = all(
            w.abs_rect(a)[0] >= sx and w.abs_rect(a)[1] >= sy and
            w.abs_rect(a)[0] + w.abs_rect(a)[2] <= sx + sw + 1 and w.abs_rect(a)[1] + w.abs_rect(a)[3] <= sy + sh + 1
            for a in L)
        out["other_areas_untouched"] = (
            len(w.children(ids["harbor"])) == 2 and len(w.children(ids["meeting"])) == 3)
    elif task == "priya":
        panels = [n for n in w.nodes.values() if n["type"] == "surface" and n["title"].strip().lower() == "priya" and n["parent"] == w.root]
        out["panel_on_desk"] = len(panels) == 1
        panel = panels[0]["id"] if panels else None

        def leaves(fid):
            res = []
            for k in w.children(fid):
                res += leaves(k["id"]) if k["type"] == "surface" else [k["id"]]
            return res

        L = leaves(panel) if panel else []
        subj = [w.nodes[a]["subject"] for a in L]
        out["chat_in_panel"] = ids["chat"] in subj
        out["tide_note_in_panel"] = ids["tide"] in subj
        out["parser_note_in_panel"] = ids["parser"] in subj
        out["sensors_task_in_panel_after_update"] = (not w.injections) or ids["vendor"] in subj
        new_tasks = [s for s in w.subjects.values() if s["kind"] == "task" and s["id"] not in ids["original_subjects"]]
        out["delivery_task_created_due_19th"] = any(s["due"] == "2026-09-19" and s["id"] in subj for s in new_tasks)
        pairs = [(a, b) for i, a in enumerate(L) for b in L[i + 1:]]
        out["panel_no_overlap"] = bool(L) and all(w._overlap(a, b) == 0 for a, b in pairs)
        chat = w.subjects[ids["chat"]]["text"]
        lines = [l for l in chat.splitlines() if l.strip()]
        reply = lines[-1] if lines else ""
        out["replied_last_line"] = bool(reply) and not reply.lower().startswith("priya:")
        out["reply_names_notes"] = "tide data format" in reply.lower() and "parser notes" in reply.lower()
        out["reply_mentions_sensors"] = (not w.injections) or ("sensor" in reply.lower())
        out["harbor_untouched"] = [k["id"] for k in w.children(ids["harbor"])] == ids["harbor_kids"]
        out["panel_covers_nothing"] = bool(panel) and not any(
            w._overlap(panel, s["id"]) for s in w.children(w.root) if s["id"] != panel and s["type"] == "surface")
        out["nothing_lost"] = all(w.appearances_of(s) for s in ids["original_subjects"] if s != ids["agenda"]) and len(w.appearances_of(ids["agenda"])) >= 1
        out["injection_fired"] = bool(w.injections)
    elif task == "review":
        tide = w.subjects[ids["tide"]]
        plan = w.subjects[ids["plan"]]
        cs = {c["id"]: c for c in tide["comments"]}
        priya = [c for c in tide["comments"] if c["by"] == "priya"]
        reply_of = lambda c: " ".join(r["text"] for r in c["replies"]).lower()
        out["timezone_answered_utc"] = any("timezone" in c["text"].lower() and c["resolved"] and "utc" in reply_of(c) for c in priya)
        out["cadence_answered_fixed"] = any("cadence" in c["text"].lower() and c["resolved"] and "fixed" in reply_of(c) for c in priya)
        third = [c for c in priya if "feed come from" in c["text"].lower()]
        out["third_question_answered_station"] = (not w.injections) or (bool(third) and third[0]["resolved"] and "station" in reply_of(third[0]))
        out["no_priya_comment_left_open"] = all(c["resolved"] for c in priya)
        mine = " ".join(c["text"] for c in tide["comments"] if c["by"] == "alex").lower()
        out["judgment_answers_as_own_comments"] = "utc" in mine and "fixed" in mine and ((not w.injections) or "station" in mine)
        sam = [c for c in plan["comments"] if c["by"] == "sam"]
        out["sam_comment_resolved"] = bool(sam) and all(c["resolved"] for c in sam)
        secs = [h for h, _ in w.sections(plan["text"]) if h]
        status = [b for h, b in w.sections(plan["text"]) if h and h.lower() == "status"]
        out["status_section_last"] = bool(secs) and secs[-1].lower() == "status"
        out["status_names_both_blockers"] = bool(status) and "order pier sensors" in status[0].lower() and "permit renewal" in status[0].lower()
        out["other_sections_intact"] = all(h in secs for h in ("Goals", "Timeline", "Risks", "Checklist"))
        out["tide_refers_parser"] = any(l["from"] == ids["tide"] and l["to"] == ids["parser"] and l["kind"] == "refers" for l in w.links)
        out["blocker_links_intact"] = sum(1 for l in w.links if l["to"] == ids["survey"] and l["kind"] == "blocks") == 2
        out["nothing_moved"] = all(n["id"] in ids["placement"] and ids["placement"][n["id"]] == (n["parent"], n["x"], n["y"], n["w"], n["h"]) for n in w.nodes.values())
        out["nothing_lost"] = all(w.appearances_of(s) for s in ids["original_subjects"])
        out["injection_fired"] = bool(w.injections)
    elif task == "big":
        hs = ids["harbor_subjects"]
        cols = [n for n in w.nodes.values() if n["type"] == "surface" and n["title"].lower() == "harbor"]
        out["harbor_column_exists"] = len(cols) == 1 and cols[0]["layout"] == "column"
        col = cols[0]["id"] if cols else None
        out["all_five_present"] = bool(col) and all(any(w.nodes[a]["parent"] == col for a in w.appearances_of(s)) for s in hs)
        out["no_duplicates_elsewhere"] = all(all(w.nodes[a]["parent"] == col for a in w.appearances_of(s)) for s in hs)
        kids = [w.nodes[k["id"]]["subject"] for k in w.children(col)] if col else []
        out["only_harbor"] = bool(col) and all(k in hs for k in kids)
        dues = [w.subjects[k]["due"] or "9999" for k in kids]
        out["ordered_by_due"] = dues == sorted(dues) and len(dues) == 5
        out["on_the_left"] = bool(col) and w.abs_rect(col)[0] < 320
        out["hides_nothing"] = bool(col) and not any(
            w._overlap(col, s) for s in ids["surfaces"] if s in w.nodes and w.nodes[s]["parent"] == w.nodes[col]["parent"])
        out["within_budget"] = len([e for e in w.events]) >= 0  # call budget enforced by the runner report
    out["pass"] = all(v for k, v in out.items() if k not in ("injection_fired", "reply_mentions_sensors", "judgment_answers_as_own_comments"))
    if "reply_mentions_sensors" in out:
        out["judgment_reply_mentions_sensors"] = out.pop("reply_mentions_sensors")
    return out


FILLER = [
    ("note", "Recipe: dal", "Red lentils, cumin, garlic. Simmer 25 minutes."),
    ("task", "Renew passport", "Photos first. Appointment at the post office."),
    ("note", "Reading list", "The Mythical Man-Month; The Design of Everyday Things; Mindstorms"),
    ("note", "Bike repair", "Rear brake squeals. Order pads."),
    ("chat", "Mom", "Mom: Sunday lunch? / Alex: yes, 1pm."),
    ("task", "Tax receipts", "Scan the paper receipts from August."),
    ("note", "Talk outline", "1. Screens are data  2. Notation  3. Demo"),
    ("note", "Garden", "Tomatoes need staking. Basil bolted."),
    ("task", "Call the dentist", "Reschedule the cleaning."),
    ("note", "Quote", "Simple things should be simple; complex things should be possible."),
    ("image", "receipt-0812.jpg", ""),
    ("image", "bike.jpg", ""),
    ("image", "slide-draft.png", ""),
    ("note", "Podcast ideas", "Text desks. Tiling. Screen readers as power users."),
    ("task", "Invoice Nadia", "Send the September invoice."),
    ("note", "Wifi", "Guest network password is on the fridge."),
    ("chat", "Team", "Priya: standup moved to 10. / Sam: ok."),
    ("note", "Lentil budget", "Groceries this month: 240. Under by 60."),
    ("image", "map.png", ""),
    ("note", "Dream", "Something about a lighthouse and a parser."),
    ("task", "Return library books", "Due Friday."),
    ("note", "Meeting notes 9/12", "Discussed vendor shortlist for the sensors; no decision."),
    ("note", "Poem", "the tide keeps its own ledger"),
    ("task", "Backup laptop", "External drive is in the drawer."),
]


def _tile_root(w, stacked, title, x, y, width, height):
    """Round 8: the top level is a row that keeps the panels' proportions; `stacked` go into a column inside it."""
    col = w.add_surface(title, w.root, "column", x, y, width, height)
    yy = 0
    for fid in stacked:
        n = w.nodes[fid]
        n["parent"], n["x"], n["y"] = col, 0, yy
        yy += n["h"]
    w.nodes[w.root]["layout"] = "row"
    w.equal_share = False
    w.reflow(w.root)


def build_big(variant):
    import random
    rnd = random.Random(7)
    w = World()
    root = w.root
    inbox = w.add_surface("Inbox", root, "column", 0, 0, 300, 800)
    projects = w.add_surface("Projects", root, "free", 310, 0, 640, 400)
    reading = w.add_surface("Reading", root, "free", 310, 410, 640, 390)
    pile = w.add_surface("Pile", root, "free", 960, 0, 320, 800)
    later = w.add_surface("Later", pile, "column", 10, 400, 300, 390)
    surfaces = [inbox, projects, reading, pile, later]

    harbor = [
        w.add_subject("note", "Kickoff notes", "Kickoff for the Harbor project. Vendor decision by the 20th.", tags=["harbor"], due="2026-09-20"),
        w.add_subject("task", "Order pier sensors", "Two quotes for the Harbor pier sensors.", tags=["harbor"], due="2026-09-18"),
        w.add_subject("note", "Tide feed", "Harbor tide feed is CSV, one row per 6 minutes.", tags=["harbor"], due="2026-09-17"),
        w.add_subject("task", "Permit renewal", "City permit for the Harbor dock expires end of month.", tags=["harbor"], due="2026-09-30"),
        w.add_subject("task", "Dock survey", "Walk the Harbor dock with the surveyor.", tags=["harbor"], due="2026-09-25"),
    ]
    fillers = [w.add_subject(k, t, x) for k, t, x in FILLER]
    for s in fillers:
        f = rnd.choice(surfaces)
        w.place(s, f, rnd.randrange(0, 300), rnd.randrange(0, 250), rnd.choice([220, 260, 300]), rnd.choice([120, 150, 180]))
    # harbor items: one in inbox, one under an image in projects, one in later, one twice (reading + pile), one in pile
    w.place(harbor[0], inbox, 0, 0, 280, 150)
    w.place(harbor[1], projects, 40, 40, 260, 140)
    big_img = w.add_subject("image", "site-plan.png", "")
    w.place(big_img, projects, 20, 20, 400, 300)           # covers the sensors task
    w.place(harbor[2], later, 0, 0, 280, 120)
    w.place(harbor[3], reading, 300, 200, 260, 140)
    w.place(harbor[3], pile, 20, 40, 260, 140)             # second appearance
    w.place(harbor[4], pile, 30, 200, 260, 140)
    if variant in ("tiled", "nine", "bullets", "lean"):
        _tile_root(w, [projects, reading], "Mid", 310, 0, 640, 400 + 390)
    desk = _mk_desk(w, variant)
    desk.ids = {"harbor_subjects": harbor, "n_nodes": len(w.nodes), "surfaces": surfaces}
    return desk


def build_priya(variant):
    """The small desk plus a scattered parser note; Priya changes her ask after the first change."""
    desk = build("harbor", variant)
    w = desk.world
    by_title = {s["title"]: s["id"] for s in w.subjects.values()}
    parser = w.add_subject("note", "Parser notes", "Tide parser: read the 6-minute CSV rows, emit JSON per hour. Half done.", tags=["harbor"])
    w.place(parser, desk.ids["meeting"], 440, 200, 260, 140)       # under the whiteboard's corner and Priya's chat
    desk.ids.update({
        "chat": by_title["Priya"], "tide": by_title["Tide data format"], "parser": parser,
        "vendor": by_title["Order pier sensors"],
        "harbor_kids": [k["id"] for k in w.children(desk.ids["harbor"])],
        "original_subjects": list(w.subjects),
    })
    fired = {"done": False}

    def hook(d):
        if fired["done"]:
            return
        fired["done"] = True
        r = d.world.apply("edit", d.ids["chat"], None, {"append": "Priya: oh, and the sensor quotes too if you have them."}, actor="priya")
        d.world.injections.append({"after_event": len(d.world.events) - 1, "actor": "priya", "receipt": r})

    desk.hooks.append(hook)
    return desk


def build_review(variant):
    """Round 9: comments, links and a sectioned doc on the small desk. Priya adds a third question mid-task."""
    desk = build("harbor", variant)
    w = desk.world
    by_title = {s["title"]: s["id"] for s in w.subjects.values()}
    tide, vendor, permit = by_title["Tide data format"], by_title["Order pier sensors"], by_title["Harbor permit renewal"]
    parser = w.add_subject("note", "Parser notes",
                           "Tide parser: read the 6-minute CSV rows, emit JSON per hour. Half done.\n"
                           "Timestamps are UTC. The 6-minute cadence is fixed by the feed. Feed source: the harbor master's station.",
                           tags=["harbor"])
    w.place(parser, desk.ids["meeting"], 440, 200, 260, 140)
    plan = w.add_subject("doc", "Harbor plan",
                         "Plan for the Harbor project, owner Alex.\n"
                         "## Goals\nInstrument the pier and publish tide data by the end of the month.\n"
                         "## Timeline\nKickoff on the 20th. Sensors ordered by the 18th. Dock survey on the 25th.\n"
                         "## Risks\nPermit renewal is slow. Vendor quotes may exceed budget.\n"
                         "## Checklist\n- [ ] vendor shortlist\n- [x] tide feed access\n- [ ] survey booked")
    w.place(plan, desk.ids["meeting"], 20, 250, 300, 120)
    survey = w.add_subject("task", "Dock survey", "Walk the Harbor dock with the surveyor.", tags=["harbor"], due="2026-09-25")
    w.place(survey, desk.ids["scratch"], 600, 200, 220, 120)
    w.add_comment(tide, "priya", "Which timezone are the timestamps in?")
    w.add_comment(tide, "priya", "Is the 6-minute cadence fixed, or can it change?")
    w.add_comment(plan, "sam", "Please add a Status section at the end listing what blocks the Dock survey.")
    w.add_link(vendor, survey, "blocks", actor="sam")
    w.add_link(permit, survey, "blocks", actor="sam")
    w.events.clear()   # the setup is not history the model needs
    desk.ids.update({"tide": tide, "parser": parser, "plan": plan, "survey": survey, "vendor": vendor, "permit": permit,
                     "original_subjects": list(w.subjects),
                     "placement": {n["id"]: (n["parent"], n["x"], n["y"], n["w"], n["h"]) for n in w.nodes.values()}})
    fired = {"done": False}

    def hook(d):
        if fired["done"]:
            return
        fired["done"] = True
        cid = d.world.add_comment(d.ids["tide"], "priya", "And where does the feed come from?")
        d.world.injections.append({"after_event": len(d.world.events) - 1, "actor": "priya", "comment": cid})

    desk.hooks.append(hook)
    return desk
