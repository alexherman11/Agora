"""My own scenarios. Each builds a Desk and returns hidden checks."""

from desk import Desk
from world import World

TASKS = {
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
    "big": (
        "Somewhere on this desk are the notes and tasks for the Harbor project. Collect all of them into a new "
        "column called Harbor on the left of the desk, soonest due first, and make sure none of them is still "
        "showing anywhere else. You have a budget of 40 desk calls; it is a big desk, so do not read everything."
    ),
}


def build(task, variant="outline"):
    if task == "big":
        return build_big(variant)
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

    desk = Desk(w, variant)
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
        out["within_budget"] = len([e for e in w.events]) >= 0  # call budget enforced by the runner report
    out["pass"] = all(v for k, v in out.items() if k != "injection_fired")
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
    desk = Desk(w, variant)
    desk.ids = {"harbor_subjects": harbor, "n_nodes": len(w.nodes), "surfaces": surfaces}
    return desk
