"""EDITING THE KERNEL (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
The kernel changes only to give every world a general capability: a word, a check, a kind of fact any app, module or
person can use. It never names its tenants: no app, module, person, kind or field name appears in this code except the
kernel's own (word, rule, kind, grant, person, ...). If your change needs `if kind == "..."`, a person's name or one app's
field, stop: the missing piece is a general word (a kind's policy, a rule step, a reading). Build that, or put it on the
Board. Names already here are debt (docs/design/source-edits/SOURCE-AUDIT-KERNEL.md lists them); take them out when you can.

Admission checks for a proposed library-limited metadata grant.

No grants are created here. A library: clause permits only folder/entry metadata,
never library creation, uploaded file mutation, attachment, or generic writes.
"""
WORDS = {"files.browse", "files.folder", "files.store", "files.rename", "files.move"}


def metadata(k, person, tid, library_id):
    """Visible inherited metadata with an unbroken same-library parent chain."""
    groups = k.groups_of(library_id)
    if len(groups) != 1:
        return False
    seen = set()
    while tid != library_id:
        if not tid or tid in seen or len(seen) >= 128:
            return False
        row = k.shown(person, tid)
        if (not row or row.get("kind") not in ("document-folder", "document-entry")
                or (seen and row.get("kind") != "document-folder")
                or row.get("library") != library_id
                or row.get("visibility_of") != library_id or k.groups_of(tid) != groups):
            return False
        seen.add(tid)
        tid = row.get("parent")
    return True


def visible_file(k, actor, tid, library_id):
    row = k.shown(actor.person, tid)
    if not row or row.get("kind") != "file":
        return False
    attached = row.get("attached_to")
    if not attached:
        return k.own(actor.person, tid)
    source = k.shown(actor.person, attached)
    return bool(source and k.groups_of(library_id)[0] in k.groups_of(attached)
                and (source.get("kind") == "post" or (
                    source.get("kind") == "document-entry" and metadata(k, actor.person, attached, library_id))))


def selection(k, actor, word, target, values):
    """Validate a complete outer request before the provider sees any input."""
    if word not in WORDS:
        return None
    allowed = {
        "files.browse": {"library", "parent", "in", "as"},
        "files.folder": {"library", "parent", "name", "in", "as"},
        "files.store": {"library", "parent", "name", "in", "as"},
        "files.rename": {"library", "name", "in", "as"},
        "files.move": {"library", "to", "in", "as"},
    }[word]
    if set(values) - allowed:
        return None
    row = k.shown(actor.person, target) if target else None
    library_id = values.get("library") or (row or {}).get("library")
    library = k.shown(actor.person, library_id)
    if not library or library.get("kind") != "document-library" or len(k.groups_of(library_id)) != 1:
        return None
    if values.get("in", k.groups_of(library_id)[0]) != k.groups_of(library_id)[0]:
        return None
    if word in ("files.rename", "files.move"):
        if not row or row.get("library") != library_id or not metadata(k, actor.person, target, library_id):
            return None
    elif word == "files.store":
        if not visible_file(k, actor, target, library_id):
            return None
    elif target:
        return None
    parent = values.get("to") if word == "files.move" else values.get("parent")
    if parent and parent != library_id:
        folder = k.shown(actor.person, parent)
        if not folder or folder.get("kind") != "document-folder" or not metadata(k, actor.person, parent, library_id):
            return None
    return library_id


def read_rows(k, actor, library_id, target, kind, rows):
    """The provider never receives unrelated visible rows or unsanitized text."""
    library = k.shown(actor.person, library_id)
    if not library or library.get("kind") != "document-library" or len(k.groups_of(library_id)) != 1:
        return []
    group = k.groups_of(library_id)[0]
    entries = [t for t in k.things("document-entry") if metadata(k, actor.person, t, library_id)]
    indexed = {k.state.get(t, "file") for t in entries}
    def fits(row):
        tid = row.get("id")
        if kind == "document-library":
            return tid == library_id
        if kind in ("document-folder", "document-entry"):
            return metadata(k, actor.person, tid, library_id)
        if kind == "post":
            return group in k.groups_of(tid)
        if kind == "file":
            if not visible_file(k, actor, tid, library_id):
                return False
            attached = row.get("attached_to")
            return tid == target or tid in indexed or (
                attached and k.state.get(attached, "kind") == "post" and group in k.groups_of(attached))
        return False
    return [row for row in rows if fits(row)]


def admits(k, actor, library_id, word, kind, target, values, group=None):
    """Check the whole proposed write, while the kernel admission lock is held."""
    if word not in ("make", "set") or kind not in ("document-folder", "document-entry"):
        return False
    library = k.shown(actor.person, library_id)
    if not library or library.get("kind") != "document-library":
        return False
    groups = k.groups_of(library_id)
    if len(groups) != 1:
        return False
    library_group = groups[0]
    values = dict(values)
    if word == "make":
        allowed = {"kind", "library", "parent", "name", "within", "in", "as"}
        if kind == "document-entry":
            allowed.add("file")
        if set(values) - allowed:
            return False
        if values.get("library") != library_id or values.get("within") != library_id:
            return False
        if group != library_group:
            return False
        current = {}
    else:
        current = k.shown(actor.person, target)
        if not current or current.get("library") != library_id:
            return False
        if current.get("visibility_of") != library_id or k.groups_of(target) != groups:
            return False
        # In particular, library/file/visibility/group cannot be reassigned.
        if not values or set(values) - {"name", "parent"}:
            return False
    if "name" in values and not 1 <= len(str(values["name"]).strip()) <= 200:
        return False
    if word == "make" and not str(values.get("name", "")).strip():
        return False
    parent = values.get("parent", current.get("parent"))
    visited = {target} if target else set()
    while parent != library_id:
        if not parent or parent in visited or len(visited) >= 128:
            return False
        visited.add(parent)
        folder = k.shown(actor.person, parent)
        if (not folder or folder.get("kind") != "document-folder"
                or folder.get("library") != library_id
                or folder.get("visibility_of") != library_id
                or k.groups_of(parent) != groups):
            return False
        parent = folder.get("parent")
    if word == "make" and kind == "document-entry":
        if not visible_file(k, actor, values.get("file"), library_id):
            return False
    return True
