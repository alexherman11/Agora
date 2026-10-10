"""Kinds in the world (Alex, 5 Oct: "can we get kinds into the world so we can have a kind for a lens").

A kind used to be one of eight words fixed in the host (world.create's check). Now a kind is also a note tagged `kind`
whose title is the kind's name, one word; its props say what it builds on, and its text describes it:

    do create <Kinds binder> kind=note title=lens tags=kind is=note text="A lens: a note whose text says how ..."

A kind note describes, it never enforces (research/command-center/DRAFT-kinds-and-shapes.md, section 3.4):
  - `is=<kind>` is what the kind builds on, so it has every verb that kind has (moo.verbs_by_origin walks the chain
    the way KIND_CHAIN did for the built-in kinds). The default is note. An `is` that names nothing known reads as
    note; a loop stops at eight steps.
  - `expects=a,b` and `lens=<name>` are words for readers (and for a future default lens); the host reads neither.
  - Changing or removing a kind note changes no thing: a thing keeps its kind word, its props and its text.

The built-in kinds are the SHAPES: how content is stored, merged, undone and fenced. A world kind has the shape of
what it is built on; `rekind` moves a thing between kinds of one shape and is refused across shapes (a chat is
lines, a note is text: make a new thing instead).

`kind:lens` in a selection is the exact word, as `kind:note` always was: `kind:note` no longer lists lens
definitions once they are rekinded, and `kind:note|lens` lists both. Lenses are found by kind=lens or the older
tag `lens` (is_lens), so frozen and foreign worlds still print.
"""
import re

# what the host does differently per built-in kind, and the verbs each inherits (most specific first)
KIND_CHAIN = {
    "surface": ["surface", "thing"],
    "note": ["note", "text", "appearance", "thing"],
    "task": ["task", "text", "appearance", "thing"],
    "chat": ["chat", "text", "appearance", "thing"],
    "doc": ["doc", "text", "appearance", "thing"],
    "image": ["image", "appearance", "thing"],
    "trial": ["trial", "text", "appearance", "thing"],
    "promise": ["promise"],     # a1587: its words are its maker's, and it ends only by its own verbs (help promises)
}
BUILT_IN = ("note", "task", "chat", "image", "doc", "trial", "surface", "view")
# the shape: how content is stored and edited. note, task, doc and trial are one shape, text, told apart by their
# verbs and printers; chat appends signed lines; an image is bytes; a surface holds things; a view holds a selection
SHAPES = {"note": "text", "task": "text", "doc": "text", "trial": "text", "chat": "lines", "image": "bytes",
          "surface": "container", "view": "selection", "promise": "promise", "person": "person"}
NAME = re.compile(r"[a-z][a-z0-9-]*")


def notes(w):
    """-> {name: subject} for every note tagged kind whose title is one word (a kind made in this world)."""
    out = {}
    for s in w.subjects.values():
        if "kind" in (s.get("tags") or []) and s.get("kind") != "kind":
            name = str(s.get("title") or "").strip().lower()
            if NAME.fullmatch(name) and name not in BUILT_IN:
                out.setdefault(name, s)
    return out


def known(w):
    """Every kind a thing may be made as here: the built-in words, and the kinds made in this world."""
    return set(BUILT_IN) | set(notes(w))


def notes_titled(w, kind):
    """Every kind note titled `kind`, in id order."""
    kind = str(kind or "").strip().lower()
    return sorted((s for s in w.subjects.values() if "kind" in (s.get("tags") or []) and s.get("kind") != "kind"
                   and str(s.get("title") or "").strip().lower() == kind), key=lambda s: int(re.sub(r"\D", "", s["id"]) or 0))


def note_for(w, kind, at=None):
    """The kind note that describes `kind` from the room `at` (a thing's own room, where its kind is read): nearest
    first by verbs.ladder (9 Oct, step 7), as a lens or a style is found. -> (subject or None, the others at the same
    distance). Two at one distance never refuse here (a kind's word must keep meaning something for the verbs that
    read its chain): the first by id is read, and the receipt says so (table.remarks)."""
    import verbs
    cands = notes_titled(w, kind)
    if not cands or kind in BUILT_IN:
        return None, []
    hits, _level = verbs.ladder(w, cands, verbs.place_of_note, at)
    if not hits:
        return None, []
    return hits[0][0], [s for s, _ in hits[1:]]


def built_on(w, kind, at=None):
    """What a world kind builds on (its `is` prop), a built-in word; None for a built-in kind."""
    s = note_for(w, kind, at)[0]
    if s is None:
        return None
    return str((s.get("props") or {}).get("is", "note")).strip().lower() or "note"


def chain(w, kind, at=None):
    """The kinds a thing of this kind is, most specific first, ending in the built-in chain its base has."""
    seen, out, k = set(), [], kind
    while k and k not in KIND_CHAIN and k not in seen and len(seen) < 8:
        seen.add(k)
        out.append(k)
        k = built_on(w, k, at) if k in notes(w) else None
    base = KIND_CHAIN.get(k) or (["view", "surface", "thing"] if k == "view" else KIND_CHAIN["note"])
    return out + list(base)


def shape(w, kind):
    for k in chain(w, kind):
        if k in SHAPES:
            return SHAPES[k]
    return "text"


def describe(w, kind, at=None):
    """A kind's own words: its note's text, or what the host says of a built-in one."""
    s = note_for(w, kind, at)[0] or next((x for x in w.subjects.values() if "kind" in (x.get("tags") or [])
                                          and str(x.get("title") or "").strip().lower() == kind), None)
    if s is not None:
        return (s.get("text") or "").strip() or f"a kind made here, built on {built_on(w, kind)} (its note says nothing more)"
    return {"note": "words: the default kind", "task": "a note with a status and an owner, done by its verbs",
            "chat": "lines appended over time, each signed by its speaker", "image": "a file, replaced whole",
            "doc": "a note printed with its ## sections", "trial": "a note whose props are a result",
            "surface": "a container with a layout", "view": "a surface whose contents are a selection"}.get(kind, "")


def is_lens(s):
    """A lens definition: a thing of kind lens, or (the older way, kept for frozen and foreign worlds) a note tagged lens."""
    return bool(s) and (s.get("kind") == "lens" or "lens" in (s.get("tags") or []))


def refusal(w, kind):
    made = sorted(notes(w))
    return (f"kind= must be {', '.join(BUILT_IN[:-1])} or {BUILT_IN[-1]}"
            + (f", or a kind made here: {', '.join(made)}" if made else "")
            + f"; {kind!r} is none of these (a kind is a note tagged kind whose title is its name; help kinds)")
