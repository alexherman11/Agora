"""dictionary (a13316): every word's dictionary entry as a row, whatever made it: the Dictionary's notes with word=
(kernel and module words) and every verb note (its own entry), with whether its implementation answers now. Terms
filter as any source's do: `rows dictionary kind=hold`, `rows dictionary bound=no`. `entry` is the note, so a gesture
on a row acts on it. The format is research/community-app/DICTIONARY-ENTRY.md; dictionary.py reads it. A row source
of its own file (scene.SOURCE_DIR, a5296)."""

USAGE = "dictionary"
FIELDS = ("word", "aliases", "kind", "takes", "undo", "may", "from", "bound", "why", "entry", "help")
ARG = "none"
OPEN = False


def rows(desk, arg, session):
    import dictionary
    out = []
    for e in dictionary.all_entries(desk):
        ok, how = dictionary.status(desk, e, session)
        first = next((l.strip() for l in e.help.splitlines() if l.strip()), "")
        out.append({"word": e.word, "aliases": " ".join(e.aliases), "kind": e.kind, "takes": e.takes, "undo": e.undo,
                    "may": e.may, "from": e.frm, "bound": "yes" if ok else "no", "why": how, "entry": e.aid,
                    "help": first})
    return out
