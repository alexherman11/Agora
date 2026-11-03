"""Admission checks for a proposed library-limited metadata grant.

No grants are created here. A library: clause permits only folder/entry metadata,
never library creation, uploaded file mutation, attachment, or generic writes.
"""
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
        file = k.shown(actor.person, values.get("file"))
        if not file or file.get("kind") != "file":
            return False
        attached = file.get("attached_to")
        if attached:
            source = k.shown(actor.person, attached)
            if not source or library_group not in k.groups_of(attached):
                return False
        elif not k.own(actor.person, values["file"]):
            return False
    return True
